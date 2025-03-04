from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import json
import logging

from db import settings

def parallelize_processing(field_to_iterate, result_field, max_workers=3):
    def decorator(func):
        @wraps(func)
        def wrapper(self, data_state):
            logging.info(f"{func.__name__}...")
            # 创建线程池
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交任务到线程池
                futures = {executor.submit(func, self, data_state, item, index): index for index, item in enumerate(data_state[field_to_iterate])}
                # 收集结果
                result_list = [None] * len(data_state[field_to_iterate])
                for future in as_completed(futures):
                    index = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        logging.error(f'{index} generated an exception: {exc}')
                    else:
                        result_list[index] = result
                # 将结果合并到review_state中
                data_state[result_field] = result_list
            return data_state
        return wrapper
    return decorator

class ResponseMessage:
    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self):
        return {
            'code': self.code,
            'message': self.message,
            'data': self.data,
        }
    def to_json(self):
        return json.dumps(self.to_dict())
    
import logging
from db.dbutils.redis_conn import RedisDB, RedisMsg
import uuid


def produce_handle_info(message):
    if message is None:
        logging.info("消息为空！")  
        return
    # 发送消息到队列
    success = RedisDB().queue_product(
        queue=settings.SVR_QUEUE_NAME, 
        message=message,
        exp=3600  # 消息保留时间（秒）
    )
    if success:
        logging.info("消息生产成功！")
    else:
        logging.info("消息生产失败！")

def get_handle_info():
    consumer_name = settings.SVR_CONSUMER_NAME
    group_name = settings.SVR_CONSUMER_GROUP_NAME
    queue_name = settings.SVR_QUEUE_NAME
    # 从队列中读取消息（阻塞式）
    msg = RedisDB().queue_consumer(
        queue_name=queue_name,
        group_name=group_name,
        consumer_name=consumer_name,
        msg_id=">"  # ">" 表示只读取新消息
    )
    if msg is None:
        return None
    message_data = None
    try:
        # 处理消息
        message_data = msg.get_message()
        
        # 确认消息（ACK）
        if msg.ack():
            logging.info("消息确认成功！")
        else:
            logging.info("消息确认失败！")

    except Exception as e:
        logging.info(f"处理消息失败: {str(e)}")
    return message_data

