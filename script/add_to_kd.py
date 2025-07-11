import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BASE_URL = "http://127.0.0.1:5000"
GET_FILE_URL = f"{BASE_URL}/get_file_by_class/all"
ADD_TO_KD_URL = f"{BASE_URL}/add_to_kd"

PAGE_SIZE = 20  # 每页数量，可根据实际情况调整
MAX_WORKERS = 8  # 线程池最大线程数

doc_id_lock = threading.Lock()
processed_doc_ids = set()

def get_all_unparsed_doc_ids():
    doc_ids = []
    page = 1
    while True:
        params = {
            "page": page,
            "limit": PAGE_SIZE
        }
        try:
            resp = requests.get(GET_FILE_URL, params=params)
            data = resp.json()
            if data.get("code") != 200 or not data.get("data"):
                print(f"获取第{page}页文件失败: {data.get('msg')}")
                break
            file_list = data["data"]["list"]
            if not file_list:
                break
            for item in file_list:
                # 只处理未解析（parse_status为0或False或None）的文件
                if not item.get("parse_status", 0):
                    doc_ids.append(item["doc_id"])
            if len(file_list) < PAGE_SIZE:
                break  # 最后一页
            page += 1
        except Exception as e:
            print(f"请求文件列表异常: {e}")
            break
    return doc_ids

def add_to_kd(doc_id):
    with doc_id_lock:
        if doc_id in processed_doc_ids:
            return  # 已处理，跳过
        processed_doc_ids.add(doc_id)
    url = f"{ADD_TO_KD_URL}/{doc_id}"
    try:
        resp = requests.post(url)
        if resp.status_code == 200:
            res = resp.json()
            print(f"doc_id: {doc_id} 解析结果: {res.get('code')} {res.get('msg')}")
        else:
            print(f"doc_id: {doc_id} 解析失败，状态码: {resp.status_code}")
    except Exception as e:
        print(f"doc_id: {doc_id} 调用解析接口异常: {e}")
    time.sleep(1)  # 避免接口压力过大

if __name__ == "__main__":
    doc_ids = get_all_unparsed_doc_ids()
    print(f"共获取到 {len(doc_ids)} 个未解析文件，开始多线程批量解析...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(add_to_kd, doc_id): doc_id for doc_id in doc_ids}
        for idx, future in enumerate(as_completed(futures), 1):
            doc_id = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"doc_id: {doc_id} 解析时发生异常: {exc}")
    print("全部未解析文件处理完成。")