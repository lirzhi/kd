
LLM = {
    "model_use": "qwen",
    "models": { 
        "deepseek": {
            "model": "deepseek-reasoner",
            "base_url": "https://api.deepseek.com/v1",
            "api_key_path": "temp/key/deepseek_key",
        },    
        "qwen": {
            "model": "qwen-turbo",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key_path": "temp/key/qwen_key",
        },
        "xh": {
            "model": "generalv3.5",
            "base_url": "https://spark-api-open.xf-yun.com/v1/",
            "api_key_path": "temp/key/xh_key",
        },
        "glm": {
            "model": "glm-4-flash",
            "base_url": "https://open.bigmodel.cn/api/paas/v4/",
            "api_key_path": "temp/key/glm_key",
        },
    }
}