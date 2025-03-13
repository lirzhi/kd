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
        self.db_session = MysqlConnection().get_session()

    def get_file_by_cls(self, class_name):
        pass
    
    def get_file_by_id(self, doc_id):
        try:
            return self.db_session.query(models.FileInfo).filter_by(doc_id=doc_id).first()
        finally:
            self.db_session.close()

    def delete_file_by_id(self, doc_id):
        try:
            return self.db_session.delete(models.FileInfo).filter_by(doc_id=doc_id)
        finally:
            self.db_session.close()
    
    def update_file_chunk_by_id(self, doc_id, chunk_size):
        try:
            self.db_session.begin()
            update_count = self.db_session.query(models.FileInfo).filter_by(doc_id=doc_id) \
            .update({"is_chunked": True, "chunk_size": chunk_size})
            self.db_session.commit()
            # Check if the update operation was successful
            if update_count > 0:
                logging.info("Document chunk information saved successfully.")
                return True, f'Document {doc_id} chunk information saved successfully'
            else:
                logging.info("No records found or updated.")
        except Exception as e:
            self.db_session.rollback()
            logging.warning(f'Error saving chunk information for document {doc_id}: {str(e)}')
            return False, f'Error saving chunk information for document {doc_id}: {str(e)}'
        finally:
            self.db_session.close()
        return True, f'Document {doc_id} chunk information saved successfully'

    def get_file_by_path(self, file_path):
        try:
            return self.db_session.query(models.FileInfo).filter_by(file_path=file_path).first()
        finally:
            self.db_session.close()

    def get_file_by_name(self, file_name):
        try:
            return self.db_session.query(models.FileInfo).filter_by(file_name=file_name).all()
        finally:
            self.db_session.close()

    def get_file_by_type(self, file_type):
        try:
            return self.db_session.query(models.FileInfo).filter_by(file_type=file_type).all()
        finally:
            self.db_session.close()

    def get_file_by_tag(self, tag):
        pass

    def get_file_by_chunk(self, chunk):
        try:
            return self.db_session.query(models.FileInfo).filter_by(doc_id=chunk["doc_id"]).first()
        finally:
            self.db_session.close()

    def get_file_by_classification(self, classification):
        try:
            return self.db_session.query(models.FileInfo).filter_by(classification=classification).all()
        finally:
            self.db_session.close()


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
                self.db_session.begin()
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
                logging.info(f'File {filename} saved successfully')
            except Exception as e:
                self.db_session.rollback()
                logging.warning(f'File upload failed: {str(e)}')
                return False, f'File upload failed: {str(e)}'
            finally:
                self.db_session.close()
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return True, doc_id