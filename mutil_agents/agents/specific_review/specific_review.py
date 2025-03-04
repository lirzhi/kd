import logging
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.specific_review_state import SpecificReviewState
from utils.common_util import parallelize_processing
from mutil_agents.agents.specific_review.tools import tools
from mutil_agents.agents.specific_review.tools import methods_mapping

class SpecificReview:
    def get_require_list(self, review_state: SpecificReviewState):
        # 获取指导原则要求和报告要求列表

        return review_state

    @parallelize_processing(field_to_iterate='review_require_list', result_field='search_plan_list')
    def analyze(self, review_state: SpecificReviewState, review_require, index):
        print("start analyze")
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
        print(ans)
        return ans["response"]
    
    @parallelize_processing(field_to_iterate='search_plan_list', result_field='search_list')
    def search(self, review_state: SpecificReviewState, search_plan, index):
        print("start search")
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
            search_list.append(ans)
        return search_list
    
    @parallelize_processing(field_to_iterate='review_require_list', result_field='review_result_list')
    def generate_report_by_require(self, review_state: SpecificReviewState, review_require, index):
        print("start generate_report_by_require")
        if review_state.get("review_result_list") != None and len(review_state["review_result_list"]) > index:
            return review_state["review_result_list"][index]
        
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
        return ans["response"]
    
    def generate_final_report(self, review_state: SpecificReviewState):
        print("start generate_final_report")
        data = {
            "content": review_state["content"],
            "review_result_list": review_state["review_result_list"],
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
        return review_state
    
    def check_report(self, review_state: SpecificReviewState):
        print("start judge")
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
        print(ans["response"]["step"])
        return ans["response"]["step"]
        