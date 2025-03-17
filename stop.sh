#!/bin/bash

# 终止 llm_server.py 进程
pkill -f llm_server.py

# 终止 app.py 进程
pkill -f app.py

echo "Both llm_server.py and app.py processes have been stopped."