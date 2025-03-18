import copy
import json
import logging
import time
from flask import Flask, Response, request, redirect, stream_with_context, url_for, render_template, flash
from flask_cors import CORS, cross_origin

from db.dbutils.redis_conn import RedisDB
from db.services.file_service import FileService
from db.services.kd_service import KDService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.review_state import ReviewState
from utils.common_util import ResponseMessage, get_handle_info
from utils.file_util import ensure_dir_exists, rewrite_json_file
from utils.parser.ctd_parser import CTDPDFParser
from utils.parser.parser_manager import CHUNK_BASE_PATH, ParserManager
from mutil_agents.agent import graph
import os

eCTD_FILE_DIR = 'data/parser/eCTD/'
ensure_dir_exists('log')
ensure_dir_exists(eCTD_FILE_DIR)
logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename='log/server.log',
                    filemode='a')
app = Flask(__name__, static_folder='templates')
app.config['SECRET_KEY'] = 'your_secret_key'  # Used to protect the application from cross-site request forgery attacks
# CORS(app, resources={r"/stream_logs": {"origins": "*"}})
CORS(app)  # 允许所有跨域请求
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

@app.route('/get_file_by_class/<classfication>', methods=['GET', 'POST'])
def get_file_by_class(classfication):
    file_list = FileService().get_file_by_classification(classfication)
    data_info = []
    for item in file_list:
        obj = {}
        obj["doc_id"] = item.doc_id
        obj["file_name"] = item.file_name
        obj["parse_status"] = item.is_chunked
        data_info.append(obj)
    return ResponseMessage(200, 'Get file list successfully', data_info).to_json()

@app.route('/get_file_classification', methods=['GET', 'POST'])
def get_file_classification():
    ans =  FileService().get_file_classification()
    list_info = []
    for item in ans:
        list_info.append(item[0])
    return ResponseMessage(200, 'Get file classification successfully', list_info).to_json()
CORS(app)  # 允许所有跨域请求
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
    content = request.json.get('content')
    content_section = request.json.get('content_section')
    review_require_list = request.json.get('review_require_list')
    if not content:
        logging.error('No review content provided')
        return ResponseMessage(400, 'No review content provided', None).to_json()
    review_state = ReviewState()
    review_state["content"] = content
    review_state["content_section"] = content_section
    review_state["review_require_list"] = review_require_list
    result = graph.invoke(review_state)
    print(ResponseMessage(200, 'Review completed', result).to_json())
    return ResponseMessage(200, 'Review completed', result).to_json()

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
        redis_conn.set(doc_id + item.get("section_id"), json.dumps(item), None) 
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
                section_ids.append(item.get("section_id"))

                yield json.dumps({"cur_section": idx, "total_section": total_sections}) + "\n"

            # Save cleaned data and update file information
            redis_conn = RedisDB()
            for item_content in cleaned_data.get("content", []):
                print(item_content)
                redis_conn.set(doc_id + item_content.get("section_id"), json.dumps(item_content), None)

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
        keys = redis_conn.keys(doc_id + "*")
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
    file_list = FileService().get_file_by_classification('ectd')
    print(file_list)
    data_info = []
    for item in file_list:
        obj = {}
        obj["doc_id"] = item.doc_id
        obj["file_name"] = item.file_name
        obj["parse_status"] = item.is_chunked
        data_info.append(obj)
    return ResponseMessage(200, 'Get eCTD file list successfully', data_info).to_json()

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

@app.route('/get_ectd_content/<ectd_key>', methods=['GET','POST'])
@cross_origin()
def get_ectd_content(ectd_key):
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

@app.route('/search_by_classification', methods=['GET','POST'])
def search_by_classification():
    pass

@app.route('/test', methods=['GET','POST'])
@cross_origin()
def test():
    data = {'content': '\n当前属于eCTD模块3.2.S.4.2分析方法部分\n2 溶解度\n2.1. 试药与试剂：甲醇\n2.2. 仪器与设备：秒表、电子分析天平(万分之一)、容量瓶、量筒、刻度吸管。\n2.3. 操作方法：\na) .水中溶解度： 精密称取本品1g,置于10ml具塞刻度试管中，加水1mL然后于25℃±2℃\n的水浴条件下每隔5分钟强力振摇30秒，观察30分钟，应完全溶解。\nb) .甲醇中的溶解度： 精密称取本品1g,置于10ml具塞刻度试管中，加水1mL然后于25℃±2℃\n的水浴条件下每隔5分钟强力振摇30秒，观察30分钟，应未完全溶解。\n精密称取本品1g,置于10ml具塞刻度试管中，加水9mL然后于25℃±2℃\n的条件下每隔5分钟强力振摇30秒，观察30分钟，应完全溶解。\n2.4.结果：本品在水中极易溶，在甲醇中易溶。', 'content_section': '3.2.S.4.2', 'review_require_list': ['1.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。', '2.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。', '1.依据相关指导原则简述各主要质量控制项目（如有关物质、异构体、残留溶剂、含量等）的分析方法筛选与确定的过程，并与现行版国内外药典收载方法参数列表对比。如有研究但未列入质量标准的项目，需一并提供分析方法描述、限度等。 ', '2.有关物质：简述分析方法筛选依据，明确色谱条件筛选所用样品（明确已知杂质信息，也可以采用粗品/粗品母液、合理设计降解试验样品等）及纯度，筛选项目及评价指标、考察结果等。如适用，列表对比自拟方法与药典方法检出能力（建议采用影响因素试验样品或加速试验样品、合理设计降解试验样品等），自拟方法的分离检出能力应不低于药典标准。提供专属性典型图谱（如系统适用性图谱、混合杂质对照品图谱等）。用表格形式表示：|有关物质|拟定注册标准|ChP（版本号）|BP（版本号）|USP（版本号）|EP（版本号）|其他|\n|方法|\n|色谱柱|\n|流动相及洗脱程序|\n|流速|\n|柱温|\n|检测波长|\n|进样体积|\n|稀释剂|\n|供试品溶液浓度|\n|对照（品）溶液浓度|\n|……|\n|定量方式', '3.如适用，请提供有关物质自拟方法与药典方法检出结果对比。', '4.研究但未订入标准的项目：参照中国药典格式提供各项目的分析方法。 ', "5. ['1.质量标准各项目分析方法的建立均应具有依据。', '2.有关物质分析方法筛选时，应在杂质谱分析全面的基础上，结合相关文献，科学选择分析方法。可以在原料药中加入限度浓度的已知杂质，证明拟定的有关物质分析方法可以单独分离目标杂质和/或使杂质与主成分有效分离；也可以采用含适量杂质的样品（如粗品或粗品母液、适当降解样品、稳定性末期样品等），对色谱条件进行比较优选研究，根据对杂质的检出能力选择适宜的色谱条件，建立有关物质分析方法。对于已有药典标准收载的，应结合原料药工艺路线分析药典标准分析方法的适用性，拟定的有关物质分析方法分离检出能力和杂质控制要求应不低于药典标准。', '3.同时，需关注稳定性考察期间总杂增加与含量下降的匹配性，如出现不匹配情况，需关注有关物质与含量测定分析方法的专属性、杂质校正因子影响等，必要时优化分析方法。 ']"], 'search_plan_list': [[{'question': '溶解度检测方法是否符合药典标准', 'tool': '分析方法检索工具', 'parameter': 'method_name=水中溶解度'}, {'question': '溶解度检测方法是否符合药典标准', 'tool': '分析方法检索工具', 'parameter': 'method_name=甲醇中溶解度'}], [{'question': '溶解度检测方法是否符合药典标准', 'tool': '分析方法检索工具', 'parameter': 'method_name=水中溶解度检测方法'}, {'question': '溶解度检测方法是否符合药典标准', 'tool': '分析方法检索工具', 'parameter': 'method_name=甲醇中溶解度检测方法'}], [{'question': '检索eCTD模块3.2.S.4.2中的指导原则信息', 'tool': '指导原则检索工具', 'parameter': ['eCTD_module=3.2.S.4.2', 'module_name=分析方法']}, {'question': '对比现行版国内外药典中关于溶解度的分析方法参数列表', 'tool': 'None', 'parameter': None}, {'question': '查询有关物质、异构体、残留溶剂、含量等质量控制项目的分析方法', 'tool': '分析方法检索工具', 'parameter': 'method_name=有关物质'}, {'question': '查询有关物质、异构体、残留溶剂、含量等质量控制项目的分析方法', 'tool': '分析方法检索工具', 'parameter': 'method_name=异构体'}, {'question': '查询有关物质、异构体、残留溶剂、含量等质量控制项目的分析方法', 'tool': '分析方法检索工具', 'parameter': 'method_name=残留溶剂'}, {'question': '查询有关物质、异构体、残留溶剂、含量等质量控制项目的分析方法', 'tool': '分析方法检索工具', 'parameter': 'method_name=含量'}], [{'question': '当前审评药品的已知杂质信息是什么？', 'tool': '分析方法检索工具', 'parameter': 'method_name=有关物质分析方法'}, {'question': '当前审评药品的自拟方法与药典方法的检出能力对比数据是什么？', 'tool': '药品信息检索工具', 'parameter': 'medicine_query=当前审评药品自拟方法与药典方法检出能力对比'}, {'question': '当前审评药品的色谱柱信息是什么？', 'tool': '分析方法检索工具', 'parameter': 'method_name=色谱柱选择依据'}, {'question': 'eCTD模块3.2.S.4.2分析方法部分的相关指导原则是什么？', 'tool': '指导原则检索工具', 'parameter': ['eCTD_module=3.2.S.4.2', 'module_name=分析方法']}], [{'question': '当前药品在水中和甲醇中的溶解度是否符合药典标准?', 'tool': '分析方法检索工具', 'parameter': 'method_name=水中溶解度'}, {'question': '当前药品在水中和甲醇中的溶解度是否符合药典标准?', 'tool': '分析方法检索工具', 'parameter': 'method_name=甲醇中溶解度'}, {'question': '药典中关于有关物质检测的方法是什么?', 'tool': '分析方法检索工具', 'parameter': 'method_name=有关物质检测'}], [{'question': '溶解度测定中使用的仪器是否需要精确控温?', 'tool': '指导原则检索工具', 'parameter': ['eCTD_module=3.2.S.4.2', 'module_name=分析方法']}, {'question': '是否需要提供溶解度测定的具体计算公式?', 'tool': '药品信息检索工具', 'parameter': 'medicine_query=本品在水和甲醇中的溶解度测定方法'}, {'question': '如何确定本品在不同溶剂中的溶解度分级标准?', 'tool': '分析方法检索工具', 'parameter': 'method_name=溶解度测定'}], [{'question': '分析方法是否需要结合药典标准进行验证', 'tool': '药品信息检索工具', 'parameter': 'medicine_query=溶解度分析方法的药典标准'}, {'question': '溶解度分析方法是否需要进一步优化', 'tool': '分析方法检索工具', 'parameter': 'method_name=溶解度分析方法'}, {'question': 'eCTD模块3.2.S.4.2部分是否需要引用特定的指导原则', 'tool': '指导原则检索工具', 'parameter': ['eCTD_module=3.2.S.4.2', 'module_name=分析方法']}]], 'search_list': [None, None, None, None, [{'response': [{'reference': '286fe8c4b60141da', 'content': '根据提供的数据片段，无法直接找到关于药品在水中和甲醇中溶解度是否符合药典标准的信息。'}, {'reference': '总结性回答', 'content': '综合所有数据片段，没有明确信息表明当前药品在水中和甲醇中的溶解度是否符合药典标准。如果需要确切的答案，建议查阅更详细的药品标准依据或相关实验报告。'}], 'reference': {'286fe8c4b60141da': {'file_name': '治疗用生物制品注册受理审查指南（试行）.docx', 'content': '18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。19.有效期：以月为单位填写。如有多个规格、包装材质，有效期如有不同则要分别对应填写，如包装材质为“玻璃瓶。塑料瓶”两种，有效期分别为18个月、12个月，应写为“18个月。12个月”。\n20.处方（含处方量）：应当使用规范的药物活性成份名称，同时应当填写按1000制剂单位计算的处方量，注明相应的制剂单位。\n21.原/辅料/包材来源或关联制剂：原材料应填写主要生物原材料，如原液。\n22.中药材标准：生物制品无需填写。\n23.药品标准依据：指本项药品申请所提交药品标准的来源或执行依据。来源于中国药典的，需写明药典版次；属局颁或部颁标准的，应写明药品标准编号；其他是指非以上来源的，应该写明具体来源，如自行研究，国产药品注册标准等情况。\n 18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。19.有效期：以月为单位填写。如有多个规格、包装材质，有效期如有不同则要分别对应填写，如包装材质为“玻璃瓶。塑料瓶”两种，有效期分别为18个月、12个月，应写为“18个月。12个月”。\n20.处方（含处方量）：应当使用规范的药物活性成份名称，同时应当填写按1000制剂单位计算的处方量，注明相应的制剂单位。\n21.原/辅料/包材来源或关联制剂：原材料应填写主要生物原材料，如原液。\n22.中药材标准：生物制品无需填写。\n23.药品标准依据：指本项药品申请所提交药品标准的来源或执行依据。来源于中国药典的，需写明药典版次；属局颁或部颁标准的，应写明药品标准编号；其他是指非以上来源的，应该写明具体来源，如自行研究，国产药品注册标准等情况。\n 18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。19.有效期：以月为单位填写。如有多个规格、包装材质，有效期如有不同则要分别对应填写，如包装材质为“玻璃瓶。塑料瓶”两种，有效期分别为18个月、12个月，应写为“18个月。12个月”。\n20.处方（含处方量）：应当使用规范的药物活性成份名称，同时应当填写按1000制剂单位计算的处方量，注明相应的制剂单位。\n21.原/辅料/包材来源或关联制剂：原材料应填写主要生物原材料，如原液。\n22.中药材标准：生物制品无需填写。\n23.药品标准依据：指本项药品申请所提交药品标准的来源或执行依据。来源于中国药典的，需写明药典版次；属局颁或部颁标准的，应写明药品标准编号；其他是指非以上来源的，应该写明具体来源，如自行研究，国产药品注册标准等情况。\n', 'classification': '法律法规'}}, 'query': '当前药品在水中和甲醇中的溶解度是否符合药典标准?'}, {'response': {'reference': '总结性回答', 'content': '根据提供的数据片段，无法直接找到关于当前药品在水中和甲醇中溶解度是否符合药典标准的具体信息。这些数据片段主要描述了药品包装、处方、标准依据等内容，并未提及溶解度的相关数据或药典的具体标准。'}, 'reference': {'286fe8c4b60141da': {'file_name': '治疗用生物制品注册受理审查指南（试行）.docx', 'content': '18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。19.有效期：以月为单位填写。如有多个规格、包装材质，有效期如有不同则要分别对应填写，如包装材质为“玻璃瓶。塑料瓶”两种，有效期分别为18个月、12个月，应写为“18个月。12个月”。\n20.处方（含处方量）：应当使用规范的药物活性成份名称，同时应当填写按1000制剂单位计算的处方量，注明相应的制剂单位。\n21.原/辅料/包材来源或关联制剂：原材料应填写主要生物原材料，如原液。\n22.中药材标准：生物制品无需填写。\n23.药品标准依据：指本项药品申请所提交药品标准的来源或执行依据。来源于中国药典的，需写明药典版次；属局颁或部颁标准的，应写明药品标准编号；其他是指非以上来源的，应该写明具体来源，如自行研究，国产药品注册标准等情况。\n 18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。19.有效期：以月为单位填写。如有多个规格、包装材质，有效期如有不同则要分别对应填写，如包装材质为“玻璃瓶。塑料瓶”两种，有效期分别为18个月、12个月，应写为“18个月。12个月”。\n20.处方（含处方量）：应当使用规范的药物活性成份名称，同时应当填写按1000制剂单位计算的处方量，注明相应的制剂单位。\n21.原/辅料/包材来源或关联制剂：原材料应填写主要生物原材料，如原液。\n22.中药材标准：生物制品无需填写。\n23.药品标准依据：指本项药品申请所提交药品标准的来源或执行依据。来源于中国药典的，需写明药典版次；属局颁或部颁标准的，应写明药品标准编号；其他是指非以上来源的，应该写明具体来源，如自行研究，国产药品注册标准等情况。\n 18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。19.有效期：以月为单位填写。如有多个规格、包装材质，有效期如有不同则要分别对应填写，如包装材质为“玻璃瓶。塑料瓶”两种，有效期分别为18个月、12个月，应写为“18个月。12个月”。\n20.处方（含处方量）：应当使用规范的药物活性成份名称，同时应当填写按1000制剂单位计算的处方量，注明相应的制剂单位。\n21.原/辅料/包材来源或关联制剂：原材料应填写主要生物原材料，如原液。\n22.中药材标准：生物制品无需填写。\n23.药品标准依据：指本项药品申请所提交药品标准的来源或执行依据。来源于中国药典的，需写明药典版次；属局颁或部颁标准的，应写明药品标准编号；其他是指非以上来源的，应该写明具体来源，如自行研究，国产药品注册标准等情况。\n', 'classification': '法律法规'}}, 'query': '当前药品在水中和甲醇中的溶解度是否符合药典标准?'}, {'response': [{'reference': '总结性回答', 'content': '药典中关于有关物质检测的方法通常包括色谱法（如高效液相色谱法HPLC）、光谱法（如紫外-可见分光光度法）、电泳法等。这些方法的选择取决于药物的具体性质、杂质的类型以及检测的灵敏度需求。'}, {'reference': '总结性回答', 'content': '在实际操作中，药典会提供详细的检测条件，例如流动相组成、检测波长、柱温、流速等参数，以确保检测结果的准确性和重复性。此外，药典还会规定具体的判断标准，用于确定药物中有关物质是否符合规定。'}], 'reference': {}, 'query': '药典中关于有关物质检测的方法是什么?'}], [['1.依据相关指导原则简述各主要质量控制项目（如有关物质、异构体、残留溶剂、含量等）的分析方法筛选与确定的过程，并与现行版国内外药典收载方法参数列表对比。如有研究但未列入质量标准的项目，需一并提供分析方法描述、限度等。 ', '2.有关物质：简述分析方法筛选依据，明确色谱条件筛选所用样品（明确已知杂质信息，也可以采用粗品/粗品母液、合理设计降解试验样品等）及纯度，筛选项目及评价指标、考察结果等。如适用，列表对比自拟方法与药典方法检出能力（建议采用影响因素试验样品或加速试验样品、合理设计降解试验样品等），自拟方法的分离检出能力应不低于药典标准。提供专属性典型图谱（如系统适用性图谱、混合杂质对照品图谱等）。用表格形式表示：|有关物质|拟定注册标准|ChP（版本号）|BP（版本号）|USP（版本号）|EP（版本号）|其他|\n|方法|\n|色谱柱|\n|流动相及洗脱程序|\n|流速|\n|柱温|\n|检测波长|\n|进样体积|\n|稀释剂|\n|供试品溶液浓度|\n|对照（品）溶液浓度|\n|……|\n|定量方式', '3.如适用，请提供有关物质自拟方法与药典方法检出结果对比。', '4.研究但未订入标准的项目：参照中国药典格式提供各项目的分析方法。 ', "5. ['1.质量标准各项目分析方法的建立均应具有依据。', '2.有关物质分析方法筛选时，应在杂质谱分析全面的基础上，结合相关文献，科学选择分析方法。可以在原料药中加入限度浓度的已知杂质，证明拟定的有关物质分析方法可以单独分离目标杂质和/或使杂质与主成分有效分离；也可以采用含适量杂质的样品（如粗品或粗品母液、适当降解样品、稳定性末期样品等），对色谱条件进行比较优选研究，根据对杂质的检出能力选择适宜的色谱条件，建立有关物质分析方法。对于已有药典标准收载的，应结合原料药工艺路线分析药典标准分析方法的适用性，拟定的有关物质分析方法分离检出能力和杂质控制要求应不低于药典标准。', '3.同时，需关注稳定性考察期间总杂增加与含量下降的匹配性，如出现不匹配情况，需关注有关物质与含量测定分析方法的专属性、杂质校正因子影响等，必要时优化分析方法。 ']"], {'response': [{'reference': None, 'content': '溶解度测定的具体计算公式通常取决于所采用的实验方法和具体的化学体系。常见的溶解度测定方法包括重量法、容量法、分光光度法等，每种方法可能需要不同的计算公式。因此，在进行溶解度测定之前，需要明确所用的方法，并参考相应的方法学指导来确定具体的计算公式。'}, {'reference': None, 'content': '如果没有特定的数据片段支持，可以根据一般科学实践建议，当进行溶解度测定研究时，确保记录详细的实验条件和使用适当的公式来处理数据，以便获得准确的结果。'}], 'reference': {}, 'query': '是否需要提供溶解度测定的具体计算公式?'}, {'response': [{'reference': '总结性回答', 'content': '确定本品在不同溶剂中的溶解度分级标准通常需要参考相关的药品标准依据，比如中国药典或其他官方颁布的标准。此外，还需要明确制剂的类型、规格、包装材质和规格、有效期、处方组成及用量等信息，这些都会影响到溶解度分级标准的制定。'}, {'reference': '总结性回答', 'content': '在实际操作中，溶解度分级标准的确定可能涉及实验室测试和数据分析，以确保药品在不同溶剂中的稳定性和有效性符合相关法规要求。具体的测定方法和分级标准可以参照国家药品监督管理部门发布的指导原则或行业标准。'}], 'reference': {'9321d179f9be44bd': {'file_name': '化学药品注册受理审查指南（第二部分 注册分类4、5.2）（试行）.docx', 'content': '15.制剂类型：制剂在“剂型”后选择所属剂型；剂型属于《中国药典》或其增补本收载的剂型，选中国药典剂型；非属《中国药典》现行版及其增补本未收载的剂型，选非中国药典剂型；如属于靶向制剂、缓释、控释制剂等特殊制剂的，可同时选择特殊剂型。16.规格：填写本制剂单剂量包装的规格，使用药典规定的单位符号。例如“克”应写为“g”，“克/毫升”应填写为“g/ml”。每一规格填写一份申请表，多个规格应分别填写申请表。\n17.同品种已被受理或同期申报的原料药、制剂或不同规格品种：填写该品种已被受理或关联审批的其他原料药、辅料、药包材、制剂或不同规格品种的受理号及名称。若为完成临床研究申请生产的需填写原临床申请受理号、临床试验批件号、临床试验登记号或生物等效性试验备案号等。\n18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×片，每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器、输液器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。\n', 'classification': '法律法规'}, '286fe8c4b60141da': {'file_name': '治疗用生物制品注册受理审查指南（试行）.docx', 'content': '18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。19.有效期：以月为单位填写。如有多个规格、包装材质，有效期如有不同则要分别对应填写，如包装材质为“玻璃瓶。塑料瓶”两种，有效期分别为18个月、12个月，应写为“18个月。12个月”。\n20.处方（含处方量）：应当使用规范的药物活性成份名称，同时应当填写按1000制剂单位计算的处方量，注明相应的制剂单位。\n21.原/辅料/包材来源或关联制剂：原材料应填写主要生物原材料，如原液。\n22.中药材标准：生物制品无需填写。\n23.药品标准依据：指本项药品申请所提交药品标准的来源或执行依据。来源于中国药典的，需写明药典版次；属局颁或部颁标准的，应写明药品标准编号；其他是指非以上来源的，应该写明具体来源，如自行研究，国产药品注册标准等情况。\n 18.包装：如有多个包装材质要分别填写，中间用句号分开，例如“玻璃瓶。塑料瓶”。包装规格：是药品生产企业生产供上市的药品最小包装，如：每瓶×毫升，每盒×支，对于按含量或浓度标示其规格的液体、半固体制剂或颗粒剂，其装量按包装规格填写。配用注射器或者专用溶媒的，也应在此处填写。每一份申请表可填写多个包装规格。19.有效期：以月为单位填写。如有多个规格、包装材质，有效期如有不同则要分别对应填写，如包装材质为“玻璃瓶。塑料瓶”两种，有效期分别为18个月、12个月，应写为“18个月。12个月”。\n20.处方（含处方量）：应当使用规范的药物活性成份名称，同时应当填写按1000制剂单位计算的处方量，注明相应的制剂单位。\n21.原/辅料/包材来源或关联制剂：原材料应填写主要生物原材料，如原液。\n22.中药材标准：生物制品无需填写。\n23.药品标准依据：指本项药品申请所提交药品标准的来源或执行依据。来源于中国药典的，需写明药典版次；属局颁或部颁标准的，应写明药品标准编号；其他是指非以上来源的，应该写明具体来源，如自行研究，国产药品注册标准等情况。\n', 'classification': '法律法规'}}, 'query': '如何确定本品在不同溶剂中的溶解度分级标准?'}], [{'response': [{'reference': '286fe8c4b60141da', 'content': '从提供的数据片段来看，关于药物研发和临床试验的相关规范中，并未直接提及分析方法需要结合药典标准进行验证的具体要求。但是，这并不意味着药典标准不重要。药典标准通常作为药品质量控制的重要依据，在药物的研发、生产和质控环节中具有指导意义。'}, {'reference': '总结性回答', 'content': '虽然提供的数据片段没有明确指出分析方法需要结合药典标准进行验证，但药典标准在药品质量控制中的作用不可忽视。因此，在实际操作中，结合药典标准对分析方法进行验证通常是必要的，以确保药品的质量和安全性符合法规和行业标准的要求。'}], 'reference': {'286fe8c4b60141da': {'file_name': '治疗用生物制品注册受理审查指南（试行）.docx', 'content': '2.6.4申请国际多中心临床试验的，应提供其临床试验用药物在符合药品生产质量管理规范的条件下制备的情况说明。3.其他申报资料\n3.1其他申报资料应按照《药品注册管理办法》附件3逐项提交，不适用的应予以标注。\n3.2非临床安全性评价研究必须在经过《药物非临床研究质量管理规范》（简称GLP）认证，符合GLP要求的机构进行，应提供GLP符合性声明。\n3.3提交新药临床试验申请的，还需提交与总局药审中心会议沟通意见建议以及申报资料补充完善的情况说明。\n3.4临床试验报告封面应包括受试药物通用名、研究类型、研究编号、研究开始日期、研究完成日期、主要研究者（签名）、研究单位（盖章）、统计学负责人签名及单位盖章、药品注册申请人（盖章）、注册申请人的联系人及联系方式、报告日期、原始资料保存地点，并应加盖临床研究基地有效公章，印章应加盖在文字处，并符合国家有关用章规定，具有法律效力。\n 2.6.4申请国际多中心临床试验的，应提供其临床试验用药物在符合药品生产质量管理规范的条件下制备的情况说明。3.其他申报资料\n3.1其他申报资料应按照《药品注册管理办法》附件3逐项提交，不适用的应予以标注。\n3.2非临床安全性评价研究必须在经过《药物非临床研究质量管理规范》（简称GLP）认证，符合GLP要求的机构进行，应提供GLP符合性声明。\n3.3提交新药临床试验申请的，还需提交与总局药审中心会议沟通意见建议以及申报资料补充完善的情况说明。\n3.4临床试验报告封面应包括受试药物通用名、研究类型、研究编号、研究开始日期、研究完成日期、主要研究者（签名）、研究单位（盖章）、统计学负责人签名及单位盖章、药品注册申请人（盖章）、注册申请人的联系人及联系方式、报告日期、原始资料保存地点，并应加盖临床研究基地有效公章，印章应加盖在文字处，并符合国家有关用章规定，具有法律效力。\n', 'classification': '法律法规'}}, 'query': '分析方法是否需要结合药典标准进行验证'}, {'response': [{'reference': None, 'content': '根据现有数据片段，没有提供关于溶解度分析方法的具体信息或相关研究进展。因此，无法直接判断溶解度分析方法是否需要进一步优化。'}, {'reference': None, 'content': '由于数据片段中未包含任何与溶解度分析方法相关的实验数据、技术细节或优化案例，我们无法得出明确结论。若要判断是否需要优化，建议补充更多背景信息和技术资料。'}], 'reference': {}, 'query': '溶解度分析方法是否需要进一步优化'}, ['1.依据相关指导原则简述各主要质量控制项目（如有关物质、异构体、残留溶剂、含量等）的分析方法筛选与确定的过程，并与现行版国内外药典收载方法参数列表对比。如有研究但未列入质量标准的项目，需一并提供分析方法描述、限度等。 ', '2.有关物质：简述分析方法筛选依据，明确色谱条件筛选所用样品（明确已知杂质信息，也可以采用粗品/粗品母液、合理设计降解试验样品等）及纯度，筛选项目及评价指标、考察结果等。如适用，列表对比自拟方法与药典方法检出能力（建议采用影响因素试验样品或加速试验样品、合理设计降解试验样品等），自拟方法的分离检出能力应不低于药典标准。提供专属性典型图谱（如系统适用性图谱、混合杂质对照品图谱等）。用表格形式表示：|有关物质|拟定注册标准|ChP（版本号）|BP（版本号）|USP（版本号）|EP（版本号）|其他|\n|方法|\n|色谱柱|\n|流动相及洗脱程序|\n|流速|\n|柱温|\n|检测波长|\n|进样体积|\n|稀释剂|\n|供试品溶液浓度|\n|对照（品）溶液浓度|\n|……|\n|定量方式', '3.如适用，请提供有关物质自拟方法与药典方法检出结果对比。', '4.研究但未订入标准的项目：参照中国药典格式提供各项目的分析方法。 ', "5. ['1.质量标准各项目分析方法的建立均应具有依据。', '2.有关物质分析方法筛选时，应在杂质谱分析全面的基础上，结合相关文献，科学选择分析方法。可以在原料药中加入限度浓度的已知杂质，证明拟定的有关物质分析方法可以单独分离目标杂质和/或使杂质与主成分有效分离；也可以采用含适量杂质的样品（如粗品或粗品母液、适当降解样品、稳定性末期样品等），对色谱条件进行比较优选研究，根据对杂质的检出能力选择适宜的色谱条件，建立有关物质分析方法。对于已有药典标准收载的，应结合原料药工艺路线分析药典标准分析方法的适用性，拟定的有关物质分析方法分离检出能力和杂质控制要求应不低于药典标准。', '3.同时，需关注稳定性考察期间总杂增加与含量下降的匹配性，如出现不匹配情况，需关注有关物质与含量测定分析方法的专属性、杂质校正因子影响等，必要时优化分析方法。 ']"]]], 'review_result_list': [{'conclusion': {'content': '根据提供的检测方法描述，溶解度测试采用了标准的实验操作步骤，包括精密称量、控制温度（25℃±2℃）、定时振摇（每隔5分钟强力振摇30秒）以及观察时间（30分钟），这些操作均符合一般化学分析的基本规范。此外，该方法区分了两种溶剂（水和甲醇）下的溶解行为，并通过观察是否“完全溶解”或“未完全溶解”来判断溶解度，这种分类方式合理且具有科学依据。                虽然没有直接引用药典或其他标准文件的具体条目，但所采用的操作流程与常见的药物溶解性测试方法一致，能够有效评估物质在不同介质中的溶解特性。因此，该检测方法具备合理性。                **建议**：若条件允许，可进一步明确操作过程中的具体细节（如振摇强度等），并考虑增加平行试验以提高数据可靠性。', 'reference': '无可用参考信息'}}, {'conclusion': {'content': '根据审评要求，需要验证检测方法的合理性。待审评内容中描述了两种溶解度测定方法：水中的溶解度和甲醇中的溶解度。这些方法详细描述了操作步骤，包括使用的仪器设备、试药试剂以及具体的实验条件（如温度、振摇频率等）。虽然提供的检索信息中没有直接引用药典或其他标准方法，但所描述的方法具有科学性和合理性，符合一般化学分析的基本原则。例如，使用精确称量、控制温度和振摇条件等措施能够有效评估物质的溶解性能。                因此，可以认为该检测方法是合理的，并且适用于评估样品在不同溶剂中的溶解性。                **注意**：尽管方法合理，但在实际应用中仍建议参考相关药典或行业标准，以确保方法的一致性和权威性。', 'reference': '无可用参考信息'}}, {'conclusion': {'content': '根据提供的待审评内容和审评要求，该部分属于eCTD模块3.2.S.4.2分析方法部分，主要涉及溶解度的测定。以下是对溶解度分析方法的审评结论：1. **分析方法的合理性**     - 水中溶解度和甲醇中溶解度的测定均采用了精密称量、恒温水浴、强力振摇的操作步骤，符合一般溶解度测定的基本要求。通过对比30分钟内的溶解情况，能够较为准确地判断溶解性。   - 方法中明确指定了试验条件（如温度、时间间隔等），操作步骤清晰且可重复。2. **与现行版国内外药典的对比**     - 提供的检索信息中未包含相关药典内容，因此无法直接与现行版国内外药典收载的方法参数列表进行对比。若后续有更多药典资料补充，建议进一步对比分析。3. **结论**     - 当前溶解度测定方法的设计合理，操作步骤明确，能够有效评估本品在水和甲醇中的溶解特性。   - 建议在后续工作中，补充与现行版国内外药典方法的对比数据，确保分析方法的一致性和科学性。', 'reference': '无可用检索信息'}}, {'conclusion': {'content': '根据审评要求，当前内容属于eCTD模块3.2.S.4.2分析方法部分，但并未涉及有关物质分析方法的相关信息，也未提供色谱条件、样品信息、药典对比等内容。因此，无法满足审评要求中关于有关物质分析方法的详细说明和表格填写需求。                                  综上所述，该部分内容不完整，需补充以下信息：                - 明确有关物质分析方法的筛选依据；                - 提供色谱条件及相关参数（如色谱柱、流动相、流速、柱温、检测波长等）；                - 列表对比自拟方法与药典方法的检出能力；                - 提供专属性典型图谱；                - 填写相关表格并补充完整信息。'}}, {'conclusion': {'content': '根据现有信息，待审评内容中提供了药品在水中和甲醇中的溶解度试验方法及结果，但并未提及具体的药典标准或与药典方法的对比。因此，无法确认该药品的溶解度是否符合药典标准。                                  **结论**：当前提供的溶解度数据未与药典方法进行对比验证，无法判断是否符合药典要求。若需进一步确认，建议补充药典方法的检测结果并与自拟方法进行比对。                **参考材料**：                - reference: 总结性回答', 'reference': '总结性回答'}}, {'conclusion': {'content': '根据提供的待审评内容，溶解度测定的操作方法详细描述了试药与试剂、仪器与设备、以及具体的实验步骤，并且明确给出了结果判定标准。以下是对该部分内容的分析和结论：1. **溶解度测定方法的合理性**     - 实验步骤清晰，涵盖了水中和甲醇中溶解度的测定，通过振摇和观察的方式验证溶解状态，符合中国药典中关于溶解度测定的基本要求。   - 测定条件（如温度、时间）设置合理，能够保证实验数据的准确性。2. **结果判定的准确性**     - 在水中，“应完全溶解”的结果判定符合“极易溶”的定义。   - 在甲醇中，“应未完全溶解”且“应完全溶解”的组合判定符合“易溶”的定义。   - 结果表述与预期一致，满足“研究但未订入标准的项目”的要求。3. **参考标准**     依据中国药典的相关指导原则，溶解度测定应明确分级标准，并与药典标准对比。虽然具体内容未提及具体药典版本，但实验方法和结果符合一般药典要求。综上所述，溶解度测定部分的操作方法和结果判定合理，符合中国药典格式要求，可作为未订入标准的项目分析方法。**参考文献：**- 中国药典关于溶解度测定的相关指导原则。- 检索信息中关于溶解度分级标准制定的原则。', 'reference': ['9321d179f9be44bd', '286fe8c4b60141da']}}, {'conclusion': {'content': '根据审评要求，分析方法的建立应当具有充分的依据，并且在涉及已有药典标准的情况下，拟定的方法应不低于药典标准的要求。对于溶解度分析方法，提供的内容描述了水和甲醇中溶解度的操作步骤，包括试药、仪器设备、操作流程及预期结果。然而，对比审评要求中的第2条，该分析方法并未提及是否基于全面的杂质谱分析或与药典标准进行对比验证。尽管提供的操作步骤较为详细，但在现有材料中未发现明确结合药典标准的验证过程。                综上所述，虽然溶解度分析方法提供了具体的操作步骤，但从审评要求的角度看，缺乏对药典标准的对比和验证，这可能影响方法的科学性和可靠性。', 'reference': '参考1'}}], 'report_require_list': ['1.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。'], 'final_report': [{'report': {'content': '## 检测方法合理性说明                                ### 已知信息                根据提供的待审评内容，检测方法主要涉及水中和甲醇中溶解度的测定。检测步骤明确，包括试药与试剂的选择、仪器与设备的使用以及操作方法的详细描述。                ### 方法合理性分析                1. **试药与试剂选择**                     - 使用甲醇作为溶剂进行溶解度测试是合理的，因为甲醇是一种常用的有机溶剂，广泛应用于药物溶解性研究。                     - 水作为对照溶剂也符合常规检测标准，因为水是最常见的生物相关介质之一，其溶解性数据对于评估药物的生物利用度至关重要。                2. **仪器与设备选择**                     - 所用仪器如秒表、电子分析天平（万分之一）、容量瓶、量筒等均为通用且高精度设备，能够满足溶解度测试的需求。                     - 具塞刻度试管的设计有助于确保实验过程中样品与溶剂混合的均匀性和密封性，减少外界环境对实验结果的影响。                3. **操作方法合理性**                     - 实验采用“强力振摇30秒”的方式模拟实际溶解过程，符合《中国药典》等相关规范中关于溶解度测定的操作要求。                     - 测试条件（25℃±2℃）也符合药物溶解度研究的标准温度范围，能够反映药物在接近人体生理条件下的溶解性能。                     - 通过间隔时间记录溶解情况（每5分钟观察一次），并持续观察30分钟，确保了实验数据的准确性和可靠性。                综上所述，该检测方法具有科学性和合理性，符合相关行业标准和实际需求。                ### 参考依据                  - 检测方法参考了《中国药典》中关于溶解度测定的相关规定。                  - 操作细节符合常规药物溶解度研究的技术要求。', 'reference': ['参考1', '参考2']}}, {'report': {'content': '### 检测方法合理性分析                **检测方法概述**                  本检测方法针对药品在不同溶剂中的溶解度进行评估，包括水中溶解度和甲醇中溶解度的测定。操作步骤清晰，通过控制温度（25℃±2℃）和时间间隔（每隔5分钟强力振摇30秒），确保实验条件的一致性，同时通过肉眼观察30分钟内的溶解情况，对溶解度进行定性判断。                **合理性分析**                  1. 药物溶解度的测定通常不直接依据药典标准方法，但本方法的设计符合一般化学分析原则，具有科学性和合理性。                  2. 使用具塞刻度试管并精密称量样品，确保了称样量的准确性，避免因称量误差导致的结果偏差。                  3. 温度控制在25℃±2℃范围内，符合药物溶解度研究的常规条件，能够反映药物在接近室温环境下的真实溶解行为。                  4. 强力振摇的操作模拟了实际使用场景中的搅拌效应，有助于加速溶解过程，提高实验效率和数据可靠性。                  5. 对比水和甲醇两种溶剂的溶解度测试，能够全面评估药物的溶解特性，为后续制剂开发提供重要参考。                **结论**                  综上所述，本检测方法设计合理且操作规范，能够准确反映药品在不同溶剂中的溶解性能，无需进一步修改即可应用于正式研究中。                *参考1：检测方法符合一般化学分析原则。*                  *参考2：实验条件与药物理化性质相匹配，结果可信。*', 'reference': ['参考1', '参考2']}}, {'report': {'content': {'reference': '参考1', '#text': '### 分析方法合理性说明                **检测方法概述**                  本分析方法用于评估产品在水和甲醇两种溶剂中的溶解度特性。操作步骤包括精密称取样品，并在严格控制的温度（25℃±2℃）条件下，通过强力振摇（每5分钟振摇30秒）模拟实际环境条件下的溶解过程，随后观察30分钟以记录溶解情况。                **合理性分析**                  - 该方法符合药物溶解度测定的一般原则，即在一定条件下观察物质是否能够完全或部分溶解，从而确定其溶解性分类。                - 使用具塞刻度试管、电子分析天平等标准化实验器材确保了实验的准确性和可重复性。                - 水浴控温系统保证了温度的一致性，这对于溶解度测定至关重要，因为温度变化会显著影响溶解速率和程度。                - 方法中对不同溶剂（水和甲醇）分别设定了不同的加入比例（如水1mL vs. 9mL），这有助于全面评估样品在不同浓度条件下的溶解行为。                **药典对比**                  本方法并未直接引用《中国药典》或其他国际通用药典的具体条目，但其设计原理与药典推荐的溶解度测定方法一致，均采用动态振摇结合静态观察的方式进行测试。此外，对于溶剂的选择及配比也符合常规溶解度研究的基本规范。                综上所述，本方法具有科学性和合理性，能够有效反映样品在指定条件下的溶解性能。                **结论**                  根据上述分析，本方法合理且适用于评估样品的溶解度特性。参考审评结论中提到的结果：“本品在水中极易溶，在甲醇中易溶”，进一步验证了该方法的有效性。'}}}]}
    return ResponseMessage(200, 'Review completed', data).to_json()

@app.route('/test_search', methods=['GET','POST'])
@cross_origin()
def test_search():
    data = {
    "response": [
        {
            "reference": "2752bc8ee7fd4901",
            "content": "在申请新药首次药物临床试验时，需要确保药物临床试验在具备相应条件并按规定备案的药物临床试验机构开展。此外，药物临床试验应当经伦理委员会审查同意，并遵守药物临床试验质量管理规范。"
        },
        {
            "reference": "25d651f2459f4f68",
            "content": "申请人完成支持药物临床试验的药学、药理毒理学等研究后，需提出药物临床试验申请，并提交相关研究资料。药品审评中心应在受理之日起六十日内决定是否同意开展，并通过网站通知申请人审批结果。若逾期未通知，则视为同意，申请人可以按照提交的方案开展药物临床试验。"
        }
    ],
    "reference": {
        "25d651f2459f4f68": {
            "file_name": "化学药品注册受理审查指南（第一部分 注册分类1、2、3、5.1）（试行）.docx",
            "content": "1.1.5完成临床试验后申报生产时应当提供《药物临床试验批件》复印件、临床试验登记与信息公示或生物等效性试验备案号等相关材料，以及临床试验用药的质量标准。1.1.6原料药的合法来源证明文件，包括原料药的批准证明文件、药品标准、检验报告、原料药生产企业的营业执照、《药品生产许可证》、《药品生产质量管理规范》认证证书、销售发票、供货协议等的复印件。\n1.1.7辅料的合法来源证明文件，包括辅料的批准证明文件（含有效的药用辅料注册证、核准编号或实行关联审批的药用辅料《受理通知书》等）、标准、检验报告、辅料生产企业的营业执照、《药品生产许可证》、销售发票、供货协议等的复印件。\n1.1.8直接接触药品的包装材料和容器的《药品包装材料和容器注册证》或者《进口包装材料和容器注册证》复印件、核准编号或实行关联审批的药包材《受理通知书》等。\n不得使用天然胶塞，不得使用安瓿装粉针剂。注射剂用玻璃包材需符合国家食品药品监督管理总局颁布的“食药监办注〔2012〕132号”文规定。\n1.1.9委托研究相关证明文件\n",
            "classification": "现行药品注册法规汇总"
        },
        "55831925e11b4e4f": {
            "file_name": "治疗用生物制品注册受理审查指南（试行）.docx",
            "content": "2.6.4申请国际多中心临床试验的，应提供其临床试验用药物在符合药品生产质量管理规范的条件下制备的情况说明。3.其他申报资料\n3.1其他申报资料应按照《药品注册管理办法》附件3逐项提交，不适用的应予以标注。\n3.2非临床安全性评价研究必须在经过《药物非临床研究质量管理规范》（简称GLP）认证，符合GLP要求的机构进行，应提供GLP符合性声明。\n3.3提交新药临床试验申请的，还需提交与总局药审中心会议沟通意见建议以及申报资料补充完善的情况说明。\n3.4临床试验报告封面应包括受试药物通用名、研究类型、研究编号、研究开始日期、研究完成日期、主要研究者（签名）、研究单位（盖章）、统计学负责人签名及单位盖章、药品注册申请人（盖章）、注册申请人的联系人及联系方式、报告日期、原始资料保存地点，并应加盖临床研究基地有效公章，印章应加盖在文字处，并符合国家有关用章规定，具有法律效力。\n",
            "classification": "现行药品注册法规汇总"
        },
        "2752bc8ee7fd4901": {
            "file_name": "药品注册管理办法.docx",
            "content": "。\n       第十条  申请人在申请药品上市注册前，应当完成药学、药理毒理学和药物临床试验等相关研究工作。药物非临床安全性评价研究应当在经过药物非临床研究质量管理规范认证的机构开展，并遵守药物非临床研究质量管理规范。药物临床试验应当经批准，其中生物等效性试验应当备案；药物临床试验应当在符合相关规定的药物临床试验机构开展，并遵守药物临床试验质量管理规范。\n       申请药品注册，应当提供真实、充分、可靠的数据、资料和样品，证明药品的安全性、有效性和质量可控性。\n       使用境外研究资料和数据支持药品注册的，其来源、研究机构或者实验室条件、质量体系要求及其他管理条件等应当符合国际人用药品注册技术要求协调会通行原则，并符合我国药品注册管理的相关要求。\n       第十一条  变更原药品注册批准证明文件及其附件所载明的事项或者内容的，申请人应当按照规定，参照相关技术指导原则，对药品变更进行充分研究和验证，充分评估变更可能对药品安全性、有效性和质量可控性的影响，按照变更程序提出补充申请、备案或者报告。\n       第十二条  药品注册证书有效期为五年，药品注册证书有效期内持有人应当持续保证上市药品的安全性、有效性和质量可控性，并在有效期届满前六个月申请药品再注册。\n       第十三条  国家药品监督管理局建立药品加快上市注册制度，支持以临床价值为导向的药物创新。对符合条件的药品注册申请，申请人可以申请适用突破性治疗药物、附条件批准、优先审评审批及特别审批程序。在药品研制和注册过程中，药品监督管理部门及其专业技术机构给予必要的技术指导、沟通交流、优先配置资源、缩短审评时限等政策和技术支持。\n       第十四条  国家药品监督管理局建立化学原料药、辅料及直接接触药品的包装材料和容器关联审评审批制度。在审批药品制剂时，对化学原料药一并审评审批，对相关辅料、直接接触药品的包装材料和容器一并审评。药品审评中心建立化学原料药、辅料及直接接触药品的包装材料和容器信息登记平台，对相关登记信息进行公示，供相关申请人或者持有人选择，并在相关药品制剂注册申请审评时关联审评。\n       第十五条  处方药和非处方药实行分类注册和转换管理。药品审评中心根据非处方药的特点，制定非处方药上市注册相关技术指导原则和程序，并向社会公布。药品评价中心制定处方药和非处方药上市后转换相关技术要求和程序，并向社会公布。\n       第十六条  申请人在药物临床试验申请前、药物临床试验过程中以及药品上市许可申请前等关键阶段，可以就重大问题与药品审评中心等专业技术机构进行沟通交流。药品注册过程中，药品审评中心等专业技术机构可以根据工作需要组织与申请人进行沟通交流。\n       沟通交流的程序、要求和时限，由药品审评中心等专业技术机构依照职能分别制定，并向社会公布。\n       第十七条  药品审评中心等专业技术机构根据工作需要建立专家咨询制度，成立专家咨询委员会，在审评、核查、检验、通用名称核准等过程中就重大问题听取专家意见，充分发挥专家的技术支撑作用。\n       第十八条  国家药品监督管理局建立收载新批准上市以及通过仿制药质量和疗效一致性评价的化学药品目录集，载明药品名称、活性成分、剂型、规格、是否为参比制剂、持有人等相关信息，及时更新并向社会公开。化学药品目录集收载程序和要求，由药品审评中心制定，并向社会公布。\n       第十九条  国家药品监督管理局支持中药传承和创新，建立和完善符合中药特点的注册管理制度和技术评价体系，鼓励运用现代科学技术和传统研究方法研制中药，加强中药质量控制，提高中药临床试验水平。\n       中药注册申请，申请人应当进行临床价值和资源评估，突出以临床价值为导向，促进资源可持续利用。\n第三章  药品上市注册\n       第一节 药物临床试验\n       第二十条  本办法所称药物临床试验是指以药品上市注册为目的，为确定药物安全性与有效性在人体开展的药物研究。\n       第二十一条  药物临床试验分为Ⅰ期临床试验、Ⅱ期临床试验、Ⅲ期临床试验、Ⅳ期临床试验以及生物等效性试验。根据药物特点和研究目的，研究内容包括临床药理学研究、探索性临床试验、确证性临床试验和上市后研究。\n       第二十二条  药物临床试验应当在具备相应条件并按规定备案的药物临床试验机构开展。其中，疫苗临床试验应当由符合国家药品监督管理局和国家卫生健康委员会规定条件的三级医疗机构或者省级以上疾病预防控制机构实施或者组织实施。\n       第二十三条  申请人完成支持药物临床试验的药学、药理毒理学等研究后，提出药物临床试验申请的，应当按照申报资料要求提交相关研究资料。经形式审查，申报资料符合要求的，予以受理。药品审评中心应当组织药学、医学和其他技术人员对已受理的药物临床试验申请进行审评。对药物临床试验申请应当自受理之日起六十日内决定是否同意开展，并通过药品审评中心网站通知申请人审批结果；逾期未通知的，视为同意，申请人可以按照提交的方案开展药物临床试验。\n       申请人获准开展药物临床试验的为药物临床试验申办者（以下简称申办者）。\n       第二十四条  申请人拟开展生物等效性试验的，应当按照要求在药品审评中心网站完成生物等效性试验备案后，按照备案的方案开展相关研究工作。\n       第二十五条  开展药物临床试验，应当经伦理委员会审查同意。\n       药物临床试验用药品的管理应当符合药物临床试验质量管理规范的有关要求。\n       第二十六条  获准开展药物临床试验的，申办者在开展后续分期药物临床试验前，应当制定相应的药物临床试验方案，经伦理委员会审查同意后开展，并在药品审评中心网站提交相应的药物临床试验方案和支持性资料。\n       第二十七条  获准开展药物临床试验的药物拟增加适应症（或者功能主治）以及增加与其他药物联合用药的，申请人应当提出新的药物临床试验申请，经批准后方可开展新的药物临床试验。\n       获准上市的药品增加适应症（或者功能主治）需要开展药物临床试验的，应当提出新的药物临床试验申请。\n       第二十八条  申办者应当定期在药品审评中心网站提交研发期间安全性更新报告。研发期间安全性更新报告应当每年提交一次，于药物临床试验获准后每满一年后的两个月内提交。药品审评中心可以根据审查情况，要求申办者调整报告周期。\n       对于药物临床试验期间出现的可疑且非预期严重不良反应和其他潜在的严重安全性风险信息，申办者应当按照相关要求及时向药品审评中心报告。根据安全性风险严重程度，可以要求申办者采取调整药物临床试验方案、知情同意书、研究者手册等加强风险控制的措施，必要时可以要求申办者暂停或者终止药物临床试验。\n       研发期间安全性更新报告的具体要求由药品审评中心制定公布。\n       第二十九条  药物临床试验期间，发生药物临床试验方案变更、非临床或者药学的变化或者有新发现的，申办者应当按照规定，参照相关技术指导原则，充分评估对受试者安全的影响。\n       申办者评估认为不影响受试者安全的，可以直接实施并在研发期间安全性更新报告中报告。可能增加受试者安全性风险的，应当提出补充申请。对补充申请应当自受理之日起六十日内决定是否同意，并通过药品审评中心网站通知申请人审批结果；逾期未通知的，视为同意。\n       申办者发生变更的，由变更后的申办者承担药物临床试验的相关责任和义务。\n       第三十条  药物临床试验期间，发现存在安全性问题或者其他风险的，申办者应当及时调整临床试验方案、暂停或者终止临床试验，并向药品审评中心报告。\n       有下列情形之一的，可以要求申办者调整药物临床试验方案、暂停或者终止药物临床试验：\n       （一）伦理委员会未履行职责的；\n       （",
            "classification": "现行药品注册法规汇总"
        }
    },
    "query": "新药首次药物临床试申请有什么注意事项"
    }
    return ResponseMessage(200, 'Search completed', data).to_json()

@app.route('/test_single_review', methods=['GET','POST'])
@cross_origin()
def test_single_review():
    data = {'content': '\n当前属于eCTD模块3.2.S.4.2分析方法部分\n2 溶解度\n2.1. 试药与试剂：甲醇\n2.2. 仪器与设备：秒表、电子分析天平(万分之一)、容量瓶、量筒、刻度吸管。\n2.3. 操作方法：\na) .水中溶解度： 精密称取本品1g,置于10ml具塞刻度试管中，加水1mL然后于25℃±2℃\n的水浴条件下每隔5分钟强力振摇30秒，观察30分钟，应完全溶解。\nb) .甲醇中的溶解度： 精密称取本品1g,置于10ml具塞刻度试管中，加水1mL然后于25℃±2℃\n的水浴条件下每隔5分钟强力振摇30秒，观察30分钟，应未完全溶解。\n精密称取本品1g,置于10ml具塞刻度试管中，加水9mL然后于25℃±2℃\n的条件下每隔5分钟强力振摇30秒，观察30分钟，应完全溶解。\n2.4.结果：本品在水中极易溶，在甲醇中易溶。', 'review_require_list': ['1.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。', '2.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。'], 'search_plan_list': [[{'tool': '指导原则检索工具', 'parameter': ['eCTD_module=3.2.S.4.2', 'module_name=分析方法', 'principle_name=药典标准检测方法']}], [{'tool': '指导原则检索工具', 'parameter': ['eCTD_module=3.2.S.4.2', 'module_name=分析方法', 'principle_name=药典标准检测方法']}]], 'search_list': [[['reference', 'content']], [['reference', 'content']]], 'review_result_list': [{'conclusion': {'content': '待审评内容的检测方法合理，水中溶解度的测试方法符合常规测试流程，通过25℃±2℃的水浴条件下强力振摇，确保样品充分溶解，操作方法符合规范。甲醇中的溶解度测试方法同样合理，通过逐步增加水量，观察样品溶解情况，可以准确判断溶解度。虽然本方法未直接引用药典检测方法，但操作步骤合理，符合溶解度测定的科学原理。', 'reference': '参考1'}}, {'conclusion': {'content': '待审评内容中关于溶解度检测的方法是合理的。虽然未直接引用药典中的检测方法，但操作方法详细描述了水中和甲醇中的溶解度测试步骤，符合溶解度测定的常规流程。水中溶解度测试通过强力振摇确保药物完全溶解，而甲醇中的溶解度测试则通过增加溶剂体积来确保未完全溶解。这种设计可以有效地比较药物在不同溶剂中的溶解性，从而评估其溶解度。没有发现检索信息中的内容与此相矛盾。', 'reference': 'reference1'}}], 'report_require_list': ['1.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。'], 'final_report': [{'report': {'content': '检测方法的合理性：本实验采用的方法参考了相关药典，对于水中溶解度的测定，采用25℃±2℃的水浴条件下强力振摇的方法，能够有效模拟人体内的溶解环境，确保结果的准确性。对于甲醇中的溶解度测定，同样采用25℃±2℃的水浴条件，通过对比水中溶解度的结果，可以判断出药物在不同溶剂中的溶解性。此方法合理且符合实际检测需求。', 'reference': '1'}}]}
    return ResponseMessage(200, 'Search completed', data).to_json()

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
    app.run(port=5000, debug=True)
