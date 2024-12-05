from utils.parser.docx_parser import DocxParser
from utils.parser.parser_manager import ParserManager
from utils.parser.pdf_parser import PdfParser
from utils.parser.qa_parser import QAParser


ParserManager.register_parser('pdf', PdfParser())
ParserManager.register_parser('docx', DocxParser())
ParserManager.register_parser('qa', QAParser())

