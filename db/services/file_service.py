from datetime import datetime
import logging
import os
import uuid
from sqlalchemy import text
from db.dbutils import singleton
from db.dbutils.mysql_conn import MysqlConnection
from db import db_model as models
from utils.file_util import ensure_dir_exists, rewrite_json_file
import PyPDF2
import io

UPLOAD_FOLDER = 'data/uploads/'  # Set the target folder for file uploads
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ppt', 'pptx', 'docx', 'qa','json'}  # Allowed file extensions
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

    # 修改获取文件列表方法，增加审评状态
    def get_files_by_classification(self, classification, offset=0, limit=10):
        """获取指定分类的文件列表（分页）"""
        session = self.db_conn.get_session()
        try:
            query = text("""
                SELECT doc_id, file_name, classification, file_type, create_time, 
                       is_chunked, review_status, review_time
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
                'parse_status': row[5],
                'review_status': row[6],
                'review_time': row[7]
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
        
    def get_all_file_count_except_ectd(self):
        """获取所有非 eCTD 类型文件的总数"""
        session = self.db_conn.get_session()
        try:
            query = text("""
                SELECT COUNT(*) 
                FROM file_info 
                WHERE classification != 'eCTD' 
                AND is_deleted = 0
            """)
            result = session.execute(query).fetchone()
            return result[0] if result else 0
        finally:
            session.close()

    def get_all_files_except_ectd(self, offset=0, limit=10):
        """获取所有非 eCTD 类型文件的列表（分页）"""
        session = self.db_conn.get_session()
        try:
            query = text("""
                SELECT doc_id, file_name, classification, file_type, create_time, is_chunked
                FROM file_info
                WHERE classification != 'eCTD'  
                AND is_deleted = 0
                ORDER BY create_time DESC
                LIMIT :limit OFFSET :offset
            """)
            results = session.execute(
                query,
                {
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

         # 新增更新审评状态方法
    def update_review_status(self, doc_id, status, review_time=None):
        """更新文件审评状态"""
        session = self.db_conn.get_session()
        try:
            session.begin()
            update_data = {
                'review_status': status
            }
            if review_time:
                update_data['review_time'] = review_time
            
            update_count = session.query(models.FileInfo).filter_by(doc_id=doc_id) \
                .update(update_data)
            session.commit()
            
            if update_count > 0:
                logging.info(f"Document {doc_id} review status updated successfully.")
                return True, f'Document {doc_id} review status updated successfully'
            else:
                logging.warning("No records found or updated.")
                return False, "No records found or updated."
        except Exception as e:
            session.rollback()
            logging.error(f'Error updating review status for document {doc_id}: {str(e)}')
            return False, f'Error updating review status: {str(e)}'
        finally:
            session.close()

    # 新增获取报告内容方法
    def get_report_content(self, doc_id, section_id=None):
        """获取报告内容"""
        session = self.db_conn.get_session()
        try:
            # 这里需要根据实际存储报告内容的数据表来实现
            # 示例代码，需要根据实际情况修改
            query = text("""
                SELECT content, section_id, create_time
                FROM report_content
                WHERE doc_id = :doc_id
                AND (:section_id IS NULL OR section_id = :section_id)
                ORDER BY create_time DESC
            """)
            results = session.execute(
                query,
                {
                    'doc_id': doc_id,
                    'section_id': section_id
                }
            ).fetchall()
            return [{
                'content': row[0],
                'section_id': row[1],
                'create_time': row[2].strftime('%Y-%m-%d %H:%M:%S')
            } for row in results]
        finally:
            session.close()

    # 新增保存报告内容方法
    def save_report_content(self, doc_id, section_id, content):
        """保存报告内容"""
        session = self.db_conn.get_session()
        try:
            session.begin()
            # 这里需要根据实际存储报告内容的数据表来实现
            # 示例代码，需要根据实际情况修改
            session.execute(text("""
                INSERT INTO report_content (doc_id, section_id, content, create_time)
                VALUES (:doc_id, :section_id, :content, :create_time)
            """), {
                'doc_id': doc_id,
                'section_id': section_id,
                'content': content,
                'create_time': datetime.now()
            })
            session.commit()
            return True, "Report content saved successfully"
        except Exception as e:
            session.rollback()
            logging.error(f'Error saving report content: {str(e)}')
            return False, f'Error saving report content: {str(e)}'
        finally:
            session.close()

    def read_pdf_content(self, file_path):
        """读取PDF文件内容"""
        try:
            with open(file_path, 'rb') as file:
                # 创建PDF阅读器对象
                pdf_reader = PyPDF2.PdfReader(file)
                content = []
                
                # 遍历所有页面
                for page in pdf_reader.pages:
                    content.append(page.extract_text())
                
                # 合并所有页面内容
                return '\n'.join(content)
        except Exception as e:
            logging.error(f'Error reading PDF file: {str(e)}')
            return f"无法读取PDF文件内容: {str(e)}"

    def get_document_info(self, doc_id):
        """获取文档信息，包括文件内容"""
        try:
            session = self.db_conn.get_session()
            file_info = session.query(models.FileInfo).filter(
                models.FileInfo.doc_id == doc_id,
                models.FileInfo.is_deleted == False
            ).first()
            
            if not file_info:
                return None, "未找到文档信息"
            
            # 根据文件类型读取内容
            content = ""
            if file_info.file_type.lower() == 'pdf':
                content = self.read_pdf_content(file_info.file_path)
            else:
                try:
                    with open(file_info.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    content = f"无法读取文件内容: {str(e)}"
            
            return {
                'doc_id': file_info.doc_id,
                'file_name': file_info.file_name,
                'file_path': file_info.file_path,
                'file_type': file_info.file_type,
                'classification': file_info.classification,
                'affect_range': file_info.affect_range,
                'content': content
            }, None
            
        except Exception as e:
            return None, f"获取文档信息失败: {str(e)}"
        finally:
            session.close()