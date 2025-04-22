from copy import deepcopy
import logging
import os

from docx import Document
from db.dbutils import singleton
from db.dbutils.redis_conn import RedisDB
from db.ectd_model import EctdSectionModel
from db.services.file_service import FileService
from mutil_agents.memory.specific_review_state import SpecificReviewState
from mutil_agents.agent import specific_report_generationAgent_graph

ReportInfo = {
        "status": 0,
        "message": "success",
        "data": None
}

REPORT_DIR = "data/reports/"  # Set the target folder for report generation
@singleton
class ReportService:
    def __init__(self):
        self.redis_conn = RedisDB()

    def ectd_judge(self, doc_id):
        resp_info = deepcopy(ReportInfo)
        # 根据eCTD的doc_id生成最终报告
        # 获取doc_id对应的文件信息
        
        file_info = FileService().get_file_by_id(doc_id)
        if file_info is None:
            resp_info["message"] = "文件不存在" 
            return resp_info
        
        if file_info.classification != "eCTD":
            resp_info["message"] = "文件类型不是eCTD"
            return resp_info
        
        if file_info.is_chunked != 1:
            resp_info["message"] = "eCTD未解析,解析后在试"
            return resp_info    

    def generate_report_by_section(self, section_id, section_name, content):
        # 按章节生成内容,生成完成后将内容存入数据库，并返回生成的内容
        review_state = SpecificReviewState()
        review_state["content"] = content
        review_state["content_section"] = section_name
        review_require_list = self.redis_conn.get(f"principle+{section_id}")
        if review_require_list is None:
            logging.warning(f"{section_id}章节要求不存在")
            review_require_list = []
        review_state["review_require_list"] = review_require_list
        result = specific_report_generationAgent_graph.invoke(review_state)
        return result
        

    def create_final_report(self, doc_id):
        resp_info = deepcopy(ReportInfo)
        # 根据eCTD的doc_id生成最终报告
        # 获取doc_id对应的文件信息
        judge_info = self.ectd_judge(doc_id)
        if judge_info["status"] == 0:
            return judge_info
            
        report = deepcopy.deepcopy(EctdSectionModel)   
        # 1. 根据框架获取所有章节信息
        for section in report:
            if len(section["children_sections"]) == 0:
                # 章节没有子章节，直接生成内容
                section_id = section["section_id"]
                section_name = section["section_name"]
                section_content = self.redis_conn.get(f"section_content+{doc_id}+{section_id}")
                if section_content is None:
                    logging.warning(f"{doc_id}章节内容不存在，章节ID：{section_id}")
                    continue
                section_report = self.generate_report_by_section(section_id, section_name, section_content)
                section["report"] = section_report["final_report"]
            else:
                # 章节有子章节，递归生成内容
                for child_section in section["children_sections"]:
                    child_section_id = child_section["section_id"]
                    child_section_name = child_section["section_name"]
                    child_section_content = self.redis_conn.get(f"section_content+{doc_id}+{child_section_id}")
                    if child_section_content is None:
                        logging.warning(f"{doc_id}章节内容不存在，章节ID：{child_section_id}")
                        continue
                    content = self.generate_report_by_section(child_section_id, child_section_name, child_section_content)
                    # 将生成的内容存入数据库
                    child_section["report"] = content["final_report"]
        resp_info["data"] = report
        return resp_info            

    def add_section_to_doc(self, doc_id, doc, section, level=0):
        """递归添加章节到文档"""
        # 添加章节标题
        doc.add_heading(f"{section['section_id']} {section['section_name']}", level=level)
        
        # 添加章节正文内容
        if self.redis_conn.exists(f"review_content+{doc_id}+{section['section_id']}"):
            content = self.redis_conn.get(f"review_content+{doc_id}+{section['section_id']}")
            if content:
                doc.add_paragraph(content)
        
        # 如果有子章节，递归添加
        for child in section.get("children_sections", []):
            self.add_section_to_doc(doc_id, doc, child, level=level + 1)

    def export_report(self, doc_id):
        # Logic to update an existing report in the database
        resp_info = deepcopy(ReportInfo)
        judge_info = self.ectd_judge(doc_id)
        if len(self.redis_conn.keys(f"review_content+{doc_id}*")) == 0:
            resp_info["message"] = "还没有章节生成报告内容"
            resp_info["status"] = 0
            return resp_info
        if judge_info["status"] == 0:
            return judge_info
        
        # 1. 根据框架获取所有章节信息
        report = deepcopy.deepcopy(EctdSectionModel)

            # 创建一个新的 Word 文档
        doc = Document()
        
        # 遍历顶级章节并添加到文档
        for section in report:
            self.add_section_to_doc(doc_id, doc, section)
        
        # 保存文档
        file_path = f"{REPORT_DIR}{doc_id}_report.docx"
        doc.save(file_path)
        resp_info["message"] = "报告生成成功"
        resp_info["status"] = 1
        resp_info["data"] = file_path
        return resp_info
        

    def delete_report(self, doc_id):
        # Logic to delete a report from the database
        if self.redis_conn.exists(f"review_content+{doc_id}*"):
            self.redis_conn.delete(f"review_content+{doc_id}*")
        if os.path.exists(f"{REPORT_DIR}{doc_id}_report.docx"):
            os.remove(f"{REPORT_DIR}{doc_id}_report.docx")
            return True
        else:
            logging.warning(f"Report file {doc_id}_report.docx does not exist.")
            return False
        