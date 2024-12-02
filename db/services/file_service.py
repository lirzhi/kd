from datetime import datetime
import logging
import os
import uuid
from sqlalchemy import text
from db.dbutils import singleton
from db.dbutils.mysql_conn import MysqlConnection
from db import db_model as models
from utils.file_util import rewrite_json_file

UPLOAD_FOLDER = 'data/uploads/'  # 设置文件上传的目标文件夹
CHUNK_FOLDER = "data/parser/chunks/"  # 设置切分文件的目标文件夹
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ppt', 'pptx', 'docx'}  # 允许的文件扩展名
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否被允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@singleton
class FileService:
    def __init__(self):
        self.db_session = MysqlConnection().get_session()

    def get_file_by_cls(self, class_name):
        pass
    
    def get_file_by_id(self, doc_id):
        result = self.db_session.query(models.FileInfo).filter_by(doc_id=doc_id).first()
        return result
    
    def update_file_chunk_by_id(self, doc_id, chunk_size):
        try:
            update_count1 = self.db_session.query(models.FileInfo).filter_by(doc_id=doc_id).update({"is_chunked": True})
            update_count2 = self.db_session.query(models.FileInfo).filter_by(doc_id=doc_id).update({"chunk_size": chunk_size})
            self.db_session.commit()
            # 检查更新操作是否成功执行
            if update_count1 > 0 and update_count2 > 0:
                print("Records updated successfully.")
            else:
                print("No records found or updated.")
        except Exception as e:
            self.db_session.rollback()
            logging.warning(f'{doc_id}文档chunk信息保存错误: {str(e)}')
            return False, f'{doc_id}文档chunk信息保存错误: {str(e)}'
        return True, f'{doc_id}文档chunk信息保存成功'

    def get_file_by_path(self, file_path):
        return self.db_session.query(models.FileInfo).filter_by(file_path=file_path).first()

    def get_file_by_name(self, file_name):
        return self.db_session.query(models.FileInfo).filter_by(file_name=file_name).all()

    def get_file_by_type(self, file_type):
        return self.db_session.query(models.FileInfo).filter_by(file_type=file_type).all()

    def get_file_by_tag(self, tag):
        pass

    def get_file_by_chunk(self, chunk):
        return self.db_session.query(models.FileInfo).filter_by(doc_id=chunk["doc_id"]).first()

    def save_file(self, file, meta_info = {}):
         if not allowed_file(file.filename):
            logging.warning('文件类型不被允许')
            return False , '文件类型不被允许'
         if file and allowed_file(file.filename):
            filename = file.filename
            file_type = filename.rsplit('.', 1)[1].lower()
            # 检查文件是否已经存在
            if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
               logging.warning(f'文件 {filename} 已存在！')
               return False, f'文件 {filename} 已存在！'
            random_uuid = uuid.uuid4()
            doc_id = str(random_uuid).replace('-', '')[:16]
            create_time = datetime.now()
            if 'classification' not in meta_info:
                meta_info['classification'] = 'other'
            if 'affect_range' not in meta_info:
                meta_info['affect_range'] = 'other'
            classification = meta_info['classification']
            affect_range = meta_info['affect_range']
            try:
                self.db_session.execute(text(
                    "INSERT INTO file_info (doc_id, file_name, file_path, file_type, classification, affect_range, is_chunked, is_deleted, create_time) VALUES (:doc_id, :file_name, :file_path, :file_type, :classification, :affect_range, :is_chunked, :is_deleted, :create_time)"),
                    {
                        'doc_id': doc_id,
                        'file_name': filename,
                        'file_path': os.path.join(UPLOAD_FOLDER + filename),
                        'file_type': file_type,
                        'classification': classification,
                        'affect_range': affect_range,
                        'is_chunked': 0,
                        'is_deleted': 0,
                        'create_time': create_time
                    }
                )
                self.db_session.commit()
                logging.info(f'文件 {filename} 保存成功')
            except Exception as e:
                self.db_session.rollback()
                logging.warning(f'文件上传失败: {str(e)}')
                return False, f'文件上传失败: {str(e)}'
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return True, doc_id
         
    def save_file_chunk(self, doc_id, chunk_data):
        # 保存成json文件
        file_name = doc_id + '.json'
        rewrite_json_file(filepath=os.path.join(CHUNK_FOLDER, file_name), json_data=chunk_data)