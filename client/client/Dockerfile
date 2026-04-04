# Python Client Dockerfile
# 复用 dotnet/runtime:8.0 基础镜像（已缓存，避免重新拉取）
FROM mcr.microsoft.com/dotnet/runtime:8.0

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY utils.py .
COPY env.py .
COPY local_input.py .
COPY converter.py .
COPY strategy_factory.py .
COPY saiblo_client.py .
COPY json_converter.py .
COPY main.py .

CMD ["python3", "-u", "main.py"]
