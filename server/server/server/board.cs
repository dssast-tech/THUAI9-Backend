using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;
using static System.Runtime.InteropServices.JavaScript.JSType;

//仅维护信息
namespace server
{

    class Board
    {
        int width, height;
        int[,] grid;  // 0: 空地, 1: 可行走, 2: 占据, -1: 禁止
        int[,] height_map;
        //分界线待实现

        int[,] validTarget(Point from, Point to, float movement)
        {
            //返回一张mask图，以01标记所有能抵达的点，用于提交给client,以及env中的合法性判定
            //不一定要实现
            throw new NotImplementedException();
        }


        bool movePiece(Piece p, Point to, float movement)
        {
            /*
             参数：要移动的棋子、终点、行动力
             返回值：是否移动成功

            该函数负责移动合法性判定和移动执行

            按文档设计，移动合法性判定至少要覆盖：绕开敌人、高度差不能过大等判定
            函数也可置于env中
             */
           throw new NotImplementedException();
        }

        bool isOccupied(Point p)
        {
            throw new NotImplementedException();
        }

        bool getHeight(Point p)
        {
            throw new NotImplementedException();
        }

        void removePiece(Piece p)
        {
            throw new NotImplementedException();
        }

        void init()
        {
            //棋盘初始化（形状、地形等）
        }
    }
}
