using System;

public class Visualizers
{
    // 显示棋盘状态
    public void ConsoleVisualize(Game game)
    {
        Console.WriteLine("---------------------------------------------------------------");
        int[,,] grid = game.board.Grid;
        for (int i = 0; i < grid.GetLength(0); i++)
        {
            for (int j = 0; j < grid.GetLength(1); j++)
            {
                if (grid[i, j, 0] != -1)
                {
                    Console.Write($"{grid[i, j, 0]}-{grid[i, j, 1]} ");  // 显示棋子所在位置
                }
                else
                {
                    Console.Write("--- ");  // 空位置
                }
            }
            Console.WriteLine();
        }

        // 显示每个棋子的健康值
        for (int player = 0; player <= 1; player++)
        {
            for (int i = 0; i < game.pieces[player].Count; i++)
            {
                Piece piece = game.pieces[player][i];

                // 仅显示存活的棋子的健康值
                if (!piece.isDead())
                {
                    Console.WriteLine($"Piece {player}-{piece.id} Health: {piece.Health}");
                }
            }
        }
        Console.WriteLine();
        Console.WriteLine($"Current Turn: {game.currentTurn}");
        if (game.isGameOver)
        {
            Console.WriteLine($"Game Over! Winner: {game.winner}");
        }

        Console.WriteLine("---------------------------------------------------------------");
    }
}
