from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.review_state import ReviewState


class ReviewAgent:
    def single_review(self, review_state: ReviewState) -> dict:
        review_state["content_split_report_list"] = []
        ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/review_prompt.j2", review_state)
        if ans == None or ans["response"] == None or len(ans["response"]) == 0:
            ans = {}
            ans["response"] = []
        if type(ans["response"]) != list:
            ans["response"] = [ans["response"]]
        review_state["content_split_report_list"] = ans["response"]
        review_state["review_report"] = ans["report"]
        return review_state