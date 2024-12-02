from datetime import datetime
import uuid
from flask import Flask, request, redirect, url_for, render_template, flash
import os
from sqlalchemy import text

from db.dbutils.es_conn import ESConnection
from db.dbutils.mysql_conn import MysqlConnection
from db.services.file_service import FileService
from db.services.kd_service import KDService
from utils.file_util import rewrite_json_file
from utils.parser.parser_manager import ParserManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 用于保护应用免受跨站请求伪造攻击
@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # 检查是否有文件在请求中
        if 'file' not in request.files:
            flash('没有文件部分')
            return redirect(request.url)
        file = request.files['file']
        # 如果用户没有选择文件，浏览器可能会提交一个没有文件名的空部分
        if file.filename == '':
            flash('没有选择文件')
            return redirect(request.url)
        meta_info = {
            "classification": request.form.get('classification'),
            "affect_range": request.form.get('affect_range'),
        }
        flag, info = FileService().save_file(file, meta_info)
        if flag == False:
            flash(info)
            return redirect(request.url)
        flash(f'文件 {file.filename} 已上传成功！doc_id: {info}')
    return render_template('upload.html')

@app.route('/add_to_kd/<doc_id>', methods=['GET','POST'])
def add_to_kd(doc_id):
    # chunk切分
    print(doc_id)
    chunks = ParserManager.parse(doc_id)
    if not chunks:
        flash('文件切分失败')
        return redirect(url_for('add_to_kd'))
    FileService().save_file_chunk(doc_id, chunks)
    # 保存chunk信息到mysql数据库
    flag, msg = FileService().update_file_chunk_by_id(doc_id, len(chunks))
    flash(msg)
    if flag == False:
        return redirect(url_for('add_to_kd'))
    # 保存到es数据库
    if len(chunks) == 0:
        flash('请检查文件是否为空')
        return redirect(url_for('add_to_kd'))
    err_msg = KDService().save_chunks_to_es(chunks, "knowledge_index", chunks[0]["classification"])
    if err_msg:
        flash(err_msg)
        return redirect(url_for('add_to_kd'))
    flash('文件已成功添加到es')

    # 保存到vector数据库
    
    res = KDService().save_chunk_to_vector(chunks)
    flash(f"{res['insert_count']}/{len(chunks)}个文档片段成功添加到向量数据库")
    return render_template('chunks.html', chunks=chunks)
   

@app.route('/search_by_query', methods=['GET','POST'])
def search_by_query():
    query = request.form.get('query')
    kb_ids = request.form.get('kb_ids')
    result = KDService().search_by_query(query, kb_ids)
    print(result)
    result = KDService().search_by_vector(query)
    print(result)
    return render_template('search_form.html', result=result[0])

@app.route('/')
def index():
    return render_template('search_form.html')
    
@app.route('/search_by_classification', methods=['GET','POST'])
def search_by_classification():
    pass


if __name__ == '__main__':
    app.run(debug=True)