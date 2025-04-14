using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace server
{
    class Piece
    {
        public int health { get; private set; }
        public int max_health { get; private set; }
        public int physical_resist { get; private set; }
        public int magic_resist { get; private set; }//豁免值
        public int physical_damage { get; private set; }
        public int magic_damage { get; private set; }
        public int action_points { get; private set; }
        public int max_action_points { get; private set; }//行动位
        public int spell_slots { get; private set; }
        public int max_spell_slots { get; private set; }//法术位
        public float movement { get; private set; }
        public float max_movement { get; private set; }//行动力

        public int id; //专属id，由初始行动序列分配，有棋子死亡时不重新分配

        // 属性项
        public int strength { get; private set; }
        public int dexterity { get; private set; }
        public int intelligence { get; private set; }

        // 实时项
        public Point position { get; set; }// 移动函数需要修改棋子坐标和高度
        public int height { get; set; }
        public int attack_range { get; private set; }
        public List<Spell> spell_list { get; private set; }
        public int deathRound { get; set; } = -1;

        // 标识项
        public int team { get; private set; }
        public int queue_index { get; private set; }
        public bool is_alive { get; private set; }
        public bool is_in_turn { get; private set; }
        public bool is_dying { get; private set; } // 濒死状态
        public double spell_range { get; private set; }
        public void setActionPoints(int action_points)
        {
            this.action_points = action_points;
        }
        public int getActionPoints()
        {
            return action_points;
        }

        // 构造函数
        public Piece()
        {
            spell_list = new List<Spell>();
            is_alive = true;
            is_dying = false;
            is_in_turn = false;
        }

        // 方法

        //前一版文档中将棋子攻击行为逻辑置于此处，为了避免棋子与棋子的直接交互，所有交互行为逻辑现在都由environment类处理，此处的方法仅用于维护内部状态（待定）

        public void receiveDamage(int damage, string type)
        {
            if (type == "physical")
            {
                damage = Math.Max(0, damage - physical_resist); // 物理伤害计算
            }
            else if (type == "magic")
            {
                damage = Math.Max(0, damage - magic_resist); // 法术伤害计算
            }
            else
            {
                throw new ArgumentException("Invalid damage type");
            }
            health -= damage; // 扣除生命值

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
            public void SetMaxHealthTo(int value) => p.max_health = value;

            public void SetPhysicalResistTo(int value) => p.physical_resist = value;
            public void SetMagicResistTo(int value) => p.magic_resist = value;
            public void SetPhysicalDamageTo(int value) => p.physical_damage = value;   //为什么是DicePair
            public void SetMagicDamageTo(int value) => p.magic_damage = value;
            public void SetMaxMovementTo(float value) => p.max_movement = value;
            public void SetMaxMovementBy(float value) => p.max_movement += value;
            public void SetMovementTo(float value) => p.movement = value;
            public void SetAttackRangeTo(int value) => p.attack_range = value;
            public void SetMaxActionPointsTo(int value) => p.max_action_points = value;
            public void SetMaxSpellSlotsTo(int value) => p.max_spell_slots = value;

            public void SetTeamTo(int value) => p.team = value;

            public void SetRangeTo(int value) => p.attack_range = value; // 物理攻击范围

            public void SetMaxActionPoints()
            {
                if (p.strength <= 13) SetMaxActionPointsTo(1);
                else if (p.strength <= 21) SetMaxActionPointsTo(2);
                else SetMaxActionPointsTo(3);
            }
            public void SetMaxSpellSlots()
            {
                if (p.intelligence <= 3) SetMaxSpellSlotsTo(1);
                else if (p.intelligence <= 7) SetMaxSpellSlotsTo(2);
                else if (p.intelligence <= 12) SetMaxSpellSlotsTo(3);
                else if (p.intelligence <= 16) SetMaxSpellSlotsTo(5);
                else if (p.intelligence <= 21) SetMaxSpellSlotsTo(8);
                else SetMaxSpellSlotsTo(9);
            }

            public void SetStrengthTo(int value)
            {
                if (value < 0) throw new ArgumentOutOfRangeException("Strength cannot be negative.");
                else p.strength = value;
            }
            public void SetDexterityTo(int value)
            {
                if (value < 0) throw new ArgumentOutOfRangeException("Dexterity cannot be negative.");
                else p.dexterity = value;
            }
            public void SetIntelligenceTo(int value)
            {
                if (value < 0) throw new ArgumentOutOfRangeException("Intelligence cannot be negative.");
                else p.intelligence = value;
            }

            public void SetActionPointsTo(int value) => p.action_points = value;
            public void ChangeActionPointsBy(int delta) => p.action_points += delta;

            public void SetSpellSlotsTo(int value) => p.spell_slots = value;
            public void ChangeSpellSlotsBy(int delta) => p.spell_slots += delta;

            public void SetAlive(bool value) => p.is_alive = value;
            public void SetDying(bool value) => p.is_dying = value;

            public void SetPosition(Point newPos) => p.position = newPos;

            public void SetMagicResistBy(int value) => p.magic_resist -= value;
            public void SetPhysicResistBy(int value) => p.physical_resist -= value;

            //调整值计算
            public int StrengthAdjustment() { if (p.strength <= 7) return 1; else if (p.strength <= 13) return 2; else if (p.strength <= 16) return 3; else return 4; }
            public int DexterityAdjustment() { if (p.dexterity <= 7) return 1; else if (p.dexterity <= 13) return 2; else if (p.dexterity <= 16) return 3; else return 4; }
            public int IntelligenceAdjustment() { if (p.intelligence <= 7) return 1; else if (p.intelligence <= 13) return 2; else if (p.intelligence <= 16) return 3; else return 4; }

        }

        // Env 专用访问接口
        internal Accessor GetAccessor()
        {
            return new Accessor(this);
        }

    }
}
