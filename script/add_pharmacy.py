import requests
import json

API_URL = 'http://127.0.0.1:5000/pharmacy/add'
JSON_PATH = '../data/raw_data/化学药品药典数据.json'

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

fields = ['name', 'prescription', 'characteristic', 'identification', 'inspection', 'content_determination', 'category', 'storage', 'preparation', 'specification']

for name, info in data.items():
    payload = {'name': name}
    payload['prescription'] = info.get('处方')
    payload['characteristic'] = info.get('性状')
    payload['identification'] = info.get('鉴别')
    payload['inspection'] = info.get('检查')
    payload['content_determination'] = info.get('含量测定')
    payload['category'] = info.get('类别')
    payload['storage'] = info.get('贮藏')
    payload['preparation'] = info.get('制剂')
    payload['specification'] = info.get('规格')
    resp = requests.post(API_URL, json=payload)
    print(f'{name}: {resp.status_code}, {resp.json()}')
