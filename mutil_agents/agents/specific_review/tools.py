import json
from sqlalchemy import text
from db.dbutils.mysql_conn import MysqlConnection
from db.dbutils.redis_conn import RedisDB
from db.services.kd_service import KDService
from mutil_agents.agents.utils.llm_util import ask_llm_by_prompt_file


tools = {
    "指导原则检索工具":{
        "parameters": {
            "eCTD_module": "string:eCTD章节的编号，例如：3.2.S.4.2",
            "module_name": "string:章节名称",
            "principle_name": "string:指导原则文件名称：如Q6A等， 非必填"
        },
        "description": "根据eCTD章节或指导原则名称获取相关指导原则信息"
    },

    "药品信息检索工具":{
        "parameters": {
            "medicine_query": "string:对于药品检索的具体问题，例如：XXX药品的性状是什么？",
        },
        "description": "通过药品问题检索是否有相关信息"
    },

    "分析方法检索工具":{
        "parameters": {
            "method_name": "string:当前审评药品质量方法的分析方法名称",
        },
        "description": "根据药品的鉴定类型（例如溶解度、比旋度、碱度等等）获取相关鉴定方法信息,检索数据属于药典标准检测方法"
    },    
}

class Tools:
    @staticmethod
    def search_principle(eCTD_module, module_name, principle_name=None):
        # 寻找直接可获取的指导原则
        value = RedisDB().get(f"principle+{eCTD_module}")
        print(f"search redis: {value}")
        if value is None:
            value = []
        else:
            value = json.loads(value)
            if module_name is None or len(module_name) == 0:
                module_name = value.get("章节名称", "")
            value = value.get("报告要求", [])
            
        # 从非结构化数据寻找指导原则
        if module_name is not None:
            query = f"{module_name}部分包含什么指导要求 ？"
            search_info = KDService().search_by_query(query=query)
            data = {
                "query": query,
                "search_info": search_info
            }
            resp = ask_llm_by_prompt_file("mutil_agents/prompts/data_access_format/principle2list.j2", data)
            if resp is not None and len(resp["response"]) > 0:
                value += resp["response"]
        print(f"value:{value}")
        # value = [value[0:2]]
        return value  

    @staticmethod   
    def search_medicine(medicine_query):
        # 获取表结构
        struct_info = MysqlConnection().get_table_structure_with_comments("medicines")
        table_name = "medicines"
        data = {
            "struct_info": struct_info,
            "table_name": table_name,
            "query": medicine_query,
            "sql": "",
            "error": None
        }

        # 构建查询语句
        sql = ask_llm_by_prompt_file("mutil_agents/prompts/data_access_format/text2sql.j2", data)['response']['sql']
        data["sql"] = sql
        # 查询数据库
        retries = 2
        for attempt in range(retries):
            try:
                result = MysqlConnection().get_session().execute(text(sql)).fetchall()
                break
            except Exception as e:
                if attempt == retries - 1:
                    return None
                data['error'] = str(e)
                sql = ask_llm_by_prompt_file("mutil_agents/prompts/data_access_format/text2sql.j2", data)['response']['sql']
                data["sql"] = sql
        return result
    
    @staticmethod
    def search_analyze_method(method_name):
        return RedisDB().get(method_name)

methods_mapping = {
     "指导原则检索工具": Tools.search_principle,  
     "药品信息检索工具": Tools.search_medicine,
     "分析方法检索工具": Tools.search_analyze_method,
}