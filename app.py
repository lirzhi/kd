import copy
import json
import logging
import time
from tkinter import N
from flask import Flask, Response, request, redirect, stream_with_context, url_for, render_template, flash, jsonify
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit
from sqlalchemy import text

from db.dbutils.redis_conn import RedisDB
from db.services.file_service import FileService
from db.services.kd_service import KDService
from db.services.report_service import ReportService
from db.services.requirement_service import RequireService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.specific_review_state import SpecificReviewState
from utils.common_util import ResponseMessage, get_handle_info
from utils.file_util import ensure_dir_exists, rewrite_json_file
from utils.parser.ctd_parser import CTDPDFParser
from utils.parser.parser_manager import CHUNK_BASE_PATH, ParserManager
from mutil_agents.agent import specific_report_generationAgent_graph
import os

logger = logging.getLogger(__name__)

eCTD_FILE_DIR = 'data/parser/eCTD/'
ensure_dir_exists('log')
ensure_dir_exists(eCTD_FILE_DIR)
logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename='log/server.log',
                    filemode='a')

app = Flask(__name__, static_folder='templates')
app.config['SECRET_KEY'] = 'your_secret_key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/upload_file', methods=['POST'])
def upload_file():
    res_data = {
        "status": 1,
        "doc_id": None,
        "msg": None
    }
    # Check if the request contains a file
    if 'file' not in request.files:
        logging.error('No file part')
        res_data["status"] = 0
        res_data["msg"] = 'No file part'
        return ResponseMessage(400, 'No file part', res_data).to_json()
    file = request.files['file']
    # If the user does not select a file, the browser may submit an empty part without a filename
    if file.filename == '':
        res_data["status"] = 0
        res_data["msg"] = 'No selected file'
        return ResponseMessage(400, 'No selected file', res_data).to_json()
    meta_info = {
        "classification": request.form.get('classification'),
        "affect_range": request.form.get('affect_range'),
    }
    flag, info = FileService().save_file(file, meta_info)
    if not flag:
        logging.warning(info)
        res_data["status"] = 0
        res_data["msg"] = info
        return ResponseMessage(400, info, res_data).to_json()
    res_data["doc_id"] = info
    res_data['msg'] = f'File {file.filename} uploaded successfully! doc_id: {info}'
    return ResponseMessage(200, f'File {file.filename} uploaded successfully! doc_id: {info}', res_data).to_json()

@app.route('/delete_file/<doc_id>', methods=['GET', 'POST'])
def delete_file(doc_id):
    file_info = FileService().get_file_by_id(doc_id)
    if file_info is None:
        logging.error(f'File {doc_id} not found')
        return ResponseMessage(400, f'File {doc_id} not found', None).to_json()
    if os.path.exists(file_info.file_path):
        try:
            os.remove(file_info.file_path)
        except Exception as e:
            logging.error(f'Failed to delete file: {str(e)}')
            return ResponseMessage(400, f'Failed to delete local file: {str(e)}', None).to_json()
    if file_info.is_chunked == 1:
        parsed_file_path=os.path.join(CHUNK_BASE_PATH, file_info.file_type, file_info.classification, "chunks", file_info.file_name)
        if os.path.exists(parsed_file_path):
            try:
                os.remove(parsed_file_path)
            except Exception as e:
                logging.error(f'Failed to delete file: {str(e)}')
                return ResponseMessage(400, f'Failed to delete local parsed file: {str(e)}', None).to_json()
        # 删除向量数据
        ids = file_info.chunk_ids.split(";")
        ans = KDService().delete_chunk_from_vector(ids)
        if ans == None:
            logging.error('Failed to delete vector data')
            return ResponseMessage(400, 'Failed to delete vector data', None).to_json()
        logging.info(f'{ans}: document fragments successfully deleted from vector database')
        
    flag = FileService().delete_file_by_id(doc_id)
    if not flag:
        logging.warning(f'Failed to delete file {doc_id}')
        return ResponseMessage(400, f'Failed to delete file {doc_id}', None).to_json()
    return ResponseMessage(200, f'File {doc_id} deleted successfully').to_json()

@app.route('/get_file_by_class/<classification>', methods=['GET'])
def get_file_by_class(classification):
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        # 获取总数
        total = FileService().get_file_count_by_classification(classification)
        
        # 获取分页数据
        files = FileService().get_files_by_classification(classification, offset, limit)
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': files,
                'total': total
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'获取文件列表失败: {str(e)}',
            'data': None
        })

@app.route('/get_file_classification', methods=['GET'])
def get_file_classification():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        # 获取总数
        total = FileService().get_file_count_by_classification('knowledge')
        
        # 获取分页数据
        files = FileService().get_files_by_classification('knowledge', offset, limit)
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': files,
                'total': total
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'获取文件列表失败: {str(e)}',
            'data': None
        })

@app.route('/add_to_kd/<doc_id>', methods=['GET','POST'])
def add_to_kd(doc_id):
    # Chunk splitting
    try:
        chunks = ParserManager.parse(doc_id)
    except Exception as e:
        logging.error(f'Failed to chunk file: {str(e)}')
        return ResponseMessage(400, f'Failed to chunk file: {str(e)}', None).to_json()
    if not chunks:
        logging.warning('File chunking failed')
        return ResponseMessage(400, 'File chunk size is 0, please check if the file content exists', None).to_json()
    
    # Save to Elasticsearch database
    err_msg = KDService().save_chunks_to_es(chunks, "knowledge_index", chunks[0]["classification"])
    if err_msg:
        flash(err_msg)
        return ResponseMessage(400, err_msg, None).to_json()
    logging.info(f'File {doc_id} successfully added to Elasticsearch')

    # Save to vector database
    res = KDService().save_chunk_to_vector(chunks)
    if res == None: 
        logging.error('Failed to save to vector database')
        return ResponseMessage(400, 'Failed to save to vector database', None).to_json()
    ids_list = []
    ids_list = [str(item) for item in res.get("ids", [])]  # 转换为字符串列表
    v_chunk_ids = ";".join(ids_list)
     # Save chunk information to MySQL database
    flag, msg = FileService().update_file_chunk_by_id(doc_id, len(chunks), v_chunk_ids)
    if not flag:
        return ResponseMessage(400, msg, None).to_json()
    
    logging.info(f"{res['insert_count']}/{len(chunks)} document fragments successfully added to vector database")
    return ResponseMessage(200, f'File {doc_id} successfully added to knowledge base', chunks).to_json()

#审评要求部分
#获取审评要求
@app.route('/get_requirement', methods=['POST'])
@cross_origin()
def get_requirement():
   try:
        # 参数校验
        section_id = request.json.get('section_id')
    
        # if not section_id:
        #     return ResponseMessage(400, 'section_id 参数缺失', None).to_json()

        # 调用服务层
        service = RequireService()
       
        result = service.get_requirement_by_section(section_id)
        # if not result.success:
        #     return ResponseMessage(500, result.error, None).to_json()
        # 返回格式化数据
        return ResponseMessage(200, 'Success', result.data).to_json()
   except ValueError:
        logger.warning("参数类型错误: section_id 必须为整数")
        return ResponseMessage(400, 'section_id 必须为整数', None).to_json()
   except Exception as e:
        logger.error(f"接口异常: {str(e)}", exc_info=True)
        return ResponseMessage(500, '服务器内部错误', None).to_json()


@app.route('/search_by_query', methods=['GET','POST'])
@cross_origin()
def search_by_query():
    query = request.form.get('query')
    if not query:
        query = request.json.get('query')
    llm_resp = KDService().search_by_query(query)
    return ResponseMessage(200, 'Search completed', llm_resp).to_json()

@app.route('/')
def index():
    return redirect(url_for("static", filename='review.html'))

@app.route('/review_text', methods=['GET','POST'])
@cross_origin()
def review_text():
    start_time = time.time()
    content = request.json.get('content')
    content_section = request.json.get('content_section')
    review_require_list = request.json.get('review_require_list')
    if not content:
        logging.error('No review content provided')
        return ResponseMessage(400, 'No review content provided', None).to_json()
    review_state = SpecificReviewState()
    review_state["content"] = content
    review_state["content_section"] = content_section
    review_state["review_require_list"] = review_require_list
    result = specific_report_generationAgent_graph.invoke(review_state)
    print(ResponseMessage(200, 'Review completed', result).to_json())
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"执行时间: {execution_time} 秒")
    return ResponseMessage(200, 'Review completed', result).to_json()

@app.route('/review_section', methods=['GET','POST'])
@cross_origin()
def review_section():
    start_time = time.time()
    doc_id = request.json.get('doc_id')
    content = request.json.get('content')
    section_name = request.json.get('section_name')
    section_id = request.json.get('section_id')
    if not content:
        logging.error('No review content provided')
        return ResponseMessage(400, 'No review content provided', None).to_json()
    
    review_state = ReportService().generate_report_by_section(doc_id, section_id, section_name, content)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"执行时间: {execution_time} 秒")
    return ResponseMessage(200, 'Review completed', review_state).to_json()

@app.route('/review_all_section', methods=['GET','POST'])
@cross_origin()
def review_all_section():
    doc_id = request.json.get('doc_id')
    review_info = ReportService().create_final_report(doc_id)
    if review_info["status"] == 0:
        logging.error(f'Failed to generate report: {review_info["message"]}')
        return ResponseMessage(400, f'Failed to generate report: {review_info["message"]}', None).to_json()
    return ResponseMessage(200, 'Report generated successfully', review_info["data"]).to_json()
    

@app.route('/export_report', methods=['GET','POST'])
@cross_origin()
def export_report():
    doc_id = request.json.get('doc_id')
    if not doc_id:
        logging.error('No doc_id provided')
        return ResponseMessage(400, 'No doc_id provided', None).to_json()
    info = ReportService().export_report(doc_id)
    if info["status"] == 0:
        logging.error(f'Failed to export report: {info["message"]}')
        return ResponseMessage(400, f'Failed to export report: {info["message"]}', None).to_json()
    file_path = info["data"]
    if not os.path.exists(file_path):
        logging.error(f'File {file_path} not found')
        return ResponseMessage(400, f'File {file_path} not found', None).to_json()
    def generate():
        with open(file_path, 'rb') as f:
            while chunk := f.read(4096):
                yield chunk

    return Response(
        generate(),
        mimetype='application/octet-stream',
        headers={
            'Content-Disposition': f'attachment; filename="{os.path.basename(file_path)}"',
            'Cache-Control': 'no-cache'
        }
    )
    

@app.route('/parse_ectd/<doc_id>', methods=['GET','POST'])
@cross_origin()
def parse_ectd(doc_id):
    file_info = FileService().get_file_by_id(doc_id)
    if file_info is None:
        logging.error(f'File {doc_id} not found')
        return ResponseMessage(400, f'File {doc_id} not found', None).to_json()
    file_path = file_info.file_path
    if file_info.classification != 'eCTD':
        logging.error(f'File {doc_id} is not an eCTD file')
        return ResponseMessage(400, f'File {doc_id} is not an eCTD file', None).to_json()
    try:
        parser = CTDPDFParser(file_path)
        data = parser.parse()
    except Exception as e:
        logging.error(f'Failed to parse file: {str(e)}')
        return ResponseMessage(400, f'Failed to parse file: {str(e)}', None).to_json()
    cleaned_data = {}
    cleaned_data['doc_id'] = doc_id
    cleaned_data['content'] = []
    content = {}
    for item in data.get("content", []):
        if item.get("content", "") == "" or len(item.get("content", "")) < 30:
            continue
        content["section_id"] = item.get("section_id")
        content["section_name"] = item.get("section_name")
        llm_data = {
            "content": item.get("content"),
        }
        try:
            ans = ask_llm_by_prompt_file("mutil_agents/prompts/data_process/eCTD_clean_prompt.j2", llm_data)
        except Exception as e:
            logging.error(f'Failed to clean file: {str(e)}')
            cleaned_data["content"].append(copy.deepcopy(item.get("content", "")))
            continue
            
        if ans == None or ans["response"] == None:
            logging.error(f"clean error: ans is None") 
            cleaned_data["content"].append(copy.deepcopy(item.get("content", "")))
            continue
        print(f"ans['response']:{ans['response']}")
        if ans["response"].get("content", None) == None:
            cleaned_data["content"].append(copy.deepcopy(item.get("content", "")))
            continue
        if type(ans["response"]["content"]) != list:
            ans["response"]["content"] = [ans["response"]["content"]]
        content["content"] = ans["response"]["content"]
        cleaned_data["content"].append(copy.deepcopy(content))
    section_ids = []
    redis_conn = RedisDB()
    for item in cleaned_data.get("content", []):
        redis_conn.set(f'section_content+{doc_id}+{item.get("section_id")}', json.dumps(item), None) 
        section_ids.append(item.get("section_id")) 
    rewrite_json_file(f'{eCTD_FILE_DIR}{doc_id}.json', cleaned_data)
    
    FileService().update_file_chunk_by_id(doc_id, len(section_ids), ";".join(section_ids))
    return ResponseMessage(200, 'File parsed successfully', cleaned_data).to_json()

@app.route('/parse_ectd_stream/<doc_id>', methods=['GET', 'POST'])
@cross_origin()
def parse_ectd_stream(doc_id):
    try:
        file_info = FileService().get_file_by_id(doc_id)
        if file_info is None:
            return ResponseMessage(400, f'File {doc_id} not found', None).to_json()
        
        if not os.path.exists(file_info.file_path):
            return ResponseMessage(400, f'File {file_info.file_path} not found', None).to_json()
        
        def generate():
            try:
                parser = CTDPDFParser(file_info.file_path)
                total_sections = len(parser.sections)
                
                for i, section in enumerate(parser.sections, 1):
                    if request.headers.get('Accept') == 'text/event-stream':
                        yield f"data: {json.dumps({'cur_section': i, 'total_section': total_sections})}\n\n"
                    else:
                        socketio.emit('parse_progress', {
                            'cur_section': i,
                            'total_section': total_sections
                        })
                    
                    time.sleep(0.1)  # 添加小延迟以便观察进度
                
                return ResponseMessage(200, 'Parse completed', None).to_json()
            except Exception as e:
                error_msg = f'Failed to parse file: {str(e)}'
                logging.error(error_msg)
                if request.headers.get('Accept') == 'text/event-stream':
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                else:
                    socketio.emit('parse_error', {'error': error_msg})
                return ResponseMessage(400, error_msg, None).to_json()
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
    except Exception as e:
        error_msg = f'Failed to parse file: {str(e)}'
        logging.error(error_msg)
        return ResponseMessage(400, error_msg, None).to_json()

@app.route('/delete_ectd/<doc_id>', methods=['GET','POST'])
@cross_origin()
def delete_ectd(doc_id):
    file_info = FileService().get_file_by_id(doc_id)
    
    if file_info is None:
        logging.error(f'File {doc_id} not found')
        return ResponseMessage(400, f'File {doc_id} not found', None).to_json()
    file_path = file_info.file_path  
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logging.error(f'Failed to delete file: {str(e)}')
            return ResponseMessage(400, f'Failed to delete local file: {str(e)}', None).to_json()
    
    if file_info.is_chunked == 1:
        if os.path.exists(f'{eCTD_FILE_DIR}{doc_id}.json'):
            try:
                os.remove(f"{eCTD_FILE_DIR}{doc_id}.json")
            except Exception as e:
                logging.error(f'Failed to delete file: {str(e)}')
                return ResponseMessage(400, f'Failed to delete local parsed file: {str(e)}', None).to_json()
        redis_conn = RedisDB()
        keys = redis_conn.keys("section_content+" + doc_id + "*")
        for key in keys:
            redis_conn.delete(key)
    flag = FileService().delete_file_by_id(doc_id)
    if not flag:
        logging.error(f'Failed to delete file {doc_id}')
        return ResponseMessage(400, f'Failed to delete file {doc_id}', None).to_json()  
    return ResponseMessage(200, 'File deleted successfully', None).to_json()

@app.route('/get_ectd_info_list', methods=['GET','POST'])
@cross_origin()
def get_ectd_info_list():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        # 获取总数
        total = FileService().get_file_count_by_classification('eCTD')
        
        # 获取分页数据
        files = FileService().get_files_by_classification('eCTD', offset, limit)
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': files,
                'total': total
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'获取文件列表失败: {str(e)}',
            'data': None
        })

@app.route('/get_ectd_sections/<doc_id>', methods=['GET','POST'])
@cross_origin()
def get_ectd_sections(doc_id):
    file_info = FileService().get_file_by_id(doc_id)
    if file_info ==None:
        logging.error(f'File {doc_id} not found')
        return ResponseMessage(400, f'File {doc_id} not found', None).to_json()
    if file_info.is_chunked != 1:
        logging.error(f'File {doc_id} is not parsed')
        return ResponseMessage(400, f'File {doc_id} is not parsed', None).to_json()
    section_str = file_info.chunk_ids
    section_ids = section_str.split(";")
    return ResponseMessage(200, 'Get eCTD sections successfully', section_ids).to_json()

@app.route('/get_report_content', methods=['GET','POST'])
@cross_origin()
def get_report_content():
    doc_id = request.json.get('doc_id')
    section_id = request.json.get('section_id')
    if not doc_id or not section_id:
        logging.error('No doc_id or section_id provided')
        return ResponseMessage(400, 'No doc_id or section_id provided', None).to_json()
    redis_conn = RedisDB()
    data = redis_conn.get(f"review_content+{doc_id}+{section_id}")
    if data == None:
        logging.error(f'No content found for doc_id: {doc_id}, section_id: {section_id}')
        return ResponseMessage(400, f'No content found for doc_id: {doc_id}, section_id: {section_id}', None).to_json()
    return ResponseMessage(200, 'Get report content successfully', data).to_json()

@app.route('/set_report_content', methods=['GET','POST'])
@cross_origin()
def set_report_content():
    doc_id = request.json.get('doc_id')
    section_id = request.json.get('section_id')
    content = request.json.get('content')
    if not doc_id or not section_id or not content:
        logging.error('No doc_id, section_id or content provided')
        return ResponseMessage(400, 'No doc_id, section_id or content provided', None).to_json()
    redis_conn = RedisDB()
    flag = redis_conn.set(f"review_content+{doc_id}+{section_id}", json.dumps(content), None)
    if not flag:
        logging.error(f'Failed to set content for doc_id: {doc_id}, section_id: {section_id}')
        return ResponseMessage(400, f'Failed to set content for doc_id: {doc_id}, section_id: {section_id}', None).to_json()
    return ResponseMessage(200, 'Set report content successfully', None).to_json()

@app.route('/get_principle_content', methods=['GET','POST'])
@cross_origin()
def get_principle_content():
    section_id = request.json.get('section_id')
    if not section_id:
        logging.error('No doc_id or section_id provided')
        return ResponseMessage(400, 'No doc_id or section_id provided', None).to_json()
    redis_conn = RedisDB()
    data = redis_conn.get(f"principle_content+{section_id}")
    if data == None:
        logging.error(f'No principle content found for section_id: {section_id}')
        return ResponseMessage(400, f'No principle content found for section_id: {section_id}', None).to_json()
    return ResponseMessage(200, 'Get principle content successfully', data).to_json()

@app.route('/set_principle_content', methods=['GET','POST'])
@cross_origin()
def set_principle_content():
    section_id = request.json.get('section_id')
    content = request.json.get('content')
    if not section_id or not content:
        logging.error('No doc_id, section_id or content provided')
        return ResponseMessage(400, 'No doc_id, section_id or content provided', None).to_json()
    if not isinstance(content, list):
        logging.error('Content is not a list')
        return ResponseMessage(400, 'Content is not a list', None).to_json()
    redis_conn = RedisDB()
    flag = redis_conn.set(f"principle_content+{section_id}", json.dumps(content), None)
    if not flag:
        logging.error(f'Failed to set principle content for doc_id: section_id: {section_id}')
        return ResponseMessage(400, f'Failed to set principle content for doc_id: section_id: {section_id}', None).to_json()
    return ResponseMessage(200, 'Set principle content successfully', None).to_json()

@app.route('/get_ectd_content', methods=['GET','POST'])
@cross_origin()
def get_ectd_content():
    doc_id = request.json.get('doc_id')
    section_id = request.json.get('section_id')
    if not doc_id or not section_id:
        logging.error('No doc_id or section_id provided')
        return ResponseMessage(400, 'No doc_id or section_id provided', None).to_json()
    ectd_key = f"section_content+{doc_id}+{section_id}"
    redis_conn = RedisDB()
    data = redis_conn.get(ectd_key)
    return ResponseMessage(200, 'Get content successfully', data).to_json()

@app.route('/regenerate_report', methods=['GET','POST'])
@cross_origin() 
def regenerate_report():
    content = request.json.get('content')
    if not content:
        logging.error('No content provided')
        return ResponseMessage(400, 'No content provided', None).to_json()
    print(content)
    ans = ask_llm_by_prompt_file("mutil_agents/prompts/review/review_report_prompt.j2", content)
    if ans == None or ans["response"] == None:
        logging.error(f"review error: ans is None") 
        ans = ""
    return ResponseMessage(200, 'Report regenerated', ans["response"]).to_json()    


@app.route('/stream_logs')
@cross_origin()
def stream_logs():
    def event_stream():
        try:
            while True:
                data = get_handle_info()
                if data:
                    # SSE 格式要求：data: {json}\n\n
                    yield f"data: {json.dumps(data)}\n\n"
                time.sleep(1)
        except GeneratorExit:
            logging.info("Client disconnected, stopping stream")

    return Response(
        event_stream(),
        mimetype="text/event-stream",  # 关键 MIME 类型
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
