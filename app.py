import copy
import json
import logging
import time
from tkinter import N
from click import DateTime
from flask import Flask, Response, request, redirect, stream_with_context, url_for, render_template, flash, jsonify, send_file
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit
from sqlalchemy import text
from datetime import datetime
from urllib.parse import quote
import platform

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
from db.services.pharmacy_service import PharmacyService
from db.services.qa_service import QAService

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
        if classification == 'all':
            # 获取所有文件，但过滤掉 eCTD 类型
            total = FileService().get_all_file_count_except_ectd()
            files = FileService().get_all_files_except_ectd(offset, limit)
        else:
            total = FileService().get_file_count_by_classification(classification)
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

@app.route('/get_file_classification', methods=['GET', 'POST'])
def get_file_classification():
    ans =  FileService().get_file_classification()
    list_info = []
    for item in ans:
        list_info.append(item[0])
    return ResponseMessage(200, 'Get file classification successfully', list_info).to_json()

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
    data = request.get_json()
    doc_id = data.get('doc_id')
    export_type = 'word'  # 强制只导出word
    if not doc_id:
        logging.error('No doc_id provided')
        return ResponseMessage(400, 'No doc_id provided', None).to_json()
    info = ReportService().export_report(doc_id, export_type)
    if info["status"] == 0:
        logging.error(f'Failed to export report: {info["message"]}')
        return ResponseMessage(400, f'Failed to export report: {info["message"]}', None).to_json()
    file_path = info["data"]
    if not os.path.exists(file_path):
        logging.error(f'File {file_path} not found')
        return ResponseMessage(400, f'File {file_path} not found', None).to_json()

    # 获取原始文件名，拼接"_报告.docx"
    file_info = FileService().get_file_by_id(doc_id)
    base_name = os.path.splitext(file_info.file_name)[0]
    download_filename = f"{base_name}_报告.docx"
    ascii_filename = download_filename.encode('ascii', 'ignore').decode('ascii') or 'report.docx'
    utf8_filename = quote(download_filename)
    content_disposition = f"attachment; filename={ascii_filename}; filename*=UTF-8''{utf8_filename}"

    def generate():
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                yield chunk

    mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    response = Response(
        generate(),
        mimetype=mimetype,
        headers={
            'Content-Disposition': content_disposition,
            'Cache-Control': 'no-cache'
        }
    )
    response.headers['Content-Length'] = str(os.path.getsize(file_path))
    return response

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
    file_info = FileService().get_file_by_id(doc_id)
    if file_info is None:
        logging.error(f'File {doc_id} not found')
        return ResponseMessage(400, f'File {doc_id} not found', None).to_json()

    if file_info.classification != 'eCTD':
        logging.error(f'File {doc_id} is not an eCTD file')
        return ResponseMessage(400, f'File {doc_id} is not an eCTD file', None).to_json()

    file_path = file_info.file_path

    def generate():
        try:
            parser = CTDPDFParser(file_path)
            data = parser.parse()
            total_sections = len(data.get("content", []))
            cleaned_data = {"doc_id": doc_id, "content": []}
            section_ids = []

            for idx, item in enumerate(data.get("content", []), start=1):
                if item.get("content", "") == "" or len(item.get("content", "")) < 70:
                    yield json.dumps({"cur_section": idx, "total_section": total_sections}) + "\n"                
                    continue

                content = {
                    "section_id": item.get("section_id", ""),
                    "section_name": item.get("section_name", ""),
                    "content": []
                }
                section_ids.append(item.get("section_id"))

                llm_data = {"content": item.get("content")}
                try:
                    ans = ask_llm_by_prompt_file("mutil_agents/prompts/data_process/eCTD_clean_prompt.j2", llm_data)
                except Exception as e:
                    logging.error(f'Failed to clean file: {str(e)}')
                    content["content"].append(copy.deepcopy(item.get("content", "")))
                    cleaned_data["content"].append(copy.deepcopy(content))
                    yield json.dumps({"cur_section": idx, "total_section": total_sections}) + "\n"
                    continue

                if ans is None or ans["response"] is None:
                    logging.error(f"clean error: ans is None")
                    content["content"].append(copy.deepcopy(item.get("content", "")))
                    cleaned_data["content"].append(copy.deepcopy(content))
                    yield json.dumps({"cur_section": idx, "total_section": total_sections}) + "\n"
                    continue

                if not isinstance(ans["response"], dict):
                    content["content"].append(copy.deepcopy(item.get("content", "")))
                    cleaned_data["content"].append(copy.deepcopy(content))
                    yield json.dumps({"cur_section": idx, "total_section": total_sections}) + "\n"
                    continue

                if ans["response"].get("content", None) is None:
                    content["content"].append(copy.deepcopy(item.get("content", "")))
                    cleaned_data["content"].append(copy.deepcopy(content))
                    yield json.dumps({"cur_section": idx, "total_section": total_sections}) + "\n"
                    continue

                if not isinstance(ans["response"]["content"], list):
                    ans["response"]["content"] = [ans["response"]["content"]]

                content["content"] = ans["response"]["content"]
                cleaned_data["content"].append(copy.deepcopy(content))

                yield json.dumps({"cur_section": idx, "total_section": total_sections}) + "\n"

            # Save cleaned data and update file information
            redis_conn = RedisDB()
            for item_content in cleaned_data.get("content", []):
                print(item_content)
                f'section_content+{doc_id}+{item.get("section_id")}'
                redis_conn.set(f'section_content+{doc_id}+{item_content.get("section_id")}', json.dumps(item_content), None)

            rewrite_json_file(f'{eCTD_FILE_DIR}{doc_id}.json', cleaned_data)
            FileService().update_file_chunk_by_id(doc_id, len(section_ids), ";".join(section_ids))
        except Exception as e:
            logging.error(f'Failed to parse file: {str(e)}')
            yield json.dumps({"error": f"Failed to parse file: {str(e)}"}) + "\n"
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

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

@app.route('/get_report', methods=['POST'])
@cross_origin()
def get_report():
    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        
        if not doc_id:
            return jsonify({
                'code': 400,
                'message': '文档ID不能为空'
            })
        
        # 使用 ReportService 获取报告内容
        report_service = ReportService()
        result = report_service.get_report_content(doc_id)
        
        if result["status"] == 0:
            return jsonify({
                'code': 400,
                'message': result["message"]
            })
            
        return jsonify({
            'code': 200,
            'data': {
                'content': result["data"]
            }
        })
        
    except Exception as e:
        logging.error(f"获取报告失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'获取报告失败: {str(e)}'
        })
@app.route('/get_report_by_section', methods=['GET','POST'])
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
    try:
        doc_id = request.json.get('doc_id')
        section_id = request.json.get('section_id')
        content = request.json.get('content')
        
        if not doc_id or not content:
            return ResponseMessage(400, '参数不完整', None).to_json()
            
        redis_conn = RedisDB()
        
        if section_id == 'all':
            # 更新完整报告
            report_key = f"report+{doc_id}"
            flag = redis_conn.set(report_key, content)
        else:
            # 更新章节报告
            section_key = f"review_content+{doc_id}+{section_id}"
            flag = redis_conn.set(section_key, content)
            
        if not flag:
            return ResponseMessage(400, '保存失败', None).to_json()
            
        return ResponseMessage(200, '保存成功', None).to_json()
        
    except Exception as e:
        logging.error(f'保存报告内容失败: {str(e)}')
        return ResponseMessage(500, f'保存失败: {str(e)}', None).to_json()

@app.route('/update_review_status', methods=['POST'])
def update_review_status():
    data = request.get_json()
    doc_id = data.get('doc_id')
    status = data.get('status')
    
    if not doc_id or status is None:
        return jsonify({'code': 400, 'msg': '参数错误'})
    
    success, message = FileService().update_review_status(
        doc_id, 
        status, 
        datetime.now() if status == 1 else None
    )
    
    if success:
        return jsonify({'code': 200, 'msg': '更新成功'})
    else:
        return jsonify({'code': 500, 'msg': message})
    
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

@app.route('/get_document_info', methods=['POST'])
@cross_origin()
def get_document_info():
    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        
        if not doc_id:
            return jsonify({
                'code': 400,
                'message': '文档ID不能为空'
            })
        
        # 使用 FileService 获取文档信息
        file_service = FileService()
        doc_info, error = file_service.get_document_info(doc_id)
        
        if error:
            return jsonify({
                'code': 404,
                'message': error
            })
            
        return jsonify({
            'code': 200,
            'data': doc_info
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取文档信息失败: {str(e)}'
        })

@app.route('/get_original_file_content', methods=['POST'])
@cross_origin()
def get_original_file_content():
    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        
        if not doc_id:
            return jsonify({
                'code': 400,
                'message': '文档ID不能为空'
            })
        
        # 获取文件信息
        file_info = FileService().get_file_by_id(doc_id)
        if not file_info:
            return jsonify({
                'code': 404,
                'message': '文件不存在'
            })
            
        # 读取PDF文件内容
        try:
            import PyPDF2
            with open(file_info.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = []
                for page in pdf_reader.pages:
                    content.append(page.extract_text())
                
                return jsonify({
                    'code': 200,
                    'data': {
                        'content': '\n\n'.join(content)
                    }
                })
        except Exception as e:
            logging.error(f'读取PDF文件失败: {str(e)}')
            return jsonify({
                'code': 500,
                'message': f'读取PDF文件失败: {str(e)}'
            })
            
    except Exception as e:
        logging.error(f'获取原始文件内容失败: {str(e)}')
        return jsonify({
            'code': 500,
            'message': f'获取原始文件内容失败: {str(e)}'
        })

@app.route('/pdf_view/<doc_id>')
@cross_origin()
def pdf_view(doc_id):
    file_info = FileService().get_file_by_id(doc_id)
    if not file_info or not os.path.exists(file_info.file_path):
        return "PDF文件不存在", 404
    return send_file(
        file_info.file_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=os.path.basename(file_info.file_path)
    )

@app.route('/get_report_status/<doc_id>', methods=['GET'])
@cross_origin()
def get_report_status(doc_id):
    """获取报告生成状态"""
    try:
        status = ReportService().get_report_status(doc_id)
        return ResponseMessage(200, 'Success', status).to_json()
    except Exception as e:
        logging.error(f'获取报告状态失败: {str(e)}')
        return ResponseMessage(500, f'获取报告状态失败: {str(e)}', None).to_json()

@app.route('/pharmacy/add', methods=['POST'])
def add_pharmacy():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'code': 400, 'msg': '药品名称必填'})
    # 只保留模型字段
    keys = ['name', 'prescription', 'characteristic', 'identification', 'inspection', 'content_determination', 'category', 'storage', 'preparation', 'specification']
    info = {k: data.get(k) for k in keys}
    success, result = PharmacyService().add_pharmacy(info)
    if success:
        return jsonify({'code': 200, 'msg': '添加成功', 'id': result})
    else:
        return jsonify({'code': 500, 'msg': f'添加失败: {result}'})

@app.route('/pharmacy/<int:id>', methods=['GET'])
def get_pharmacy(id):
    obj = PharmacyService().get_pharmacy_by_id(id)
    if obj:
        return jsonify({'code': 200, 'data': obj.__dict__})
    else:
        return jsonify({'code': 404, 'msg': '未找到'})

@app.route('/pharmacy/list', methods=['GET'])
def list_pharmacy():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    objs = PharmacyService().list_pharmacy(offset, limit)
    total = PharmacyService().count_pharmacy()
    data = [o.__dict__ for o in objs]
    for d in data:
        d.pop('_sa_instance_state', None)
    return jsonify({'code': 200, 'data': {'list': data, 'total': total}})

@app.route('/pharmacy/update/<int:id>', methods=['POST'])
def update_pharmacy(id):
    data = request.get_json()
    keys = ['name', 'prescription', 'characteristic', 'identification', 'inspection', 'content_determination', 'category', 'storage', 'preparation', 'specification']
    update_dict = {k: data.get(k) for k in keys if k in data}
    success = PharmacyService().update_pharmacy(id, update_dict)
    if success:
        return jsonify({'code': 200, 'msg': '更新成功'})
    else:
        return jsonify({'code': 500, 'msg': '更新失败'})

@app.route('/pharmacy/delete/<int:id>', methods=['POST'])
def delete_pharmacy(id):
    success = PharmacyService().delete_pharmacy(id)
    if success:
        return jsonify({'code': 200, 'msg': '删除成功'})
    else:
        return jsonify({'code': 500, 'msg': '删除失败'})

@app.route('/qa/add', methods=['POST'])
def add_qa():
    data = request.get_json()
    if not data or 'category' not in data or 'question' not in data:
        return jsonify({'code': 400, 'msg': '问题类别和问题必填'})
    keys = ['category', 'question', 'answer']
    info = {k: data.get(k) for k in keys}
    success, result = QAService().add_qa(info)
    if success:
        return jsonify({'code': 200, 'msg': '添加成功', 'id': result})
    else:
        return jsonify({'code': 500, 'msg': f'添加失败: {result}'})

@app.route('/qa/<int:id>', methods=['GET'])
def get_qa(id):
    obj = QAService().get_qa_by_id(id)
    if obj:
        return jsonify({'code': 200, 'data': obj.__dict__})
    else:
        return jsonify({'code': 404, 'msg': '未找到'})

@app.route('/qa/list', methods=['GET'])
def list_qa():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit
    category = request.args.get('category')
    objs = QAService().list_qa(category, offset, limit)
    total = QAService().count_qa(category)
    data = [o.__dict__ for o in objs]
    for d in data:
        d.pop('_sa_instance_state', None)
    return jsonify({'code': 200, 'data': {'list': data, 'total': total}})

@app.route('/qa/update/<int:id>', methods=['POST'])
def update_qa(id):
    data = request.get_json()
    keys = ['category', 'question', 'answer']
    update_dict = {k: data.get(k) for k in keys if k in data}
    success = QAService().update_qa(id, update_dict)
    if success:
        return jsonify({'code': 200, 'msg': '更新成功'})
    else:
        return jsonify({'code': 500, 'msg': '更新失败'})

@app.route('/qa/delete/<int:id>', methods=['POST'])
def delete_qa(id):
    success = QAService().delete_qa(id)
    if success:
        return jsonify({'code': 200, 'msg': '删除成功'})
    else:
        return jsonify({'code': 500, 'msg': '删除失败'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
