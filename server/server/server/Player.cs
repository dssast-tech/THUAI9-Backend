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
        int id;
        List<Piece> pieces; //持有的棋子

        int attr_total;

        initializationSet localInit()
        {
            initializationSet init = initInput();

            //所有不涉及地图信息、对方信息的初始化在此进行
            //如力量、敏捷、智力分配，棋子武器、防具分配

            //env环境会调用此函数，利用返回值初始化设计地图交互的其他信息（如棋子位置等）
            return init;
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
                if (initializationSet[0] + initializationSet[1] + initializationSet[2] + initializationSet[3] != 30)
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
