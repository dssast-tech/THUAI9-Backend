using GrpcServer.Services;

var builder = WebApplication.CreateBuilder(args);

// 添加 gRPC 服务
builder.Services.AddGrpc();

var app = builder.Build();

// 配置 gRPC 服务端点
app.MapGrpcService<GameServiceImpl>();
app.MapGet("/", () => "gRPC 服务器已启动。请使用 gRPC 客户端进行通信。");

// 显示 gRPC 服务监听地址
Console.WriteLine("gRPC 服务正在监听地址：localhost:50051");

// 显式指定 gRPC 服务监听的端口
app.Urls.Add("http://localhost:50051");

app.Run();