import json
import logging
from db.dbutils import singleton


@singleton
class QAParser:
    def process_qa_file(self, file_name):
        try:
            # 打开并读取 JSON 文件
            with open(file_name, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # 初始化一个空列表来存储 chunks
            chunks = []
            
            # 遍历数据中的每个问答对
            for index, item in enumerate(data):
                # 拼接 question 和 answer
                text = f"question:{item['question']} \n 答案：{item['answer']}"
                
                # 创建一个新的 chunk 并添加到列表中
                chunk = {'text': text}
                chunk["chunk_id"] = index + 1
                chunk["image_paths"] = []
                chunk["tables"] = []
                chunks.append(chunk)
            
            return chunks
        except FileNotFoundError:
            logging.error(f"文件 {file_name} 未找到。")
            return []
        except json.JSONDecodeError:
            logging.error(f"文件 {file_name} 不是有效的 JSON 文件。")
            return []
        except Exception as e:
            logging.error(f"处理文件 {file_name} 时发生错误: {str(e)}")
            return []

    def __call__(self, path):
            return self.process_qa_file(path)