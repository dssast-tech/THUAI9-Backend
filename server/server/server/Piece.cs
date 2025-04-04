using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace server
{
    abstract class Piece
    {
        int health, max_health;
        int physical_resist, magic_resist;
        DicePair physical_damage, magic_damage;
        int action_points, max_action_points;
        int spell_slots, max_spell_slots;
        float movement, max_movement;

        // 属性项
        int strength, dexterity, intelligence;

        // 实时项
        Point position;
        int height;
        int attack_range;
        List<Spell> spell_list;

        // 标识项
        int team;
        int queue_index;
        bool is_alive;
        bool is_in_turn;
        bool is_dying; // 濒死状态

        // 方法

        //前一版文档中将棋子攻击行为逻辑置于此处，为了避免棋子与棋子的直接交互，所有交互行为逻辑现在都由environment类处理，此处的方法仅用于维护内部状态（待定）

        void receiveDamage(int damage, string type)
        {
            //接收伤害。免伤逻辑应在env中处理完毕，此处直接进行扣血和死亡判定。
        }

        bool deathCheck()
        {
            return is_alive;
        }
    }
}
