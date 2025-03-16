// See https://aka.ms/new-console-template for more information
// See https://aka.ms/new-console-template for more information
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Linq;
using System.ComponentModel.DataAnnotations;
using System.IO;

class Program
{
    static void Main()
    {
        List<Player> players = new List<Player>();
        players.Add(new Player(0));
        players.Add(new Player(1));
        Game game = new Game(5, 5, 3); // 创建一个 5x5 的棋盘，每位玩家 3 颗棋子
        Visualizers visualizer = new Visualizers();
        int p = 0;
        visualizer.ConsoleVisualize(game);
        while (!game.isGameOver)
        {
            Piece next = game.nextMovePiece();
            actionSet action = players[p].policy(next);
            game.step(action);
            p = 1 - p;
            visualizer.ConsoleVisualize(game);
        }
    }
}

struct Point
{
    public int x;
    public int y;
}

//class GameState
//{
//    public Board Board { get; private set; }
//    public List<List<Piece>> pieces { get; private set; }
//    public int CurrentTurn { get; private set; }
//    public bool IsGameOver { get; private set; }
//}

struct actionSet
{
    //public int piece;
    public Point move_target;
    public int attack;
    public int skill;
}



class Game
{
    public Board board { get; private set; }
    public List<List<Piece>> pieces { get; private set; }   //pieces[0]为玩家 0 的棋子，pieces[1] 为玩家 1 的棋子
    public int currentTurn { get; private set; }
    public bool isGameOver { get; private set; }
    public int winner { get; private set; }
    public int[] piecePtr { get; private set; }

    private int maxPiecesCount;



    public Game(int width, int height, int pieceCount)
    {
        board = new Board(width, height);
        pieces = new List<List<Piece>> { new List<Piece>(), new List<Piece>() };
        winner = -1;
        currentTurn = 0;
        isGameOver = false;
        maxPiecesCount = pieceCount;
        piecePtr = new int[2];
        piecePtr[0] = 0;
        piecePtr[1] = 0;
        for (int j = 0; j <= 1; j++)
        {
            Random random = new Random();
            List<Piece> temp = new List<Piece>();
            for (int i = 0; i < pieceCount; i++)
            {
                int x = j == 0 ? 0 : board.Grid.GetLength(0) - 1;
                int y = i;
                temp.Add(new Piece(x, y, j, i));
            }
            pieces[j] = temp.OrderBy(x => random.Next()).ToList();
            for (int i = 0; i < pieceCount; i++)
            {
                int x = pieces[j][i].X;
                int y = pieces[j][i].Y;
                pieces[j][i].id = i;
                board.Grid[x, y, 0] = j;
                board.Grid[x, y, 1] = i;
            }

        }

    }

    public Piece nextMovePiece()
    {
        int player = currentTurn % 2;
        List<Piece> cur_pieces = pieces[player];
        while (cur_pieces[piecePtr[player]].isDead())
            piecePtr[player]++;
        return cur_pieces[piecePtr[player]];
    }

    public void step(actionSet action)
    {
        int cur_player = currentTurn % 2;
        List<Piece> cur_pieces = pieces[cur_player];
        List<Piece> enemy_pieces = pieces[(cur_player + 1) % 2];

        Piece cur_piece = cur_pieces[piecePtr[cur_player]];

        if (!board.IsValidMove(action.move_target.x, action.move_target.y))
        {
            throw new InvalidOperationException("移动目标越界或已有棋子");
        }

        if (action.move_target.x - cur_piece.X + action.move_target.y - cur_piece.Y > cur_piece.Speed)
        {
            throw new InvalidOperationException("移动距离超过棋子速度");
        }

        board.UpdatePiecePosition(cur_piece, action.move_target.x, action.move_target.y);

        if (action.attack == 1)
        {
            //攻击逻辑暂不明确，目前会选定周围一圈中优先发现的敌人进行攻击
            Piece target = null;
            for (int i = -1; i <= 1; i++)
            {
                for (int j = -1; j <= 1; j++)
                {
                    if (i == 0 && j == 0)
                    {
                        continue;
                    }
                    int target_x = cur_piece.X + i;
                    int target_y = cur_piece.Y + j;
                    if (target_x >= 0 && target_x < board.Grid.GetLength(0) && target_y >= 0 && target_y < board.Grid.GetLength(1))
                    {
                        if (board.Grid[target_x, target_y, 0] == (cur_player + 1) % 2)
                        {
                            Piece temp = enemy_pieces[board.Grid[target_x, target_y, 1]];
                            if (temp == null || temp.isDead())
                                continue;
                            target = temp;
                            break;
                        }
                    }
                }
            }
            if (target != null)
            {
                cur_piece.Attack(target);
            }
            else
            {
                Console.WriteLine("未找到可攻击的目标");
            }
        }

        if (action.skill == 1)
        {
            cur_piece.UseSkill();
        }

        currentTurn++;
        isGameOver = IsGameOver();
    }

    //public void Start()
    //{
    //    while (!IsGameOver())
    //    {
    //        Player currentPlayer = players[currentTurn % 2];
    //        Console.Clear();
    //        board.Render();
    //        Console.WriteLine($"Player {currentPlayer.Id}'s turn");
    //        currentPlayer.TakeTurn(board);
    //        currentTurn++;
    //    }
    //    Console.WriteLine("Game Over!");
    //}

    public bool IsGameOver()
    {
        for (int i = 0; i <= 1; i++)
        {
            bool allDead = true;
            foreach (Piece piece in pieces[i])
            {
                if (!piece.isDead())
                {
                    allDead = false;
                    break;
                }
            }
            if (allDead)
            {
                winner = i;
                return true;
            }
        }
        return false;
    }
}

class Board
{
    private int width, height;
    public int[,,] Grid;

    public Board(int width, int height)
    {
        this.width = width;
        this.height = height;
        Grid = new int[width, height, 2];
        for (int i = 0; i < width; i++)
        {
            for (int j = 0; j < height; j++)
            {
                Grid[i, j, 0] = -1; //0维保存棋子拥有者
                Grid[i, j, 1] = -1; //1维保存棋子编号
            }
        }
    }

    public bool IsValidMove(int x, int y)
    {
        return x >= 0 && x < width && y >= 0 && y < height && Grid[x, y, 0] == -1;
    }

    public void UpdatePiecePosition(Piece piece, int newX, int newY)
    {
        Grid[piece.X, piece.Y, 0] = -1;
        Grid[piece.X, piece.Y, 1] = -1;
        piece.X = newX;
        piece.Y = newY;
        Grid[piece.X, piece.Y, 0] = piece.owner;
        Grid[piece.X, piece.Y, 1] = piece.id;
    }


}

class Player
{
    public int id { get; private set; }
    public Player(int id)
    {
        this.id = id;
    }
    public actionSet policy(Piece next)
    {
        Console.WriteLine($"Player {id}'s turn");
        Console.WriteLine($"Movable Piece: {next.owner}-{next.id}");
        Console.WriteLine("Please key in the target coordinate: (separate x and y with space)");
        string input = Console.ReadLine();
        string[] parts = input.Split(' ');
        int tmp_x = 0, tmp_y = 0;
        int attak, skill;
        if (parts.Length == 2 && int.TryParse(parts[0], out tmp_x) && int.TryParse(parts[1], out tmp_y))
        {
            Console.WriteLine($"Coordinate: {tmp_x} 和 {tmp_y}");
        }
        else
        {
            Console.WriteLine("输入无效，请确保输入两个用空格分隔的数字。");
        }

        Console.WriteLine("Please key in the Attack Operation: (0: no op, 1: attack)");
        input = Console.ReadLine();
        if (int.TryParse(input, out attak))
        {
            Console.WriteLine($"Attack Operation: {attak}");
        }
        else
        {
            Console.WriteLine("输入无效，请确保输入一个数字。");
        }

        Console.WriteLine("Please key in the Skill Operation: (0: no op, 1: skill)");
        input = Console.ReadLine();
        if (int.TryParse(input, out skill))
        {
            Console.WriteLine($"Skill Operation: {skill}");
        }
        else
        {
            Console.WriteLine("输入无效，请确保输入一个数字。");
        }

        return new actionSet { move_target = new Point { x = tmp_x, y = tmp_y }, attack = attak, skill = skill };
    }
}

class Piece
{
    public int X { get; internal set; }
    public int Y { get; internal set; }
    public int Health { get; internal set; } = 10;
    public int Damage { get; internal set; } = 3;
    public int Speed { get; internal set; } = 1;
    public int owner;
    public int id;

    public bool isDead()
    {
        return Health <= 0;
    }


    public Piece(int x, int y, int owner, int id)
    {
        X = x;
        Y = y;
        this.owner = owner;
        this.id = id;
    }

    public void Attack(Piece target)
    {
        Random rnd = new Random();
        int damageDealt = rnd.Next(1, Damage + 1);
        target.Health -= damageDealt;
        Console.WriteLine($"Piece {owner}-{id} Attacked enemy {target.owner}-{target.id} for {damageDealt} damage!");
    }

    public void UseSkill()
    {
        Console.WriteLine("Special skill not implemented yet.");
    }

}

class Visualizers
{
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
                    Console.Write($"{grid[i, j, 0]}-{grid[i, j, 1]} ");
                }
                else
                {
                    Console.Write("--- ");
                }
            }
            Console.WriteLine();
        }

        for (int i = 0; i < game.pieces[0].Count; i++)
        {
            Console.WriteLine($"Piece 0-{i} Health: {game.pieces[0][i].Health}    Piece 1-{i} Health: {game.pieces[1][i].Health}");
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
