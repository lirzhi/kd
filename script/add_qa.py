import requests
import json

API_URL = 'http://127.0.0.1:5000/qa/add'
JSON_PATH = '../data/raw_data/识林社区问答数据.qa'
CATEGORY = '识林社区问答数据'  # 可根据实际需要修改

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    payload = {
        'category': CATEGORY,
        'question': item.get('question'),
        'answer': item.get('answer')
    }
    resp = requests.post(API_URL, json=payload)
    print(f"{payload['question'][:20]}...: {resp.status_code}, {resp.json()}")
