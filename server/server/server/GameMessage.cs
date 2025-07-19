using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Server
{

    class MessageWrapper<T>
    {
        public int type { get; set; } // 0for init, 1 for game
        public T data { get; set; }
    }

    class InitGameMessage
    { 
        public int pieceCnt { get; set; }
        public int id { get; set; }
        public Board board { get; set; }
    }

    class InitPolicyMessage
    {
        public List<pieceArg> pieceArgs;
    }
    class GameMessage
    {
        public List<Piece> action_queue; // 棋子的行动队列
        public Piece current_piece; // 当前行动的棋子
        public int round_number; // 当前回合数
        public List<SpellContext> delayed_spells; // 延时法术列表
        public Player player1; // 玩家1
        public Player player2; // 玩家2
        public Board board; // 棋盘
    }
    class PolicyMessage
    {
        public actionSet action_set;
    }

    class pieceArg
    {
        public int strength;
        public int intelligence;
        public int dexterity;
        public Point equip;
        public Point pos;
    }

}
