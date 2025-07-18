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
        public int mode;// 0 for local, 1 for http
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
        // public ServerCommunicator communicator;

        public InitWaiter connectWaiter;
        public InitWaiter initWaiter;
        public ActionWaiter actionWaiter;
        public int Idcnt = 0; 

        // 添加输入方法管理器
        public InputMethodManager inputMethodManager;

        public bool action_received;
        public int input_allowed; //0for forbidden; 1 for player1; 2 for player 2

        private async Task BroadcastGameState()
        {
            if (mode == 1 && GameServiceImpl.Instance != null)
            {
                await GameServiceImpl.Instance.BroadcastToAllClients();
            }
        }

        public Env()
        {
            // communicator = new ServerCommunicator(
            //     "address1",
            //     "address2"
            //     );
            mode = 0;
            connectWaiter = new InitWaiter(2, TimeSpan.FromSeconds(10),22);
            initWaiter = new InitWaiter(2, TimeSpan.FromSeconds(10),11);
            actionWaiter = new ActionWaiter();
            
            // 初始化输入方法管理器
            inputMethodManager = new InputMethodManager(this);
        }

        public async Task initialize()
        {
            //执行各类初始化
            //注：对于player类，先调用player的localInit函数进行初始化，并根据Init返回值进行地图信息的初始化（需要进行各种合法性检查，如初始位置是否越过双方边界线）
            
            // 默认设置双方为控制台输入方式
            // inputMethodManager.SetConsoleInputMethod(1);
            // inputMethodManager.SetConsoleInputMethod(2);
            
            // 示例：如何设置其他输入方式
            // 1. 设置玩家1为远程输入方式
            inputMethodManager.SetRemoteInputMethod(1);
            inputMethodManager.SetRemoteInputMethod(2);
            
            // 2. 设置玩家2为本地函数输入，使用攻击型策略
            // inputMethodManager.SetFunctionLocalInputMethod(2, 
            //     StrategyFactory.GetAggressiveInitStrategy(), 
            //     StrategyFactory.GetAggressiveActionStrategy());

            // 3. 设置玩家1为本地函数输入，使用防御型策略
            // inputMethodManager.SetFunctionLocalInputMethod(1,
            //     StrategyFactory.GetDefensiveInitStrategy(),
            //     StrategyFactory.GetDefensiveActionStrategy());

            // 4. 设置玩家2为本地函数输入，使用法师型策略
            // inputMethodManager.SetFunctionLocalInputMethod(2,
            //     StrategyFactory.GetMageInitStrategy(),
            //     StrategyFactory.GetMageActionStrategy());

            // 5. 设置玩家1为本地函数输入，使用随机策略
            // inputMethodManager.SetFunctionLocalInputMethod(1,
            //     StrategyFactory.GetRandomInitStrategy(),
            //     StrategyFactory.GetRandomActionStrategy());

            board = new Board();
            string filePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "BoardCase", "case1.txt");
            board.init(filePath);

            player1 = new Player();
            player2 = new Player();
            player1.id = 1;
            player2.id = 2;

            // 如果有任何玩家使用远程输入，设置模式为远程模式
            if (inputMethodManager.IsRemoteInput(1) || inputMethodManager.IsRemoteInput(2))
            {
                mode = 1;
            }

            if (mode == 0)
            {
                // 本地模式 - 使用本地输入方法
                // 初始化player1
                if (!inputMethodManager.IsRemoteInput(1))
                {
                    // 准备InitGameMessage
                    var initMessage = new InitGameMessage
                    {
                        pieceCnt = Player.PIECECNT,
                        id = 1,
                        board = board
                    };
                    
                    // 使用本地输入方法处理初始化
                    var initPolicy = inputMethodManager.HandleInitInput(1, initMessage);
                    player1.localInit(initPolicy, board);
                }
                
                // 初始化player2
                if (!inputMethodManager.IsRemoteInput(2))
                {
                    // 准备InitGameMessage
                    var initMessage = new InitGameMessage
                    {
                        pieceCnt = Player.PIECECNT,
                        id = 2,
                        board = board
                    };
                    
                    // 使用本地输入方法处理初始化
                    var initPolicy = inputMethodManager.HandleInitInput(2, initMessage);
                    player2.localInit(initPolicy, board);
                }
            }
            else
            {
                try
                {
                    Console.WriteLine($"Waiting for 2 clients to initialize...");

                    // ⏳ 阻塞在这里，直到所有client都初始化完成，或超时
                    await initWaiter.WaitForAllClientsAsync();

                    Console.WriteLine("All clients initialized, game starting...");
                    // 远程模式下不需要额外操作，因为远程输入是通过gRPC通道自动处理的
                }
                catch (TimeoutException)
                {
                    Console.WriteLine("Game starting despite timeout...");
                    // 如果超时，可以选择自动开始游戏
                }
            }


            // 以下是原有初始化代码，无需修改
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

            board.init_pieces_location(player1.pieces, player2.pieces);

            logdata = new LogConverter();
            logdata.init(action_queue, board);
            lastRoundDeadPieces = new List<Piece>();
        }
        // 获取当前棋子的行动指令集
        actionSet getAction(int mode = 0)
        {
            // 确定当前玩家ID
            int currentPlayerId = current_piece.team;
            
            // 根据模式决定如何处理输入
            if (mode == 1 || inputMethodManager.IsRemoteInput(currentPlayerId))
            {
                // 远程模式下，使用actionWaiter等待远程输入
                // 这里通常由GRPC处理器处理，等待客户端响应
                throw new NotImplementedException("此函数不会在远程模式下直接调用，Step方法中会处理远程输入");
                }
                else
                {
                // 使用本地输入方法获取行动
                return inputMethodManager.HandleActionInput(currentPlayerId);
            }
        }

        actionSet getAction(actionSet inputAction)
        {
            throw new NotImplementedException();
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
                int damage = context.attacker.physical_damage;
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
        // 单回合步进逻辑
        public async Task step()
        {

            //***ForDebug***//
            //手动结束游戏
            // Console.WriteLine("输入exit结束游戏：");
            // string input = Console.ReadLine();
            // if (input == "exit")
            // {
            //     isGameOver = true;
            //     return;
            // }

            //**************//

            //回合初始化
            round_number++;  // 回合计数器递增
            action_received = false;
            input_allowed = 0;

            // 重置所有存活棋子的行动点
            foreach (var piece in action_queue.Where(p => p.is_alive))
            {
                piece.setActionPoints(piece.max_action_points);
            }

            //处理行动队列
            int processedCount = 0;  // 已处理棋子计数器
            current_piece = action_queue[0];  // 取队列第一个
            int current_player = current_piece.team;

            logdata.addRound(round_number, action_queue);
            log(0);
            
            // 在回合开始时广播游戏状态
            Console.WriteLine("Broadcasting game state...");
            await BroadcastGameState();
            Console.WriteLine("Broadcasting game state done");

            // 获取行动
            actionSet action;
            
            // 根据当前玩家的输入方法决定如何获取行动
            if (inputMethodManager.IsRemoteInput(current_player))
            {
                // 使用远程输入方法（通过actionWaiter）
                action = Converter.FromProto(await actionWaiter.WaitForPlayerActionAsync(current_player, TimeSpan.FromSeconds(2)), this);
            }
            else
            {
                // 使用本地输入方法
                action = inputMethodManager.HandleActionInput(current_player);
            }

            // 更新行动队列
            action_queue.RemoveAt(0);
            action_queue.Add(current_piece);
            processedCount++;

            if (current_piece.action_points > 0 && action.move)
            {
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
            //！移除操作已由攻击组完成
            // 移除死亡单位
            //var deadPieces = action_queue.Where(p => !p.is_alive).ToList();
            //foreach (var dead in deadPieces)
            //{
            //    board.removePiece(dead);
            //   action_queue.Remove(dead);
            //}


            // 游戏结束检查
            isGameOver = !player1.pieces.Any(p => p.is_alive) ||
         
            !player2.pieces.Any(p => p.is_alive);
            logdata.finishRound(round_number, action_queue, player1.pieces.Count, player2.pieces.Count, isGameOver);
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

        // 游戏主循环
        public async Task run()
        {
         
            
            await initialize(); // 初始化游戏
            Console.WriteLine("游戏初始化完成，开始游戏！");
            VisualizeArray(board.grid);

            await Task.Delay(1000);
            // 游戏主循环
            while (!isGameOver) 
            {
                await step();
            }
            
            logdata.save();
        }
        

    }
}
