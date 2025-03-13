import logging
import os
import jieba
from sympy import factor_list
from db.dbutils import singleton
from db.dbutils.doc_store_conn import MatchTextExpr, OrderByExpr
from db.dbutils.es_conn import ESConnection
from db.dbutils.mysql_conn import MysqlConnection
from db.dbutils.redis_conn import RedisDB
from db.dbutils.vector_db import Embedding, VectorDB
from db.services.file_service import FileService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file

WORD_DICT = "userdict.txt"
@singleton
class KDService:
    def __init__(self):
        self.db_session = MysqlConnection().get_session()
        self.es_conn = ESConnection()
        self.embedding = Embedding()
        self.vector_db = VectorDB()
        self.redis_conn = RedisDB()
        if not os.path.exists(WORD_DICT):
            with open(WORD_DICT, 'w') as f:
                pass
        jieba.load_userdict("userdict.txt")

    def save_chunks_to_es(self, chunk, index_name, kd_id):
        self.es_conn.createIdx(index_name, kd_id, 64)
        return self.es_conn.insert(chunk, index_name, kd_id)

    def delete_chunk_from_es_by_id(self,doc_id, chunk_id, index_name, kd_id):
        condition = {
            "id": doc_id + "_" + chunk_id,
        }
        return self.es_conn.delete(condition=condition, indexName=index_name, knowledgebaseId=kd_id)
        

    def search_by_query(self, query, kb_ids=[]):
        # 构建查询条件
        condition = {
            "text": query  # 假设您想要查询文本字段中包含"example"的文档
        }
        return self.es_conn.search(
            condition=condition,
            indexNames="knowledge_index",
        )

        # match_expr = MatchTextExpr(
        #     fields=["text"],
        #     matching_text=query,
        #     topn=10,
        #     extra_options={}
        # )
        # order_by_expr = OrderByExpr()
        # order_by_expr.desc("classification")
        
        # return self.es_conn.search(
        #     selectFields=["chunk_id", "doc_id", "text", "classification", "affect_range", "index"],
        #     highlightFields=["text"],
        #     condition=condition,
        #     matchExprs=[match_expr],
        #     orderBy=order_by_expr,
        #     offset=0,
        #     limit=10,
        #     indexNames="knowledge_index",
        #     knowledgebaseIds=kb_ids
        # )

    def get_chunk_by_id(self, doc_id, chunk_id):
        pass

    def get_chunks_by_doc_id(self, doc_id):
        pass

    def build_classification_index(self, index_graph):
        pass

    def search_by_cls(self, cls):
        pass

    def build_es_index(self, index_name):
        pass

    def search_by_query_es(self, query):
        # 构建查询条件
        condition = {
            "text": query  # 假设您想要查询文本字段中包含"example"的文档
        }
        return self.es_conn.search(
            condition=condition,
            indexNames="knowledge_index",
        )
        pass

    def save_chunk_to_vector(self, chunks=[], db_name="test_collection"):
        embedding_text_list = []
        for chunk in chunks:
            embedding_text_list.append(chunk["text"])
    
        vectors = self.embedding.convert_text_to_embedding(source_sentence=embedding_text_list)
        for index, chunk in enumerate(chunks):
            chunk["vector"] = vectors[index]
        
        return self.vector_db.save(data=chunks)
    

    def search_by_vector(self, query="", classification_filters=[], db_name="test_collection"):
        query_embedding = self.embedding.convert_text_to_embedding(source_sentence=[query])[0]
        query_results_list = self.vector_db.search(query_embedding=[query_embedding])[0]
        if len(classification_filters) != 0:
            query_results_list = [item for item in query_results_list if item["entity"]["classification"] in classification_filters]
        return query_results_list
    
    def add_explain_word(self, word, explain):
        if self.redis_conn.exist(word):
            logging.warning(f"word {word} already exists. new explain：{explain}")
        ans = self.redis_conn.set(word, explain)
        # 将word放入分词器的词表中
        jieba.add_word(word)
        return ans
    
    def search_explain_by_content(self, content):
        # 分词后查询每个词是否有含义的解释,并返回词在句子中的位置
        word_dict = {}
        tokens = jieba.tokenize(content)
        for word,start,end in tokens:
           if self.redis_conn.exist(word):
                word_dict[word] = {}
                word_dict[word]["explain"] = self.redis_conn.get(word)
                word_dict[word]["start"] = start
                word_dict[word]["end"] = end
        return word_dict

    def search_by_query(self, query):
        result = KDService().search_by_vector(query)
        if result is None or len(result) == 0:
            return None
        resp = []
        llm_context = {}
        llm_context["query"] = query
        llm_context["content"] = []
        llm_context["reference"] = []
        llm_resp = {}
        reference_map = {}
        for item in result:
            file_info = FileService().get_file_by_id(item["entity"]["doc_id"])
            if file_info is None:
                continue
            temp = {}
            temp["doc_id"] = item["entity"]["doc_id"]
            temp["content"] = item["entity"]["text"]
            llm_context["content"].append(temp["content"])
            llm_context["reference"].append(temp["doc_id"])
            reference_file_info = {}
            reference_file_info["file_name"] = file_info.file_name
            reference_file_info["content"] = temp["content"]
            reference_file_info["classification"] = item["entity"]["classification"]
            if item["entity"]["doc_id"] in reference_map:
                reference_map[item["entity"]["doc_id"]]["content"] += " " + reference_file_info["content"]
            else:
                reference_map[item["entity"]["doc_id"]] = reference_file_info
        gen = ask_llm_by_prompt_file("mutil_agents/prompts/review/generate_prompt.j2", llm_context)
        llm_resp["response"] = gen["response"]
        llm_resp["reference"] = reference_map
        llm_resp["query"] = query
        return llm_resp