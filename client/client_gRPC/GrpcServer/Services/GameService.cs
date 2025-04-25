using Grpc.Core;
using Game; // 自动生成的命名空间，基于 message.proto 文件

namespace GrpcServer.Services
{
    public class GameServiceImpl : GameService.GameServiceBase // 修改类名为 GameServiceImpl
    {
        public override Task<InitializationResponse> Initialize(InitializationRequest request, ServerCallContext context)
        {
            Console.WriteLine("收到初始化请求");
            return Task.FromResult(new InitializationResponse
            {
                Success = true,
                Message = "Game initialized"
            });
        }

        public override Task<ActionResponse> SendAction(ActionRequest request, ServerCallContext context)
        {
            Console.WriteLine($"收到客户端动作: {request}");
            return Task.FromResult(new ActionResponse
            {
                Success = true,
                Message = "Action received"
            });
        }

        public override Task<GameStateResponse> GetGameState(GameStateRequest request, ServerCallContext context)
        {
            var gameState = new GameStateResponse
            {
                GameState = new GameState
                {
                    CurrentRound = 1,
                    CurrentPlayerId = 0
                },
                Piece = new Piece
                {
                    Health = 100,
                    MaxHealth = 100,
                    Id = 1
                },
                Board = new Board
                {
                    Width = 10,
                    Height = 10
                },
                Env = new Env
                {
                    RoundNumber = 1,
                    IsGameOver = false
                }
            };

            Console.WriteLine("返回当前游戏状态");
            return Task.FromResult(gameState);
        }
    }
}