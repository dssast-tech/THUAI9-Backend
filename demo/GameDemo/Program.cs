using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        List<Player> players = new List<Player>();
        players.Add(new Player(0));  // 创建玩家 0
        players.Add(new Player(1));  // 创建玩家 1
        Game game = new Game(5, 5, 3); // 创建一个 5x5 的棋盘，每位玩家 3 颗棋子
        Visualizers visualizer = new Visualizers();
        int p = 0;
        visualizer.ConsoleVisualize(game); // 显示初始棋盘
        while (!game.isGameOver)  // 游戏未结束时，持续循环
        {
            Piece next = game.nextMovePiece(); // 获取下一个要移动的棋子
            actionSet action = players[p].policy(next); // 获取玩家的操作
            game.step(action);  // 执行一步操作
            p = 1 - p;  // 切换玩家
            visualizer.ConsoleVisualize(game); // 显示当前棋盘
        }
    }
}
