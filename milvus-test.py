
import numpy as np
from pymilvus import Collection
from db.dbutils.vector_db import Embedding, VectorDB
# 连接 Milvus
collection = VectorDB()  # 替换为你的集合名

# 生成测试稠密向量 (768维)
query_embedding = [np.random.rand(768).tolist()]  # 注意是双重列表
limit = 5,
metric_type = "IP",
# 查询数据（获取前10条）
results = collection.search(query_embedding)
print(results)