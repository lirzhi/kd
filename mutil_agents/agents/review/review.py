import logging
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.review_state import ReviewState
from utils.common_util import parallelize_processing


class ReviewAgent:
    @parallelize_processing(field_to_iterate='content_split_list', result_field='content_split_report_list')
    def single_review(self, review_state: ReviewState, split_text) -> dict:
        index = review_state["content_split_list"].index(split_text)
        data = {}
        data["content"] = split_text
        data["content_split_require_list"] = review_state["content_split_require_list"][index]
        data["content_split_question_list"] = review_state["content_split_question_list"][index]
        data["conten_split_search_list"] = review_state["content_split_search_list"][index]
        data["relate_reference"] = review_state["relate_reference"][index]
        ans = ask_llm_by_prompt_file("mutil_agents/prompts/review/single_review_prompt.j2", data)
        if ans == None or ans["response"] == None:
            ans["response"] = ""
        if not isinstance(ans["response"], list):
            ans["response"] = [ans["response"]]
        return ans["response"]
    
    def review_report(self, review_state: ReviewState) -> dict:
        reference = []
        review_state["final_reference"] = []
        for items in review_state["content_split_report_list"]:
           for item in items:
                if item["conclusion"]["reference"] not in reference:
                    reference.append(item["conclusion"]["reference"])
        for item in review_state["relate_reference"]:
            for ref in item:
                if ref["reference"] in reference:
                   review_state["final_reference"].append(ref)

        for answers in review_state["content_split_search_list"]:
            for answer in answers:
                for ref in answer:
                    if ref["reference"] in reference:
                        review_state["final_reference"].append(ref)


        ans = ask_llm_by_prompt_file("mutil_agents/prompts/review/review_report_prompt.j2", review_state)
        if ans == None or ans["response"] == None:
            logging.error(f"review error: ans is None") 
            ans = ""
        review_state["final_report"] = ans["response"]["report"]
        return review_state