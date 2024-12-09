
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from db.settings import MYSQL
from db.dbutils import singleton


SQLALCHEMY_DATABASE_URL = f'mysql+pymysql://{MYSQL["user"]}:{MYSQL["password"]}@{MYSQL["host"]}:{MYSQL["port"]}/{MYSQL["database"]}'
print("database: ", SQLALCHEMY_DATABASE_URL)

Base = declarative_base()

@singleton
class MysqlConnection:
    def __init__(self):
        SQLALCHEMY_ENGINE_OPTIONS = {'pool_size': MYSQL['pool_size'], 'max_overflow': MYSQL['max_overflow']}
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False, **SQLALCHEMY_ENGINE_OPTIONS)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        print("MysqlConnection init")

    def get_session(self):
        return self.SessionLocal()

    def recreate_all(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

