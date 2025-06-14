from datetime import datetime
import logging
import os
import uuid
from sqlalchemy import text
from db.dbutils import singleton
from db.dbutils.mysql_conn import MysqlConnection
from db import db_model as models
from utils.file_util import ensure_dir_exists, rewrite_json_file

UPLOAD_FOLDER = 'data/uploads/'  # Set the target folder for file uploads
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ppt', 'pptx', 'docx', 'qa'}  # Allowed file extensions
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@singleton
class FileService:
    def __init__(self):
        ensure_dir_exists(UPLOAD_FOLDER)
        self.db_conn = MysqlConnection()

    def get_file_by_cls(self, class_name):
        pass
    
    def get_file_by_id(self, doc_id):
        try:
            session = self.db_conn.get_session()
            return session.query(models.FileInfo).filter_by(doc_id=doc_id).first()
        finally:
            session.close()

    def delete_file_by_id(self, doc_id):
        try:
            session = self.db_conn.get_session()
            ans = session.query(models.FileInfo).filter_by(doc_id=doc_id).delete()
            session.commit()
            return ans
        finally:
            session.close()

    def get_file_classification(self):
        try:
           session = self.db_conn.get_session()
           return session.query(models.FileInfo.classification).distinct().all()
        finally:
            session.close()
    
    def update_file_chunk_by_id(self, doc_id, chunk_size, v_chunk_ids):
        try:
            session = self.db_conn.get_session()
            session.begin()
            update_count = session.query(models.FileInfo).filter_by(doc_id=doc_id) \
            .update({"is_chunked": True, "chunk_size": chunk_size, "chunk_ids": v_chunk_ids})
            session.commit()
            # Check if the update operation was successful
            if update_count > 0:
                logging.info("Document chunk information saved successfully.")
                return True, f'Document {doc_id} chunk information saved successfully'
            else:
                logging.info("No records found or updated.")
        except Exception as e:
            session.rollback()
            logging.warning(f'Error saving chunk information for document {doc_id}: {str(e)}')
            return False, f'Error saving chunk information for document {doc_id}: {str(e)}'
        finally:
            session.close()
        return True, f'Document {doc_id} chunk information saved successfully'

    def get_file_by_path(self, file_path):
        try:
            session = self.db_conn.get_session()
            return session.query(models.FileInfo).filter_by(file_path=file_path).first()
        finally:
            session.close()

    def get_file_by_name(self, file_name):
        try:
            session = self.db_conn.get_session()
            return session.query(models.FileInfo).filter_by(file_name=file_name).all()
        finally:
            session.close()

    def get_file_by_type(self, file_type):
        try:
            session = self.db_conn.get_session()
            return session.query(models.FileInfo).filter_by(file_type=file_type).all()
        finally:
            session.close()

    def get_file_by_tag(self, tag):
        pass

    def get_file_by_chunk(self, chunk):
        try:
            session = self.db_conn.get_session()
            return session.query(models.FileInfo).filter_by(doc_id=chunk["doc_id"]).first()
        finally:
            session.close()

    def get_file_by_classification(self, classification):
        try:
            session = self.db_conn.get_session()
            return session.query(models.FileInfo).filter_by(classification=classification).all()
        finally:
            session.close()

    def get_file_count_by_classification(self, classification):
        """获取指定分类的文件总数"""
        session = self.db_conn.get_session()
        try:
            query = text("""
                SELECT COUNT(*) 
                FROM file_info 
                WHERE classification = :classification 
                AND is_deleted = 0
            """)
            result = session.execute(query, {'classification': classification}).fetchone()
            return result[0] if result else 0
        finally:
            session.close()

    def get_files_by_classification(self, classification, offset=0, limit=10):
        """获取指定分类的文件列表（分页）"""
        session = self.db_conn.get_session()
        try:
            query = text("""
                SELECT doc_id, file_name, classification, file_type, create_time, is_chunked
                FROM file_info
                WHERE classification = :classification
                AND is_deleted = 0
                ORDER BY create_time DESC
                LIMIT :limit OFFSET :offset
            """)
            results = session.execute(
                query,
                {
                    'classification': classification,
                    'limit': limit,
                    'offset': offset
                }
            ).fetchall()
            return [{
                'doc_id': row[0],
                'file_name': row[1],
                'doc_classification': row[2],
                'doc_type': row[3],
                'create_time': row[4],
                'parse_status': row[5]
            } for row in results]
        finally:
            session.close()

    def get_file_by_classification(self, classification):
        """获取指定分类的所有文件（不分页）"""
        session = self.db_conn.get_session()
        try:
            query = text("""
                SELECT doc_id, file_name, classification, file_type, create_time, is_chunked
                FROM file_info
                WHERE classification = :classification
                AND is_deleted = 0
                ORDER BY create_time DESC
            """)
            results = session.execute(query, {'classification': classification}).fetchall()
            return [{
                'doc_id': row[0],
                'file_name': row[1],
                'doc_classification': row[2],
                'doc_type': row[3],
                'create_time': row[4],
                'parse_status': row[5]
            } for row in results]
        finally:
            session.close()

    def save_file(self, file, meta_info = {}):
         if not allowed_file(file.filename):
            logging.warning('File type not allowed')
            return False , 'File type not allowed'
         if file and allowed_file(file.filename):
            filename = file.filename
            file_type = filename.rsplit('.', 1)[1].lower()
            # Check if the file already exists
            if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
               logging.warning(f'File {filename} already exists!')
               return False, f'File {filename} already exists!'
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
                session = self.db_conn.get_session()
                session.begin()
                session.execute(text(
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
                session.commit()
                logging.info(f'File {filename} saved successfully')
            except Exception as e:
                session.rollback()
                logging.warning(f'File upload failed: {str(e)}')
                return False, f'File upload failed: {str(e)}'
            finally:
                session.close()
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return True, doc_id