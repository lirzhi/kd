from db.dbutils import singleton
from db.dbutils.mysql_conn import MysqlConnection
from db import db_model as models

@singleton
class QAService:
    def __init__(self):
        self.db_conn = MysqlConnection()

    def add_qa(self, info_dict):
        session = self.db_conn.get_session()
        try:
            qa = models.QAInfo(**info_dict)
            session.add(qa)
            session.commit()
            return True, qa.id
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    def get_qa_by_id(self, id):
        session = self.db_conn.get_session()
        try:
            return session.query(models.QAInfo).filter_by(id=id).first()
        finally:
            session.close()

    def update_qa(self, id, update_dict):
        session = self.db_conn.get_session()
        try:
            session.begin()
            update_count = session.query(models.QAInfo).filter_by(id=id).update(update_dict)
            session.commit()
            return update_count > 0
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def delete_qa(self, id):
        session = self.db_conn.get_session()
        try:
            session.begin()
            count = session.query(models.QAInfo).filter_by(id=id).delete()
            session.commit()
            return count > 0
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def list_qa(self, category=None, offset=0, limit=20):
        session = self.db_conn.get_session()
        try:
            query = session.query(models.QAInfo)
            if category:
                query = query.filter_by(category=category)
            return query.offset(offset).limit(limit).all()
        finally:
            session.close()

    def count_qa(self, category=None):
        session = self.db_conn.get_session()
        try:
            query = session.query(models.QAInfo)
            if category:
                query = query.filter_by(category=category)
            return query.count()
        finally:
            session.close()
