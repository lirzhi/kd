from flask import session
from sqlalchemy import text
from db.dbutils.mysql_conn import MysqlConnection
from db import db_model as models


class FileService:
    def get_file_by_cls(self, class_name):
        pass
    
    @staticmethod
    def get_file_by_id(doc_id):
        session = MysqlConnection().get_session()
        result = session.query(models.FileInfo).filter_by(doc_id=doc_id).first()
        return result
      

    def get_file_by_path(self, file_path):
        pass

    def get_file_by_name(self, file_name):
        pass

    def get_file_by_type(self, file_type):
        pass

    def get_file_by_tag(self, tag):
        pass

    def get_file_by_chunk(self, chunk):
        pass

    def save_file(self, file_path):
        pass