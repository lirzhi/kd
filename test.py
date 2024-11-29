import json
import logging
from db.dbutils.es_conn import ESConnection
from utils.parser.docx_parser import RAGFlowDocxParser
logging.basicConfig(level=logging.INFO)
# 创建DocxParser实例
parser = RAGFlowDocxParser()

# 解析.docx文档
# file_path = 'data/uploads/test.docx'
# parsed_content, parsed_table = parser(file_path)
# print(type)
# 打印解析后的内容
# for section in parsed_content:
#     print(type(section))
#     for block in section:
#         print(block)
#     print('----------------')
#     break

# for table in parsed_table:
#     print(table)
#     print('----------------')
#     break


# txt_parser = RAGFlowTxtParser()
# file_path = 'data/uploads/test.txt'
# parsed_content = txt_parser(file_path)
# for section in parsed_content:
#     print(section)
#     print('----------------')
#     break


es_conn = ESConnection()
es_conn.createIdx("test_index", "test_type", 64)
with open('data/parser/chunks/28a5d474d609499b.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)
    chunks_data = []
    for chunk in chunks:
        chunk["id"] = chunk["doc_id"] + str(chunk["chunk_id"])
        chunks_data.append(chunk)
   
    res = es_conn.insert(chunks_data, "test_index", "test_type")
    print(res)
     