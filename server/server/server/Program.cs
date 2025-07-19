using Server;
using System.Net.NetworkInformation;
using Grpc.Core;
using Microsoft.AspNetCore.Builder;
using System.Threading.Tasks;

class Program
{
    static async Task Main(string[] args)
    {
        // 解析命令行参数
        string url = "http://localhost:50051"; // 默认URL
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--urls" && i + 1 < args.Length)
            {
                url = args[i + 1];
            }
        }

        var builder = WebApplication.CreateBuilder(args);

        // 添加 gRPC 服务
        builder.Services.AddSingleton<Env>();  // Env 单例，确保整个应用使用同一个实例
        builder.Services.AddSingleton<GameServiceImpl>();  // 将GameServiceImpl注册为单例
        builder.Services.AddGrpc();

        builder.WebHost.ConfigureKestrel(options =>
        {
            var uri = new Uri(url);
            if (uri.Host == "0.0.0.0")
            {
                options.ListenAnyIP(uri.Port, o =>
                {
                    o.Protocols = Microsoft.AspNetCore.Server.Kestrel.Core.HttpProtocols.Http2;
                });
            }
            else
            {
                options.ListenLocalhost(uri.Port, o =>
                {
                    o.Protocols = Microsoft.AspNetCore.Server.Kestrel.Core.HttpProtocols.Http2;
                });
            }
        });

        var app = builder.Build();

        // 配置 gRPC 服务端点
        app.MapGrpcService<GameServiceImpl>();
        app.MapGet("/", () => $"gRPC 服务器已启动。请使用 gRPC 客户端进行通信。");

        // 显示 gRPC 服务监听地址
        Console.WriteLine($"gRPC 服务正在监听地址：{url}");

        // 显式指定 gRPC 服务监听的地址
        app.Urls.Add(url);

        var serverTask = app.RunAsync();
        var game = app.Services.GetRequiredService<Env>();
        
        // 输入方式现在在Env.initialize()中设置
        
        Task.Run(() => game.run());  // 在后台线程运行 game.run()

        await serverTask;
    }
}