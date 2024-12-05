from utils.parser.docx_parser import DocxParser
from utils.parser.parser_manager import ParserManager
from utils.parser.pdf_parser import PdfParser


ParserManager.register_parser('pdf', PdfParser())
ParserManager.register_parser('docx', DocxParser())