public class Board
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
                Grid[i, j, 0] = -1; // 0维保存棋子拥有者
                Grid[i, j, 1] = -1; // 1维保存棋子编号
            }
        }
    }

    // 判断移动是否有效
    public bool IsValidMove(int x, int y)
    {
        return x >= 0 && x < width && y >= 0 && y < height && Grid[x, y, 0] == -1;
    }

    // 更新棋子位置
    public void UpdatePiecePosition(Piece piece, int newX, int newY)
    {
        if (piece.isDead()) return;

        Grid[piece.X, piece.Y, 0] = -1;
        Grid[piece.X, piece.Y, 1] = -1;
        piece.X = newX;
        piece.Y = newY;
        Grid[piece.X, piece.Y, 0] = piece.owner;
        Grid[piece.X, piece.Y, 1] = piece.id;
    }

    public void RemovePiece(Piece piece)
    {
        Grid[piece.X, piece .Y, 0] = -1;
        Grid[piece.X, piece.Y, 1] = -1;
        Console.WriteLine($"Piece {piece.owner}-{piece.id} has been removed from the board.");
    }
}
