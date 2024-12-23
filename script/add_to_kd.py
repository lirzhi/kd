import requests
import time

# Flask 应用的 URL
BASE_URL = "http://127.0.0.1:5000/add_to_kd"

# 读取 doc_id 列表
with open('temp.txt', 'r') as file:
    doc_ids = [line.strip() for line in file.readlines() if line.strip()]

# 遍历 doc_id 列表并调用接口
for doc_id in doc_ids:
    url = f"{BASE_URL}/{doc_id}"
    try:
        response = requests.post(url)  # 使用 POST 请求
        if response.status_code == 200:
            print(f"成功调用接口，doc_id: {doc_id}, 返回信息: {response.json()['code']} {response.json()['message']}")
        else:
            print(f"调用接口失败，doc_id: {doc_id}，状态码: {response.status_code}")
    except Exception as e:
        print(f"调用接口时发生异常，doc_id: {doc_id}，错误信息: {str(e)}")
    
    time.sleep(1)  # 等待1秒再进行下一次调用