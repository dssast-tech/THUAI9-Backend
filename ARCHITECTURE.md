# Warchess 项目架构总览

> 本文件为架构分析说明文档，面向开发者，聚焦于 Server、Client（Python gRPC）与前端三者的交互关系，以及 Docker 部署方式。

---

## 一、项目整体结构

```
real-thuai8/
├── server/                      # 游戏服务端（ASP.NET Core + gRPC）
│   ├── Dockerfile               # 服务端 Docker 镜像定义
│   ├── SERVER.md
│   └── server/server/server/    # 实际源码目录
│       ├── Program.cs           # 程序入口，Kestrel HTTP/2 配置，启动游戏主循环
│       ├── env.cs               # 游戏核心控制器（Env 类）
│       ├── Piece.cs             # 棋子类（内置 Accessor 保护写权限）
│       ├── Player.cs            # 玩家类，棋子初始化与验证
│       ├── board.cs             # 棋盘类，A* 寻路，格子状态管理
│       ├── utils.cs             # 辅助数据结构（Point/ActionSet/SpellContext 等）
│       ├── ServerCommunicator.cs# gRPC 服务实现（GameServiceImpl）+ 同步辅助类
│       ├── ProtoConverter.cs    # Proto ↔ C# 对象双向转换
│       ├── GameMessage.cs       # 消息结构定义
│       ├── LocalInput.cs        # 本地输入系统（Console/函数策略）
│       ├── LogConverter.cs      # 游戏过程序列化为 log.json（供前端使用）
│       ├── FrontClasses.cs      # 前端 JSON 数据结构定义
│       └── Protos/message.proto # gRPC 接口定义（权威协议文件）
│
├── client/
│   ├── client_gRPC/             # Python AI 客户端（主要客户端实现）
│   │   ├── grpc_client.py       # 客户端主入口，gRPC 连接与主流程
│   │   ├── env.py               # 客户端本地 Environment（含完整游戏逻辑副本）
│   │   ├── converter.py         # Proto ↔ Python 对象双向转换
│   │   ├── strategy_factory.py  # AI 策略工厂（激进/防御/MCTS）
│   │   ├── local_input.py       # 本地模式输入处理
│   │   ├── utils.py             # 辅助数据结构（与 server/utils.cs 对应）
│   │   ├── message.proto        # proto 文件（应与 server 端保持一致）
│   │   ├── message_pb2.py       # proto 自动生成代码
│   │   ├── message_pb2_grpc.py  # proto 自动生成 gRPC stub
│   │   ├── Dockerfile           # 客户端 Docker 镜像定义
│   │   └── requirements.txt     # Python 依赖
│   ├── client/                  # C# 客户端（备用/参考实现）
│   └── client_cpp/              # C++ 客户端（备用/参考实现）
│
├── demo/                        # 独立的游戏逻辑演示项目（GameDemo）
├── docker-compose.yml           # 一键编排：1 server + 2 client 容器
└── bin/                         # 输出目录（含 log.json）
```
client目录下C#格式和cpp格式的两个client都是完全不可用的，可以直接忽略。

---

## 二、核心架构：Server 与 Client 的交互

### 2.1 整体交互模型

```
┌─────────────────────────────────────────────────────────────────┐
│                        Game Server                              │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────────────┐     │
│  │  env.cs  │◄──│GameServiceImpl│◄──│ ServerCommunicator  │     │
│  │  (Env)   │   │  (gRPC 服务)  │   │ (BroadcastGameState │     │
│  └──────────┘   └──────────────┘   │  SendInit           │     │
│       │                            │  SendInitPolicy      │     │
│  ┌────▼─────┐                      │  SendAction)         │     │
│  │LogConverter│ ─────────────────► │                     │     │
│  │ log.json  │                     └─────────────────────┘     │
│  └──────────┘                              ▲  │                 │
└──────────────────────────────────────────── │  │ ───────────────┘
                                       gRPC   │  │  stream/unary
                        ┌──────────────────── │  │ ──────────────┐
                        │  Python Client       │  ▼              │
                        │  ┌────────────────────────────────┐    │
                        │  │       grpc_client.py           │    │
                        │  │  SendInit() → 获取 player_id   │    │
                        │  │  SendInitPolicy() → 发送配置   │    │
                        │  │  BroadcastGameState() → 订阅   │    │
                        │  │  SendAction() → 发送行动        │    │
                        │  └────────────────────────────────┘    │
                        │            ▲  │                        │
                        │  ┌─────────┘  ▼                       │
                        │  │  strategy_factory.py（AI 策略）     │
                        │  │  converter.py（Proto ↔ Python）     │
                        │  │  env.py（本地状态镜像）              │
                        └────────────────────────────────────────┘
```

### 2.2 gRPC 与 Protobuf 简介

#### 核心思路：像调用本地函数一样调用远程函数

gRPC 要解决的问题是：**A 程序（客户端）如何调用运行在另一台机器上的 B 程序（服务端）里的函数？**

朴素的做法是自己拼 HTTP 请求、手写 JSON、再手动解析响应——繁琐且容易出错。gRPC 的思路是：**先用一份"合同"文件（`.proto`）把双方约定好，然后自动生成调用代码**，开发者只需要像调用本地函数一样写代码即可。

#### 第一步：写 .proto 文件——定义"合同"

`.proto` 文件描述两件事：**数据长什么样**（`message`）、**能调用哪些函数**（`service`）。

```protobuf
// 定义一种数据结构
message _InitRequest {
    string message = 1;   // 字段编号用于二进制编码，不是默认值
}

message _InitResponse {
    int32 id = 2;         // 服务端分配的玩家ID
}

// 定义服务：里面列出所有可远程调用的函数
service GameService {
    rpc SendInit (_InitRequest) returns (_InitResponse);
}
```

#### 第二步：用 protoc 编译——自动生成代码

写完 `.proto` 后，用编译器（`protoc`）生成各语言的代码：

```
message.proto  ──protoc──►  C# 代码（服务端自动生成）
               ──protoc──►  Python 代码（message_pb2.py + message_pb2_grpc.py）
```

生成的代码里已经包含了所有数据类的定义和网络通信逻辑，开发者不需要关心底层细节。

#### 第三步：服务端实现函数体

服务端继承生成的基类，填写函数的具体逻辑：

```csharp
// C# 服务端：继承自动生成的基类，实现函数体
class GameServiceImpl : GameService.GameServiceBase
{
    public override Task<_InitResponse> SendInit(_InitRequest request, ...)
    {
        // 这里写真正的业务逻辑
        return Task.FromResult(new _InitResponse { Id = 1 });
    }
}
```

#### 第四步：客户端直接"调用"

客户端用生成的 Stub（存根）发起调用，写法和调用本地函数几乎一样：

```python
# Python 客户端：通过 stub 调用，感觉像在调用本地函数
stub = GameServiceStub(channel)
response = stub.SendInit(_InitRequest(message="hello"))
print(response.id)  # 拿到服务端返回的玩家ID
```

底层实际发生的事情是：stub 把参数序列化成二进制，通过网络发给服务端，服务端执行函数后把返回值序列化回来，stub 再反序列化给调用方——这一切对开发者透明。

#### 特殊情况：服务端推流（Server Streaming）

普通 RPC 是"一问一答"。本项目的 `BroadcastGameState` 是**服务端推流**模式：客户端发一次请求，服务端可以持续往回推送多条消息，直到连接关闭。

```protobuf
// proto 中用 stream 关键字标记推流
rpc BroadcastGameState (_GameStateRequest) returns (stream _GameStateResponse);
```

```python
# 客户端用 for 循环持续接收，服务端每次广播都会触发一次循环体
for state in stub.BroadcastGameState(request):
    print(f"收到第 {state.currentRound} 回合状态")
    if state.isGameOver:
        break
```

#### 本项目的完整流程

```
① 双方都持有同一份 message.proto
         │
         ▼
② protoc 编译 → 生成 C# 代码（服务端）和 Python 代码（客户端）
         │
         ▼
③ 服务端启动，监听 50051 端口
         │
         ▼
④ 客户端创建 channel（网络连接）和 stub（调用代理）
         │
         ▼
⑤ 客户端通过 stub 调用 RPC，数据自动序列化/反序列化传输
```

> **重要**：两份 `message.proto` 副本（服务端 `Protos/message.proto` 与客户端 `client_gRPC/message.proto`）**必须完全一致**。如果一方修改了字段编号或类型，另一方解析时会得到错误数据，且不会有明显报错。

### 2.4 gRPC 接口

协议定义于 `Protos/message.proto`（服务端权威版本）与 `client/client_gRPC/message.proto`（客户端副本）。

| RPC 方法 | 方向 | 类型 | 说明 |
|---|---|---|---|
| `SendInit` | Client → Server | Unary | 客户端注册，获取 player_id 和地图信息 |
| `SendInitPolicy` | Client → Server | Unary | 发送棋子初始化配置（属性/装备/位置） |
| `BroadcastGameState` | Server → Client | Server Stream | 每棋子行动前推送完整游戏状态 |
| `SendAction` | Client → Server | Unary | 轮到己方时发送行动指令 |

### 2.5 标准 gRPC 对接流程

```
Client                          Server
  │                               │
  │── BroadcastGameState(id) ────►│  (建立长连接，等待推送)
  │                               │
  │── SendInit("") ──────────────►│  获得 player_id + 地图
  │◄─ _InitResponse ──────────────│
  │                               │
  │── SendInitPolicy(id, args) ──►│  服务端初始化棋子
  │◄─ _InitPolicyResponse ────────│
  │                               │
  │       游戏开始，服务端推送     │
  │◄═══ _GameStateResponse ═══════│  (stream)
  │                               │
  │  if currentPlayerId == my_id: │
  │── SendAction(actionSet) ─────►│
  │◄─ _actionResponse ────────────│
  │                               │
  │       ... 循环 ...            │
  │◄═══ isGameOver=true ══════════│
  │  关闭连接                     │
```

> **注意**：客户端实际代码中，`BroadcastGameState` 的订阅（`start_subscription`）在 `SendInit` 和 `SendInitPolicy` **之后**才启动线程，与服务端 README 描述的"应在连接后立即调用"顺序存在差异。

---

## 三、Server 内部架构

### 3.1 Env（游戏核心控制器）

`env.cs` 中的 `Env` 类是游戏主逻辑中枢，负责：
- 维护 `action_queue`（行动队列）、`current_piece`、`round_number`、`delayed_spells`
- 管理输入方式（本地控制台 / 函数策略注入 / 远程 gRPC）
- 执行每轮行动（移动、攻击、法术）
- 触发状态广播（调用 `GameServiceImpl.BroadcastToAllClients()`）
- 游戏结束后调用 `LogConverter` 生成 `log.json`

运行模式（`mode` 字段）：
- `mode = 0`：本地模式（控制台输入或函数策略注入）
- `mode = 1`：远程 gRPC 模式

### 3.2 同步机制

`ServerCommunicator.cs` 中包含两个同步辅助类：

**`InitWaiter`**：等待所有客户端完成初始化

```
connectWaiter（等2个客户端 SendInit 完成）
initWaiter   （等2个客户端 SendInitPolicy 完成）
```

**`ActionWaiter`**：每轮等待当前玩家发送 `SendAction`

```
WaitForPlayerActionAsync(playerId, timeout)
→ 超时抛出 ApplicationException
→ 客户端发送 SendAction 时通过 TrySetResult 解锁
```

### 3.3 GameServiceImpl 单例问题

`GameServiceImpl` 同时被注册为 DI 单例并使用 `static Instance` 字段存储。构造函数中的 `instanceCount` 计数和 `VerifyInstance()` 调用是调试遗留代码，生产环境不必要。

---

## 四、Client 内部架构（Python gRPC 客户端）

### 4.1 三种运行模式

| 模式 | 参数 | 说明 |
|---|---|---|
| `remote` | `--mode remote` | 连接真实服务端，AI 策略驱动 |
| `local` | `--mode local` | 完全本地运行，使用 env.py 内置游戏循环 |
| `function` | `--mode function` | 本地模式，玩家1=AI，玩家2=控制台 |

### 4.2 核心模块关系

```
grpc_client.py
    │
    ├── strategy_factory.py  ← 生成 init_strategy / action_strategy 函数
    ├── converter.py         ← Proto ↔ Python 对象转换（Converter 类）
    ├── env.py               ← 本地状态镜像（Environment / Piece / Board 等）
    └── utils.py             ← 基础数据结构（Point / SpellContext / Spell 等）
```

**`env.py`** 的特殊性：客户端维护了一份**完整的游戏逻辑副本**（包括攻击计算、法术判断、A*寻路等），主要用于：
1. local 模式下独立运行整局游戏
2. remote 模式下为 MCTS 策略提供模拟环境（rollout）

### 4.3 线程模型

```
主线程
  │── SendInit()
  │── SendInitPolicy()
  │── 启动 subscription_thread（daemon）
  │       └── asyncio event loop
  │               └── subscribe_game_state()（同步 for 循环）
  │                       └── send_action()（await asyncio.sleep(0.1) + stub.SendAction）
  └── join subscription_thread
```

> **注意**：`subscribe_game_state` 函数虽然声明为 `async def`，内部使用的 `stub.BroadcastGameState` 是**同步迭代器**（非 async），通过 `asyncio.new_event_loop()` 运行在独立线程中，混用了同步和异步代码。

---

## 五、Server 与前端的交互

### 5.1 前端不参与实时通信

前端（渲染/回放系统）**不直接与服务端进行实时 gRPC 通信**，而是通过读取游戏结束后生成的 **`log.json`** 文件进行离线回放渲染。

```
Server ──游戏结束──► LogConverter ──► log.json ──► 前端回放渲染
```

### 5.2 log.json 结构

游戏结束后，`LogConverter.cs` 将游戏数据序列化为以下结构：

```json
{
  "mapdata": {
    "mapWidth": 20,
    "rows": [{ "row": [1, 2, ...] }, ...]
  },
  "playerData": { "player1": "Red", "player2": "Blue" },
  "soldiersData": [
    {
      "ID": 0,
      "soldierType": "Warrior",
      "camp": "Red",
      "position": { "x": 3, "y": 1, "z": 5 },
      "stats": { "health": 60, "strength": 15, "intelligence": 5 }
    }
  ],
  "gameRounds": [
    {
      "roundNumber": 1,
      "actions": [ ... ],
      "stats": [ ... ],
      "score": { "redScore": 0, "blueScore": 0 },
      "end": "false"
    }
  ]
}
```

动作类型（`actionType`）：`Movement` / `Attack` / `Ability` / `Death`

---

## 六、Docker 部署架构

### 6.1 docker-compose.yml 编排

```yaml
services:
  server:           # ASP.NET Core gRPC 服务端
    build: ./server/Dockerfile
    ports: ["50051:50051"]
    command: ["--urls", "http://0.0.0.0:50051"]
    networks: [game-network]

  client1:          # Python AI 客户端（MCTS 策略）
    build: ./client/client_gRPC/Dockerfile
    depends_on: [server]
    command: ["--host", "server", "--port", "50051", "--mode", "remote", "--strategy", "mcts"]
    networks: [game-network]

  client2:          # Python AI 客户端（激进策略）
    build: ./client/client_gRPC/Dockerfile
    depends_on: [server]
    command: ["--host", "server", "--port", "50051", "--mode", "remote", "--strategy", "aggressive"]
    networks: [game-network]

networks:
  game-network: { driver: bridge }
```

### 6.2 Server Dockerfile（多阶段构建）

```dockerfile
# 阶段1：构建
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
WORKDIR /src/server/server/server
RUN dotnet restore server.csproj
RUN dotnet publish server.csproj -c Release -o /app

# 阶段2：运行时
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app .
EXPOSE 50051
ENTRYPOINT ["dotnet", "server.dll"]
```

> **注意**：Server Dockerfile 的 build context 为项目根目录（`context: .`），会将整个仓库复制进构建上下文，包括 client 目录，导致镜像构建缓慢。

### 6.3 Client Dockerfile

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY *.py /app/
COPY *.proto /app/
# 在容器内编译 proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. message.proto
ENTRYPOINT ["python", "grpc_client.py"]
```

> **注意**：容器启动时会覆盖已预先生成好的 `message_pb2.py` 和 `message_pb2_grpc.py`（通过 `COPY *.py` 拷入，再通过 `RUN grpc_tools.protoc` 重新生成）。两份文件并存，存在版本覆盖不一致的风险。

### 6.4 启动时序

```
docker-compose up
    │
    ├── server 容器启动
    │     └── 等待客户端连接（connectWaiter, 超时 10s）
    │
    ├── client1 容器启动（depends_on server）
    │     └── SendInit → SendInitPolicy → BroadcastGameState
    │
    └── client2 容器启动（depends_on server）
          └── SendInit → SendInitPolicy → BroadcastGameState
```

> **注意**：
> 1.  docker部署仅在本地进行过测试，不保证可用，也不保证与saiblo平台兼容
> 2. `depends_on` 仅保证 server 容器**启动**，不保证 gRPC 服务**就绪**。client 可能在 server 完成监听之前发起连接，导致连接失败。

---

## 七、关键数据流汇总

```
[Client 初始化]
  SendInit ──────────────────────────► ServerCommunicator.SendInit()
                                            ├── Interlocked.Increment(Idcnt)
                                            ├── connectWaiter.ClientReady()
                                            └── 返回 player_id + Board

[棋子配置]
  SendInitPolicy(pieceArgs) ─────────► ServerCommunicator.SendInitPolicy()
                                            ├── player.localInit(initMessage, board)
                                            │    ├── ValidateAttributes()
                                            │    ├── ValidateEquipment()
                                            │    └── ValidatePosition()
                                            └── initWaiter.ClientReady()

[游戏主循环]
  env.run()（后台线程）
    └── 每个棋子行动前：
         ├── BroadcastGameState() ──► GameServiceImpl.BroadcastToAllClients()
         │                                └── _clients[id].WriteAsync(state)
         │                                      └── ──► Client.subscribe_game_state()
         │                                                  └── if my_turn: send_action()
         └── ActionWaiter.WaitForPlayerActionAsync()
               └── SendAction() ──────────────────────────► 解锁 TCS

[游戏结束]
  LogConverter.SaveLog("log.json") ──► 前端读取回放
```

---


