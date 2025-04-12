using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Serialization;

// 环境类：游戏核心控制器，管理所有游戏逻辑和状态
namespace server
{
    class Env
    {
        List<Piece> action_queue;       // 行动队列，按顺序存储待行动棋子
        Piece current_piece;            // 当前正在执行行动的棋子
        int round_number;               // 当前回合计数器
        List<SpellContext> delayed_spells; // 延时生效的法术上下文列表
        Player player1;                 // 玩家1实例
        Player player2;                 // 玩家2实例
        Board board;                    // 棋盘状态管理器
        bool isGameOver;                // 游戏结束标志位

        // 游戏初始化方法
        void initialize()
        {
            // 初始化玩家、棋盘状态，进行合法性校验
            // 注意：需要先调用player的localInit进行本地初始化
        }

        // 获取当前棋子的行动指令集
        actionSet getAction()
        {
            // 通过当前玩家对象获取行动决策（需具体实现）
            throw new NotImplementedException();
        }

        // 骰子投掷方法：生成指定面数的随机数
        private int RollDice(int sides)
        {
            Random random = new Random();
            return random.Next(1, sides + 1);  // 返回1到sides的闭区间随机值
        }

        //-----------------------------------------------------------------攻击逻辑------------------------------------------------------------//
        // 执行攻击上下文
        void executeAttack(AttackContext context)
        {
            // 行动点校验
            if (context.attacker.action_points <= 0)
            {
                return; // 无可用行动点，终止攻击流程
            }

            // 攻击范围处理逻辑
            if (!IsInAttackRange(context.attacker, context.target))
            {
                // 路径计算与移动尝试
                Point bestMovePos = CalculateBestMovePosition(context.attacker, context.target);
                if (!board.movePiece(context.attacker, bestMovePos, context.attacker.movement))
                {
                    return; // 移动失败，终止攻击
                }
            }

            // D20骰子攻击检定
            int attackRoll = RollDice(20);
            bool isHit = false;
            bool isCritical = false;

            // 特殊骰值处理
            if (attackRoll == 1) // 大失败
            {
                isHit = false;
            }
            else if (attackRoll == 20) // 大成功
            {
                isHit = true;
                isCritical = true;
            }
            else // 常规攻击计算
            {
                // 优势值计算（地形+环境）
                int advantageValue = CalculateAdvantageValue(context.attacker, context.target);
                int attackThrow = attackRoll +
                                GetStrengthModifier(context.attacker.strength) +
                                advantageValue;
                int defenseValue = context.target.physical_resist +
                                GetDexterityModifier(context.target.dexterity);
                isHit = attackThrow > defenseValue;
            }

            // 伤害处理逻辑
            if (isHit)
            {
                int damage = context.attacker.physical_damage.Roll();
                if (isCritical) damage *= 2; // 暴击伤害翻倍
                context.target.receiveDamage(damage, "physical");

                // 死亡状态处理
                if (context.target.health <= 0)
                {
                    HandleDeathCheck(context.target); // 执行死亡检定
                }
            }

            context.attacker.action_points--; // 消耗行动点
        }

        // 判断攻击范围（欧几里得距离）
        private bool IsInAttackRange(Piece attacker, Piece target)
        {
            double distance = Math.Sqrt(
                Math.Pow(attacker.position.x - target.position.x, 2) +
                Math.Pow(attacker.position.y - target.position.y, 2)
            );
            return distance <= attacker.attack_range;
        }

        // 死亡检定处理
        private void HandleDeathCheck(Piece target)
        {
            int deathRoll = RollDice(20);
            if (deathRoll == 20) // 奇迹生还
            {
                target.health = 1;
            }
            else if (deathRoll == 1) // 立即死亡
            {
                target.is_alive = false;
                board.removePiece(target);
                action_queue.Remove(target);
                CheckGameOver(); // 触发游戏结束检查
            }
            else // 濒死状态
            {
                target.is_dying = true;
            }
        }

        //-----------------------------------------------------------------法术逻辑------------------------------------------------------------//
        // 执行法术上下文
        void executeSpell(SpellContext context)
        {
            // 资源校验（行动点和法术位）
            if (context.caster.action_points <= 0 || context.caster.spell_slots <= 0)
            {
                return; // 资源不足终止施法
            }

            // 法术类型分发处理
            if (context.isDelaySpell)
            {
                ExecuteDelaySpell(context); // 延时法术处理
            }
            else if (context.isAreaEffect)
            {
                ExecuteAreaSpell(context); // 范围法术处理
            }
            else
            {
                ExecuteSingleTargetSpell(context); // 单体法术处理
            }

            // 资源消耗
            context.caster.action_points--;
            context.caster.spell_slots -= context.spellCost;
        }

        // 应用法术效果（根据类型）
        private void ApplySpellEffect(Piece target, SpellContext context)
        {
            switch (context.spellEffectType)
            {
                case SpellEffectType.BuffDamage: // 伤害增益
                    target.physical_damage.AddBonus(context.effectValue);
                    break;
                case SpellEffectType.DebuffResist: // 抗性削弱
                    target.physical_resist -= context.effectValue;
                    target.magic_resist -= context.effectValue;
                    break;
                case SpellEffectType.Heal: // 生命恢复
                    target.health = Math.Min(target.health + context.effectValue, target.max_health);
                    break;
            }
        }

        //-----------------------------------------------------------------核心逻辑------------------------------------------------------------//
        // 单回合步进逻辑
        void step()
        {
            //回合初始化
            round_number++;  // 回合计数器递增

            // 重置所有存活棋子的行动点
            foreach (var piece in action_queue.Where(p => p.is_alive))
            {
                piece.setActionPoints(piece.max_action_points);  // 从piece类获取最大值
            }

            //处理行动队列
            int processedCount = 0;  // 已处理棋子计数器
            while (processedCount < action_queue.Count)
            {
                current_piece = action_queue[0];  // 取队列第一个
                action_queue.RemoveAt(0);

                // 跳过死亡/非己方回合单位
                if (!current_piece.is_alive || current_piece.team != (round_number % 2 + 1))
                {
                    action_queue.Add(current_piece);
                    processedCount++;
                    continue;
                }

                // 移动阶段
                if (current_piece.action_points > 0)
                {
                    // 从玩家获取移动目标（需实现getAction）
                    var moveAction = getAction().move_target;
                    // 调用棋盘移动验证
                    bool moveSuccess = board.movePiece(
                        current_piece,
                        moveAction,
                        current_piece.movement  // 使用piece类的movement属性
                    );
                    if (moveSuccess) current_piece.setActionPoints(current_piece.getActionPoints()-1);
                }

                // 攻击阶段
                while (current_piece.action_points > 0)  // 可执行多次攻击
                {
                    var attack_context = getAction().attack_context;
                    executeAttack(attack_context);  // 内部会消耗action_points
                }

                // 法术阶段
                if (current_piece.spell_slots > 0 && current_piece.action_points > 0)
                {
                    var spell_context = getAction().spell_context;
                    executeSpell(spell_context);  // 内部会消耗spell_slots和action_points
                }

                // 将棋子放回队列末尾
                action_queue.Add(current_piece);
                processedCount++;
            }

            // 延时法术处理
            for (int i = delayed_spells.Count - 1; i >= 0; i--)
            {
                var spell = delayed_spells[i];
                spell.spellLifespan--;

                // 触发到期法术
                if (spell.spellLifespan <= 0)
                {
                    // 根据法术类型处理
                    if (spell.isDamageSpell)
                    {
                        spell.target.receiveDamage(spell.damageValue, "magic");
                        if (spell.target.health <= 0) HandleDeathCheck(spell.target);
                    }
                    delayed_spells.RemoveAt(i);
                }
            }


            // 移除死亡单位
            var deadPieces = action_queue.Where(p => !p.is_alive).ToList();
            foreach (var dead in deadPieces)
            {
                board.removePiece(dead);
                action_queue.Remove(dead);
            }

            // 游戏结束检查
            isGameOver = !player1.getPieces().Any(p => p.is_alive) ||
              !player2.getPieces().Any(p => p.is_alive);

            log(0);
        }

        void log(int mode)
        {
            if (mode != 0) return;

            // 回合基础信息
            Console.WriteLine($"\n===== 回合 {round_number} 日志 =====");

            // 行动队列状态
            Console.WriteLine($"\n[行动队列] 剩余单位: {action_queue.Count(p => p.is_alive)}活 / {action_queue.Count(p => !p.is_alive)}亡");

            // 存活单位详细信息
            Console.WriteLine("\n[存活单位]");
            foreach (var piece in action_queue.Where(p => p.is_alive))
            {
                Console.WriteLine($"├─ {piece.GetType().Name} #{piece.GetHashCode() % 1000:000}");
                Console.WriteLine($"│  所属: 玩家{piece.team} 位置: ({piece.position.x},{piece.position.y})");
                Console.WriteLine($"│  生命: {piece.health}/{piece.max_health} 行动点: {piece.action_points}");
                Console.WriteLine($"└─ 法术位: {piece.spell_slots}/{piece.max_spell_slots}");
            }

            // 死亡单位简报
            var newDead = action_queue.Where(p => !p.is_alive && p.deathRound == round_number);
            if (newDead.Any())
            {
                Console.WriteLine("\n[本回合阵亡]");
                foreach (var dead in newDead)
                    Console.WriteLine($"▣ {dead.GetType().Name} #{dead.GetHashCode() % 1000:000} 原属玩家{dead.team}");
            }

            // 游戏状态概要
            Console.WriteLine($"\n[游戏状态] {(isGameOver ? "已结束" : "进行中")}");

        }

        // 游戏主循环
        public void run()
        {
            initialize(); // 初始化游戏
            while (!isGameOver) step(); // 回合制循环
        }
    }
}