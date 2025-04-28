
from typing import List, TypedDict


class SpecificReviewState(TypedDict):
    task_id: str                    # 任务ID
    content: str                    # 待审内容
    content_section: str            # 待审章节编号
    content_section_name: str       # 待审章节名称
    review_require_list: List[str]  # 指导原则要求列表
    search_plan_list: List          # 搜索计划列表
    search_list: List               # 搜索结果列表
    review_result_list: List        # 评估结果列表
    report_require_list: List[str]  # 报告撰写要求
    final_report: List[str]               # 最终报告
    final_report_content: str
    judge_result: dict              # 评估结果
