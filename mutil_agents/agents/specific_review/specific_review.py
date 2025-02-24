import logging
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.specific_review_state import SpecificReviewState
from utils.common_util import parallelize_processing

tools = {
    "指导原则检索工具":{
        "parameters": {
            "medical_type": "string:药品的类型,比如化学药、原料药等（不强制指定，可为空）",
            "priciple_name": "string:指导原则的名字(如:Q6A)，可选",
            "affected_section": "string:指导原则的章节"
        },
        "description": "根据药品类型和章节获取相关指导原则信息"
    },

    "药品信息检索工具":{
        "parameters": {
            "medicine_name": "string:当前审评药品的类型",
        },
        "description": "通过药品名称检索是否有相关信息，在审评资料中若出现药品名称，可通过此工具检索药品信息"
    },

    "分析方法检索工具":{
        "parameters": {
            "method_name": "string:当前审评药品质量方法的分析方法名称",
        },
        "description": "根据药品的鉴定类型（例如溶解度、比旋度、碱度等等）获取相关鉴定方法信息,检索数据属于药典标准检测方法"
    },    
}

class Tools:
    @staticmethod
    def search_principle(eCTD_module, medical_type=None):
        return "指导原则检索工具被调用， ectd_module: {}, medical_type: {}".format(eCTD_module, medical_type)  

    @staticmethod   
    def search_medicine(medicine_name):
        return "药品信息检索工具被调用， medicine_name: {}".format(medicine_name)
    
    @staticmethod
    def search_analyze_method(method_name):
        return "分析方法检索工具被调用， method_name: {}".format(method_name)

methods_mapping = {
     "指导原则检索工具": Tools.search_principle,  
     "药品信息检索工具": Tools.search_medicine,
     "分析方法检索工具": Tools.search_analyze_method,
     
}

class SpecificReview:
    @parallelize_processing(field_to_iterate='review_require_list', result_field='search_plan_list')
    def analyze(self, review_state: SpecificReviewState, review_require, index):
        print("start analyze")
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
            "report_require": review_state["report_require_list"]
        }
        ans = ask_llm_by_prompt_file("mutil_agents/prompts/specific_review/final_report_generate_prompt.j2", data)
        if ans == None or ans["response"] == None or len(ans["response"]) == 0:
            ans = {
                "response": None
            }
        review_state["final_report"] = ans["response"]
        return review_state
    
    def check_report(self, review_state: SpecificReviewState):
        print("start judge")
        ans = ask_llm_by_prompt_file("mutil_agents/prompts/specific_review/judge_report_prompt.j2", review_state)
        if ans == None or ans["response"] == None or len(ans["response"]) == 0:
            ans = {
                "response": {
                    "step": "continue",
                    "info": "ok"
                }
            }
        review_state["judge_result"] = ans["response"]
        print(ans["response"]["step"])
        return ans["response"]["step"]
        