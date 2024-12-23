from mutil_agents.agents.report_generation import ReportGenerationAgent

report_generator = ReportGenerationAgent()
workflow = report_generator.init_report_generator()
graph = workflow.compile()

