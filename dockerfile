# ===================== 基础层（永不变化） =====================
# 使用官方 Python 3.10.15 镜像作为基础镜像
FROM python:3.10.15-slim

# ===================== 系统依赖层（低频变化） =====================
# 安装系统级编译工具（合并 RUN 减少层数）
# 安装系统级编译工具（合并 RUN 减少层数）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    graphviz \
    graphviz-dev \
    && rm -rf /var/lib/apt/lists/*

RUN apt update

# ===================== 环境配置层（中频变化） =====================
WORKDIR /knowledge_database

# ===================== 依赖安装层（中频变化） =====================
# 优先复制依赖声明文件（触发缓存失效的关键层）
COPY requirements.txt .
RUN pip install --upgrade pip setuptools && \
pip install --no-deps --ignore-requires-python -r requirements.txt

# ===================== 静态文件层（低频变化） =====================
COPY conf/ ./conf/
COPY db/ ./db/
COPY templates/ ./templates/
COPY utils/ ./utils/

# ===================== 动态代码层（高频变化） =====================
COPY llm/ ./llm/
COPY mutil_agents/ ./mutil_agents/
COPY app.py .
COPY start.sh .
COPY stop.sh .
# ===================== 运行时配置层 =====================
EXPOSE 5000

RUN apt install dos2unix
RUN dos2unix start.sh
CMD ["/bin/bash", "start.sh"]