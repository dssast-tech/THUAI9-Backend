using System;

public abstract class Piece
{
    public int X { get; internal set; }
    public int Y { get; internal set; }
    public int Health { get; internal set; } = 10;  // 初始生命值
    public int Speed { get; internal set; } = 4;    // 初始速度
    public int owner;  // 所属玩家
    public int id;     // 棋子编号

    // 判断棋子是否死亡
    public bool isDead()
    {
        return Health <= 0;
    }

    // 抽象方法，所有子类必须实现自己的攻击逻辑
    public abstract void Attack(Piece target);

    // 抽象方法，所有子类必须实现自己的技能使用逻辑
    public abstract void UseSkill();

    public Piece(int x, int y, int owner, int id)
    {
        X = x;
        Y = y;
        this.owner = owner;
        this.id = id;
    }
}
