import json
from jinja2 import Environment, FileSystemLoader


env = Environment(loader=FileSystemLoader('.'))
# 注册 'loads' 过滤器
def json_loads(value):
    return json.loads(value)

env.filters['loads'] = json_loads
