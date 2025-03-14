import json
import os.path
from typing import List, Dict
from pymilvus import MilvusClient
from typing import List
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

from db.dbutils import singleton
from utils.file_util import ensure_dir_exists

@singleton
class Embedding:

    def __init__(self,
                 model_id="iic/nlp_gte_sentence-embedding_chinese-base",
                 sequence_length=128
                 ):
        self.pipeline = pipeline(Tasks.sentence_embedding,
                                 model=model_id,
                                 sequence_length=sequence_length  # sequence_length 代表最大文本长度
                                 )

    def convert_text_to_embedding(self, source_sentence: List[str]):
        input_text = {
            "source_sentence": source_sentence
        }
        result = self.pipeline(input=input_text)
        return result["text_embedding"].tolist()  # 把np数组转成list
    
@singleton
class VectorDB:
    def __init__(self, db_path="data/db/milvus_demo.db", collection_name="test_collection", collection_dim=768):
        self.db_path = db_path
        self.collection_name = collection_name

        # 自动创建文件夹
        db_dir = os.path.dirname(db_path)
        ensure_dir_exists(db_dir)
        self.client = MilvusClient(self.db_path)

        # 自动创建collection
        if self.collection_name not in self.client.list_collections():
            self.client.create_collection(
                collection_name=self.collection_name, dimension=collection_dim, metric_type="IP"
            )

    def save(self, data: List[Dict[str, int]]):
        res = self.client.insert(collection_name="test_collection", data=data)
        return res
    
    def deleteByIds(self, doc_ids: list):
        return self.client.delete(collection_name="test_collection", ids=doc_ids)

    def search(
        self,
        query_embedding: List[List[float]],
        limit: int = 5,
        metric_type: str = "IP",
        params=None,
    ):
        if params is None:
            params = {}
        result = self.client.search(
            collection_name=self.collection_name,
            data=query_embedding,
            limit=limit,
            search_params={"metric_type": metric_type, "params": params},
            output_fields=["doc_id", "text", "classification", "affect_range", "index", "page"],
        )
        return result


if __name__ == "__main__":
    store_embedding = [
        {
            "id": 0,
            "vector": [
                0.3580376395471989,
                -0.6023495712049978,
                0.18414012509913835,
                -0.26286205330961354,
                0.9029438446296592,
            ],
            "raw_text": "pink_8682",
        },
        {
            "id": 1,
            "vector": [
                0.19886812562848388,
                0.06023560599112088,
                0.6976963061752597,
                0.2614474506242501,
                0.838729485096104,
            ],
            "raw_text": "red_7025",
        },
        {
            "id": 2,
            "vector": [
                0.43742130801983836,
                -0.5597502546264526,
                0.6457887650909682,
                0.7894058910881185,
                0.20785793220625592,
            ],
            "raw_text": "orange_6781",
        },
        {
            "id": 3,
            "vector": [
                0.3172005263489739,
                0.9719044792798428,
                -0.36981146090600725,
                -0.4860894583077995,
                0.95791889146345,
            ],
            "raw_text": "pink_9298",
        },
        {
            "id": 4,
            "vector": [
                0.4452349528804562,
                -0.8757026943054742,
                0.8220779437047674,
                0.46406290649483184,
                0.30337481143159106,
            ],
            "raw_text": "red_4794",
        },
        {
            "id": 5,
            "vector": [
                0.985825131989184,
                -0.8144651566660419,
                0.6299267002202009,
                0.1206906911183383,
                -0.1446277761879955,
            ],
            "raw_text": "yellow_4222",
        },
        {
            "id": 6,
            "vector": [
                0.8371977790571115,
                -0.015764369584852833,
                -0.31062937026679327,
                -0.562666951622192,
                -0.8984947637863987,
            ],
            "raw_text": "red_9392",
        },
        {
            "id": 7,
            "vector": [
                -0.33445148015177995,
                -0.2567135004164067,
                0.8987539745369246,
                0.9402995886420709,
                0.5378064918413052,
            ],
            "raw_text": "grey_8510",
        },
        {
            "id": 8,
            "vector": [
                0.39524717779832685,
                0.4000257286739164,
                -0.5890507376891594,
                -0.8650502298996872,
                -0.6140360785406336,
            ],
            "raw_text": "white_9381",
        },
        {
            "id": 9,
            "vector": [
                0.5718280481994695,
                0.24070317428066512,
                -0.3737913482606834,
                -0.06726932177492717,
                -0.6980531615588608,
            ],
            "raw_text": "purple_4976",
        },
    ]
    query_embedding = [
        [0.3580376395471989, -0.6023495712049978, 0.18414012509913835, -0.26286205330961354, 0.9029438446296592]
    ]

    vector_db = VectorDB()
    vector_db.save(data=store_embedding)
    r = vector_db.search(query_embedding=query_embedding)
    print(r)