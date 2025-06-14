import json
import logging
from multiprocessing import Pool
import re
import time
import requests
import xmltodict
from ... import env

def ask_llm(content="", mode="qwen"):
    if mode == "ollama":
        model = "gemma2"
        url = "http://localhost:11434/api/generate"  # 本地ollama提供的api
        data = {"model": model, "prompt": content, "stream": False, "context": []}

        headers = {"Content-Type": "application/json"}

        begin_time = time.time()
        response = requests.post(url, data=json.dumps(data), headers=headers)
        resp_time = time.time()
        full_answer = response.json()["response"]
        output_time_count = resp_time - begin_time
        print(
            f"token生成速度:{round(len(full_answer) / output_time_count, 3)}字符/秒，"
            f"token生成耗时{round(output_time_count, 3)}秒"
        )
        return full_answer
    elif mode == "gpt":
        url = "http://localhost:9012/chat"
        data = {
            "chat_history": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. 请使用中文回答问题",
                },
                {"role": "user", "content": content},
            ],
        }
        response = requests.post(url, json=data)
        return response.json()["answer"]

    elif mode == "qwen":
        url = "http://localhost:8024/fastchat"
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. 请使用中文回答问题",
                },
                {"role": "user", "content": content},
            ],
        }
        response = requests.post(url, json=data)
        return response.text

def ask_llm_by_prompt_file(file_name, data="", mode="qwen"):
    template = env.get_template(file_name)
    answer = ask_llm(template.render(data=data), mode)
    xml_str = extract_xml_str(answer)
    if xml_str:
            xml_str = xml_str.replace(r"\n", "")  # 有时模型输出的xml会有很多换行符号，需要去掉
            xml_str = xml_str.replace("&", " ")
            data = convert_xml_to_dict(xml_str)
            if data:
                return data
    logging.warning(f"模型访问失败，返回原始字符串：{answer}")
    return None


def convert_xml_to_dict(xml_str):
    xml_str = "<output>" + xml_str + "</output>"  # 需要加上root标签以转dict
    # 尝试转为json
    try:
        xml_dict = xmltodict.parse(xml_str)
    except:
        return False
    # 去掉root节点
    xml_dict = xml_dict[list(xml_dict.keys())[0]]
    return xml_dict


def extract_xml_str(answer):
    # 尝试读取出xml的字符串，output标签为统一的标准根节点，不同的prompt都要输出这个
    pattern = r"<output>(.*?)</output>"
    matches = re.findall(pattern, answer, re.DOTALL)
    if len(matches) != 1:
        return False
    return matches[0]