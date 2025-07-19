# 使用.NET SDK作为基础镜像
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# 复制项目文件
COPY . .

# 构建项目
WORKDIR /src/server/server/server
RUN dotnet restore server.csproj
RUN dotnet publish server.csproj -c Release -o /app

# 构建运行时镜像
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app .

# 暴露gRPC端口
EXPOSE 50051

ENTRYPOINT ["dotnet", "server.dll"] 