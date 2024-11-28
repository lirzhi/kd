from utils.docx_parser import RAGFlowDocxParser
from utils.txt_parser import RAGFlowTxtParser

# 创建DocxParser实例
parser = RAGFlowDocxParser()

# 解析.docx文档
file_path = 'data/uploads/test.docx'
parsed_content, parsed_table = parser(file_path)
print(type)
# 打印解析后的内容
# for section in parsed_content:
#     print(type(section))
#     for block in section:
#         print(block)
#     print('----------------')
#     break

for table in parsed_table:
    print(table)
    print('----------------')
    break


txt_parser = RAGFlowTxtParser()
file_path = 'data/uploads/test.txt'
parsed_content = txt_parser(file_path)
for section in parsed_content:
    print(section)
    print('----------------')
    break