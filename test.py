import json
import logging
from db.dbutils.vector_db import VectorDB, Embedding
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


# es_conn = ESConnection()
# es_conn.createIdx("test_index", "test_type", 64)
# with open('data/parser/chunks/28a5d474d609499b.json', 'r', encoding='utf-8') as f:
#     chunks = json.load(f)
#     chunks_data = []
#     for chunk in chunks:
#         chunk["id"] = chunk["doc_id"] + str(chunk["chunk_id"])
#         chunks_data.append(chunk)
   
#     res = es_conn.insert(chunks_data, "test_index", "test_type")
#     print(res)
embedding = Embedding()
vector_db = VectorDB()
for_embedding_text_list = []
with open('data/parser/chunks/f4646ec7c13a4f9f.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)
    for chunk in chunks:
        for_embedding_text_list.append(chunk["text"])
    
vectors = embedding.convert_text_to_embedding(source_sentence=for_embedding_text_list)
for index, chunk in enumerate(chunks):
    print(vectors[index])
    chunk["vector"] = vectors[index]
    chunk["id"] = index
vector_db.save(data=chunks)
print(chunks[8])
store_embedding = []
query_text = "生产设备有什么要求" 
query_embedding = embedding.convert_text_to_embedding(source_sentence=[query_text])[0]
query_results_list = vector_db.search(query_embedding=[query_embedding])
print(query_results_list)