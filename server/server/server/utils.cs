using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

//所有辅助类应置于此文件中


namespace server
{
    struct Point
    {
        int x, y;
    }

    struct actionSet
    {
        Point move_target;
        bool attack;
        AttackContext attack_context;
        bool spell;
        SpellContext spell_context;
    }

    struct initializationSet
    {
        //用于棋子初始化的信息，具体内容待定
    }

    struct DicePair
    {

    }

    struct Message
    {
        //通信预留转接类
    }

    struct AttackContext
    {
        //攻击参数打包在此（如攻击范围、攻击目标、攻击类型等）
    }

    struct SpellContext
    {
        Spell spell;
        //法术参数打包在此（如法术目标、延时等）
    }

    //注：任何类调用任何攻击行为时，参数最好都应该封装在context包中进行传递，不应产生额外的独立参数，这样可以避免参数过多导致的函数调用混乱，也有利于向前端传递的日志输出


    struct Spell
    {
        //法术属性打包在此（如法术名称、法术范围）
    }

    //应该区分spell和spellcontext，后者可理解为一个已经打出的法术，包含目标信息，主要用于env类；前者是法术本身的属性，主要用于棋子类中标记该棋子可用的法术
}
