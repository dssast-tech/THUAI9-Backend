# gRPC通信模式设计

在回合制棋类游戏中，选择合适的 gRPC 通信模式 并设计合理的 游戏流程 是关键。以下是详细分析和实现方案：

---

**1. 选择 gRPC 的 RPC 模式**
回合制棋类游戏的核心需求是 顺序交替的玩家动作 和 实时状态同步，推荐使用以下两种模式组合：

**(1) Unary RPC（一元调用）**
• 适用场景：  

  • 玩家提交回合动作（如落子、移动棋子）。  

  • 查询游戏状态（如棋盘当前布局、胜负判定）。  

• 特点：  

  • 简单、符合“请求-响应”逻辑。  

  • 适合离散的、非连续的操作。  

**(2) Bidirectional Streaming RPC（双向流式）**  
• 适用场景：  

  • 实时推送对手动作和游戏状态更新（如对手落子后立即通知本方）。  

  • 长连接保持，避免频繁轮询。  

• 特点：  

  • 服务端和客户端可主动发送消息。  

  • 减少延迟，提升实时性。  


**为什么不用 Server Streaming？**  
• 单纯服务端推送无法处理客户端随时发起的动作（如悔棋请求）。  


**为什么不用 Client Streaming？**  
• 客户端单向流式不适合回合制游戏的交互需求。  


---

**2. 整体游戏流程设计**
**阶段 1：玩家匹配与房间管理（Unary RPC）**
1. 玩家登录  
   • 调用 `PlayerService.Login` 获取身份令牌（Token）。  

2. 创建/加入房间  
   • 调用 `RoomService.CreateRoom` 或 `RoomService.JoinRoom`，返回房间 ID。  

3. 等待对手  
   • 服务端管理房间状态，满员后通知双方游戏开始（通过 Bidirectional Streaming）。  


**阶段 2：游戏回合交互（Bidirectional Streaming + Unary RPC）**
1. 建立双向流式连接  
   • 客户端调用 `GameService.Play` 建立长连接，持续接收服务端推送。  

2. 玩家提交动作（Unary RPC）  
   • 当前回合玩家调用 `GameService.SubmitMove` 提交动作（如象棋的 `move from A1 to B2`）。  

3. 服务端验证并广播  
   • 服务端验证动作合法性，更新游戏状态，通过 Bidirectional Streaming 推送新状态给双方玩家。  

4. 轮换回合  
   • 服务端标记下一回合玩家，客户端界面更新当前可操作玩家。  


**阶段 3：游戏结束与结算（Unary RPC）**
1. 胜负判定  
   • 服务端检测游戏结束条件（如将军、五子连珠），调用 `GameService.EndGame` 推送结果。  

2. 数据持久化  
   • 记录对战结果到数据库（如 MongoDB 或 PostgreSQL）。  


---

**3. 关键代码示例（gRPC + Protobuf）**
**(1) 定义 Protobuf 服务（`game.proto`）**

**(2) 服务端逻辑（Python 示例）**
```python
class GameService(game_pb2_grpc.GameServiceServicer):
    def Play(self, request_iterator, context):
        # 处理双向流式连接
        for client_msg in request_iterator:
            if client_msg.HasField("move"):
                # 验证动作并更新棋盘
                valid = self._validate_move(client_msg.move)
                if valid:
                    # 广播新状态给双方玩家
                    yield game_pb2.ServerMessage(
                        board=current_board,
                        current_player=next_player
                    )

    def SubmitMove(self, request, context):
        # 一元调用：提交动作（兼容非流式客户端）
        return game_pb2.MoveResponse(is_valid=True)
```

**(3) 客户端逻辑（伪代码）**

```python
# 建立双向流式连接
stream = stub.Play()

# 线程1：接收服务端推送
def listen_for_updates():
    for server_msg in stream:
        update_ui(server_msg.board)

# 线程2：发送玩家动作
def on_player_move(from_pos, to_pos):
    stream.send(MoveRequest(from_pos=from_pos, to_pos=to_pos))
```

---

**4. 优化与注意事项**
1. 状态同步一致性  
   • 服务端是唯一权威（避免客户端作弊），所有动作需经过验证。  

2. 断线重连  
   • 客户端需缓存本地状态，断线后通过 Unary RPC 重新获取最新棋盘。  

3. 超时处理  
   • 设置回合超时（如 30 秒未落子自动判负）。  

4. 扩展性  
   • 使用 Redis 管理房间状态，支持分布式部署。  


---

**5. 总结**
• 推荐模式：  

  • Bidirectional Streaming RPC（实时状态推送） + Unary RPC（动作提交）。  

• 流程：  

  `登录 → 匹配 → 回合交替 → 结束结算`  
• 优势：  

  • 低延迟、高实时性，适合棋类游戏的强顺序性需求。  


通过合理设计 gRPC 服务，可以高效实现一个可扩展的回合制棋类游戏后端！ ♟️