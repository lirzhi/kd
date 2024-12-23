import logging
from flask import Flask, request, redirect, url_for, render_template, flash
from sqlalchemy import text

from db.services.file_service import FileService
from db.services.kd_service import KDService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from utils.common_util import ResponseMessage
from utils.file_util import ensure_dir_exists, rewrite_json_file
from utils.parser.parser_manager import ParserManager

ensure_dir_exists('log')
logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename='log/server.log',
                    filemode='a')
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Used to protect the application from cross-site request forgery attacks

@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the request contains a file
        if 'file' not in request.files:
            logging.error('No file part')
            return ResponseMessage(400, 'No file part', None).to_json()
        file = request.files['file']
        # If the user does not select a file, the browser may submit an empty part without a filename
        if file.filename == '':
            flash('No selected file')
            return ResponseMessage(400, 'No selected file', None).to_json()
        meta_info = {
            "classification": request.form.get('classification'),
            "affect_range": request.form.get('affect_range'),
        }
        flag, info = FileService().save_file(file, meta_info)
        if not flag:
            logging.warning(info)
            return ResponseMessage(400, info, None).to_json()
        flash(f'File {file.filename} uploaded successfully! doc_id: {info}')
        return ResponseMessage(200, f'File {file.filename} uploaded successfully! doc_id: {info}', {"file_name": file.filename, "doc_id": info}).to_json()
    return render_template('upload.html')

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
    # Save chunk information to MySQL database
    flag, msg = FileService().update_file_chunk_by_id(doc_id, len(chunks))
    flash(msg)
    if not flag:
        return ResponseMessage(400, msg, None).to_json()
    
    # Save to Elasticsearch database
    err_msg = KDService().save_chunks_to_es(chunks, "knowledge_index", chunks[0]["classification"])
    if err_msg:
        flash(err_msg)
        return ResponseMessage(400, err_msg, None).to_json()
    logging.info(f'File {doc_id} successfully added to Elasticsearch')

    # Save to vector database
    res = KDService().save_chunk_to_vector(chunks)
    logging.info(f"{res['insert_count']}/{len(chunks)} document fragments successfully added to vector database")
    return ResponseMessage(200, f'File {doc_id} successfully added to knowledge base', chunks).to_json()

@app.route('/search_by_query', methods=['GET','POST'])
def search_by_query():
    query = request.form.get('query')
    # result = KDService().search_by_query(query)
    result = KDService().search_by_vector(query)
    resp = []
    llm_context = {}
    llm_context["query"] = query
    llm_context["content"] = []
    llm_context["reference"] = []
    llm_resp = {}
    reference_list = []
    for item in result:
        file_info = FileService().get_file_by_id(item["entity"]["doc_id"])
        temp = {}
        temp["doc_id"] = item["entity"]["doc_id"]
        temp["file_name"] = file_info.file_name
        temp["content"] = item["entity"]["text"]
        temp["classification"] = item["entity"]["classification"]
        temp["affect_range"] = item["entity"]["affect_range"]
        llm_context["content"].append(temp["content"])
        llm_context["reference"].append(temp["file_name"])
        reference_file_info = {}
        reference_file_info["doc_id"] = item["entity"]["doc_id"]
        reference_file_info["file_name"] = file_info.file_name
        reference_file_info["classification"] = item["entity"]["classification"]
        reference_list.append(reference_file_info)
        resp.append(temp)
    gen = ask_llm_by_prompt_file("mutil_agents/agents/prompts/generate_prompt.j2", llm_context)
    llm_resp["response"] = gen
    llm_resp["reference"] = reference_list
    
    return render_template('search_form.html', result=llm_resp)

@app.route('/')
def index():
    resp = {}
    resp["response"] = None
    return render_template('search_form.html', result=resp)
    
@app.route('/search_by_classification', methods=['GET','POST'])
def search_by_classification():
    pass

if __name__ == '__main__':
    app.run(debug=True)
