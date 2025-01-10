from langgraph.graph import StateGraph
from mutil_agents.agents.content_analysis import ContentAnalyzeAgent
from mutil_agents.agents.review import ReviewAgent
from mutil_agents.agents.search import SearchAgent
from mutil_agents.memory.review_state import ReviewState
from langgraph.graph import START, END


class ReportGenerationAgent:

    def initialize_agent(self):
        return {
            "content_analyze": ContentAnalyzeAgent(),
            "search": SearchAgent(),
            "review": ReviewAgent(),
        }
    
    def init_report_generator(self):
        agents = self.initialize_agent()
        return self.create_workflow(agents)


    def add_workflow_edges(self, workflow):
        workflow.add_edge(START, "content_analyze")
        workflow.add_edge("content_analyze", "search_direct_reference")
        workflow.add_edge("search_direct_reference", "search_requirements")
        workflow.add_edge("search_requirements", "search_questions")
        workflow.add_edge("search_questions", "single_review")
        workflow.add_edge("single_review", "generate_report")
        workflow.add_edge("generate_report", END)

    def create_workflow(self, agents):
        workflow = StateGraph(ReviewState)
        workflow.add_node("content_analyze", agents["content_analyze"].analyze)
        workflow.add_node("search_direct_reference", agents["search"].search_direct_reference)
        workflow.add_node("search_requirements", agents["search"].search_requirements)
        workflow.add_node("search_questions", agents["search"].search_questions)
        workflow.add_node("single_review", agents["review"].single_review)
        workflow.add_node("generate_report", agents["review"].review_report)
        self.add_workflow_edges(workflow)
        return workflow

    