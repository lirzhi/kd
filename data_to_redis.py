import json
import logging

from db.dbutils.redis_conn import RedisDB

def upload_principle(file_path):
    data = None
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    if data is None:
        logging.error(f"upload_principle failed, file_path: {file_path}")
        return
    # 上传到redis
    redis_conn  = RedisDB()
    count = 0
    for key, value in data.items():
        redis_conn.set(f"principle+{key}", json.dumps(value), None)
        ++count
    logging.info(f"upload_principle success, count: {count}")

file_path = 'data/raw_data/指导原则.json'
upload_principle(file_path=file_path)

def upload_analize(file_path):
    data = None
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    if data is None:
        logging.error(f"upload_principle failed, file_path: {file_path}")
        return
    # 上传到redis
    redis_conn  = RedisDB()
    count = 0
    for key, value in data.items():
        redis_conn.set(f"principle+{key}", json.dumps(value), None)
        ++count
    logging.info(f"upload_principle success, count: {count}")

file_path = 'data/raw_data/分析方法.json'
upload_analize(file_path=file_path)