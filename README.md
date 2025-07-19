# THUAI-8: WarChess

This is the official repository for the THUAI-8 project, a turn-based strategy warchess game.
```python
thuai8/
│
├── demo/ # It is just a demo.
│
├── client/ # This part contains all functions that the players should
│           # complete in order to interact with the game server.
└── server/ # TThis part contains all functions that the game server
            # (logic) requires.
```
In such case it is convenient to use TCP/IP protocol to communicate between the clients (players) and the game server.
It is reconmmended to refer to the demo when finishing the client-server part, and you can also use ApiFox for testing the APIs.

## 启动说明

**1.Python Client**  
位于`/client/client_gRPC`目录，启动指令：
`python grpc_client.py --host 192.168.1.100 --port 50052` 第一个参数为server地址，第二个参数为端口

**2. Cpp Client**
*未完成*

**3. Server**
C#版本：net8.0, 位于server目录下，启动指令：
`dotnet run --urls localhost:50051` 参数为监听地址和端口