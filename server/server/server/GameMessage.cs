using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace server
{

    class MessageWrapper<T>
    {
        public int type; // 0for init, 1 for game
        public T data;
    }

    class InitGameMessage
    {
        public int pieceCnt; //
        public int id;
        public Board board;
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
        public struct actionSet;
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
