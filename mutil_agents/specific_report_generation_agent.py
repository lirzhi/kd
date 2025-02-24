from langgraph.graph import StateGraph
from mutil_agents.agents.specific_review.specific_review import SpecificReview
from mutil_agents.memory.specific_review_state import SpecificReviewState
from langgraph.graph import START, END


class SpecificReportGenerationAgent:
    def initialize_agent(self):
        return {
          "review_agent": SpecificReview()
        }
    
    def init_report_generator(self):
        agents = self.initialize_agent()
        return self.create_workflow(agents)


    def add_workflow_edges(self, workflow, agents):
        workflow.add_edge(START, "content_analyze")
        workflow.add_edge("content_analyze", "search_direct_reference")
        workflow.add_edge("search_direct_reference", "generate_report_by_require")
        workflow.add_edge("generate_report_by_require", "generate_final_report")
        workflow.add_conditional_edges("generate_final_report", agents["review_agent"].check_report, {"continue": END, 
                                                                                                      "analyze": "content_analyze",
                                                                                                      "review":"generate_report_by_require",
                                                                                                      "generate": "generate_final_report"})
    def create_workflow(self, agents):
        workflow = StateGraph(SpecificReviewState)
        workflow.add_node("content_analyze", agents["review_agent"].analyze)
        workflow.add_node("search_direct_reference", agents["review_agent"].search)
        workflow.add_node("generate_report_by_require", agents["review_agent"].generate_report_by_require)
        workflow.add_node("generate_final_report", agents["review_agent"].generate_final_report)
        self.add_workflow_edges(workflow, agents)
        return workflow