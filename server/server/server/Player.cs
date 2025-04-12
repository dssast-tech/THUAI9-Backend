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
        int feature_total=30;
        void localInit()
        {
            //所有不涉及地图信息、对方信息的初始化在此进行
            //如力量、敏捷、智力分配，棋子武器、防具分配
            //env环境会调用此函数，利用返回值初始化设计地图交互的其他信息（如棋子位置等）

            for(int i=0;i<3;i++){
                pieces.Add(new Piece());
                pieces[i].team = id;
                List<int> feature = initInput();
                pieces[i].strength = feature[0];
                pieces[i].dexterity = feature[1];
                pieces[i].intelligence = feature[2];
                pieces[i].max_health = feature[3];
                pieces[i].health = feature[3];
                pieces
            }
            
            
        }


        public actionSet getAction(Piece currentPiece)
        {
            //控制台或AI逻辑
            throw new NotImplementedException();
        }

        List<int> initInput()
        {
            //接收控制台或TCP输入，将信息解析为一个ListInt（格式自定）
            throw new NotImplementedException();
            
        }



    }
}
