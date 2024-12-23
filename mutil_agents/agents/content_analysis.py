from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file
from mutil_agents.memory.review_state import ReviewState


class ContentAnalyzeAgent:
    def analyze(self, review_state: ReviewState) -> dict:
        print("analyzing...")
        if ReviewState["content"] == None or ReviewState["content"] == "":
                    return ReviewState
        ans = ask_llm_by_prompt_file("mutil_agents/agents/prompts/content_analyze_prompt.j2", review_state)
        if ans == None or ans["response"] == None or len(ans["response"]) == 0:
               review_state["status"] = False
               return review_state
        review_state["content_split_list"] = []
        review_state["content_split_summary_list"]  = []
        review_state["content_split_question_list"]  = []
        if type(ans["response"]) != list:
            ans["response"] = [ans["response"]]
        for item in ans["response"]:
            review_state["content_split_list"].append(item["content"])
            review_state["content_split_summary_list"].append(item["summary"])
            if item["question"] == None or len(item["question"]) == 0:
                review_state["content_split_question_list"].append([])
            else:
                if type(item["question"]) != list:
                    item["question"] = [item["question"]]
                review_state["content_split_question_list"].append(item["question"])
        return review_state
    
