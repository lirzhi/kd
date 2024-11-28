from datetime import datetime
import uuid
from flask import Flask, request, redirect, url_for, render_template, flash
import os
from sqlalchemy import text

from db.dbutils.es_conn import ESConnection
from db.dbutils.mysql_conn import MysqlConnection
from utils.file_utils import rewrite_json_file
from utils.parser.parser_manager import ParserManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 用于保护应用免受跨站请求伪造攻击
app.config['UPLOAD_FOLDER'] = 'data/uploads/'  # 设置文件上传的目标文件夹
app.config["CHUNK_FOLDER"] = "data/parser/chunks/"  # 设置切分文件的目标文件夹
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ppt', 'pptx', 'docx'}  # 允许的文件扩展名

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否被允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
        if not allowed_file(file.filename):
            flash('文件类型不被允许')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            file_type = filename.rsplit('.', 1)[1].lower()
            # 检查文件是否已经存在
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
               flash(f'文件 {filename} 已存在！')
               return redirect(request.url)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            random_uuid = uuid.uuid4()
            doc_id = str(random_uuid).replace('-', '')[:16]
            create_time = datetime.now()
            classification = request.form['classification']
            affect_range = request.form['affect_range']
            try:
                session = MysqlConnection().get_session()
                session.execute(text(
                    "INSERT INTO file_info (doc_id, file_name, file_path, file_type, classification, affect_range, is_chunked, is_deleted, create_time) VALUES (:doc_id, :file_name, :file_path, :file_type, :classification, :affect_range, :is_chunked, :is_deleted, :create_time)"),
                    {
                        'doc_id': doc_id,
                        'file_name': filename,
                        'file_path': os.path.join(app.config['UPLOAD_FOLDER'] + filename),
                        'file_type': file_type,
                        'classification': classification,
                        'affect_range': affect_range,
                        'is_chunked': 0,
                        'is_deleted': 0,
                        'create_time': create_time
                    }
                )
                session.commit()
                flash(f'文件 {filename} 已上传成功！doc_id: {doc_id}')
            except Exception as e:
                session.rollback()
                print(e)
                flash(f'文件上传失败: {str(e)}')
            finally:
                session.close()
    return render_template('upload.html')

@app.route('/add_to_kd/<doc_id>', methods=['GET','POST'])
def add_to_kd(doc_id):
    # chunk切分
    print(doc_id)
    chunks = ParserManager.parse(doc_id)
    if not chunks:
        flash('文件切分失败')
        return redirect(url_for('add_to_kd'))
    # 保存成json文件
    file_name = doc_id + '.json'
    rewrite_json_file(filepath=os.path.join(app.config['CHUNK_FOLDER'], file_name), json_data=chunks)
    # 保存到数据库
    es_conn = ESConnection()
    index_name = f"chunks_{chunks[0]['classification']}"
    
    # Define the index properties based on chunk attributes
    index_properties = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "doc_id": {"type": "keyword"},
                "content": {"type": "text"},
                "classification": {"type": "keyword"},
                "affect_range": {"type": "keyword"},
                "create_time": {"type": "date"}
            }
        }
    }
    
    # Create index if it does not exist
    # if not es_conn.indexExist(index_name, knowledgebaseId="default"):
    #     es_conn.createIdx(index_name, knowledgebaseId="default", vectorSize=768, properties=index_properties)
    
    # # Insert chunks into Elasticsearch
    # try:
    #     es_conn.insert(documents=chunks, indexName=index_name, knowledgebaseId="default")
    #     flash(f'文件 {doc_id} 的切分内容已成功添加到知识库！')
    # except Exception as e:
    #     flash(f'文件 {doc_id} 的切分内容添加到知识库失败: {str(e)}')
    return render_template('chunks.html', chunks=chunks)
   

@app.route('/search_by_query', methods=['GET','POST'])
def search_by_query():
    query = request.args.get('query')
    session = MysqlConnection().get_session()
    
@app.route('/search_by_classification', methods=['GET','POST'])
def search_by_classification():
    pass


if __name__ == '__main__':
    app.run(debug=True)