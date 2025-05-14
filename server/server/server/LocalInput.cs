using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Server
{
    // 输入方法接口 - 定义所有输入方法的通用接口
    interface IInputMethod
    {
        // 处理初始化输入
        InitPolicyMessage HandleInitInput(InitGameMessage initMessage);

        // 处理游戏中的行动输入
        actionSet HandleActionInput(Env _env);


        // 输入方法的名称
        string Name { get; }
    }
    
    // 控制台输入方法
    class ConsoleInputMethod : IInputMethod
    {
        public string Name => "控制台输入";

        public InitPolicyMessage HandleInitInput(InitGameMessage initMessage)
        {
            Console.WriteLine($"为玩家 {initMessage.id} 初始化棋子");
            
            var initPolicy = new InitPolicyMessage
            {
                pieceArgs = new List<pieceArg>()
            };
            
            // 为每个棋子创建初始属性
            for (int i = 0; i < initMessage.pieceCnt; i++)
            {
                var pieceArg = new pieceArg();
                
                // 属性分配
                bool inputCorrect = false;
                do
                {
                    Console.WriteLine($"为棋子 {i + 1} 输入属性分配，格式为：力量 敏捷 智力 总和不超过30");
                    string input = Console.ReadLine();
                    if (!string.IsNullOrEmpty(input))
                    {
                        string[] inputs = input.Split(' ');
                        if (inputs.Length != 3)
                        {
                            Console.WriteLine("输入的整数不是3个");
                            continue;
                        }
                        
                        if (!int.TryParse(inputs[0], out int strength) || 
                            !int.TryParse(inputs[1], out int dexterity) || 
                            !int.TryParse(inputs[2], out int intelligence))
                        {
                            Console.WriteLine("输入的不是整数");
                            continue;
                        }
                        
                        if (strength < 0 || dexterity < 0 || intelligence < 0)
                        {
                            Console.WriteLine("输入的整数不能为负数！");
                            continue;
                        }
                        
                        if (strength + dexterity + intelligence > 30)
                        {
                            Console.WriteLine("输入的整数之和多于30！");
                            continue;
                        }
                        
                        pieceArg.strength = strength;
                        pieceArg.dexterity = dexterity;
                        pieceArg.intelligence = intelligence;
                        inputCorrect = true;
                    }
                } while (!inputCorrect);
                
                // 显示武器防具表
                Console.WriteLine("武器防具表展示如下：");
                Console.WriteLine("武器:         物伤值      法伤值     范围");
                Console.WriteLine("1~长剑       18           0         5");
                Console.WriteLine("2~短剑       24           0         3");
                Console.WriteLine("3~弓         16           0         9");
                Console.WriteLine("4~法杖        0           22        12");
                Console.WriteLine("防具:         物豁免值      法豁免值   行动力影响");
                Console.WriteLine("1~轻甲         8            10        +3");
                Console.WriteLine("2~中甲         15           13        0");
                Console.WriteLine("3~重甲         23           17        -3");
                
                // 装备选择
                inputCorrect = false;
                do
                {
                    Console.WriteLine("现在输入武器和防具，格式为：武器类型(1-4) 防具类型(1-3)");
                    string input = Console.ReadLine();
                    if (!string.IsNullOrEmpty(input))
                    {
                        string[] inputs = input.Split(' ');
                        if (inputs.Length != 2)
                        {
                            Console.WriteLine("输入的整数不是2个");
                            continue;
                        }
                        
                        if (!int.TryParse(inputs[0], out int weapon) || 
                            !int.TryParse(inputs[1], out int armor))
                        {
                            Console.WriteLine("输入的不是整数");
                            continue;
                        }
                        
                        if (weapon < 1 || weapon > 4 || armor < 1 || armor > 3)
                        {
                            Console.WriteLine("输入的整数不在范围里！");
                            continue;
                        }
                        
                        if (weapon == 4 && armor != 1)
                        {
                            Console.WriteLine("法杖只能配轻甲！");
                            continue;
                        }
                        
                        pieceArg.equip = new Point(weapon, armor);
                        inputCorrect = true;
                    }
                } while (!inputCorrect);
                
                // 位置选择
                inputCorrect = false;
                do
                {
                    int rows = initMessage.board.height;
                    int cols = initMessage.board.width;
                    int boarder = initMessage.board.boarder;
                    
                    Console.WriteLine("现在输入棋子初始坐标，格式为：x y");
                    string input = Console.ReadLine();
                    if (!string.IsNullOrEmpty(input))
                    {
                        string[] inputs = input.Split(' ');
                        if (inputs.Length != 2)
                        {
                            Console.WriteLine("输入的整数不是2个");
                            continue;
                        }
                        
                        if (!int.TryParse(inputs[0], out int x) || 
                            !int.TryParse(inputs[1], out int y))
                        {
                            Console.WriteLine("输入的不是整数");
                            continue;
                        }
                        
                        if (x < 0 || x >= cols || y < 0 || y >= rows)
                        {
                            Console.WriteLine("输入的整数超过范围！");
                            continue;
                        }
                        
                        if (initMessage.board.grid[x, y].state != 1)
                        {
                            Console.WriteLine("输入的坐标状态为不可占据!");
                            continue;
                        }
                        
                        // 检查是否与已添加的棋子位置冲突
                        bool isValid = true;
                        foreach (var arg in initPolicy.pieceArgs)
                        {
                            if (arg.pos.x == x && arg.pos.y == y)
                            {
                                Console.WriteLine("输入的坐标与已有棋子重合！");
                                isValid = false;
                                break;
                            }
                        }
                        
                        if (!isValid)
                            continue;
                        
                        pieceArg.pos = new Point(x, y);
                        inputCorrect = true;
                    }
                } while (!inputCorrect);
                
                // 添加棋子参数到策略中
                initPolicy.pieceArgs.Add(pieceArg);
            }
            
            return initPolicy;
        }

        public actionSet HandleActionInput(Env _env)
        {
            var actionSet = new actionSet();
            
            // 移动部分
            while (true)
            {
                Console.WriteLine("请输入目标移动位置（格式：x y, 若不移动，输入-1 -1）：");
                string input = Console.ReadLine();
                
                try
                {
                    string[] inputs = input.Split(' ');
                    if (inputs.Length != 2)
                    {
                        throw new Exception("输入格式错误，应为两个用空格隔开的整数。");
                    }
                    
                    int x = int.Parse(inputs[0]);
                    int y = int.Parse(inputs[1]);
                    
                    if (x == -1 || y == -1)
                    {
                        actionSet.move = false;
                        break;
                    }
                    
                    actionSet.move = true;
                    actionSet.move_target = new Point(x, y);
                    break;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"输入错误：{ex.Message}");
                }
            }
            
            // 攻击部分
            while (true)
            {
                Console.WriteLine("请输入要攻击的棋子id编号（若不攻击，输入-1)");
                string input = Console.ReadLine();
                try
                {
                    int x = int.Parse(input);
                    if (x == -1)
                    {
                        actionSet.attack = false;
                        break;
                    }
                    else
                    {
                        actionSet.attack = true;
                        actionSet.attack_context = new AttackContext();
                        actionSet.attack_context.attacker = _env.current_piece;
                        Piece foundPiece = _env.action_queue.FirstOrDefault(p => p.id == x);
                        if (foundPiece == null)
                            throw new Exception("未找到指定的棋子。");
                        actionSet.attack_context.target = foundPiece;
                        actionSet.attack_context.attackPosition = _env.current_piece.position;
                        break;
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"输入错误：{ex.Message}");
                }
            }
            
            // 法术部分
            Console.WriteLine("是否要施放法术？(1/-1)");
            string spellChoice = Console.ReadLine();
            if (spellChoice != null && spellChoice.Trim() == "1")
            {
                while (true)
                {
                    Console.WriteLine("请输入要施加的法术id（若不施法，输入-1)");
                    string input = Console.ReadLine();
                    
                    int spellId = int.Parse(input);
                    if (spellId == -1)
                    {
                        actionSet.spell = false;
                        break;
                    }
                    
                    Spell? selectedSpell = SpellFactory.GetSpellById(spellId);
                    if (!selectedSpell.HasValue)
                    {
                        Console.WriteLine("未找到指定的法术，请重新输入。");
                        continue;
                    }
                    var spell = selectedSpell.Value;
                    actionSet.spell = true;
                    
                    Console.WriteLine($"已选择法术: {spell.name} - {spell.description}");
                    
                    Console.WriteLine("请输入要施加的法术中心坐标（格式：x y）");
                    string[] inputs = Console.ReadLine().Split(' ');
                    if (inputs.Length != 2)
                    {
                        Console.WriteLine("输入格式错误，应为两个用空格隔开的整数。");
                        continue;
                    }
                    
                    int x, y;
                    if (!int.TryParse(inputs[0], out x) || !int.TryParse(inputs[1], out y))
                    {
                        Console.WriteLine("坐标输入格式错误，请重新输入。");
                        continue;
                    }
                    
                    if (Math.Sqrt(Math.Pow(_env.current_piece.position.x - x, 2) +
                                  Math.Pow(_env.current_piece.position.y - y, 2)) > 100.0)
                    {
                        Console.WriteLine("施法范围超出限制，请重新输入。");
                        continue;
                    }
                    
                    Console.WriteLine("请输入要攻击的棋子id编号");
                    string targetInput = Console.ReadLine();
                    int targetId;
                    if (!int.TryParse(targetInput, out targetId))
                    {
                        Console.WriteLine("棋子id输入格式错误，请重新输入。");
                        continue;
                    }
                    Piece foundPiece = _env.action_queue.FirstOrDefault(p => p.id == targetId);
                    if (foundPiece == null)
                    {
                        Console.WriteLine("未找到指定的棋子，请重新输入。");
                        continue;
                    }
                    
                    actionSet.spell_context = new SpellContext();
                    actionSet.spell_context.target = foundPiece;
                    actionSet.spell_context.targetArea = new Area
                    {
                        x = x,
                        y = y,
                        radius = spell.areaRadius
                    };
                    
                    actionSet.spell = true;
                    actionSet.spell_context.isDelaySpell = spell.isDelaySpell;
                    actionSet.spell_context.spellLifespan = spell.baseLifespan;
                    actionSet.spell_context.delayAdd = false;
                    actionSet.spell_context.caster = _env.current_piece;
                    actionSet.spell_context.spell = spell;
                    
                    Console.WriteLine($"法术 {spell.name} 已准备施放，目标区域中心: ({x}, {y})");
                    break;
                }
            }
            else
            {
                actionSet.spell = false;
            }
            
            return actionSet;
        }
    }
    
    // 函数式本地输入方法
    class FunctionLocalInputMethod : IInputMethod
    {
        private readonly Func<InitGameMessage, InitPolicyMessage> _initHandler;
        private readonly Func<Env, actionSet> _actionHandler;
        
        public string Name => "函数式本地输入";
        
        public FunctionLocalInputMethod(
            Func<InitGameMessage, InitPolicyMessage> initHandler,
            Func<Env, actionSet> actionHandler)
        {
            _initHandler = initHandler;
            _actionHandler = actionHandler;
        }
        
        public InitPolicyMessage HandleInitInput(InitGameMessage initMessage)
        {
            return _initHandler(initMessage);
        }
        
        public actionSet HandleActionInput(Env _env)
        {
            return _actionHandler(_env);
        }
    }
    
    // 远程输入方法 - 通过GRPC实现
    class RemoteInputMethod : IInputMethod
    {
        private readonly Env _env;
        
        public string Name => "远程连接输入";
        
        public RemoteInputMethod(Env env)
        {
            _env = env;
        }
        
        public InitPolicyMessage HandleInitInput(InitGameMessage initMessage)
        {
            // 远程输入方法在初始化时不执行任何操作，因为它依赖于GRPC客户端的异步响应
            // 在当前实现中，initWaiter负责等待客户端初始化
            throw new NotImplementedException("远程输入方法使用initWaiter来处理初始化");
        }
        
        public actionSet HandleActionInput(Env _env)
        {
            // 远程输入方法在请求行动时不执行任何操作，因为它依赖于GRPC客户端的异步响应
            // 在当前实现中，actionWaiter负责等待客户端行动
            throw new NotImplementedException("远程输入方法使用actionWaiter来处理行动输入");
        }
    }
    
    // 输入方法管理器
    class InputMethodManager
    {
        private readonly Dictionary<int, IInputMethod> _playerInputMethods = new Dictionary<int, IInputMethod>();
        private readonly Env _env;
        
        public InputMethodManager(Env env)
        {
            _env = env;
            
            // 默认为所有玩家设置控制台输入方法
            SetInputMethod(1, new ConsoleInputMethod());
            SetInputMethod(2, new ConsoleInputMethod());
        }
        
        public void SetInputMethod(int playerId, IInputMethod inputMethod)
        {
            _playerInputMethods[playerId] = inputMethod;
            Console.WriteLine($"玩家 {playerId} 的输入方式已设置为: {inputMethod.Name}");
        }
        
        public IInputMethod GetInputMethod(int playerId)
        {
            if (_playerInputMethods.TryGetValue(playerId, out var method))
            {
                return method;
            }
            
            // 默认返回控制台输入
            var defaultMethod = new ConsoleInputMethod();
            _playerInputMethods[playerId] = defaultMethod;
            return defaultMethod;
        }
        
        // 为玩家设置函数式本地输入方法
        public void SetFunctionLocalInputMethod(
            int playerId, 
            Func<InitGameMessage, InitPolicyMessage> initHandler,
            Func<Env, actionSet> actionHandler)
        {
            var inputMethod = new FunctionLocalInputMethod(initHandler, actionHandler);
            SetInputMethod(playerId, inputMethod);
        }
        
        // 为玩家设置控制台输入方法
        public void SetConsoleInputMethod(int playerId)
        {
            SetInputMethod(playerId, new ConsoleInputMethod());
        }
        
        // 为玩家设置远程输入方法
        public void SetRemoteInputMethod(int playerId)
        {
            SetInputMethod(playerId, new RemoteInputMethod(_env));
        }
        
        // 处理当前玩家的初始化输入
        public InitPolicyMessage HandleInitInput(int playerId, InitGameMessage initMessage)
        {
            var inputMethod = GetInputMethod(playerId);
            
            if (inputMethod is RemoteInputMethod)
            {
                // 远程输入方法不直接处理初始化，由initWaiter处理
                throw new InvalidOperationException("远程输入方法使用initWaiter来处理初始化");
            }
            
            return inputMethod.HandleInitInput(initMessage);
        }
        
        // 处理当前玩家的行动输入
        public actionSet HandleActionInput(int playerId)
        {
            var inputMethod = GetInputMethod(playerId);
            
            if (inputMethod is RemoteInputMethod)
            {
                // 远程输入方法不直接处理行动输入，由actionWaiter处理
                throw new InvalidOperationException("远程输入方法使用actionWaiter来处理行动输入");
            }
            
            return inputMethod.HandleActionInput(_env);
        }
        
        // 检查玩家是否使用远程输入方法
        public bool IsRemoteInput(int playerId)
        {
            return GetInputMethod(playerId) is RemoteInputMethod;
        }
    }
    
    // =========================================================================
    // 具体策略实现示例
    // =========================================================================
    
    /// <summary>
    /// 策略工厂类 - 提供不同的策略函数
    /// </summary>
    static class StrategyFactory
    {
        /// <summary>
        /// 获取攻击型初始化策略
        /// </summary>
        public static Func<InitGameMessage, InitPolicyMessage> GetAggressiveInitStrategy()
        {
            return (initMessage) => 
            {
                var policy = new InitPolicyMessage 
                { 
                    pieceArgs = new List<pieceArg>() 
                };
                
                // 攻击型配置：高力量，中敏捷，低智力
                for (int i = 0; i < initMessage.pieceCnt; i++)
                {
                    var arg = new pieceArg
                    {
                        strength = 20,      // 高力量
                        dexterity = 8,      // 中敏捷
                        intelligence = 2,    // 低智力
                        equip = new Point(2, 3), // 短剑+重甲 (高伤害+高防御)
                    };
                    
                    // 设置位置 - 偏向前线位置
                    if (initMessage.id == 1) // 第一个玩家
                    {
                        arg.pos = new Point(2 + i * 2, 5);
                    }
                    else // 第二个玩家
                    {
                        arg.pos = new Point(initMessage.board.width - 3 - i * 2, initMessage.board.height - 6);
                    }
                    
                    policy.pieceArgs.Add(arg);
                }
                
                return policy;
            };
        }
        
        /// <summary>
        /// 获取防御型初始化策略
        /// </summary>
        public static Func<InitGameMessage, InitPolicyMessage> GetDefensiveInitStrategy()
        {
            return (initMessage) => 
            {
                var policy = new InitPolicyMessage 
                { 
                    pieceArgs = new List<pieceArg>() 
                };
                
                // 防御型配置：中力量，高敏捷，中智力
                for (int i = 0; i < initMessage.pieceCnt; i++)
                {
                    var arg = new pieceArg
                    {
                        strength = 5,      // 低力量
                        dexterity = 15,    // 高敏捷
                        intelligence = 10,  // 中智力
                        equip = new Point(3, 1), // 弓+轻甲 (远程+机动性)
                    };
                    
                    // 设置位置 - 偏向后方位置
                    if (initMessage.id == 1) // 第一个玩家
                    {
                        arg.pos = new Point(3 + i * 3, 3);
                    }
                    else // 第二个玩家
                    {
                        arg.pos = new Point(initMessage.board.width - 4 - i * 3, initMessage.board.height - 4);
                    }
                    
                    policy.pieceArgs.Add(arg);
                }
                
                return policy;
            };
        }
        
        /// <summary>
        /// 获取法师型初始化策略
        /// </summary>
        public static Func<InitGameMessage, InitPolicyMessage> GetMageInitStrategy()
        {
            return (initMessage) => 
            {
                var policy = new InitPolicyMessage 
                { 
                    pieceArgs = new List<pieceArg>() 
                };
                
                // 法师型配置：低力量，中敏捷，高智力
                for (int i = 0; i < initMessage.pieceCnt; i++)
                {
                    var arg = new pieceArg
                    {
                        strength = 5,       // 低力量
                        dexterity = 5,      // 低敏捷
                        intelligence = 20,   // 高智力
                        equip = new Point(4, 1), // 法杖+轻甲 (必须搭配)
                    };
                    
                    // 设置位置 - 中间位置
                    if (initMessage.id == 1) // 第一个玩家
                    {
                        arg.pos = new Point(4 + i * 3, 4);
                    }
                    else // 第二个玩家
                    {
                        arg.pos = new Point(initMessage.board.width - 5 - i * 3, initMessage.board.height - 5);
                    }
                    
                    policy.pieceArgs.Add(arg);
                }
                
                return policy;
            };
        }
        
        /// <summary>
        /// 获取攻击型行动策略 - 主动接近并攻击敌人
        /// </summary>
        public static Func<Env, actionSet> GetAggressiveActionStrategy()
        {
            return (env) => 
            {
                var action = new actionSet();
                var currentPiece = env.current_piece;
                
                // 寻找最近的敌人
                Piece targetEnemy = null;
                double nearestDistance = double.MaxValue;
                
                foreach (var piece in env.action_queue)
                {
                    if (piece.team != currentPiece.team && piece.is_alive)
                    {
                        double distance = CalculateDistance(currentPiece.position, piece.position);
                        if (distance < nearestDistance)
                        {
                            nearestDistance = distance;
                            targetEnemy = piece;
                        }
                    }
                }
                
                // 没有敌人，不执行任何动作
                if (targetEnemy == null)
                {
                    action.move = false;
                    action.attack = false;
                    action.spell = false;
                    return action;
                }
                
                // 移动决策 - 向目标敌人移动
                action.move = true;
                
                // 计算向敌人方向移动的方向
                int dx = Math.Sign(targetEnemy.position.x - currentPiece.position.x);
                int dy = Math.Sign(targetEnemy.position.y - currentPiece.position.y);
                
                // 移动到目标位置
                action.move_target = new Point(
                    currentPiece.position.x + dx,
                    currentPiece.position.y + dy
                );
                
                // 如果已经在攻击范围内，则攻击
                if (nearestDistance <= currentPiece.attack_range)
                {
                    action.attack = true;
                    action.attack_context = new AttackContext
                    {
                        attacker = currentPiece,
                        target = targetEnemy,
                        attackPosition = currentPiece.position
                    };
                }
                else
                {
                    action.attack = false;
                }
                
                // 暂不使用法术
                action.spell = false;
                
                return action;
            };
        }
        
        /// <summary>
        /// 获取防御型行动策略 - 保持距离，使用远程攻击
        /// </summary>
        public static Func<Env, actionSet> GetDefensiveActionStrategy()
        {
            return (env) => 
            {
                var action = new actionSet();
                var currentPiece = env.current_piece;
                
                // 寻找最近的敌人
                Piece targetEnemy = null;
                double nearestDistance = double.MaxValue;
                
                foreach (var piece in env.action_queue)
                {
                    if (piece.team != currentPiece.team && piece.is_alive)
                    {
                        double distance = CalculateDistance(currentPiece.position, piece.position);
                        if (distance < nearestDistance)
                        {
                            nearestDistance = distance;
                            targetEnemy = piece;
                        }
                    }
                }
                
                // 没有敌人，不执行任何动作
                if (targetEnemy == null)
                {
                    action.move = false;
                    action.attack = false;
                    action.spell = false;
                    return action;
                }
                
                // 移动决策 - 保持在攻击范围内，但不要太近
                action.move = true;
                
                // 理想距离是攻击范围的70%
                double idealDistance = currentPiece.attack_range * 0.7;
                
                if (nearestDistance < idealDistance - 2) // 太近了，远离
                {
                    // 远离敌人
                    int dx = Math.Sign(currentPiece.position.x - targetEnemy.position.x);
                    int dy = Math.Sign(currentPiece.position.y - targetEnemy.position.y);
                    
                    action.move_target = new Point(
                        currentPiece.position.x + dx,
                        currentPiece.position.y + dy
                    );
                }
                else if (nearestDistance > idealDistance + 2) // 太远了，靠近
                {
                    // 靠近敌人
                    int dx = Math.Sign(targetEnemy.position.x - currentPiece.position.x);
                    int dy = Math.Sign(targetEnemy.position.y - currentPiece.position.y);
                    
                    action.move_target = new Point(
                        currentPiece.position.x + dx,
                        currentPiece.position.y + dy
                    );
                }
                else // 在理想范围内
                {
                    action.move = false;
                }
                
                // 如果在攻击范围内，则攻击
                if (nearestDistance <= currentPiece.attack_range)
                {
                    action.attack = true;
                    action.attack_context = new AttackContext
                    {
                        attacker = currentPiece,
                        target = targetEnemy,
                        attackPosition = currentPiece.position
                    };
                }
                else
                {
                    action.attack = false;
                }
                
                // 暂不使用法术
                action.spell = false;
                
                return action;
            };
        }
        
        /// <summary>
        /// 获取法师型行动策略 - 保持距离，使用法术
        /// </summary>
        public static Func<Env, actionSet> GetMageActionStrategy()
        {
            return (env) => 
            {
                var action = new actionSet();
                var currentPiece = env.current_piece;
                
                // 寻找最近的敌人
                Piece targetEnemy = null;
                double nearestDistance = double.MaxValue;
                
                foreach (var piece in env.action_queue)
                {
                    if (piece.team != currentPiece.team && piece.is_alive)
                    {
                        double distance = CalculateDistance(currentPiece.position, piece.position);
                        if (distance < nearestDistance)
                        {
                            nearestDistance = distance;
                            targetEnemy = piece;
                        }
                    }
                }
                
                // 寻找生命值最低的友方
                Piece lowestHealthAlly = null;
                int lowestHealth = int.MaxValue;
                
                foreach (var piece in env.action_queue)
                {
                    if (piece.team == currentPiece.team && piece.is_alive && piece != currentPiece)
                    {
                        if (piece.health < lowestHealth)
                        {
                            lowestHealth = piece.health;
                            lowestHealthAlly = piece;
                        }
                    }
                }
                
                // 没有敌人，不执行任何动作
                if (targetEnemy == null)
                {
                    action.move = false;
                    action.attack = false;
                    action.spell = false;
                    return action;
                }
                
                // 移动决策 - 尽量保持距离
                double safeDistance = 8; // 安全距离，避免近战攻击
                
                if (nearestDistance < safeDistance)
                {
                    action.move = true;
                    
                    // 远离敌人
                    int dx = Math.Sign(currentPiece.position.x - targetEnemy.position.x);
                    int dy = Math.Sign(currentPiece.position.y - targetEnemy.position.y);
                    
                    action.move_target = new Point(
                        currentPiece.position.x + dx,
                        currentPiece.position.y + dy
                    );
                }
                else
                {
                    action.move = false;
                }
                
                // 如果有法术位，根据情况选择合适的法术
                if (currentPiece.spell_slots > 0)
                {
                    // 获取所有可用法术
                    var allSpells = SpellFactory.GetAllSpells();
                    Spell? selectedSpell = null;
                    
                    // 如果自己或友军生命值低于30%，优先考虑治疗
                    if ((lowestHealthAlly != null && 
                         (double)lowestHealthAlly.health / lowestHealthAlly.max_health < 0.3) ||
                        (double)currentPiece.health / currentPiece.max_health < 0.3)
                    {
                        // 尝试获取治疗法术
                        selectedSpell = allSpells.FirstOrDefault(s => 
                            s.effectType == SpellEffectType.Heal && 
                            s.id == 2); // 假设ID为2的是治疗法术
                    }
                    
                    // 如果敌人靠得太近并且没有选择治疗法术，考虑使用瞬间移动
                    if (selectedSpell == null && nearestDistance < 3)
                    {
                        selectedSpell = allSpells.FirstOrDefault(s => 
                            s.effectType == SpellEffectType.Move && 
                            s.id == 5); // 假设ID为5的是瞬间移动
                    }
                    
                    // 如果有多个敌人聚在一起，优先使用范围伤害法术
                    if (selectedSpell == null)
                    {
                        int enemiesInRange = 0;
                        foreach (var piece in env.action_queue)
                        {
                            if (piece.team != currentPiece.team && piece.is_alive)
                            {
                                double distanceFromTarget = CalculateDistance(targetEnemy.position, piece.position);
                                if (distanceFromTarget <= 5) // 火球半径是5
                                {
                                    enemiesInRange++;
                                }
                            }
                        }
                        
                        if (enemiesInRange >= 2)
                        {
                            selectedSpell = allSpells.FirstOrDefault(s => 
                                s.effectType == SpellEffectType.Damage && 
                                s.isAreaEffect && 
                                s.id == 1); // 假设ID为1的是火球
                        }
                    }
                    
                    // 如果还没选择法术，默认使用单体伤害法术
                    if (selectedSpell == null && nearestDistance <= 12) // 法杖范围是12
                    {
                        selectedSpell = allSpells.FirstOrDefault(s => 
                            s.effectType == SpellEffectType.Damage && 
                            !s.isAreaEffect && 
                            s.id == 3); // 假设ID为3的是箭击
                    }
                    
                    // 如果选择了法术并且在施法范围内，则施放法术
                    if (selectedSpell.HasValue && nearestDistance <= selectedSpell.Value.range)
                    {
                        action.spell = true;
                        Spell spell = selectedSpell.Value;
                        
                        // 根据法术类型配置法术上下文
                        action.spell_context = new SpellContext
                        {
                            caster = currentPiece,
                            spell = spell,
                            isDelaySpell = spell.isDelaySpell,
                            spellLifespan = spell.baseLifespan,
                            delayAdd = false
                        };
                        
                        if (spell.effectType == SpellEffectType.Heal)
                        {
                            // 治疗法术目标选择
                            Piece healTarget = (lowestHealthAlly != null && 
                                               (double)lowestHealthAlly.health / lowestHealthAlly.max_health < 0.3) 
                                               ? lowestHealthAlly : currentPiece;
                                               
                            action.spell_context.target = healTarget;
                            action.spell_context.targetArea = new Area
                            {
                                x = healTarget.position.x,
                                y = healTarget.position.y,
                                radius = spell.areaRadius
                            };
                        }
                        else if (spell.effectType == SpellEffectType.Move)
                        {
                            // 瞬间移动法术
                            // 计算一个远离敌人的安全位置
                            int dx = Math.Sign(currentPiece.position.x - targetEnemy.position.x) * 3;
                            int dy = Math.Sign(currentPiece.position.y - targetEnemy.position.y) * 3;
                            
                            action.spell_context.target = currentPiece; // 移动法术目标是自己
                            action.spell_context.targetArea = new Area
                            {
                                x = Math.Max(0, Math.Min(env.board.width - 1, currentPiece.position.x + dx)),
                                y = Math.Max(0, Math.Min(env.board.height - 1, currentPiece.position.y + dy)),
                                radius = 0
                            };
                        }
                        else
                        {
                            // 伤害法术目标选择
                            action.spell_context.target = targetEnemy;
                            action.spell_context.targetArea = new Area
                            {
                                x = targetEnemy.position.x,
                                y = targetEnemy.position.y,
                                radius = spell.areaRadius
                            };
                        }
                    }
                    else
                    {
                        action.spell = false;
                    }
                }
                else
                {
                    action.spell = false;
                }
                
                // 如果在攻击范围内且没使用法术，则使用普通攻击
                if (!action.spell && nearestDistance <= currentPiece.attack_range)
                {
                    action.attack = true;
                    action.attack_context = new AttackContext
                    {
                        attacker = currentPiece,
                        target = targetEnemy,
                        attackPosition = currentPiece.position
                    };
                }
                else
                {
                    action.attack = false;
                }
                
                return action;
            };
        }
        
        /// <summary>
        /// 随机选择一个初始化策略
        /// </summary>
        public static Func<InitGameMessage, InitPolicyMessage> GetRandomInitStrategy()
        {
            var random = new Random();
            int strategyType = random.Next(3);
            
            switch(strategyType)
            {
                case 0: return GetAggressiveInitStrategy();
                case 1: return GetDefensiveInitStrategy();
                case 2: return GetMageInitStrategy();
                default: return GetAggressiveInitStrategy();
            }
        }
        
        /// <summary>
        /// 随机选择一个行动策略
        /// </summary>
        public static Func<Env, actionSet> GetRandomActionStrategy()
        {
            var random = new Random();
            int strategyType = random.Next(3);
            
            switch(strategyType)
            {
                case 0: return GetAggressiveActionStrategy();
                case 1: return GetDefensiveActionStrategy();
                case 2: return GetMageActionStrategy();
                default: return GetAggressiveActionStrategy();
            }
        }
        
        // 辅助方法：计算两点之间的距离
        private static double CalculateDistance(Point p1, Point p2)
        {
            return Math.Sqrt(Math.Pow(p1.x - p2.x, 2) + Math.Pow(p1.y - p2.y, 2));
        }
    }
    
    
}
