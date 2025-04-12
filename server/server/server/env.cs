using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Serialization;


//env类是整个游戏的核心，应该有权读取所有信息，并通过其他类给定的接口修改信息。所有涉及棋子与棋子交互、棋子与棋盘交互的行为都应在env类中进行处理。
namespace server
{
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

        void initialize()
        {
            //执行各类初始化
            //注：对于player类，先调用player的localInit函数进行初始化，并根据Init返回值进行地图信息的初始化（需要进行各种合法性检查，如初始位置是否越过双方边界线）
        }

        actionSet getAction()
        {
            //获取当前棋子的行动，应该通过player类获取一个actionSet
            throw new NotImplementedException();
        }

        // 投掷骰子  
        private int RollDice(int sides)
        {
            Random random = new Random();
            return random.Next(1, sides + 1);
        }

        //-----------------------------------------------------------------攻击逻辑------------------------------------------------------------//
        void executeAttack(AttackContext context)
        {
            if (context.attacker == null || context.target == null || !context.attacker.is_alive || !context.target.is_alive)
                return;

            // 1. 检查行动点
            if (context.attacker.action_points <= 0)
            {
                Console.WriteLine("[Attack] Failed: Not enough action points.");
                return;
            }

            // 2. 检查攻击范围
            if (!IsInAttackRange(context.attacker, context.target))
            {
                Point bestMovePos = CalculateBestMovePosition(context.attacker, context.target);
                if (!board.movePiece(context.attacker, bestMovePos, context.attacker.movement))
                {
                    Console.WriteLine("[Attack] Failed: Out of range and movement failed.");
                    return;
                }
            }

            // 3. 掷骰子命中判定
            int attackRoll = RollDice(20);
            bool isHit = false;
            bool isCritical = false;

            if (attackRoll == 1)
            {
                Console.WriteLine("[Attack] Natural 1 - Critical Miss.");
                isHit = false;
            }
            else if (attackRoll == 20)
            {
                Console.WriteLine("[Attack] Natural 20 - Critical Hit!");
                isHit = true;
                isCritical = true;
            }
            else
            {
                int attackThrow = attackRoll +
                                GetStrengthModifier(context.attacker.strength) +
                                CalculateAdvantageValue(context.attacker, context.target);

                int defenseValue = context.target.physical_resist +
                                GetDexterityModifier(context.target.dexterity);

                isHit = attackThrow > defenseValue;

                Console.WriteLine($"[Attack] Roll: {attackRoll} → Total Attack: {attackThrow}, Defense: {defenseValue}, Hit: {isHit}");
            }

            // 4. 命中后伤害处理
            if (isHit)
            {
                int damage = context.attacker.physical_damage.Roll();
                if (isCritical)
                    damage *= 2;

                Console.WriteLine($"[Attack] Dealing {damage} {(isCritical ? "(Critical) " : "")}damage to target.");

                context.target.receiveDamage(damage, "physical");

                if (context.target.health <= 0)
                {
                    HandleDeathCheck(context.target);
                }
            }

            // 5. 扣除行动点
            context.attacker.action_points--;
        }


        // 辅助函数
        private bool IsInAttackRange(Piece attacker, Piece target)
        {
            // 计算两点之间的距离
            double distance = Math.Sqrt(
                Math.Pow(attacker.position.x - target.position.x, 2) +
                Math.Pow(attacker.position.y - target.position.y, 2)
            );

            return distance <= attacker.attack_range;
        }

        private Point CalculateBestMovePosition(Piece attacker, Piece target)
        {
            // 简化的实现：寻找离目标最近的可移动位置
            // 实际实现应考虑寻路算法和移动力限制
            // 这里返回目标位置作为示例
            return target.position;
        }

        private int CalculateAdvantageValue(Piece attacker, Piece target)
        {
            // 高低差优势: 2*(攻击者高度-受击者高度)
            int heightAdvantage = 2 * (attacker.height - target.height);

            // 环境优势: 3*(攻击者环境值-受击者环境值)
            int attackerEnvValue = CalculateEnvironmentValue(attacker);
            int targetEnvValue = CalculateEnvironmentValue(target);
            int envAdvantage = 3 * (attackerEnvValue - targetEnvValue);

            return heightAdvantage + envAdvantage;
        }

        private int CalculateEnvironmentValue(Piece piece)
        {
            // 遍历延时法术列表，计算环境值
            int envValue = 0;
            foreach (var spell in delayed_spells)
            {
                if (IsAffectedBySpell(piece, spell))
                {
                    // 处在伤害法术范围里为-1，处在buff效果中为1
                    envValue += spell.isBuff ? 1 : -1;
                }
            }
            return envValue;
        }

        private void HandleDeathCheck(Piece target)
        {
            int deathRoll = RollDice(20);

            if (deathRoll == 20)
            {
                // 恢复至1滴血
                target.health = 1;
            }
            else if (deathRoll == 1)
            {
                // 直接死亡
                target.is_alive = false;
                board.removePiece(target);
                action_queue.Remove(target);

                // 检查游戏是否结束
                CheckGameOver();
            }
            else
            {
                // 进入濒死状态
                target.is_dying = true;
            }
        }

        //法术攻击
        void executeSpell(SpellContext context)
        {
            if (context.caster == null || context.caster.action_points <= 0 || context.caster.spell_slots < context.spellCost)
            {
                Console.WriteLine("[Spell] Failed: Not enough resources.");
                return;
            }

            bool spellSuccess = false;

            if (context.isDelaySpell)
            {
                ExecuteDelaySpell(context);
            }
            else if (context.isAreaEffect)
            {
                ExecuteAreaSpell(context);
            }
            else
            {
                ExecuteSingleTargetSpell(context);
            }

            context.caster.action_points--;
            context.caster.spell_slots -= context.spellCost;
        }


        private void ExecuteDelaySpell(SpellContext context)
        {
            // 1. 法术发动检定
            int spellRoll = RollD20();
            bool isSuccess = false;

            // 非锁定类法术需要至少2.5倍法术强属性的投掷值
            if (!context.isLockingSpell)
            {
                int requiredRoll = (int)(2.5 * context.spellPower);
                isSuccess = spellRoll >= requiredRoll;
            }
            else
            {
                // 锁定类法术正常检定
                int attackThrow = spellRoll +
                                GetIntelligenceModifier(context.caster.intelligence) +
                                context.spellPower;

                int defenseValue = context.target.magic_resist;
                isSuccess = attackThrow > defenseValue;
            }

            // 2. 如果成功，加入延时法术列表
            if (isSuccess)
            {
                delayed_spells.Add(context);
                context.spellLifespan = context.baseLifespan;
            }
        }

        private void ExecuteAreaSpell(SpellContext context)
        {
            // 1. 法术发动检定
            int spellRoll = RollDice(20);
            int attackThrow = spellRoll +
                            GetIntelligenceModifier(context.caster.intelligence) +
                            context.spellPower;

            // 2. 获取范围内的所有目标
            List<Piece> targets = GetPiecesInArea(context.targetArea);

            // 3. 对每个目标进行处理
            foreach (var target in targets)
            {
                // 范围法术不分敌我
                int defenseValue = target.magic_resist;
                bool isHit = attackThrow > defenseValue;

                if (isHit)
                {
                    // 应用伤害或效果
                    if (context.isDamageSpell)
                    {
                        int damage = context.spellDamage.Roll();
                        target.receiveDamage(damage, "magic");

                        // 死亡检定
                        if (target.health <= 0)
                        {
                            HandleDeathCheck(target);
                        }
                    }
                    else
                    {
                        // 应用buff/debuff效果
                        ApplySpellEffect(target, context);
                    }
                }
            }
        }

        private void ExecuteSingleTargetSpell(SpellContext context)
        {
            // 1. 检查目标是否在施法范围内
            if (!IsInSpellRange(context.caster, context.target))
            {
                return;
            }

            // 2. 法术发动检定
            int spellRoll = RollD20();
            int attackThrow = spellRoll +
                            GetIntelligenceModifier(context.caster.intelligence) +
                            context.spellPower;

            int defenseValue = context.target.magic_resist;
            bool isHit = attackThrow > defenseValue;

            // 3. 如果命中，应用效果
            if (isHit)
            {
                if (context.isDamageSpell)
                {
                    int damage = context.spellDamage.Roll();
                    context.target.receiveDamage(damage, "magic");

                    // 死亡检定
                    if (context.target.health <= 0)
                    {
                        HandleDeathCheck(context.target);
                    }
                }
                else
                {
                    // 应用buff/debuff效果
                    ApplySpellEffect(context.target, context);
                }
            }
        }

        private void ApplySpellEffect(Piece target, SpellContext context)
        {
            // 根据法术类型应用不同效果
            switch (context.spellEffectType)
            {
                case SpellEffectType.BuffDamage:
                    target.physical_damage.AddBonus(context.effectValue);
                    break;
                case SpellEffectType.DebuffResist:
                    target.physical_resist -= context.effectValue;
                    target.magic_resist -= context.effectValue;
                    break;
                case SpellEffectType.Heal:
                    target.health = Math.Min(target.health + context.effectValue, target.max_health);
                    break;
                    // 其他效果类型...
            }
        }

        private List<Piece> GetPiecesInArea(Area targetArea)
        {
            // 获取区域内的所有棋子
            List<Piece> piecesInArea = new List<Piece>();

            foreach (var piece in action_queue)
            {
                if (piece.is_alive && targetArea.Contains(piece.position))
                {
                    piecesInArea.Add(piece);
                }
            }

            return piecesInArea;
        }

        private bool IsInSpellRange(Piece caster, Piece target)
        {
            // 计算施法范围
            // 这里可以使用与物理攻击相同的距离计算方式
            double distance = Math.Sqrt(
                Math.Pow(caster.position.x - target.position.x, 2) +
                Math.Pow(caster.position.y - target.position.y, 2)
            );

            return distance <= caster.spell_range;
        }

        //-----------------------------------------------------------------------------------------------------------------移动逻辑--------------------------------------------------------------------------------------//

        void executeMove(Piece cur_piece, Point move_target, float movement)
        {
            board.movePiece(cur_piece, move_target, movement);
            //执行移动
        }

        //潜在的其他行为

        //-----------------------------------------------------------------------------------------------------------------主逻辑---------------------------------------------------------------------------------------//
        void step()
        {
            //执行每回合的逻辑
            //包括：执行行为逻辑getAction,executeAttack等，在执行行为后进行行动队列的更新、棋子状态的更新、棋盘状态的更新、终局判定等
            //注：棋盘状态的更新应在每回合结束时进行
        }

        void log(int mode)
        {
            //日志生成
            //应该支持输出到回放文件、输出到控制台两种模式
        }

        public void run()
        {
            initialize();
            while (!isGameOver) step();
            log(0);
        }
    }
}
