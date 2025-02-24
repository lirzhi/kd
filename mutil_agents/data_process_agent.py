from mutil_agents.agents.data_process.data_process import DataProcess
from langgraph.graph import StateGraph
from langgraph.graph import START, END

from mutil_agents.memory.data_state import DataState

class DataProcessAgent:

    def initialize_agent(self):
        return {
            "data_process": DataProcess(),
        }
    
    def init_report_generator(self):
        agents = self.initialize_agent()
        return self.create_workflow(agents)


    def add_workflow_edges(self, workflow, agents):
        workflow.add_edge(START, "parse_file")
        workflow.add_conditional_edges("parse_file", agents["data_process"].check_parse, {"stop": END, "continue": "chunk_clean"})
        workflow.add_edge("chunk_clean", "content_split")
        workflow.add_edge("content_split", "content_question_add")
        workflow.add_edge("content_question_add", END)

    def create_workflow(self, agents):
        workflow = StateGraph(DataState)
        workflow.add_node("parse_file", agents["data_process"].parse_file)
        workflow.add_node("chunk_clean", agents["data_process"].chunk_clean)
        workflow.add_node("content_split", agents["data_process"].content_split)
        workflow.add_node("content_question_add", agents["data_process"].content_question_add)
       
        self.add_workflow_edges(workflow, agents)
        return workflow