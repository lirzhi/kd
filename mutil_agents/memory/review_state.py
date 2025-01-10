from typing import TypedDict, List


class ReviewState(TypedDict):
    task_id: str
    content: str
    content_split_list: List[str]
    content_split_summary_list: List[str]
    content_split_question_list: List[List[str]]
    content_split_search_list: List
    content_split_require_list: List[List[str]]
    content_split_report_list: List[str]
    relate_reference: List
    final_reference: List
    final_report: str
    status: bool
