using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace server
{
    abstract class Piece
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

        // 方法

        //前一版文档中将棋子攻击行为逻辑置于此处，为了避免棋子与棋子的直接交互，所有交互行为逻辑现在都由environment类处理，此处的方法仅用于维护内部状态（待定）

        public void receiveDamage(int damage, string type)
        {
            //接收伤害。免伤逻辑应在env中处理完毕，此处直接进行扣血和死亡判定。
        }

        public bool deathCheck()
        {
            return is_alive;
        }
        // Env 专用修改器（只 Env 可通过 internal 方法调用）
        public class Accessor
        {
            private Piece p;
            internal Accessor(Piece piece)
            {
                this.p = piece;
            }

            // 清晰的命名避免与属性冲突
            public void SetHealthTo(int value) => p.health = value;
            public void ChangeHealthBy(int delta) => p.health += delta;

            public void SetActionPointsTo(int value) => p.action_points = value;
            public void ChangeActionPointsBy(int delta) => p.action_points += delta;

            public void SetSpellSlotsTo(int value) => p.spell_slots = value;
            public void ChangeSpellSlotsBy(int delta) => p.spell_slots += delta;

            public void SetAlive(bool value) => p.is_alive = value;
            public void SetDying(bool value) => p.is_dying = value;

            public void SetPosition(Point newPos) => p.position = newPos;
        }

        // Env 专用访问接口
        internal Accessor GetAccessor()
        {
            return new Accessor(this);
        }
        
    }
}
