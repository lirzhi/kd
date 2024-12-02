import re
import pymupdf4llm

from utils.text_util import clean_text

class PdfParser:
    
    def __call__(self, fnm):
        return self.parse_pdf(fnm)
    
    @classmethod
    def parse_pdf(cls, pdf_path):
        md_chunks = pymupdf4llm.to_markdown(
            doc=pdf_path,
            page_chunks=True,
            write_images=True,
            image_path="data/parser/images",
            image_format="png", 
            dpi=300,
        )
        chunks = []
        size = len(md_chunks)
        for index, element in enumerate(md_chunks):
            chunk = {}   
            chunk["chunk_id"] = index + 1
            chunk["image_paths"] = PdfParser.extract_image_paths(element)
            chunk["text"] = clean_text(element["text"]) 
            chunk["size"] = size
            chunk["page"] = element["metadata"]["page"]
            chunks.append(chunk)
        return chunks

    @staticmethod
    def extract_image_paths(chunk):
        # 正则表达式匹配Markdown中的图片路径
        md_text = chunk["text"]
        pattern = r"!\[(.*?)\]\((.*?)\)"
        # 查找所有匹配的图片路径
        image_paths = re.findall(pattern, md_text)
        # 返回一个包含所有图片路径的列表
        return [path[1] for path in image_paths]