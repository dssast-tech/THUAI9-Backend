# 使用Python基础镜像（国内镜像源 - 网易云镜像）
FROM hub-mirror.c.163.com/library/python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install -r requirements.txt

# 复制所有必要文件
COPY *.py /app/
COPY *.proto /app/
COPY README*.md /app/

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 编译proto文件
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. message.proto

# 设置默认命令
ENTRYPOINT ["python", "grpc_client.py"] 