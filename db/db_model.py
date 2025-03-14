from sqlalchemy import Boolean, Column, Integer, String, Text
from db.dbutils.mysql_conn import Base, MysqlConnection
class FileInfo(Base):
    __tablename__ = "file_info"

    id = Column(Integer, primary_key=True, index=True, comment="主键自增id")
    doc_id = Column(String(256), nullable=False, index=True, comment="文档id")
    file_name = Column(String(256), nullable=False)
    file_path = Column(String(256), nullable=False, unique=True)
    file_type = Column(String(256), nullable=False)
    classification = Column(String(256), nullable=False)
    affect_range = Column(String(256), nullable=False)
    is_chunked = Column(Boolean, default=False)
    chunk_ids = Column(Text, nullable=True)
    chunk_size = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(String(256), nullable=False)

if __name__ == "__main__":
    db_conn = MysqlConnection()
    db_conn.recreate_all()

