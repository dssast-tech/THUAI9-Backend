FROM mcr.microsoft.com/dotnet/runtime:8.0

RUN apt-get update && apt-get install -y \
    g++ \
    cmake \
    nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN mkdir -p build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc)

CMD ["./build/thuai9_client"]
