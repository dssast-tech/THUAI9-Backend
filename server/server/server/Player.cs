using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

//client和server的交互应通过player类进行，所有函数均应该能够与通信类交互（待定）

namespace server
{
    class Player
    {
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

            for(int i=0;i<3;i++){
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
                bool inputcorrect=false;
                do{
                    Console.WriteLine("现在输入棋子属性分配，格式为：力量 敏捷 智力 总和不超过30");
                    string input = Console.ReadLine();
                    if (!string.IsNullOrEmpty(input))
                    {
                        string[] inputs = input.Split(' ');
                        int[] nums = new int[inputs.Length];
                        for(int i = 0; i < inputs.Length; i++) nums[i] = int.Parse(inputs[i]);
                        if(nums.Length != 3){
                            Console.WriteLine("输入的整数不是3个");
                            continue;
                        }
                        if(nums[0] < 0 || nums[1] < 0 || nums[2] < 0){
                            Console.WriteLine("输入的整数不能为负数！");
                            continue;
                        }
                        if(nums[0] + nums[1] + nums[2] > 30){
                            Console.WriteLine("输入的整数之和多于30！");
                            continue;
                        }
                        for(int i = 0; i < nums.Length; i++) initializationSet.Add(nums[i]);
                        inputcorrect=true;
                    }
                }while(inputcorrect==false);
                

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
                
                inputcorrect=false;
                do{
                    Console.WriteLine("现在输入武器和防具，格式为：武器类型(1-4) 防具类型(1-3)");
                    string input = Console.ReadLine();
                    if (!string.IsNullOrEmpty(input))
                    {
                        string[] inputs = input.Split(' ');
                        int[] nums = new int[inputs.Length];
                        for(int i = 0; i < inputs.Length; i++) nums[i] = int.Parse(inputs[i]);
                        if(nums.Length != 2){
                            Console.WriteLine("输入的整数不是3个");
                            continue;
                        }
                        if(nums[0] < 1 || nums[1] < 1 || nums[0] > 4 || nums[1] > 3){
                            Console.WriteLine("输入的整数不在范围里！");
                            continue;
                        }
                        if(nums[0] == 4 && nums[1] != 1){
                            Console.WriteLine("法杖只能配轻甲！");
                            continue;
                        }
                        for(int i = 0; i < nums.Length; i++) initializationSet.Add(nums[i]);
                        inputcorrect=true;
                    }
                }while(inputcorrect==false);

                inputcorrect=false;
                do{
                    int rows=board.height;int cols=board.width;
                    int boarder=board.boarder;
                    //TODO给用户显示地图信息
                    Console.WriteLine("现在输入棋子初始坐标，格式为：x y");
                    string input = Console.ReadLine();
                    if (!string.IsNullOrEmpty(input))
                    {
                        string[] inputs = input.Split(' ');
                        int[] nums = new int[inputs.Length];
                        for(int i = 0; i < inputs.Length; i++) nums[i] = int.Parse(inputs[i]);
                        if(nums.Length != 2){
                            Console.WriteLine("输入的整数不是2个");
                            continue;
                        }
                        if (nums[0]<0||nums[0]>cols-1||nums[1]> rows - 1 || nums[1]<0){
                            Console.WriteLine("输入的整数超过范围！");
                            continue;
                        }
                        if(board.grid[nums[0],nums[1]]!=1){
                            Console.WriteLine("输入的坐标状态为不可占据!");
                            continue;
                        }
                        bool is_vaild=true;
                        for(int i=0;i<piece_num;i++){
                            if(nums[0]==pieces[i].position.x && nums[1]==pieces[i].position.y){
                                Console.WriteLine("输入的坐标与已有棋子重合！");
                                is_vaild=false;
                            }
                        }
                        if(!is_vaild) continue; 
                        for(int i = 0; i < nums.Length; i++) initializationSet.Add(nums[i]);
                        inputcorrect=true;
                    }
                }while(inputcorrect==false);
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
