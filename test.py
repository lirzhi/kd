
from db.dbutils.redis_conn import RedisDB
from db.services.kd_service import KDService
from mutil_agents.agents.utils.llm_util import ask_llm
from mutil_agents.memory.review_state import ReviewState
from mutil_agents.agent import graph, data_graph
from IPython.display import Image
# CFLAGS="-I$(brew --prefix graphviz)/include" LDFLAGS="-L$(brew --prefix graphviz)/lib" pip install pygraphviz

if __name__ == "__main__":

   service =  KDService()
   service.add_explain_word("易溶", "溶质1g/ml能在溶剂1~不到10ml中溶解")
   service.add_explain_word("极易溶解", "溶质1g/ml能在溶剂不到1ml中溶解")
   ans = service.search_explain_by_content("本品在水中极易溶解，在甲醇中易溶。")
   print(ans)

