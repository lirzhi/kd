tools = {
    "指导原则检索工具":{
        "parameters": {
            "medical_type": "string:药品的类型,比如化学药、原料药等（不强制指定，可为空）",
            "priciple_name": "string:指导原则的名字(如:Q6A)，可选",
            "affected_section": "string:指导原则的章节"
        },
        "description": "根据药品类型和章节获取相关指导原则信息"
    },

    "药品信息检索工具":{
        "parameters": {
            "medicine_name": "string:当前审评药品的类型",
        },
        "description": "通过药品名称检索是否有相关信息"
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
    def search_principle(eCTD_module, medical_type=None):
        return "指导原则检索工具被调用， ectd_module: {}, medical_type: {}".format(eCTD_module, medical_type)  

    @staticmethod   
    def search_medicine(medicine_name):
        return "药品信息检索工具被调用， medicine_name: {}".format(medicine_name)
    
    @staticmethod
    def search_analyze_method(method_name):
        return "分析方法检索工具被调用， method_name: {}".format(method_name)

methods_mapping = {
     "指导原则检索工具": Tools.search_principle,  
     "药品信息检索工具": Tools.search_medicine,
     "分析方法检索工具": Tools.search_analyze_method,
     
}
