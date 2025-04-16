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
        List<Piece> action_queue; // 棋子的行动队列
        Piece current_piece; // 当前行动的棋子
        int round_number; // 当前回合数
        List<SpellContext> delayed_spells; // 延时法术列表
        Player player1; // 玩家1
        Player player2; // 玩家2
        Board board; // 棋盘
        bool isGameOver; // 游戏是否结束
        List<Piece> newDeadThisRound; // 记录本回合新死亡的棋子列表
        List<Piece> lastRoundDeadPieces;
        GameData logdata;

        void initialize()
        {
            //执行各类初始化
            //注：对于player类，先调用player的localInit函数进行初始化，并根据Init返回值进行地图信息的初始化（需要进行各种合法性检查，如初始位置是否越过双方边界线）
            board = new Board();
            string filePath = filePath.Combine(AppDomain.CurrentDomain.BaseDirectory, "BoardCase","case1.txt");
            board.init(filePath);
            
            player1 = new Player();
            player2 = new Player();
            player1.id = 1;
            player2.id = 2;
            player1.localInit(board,player1.id);
            player2.localInit(board,player2.id);
            
            board.init_pieces_location(player1.pieces, player2.pieces);
            // 初始化棋盘
            action_queue = new List<Piece>();
            delayed_spells = new List<SpellContext>();
            
            isGameOver = false;
            round_number = 0;
            newDeadThisRound = new List<Piece>();

            // 初始化行动列表
            action_queue = new List<Piece>();
            
            Dictionary<Piece, int> piecePriority = new Dictionary<Piece, int>();
            
            // 为每个棋子计算优先级
            foreach (var piece in player1.pieces)
            {
                int priority = RollDice(1, 20) + piece.intelligence;
                piecePriority[piece] = priority;
            }
            
            foreach (var piece in player2.pieces)
            {
                int priority = RollDice(1, 20) + piece.dexterity;
                piecePriority[piece] = priority;
            }
            
            // 按优先级从大到小排序并添加到行动队列
            action_queue = piecePriority
                .OrderByDescending(pair => pair.Value)
                .Select(pair => pair.Key)
                .ToList();

            for (int i = 0; i < action_queue.Count(); i++)
            {
                action_queue[i].id = i;
            }

            // 初始化棋盘
            board = new Board();
            string filePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "BoardCase", "case1.txt");
            board.init(filePath);
        }

        // 获取当前棋子的行动指令集
        actionSet getAction()
        {
            // 通过当前玩家对象获取行动决策（需具体实现）
            actionSet action = new actionSet();
            while (true)
            {
                Console.WriteLine("请输入目标移动位置（格式：x y）：");
                string input = Console.ReadLine();

                try
                {
                    // 检查输入是否为两个用空格隔开的整数
                    string[] inputs = input.Split(' ');
                    if (inputs.Length != 2)
                    {
                        throw new Exception("输入格式错误，应为两个用空格隔开的整数。");
                    }

                    int x = int.Parse(inputs[0]);
                    int y = int.Parse(inputs[1]);

                    // 执行业务逻辑
                    // 例如：设置棋子的目标位置
                    action.move_target = new Point(x, y);

                    // 退出循环
                    break;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"输入错误：{ex.Message}");
                }
            }
            while (true)
            {
                Console.WriteLine("请输入要攻击的棋子编号（若不攻击，输入-1)");
                string input = Console.ReadLine();
                try
                {
                    int x = int.Parse(input);
                    if (x == -1)
                    {
                        action.attack = false;
                        break;
                    }
                    else
                    {
                        action.attack = true;
                        action.attack_context.attacker = current_piece;
                        action.attack_context.target = action_queue[x];
                        action.attack_context.attackPosition = current_piece.position;
                        // 其他攻击相关逻辑
                        break;
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"输入错误：{ex.Message}");
                }
            }
            if (action.attack == true)
            {
                while (true)
                {
                    Console.WriteLine("请输入要施加的法术id（若不攻击，输入None)");
                    string input = Console.ReadLine();
                    try
                    {
                        int x = int.Parse(input);
                        if (x == -1)
                        {
                            action.spell = false;
                            break;
                        }
                        else
                        {
                            action.spell = true;
                            action.spell_context.caster = current_piece;
                            action.spell_context.target = action_queue[x];
                            // 其他法术相关逻辑
                            break;
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"输入错误：{ex.Message}");
                    }
                }
            }
            return action;
        }

        // 投掷骰子  
        private int RollDice(int n, int sides) // n为投掷次数，sides为骰子面数
        {
            Random random = new Random();
            return random.Next(1, sides + 1);
        }
        private int Step_Modified_Func(int num){
            if(num<=10)num=1;
            else if(num<=20)num=2;
            else if(num<=30)num=3;
            else num=4;
            return num;
        }
        //-----------------------------------------------------------------攻击逻辑------------------------------------------------------------//
        // 执行攻击上下文
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
                int damage = context.attacker.physical_damage;
                if (isCritical)
                    damage *= 2;

                Console.WriteLine($"[Attack] Dealing {damage} {(isCritical ? "(Critical) " : "")}damage to target.");

                context.target.receiveDamage(damage, "physical");

                if (context.target.health <= 0)
                {
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
                if (spell.targetArea.Contains(piece.position))
                {
                    // 处在伤害法术范围里为-1，处在buff效果中为1
                    if (spell.effectType == SpellEffectType.BuffDamage) envValue += 1;
                    if (spell.effectType == SpellEffectType.Damage) envValue -= 1;
                }
            }
            return envValue;
        }

        private void HandleDeathCheck(Piece target)
        {
            int deathRoll = RollDice(1,20);
            var accessor=target.GetAccessor();
            if (deathRoll == 20)
            {
                // 恢复至1滴血
                accessor.SetHealthTo(1);
                accessor.SetDying(false);
                accessor.SetAlive(true);
                //target.health = 1;
            }
            else if (deathRoll == 1) // 立即死亡
            {
                // 直接死亡
                accessor.SetAlive(false);

                board.removePiece(target);
                action_queue.Remove(target);
                newDeadThisRound.Add(target);
                target.deathRound = round_number; 
            }
            else // 濒死状态
            {
                // 进入濒死状态
                //target.is_dying = true;
                accessor.SetDying(true);
                accessor.SetAlive(true);
            }
        }

        //-----------------------------------------------------------------法术逻辑------------------------------------------------------------//
        // 执行法术上下文
        void executeSpell(SpellContext context)
        {
            if (context.caster == null || context.caster.action_points <= 0 || context.caster.spell_slots < context.spellCost)
            {
                Console.WriteLine("[Spell] Failed: Not enough resources.");
                return;
            }

            bool spellSuccess = false;

            if (context.isDelaySpell && context.baseLifespan==context.spellLifespan)
            {
                ExecuteDelaySpell(context); //若是第一次,进行初始化，下一轮才开始处理效果
                return;
            }

            if (context.isAreaEffect)
            {
                ExecuteAreaSpell(context);
            }
            else
            {
                ExecuteSingleTargetSpell(context);
            }
            var accessor=context.caster.GetAccessor();
            accessor.ChangeActionPointsBy(-1);
        }

        // 应用法术效果（根据类型）

        private void ExecuteDelaySpell(SpellContext context)
        {
            // 1. 法术发动检定
            int spellRoll = RollDice(1,20);
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
                                Step_Modified_Func(context.caster.intelligence) +
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
                int spellRoll = RollDice(1,20);
                int attackThrow = spellRoll +
                             Step_Modified_Func(context.caster.intelligence) +
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
                            int damage = context.damageValue;
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
            int spellRoll = RollDice(1,20);
            int attackThrow = spellRoll +
                            Step_Modified_Func(context.caster.intelligence) +
                            context.spellPower;

            int defenseValue = context.target.magic_resist;
            bool isHit = attackThrow > defenseValue;
        }


        private void ApplySpellEffect(Piece target, SpellContext context)
        {
            var accessor = target.GetAccessor();
            // 根据法术类型应用不同效果
            switch (context.effectType)
            {
                case SpellEffectType.BuffDamage:
                    //target.physical_damage.AddBonus(context.effectValue);
                    accessor.SetPhysicalDamageTo(target.physical_damage + context.effectValue);
                    break;
                case SpellEffectType.DebuffResist:
                    accessor.SetPhysicResistBy(context.effectValue);
                    //target.physical_resist -= context.effectValue;
                    accessor.SetMagicResistBy(context.effectValue);
                    //target.magic_resist -= context.effectValue;
                    break;
                case SpellEffectType.Heal:
                    accessor.SetHealthTo(Math.Min(target.health + context.effectValue, target.max_health));
                    break;

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

        //-----------------------------------------------------------------核心逻辑------------------------------------------------------------//
        // 单回合步进逻辑
        void step()
        {
            //回合初始化
            round_number++;  // 回合计数器递增

            // 重置所有存活棋子的行动点
            foreach (var piece in action_queue.Where(p => p.is_alive))
            {
                piece.setActionPoints(piece.max_action_points);  

            }

            //处理行动队列
            int processedCount = 0;  // 已处理棋子计数器
            current_piece = action_queue[0];  // 取队列第一个
            action_queue.RemoveAt(0);
            // 将棋子放回队列末尾
            action_queue.Add(current_piece);
            processedCount++;

            log(0);
            //// 跳过死亡/非己方回合单位
            //if (!current_piece.is_alive || current_piece.team != (round_number % 2 + 1))
            //{
            //    action_queue.Add(current_piece);
            //    processedCount++;
            //    continue;
            //}

            var action = getAction();

                // 移动阶段
            if (current_piece.action_points > 0)
            {
                // 从玩家获取移动目标
                var moveAction = action.move_target;
                // 调用棋盘移动验证
                bool moveSuccess = board.movePiece(
                    current_piece,
                    moveAction,
                    current_piece.movement  // 使用piece类的movement属性
                );
                if (moveSuccess)
                {
                    current_piece.setActionPoints(current_piece.getActionPoints() - 1);
                    var accessor = current_piece.GetAccessor();
                    accessor.SetPosition(moveAction);
                }
            }

            // 攻击阶段
            if (current_piece.action_points > 0)  // 可执行多次攻击
            {
                var attack_context = action.attack_context;
                executeAttack(attack_context);  // 内部会消耗action_points
            }

            // 法术阶段
            if (current_piece.spell_slots > 0 && current_piece.action_points > 0)
            {
                var spell_context = action.spell_context;
                executeSpell(spell_context);  // 内部会消耗spell_slots和action_points
            }


            // 延时法术处理
            for (int i = delayed_spells.Count - 1; i >= 0; i--)
            {
                var spell = delayed_spells[i];
                spell.spellLifespan--;

                // 触发到期法术
                if (spell.spellLifespan >= 0)
                {
                    // 根据法术类型处理
                    //if (spell.isDamageSpell)
                    //{
                    //    spell.target.receiveDamage(spell.damageValue, "magic");
                    //    if (spell.target.health <= 0) HandleDeathCheck(spell.target);
                    //}
                    //delayed_spells.RemoveAt(i);
                    executeSpell(spell);
                }
                else
                {
                    delayed_spells.RemoveAt(i);
                }
            }
            //！移除操作已由攻击组完成
            // 移除死亡单位
            //var deadPieces = action_queue.Where(p => !p.is_alive).ToList();
            //foreach (var dead in deadPieces)
            //{
            //    board.removePiece(dead);
            //    action_queue.Remove(dead);
            //}

            // 游戏结束检查
            isGameOver = !player1.pieces.Any(p => p.is_alive) ||
              !player2.pieces.Any(p => p.is_alive);

        }

        void log(int mode)
        {
            if (mode != 0) return;

            // 回合基础信息
            Console.WriteLine($"\n===== 回合 {round_number} 日志 =====");

            Console.WriteLine($"\n[当前行动棋子id]: {current_piece.id}");
            // 行动队列状态
            Console.WriteLine($"\n[行动队列] 剩余单位: {action_queue.Count(p => p.is_alive)}存活 / {action_queue.Count(p => !p.is_alive)}阵亡");

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
            //！！！！该模块应该无法正常工作，运行到log时p已经被移除
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

        // 游戏主循环
        public void run()
        {
            initialize(); // 初始化游戏
            while (!isGameOver) step(); // 回合制循环
        }
    }
}