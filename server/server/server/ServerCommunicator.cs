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


        Env env;

        public GameServiceImpl(Env env)
        {
            this.env = env;
        }

        // 1. SendInit 实现
        public override Task<_InitResponse> SendInit(_InitRequest request, ServerCallContext context)
        {
            Console.WriteLine("Received InitRequest");

            // 模拟初始化棋盘的回信
            var response = new _InitResponse
            {
                PieceCnt = Player.PIECECNT,
            };

            return Task.FromResult(response);
        }

        // 2. SendInitPolicy 实现
        public override Task<_InitPolicyResponse> SendInitPolicy(_InitPolicyRequest request, ServerCallContext context)
        {
            //request to meaage
            env.initWaiter.RegisterClient(request.PlayerId.ToString());

            // 这里我们可以模拟“准备完毕”信号
            env.initWaiter.ClientReady(request.PlayerId.ToString());
            // 模拟初始化策略的回信
            var response = new _InitPolicyResponse
            {
                Success = true,
                Mes = "Policy confirmed"
            };

            return Task.FromResult(response);
        }

        // 3. SendAction 实现
        public override Task<_actionResponse> SendAction(_actionSet request, ServerCallContext context)
        {
            Console.WriteLine("Received ActionSet: ");

            // 验证动作并创建响应
            var actionResponse = new _actionResponse
            {
                Success = true,
                Mes = "Policy confirmed"
            };


            return Task.FromResult(actionResponse);
        }

        // 4. BroadcastGameState 实现
        public override async Task BroadcastGameState(_GameStateRequest request, IServerStreamWriter<_GameStateResponse> responseStream, ServerCallContext context)
        {
            Console.WriteLine("Received GameStateRequest: " );

            // 模拟每回合的游戏状态更新

            // 模拟游戏状态
            var gameStateResponse = new _GameStateResponse
            {

            };

            // 通过流发送游戏状态更新
            await responseStream.WriteAsync(gameStateResponse);

                // 暂停一段时间，模拟游戏回合的进展
            await Task.Delay(1000); // 模拟1秒的间隔
        }
    }

    public class InitWaiter
    {
        private readonly int _expectedClients;
        private readonly Dictionary<string, bool> _clientReadyStatus = new Dictionary<string, bool>();
        private readonly Dictionary<string, Task> _clientTimeoutTasks = new Dictionary<string, Task>();
        private readonly TaskCompletionSource<bool> _tcs = new TaskCompletionSource<bool>();
        private readonly TimeSpan _timeout;

        public InitWaiter(int expectedClients, TimeSpan timeout)
        {
            _expectedClients = expectedClients;
            _timeout = timeout;
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
                    Console.WriteLine($"[InitWaiter] Registered client: {clientId} (Total clients: {_clientReadyStatus.Count}/{_expectedClients})");
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
                if (!_clientReadyStatus[clientId])
                {
                    Console.WriteLine($"[InitWaiter] Client {clientId} timed out after {_timeout.TotalSeconds} seconds.");
                }
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
                    Console.WriteLine($"[InitWaiter] Client {clientId} is ready! ({_clientReadyStatus.Values.Count(v => v)} out of {_expectedClients})");
                }

                // 如果所有客户端都准备好了，解除阻塞
                if (_clientReadyStatus.Values.All(v => v))
                {
                    _tcs.SetResult(true);
                }
            }
        }
        public async Task WaitForAllClientsAsync()
        {
            var timeoutTask = Task.Delay(_timeout);
            var completedTask = await Task.WhenAny(_tcs.Task, timeoutTask);

            if (completedTask == timeoutTask)
            {
                Console.WriteLine("[InitWaiter] Timeout waiting for clients.");
                // 超时逻辑：可能是自动开始游戏，或者错误提示
                throw new TimeoutException("Timed out waiting for all clients to initialize.");
            }
        }
    }

    class ServerCommunicator
    {
        private static readonly HttpClient client = new HttpClient();
        private string address1;
        private string address2;

        public ServerCommunicator(string address1, string address2)
        {
            this.address1 = address1;
            this.address2 = address2;
        }

        public InitPolicyMessage? SendInitRequest(int target, MessageWrapper<InitGameMessage> message, int timeoutMs = 5000)
        {
            string clientUrl = target == 1 ? address1 : address2;
            var json = JsonSerializer.Serialize(message);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            // 获取当前目录
            string currentDirectory = Directory.GetCurrentDirectory();

            // 定义文件路径
            string filePath = Path.Combine(currentDirectory, "initlog.json");

            // 将JSON写入文件
            File.WriteAllText(filePath, json);
            using var cts = new CancellationTokenSource(timeoutMs);
            try
            {
                // 同步等待 PostAsync 的结果
                var response = client.PostAsync(clientUrl, content, cts.Token).Result;
                response.EnsureSuccessStatusCode();

                // 同步读取响应内容
                var responseJson = response.Content.ReadAsStringAsync().Result;
                return JsonSerializer.Deserialize<InitPolicyMessage>(responseJson);
            }
            catch (AggregateException ex) when (ex.InnerException is TaskCanceledException)
            {
                Console.WriteLine("请求超时");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine("通信异常: " + ex.Message);
                return null;
            }
        }

        public PolicyMessage? SendActionRequest(int target, MessageWrapper<GameMessage> message, int timeoutMs = 5000)
        {
            string clientUrl = target == 1 ? address1 : address2;
            var json = JsonSerializer.Serialize(message);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            using var cts = new CancellationTokenSource(timeoutMs);
            try
            {
                // 同步等待 PostAsync 的结果
                var response = client.PostAsync(clientUrl, content, cts.Token).Result;
                response.EnsureSuccessStatusCode();

                // 同步读取响应内容
                var responseJson = response.Content.ReadAsStringAsync().Result;
                return JsonSerializer.Deserialize<PolicyMessage>(responseJson);
            }
            catch (AggregateException ex) when (ex.InnerException is TaskCanceledException)
            {
                Console.WriteLine("请求超时");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine("通信异常: " + ex.Message);
                return null;
            }
        }
    }
}
