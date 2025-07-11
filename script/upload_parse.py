import os
import requests
from pathlib import Path

def upload_and_process_files(classification , affect_range):
    # 设置路径
    script_dir = Path(r".\script")
    upload_dir = Path(r"..\data\raw_data\law")
    
    # 确保上传目录存在
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # 遍历上传目录中的所有文件
    for filename in os.listdir(upload_dir):
        file_path = upload_dir / filename
        
        # 跳过子目录，只处理文件
        if not file_path.is_file():
            continue
            
        print(f"正在处理文件: {filename}")
        
        # 上传文件到第一个接口
        upload_url = "http://127.0.0.1:5000/upload_file"
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (filename, file)}
                data = {'classification': classification,'affect_range': affect_range}
                response = requests.post(upload_url, files=files, data=data)
                response_data = response.json()
                print(response_data)
                if response.status_code != 200:
                    print(f"文件上传失败: {response.text}")
                    continue
                    
                response_data = response.json()
                if not response_data.get('status'):
                    print(f"文件上传失败: {response_data.get('msg')}")
                    continue
                    
                doc_id = response_data['doc_id']
                print(f"文件上传成功，doc_id: {doc_id}")
                
                # 调用第二个接口处理文档
                process_url = f"http://127.0.0.1:5000/add_to_kd/{doc_id}"
                process_response = requests.post(process_url)
                
                if process_response.status_code != 200:
                    print(f"文档处理失败: {process_response.text}")
                else:
                    print(f"文档处理成功: {process_response.json().get('message')}")
                    
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {str(e)}")
            continue

if __name__ == "__main__":
    classification = "法律法规"
    affect_range ="法律法规"
    upload_and_process_files(classification , affect_range)