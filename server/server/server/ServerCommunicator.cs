using Grpc.Core;
using Microsoft.AspNetCore.Identity.Data;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Channels;
using System.Threading.Tasks;
//using Server;


namespace Server
{
    class GameServiceImpl : GameService.GameServiceBase
    {
        private static int instanceCount = 0;  // 添加静态计数器
        private readonly string instanceId = Guid.NewGuid().ToString();  // 添加唯一标识符
        Env env;
        public static GameServiceImpl Instance { get; private set; }

        public GameServiceImpl(Env env)
        {
            instanceCount++;  // 构造函数调用时增加计数
            Console.WriteLine($"GameServiceImpl constructor called. Total instances created: {instanceCount}");
            Console.WriteLine($"New instance created with ID: {instanceId}");
            
            this.env = env;
            Instance = this;
        }

        // 添加验证方法
        public void VerifyInstance()
        {
            if (Instance == null)
            {
                Console.WriteLine("Warning: Instance is null!");
                return;
            }

            Console.WriteLine($"Current instance ID: {instanceId}");
            Console.WriteLine($"Static Instance ID: {Instance.instanceId}");
            Console.WriteLine($"Are they the same instance? {ReferenceEquals(this, Instance)}");
            Console.WriteLine($"Total instances created: {instanceCount}");
        }

        private readonly ConcurrentDictionary<int, IServerStreamWriter<_GameStateResponse>> _clients =
        new ConcurrentDictionary<int, IServerStreamWriter<_GameStateResponse>>();

        // 客户端调用这个方法订阅
        public override async Task BroadcastGameState(_GameStateRequest request, IServerStreamWriter<_GameStateResponse> responseStream, ServerCallContext context)
        {
            VerifyInstance();  // 验证实例
            var clientId = request.PlayerID;
            Console.WriteLine($"Client {clientId} connected.");

            // 加入连接池
            bool addSuccess = _clients.TryAdd(clientId, responseStream);
            Console.WriteLine($"Client {clientId} connection attempt - Success: {addSuccess}");
            Console.WriteLine($"Current client count: {_clients.Count}");

            try
            {
                // 保持连接直到客户端断开
                await Task.Delay(Timeout.Infinite, context.CancellationToken);
            }
            catch (TaskCanceledException)
            {
                // 客户端断开
                Console.WriteLine($"Client {clientId} disconnected by accident.");
            }
            // finally
            // {
            //     // 移除连接
            //     _clients.TryRemove(clientId, out _);
            //     Console.WriteLine($"Client {clientId} disconnected by will.");
            // }
        }

        // 这个方法在主逻辑中调用，用于广播数据
        public async Task BroadcastToAllClients()
        {
            var gameStateResponse = new _GameStateResponse
            {
                CurrentRound = env.round_number,
                CurrentPlayerId = env.current_piece.team,
                ActionQueue = { env.action_queue.Select(Converter.ToProto) },
                CurrentPieceID = env.current_piece.id,
                DelayedSpells = { env.delayed_spells.Select(Converter.ToProto) },
                Board = Converter.ToProto(env.board),
                IsGameOver = env.isGameOver
            };

            Console.WriteLine($"Broadcasting game state to {_clients.Count} clients");
            foreach (var client in _clients)
            {
                try
                {
                    await client.Value.WriteAsync(gameStateResponse);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Failed to send to client {client.Key}: {ex.Message}");
                    // 可以考虑移除失效的连接
                }
            }
        }

        /// <summary>
        /// 断开所有客户端连接
        /// </summary>
        public async Task DisconnectAllClients()
        {
            Console.WriteLine($"开始断开 {_clients.Count} 个客户端连接...");
            
            // 发送最终的游戏状态（包含isGameOver=true）
            var finalGameState = new _GameStateResponse
            {
                CurrentRound = env.round_number,
                CurrentPlayerId = env.current_piece?.team ?? 0,
                ActionQueue = { env.action_queue.Select(Converter.ToProto) },
                CurrentPieceID = env.current_piece?.id ?? -1,
                DelayedSpells = { env.delayed_spells.Select(Converter.ToProto) },
                Board = Converter.ToProto(env.board),
                IsGameOver = true  // 确保客户端知道游戏已结束
            };

            // 向所有客户端发送最终状态
            foreach (var client in _clients.ToList())
            {
                try
                {
                    await client.Value.WriteAsync(finalGameState);
                    Console.WriteLine($"已向客户端 {client.Key} 发送最终游戏状态");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"向客户端 {client.Key} 发送最终状态失败: {ex.Message}");
                }
            }

            // 等待一段时间确保消息发送完成
            await Task.Delay(1000);

            // 清空所有客户端连接
            var disconnectedClients = new List<int>();
            foreach (var client in _clients.ToList())
            {
                try
                {
                    // 移除客户端连接
                    if (_clients.TryRemove(client.Key, out _))
                    {
                        disconnectedClients.Add(client.Key);
                        Console.WriteLine($"客户端 {client.Key} 连接已断开");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"断开客户端 {client.Key} 时出错: {ex.Message}");
                }
            }

            Console.WriteLine($"已断开 {disconnectedClients.Count} 个客户端连接");
            Console.WriteLine($"剩余连接数: {_clients.Count}");
        }

        // 1. SendInit 实现
        public override Task<_InitResponse> SendInit(_InitRequest request, ServerCallContext context)
        {
            VerifyInstance();  // 验证实例
            Console.WriteLine("Received InitRequest");
            int assignedId = Interlocked.Increment(ref env.Idcnt);
            Console.WriteLine($"Handling player{assignedId}");

            env.connectWaiter.RegisterClient(assignedId.ToString());
            env.connectWaiter.ClientReady(assignedId.ToString());
            // 模拟初始化棋盘的回信
            var response = new _InitResponse
            {
                PieceCnt = Player.PIECECNT,
                Id = assignedId,
                Board = Converter.ToProto(env.board)
            };

            return Task.FromResult(response);
        }

        // 2. SendInitPolicy 实现
        public override Task<_InitPolicyResponse> SendInitPolicy(_InitPolicyRequest request, ServerCallContext context)
        {
            VerifyInstance();  // 验证实例

            int player = request.PlayerId;
            var _pieceArgs = request.PieceArgs.ToList();
            var initPolicyMessage = new InitPolicyMessage();
            initPolicyMessage.pieceArgs = new List<pieceArg>();
            foreach (var pieceArg in _pieceArgs)
            {
                initPolicyMessage.pieceArgs.Add(Converter.FromProto(pieceArg));
            }

            if (player == 1) env.player1.localInit(initPolicyMessage, env.board);
            else env.player2.localInit(initPolicyMessage, env.board);


            // 模拟初始化策略的回信
            var response = new _InitPolicyResponse
            {
                Success = true,
                Mes = "Policy confirmed"
            };

            env.initWaiter.RegisterClient(player.ToString());
            env.initWaiter.ClientReady(player.ToString());
            
            return Task.FromResult(response);
        }

        // 3. SendAction 实现
        public override Task<_actionResponse> SendAction(_actionSet request, ServerCallContext context)
        {
            Console.WriteLine("Received ActionSet: ");

            bool accepted = false;
            if (env.actionWaiter._playerActions.TryGetValue(request.PlayerId, out var tcs))
            {
                accepted = tcs.TrySetResult(request);  // 解锁等待
            }

            var actionResponse = new _actionResponse
            {
                Success = accepted,
                Mes = accepted ? "Policy confirmed" : "No action expected at this time"
            };


            return Task.FromResult(actionResponse);
        }

    }

    public class InitWaiter
    {
        private readonly int _expectedClients;
        private readonly Dictionary<string, bool> _clientReadyStatus = new Dictionary<string, bool>();
        private readonly Dictionary<string, Task> _clientTimeoutTasks = new Dictionary<string, Task>();
        private readonly TaskCompletionSource<bool> _tcs = new TaskCompletionSource<bool>();
        private readonly TimeSpan _timeout;
        private int loadedClients = 0;

        private int flag = 0;

        public InitWaiter(int expectedClients, TimeSpan timeout, int Flag)
        {
            _expectedClients = expectedClients;
            _timeout = timeout;
            flag = Flag;
        }

        // 注册一个client
        public void RegisterClient(string clientId)
        {
            lock (_clientReadyStatus)  // 保证线程安全
            {
                if (!_clientReadyStatus.ContainsKey(clientId))
                {
                    _clientReadyStatus.Add(clientId, false);
                    _clientTimeoutTasks[clientId] = StartTimeoutTask(clientId);  // 启动超时任务
                    Console.WriteLine($"[InitWaiter: {flag}] Registered client: {clientId} (Total clients: {_clientReadyStatus.Count}/{_expectedClients})");
                    Interlocked.Increment(ref loadedClients);
                }
            }
        }

        // 启动超时任务
        private async Task StartTimeoutTask(string clientId)
        {
            await Task.Delay(_timeout);

            // 如果超时并且client还没有准备好，输出超时信息
            lock (_clientReadyStatus)
            {
                if (_clientReadyStatus.ContainsKey(clientId) && !_clientReadyStatus[clientId])
                {
                    Console.WriteLine($"[InitWaiter] Client {clientId} timed out after {_timeout.TotalSeconds} seconds.");
                }
            }
        }

        private void CheckAndSetCompletion()
        {
            // 已经在锁内，不需要再加锁
            if (loadedClients == _expectedClients &&
                !_tcs.Task.IsCompleted)
            {
                Console.WriteLine($"[InitWaiter: {flag}] All clients registered and ready, attempting to complete task.");
                _tcs.TrySetResult(true);

            }
        }

        // 标记一个client已经准备好
        public void ClientReady(string clientId)
        {
            lock (_clientReadyStatus)
            {
                if (_clientReadyStatus.ContainsKey(clientId))
                {
                    _clientReadyStatus[clientId] = true;
                    Console.WriteLine($"[InitWaiter: {flag}] Client {clientId} is ready! ({_clientReadyStatus.Values.Count(v => v)} out of {_expectedClients})");
                    CheckAndSetCompletion();
                }
            }
        }

        public async Task WaitForAllClientsAsync()
        {
            var timeoutTask = Task.Delay(_timeout);
            var completedTask = await Task.WhenAny(_tcs.Task, timeoutTask);



            Console.WriteLine($"[InitWaiter] Task completed: {(completedTask == _tcs.Task ? "Main Task" : "Timeout Task")}");
            Console.WriteLine($"[InitWaiter] TCS Task Status: {_tcs.Task.Status}");
            
            if (completedTask == timeoutTask)
            {
                Console.WriteLine("[InitWaiter] Timeout occurred while waiting for clients.");
                Console.WriteLine($"[InitWaiter] Flag: {flag}");
                throw new TimeoutException("Timed out waiting for all clients to initialize.");
            }
            
            Console.WriteLine("[InitWaiter] Successfully completed waiting for all clients.");
        }
    }

    class ActionWaiter
    {
        public ConcurrentDictionary<int, TaskCompletionSource<_actionSet>> _playerActions
             = new ConcurrentDictionary<int, TaskCompletionSource<_actionSet>>();
        public async Task<_actionSet> WaitForPlayerActionAsync(int playerId, TimeSpan timeout)
        {
            var tcs = new TaskCompletionSource<_actionSet>();
            _playerActions[playerId] = tcs;

            var completedTask = await Task.WhenAny(tcs.Task, Task.Delay(timeout));

            _playerActions.TryRemove(playerId, out _);  // 清理

            if (completedTask == tcs.Task)
            {
                var _action = tcs.Task.Result;
                return _action;
            }
            else
            {
                Console.WriteLine($"Player {playerId} action timeout.");
                throw new ApplicationException();
            }
        }
    }

}

    /*******************旧版********************************/

//     class ServerCommunicator
//     {
//         private static readonly HttpClient client = new HttpClient();
//         private string address1;
//         private string address2;

//         public ServerCommunicator(string address1, string address2)
//         {
//             this.address1 = address1;
//             this.address2 = address2;
//         }

//         public InitPolicyMessage? SendInitRequest(int target, MessageWrapper<InitGameMessage> message, int timeoutMs = 5000)
//         {
//             string clientUrl = target == 1 ? address1 : address2;
//             var json = JsonSerializer.Serialize(message);
//             var content = new StringContent(json, Encoding.UTF8, "application/json");

//             // 获取当前目录
//             string currentDirectory = Directory.GetCurrentDirectory();

//             // 定义文件路径
//             string filePath = Path.Combine(currentDirectory, "initlog.json");

//             // 将JSON写入文件
//             File.WriteAllText(filePath, json);
//             using var cts = new CancellationTokenSource(timeoutMs);
//             try
//             {
//                 // 同步等待 PostAsync 的结果
//                 var response = client.PostAsync(clientUrl, content, cts.Token).Result;
//                 response.EnsureSuccessStatusCode();

//                 // 同步读取响应内容
//                 var responseJson = response.Content.ReadAsStringAsync().Result;
//                 return JsonSerializer.Deserialize<InitPolicyMessage>(responseJson);
//             }
//             catch (AggregateException ex) when (ex.InnerException is TaskCanceledException)
//             {
//                 Console.WriteLine("请求超时");
//                 return null;
//             }
//             catch (Exception ex)
//             {
//                 Console.WriteLine("通信异常: " + ex.Message);
//                 return null;
//             }
//         }

//         public PolicyMessage? SendActionRequest(int target, MessageWrapper<GameMessage> message, int timeoutMs = 5000)
//         {
//             string clientUrl = target == 1 ? address1 : address2;
//             var json = JsonSerializer.Serialize(message);
//             var content = new StringContent(json, Encoding.UTF8, "application/json");

//             using var cts = new CancellationTokenSource(timeoutMs);
//             try
//             {
//                 // 同步等待 PostAsync 的结果
//                 var response = client.PostAsync(clientUrl, content, cts.Token).Result;
//                 response.EnsureSuccessStatusCode();

//                 // 同步读取响应内容
//                 var responseJson = response.Content.ReadAsStringAsync().Result;
//                 return JsonSerializer.Deserialize<PolicyMessage>(responseJson);
//             }
//             catch (AggregateException ex) when (ex.InnerException is TaskCanceledException)
//             {
//                 Console.WriteLine("请求超时");
//                 return null;
//             }
//             catch (Exception ex)
//             {
//                 Console.WriteLine("通信异常: " + ex.Message);
//                 return null;
//             }
//         }
//     }
// }
