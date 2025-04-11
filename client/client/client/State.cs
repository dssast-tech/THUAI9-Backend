using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace client
{
    class Piece
    {
        public int health { get; private set; }
        public int max_health { get; private set; }
        public int physical_resist { get; private set; }
        public int magic_resist { get; private set; }
        public DicePair physical_damage { get; private set; }
        public DicePair magic_damage { get; private set; }
        public int action_points { get; private set; }
        public int max_action_points { get; private set; }
        public int spell_slots { get; private set; }
        public int max_spell_slots { get; private set; }
        public float movement { get; private set; }
        public float max_movement { get; private set; }

        // 属性项
        public int strength { get; private set; }
        public int dexterity { get; private set; }
        public int intelligence { get; private set; }

        // 实时项
        public Point position { get; set; }// 移动函数需要修改棋子坐标和高度
        public int height { get; set; }
        public int attack_range { get; private set; }
        public List<Spell> spell_list { get; private set; }

        // 标识项
        public int team { get; private set; }
        public int queue_index { get; private set; }
        public bool is_alive { get; private set; }
        public bool is_in_turn { get; private set; }
        public bool is_dying { get; private set; } // 濒死状态
        public double spell_range { get; private set; }

        // 构造函数
        public Piece()
        {
            spell_list = new List<Spell>();
        }

    }

    class Board
    {
        int width, height;
        int[,] grid;  // 0: 空地, 1: 可行走, 2: 占据, -1: 禁止 //不知道 0 的意义，实现没有用到 4/10
        int[,] height_map;
    }

    class Env
    {
        List<Piece> action_queue;
        Piece current_piece;
        int round_number;
        List<SpellContext> delayed_spells;
        Player player1;
        Player player2;
        Board board;
        bool isGameOver;
    }
}
