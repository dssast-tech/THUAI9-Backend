using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Serialization;


//env类是整个游戏的核心，应该有权读取所有信息，并通过其他类给定的接口修改信息。所有涉及棋子与棋子交互、棋子与棋盘交互的行为都应在env类中进行处理。
namespace server
{
    class Env
    {
        List<Piece> action_queue;
        Piece current_piece;
        int round_number;
        List<SpellContext> delayed_spells;
        Player player1;
        Player player2;
        Board board;
        bool isGameOver;
        
        void initialize()
        {
            //执行各类初始化
            //注：对于player类，先调用player的localInit函数进行初始化，再调用envInit函数，并根据envInit返回值进行地图信息的初始化（需要进行各种合法性检查，如初始位置是否越过双方边界线）
        }

        actionSet getAction()
        {
            //获取当前棋子的行动，应该通过player类获取一个actionSet
            throw new NotImplementedException();
        }

        void executeAttack(AttackContext context)
        {
            //执行攻击，包括合法性检查，免伤计算，暴击计算，扣血等
        }

        void executeSpell(SpellContext context)
        {
            //执行法术，包括合法性检查，免伤计算，扣血等
        }



        void executeMove(Point move_target)
        {
            //执行移动
        }

        //潜在的其他行为

        void step()
        {
            //执行每回合的逻辑
            //包括：执行行为逻辑getAction,executeAttack等，在执行行为后进行行动队列的更新、棋子状态的更新、棋盘状态的更新、终局判定等
            //注：棋盘状态的更新应在每回合结束时进行
        }

        void log(int mode)
        {
            //日志生成
            //应该支持输出到回放文件、输出到控制台两种模式
        }

        public void run()
        {
            initialize();
            while (!isGameOver) step();
            log(0);
        }
    }
}
