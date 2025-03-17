# 使用官方 Python 3.8 镜像作为基础镜像
FROM python:3.10

# 设置工作目录为 /app
WORKDIR /app

# 复制 requirements.txt 文件到工作目录
COPY requirements.txt .

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件到工作目录
COPY . .

# 暴露端口（根据你的应用需求修改端口号）
EXPOSE 8000

# 设置环境变量（根据需要添加）
ENV NAME World

# 运行应用（根据你的应用入口点修改命令）
CMD ["python", "app.py"]