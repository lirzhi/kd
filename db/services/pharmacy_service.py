from db.dbutils import singleton
from db.dbutils.mysql_conn import MysqlConnection
from db import db_model as models

@singleton
class PharmacyService:
    def __init__(self):
        self.db_conn = MysqlConnection()

    def add_pharmacy(self, info_dict):
        session = self.db_conn.get_session()
        try:
            pharmacy = models.PharmacyInfo(**info_dict)
            session.add(pharmacy)
            session.commit()
            return True, pharmacy.id
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    def get_pharmacy_by_id(self, id):
        session = self.db_conn.get_session()
        try:
            return session.query(models.PharmacyInfo).filter_by(id=id).first()
        finally:
            session.close()

    def get_pharmacy_by_name(self, name):
        session = self.db_conn.get_session()
        try:
            return session.query(models.PharmacyInfo).filter_by(name=name).first()
        finally:
            session.close()

    def update_pharmacy(self, id, update_dict):
        session = self.db_conn.get_session()
        try:
            session.begin()
            update_count = session.query(models.PharmacyInfo).filter_by(id=id).update(update_dict)
            session.commit()
            return update_count > 0
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def delete_pharmacy(self, id):
        session = self.db_conn.get_session()
        try:
            session.begin()
            count = session.query(models.PharmacyInfo).filter_by(id=id).delete()
            session.commit()
            return count > 0
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def list_pharmacy(self, offset=0, limit=20):
        session = self.db_conn.get_session()
        try:
            return session.query(models.PharmacyInfo).offset(offset).limit(limit).all()
        finally:
            session.close()

    def count_pharmacy(self):
        session = self.db_conn.get_session()
        try:
            return session.query(models.PharmacyInfo).count()
        finally:
            session.close()
