using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


//client和server的交互应通过player类进行，所有函数均应该能够与通信类交互（待定）

namespace server
{
    public class Player
    {
        int id;
        List<Piece> pieces; //持有的棋子
        int strength_total;
        int dexterity_total;
        int intelligence_total;

        void localInit()
        {
            //所有不涉及地图信息、对方信息的初始化在此进行
            //如力量、敏捷、智力分配，棋子武器、防具分配
            throw new NotImplementedException();
        }

        initializationSet envInit()
        {
            //初始化涉及地图信息的类，将需要初始化的内容打包为一个initializationSet（格式自定），env会调用该函数并处理具体逻辑
            //如地图位置
            throw new NotImplementedException();
        }

        public actionSet getAction(Piece currentPiece)
        {
            //控制台或AI逻辑
            throw new NotImplementedException();
        }




    }
}
