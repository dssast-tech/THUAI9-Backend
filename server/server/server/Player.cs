
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

//client和server的交互应通过player类进行，所有函数均应该能够与通信类交互（待定）


namespace Server
{
    class Player
    {
        public const int PIECECNT = 1; //此处进行了一次修改
        public int id;
        public List<Piece> pieces; //持有的棋子
        public int feature_total=30;
        public int piece_num=0;
        void SetWeapon(int weapon, Piece node)
        {
            // 设置武器
            // weapon: 1~长剑 2~短剑 3~弓 4~法杖
            /* 武器:         物伤值      法伤值     范围
                    1~长剑       18           0         5
                    2~短剑       24           0         3
                    3~弓         16           0         9
                    4~法杖        0           22        12
                */
            var accessor=node.GetAccessor();
            switch(weapon){
                case 1:
                    accessor.SetPhysicalDamageTo(18);
                    accessor.SetMagicDamageTo(0);
                    accessor.SetRangeTo(5);
                    break;
                case 2:
                    accessor.SetPhysicalDamageTo(24);
                    accessor.SetMagicDamageTo(0);
                    accessor.SetRangeTo(3);
                    break;
                case 3:
                    accessor.SetPhysicalDamageTo(16);
                    accessor.SetMagicDamageTo(0);
                    accessor.SetRangeTo(9);
                    break;
                case 4:
                    accessor.SetPhysicalDamageTo(0);
                    accessor.SetMagicDamageTo(22);
                    accessor.SetRangeTo(12);
                    break;
                default:
                    throw new ArgumentException("wrong weapon type!");
                    break;
            }
        }
        
        void SetArmor(int armor, Piece node)
        {
            // 设置装备
            /* 防具:         物豁免值      法豁免值   行动力影响movement
                1~轻甲         8            10        +3
                2~中甲         15           13        0
                3~重甲         23           17        -3
            */
            var accessor=node.GetAccessor();
            switch(armor){
                case 1:
                    accessor.SetPhysicalResistTo(8);
                    accessor.SetMagicResistTo(10);
                    accessor.SetMaxMovementBy(3);
                    break;
                case 2:
                    accessor.SetPhysicalResistTo(15);
                    accessor.SetMagicResistTo(13);
                    break;
                case 3:
                    accessor.SetPhysicalDamageTo(23);
                    accessor.SetMagicDamageTo(17);
                    accessor.SetRangeTo(-3);
                    break;
                default:
                    throw new ArgumentException("wrong armor type!");
                    break;
            }
        }
      
        public void localInit(Board board,int id)
        {
            //所有不涉及地图信息、对方信息的初始化在此进行
            //如力量、敏捷、智力分配，棋子武器、防具分配
            //env环境会调用此函数，利用返回值初始化设计地图交互的其他信息（如棋子位置等）
            pieces= new List<Piece>();

            for(int i=0;i<PIECECNT;i++){
                Console.WriteLine($"现在为棋手 {this.id} 的第 {i + 1} 个棋子初始化");
                pieces.Add(new Piece());
                //没有初始化piece所在的高度 后面记得写
                var accessor=pieces[i].GetAccessor();
                accessor.SetTeamTo(id);
              
                List<int> feature = initInput(board,id);
                piece_num++;
                int strength = feature[0];int dexterity = feature[1];int intelligence = feature[2];
                accessor.SetStrengthTo(strength);accessor.SetDexterityTo(dexterity);accessor.SetIntelligenceTo(intelligence);
                int weapon = feature[3];int armor = feature[4];

                accessor.SetMaxHealthTo(30+strength*2);
                accessor.SetHealthTo(pieces[i].max_health);

                accessor.SetMaxActionPoints();
                accessor.SetActionPointsTo(pieces[i].max_action_points);

                accessor.SetMaxSpellSlots();
                accessor.SetSpellSlotsTo(pieces[i].max_spell_slots);

                accessor.SetMaxMovementTo(dexterity+(float)0.5*strength+10);
                accessor.SetMovementTo(pieces[i].max_movement);

                SetWeapon(weapon,pieces[i]);
                SetArmor(armor,pieces[i]);
                
                Point t=new Point();t.x=feature[5];t.y=feature[6];
                accessor.SetPosition(t);
            
            }
            
        }

        public void localInit(InitPolicyMessage initMessage, Board board)
        {
            // 防御性编程 - 空值校验
            if (initMessage == null)
                throw new ArgumentNullException(nameof(initMessage), "初始化策略消息不能为空");

            if (initMessage.pieceArgs == null)
                throw new ArgumentException("棋子参数列表未初始化", nameof(initMessage.pieceArgs));

            // 策略完整性校验
            if (initMessage.pieceArgs.Count < PIECECNT)
                throw new ArgumentException($"需要{PIECECNT}组初始化参数，当前收到{initMessage.pieceArgs.Count}组");

            pieces = new List<Piece>();

            for (int i = 0; i < PIECECNT; i++)
            {
                var arg = initMessage.pieceArgs[i];

                // 单棋子参数空值检查
                if (arg == null)
                    throw new ArgumentException($"第{i + 1}个棋子参数为空", nameof(initMessage.pieceArgs));

                // 属性校验层
                ValidateAttributes(arg, i);

                // 装备校验层
                ValidateEquipment(arg.equip, i);

                // 位置校验层
                ValidatePosition(arg.pos, i, board);

                // ---- 初始化逻辑 ----
                Console.WriteLine($"通过策略消息初始化棋手 {id} 的第 {i + 1} 个棋子");
                var piece = new Piece();
                pieces.Add(piece);
                var accessor = piece.GetAccessor();

                // 基础属性设置
                accessor.SetTeamTo(id);
                accessor.SetStrengthTo(arg.strength);
                accessor.SetDexterityTo(arg.dexterity);
                accessor.SetIntelligenceTo(arg.intelligence);

                // 派生属性计算
                accessor.SetMaxHealthTo(30 + arg.strength * 2);
                accessor.SetHealthTo(piece.max_health);
                accessor.SetMaxMovementTo(arg.dexterity + (float)(0.5 * arg.strength) + 10);

                // 装备系统初始化
                SetWeapon(arg.equip.x, piece);
                SetArmor(arg.equip.y, piece);

                // 位置初始化（已通过校验）
                accessor.SetPosition(arg.pos);

                piece_num++;
            }
        }

        private void ValidateAttributes(pieceArg arg, int index)
        {
            const int MAX_FEATURE_TOTAL = 30;
            var errorPrefix = $"第{index + 1}个棋子属性错误：";

            // 基础属性范围
            if (arg.strength < 0 || arg.dexterity < 0 || arg.intelligence < 0)
                throw new ArgumentException(errorPrefix + "属性值不能为负数");

            // 策略平衡性规则
            if (arg.strength + arg.dexterity + arg.intelligence > MAX_FEATURE_TOTAL)
                throw new ArgumentException(errorPrefix + $"属性总和超过{MAX_FEATURE_TOTAL}限制");
        }

        private void ValidateEquipment(Point equip, int index)
        {
            var errorPrefix = $"第{index + 1}个棋子装备错误：";

            // 武器类型验证
            if (equip.x < 1 || equip.x > 4)
                throw new ArgumentException(errorPrefix + $"无效武器类型{equip.x} (允许值1-4)");

            // 防具类型验证
            if (equip.y < 1 || equip.y > 3)
                throw new ArgumentException(errorPrefix + $"无效防具类型{equip.y} (允许值1-3)");

            // 特殊装备组合规则
            if (equip.x == 4 && equip.y != 1)
                throw new ArgumentException(errorPrefix + "法杖必须搭配轻甲");
        }

        private void ValidatePosition(Point pos, int index, Board board)
        {
            var errorPrefix = $"第{index + 1}个棋子位置错误：";

            // 边界检查
            if (pos.x < 0 || pos.x >= board.width ||
                pos.y < 0 || pos.y >= board.height)
                throw new ArgumentException(errorPrefix + $"坐标({pos.x},{pos.y})超出棋盘范围");

            // 地形状态验证
            var gridState = board.grid[pos.x, pos.y].state;
            if (gridState != 1)
                throw new ArgumentException(errorPrefix + $"目标位置状态不可用(当前状态:{gridState})");

            // 位置冲突检测
            if (pieces.Any(p => p.position.Equals(pos)))
                throw new ArgumentException(errorPrefix + "位置已被其他棋子占据");
        }



        public actionSet getAction(Piece currentPiece)
        {
            //控制台或AI逻辑
            
            throw new NotImplementedException();
        }


        List<int> initInput(Board board,int id)
        {
                // 接收控制台输入，将信息解析为一个initializationSet
                List<int> initializationSet = new List<int>();
                try
                {
                    bool inputcorrect = false;
                    do
                    {
                        Console.WriteLine("现在输入棋子属性分配，格式为：力量 敏捷 智力 总和不超过30");
                        string input = Console.ReadLine();
                        if (!string.IsNullOrEmpty(input))
                        {
                            string[] inputs = input.Split(' ');
                            int[] nums = new int[inputs.Length];
                            for (int i = 0; i < inputs.Length; i++) nums[i] = int.Parse(inputs[i]);
                            if (nums.Length != 3)
                            {
                                Console.WriteLine("输入的整数不是3个");
                                continue;
                            }
                            if (nums[0] < 0 || nums[1] < 0 || nums[2] < 0)
                            {
                                Console.WriteLine("输入的整数不能为负数！");
                                continue;
                            }
                            if (nums[0] + nums[1] + nums[2] > 30)
                            {
                                Console.WriteLine("输入的整数之和多于30！");
                                continue;
                            }
                            for (int i = 0; i < nums.Length; i++) initializationSet.Add(nums[i]);
                            inputcorrect = true;
                        }
                    } while (inputcorrect == false);


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

                    inputcorrect = false;
                    do
                    {
                        Console.WriteLine("现在输入武器和防具，格式为：武器类型(1-4) 防具类型(1-3)");
                        string input = Console.ReadLine();
                        if (!string.IsNullOrEmpty(input))
                        {
                            string[] inputs = input.Split(' ');
                            int[] nums = new int[inputs.Length];
                            for (int i = 0; i < inputs.Length; i++) nums[i] = int.Parse(inputs[i]);
                            if (nums.Length != 2)
                            {
                                Console.WriteLine("输入的整数不是3个");
                                continue;
                            }
                            if (nums[0] < 1 || nums[1] < 1 || nums[0] > 4 || nums[1] > 3)
                            {
                                Console.WriteLine("输入的整数不在范围里！");
                                continue;
                            }
                            if (nums[0] == 4 && nums[1] != 1)
                            {
                                Console.WriteLine("法杖只能配轻甲！");
                                continue;
                            }
                            for (int i = 0; i < nums.Length; i++) initializationSet.Add(nums[i]);
                            inputcorrect = true;
                        }
                    } while (inputcorrect == false);

                    inputcorrect = false;
                    do
                    {

                        int rows = board.height; int cols = board.width;
                        int boarder = board.boarder;
                        //TODO给用户显示地图信息
                        Console.WriteLine("现在输入棋子初始坐标，格式为：x y");
                        string input = Console.ReadLine();
                        if (!string.IsNullOrEmpty(input))
                        {
                            string[] inputs = input.Split(' ');
                            int[] nums = new int[inputs.Length];
                            for (int i = 0; i < inputs.Length; i++) nums[i] = int.Parse(inputs[i]);
                            if (nums.Length != 2)
                            {
                                Console.WriteLine("输入的整数不是2个");
                                continue;
                            }

                            if (nums[0] < 0 || nums[0] > cols - 1 || nums[1] > rows - 1 || nums[1] < 0)
                            {
                                Console.WriteLine("输入的整数超过范围！");
                                continue;
                            }
                            if (board.grid[nums[0], nums[1]].state != 1)
                            {
                                Console.WriteLine("输入的坐标状态为不可占据!");
                                continue;
                            }
                            bool is_vaild = true;
                            for (int i = 0; i < piece_num; i++)
                            {
                                if (nums[0] == pieces[i].position.x && nums[1] == pieces[i].position.y)
                                {
                                    Console.WriteLine("输入的坐标与已有棋子重合！");
                                    is_vaild = false;
                                }
                            }
                            if (!is_vaild) continue;
                            for (int i = 0; i < nums.Length; i++) initializationSet.Add(nums[i]);
                            inputcorrect = true;
                        }
                    } while (inputcorrect == false);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"输入错误：{ex.Message}");
                    throw;
                }

                return initializationSet;
            
        }
    }
}
