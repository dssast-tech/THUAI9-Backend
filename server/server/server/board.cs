using System;
using System.Collections.Generic;
using System.Diagnostics.Tracing;
using System.Linq;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;
using static System.Runtime.InteropServices.JavaScript.JSType;

//仅维护信息
namespace server
{
    public struct Cell
    {
        public int state { get; set; } // 0: 空地, 1: 可行走, 2: 占据, -1: 禁止
        public int playerId { get; set; } // 0: 无人, 1: 玩家1, 2: 玩家2
        public int pieceId { get; set; }

        public Cell(int state_, int playerId_ = -1, int pieceId_ = -1)
        {
            state = state_;
            playerId = playerId_;
            pieceId = pieceId_;
        }
    }


    class Board
    {
        public int width { get; private set; }
        public int height { get; private set; }
        public Cell[,] grid { get; private set; }// 0: 空地, 1: 可行走, 2: 占据, -1: 禁止 //不知道 0 的意义，实现没有用到 4/10
        public int[,] height_map { get; private set; }
        
        public int boarder { get; private set; } // 分界线

        public int getWidth()
        {
            return width;
        }

        public int getHeight()
        {
            return height;
        }

        public int[,] validTarget(Piece p, float movement)// 接受参数棋子和行动力，返回该棋子的mask图，-1表示不可达，其他数字为到达该点的移动力消耗，如原地不动为0，需要遍历，时间开销比较大
        {
            //返回一张mask图，以01标记所有能抵达的点，用于提交给client,以及env中的合法性判定
            //不一定要实现

            int[,] mask = new int[width, height];
            for (int x = 0; x < width; x++)
            {
                for (int y = 0; y < height; y++)
                {
                    mask[x, y] = -1;
                }
            }

            for (int x = 0; x < width; x++)
            {
                for (int y = 0; y < height; y++)
                {
                    Point target = new Point(x, y);
                    if (grid[x, y].state == 1 && (Math.Abs(x - target.x) + Math.Abs(y - target.y) <= movement))
                    {
                        var (path, cost) = FindShortestPath(p, p.position, target, movement);
                        if (path != null && cost <= movement)
                        {
                            mask[x, y] = (int)MathF.Ceiling(cost);
                        }
                    }
                    
                }
            }

            return mask;
        }


        public bool movePiece(Piece p, Point to, float movement, out List<Vector3Serializable> Vec_path)
        {
            if (!IsWithinBounds(to) || grid[to.x, to.y].state != 1)
            {
                Vec_path = null;
                return false; // 终点超出地图大小、被占据、禁止到达
            }

            (List<Point>? path, float cost) = FindShortestPath(p, p.position, to, movement);
            if (path == null)
            {
                Vec_path = null;
                return false; //没有可达路径（沿途被阻挡）、行动力不足
            }

            List<Vector3Serializable> vectorPath = path.
                Where(point => point.x >= 0 && point.x < width && point.y >= 0 && point.y < height)
                .Select(point => new Vector3Serializable(point.x, point.y, height_map[point.x, point.y]))
                .ToList();
            Vec_path = vectorPath;
            // p.movement -= cost;
            grid[p.position.x, p.position.y].state = 1; // 原位置状态更新
            grid[p.position.x, p.position.y].playerId = -1; // 原位置玩家ID更新
            grid[p.position.x, p.position.y].pieceId = -1; // 原位置棋子ID更新
            grid[to.x, to.y].state = 2; // 目标位置状态更新
            grid[to.x, to.y].playerId = p.team; // 目标位置玩家ID更新
            grid[to.x, to.y].pieceId = p.id; // 目标位置棋子ID更新
            p.position = to; // 更新棋子的位置
            p.height = height_map[to.x, to.y]; // 更新棋子的高度

            return true;
        }

        public bool isOccupied(Point p)
        {
            return grid[p.x, p.y].state == 2; 
        }

        public int getHeight(Point p)
        {
            return height_map[p.x, p.y];
        }

        public void removePiece(Piece p) //
        {
            throw new NotImplementedException();
        }

        private bool IsWithinBounds(Point p)// 目标位置需要在矩形棋盘内部
        {
            return p.x >= 0 && p.x < width && p.y >= 0 && p.y < height;
        }

        private List<Point> GetNeighbors(Point p)// 返回点p的所有可达邻点表
        {
            List<Point> neighbors = new List<Point>
            {
                new Point(p.x - 1, p.y),
                new Point(p.x + 1, p.y),
                new Point(p.x, p.y - 1),
                new Point(p.x, p.y + 1)
            };

            return neighbors.Where(n => IsWithinBounds(n) && grid[n.x, n.y].state == 1).ToList();
        }

        private (List<Point>? path, float cost) FindShortestPath(Piece p, Point start, Point goal, float movement)// 返回棋子移动的最短路径和需要消耗的行动力大小，如果需要显示路径可调用
        {                                                                                                         // path是棋子移动路径，可为null
            Dictionary<Point, Point> cameFrom = new Dictionary<Point, Point>();
            Dictionary<Point, float> costSoFar = new Dictionary<Point, float>();
            PriorityQueue<Point, float> frontier = new PriorityQueue<Point, float>();

            frontier.Enqueue(start, 0);
            cameFrom[start] = start;
            costSoFar[start] = 0;

            while (frontier.Count > 0)
            {
                Point current = frontier.Dequeue();

                if (current.Equals(goal))
                {
                    break;
                }

                foreach (var next in GetNeighbors(current))
                {
                    float heightDiff = height_map[next.x, next.y] - height_map[current.x, current.y];
                    float moveCost = 1 + Math.Max(0, heightDiff); // 爬山消耗：1 + 高度差（下坡不增加）

                    float newCost = costSoFar[current] + moveCost;

                    if (newCost > movement)
                        continue; // 超出可用行动力，不考虑这个点

                    if (!costSoFar.ContainsKey(next) || newCost < costSoFar[next])
                    {
                        costSoFar[next] = newCost;
                        frontier.Enqueue(next, newCost);
                        cameFrom[next] = current;
                    }
                }
            }

            if (!cameFrom.ContainsKey(goal))
            {
                return (null, 0); // 不可达
            }

            List<Point> path = new List<Point>();
            Point temp = goal;

            while (!temp.Equals(start))
            {
                path.Add(temp);
                temp = cameFrom[temp];
            }

            path.Reverse();

            return (path, costSoFar[goal]); // 返回路径和行动力消耗
        }

        public void init(string filePath)// 接受参数txt文件case，case格式参见 server/BoardCase/case1.txt
        {
            string[] lines = File.ReadAllLines(filePath);
            string[] dimensions = lines[0].Split(' ');
            width = int.Parse(dimensions[0]);
            height = int.Parse(dimensions[1]);
            Console.WriteLine($"Width: {width}, Height: {height}");

            // 加载地图数据
            grid = new Cell[width, height];
            height_map = new int[width, height];
            boarder = height / 2; // 设定分界线为height的一半

            int lineIndex = 2; // 跳过第一行和空行

            // 读取grid
            for (int y = 0; y < height; y++)
            {
                var values = lines[lineIndex].Split(',');
                for (int x = 0; x < width; x++)
                {
                    grid[x, y].state = int.Parse(values[x].Trim());
                }
                lineIndex++;
            }

            lineIndex++;

            // 初始化棋盘上所有格子的playerID为-1
            for (int x = 0; x < width; ++x)
            {
                for (int y = 0; y < height; ++y)
                {
                    grid[x, y].playerId = -1;
                }
            }

            // 初始化棋盘上所有格子的pieceID为-1
            for (int x = 0; x < width; ++x)
            {
                for (int y = 0; y < height; ++y)
                {
                    grid[x, y].pieceId = -1;
                }
            }

            // 读取height_map
            for (int y = 0; y < height; y++)
            {
                var values = lines[lineIndex].Split(',');
                for (int x = 0; x < width; x++)
                {
                    height_map[x, y] = int.Parse(values[x].Trim());
                }
                lineIndex++;
            }
        }
            public void init_pieces_location(List<Piece> player1_pieces, List<Piece> player2_pieces)
        {
            // 处理玩家棋子处在不同侧的错误情况
            bool player1_pieces_ontop = player1_pieces.All(piece => piece.position.y < boarder);
            bool player1_pieces_below = player1_pieces.All(piece => piece.position.y > boarder);
            if (!(player1_pieces_ontop || player1_pieces_below))
            {
                throw new InvalidOperationException("Player 1's chess pieces are placed on both sides of the board.");
            }

            bool player2_pieces_ontop = player2_pieces.All(piece => piece.position.y < boarder);
            bool player2_pieces_below = player2_pieces.All(piece => piece.position.y >= boarder);
            if (!(player2_pieces_ontop || player2_pieces_below))
            {
                throw new InvalidOperationException("Player 2's chess pieces are placed on both sides of the board.");
            }

            // 确保两个玩家的棋子不在同一侧
            if ((player1_pieces_ontop && player2_pieces_ontop) || (player1_pieces_below && player2_pieces_below))
            {
                // 并没有重合检测，不同玩家棋子重合仍然在这里判断
                Console.WriteLine("不同玩家不能有棋子处在同侧");//直接退出程序，后续可以修改
                throw new InvalidOperationException("Both players' chess pieces are placed on the same side of the board.");
            }

            // 所有棋子的坐标grid初始化为2
            foreach (var piece in player1_pieces)
            {
                grid[piece.position.x, piece.position.y].state = 2;
                grid[piece.position.x, piece.position.y].playerId = piece.team; // 玩家1的棋子
                grid[piece.position.x, piece.position.y].pieceId = piece.id;
            }
            foreach (var piece in player2_pieces)
            {
                grid[piece.position.x, piece.position.y].state = 2;
                grid[piece.position.x, piece.position.y].playerId = piece.team; // 玩家2的棋子
                grid[piece.position.x, piece.position.y].pieceId = piece.id;
            }
        }
    }
}
