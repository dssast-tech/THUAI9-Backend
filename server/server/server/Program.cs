using Server;
using System.Net.NetworkInformation;
using Grpc.Core;
using Microsoft.AspNetCore.Builder;
using System.Threading.Tasks;

class Program
{
    static async Task Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        // 添加 gRPC 服务
        builder.Services.AddSingleton<Env>();  // Env 单例，确保整个应用使用同一个实例
        builder.Services.AddGrpc();

        builder.WebHost.ConfigureKestrel(options =>
        {
            options.ListenLocalhost(50051, o =>
            {
                o.Protocols = Microsoft.AspNetCore.Server.Kestrel.Core.HttpProtocols.Http2;
            });
        });

        var app = builder.Build();

        // 配置 gRPC 服务端点
        app.MapGrpcService<GameServiceImpl>();
        app.MapGet("/", () => "gRPC 服务器已启动。请使用 gRPC 客户端进行通信。");

        // 显示 gRPC 服务监听地址
        Console.WriteLine("gRPC 服务正在监听地址：localhost:50051");

        // 显式指定 gRPC 服务监听的端口
        app.Urls.Add("http://localhost:50051");

        var serverTask = app.RunAsync();
        var game = app.Services.GetRequiredService<Env>();
        
        // 输入方式现在在Env.initialize()中设置
        
        Task.Run(() => game.run());  // 在后台线程运行 game.run()

        await serverTask;
    }
    
    
}