# C#版本Server及Python版本Client启动说明

## 运行Server

进入GrpcServer文件夹，运行以下命令以安装必要的 gRPC 包（如果未自动安装）：

```bash
dotnet add package Grpc.AspNetCore
```

运行以下命令启动服务端：

```bash
dotnet run
```

服务端将监听 `localhost:50051`，并输出以下信息：

```bash
gRPC 服务正在监听地址：localhost:50051
```

## 运行Client

确保已安装 `grpcio` 和 `grpcio-tools`：

```bash
pip install grpcio grpcio-tools
```

在另一个终端中进入client_gRPC文件夹，运行以下命令启动 Python 客户端：

```bash
python grpc_client.py
```

## 预期结果

预期client显示结果

```bash
$ python grpc_client.py
初始化响应: Game initialized
当前游戏状态: game_state {
  current_round: 1
}
piece {
  health: 100
  max_health: 100
  id: 1
}
board {
  width: 10
  height: 10
}
env {
  round_number: 1
}

动作响应: Action received
```

预期Server显示结果

```bash
$ dotnet run
正在生成...
gRPC 服务正在监听地址：localhost:50051
info: Microsoft.Hosting.Lifetime[14]
      Now listening on: http://localhost:50051
info: Microsoft.Hosting.Lifetime[0]
      Application started. Press Ctrl+C to shut down.
info: Microsoft.Hosting.Lifetime[0]
      Hosting environment: Development
info: Microsoft.Hosting.Lifetime[0]
      Content root path: /Users/liyanjia/Desktop/科协/real-thuai8/client/client_gRPC/GrpcServer
收到初始化请求
返回当前游戏状态
收到客户端动作: { "actionSet": { "moveTarget": { "x": 3, "y": 5 } } }
```

