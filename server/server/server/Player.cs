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
        public void localInit()
        {
            //所有不涉及地图信息、对方信息的初始化在此进行
            //如力量、敏捷、智力分配，棋子武器、防具分配
            //env环境会调用此函数，利用返回值初始化设计地图交互的其他信息（如棋子位置等）
            pieces= new List<Piece>();
            for(int i=0;i<3;i++){
                pieces.Add(new Piece());
                //没有初始化piece所在的高度 后面记得写
                var accessor=pieces[i].GetAccessor();
                accessor.SetTeamTo(id);
                List<int> feature = initInput();
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

        List<int> initInput()
        {
            // 接收控制台输入，将信息解析为一个initializationSet
            List<int> initializationSet = new List<int>();
            Console.WriteLine("请输入7个整数（以空格分隔）：");
        
            try
            {
                // 从终端读取一行输入，并将其解析为整数
                string input = Console.ReadLine();
                if (!string.IsNullOrEmpty(input))
                {
                    // 将输入按空格分割并解析为整数
                    string[] inputs = input.Split(' ');
                    // 输入的属性分别代表棋子的力量、智力、敏捷、武器、防具、初始x坐标、初始y坐标
                    foreach (string str in inputs)
                    {
                        if (initializationSet.Count >= 7)
                            break; // 只接受7个整数
        
                        initializationSet.Add(int.Parse(str));
                    }
                }
        
                // 检查是否输入了足够的整数
                if (initializationSet.Count < 5)
                {
                    throw new Exception("输入的整数不足5个！");
                }
                // 检查输入的角色属性是否在范围内
                for (int i = 0; i < initializationSet.Count; i++)
                {
                    if (initializationSet[i] < 0)
                    {
                        throw new Exception($"输入的整数{initializationSet[i]}不在范围内（0-10）！");
                    }
                }
                // 检查输入的角色属性总和是否等于30
                if (initializationSet[0] + initializationSet[1] + initializationSet[2]  != 30)  //！几个参数？
                {
                    throw new Exception("输入的整数之和不等于30！");
                }
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
