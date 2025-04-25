using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace server
{
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
