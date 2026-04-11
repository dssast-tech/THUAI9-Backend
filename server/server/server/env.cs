using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Linq;
using System.Numerics;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Xml.Serialization;
using static System.Collections.Specialized.BitVector32;

// 环境类：游戏核心控制器，管理所有游戏逻辑和状态
namespace Server
{
    class Env
    {

        public List<Piece> action_queue; // 棋子的行动队列
        public Piece current_piece; // 当前行动的棋子
        public int round_number; // 当前回合数
        public List<SpellContext> delayed_spells; // 延时法术列表
        public Player player1; // 玩家1
        public Player player2; // 玩家2
        public Board board; // 棋盘
        public bool isGameOver; // 游戏是否结束
        public List<Piece> newDeadThisRound; // 记录本回合新死亡的棋子列表
        public List<Piece> lastRoundDeadPieces;
        public LogConverter logdata;

        // 战斗是否已经初始化（行动队列 / 日志 ）
        public bool isBattleInitialized;

        // 最大回合数（实例级），可调整
        public int max_rounds = 100;

        public Env()
        {
            isBattleInitialized = false;
        }



        /// <summary>
        /// 初始化棋盘与玩家对象，不包含棋子配置与战斗初始化。
        /// 棋子会由外部通过 Player.localInit / GameEngine.SetPlayerPieces 完成。
        /// </summary>
        public Task initialize()
        {
            board = new Board();
            string filePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "BoardCase", "case1.txt");
            board.init(filePath);

            player1 = new Player();
            player2 = new Player();
            player1.id = 1;
            player2.id = 2;

            delayed_spells = new List<SpellContext>();
            isGameOver = false;
            round_number = 0;
            newDeadThisRound = new List<Piece>();
            action_queue = new List<Piece>();
            lastRoundDeadPieces = new List<Piece>();
            isBattleInitialized = false;

            return Task.CompletedTask;
        }

        /// <summary>
        /// 在双方棋子已经配置完成后，根据当前棋子列表初始化行动队列、棋盘占据信息以及日志。
        /// </summary>
        public void SetupBattle()
        {
            if (player1.pieces == null || player2.pieces == null)
            {
                throw new InvalidOperationException("玩家棋子尚未配置完成，无法初始化战斗。");
            }

            Dictionary<Piece, int> piecePriority = new Dictionary<Piece, int>();

            foreach (var piece in player1.pieces)
            {
                int priority = RollDice(1, 20) + piece.dexterity;
                piecePriority[piece] = priority;
            }

            foreach (var piece in player2.pieces)
            {
                int priority = RollDice(1, 20) + piece.dexterity;
                piecePriority[piece] = priority;
            }

            action_queue = piecePriority
                .OrderByDescending(pair => pair.Value)
                .Select(pair => pair.Key)
                .ToList();

            for (int i = 0; i < action_queue.Count; i++)
            {
                action_queue[i].id = i;
            }

            board.init_pieces_location(player1.pieces, player2.pieces);

            logdata = new LogConverter();
            logdata.init(action_queue, board);

            isBattleInitialized = true;
        }

        // 投掷骰子  
        private int RollDice(int n, int sides) // n为投掷次数，sides为骰子面数
        {
            Random random = new Random();
            return random.Next(1, sides + 1);
        }
        private int Step_Modified_Func(int num)
        {
            if (num <= 10) num = 1;
            else if (num <= 20) num = 2;
            else if (num <= 30) num = 3;
            else num = 4;
            return num;
        }
        //-----------------------------------------------------------------攻击逻辑------------------------------------------------------------//
        // 执行攻击上下文
        void executeAttack(ref AttackContext context)
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
                //Point bestMovePos = CalculateBestMovePosition(context.attacker, context.target);
                //List<Vector3Serializable> movePath = new List<Vector3Serializable>();
                //if (!board.movePiece(context.attacker, bestMovePos, context.attacker.movement, out movePath))
                //{
                //    Console.WriteLine("[Attack] Failed: Out of range and movement failed.");
                //    return;
                //}
                //logdata.addMove(context.attacker, movePath);

                //删除在攻击时移动的功能，以减少代码复杂性
                Console.WriteLine("[Attack] Failed: Out of range.");
                return;
            }

            // 3. 掷骰子命中判定
            int attackRoll = RollDice(1, 20);
            bool isHit = false;
            bool isCritical = false;



            if (attackRoll == 1)
            {
                Console.WriteLine("[Attack] Natural 1 - Critical Miss.");
                isHit = false;
            }
            else if (attackRoll == 20) // 大成功
            {
                Console.WriteLine("[Attack] Natural 20 - Critical Hit!");
                isHit = true;
                isCritical = true;
            }
            else // 常规攻击计算
            {
                int attackThrow = attackRoll +
                                Step_Modified_Func(context.attacker.strength) +
                                CalculateAdvantageValue(context.attacker, context.target);

                int defenseValue = context.target.physical_resist +
                                Step_Modified_Func(context.target.dexterity);

                isHit = attackThrow > defenseValue;

                Console.WriteLine($"[Attack] Roll: {attackRoll} → Total Attack: {attackThrow}, Defense: {defenseValue}, Hit: {isHit}");
            }

            // 4. 命中后伤害处理
            if (isHit)
            {
                int damage = context.attacker.physical_damage + context.attacker.strength;
                if (isCritical)
                    damage *= 2;

                Console.WriteLine($"[Attack] Dealing {damage} {(isCritical ? "(Critical) " : "")}damage to target.");

                context.target.receiveDamage(damage, "physical");
                context.damageDealt = damage; // 记录实际造成的伤害
                Console.WriteLine($"[Debug] damage:{damage}");

                if (context.target.health <= 0)
                {
                    // Console.Write($"debug");// debug
                    HandleDeathCheck(context.target); // 执行死亡检定
                }
            }

            // 5. 扣除行动点
            var accessor = context.attacker.GetAccessor();
            accessor.ChangeActionPointsBy(-1);
            // context.attacker.action_points--;
        }


        // 辅助函数
        private bool IsInAttackRange(Piece attacker, Piece target)
        {
            double distance = Math.Sqrt(
                Math.Pow(attacker.position.x - target.position.x, 2) +
                Math.Pow(attacker.position.y - target.position.y, 2)
            );

            return distance <= attacker.attack_range;
        }

        //private Point CalculateBestMovePosition(Piece attacker, Piece target)
        //{
        //    // 简化的实现：寻找离目标最近的可移动位置
        //    // 实际实现应考虑寻路算法和移动力限制
        //    // 这里返回目标位置作为示例
        //    return target.position;
        //}

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
                if (spell.targetArea.Contains(piece.position))
                {
                    // 处在伤害法术范围里为-1，处在buff效果中为1
                    if (spell.effectType == SpellEffectType.Buff) envValue += 1;
                    if (spell.effectType == SpellEffectType.Damage) envValue -= 1;
                }
            }
            return envValue;
        }

        private void HandleDeathCheck(Piece target)
        {
            int deathRoll = RollDice(1, 20);
            Console.WriteLine($"[DeathCheck] Roll: {deathRoll}");
            var accessor = target.GetAccessor();
            if (deathRoll == 20)
            {
                // 恢复至1滴血
                accessor.SetHealthTo(1);
                accessor.SetDying(false);
                accessor.SetAlive(true);
                //target.health = 1;
            }
            else // 立即死亡
            {
                // 直接死亡
                accessor.SetAlive(false);

                logdata.addDeath(target);
                board.removePiece(target);
                action_queue.Remove(target);
                newDeadThisRound.Add(target);
                target.deathRound = round_number;
            }
            //else // 濒死状态
            //{
            //    // 进入濒死状态
            //    //target.is_dying = true;
            //    accessor.SetDying(true);
            //    accessor.SetAlive(false);
            //}
        }

        //-----------------------------------------------------------------法术逻辑------------------------------------------------------------//
        // 执行法术上下文
        void executeSpell(SpellContext context)
        {
            //检查是否为延时法术
            if (context.isDelaySpell && !context.delayAdd)
            {
                if (context.caster == null || context.caster.action_points <= 0 || context.caster.spell_slots < context.spellCost)
                {
                    Console.WriteLine("[Spell] Failed: Not enough resources or do not use spell.");
                    return;
                }
                context.delayAdd = true;
                delayed_spells.Add(context);
                // 扣除施法者资源
                var accessorTemp = context.caster.GetAccessor();
                accessorTemp.ChangeActionPointsBy(-1);
                accessorTemp.ChangeSpellSlotsBy(-1);
                Console.WriteLine("[Spell] Delayed spell added.");

                return;

            }
            else if (context.isDelaySpell && context.spellLifespan == 0)
            {
                List<Piece> targets = GetPiecesInArea(context.targetArea);
                context.hitPiecies = GetPiecesInArea(context.targetArea);
                foreach (var target in targets)
                {
                    Console.WriteLine("[Spell] Execute delay spell.");
                    Console.WriteLine("[Spell] Effect applied to multi target.");
                    ApplySpellEffect(target, context);
                    logdata.addSpell(context, board);
                }
                return;
            }

            // 检查施法者是否有足够的资源
            if (context.caster == null || context.caster.action_points <= 0 || context.caster.spell_slots < context.spellCost)
            {
                Console.WriteLine("[Spell] Failed: Not enough resources or do not use spell.");
                return;
            }

            // 检查目标是否在施法范围内

            if (context.spell.isLockingSpell)
            {
                if (!IsInSpellRange(context.target, context.targetArea))
                {
                    Console.WriteLine("[Spell] Target is out of range.");
                    return;
                }
                Console.WriteLine("[Spell] Effect applied to single target.");
                ApplySpellEffect(context.target, context);
                logdata.addSpell(context, board);
            }
            else
            {
                // 获取目标区域内的棋子
                List<Piece> targets = GetPiecesInArea(context.targetArea);
                context.hitPiecies = GetPiecesInArea(context.targetArea);
                foreach (var target in targets)
                {
                    Console.WriteLine("[Spell] Effect applied to multi target.");
                    ApplySpellEffect(target, context);
                    logdata.addSpell(context, board);
                }
            }

            // 扣除施法者资源
            var accessor = context.caster.GetAccessor();
            accessor.ChangeActionPointsBy(-1);
            accessor.ChangeSpellSlotsBy(-1);

            Console.WriteLine("[Spell] Spell successfully cast.");
            return;
        }

        // 辅助函数
        private bool IsInSpellRange(Piece target, Area targetArea)
        {
            double distance = Math.Sqrt(
                Math.Pow(target.position.x - targetArea.x, 2) +
                Math.Pow(target.position.y - targetArea.y, 2)
            );
            return distance <= targetArea.radius;
        }

        private List<Piece> GetPiecesInArea(Area targetArea)
        {
            return action_queue.Where(piece => targetArea.Contains(piece.position)).ToList();
        }

        private void ApplySpellEffect(Piece target, SpellContext context)
        {
            Console.WriteLine("[Spell] Applying effect to target...");
            var accessor = target.GetAccessor();
            switch (context.spell.effectType)
            {
                case SpellEffectType.Damage:
                    accessor.SetHealthTo(Math.Max(target.health - context.spell.baseValue, 0));
                    if (context.target.health <= 0)
                    {
                        // Console.Write($"debug");// debug
                        HandleDeathCheck(target); // 执行死亡检定
                    }
                    break;
                case SpellEffectType.Heal:
                    accessor.SetHealthTo(Math.Max(target.health + context.spell.baseValue, target.max_health));
                    break;
                case SpellEffectType.Buff:
                    accessor.SetPhysicalDamageTo(target.physical_damage + context.spell.baseValue);
                    break;
                case SpellEffectType.Debuff:
                    accessor.SetPhysicResistBy(context.spell.baseValue);
                    accessor.SetMagicResistBy(context.spell.baseValue);
                    break;
                case SpellEffectType.Move:
                    Console.WriteLine("[Spell:Move] Effect applied to single target.");
                    List<Vector3Serializable> movePath = new List<Vector3Serializable>();
                    bool success = board.movePiece(
                    target,
                    new Point(context.targetArea.x, context.targetArea.y),
                    100,
                    out movePath
                    );
                    Console.WriteLine($"[Spell:Move] Move success: {success}");
                    if (success)
                    {
                        target.setActionPoints(current_piece.getActionPoints() - 1);
                        var accessortemp = target.GetAccessor();
                        accessortemp.SetPosition(new Point(context.targetArea.x, context.targetArea.y));
                    }
                    else
                    {
                        Console.WriteLine("[Move] Failed: Out of Range");
                    }

                    break;
            }
        }

        //-----------------------------------------------------------------核心逻辑------------------------------------------------------------//
        /// <summary>
        /// 回合开始：递增回合数、为所有存活棋子重置行动点，并确定当前应行动棋子。
        /// 不执行任何玩家操作，适合作为对外广播/获取状态的时机。
        /// </summary>
        public void BeginTurn()
        {
            if (!isBattleInitialized)
            {
                throw new InvalidOperationException("战斗尚未初始化，请先调用 SetupBattle。");
            }

            if (isGameOver)
            {
                return;
            }

            // 回合计数器递增
            round_number++;

            // 重置所有存活棋子的行动点
            foreach (var piece in action_queue.Where(p => p.is_alive))
            {
                piece.setActionPoints(piece.max_action_points);
                Console.WriteLine($"Piece {piece.id} action points: {piece.action_points}");
            }

            // 当前行动棋子为队列首
            current_piece = action_queue[0];

            // 记录回合开始日志
            logdata.addRound(round_number, action_queue);
            log(0);
        }

        /// <summary>
        /// 执行当前棋子的行动指令集（移动/攻击/施法/延时法术推进），不负责轮转队列与胜负判定。
        /// 必须在 BeginTurn 之后调用。
        /// </summary>
        public void ApplyAction(actionSet action)
        {
            if (!isBattleInitialized)
            {
                throw new InvalidOperationException("战斗尚未初始化，请先调用 SetupBattle。");
            }

            if (isGameOver || current_piece == null)
            {
                return;
            }

            if (current_piece.action_points > 0 && action.move)
            {
                Console.WriteLine("Now begin moving");
                Console.WriteLine($"[Move] movement: {current_piece.movement}"); // 输出当前行动点和攻击状态
                // 从玩家获取移动目标
                var moveAction = action.move_target;
                // 调用棋盘移动验证
                List<Vector3Serializable> movePath = new List<Vector3Serializable>();
                bool moveSuccess = board.movePiece(
                    current_piece,
                    moveAction,
                    current_piece.movement, // 使用piece类的movement属性
                    out movePath
                );
                if (moveSuccess)
                {
                    Console.WriteLine("[Move] Success");
                    current_piece.setActionPoints(current_piece.getActionPoints() - 1);
                    var accessor = current_piece.GetAccessor();
                    accessor.SetPosition(moveAction);
                    logdata.addMove(current_piece, movePath);
                }
                else
                {
                    Console.WriteLine("[Move] Failed: Out of Range");
                }
            }


            Console.WriteLine("Now begin attacking");
            // 攻击阶段
            // 输出current_piece.action_points和action.attack

            Console.WriteLine($"[Attack] Action Points: {current_piece.action_points}, Attack: {action.attack}"); // 输出当前行动点和攻击状态
            if (current_piece.action_points > 0 && action.attack)
            {
                //Console.WriteLine("enter attacking");
                var attack_context = action.attack_context;
                attack_context.damageDealt = 0; // 初始化伤害值
                executeAttack(ref attack_context);  // 内部会消耗action_points
                //输出demage的值
                Console.WriteLine($"[Attack] Damage Dealt: {attack_context.damageDealt}");
                logdata.addAttack(attack_context); // 记录攻击日志
            }

            // test
            //打印current_piece.spell_slots > 0 && current_piece.action_points > 0 && action.spell
            //Console.WriteLine($"[Spell] Spell Slots: {current_piece.spell_slots}, Action Points: {current_piece.action_points}, Spell: {action.spell}");


            // 法术阶段
            if (current_piece.spell_slots > 0 && current_piece.action_points > 0 && action.spell)
            {
                var spell_context = action.spell_context;
                executeSpell(spell_context);  // 内部会消耗spell_slots和action_points
            }



            // 延时法术处理
            for (int i = delayed_spells.Count - 1; i >= 0; i--)
            {
                var spell = delayed_spells[i];
                spell.spellLifespan--;
                delayed_spells[i] = spell; // 重新赋值

                if (spell.spellLifespan == 0)
                {
                    executeSpell(spell);
                    delayed_spells.RemoveAt(i);
                    Console.WriteLine("[Spell] Delayed spell triggered and removed.");
                }
                else if (spell.spellLifespan < 0)
                {
                    delayed_spells.RemoveAt(i);
                    Console.WriteLine("[Spell] Delayed spell expired and removed.");
                }
            }
            // 延时法术处理后打印所有延时法术信息
            if (delayed_spells.Count > 0)
            {
                Console.WriteLine("[Spell] 当前延时法术列表：");
                foreach (var spell in delayed_spells)
                {
                    Console.WriteLine($"  - {spell.spell.name} 剩余周期: {spell.spellLifespan}");
                }
            }
            else
            {
                Console.WriteLine("[Spell] 当前无延时法术。");
            }
        }

        /// <summary>
        /// 回合结束：轮转行动队列、执行胜负与回合上限判定、写入回合结束日志。
        /// 必须在 ApplyAction 之后调用。
        /// </summary>
        public void EndTurn()
        {
            if (!isBattleInitialized)
            {
                throw new InvalidOperationException("战斗尚未初始化，请先调用 SetupBattle。");
            }

            if (isGameOver || current_piece == null)
            {
                return;
            }

            // 将当前棋子移到队列末尾
            action_queue.RemoveAt(0);
            action_queue.Add(current_piece);

            // 游戏结束检查
            bool player1Alive = player1.pieces.Any(p => p.is_alive);
            bool player2Alive = player2.pieces.Any(p => p.is_alive);
            isGameOver = !player1Alive || !player2Alive;

            // 常规胜负判定
            string winner = null;
            if (isGameOver)
            {
                if (player1Alive && !player2Alive)
                {
                    winner = "玩家1";
                }
                else if (player2Alive && !player1Alive)
                {
                    winner = "玩家2";
                }
                else if (!player1Alive && !player2Alive)
                {
                    winner = "平局";
                }
            }

            logdata.finishRound(round_number, action_queue, player1.pieces.Count, player2.pieces.Count, isGameOver);

            // 最大回合数上限判定：若达到上限且未结束，则根据双方总血量判断胜负/平局并终止游戏
            if (!isGameOver && round_number >= max_rounds)
            {
                int team1Health = player1.pieces.Where(p => p.is_alive).Sum(p => p.health);
                int team2Health = player2.pieces.Where(p => p.is_alive).Sum(p => p.health);

                Console.WriteLine($"[RoundCap] 达到最大回合数 {max_rounds}。双方总血量：P1={team1Health}, P2={team2Health}");
                if (team1Health > team2Health)
                {
                    Console.WriteLine("[RoundCap] 按总血量判定：玩家1胜利");
                    winner = "玩家1";
                }
                else if (team2Health > team1Health)
                {
                    Console.WriteLine("[RoundCap] 按总血量判定：玩家2胜利");
                    winner = "玩家2";
                }
                else
                {
                    Console.WriteLine("[RoundCap] 按总血量判定：平局");
                    winner = "平局";
                }
                isGameOver = true;
            }
        }

        void log(int mode)
        {
            if (mode != 0) return;

            // 回合基础信息
            Console.WriteLine($"\n===== 回合 {round_number} 日志 =====");

            Console.WriteLine($"\n[当前行动棋子id]: {current_piece.id}");
            // 行动队列状态
            Console.WriteLine($"\n[行动队列] 剩余单位: {action_queue.Count(p => p.is_alive)}存活 / {action_queue.Count(p => !p.is_alive)}阵亡");

            Console.WriteLine("\n[地图]:\n");
            VisualizeArray(board.grid);

            // 存活单位详细信息
            Console.WriteLine("\n[存活单位]");
            foreach (var piece in action_queue.Where(p => p.is_alive))
            {
                Console.WriteLine($"├─ {piece.GetType().Name} #{piece.id}");
                Console.WriteLine($"│  所属: 玩家{piece.team} 位置: ({piece.position.x},{piece.position.y})");
                Console.WriteLine($"│  生命: {piece.health}/{piece.max_health} 行动点: {piece.action_points}");
                Console.WriteLine($"└─ 法术位: {piece.spell_slots}/{piece.max_spell_slots}");
            }

            // 死亡单位简报
            if (lastRoundDeadPieces.Any())
            {
                Console.WriteLine("\n[上一回合阵亡]");
                foreach (var piece in lastRoundDeadPieces)
                {
                    Console.WriteLine($"棋子ID: {piece.queue_index}, 死亡回合: {round_number - 1}");
                }
            }

            //清空本回合死亡棋子列表，以便下回合使用
            lastRoundDeadPieces = new List<Piece>(newDeadThisRound);
            newDeadThisRound.Clear();

            // 游戏状态概要
            Console.WriteLine($"\n[游戏状态] {(isGameOver ? "已结束" : "进行中")}");

        }


        public void VisualizeArray(Cell[,] array)
        {
            // 遍历二维数组的每一行
            for (int i = 0; i < array.GetLength(0); i++)
            {
                // 遍历当前行的每一列
                for (int j = 0; j < array.GetLength(1); j++)
                {
                    if (array[i, j].state == 2)
                    {
                        if (array[i, j].playerId == 1)
                        {
                            Console.ForegroundColor = ConsoleColor.Red; // 设置颜色为红色
                        }
                        else if (array[i, j].playerId == 2)
                        {
                            Console.ForegroundColor = ConsoleColor.Blue; // 设置颜色为蓝色
                        }
                    }
                    else
                    {
                        Console.ResetColor(); // 恢复默认颜色
                    }
                    // 输出每个数字，固定占位 2 格，用空格隔开
                    if (array[i, j].state == 2)
                        Console.Write($"{array[i, j].pieceId,2} ");
                    else
                        Console.Write($"{array[i, j].state,2} ");
                }

                // 换行
                Console.WriteLine();
            }
        }

    }
}
