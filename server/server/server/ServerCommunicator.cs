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

        public async Task<GameMessage?> SendRequestAsync(string clientUrl, GameMessage message, int timeoutMs = 5000)
        {
            var json = JsonSerializer.Serialize(message);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            using var cts = new CancellationTokenSource(timeoutMs);
            try
            {
                var response = await client.PostAsync(clientUrl, content, cts.Token);
                response.EnsureSuccessStatusCode();
                var responseJson = await response.Content.ReadAsStringAsync();
                return JsonSerializer.Deserialize<GameMessage>(responseJson);
            }
            catch (TaskCanceledException)
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
