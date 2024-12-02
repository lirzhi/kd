from db.dbutils import singleton
from db.dbutils.doc_store_conn import MatchTextExpr, OrderByExpr
from db.dbutils.es_conn import ESConnection
from db.dbutils.mysql_conn import MysqlConnection


@singleton
class KDService:
    def __init__(self):
        self.db_session = MysqlConnection().get_session()
        self.es_conn = ESConnection()

    def save_chunks_to_es(self, chunk, index_name, kd_id):
        self.es_conn.createIdx(index_name, kd_id, 64)
        return self.es_conn.insert(chunk, index_name, kd_id)

    def delete_chunk_from_es_by_id(self,doc_id, chunk_id, index_name, kd_id):
        condition = {
            "id": doc_id + "_" + chunk_id,
        }
        return self.es_conn.delete(condition=condition, indexName=index_name, knowledgebaseId=kd_id)
        

    def search_by_query(self, query, kb_ids):
        # 构建查询条件
        condition = {
            "text": query  # 假设您想要查询文本字段中包含"example"的文档
        }

        match_expr = MatchTextExpr(
            fields=["text"],
            matching_text=query,
            topn=10,
            extra_options={}
        )
        order_by_expr = OrderByExpr()
        order_by_expr.desc("classification")
        
        return self.es_conn.search(
            selectFields=["chunk_id", "doc_id", "text", "classification", "affect_range", "index"],
            highlightFields=["text"],
            condition=condition,
            matchExprs=[match_expr],
            orderBy=order_by_expr,
            offset=0,
            limit=10,
            indexNames="knowledge_index",
            knowledgebaseIds=kb_ids
        )

    def get_chunk_by_id(self, chunk_id):
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
        pass

    def build_vector_index(self, index_name, query):
        pass

    def search_by_vector(self, index_name, vector):
        pass
    
