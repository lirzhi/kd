import logging
from flask import Flask, request, redirect, url_for, render_template, flash
from sqlalchemy import text

from db.services.file_service import FileService
from db.services.kd_service import KDService
from llm.llm_util import ask_llm_by_prompt_file
from utils.common_util import ResponseMessage
from utils.file_util import rewrite_json_file
from utils.parser.parser_manager import ParserManager



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 用于保护应用免受跨站请求伪造攻击
@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # 检查是否有文件在请求中
        if 'file' not in request.files:
            logging.error('没有文件部分')
            return ResponseMessage(400, f'文件提交不存在', None).to_json()
        file = request.files['file']
        # 如果用户没有选择文件，浏览器可能会提交一个没有文件名的空部分
        if file.filename == '':
            flash('没有选择文件')
            return ResponseMessage(400, f'未选择文件', None).to_json()
        meta_info = {
            "classification": request.form.get('classification'),
            "affect_range": request.form.get('affect_range'),
        }
        flag, info = FileService().save_file(file, meta_info)
        if flag == False:
            logging.warning(info)
            return ResponseMessage(400, info, None).to_json()
        flash(f'文件 {file.filename} 已上传成功！doc_id: {info}')
        return ResponseMessage(200, f'文件 {file.filename} 已上传成功！doc_id: {info}', {"file_name": file.filename, "doc_id": info}).to_json()
    return render_template('upload.html')

@app.route('/add_to_kd/<doc_id>', methods=['GET','POST'])
def add_to_kd(doc_id):
    # chunk切分
    try:
        chunks = ParserManager.parse(doc_id)
    except Exception as e:
        logging.error(f'文件未能成功chunk: {str(e)}')
        return ResponseMessage(400, f'文件未能成功chunk: {str(e)}', None).to_json()
    if not chunks:
        logging.warning('文件切分失败')
        return ResponseMessage(400, f'文件chunk_size为0, 请检查文件内容是否存在', None).to_json()
    # 保存chunk信息到mysql数据库
    flag, msg = FileService().update_file_chunk_by_id(doc_id, len(chunks))
    flash(msg)
    if flag == False:
        return ResponseMessage(400, msg, None).to_json()
    
    # 保存到es数据库
    err_msg = KDService().save_chunks_to_es(chunks, "knowledge_index", chunks[0]["classification"])
    if err_msg:
        flash(err_msg)
        return ResponseMessage(400, err_msg, None).to_json()
    logging.info(f'文件{doc_id}已成功添加到es')

    # 保存到vector数据库
    res = KDService().save_chunk_to_vector(chunks)
    logging.info(f"{res['insert_count']}/{len(chunks)}个文档片段成功添加到向量数据库")
    return ResponseMessage(200, f'文件{doc_id}成功添加到知识库', chunks).to_json()
   

@app.route('/search_by_query', methods=['GET','POST'])
def search_by_query():
    query = request.form.get('query')
    # result = KDService().search_by_query(query)
    result = KDService().search_by_vector(query)
    resp = []
    llm_context = {}
    llm_context["query"] = query
    llm_context["content"] = []
    llm_resp = {}
    reference_list = []
    for items in result:
        for item in items:
            file_info = FileService().get_file_by_id(item["entity"]["doc_id"])
            temp = {}
            temp["doc_id"] = item["entity"]["doc_id"]
            temp["file_name"] = file_info.file_name
            temp["content"] = item["entity"]["text"]
            temp["classification"] = item["entity"]["classification"]
            temp["affect_range"] = item["entity"]["affect_range"]
            llm_context["content"].append(temp["content"])
            reference_file_info = {}
            reference_file_info["doc_id"] = item["entity"]["doc_id"]
            reference_file_info["file_name"] = file_info.file_name
            reference_file_info["classification"] = item["entity"]["classification"]
            reference_list.append(reference_file_info)
            resp.append(temp)
    gen = ask_llm_by_prompt_file("llm/prompts/generate_prompt.j2", llm_context)
    llm_resp["response"] = gen
    llm_resp["reference"] = reference_list
    
    return render_template('search_form.html', result=llm_resp)

@app.route('/')
def index():
    return render_template('search_form.html')
    
@app.route('/search_by_classification', methods=['GET','POST'])
def search_by_classification():
    pass


if __name__ == '__main__':
    app.run(debug=True)