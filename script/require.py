import json
import requests

def read_json_file(file_path):
    """读取JSON文件并返回数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"读取JSON文件出错: {e}")
        return None

def post_to_api(section_id, content):
    """调用API接口上传数据"""
    url = "http://127.0.0.1:5000/set_principle_content"
    payload = {
        "section_id": section_id,
        "content": content
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 检查请求是否成功
        print(f"成功上传 section_id: {section_id}, 响应: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"上传 section_id {section_id} 失败: {e}")

def process_json_data(json_data):
    """处理JSON数据并调用API"""
    if not json_data:
        print("JSON数据为空，无法处理")
        return
    
    for section_id, section_data in json_data.items():
        # 获取自评估关注点内容
        assessment_points = section_data.get("自评估关注点", [])
        # print(section_id)
        # print(assessment_points)
        # 如果自评估关注点不为空，则调用API
        if assessment_points:
            post_to_api(section_id, assessment_points)

def main():
    # JSON文件路径
    json_file_path = "./data/raw_data/require.json"
    
    # 读取JSON文件
    json_data = read_json_file(json_file_path)
    
    # 处理数据并调用API
    if json_data:
        process_json_data(json_data)

if __name__ == "__main__":
    main()