from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from db.services.kd_service import KDService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.review_state import ReviewState
from utils.common_util import parallelize_processing


class SearchAgent:
    @parallelize_processing(field_to_iterate='content_split_list', result_field='relate_reference')
    def search_direct_reference(self, review_state: ReviewState, split_text) -> dict:
        print("search_direct_reference...")
        result = KDService().search_by_vector(split_text)
        ans = []
        for item in result:
            ans.append(
                { "reference": item["entity"]["doc_id"], "content": item["entity"]["text"] }
            )
        return ans

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
        ans = ask_llm_by_prompt_file("mutil_agents/prompts/review/requirement_generate_prompt.j2", data)
        if ans is None or ans["response"] is None or len(ans["response"]) == 0:
            ans = {}
            ans["response"] = []
        if not isinstance(ans["response"], list):
            ans["response"] = [ans["response"]]
        return ans["response"]
    

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
            ans = ask_llm_by_prompt_file("mutil_agents/prompts/review/generate_prompt.j2", data)
            if ans is None or ans["response"] is None or len(ans["response"]) == 0:
                ans = {}
                ans["response"] = []
            if not isinstance(ans["response"], list):
                ans["response"] = [ans["response"]]
            answer.append(ans["response"])
        return answer

