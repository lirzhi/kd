from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from db.services.kd_service import KDService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.review_state import ReviewState
from utils.common_util import parallelize_processing


class SearchAgent:
    def search_direct_reference(self, review_state: ReviewState) -> dict:
        print("search_direct_reference...")
        result = KDService().search_by_vector(review_state["content"])
        review_state["relate_reference"] = []
        for item in result:
            review_state["relate_reference"].append(item["entity"]["text"])
        return review_state
    
    # def search_requirements(self, review_state: ReviewState) -> dict:
    #     print("search_requirements...")
    #     # 可以使用并行处理优化
    #     review_state["content_split_require_list"] = []
    #     for split_text in review_state["content_split_list"]:
    #         result = KDService().search_by_vector(split_text)
    #         data = {}
    #         data["query"] = split_text
    #         data["content"] = []
    #         data["reference"] = []
    #         for items in result:
    #             for item in items:
    #                 data["content"].append(item["entity"]["text"])
    #                 data["reference"].append(item["entity"]["doc_id"])     
    #         ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/requirement_generate_prompt.j2", data)
    #         if ans == None or ans["response"] == None or len(ans["response"]) == 0:
    #             ans = {}
    #             ans["response"] = []
    #         if type(ans["response"]) != list:
    #             ans["response"] = [ans["response"]]
    #         review_state["content_split_require_list"].append(ans["response"])
    #     return review_state

    @parallelize_processing(field_to_iterate='content_split_list', result_field='content_split_require_list')
    def search_requirements(self, review_state: ReviewState, split_text):
        result = KDService().search_by_vector(split_text, ["指导原则"])
        if len(result) == 0:
            return []
        data = {}
        data["query"] = split_text
        data["content"] = []
        data["reference"] = []
        for item in result:
            data["content"].append(item["entity"]["text"])
            data["reference"].append(item["entity"]["doc_id"])
        ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/requirement_generate_prompt.j2", data)
        if ans is None or ans["response"] is None or len(ans["response"]) == 0:
            ans = {}
            ans["response"] = []
        if not isinstance(ans["response"], list):
            ans["response"] = [ans["response"]]
        return ans["response"]
        
    # def search_questions(self, review_state: ReviewState) -> dict:
    #     print("search_questions...")
    #     # 可以使用并行处理优化
    #     review_state["content_split_search_list"] = []
    #     for questions in review_state["content_split_question_list"]:
    #         answer = []
    #         for question in questions:
    #             result = KDService().search_by_vector(question)
    #             data = {}
    #             data["query"] = question
    #             data["content"] = []
    #             data["reference"] = []
    #             for items in result:
    #                 for item in items:
    #                     data["content"].append(item["entity"]["text"])
    #                     data["reference"].append(item["entity"]["doc_id"])     
    #             ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/generate_prompt.j2", data)
    #             if ans == None or ans["response"] == None or len(ans["response"]) == 0:
    #                 ans = {}
    #                 ans["response"] = []
    #             if type(ans["response"]) != list:
    #                 ans["response"] = [ans["response"]]
    #             answer.append(ans["response"])
    #         review_state["content_split_search_list"].append(answer)
    #     return review_state
    

    @parallelize_processing(field_to_iterate='content_split_question_list', result_field='content_split_search_list')
    def search_questions(self, review_state: ReviewState, questions):
        answer = []
        for question in questions:
            result = KDService().search_by_vector(question)
            data = {}
            data["query"] = question
            data["content"] = []
            data["reference"] = []
            for item in result:
                data["content"].append(item["entity"]["text"])
                data["reference"].append(item["entity"]["doc_id"])
            ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/generate_prompt.j2", data)
            if ans is None or ans["response"] is None or len(ans["response"]) == 0:
                ans = {}
                ans["response"] = []
            if not isinstance(ans["response"], list):
                ans["response"] = [ans["response"]]
            answer.append(ans["response"])
        return answer

