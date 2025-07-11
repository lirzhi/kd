from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime
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
    review_status = Column(Integer, default=0, comment="审评状态：0-未审评，1-已审评")
    review_time = Column(DateTime, nullable=True, comment="审评时间")

class RequireInfo(Base):
    __tablename__ = "require_info"
    id = Column(Integer, primary_key=True, index=True, comment="主键自增id")
    section_id = Column(String(256), nullable=False, index=True, comment="章节id")
    parent_section = Column(String(256), nullable=False, index=True, comment="父章节id")
    requirement = Column(String(1024), nullable=False)
    is_origin = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(String(256), nullable=False)

class ReportContent(Base):
    __tablename__ = "report_content"

    id = Column(Integer, primary_key=True, index=True, comment="主键自增id")
    doc_id = Column(String(256), nullable=False, index=True, comment="文档id")
    section_id = Column(String(256), nullable=False, index=True, comment="章节id")
    content = Column(Text, nullable=False, comment="报告内容")
    create_time = Column(DateTime, nullable=False, comment="创建时间")

class PharmacyInfo(Base):
    __tablename__ = "pharmacy_info"

    id = Column(Integer, primary_key=True, index=True, comment="主键自增id")
    name = Column(String(256), nullable=False, unique=True, comment="药品名称")
    prescription = Column(Text, nullable=True, comment="处方")
    characteristic = Column(Text, nullable=True, comment="性状")
    identification = Column(Text, nullable=True, comment="鉴别")
    inspection = Column(Text, nullable=True, comment="检查")
    content_determination = Column(Text, nullable=True, comment="含量测定")
    category = Column(String(256), nullable=True, comment="类别")
    storage = Column(Text, nullable=True, comment="贮藏")
    preparation = Column(Text, nullable=True, comment="制剂")
    specification = Column(String(256), nullable=True, comment="规格")

class QAInfo(Base):
    __tablename__ = "qa_info"

    id = Column(Integer, primary_key=True, index=True, comment="主键自增id")
    category = Column(String(256), nullable=False, comment="问题类别")
    question = Column(Text, nullable=False, comment="问题")
    answer = Column(Text, nullable=True, comment="答案")

if __name__ == "__main__":
    db_conn = MysqlConnection()
    db_conn.recreate_all()

