using System;
using System.Collections.Generic;
using System.Linq;

public class Game
{
    public Board board { get; private set; }
    public List<List<Piece>> pieces { get; private set; }
    public int currentTurn { get; private set; }
    public bool isGameOver { get; private set; }
    public int winner { get; private set; }

    private int maxPiecesCount;

    // 构造函数，初始化游戏
    public Game(int width, int height, int pieceCount)
    {
        board = new Board(width, height);
        pieces = new List<List<Piece>> { new List<Piece>(), new List<Piece>() };
        winner = -1;
        currentTurn = 0;
        isGameOver = false;
        maxPiecesCount = pieceCount;

        // 创建棋子，按顺序排列
        for (int j = 0; j <= 1; j++)
        {
            Random random = new Random();
            List<Piece> temp = new List<Piece>();
            for (int i = 0; i < pieceCount; i++)
            {
                int x = j == 0 ? 0 : board.Grid.GetLength(0) - 1;  // 玩家 0 在左边，玩家 1 在右边
                int y = i;
                temp.Add(new CommonPiece(x, y, j, i));
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

    // 获取当前轮到的玩家的可移动棋子
    public Piece nextMovePiece()
    {
        int player = currentTurn % 2;
        List<Piece> cur_pieces = pieces[player];

        // 计算当前轮到操作的棋子序号
        int pieceIndex = currentTurn / 2; // 每个玩家每轮操作自己的一个棋子
        pieceIndex = pieceIndex % cur_pieces.Count;// 保证pieceIndex不会越界并且能循环

        return cur_pieces[pieceIndex];
    }

    // 执行一步操作
    public void step(actionSet action)
    {
        int cur_player = currentTurn % 2;
        List<Piece> cur_pieces = pieces[cur_player];
        List<Piece> enemy_pieces = pieces[(cur_player + 1) % 2];

        Piece cur_piece = cur_pieces[currentTurn / 2];  // 当前要操作的棋子，轮到本方第 N 个棋子



        if (!board.IsValidMove(action.move_target.x, action.move_target.y))
        {
            throw new InvalidOperationException("移动目标越界或已有棋子");
        }

        if (Math.Abs(action.move_target.x - cur_piece.X) + Math.Abs(action.move_target.y - cur_piece.Y) > cur_piece.Speed)
        {

            throw new InvalidOperationException("移动距离超过棋子速度");
        }

        board.UpdatePiecePosition(cur_piece, action.move_target.x, action.move_target.y);

        if (action.attack == 1)
        {
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
                //如果目标棋子死亡，立马删除该棋子
                if(target.isDead())
                {
                    board.RemovePiece(target);
                    enemy_pieces.Remove(target);
                }
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

    // 判断游戏是否结束
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
