
# from db.dbutils.redis_conn import RedisDB
# from db.services.kd_service import KDService
# from mutil_agents.agents.utils.llm_util import ask_llm
# from mutil_agents.memory.review_state import ReviewState
# from mutil_agents.agent import graph, data_graph
# from IPython.display import Image
# # CFLAGS="-I$(brew --prefix graphviz)/include" LDFLAGS="-L$(brew --prefix graphviz)/lib" pip install pygraphviz

# if __name__ == "__main__":

#    service =  KDService()
#    service.add_explain_word("易溶", "溶质1g/ml能在溶剂1~不到10ml中溶解")
#    service.add_explain_word("极易溶解", "溶质1g/ml能在溶剂不到1ml中溶解")
#    ans = service.search_explain_by_content("本品在水中极易溶解，在甲醇中易溶。")
#    print(ans)

from mutil_agents.agent import specific_report_generationAgent_graph
from mutil_agents.memory.specific_review_state import SpecificReviewState


content = """
当前属于eCTD模块3.2.S.4.2分析方法部分
2 溶解度
2.1. 试药与试剂：甲醇
2.2. 仪器与设备：秒表、电子分析天平(万分之一)、容量瓶、量筒、刻度吸管。
2.3. 操作方法：
a) .水中溶解度： 精密称取本品1g,置于10ml具塞刻度试管中，加水1mL然后于25℃±2℃
的水浴条件下每隔5分钟强力振摇30秒，观察30分钟，应完全溶解。
b) .甲醇中的溶解度： 精密称取本品1g,置于10ml具塞刻度试管中，加水1mL然后于25℃±2℃
的水浴条件下每隔5分钟强力振摇30秒，观察30分钟，应未完全溶解。
精密称取本品1g,置于10ml具塞刻度试管中，加水9mL然后于25℃±2℃
的条件下每隔5分钟强力振摇30秒，观察30分钟，应完全溶解。
2.4.结果：本品在水中极易溶，在甲醇中易溶。"""

requirements = [
    "1.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。",
    "2.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。",
]

report_require_list = [
    "1.需要说明检测方法合理性，一般如果药典存在检测方法，可以直接引用，如果没有，需要说明检测方法的合理性。",
]

review_state = SpecificReviewState()
review_state["content"] = content
review_state["review_require_list"] = requirements
review_state["report_require_list"] = report_require_list
print(review_state)
ans = specific_report_generationAgent_graph.invoke(review_state)
print(ans)