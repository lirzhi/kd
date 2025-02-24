from mutil_agents.data_process_agent import DataProcessAgent
from mutil_agents.report_generation_agent import ReportGenerationAgent
from mutil_agents.specific_report_generation_agent import SpecificReportGenerationAgent


report_generator = ReportGenerationAgent()
workflow = report_generator.init_report_generator()
graph = workflow.compile()

data_process_agent = DataProcessAgent()
data_workflow = data_process_agent.init_report_generator()
data_graph = data_workflow.compile()

specific_report_generationAgent = SpecificReportGenerationAgent()
specific_report_generationAgent_workflow = specific_report_generationAgent.init_report_generator()
specific_report_generationAgent_graph = specific_report_generationAgent_workflow.compile()