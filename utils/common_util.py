from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import json
import logging

def parallelize_processing(field_to_iterate, result_field):
    def decorator(func):
        @wraps(func)
        def wrapper(self, review_state):
            logging.info(f"{func.__name__}...")
            # 创建线程池
            with ThreadPoolExecutor() as executor:
                # 提交任务到线程池
                futures = {executor.submit(func, self, review_state, item): index for index, item in enumerate(review_state[field_to_iterate])}
                # 收集结果
                result_list = [None] * len(review_state[field_to_iterate])
                for future in as_completed(futures):
                    index = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        logging.error(f'{index} generated an exception: {exc}')
                    else:
                        result_list[index] = result
                # 将结果合并到review_state中
                review_state[result_field] = result_list
            return review_state
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
