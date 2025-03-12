import fitz
import pdfplumber
import re
import json
from dataclasses import dataclass
from typing import List

@dataclass
class Section:
    id: str
    name: str
    start_page: int = 0       # 章节起始页码
    start_y: float = 0.0      # 章节起始Y坐标
    content: str = ""
    tables: List[str] = None

    def __post_init__(self):
        self.tables = []

class CTDPDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.sections = []    # 扁平存储所有章节
        self.current_section = None
        self.header_pattern = re.compile(
            r'(\d+\.\d+\.(?:S|P)\.\d+(?:\.\d)*)\s*([^\n]+)', 
            re.MULTILINE
        )
        
        # 记录所有表格的位置信息（page_num, y0, table_md）
        self.table_positions = []

    def parse(self) -> List[dict]:
        # 第一阶段：提取所有表格及其位置
        self._extract_tables_with_positions()
        
        # 第二阶段：构建章节结构并填充内容
        self._build_sections()
        
        # 第三阶段：关联表格到章节
        self._assign_tables_to_sections()

        # 构建返回数据
        data = {
            "file_name": self.pdf_path.split('/')[-1].rsplit('.', 1)[0],
            "content": [self._serialize(s) for s in self.sections]
        }
        return data

    def _extract_tables_with_positions(self):
        """提取表格并记录位置信息"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # 提取表格的垂直坐标（取表格顶部）
                tables = page.find_tables()
                for table in tables:
                    bbox = table.bbox
                    table_data = page.crop(bbox).extract_table()
                    md_table = self._table_to_markdown(table_data)
                    self.table_positions.append((
                        page_num,
                        bbox[1],  # y0坐标
                        md_table
                    ))

    def _build_sections(self):
        """构建扁平章节结构并收集内容"""
        with fitz.open(self.pdf_path) as doc:
            for page_num, page in enumerate(doc):
                blocks = page.get_text("blocks", sort=True)
                
                for block in blocks:
                    text = block[4].strip()
                    y0 = block[1]  # 文本块顶部坐标
                    
                    if match := self.header_pattern.match(text):
                        # 遇到新章节时结束当前章节
                        if self.current_section:
                            self.sections.append(self.current_section)
                            
                        self.current_section = Section(
                            id=match.group(1),
                            name=match.group(2),
                            start_page=page_num,
                            start_y=y0
                        )
                    elif text and self.current_section:
                        self.current_section.content += text + "\n"
                
                # 页面处理完成后保存当前章节
                if self.current_section and page_num == len(doc)-1:
                    self.sections.append(self.current_section)

    def _assign_tables_to_sections(self):
        """将表格分配给对应的章节"""
        # 按位置排序表格（先页码后y坐标）
        sorted_tables = sorted(self.table_positions, key=lambda x: (x[0], x[1]))
        
        for section in self.sections:
            # 找到在该章节区域内的表格（相同页码且y坐标在章节内容之后）
            for table in sorted_tables:
                if (table[0] == section.start_page and 
                    table[1] > section.start_y):
                    section.tables.append(table[2])
                    sorted_tables.remove(table)  # 避免重复分配

    @staticmethod
    def _table_to_markdown(table: List[List[str]]) -> str:
        """生成Markdown格式表格"""
        if not table or len(table[0]) == 0:
            return ""
        
        markdown = []
        headers = table[0]
        markdown.append("| " + " | ".join(headers) + " |")
        markdown.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in table[1:]:
            markdown.append("| " + " | ".join(str(cell) for cell in row) + " |")
        return "\n".join(markdown)

    @staticmethod
    def _serialize(section: Section) -> dict:
        return {
            "section_id": section.id,
            "section_name": section.name,
            "content": section.content.strip(),
            "tables": section.tables
        }

    def save_json(self, output_path: str):
        data = self.parse()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = CTDPDFParser("CTD资料.pdf")
    parser.save_json("flat_output.json")
    print("解析完成！结果已保存为 flat_output.json")