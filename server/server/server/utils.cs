using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

//所有辅助类应置于此文件中


namespace server
{
    struct Point(int x, int y)//添加构造函数
    {
        public int x = x, y = y;
    }

    struct actionSet
    {
        public Point move_target;
        public bool attack;
        public  AttackContext attack_context;
        public bool spell;
        public  SpellContext spell_context;
    }

    struct initializationSet
    {
        //用于棋子初始化的信息，具体内容待定
    }

    struct DicePair
    {

    }

    struct Message
    {
        //通信预留转接类
    }

    struct AttackContext
    {
        public Piece attacker;       // 攻击发起者
        public Piece target;         // 攻击目标
        public AttackType attackType;// 攻击类型（物理/法术/卓越等）
        public bool isCritical;      // 是否暴击
        public int damageDealt;      // 造成的伤害值
        public bool isHit;           // 是否命中
        public int advantageValue;   // 优势值
        public Point attackPosition; // 攻击发起位置（用于范围判定）
        
        // 物理攻击特有
        public int attackRoll;       // 攻击投掷值(1d20+调整值)
        public int defenseValue;     // 防御值(豁免+调整值)
        
        
        // 死亡检定相关
        public bool causedDeath;     // 是否导致死亡
        public int deathRoll;        // 死亡检定骰值
    }

    enum AttackType
    {
        Physical,    // 物理攻击
        Spell,       // 法术攻击
        Excellence   // 卓越攻击
    }

    struct SpellContext
    {
        public Piece caster;          // 施法者
        public Spell spell;          // 关联的法术数据模板
        public int spellPower;       // 法术强度（影响命中加值）
        public TargetType targetType; // 目标类型（单体/范围/自身等）
        public Piece target;          // 单体目标（当targetType=Single时使用）
        public Area targetArea;       // 区域目标（圆心+半径）
        public float spellRange;      // 施法最大距离
        public SpellEffectType effectType;  // 效果类型（伤害/治疗/buff等）
        public DamageType damageType;       // 伤害类型（火焰/冰霜等）
        public int damageValue;        // 伤害值（如3d6）
        public int healValue;               // 治疗量
        public int effectValue;             // 通用效果值（用于buff/debuff）
        public bool isDelaySpell;     // 是否为延时法术    //瞬发改为延时1/延时0
        public int baseLifespan;      // 基础持续时间（回合数）
        public int spellLifespan;     // 剩余持续时间
        public bool isDamageSpell;    //是否为伤害法术
        public bool isAreaEffect;     // 是否为范围效果
        public bool isLockingSpell;   // 是否为锁定类法术（无视范围敌我）

        public int spellCost;         // 法术位消耗
        public int actionCost;        // 行动点消耗（通常为1）

        public bool isHit;            // 是否命中
        public bool isCritical;       // 是否暴击
    }

    // 配套枚举类型
    public enum TargetType { Single, Area, Self, Chain }
    public enum SpellEffectType { Damage, Heal, BuffDamage, DebuffResist }
    public enum DamageType { Fire, Ice, Lightning, Physical, Pure }//技能仅示例，有待完善

    //注：任何类调用任何攻击行为时，参数最好都应该封装在context包中进行传递，不应产生额外的独立参数，这样可以避免参数过多导致的函数调用混乱，也有利于向前端传递的日志输出
    class Area
    {
        public int x { get; set; }
        public int y { get; set; }
        public int radius { get; set; }

        public bool Contains(Point point)
        {
            double distance = Math.Sqrt(Math.Pow(point.x - x, 2) + Math.Pow(point.y - y, 2));
            return distance <= radius;
        }
    }

    struct Spell
    {
        //法术属性打包在此（如法术名称、法术范围）
    }

    //应该区分spell和spellcontext，后者可理解为一个已经打出的法术，包含目标信息，主要用于env类；前者是法术本身的属性，主要用于棋子类中标记该棋子可用的法术
}
