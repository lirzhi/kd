import logging
from db.dbutils.redis_conn import RedisDB
from db.services.kd_service import KDService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.specific_review_state import SpecificReviewState
from utils.common_util import parallelize_processing, produce_handle_info
from mutil_agents.agents.specific_review.tools import Tools, tools
from mutil_agents.agents.specific_review.tools import methods_mapping

class SpecificReview:
    def get_require_list(self, review_state: SpecificReviewState):
        # 获取指导原则要求和报告要求列表
        data = Tools.search_principle(review_state.get("content_section",""), review_state.get("content_section_name",""))
        if data == None or len(data) == 0:
            data = []
        if review_state.get("report_require_list", None) == None:
            review_state["report_require_list"] = []
        review_state["review_require_list"] += data
        produce_handle_info({"task": "【规划分析智能体】", "data":f"获取指导原则要求：{len(review_state['review_require_list'])}条"})
        return review_state

    @parallelize_processing(field_to_iterate='review_require_list', result_field='search_plan_list')
    def analyze(self, review_state: SpecificReviewState, review_require, index):
        # print("start analyze")
        if review_state.get("search_plan_list") != None and len(review_state["search_plan_list"]) > index:
            return review_state["search_plan_list"][index]
        data = {
            "content": review_state["content"],
            "review_require": review_require,
            "tools": tools
        }
        ans = ask_llm_by_prompt_file("mutil_agents/prompts/specific_review/content_analyze_prompt.j2", data)
        if ans == None or ans["response"] == None or len(ans["response"]) == 0:
               ans = {
                "response": None
               }
        if ans["response"] != None and type(ans["response"]) != list:
            ans["response"] = [ans["response"]]
        for item in ans["response"]:
            if item.get("question") != None:
                produce_handle_info({"task": "【分析智能体】", "data":item.get("question")})
        return ans["response"]
    
    @parallelize_processing(field_to_iterate='search_plan_list', result_field='search_list')
    def search(self, review_state: SpecificReviewState, search_plan, index):
        # print("start search")
        if review_state.get("search_list") != None and len(review_state["search_list"]) > index:
            return review_state["search_list"][index]
        if search_plan == None or len(search_plan) == 0:
            logging.warning("search_plan is empty")
            return None
        if type(search_plan) != list:
            search_plan = [search_plan]
        search_list = []
        for tool in search_plan:
            func = methods_mapping.get(tool["tool"], None)
            if func == None:
                search_list.append(None)
                logging.warning("tool not found")
                continue
            produce_handle_info({"task": "【检索智能体】", "data":'检索工具调用：{tool["tool"]}'})
            parameters = tool["parameter"]
            if parameters == None or len(parameters) == 0:
                parameters = []
            if type(parameters) != list:
                parameters = [parameters]
            param_dict = {}
            for param in parameters:
                key, value = param.split('=')
                param_dict[key] = value
            try:
                ans = func(**param_dict)
            except Exception as e:
                logging.error(e)
                ans = None
            if ans == None: # 检索向量知识库
                ans = KDService().search_by_query(tool.get("question"))
                print(f"search by query:{ans}")
            search_list.append(ans)
        return search_list
    
    @parallelize_processing(field_to_iterate='review_require_list', result_field='review_result_list')
    def generate_report_by_require(self, review_state: SpecificReviewState, review_require, index):
        # print("start generate_report_by_require")
        if review_state.get("review_result_list") != None and len(review_state["review_result_list"]) > index:
            return review_state["review_result_list"][index]
        produce_handle_info({"task": "【审评智能体】", "data": f'当前处理审评要求：{review_require}'})
        data = {
            "content": review_state["content"],
            "search_info": review_state["search_list"][index],
            "review_require": review_require, 
        }
        ans = ask_llm_by_prompt_file("mutil_agents/prompts/specific_review/report_generate_by_require_prompt.j2", data)
        if ans == None or ans["response"] == None or len(ans["response"]) == 0:
            ans = {
                "response": None
            }
        if ans["response"] != None and ans["response"].get("content", None) != None :
            produce_handle_info({"task": "【审评智能体】", "data": ans["response"]})
        return ans["response"]
    
    def generate_final_report(self, review_state: SpecificReviewState):
        # print("start generate_final_report")
        produce_handle_info({"task": "最终报告生成", "data": "开始生成最终报告..."})
        data = {
            "content": review_state["content"],
            "review_result_list": review_state["review_result_list"],
            "review_require_list":review_state["review_require_list"],
            "report_require": review_state["report_require_list"],
        }
        ans = ask_llm_by_prompt_file("mutil_agents/prompts/specific_review/final_report_generate_prompt.j2", data)
        if ans == None or ans["response"] == None or len(ans["response"]) == 0:
            ans = {
                "response": None
            }
        if review_state.get("final_report") == None:
            review_state["final_report"] = []
        review_state["final_report"].append(ans["response"])
        report_content = ""
        print(review_state)
        for report in review_state["final_report"]:
            if report is None:
                continue
            if report.get("report", None) is None:
                continue
            if report["report"].get("content", None) is None:
                continue
            report_content += report["report"]["content"]
            print(report_content)
        review_state["final_report_content"] = report_content

        return review_state
    
    def check_report(self, review_state: SpecificReviewState):
        # print("start judge")
        if len(review_state.get("final_report", [])) > 2:
            return "continue"
        produce_handle_info({"task": "【评估智能体】", "data": "评估最终报告..."})
        data = {
            "content": review_state["content"],
            "review_require_list": review_state["review_require_list"],
            "review_result_list": review_state["review_result_list"],
            "final_report": review_state["final_report"][-1]
        }
        ans = ask_llm_by_prompt_file("mutil_agents/prompts/specific_review/judge_report_prompt.j2", review_state)
        if ans == None or ans["response"] == None or len(ans["response"]) == 0:
            ans = {
                "response": {
                    "step": "continue",
                    "info": "ok"
                }
            }
        if review_state.get("judge_result") == None:
            review_state["judge_result"] = []   
        review_state["judge_result"].append(ans["response"])
        info = "评估通过" if ans["response"]["step"] == "continue" else f"报告评估未通过，存在问题：{ans['response']['info']}" 
       
        produce_handle_info({"task": "【评估智能体】", "data": f'评估结论:{info}'})
        print(ans["response"]["step"])
        return ans["response"]["step"]
        