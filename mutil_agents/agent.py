from mutil_agents.data_process_agent import DataProcessAgent
from mutil_agents.report_generation_agent import ReportGenerationAgent

report_generator = ReportGenerationAgent()
workflow = report_generator.init_report_generator()
graph = workflow.compile()

data_process_agent = DataProcessAgent()
data_workflow = data_process_agent.init_report_generator()
data_graph = data_workflow.compile()