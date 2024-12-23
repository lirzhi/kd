import requests
from bs4 import BeautifulSoup
import os

def upload_files_and_extract_doc_id(upload_dir, classification, affect_range):
    # Flask 应用的 URL
    upload_url = "http://localhost:5000/upload_file"

    # 确保上传目录存在
    if not os.path.isdir(upload_dir):
        print(f"Upload directory {upload_dir} does not exist.")
        return

    # 遍历 upload_dir 目录下的所有文件
    for file_name in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, file_name)
        if os.path.isfile(file_path):
            # 使用 requests 上传文件
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f)}
                data = {
                    'classification': classification,
                    'affect_range': affect_range
                }
                response = requests.post(upload_url, files=files, data=data)
                
                # 检查响应状态
                if response.status_code == 200:   
                    # 保存 doc_id 到临时文件
                    if response.json()['code'] == 200 :
                        doc_id = response.json()['data']['doc_id']  
                        with open('temp.txt', 'a') as temp_file:
                            temp_file.write(doc_id + '\n')  # 每行一个 doc_id
                        print(f"文件 {file_name} 上传成功，doc_id: {doc_id}")
                    else:
                        print(f"{file_name} 上传失败，原因:", response.json()['message'])
                else:
                    print(f"文件 {file_name} 上传失败，状态码：{response.status_code}")

# 使用示例
upload_dir = '../data/raw_data/现行药品注册法规汇总/3.临床试验实施/3.4试验符合性/None/None/'
classification = '现行药品注册法规汇总'
affect_range = '3.1.1'
upload_files_and_extract_doc_id(upload_dir, classification, affect_range)