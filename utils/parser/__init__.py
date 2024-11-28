from utils.parser.parser_manager import ParserManager
from utils.parser.pdf_parser import PdfParser


ParserManager.registaer_parser('pdf', PdfParser())