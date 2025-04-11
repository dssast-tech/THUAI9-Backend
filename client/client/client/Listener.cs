using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace client
{
    internal class ClientListener
    {
        private readonly HttpListener listener = new HttpListener();
        private readonly string prefix;
        private bool isRunning = false;

        public ClientListener(string urlPrefix)
        {
            prefix = urlPrefix;
            listener.Prefixes.Add(prefix);
        }

        public async Task StartAsync()
        {
            listener.Start();
            isRunning = true;
            Console.WriteLine($"客户端监听启动: {prefix}");

            while (isRunning)
            {
                var context = await listener.GetContextAsync();
                _ = Task.Run(() => HandleRequest(context)); // 非阻塞处理
            }
        }

        private async Task HandleRequest(HttpListenerContext context)
        {
            try
            {
                using var reader = new StreamReader(context.Request.InputStream, context.Request.ContentEncoding);
                string json = await reader.ReadToEndAsync();
                var message = JsonSerializer.Deserialize<GameMessage>(json);

                // 调用客户端业务逻辑
                var reply = HandleGameMessage(message);

                string responseJson = JsonSerializer.Serialize(reply);
                byte[] buffer = Encoding.UTF8.GetBytes(responseJson);
                context.Response.ContentType = "application/json";
                await context.Response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
            }
            catch (Exception ex)
            {
                Console.WriteLine("处理请求时出错: " + ex.Message);
                context.Response.StatusCode = 500;
            }
            finally
            {
                context.Response.Close();
            }
        }

        private PolicyMessage HandleGameMessage(GameMessage msg)
        {
            //调用业务逻辑函数
            throw new NotImplementedException();
        }

        public void Stop()
        {
            isRunning = false;
            listener.Stop();
            listener.Close();
        }
    }
}
