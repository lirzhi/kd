
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from db.settings import MYSQL
from db.dbutils import singleton


SQLALCHEMY_DATABASE_URL = f'mysql+pymysql://{MYSQL["user"]}:{MYSQL["password"]}@{MYSQL["host"]}:{MYSQL["port"]}/{MYSQL["database"]}'

Base = declarative_base()

@singleton
class MysqlConnection:
    def __init__(self):
        SQLALCHEMY_ENGINE_OPTIONS = {'pool_size': MYSQL['pool_size'], 'max_overflow': MYSQL['max_overflow']}
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False, pool_pre_ping=True, **SQLALCHEMY_ENGINE_OPTIONS)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logging.info(f"MysqlConnection init:{SQLALCHEMY_DATABASE_URL}")

    def get_session(self):
        return self.SessionLocal()

    def recreate_all(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_table_structure_with_comments(self, table_name):
        inspector = inspect(self.engine)
        # 获取表的列信息
        columns = inspector.get_columns(table_name)
        # 构建结果字典
        table_structure = {}
        for column in columns:
            column_name = column['name']
            column_comment = column.get('comment', 'No comment')  # 如果没有注释，默认为 'No comment'
            if column_comment is None:
                column_comment = 'No comment'
            table_structure[column_name] = column_comment
        return table_structure

