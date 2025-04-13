using System;

public class CommonPiece : Piece
{
    public int Damage { get; internal set; } = 100;  // 初始伤害

    public CommonPiece(int x, int y, int owner, int id) : base(x, y, owner, id)
    {
    }

    // 实现攻击逻辑
    public override void Attack(Piece target)
    {
        Random rnd = new Random();
        int damageDealt = rnd.Next(1, Damage + 1);
        target.Health -= damageDealt;
        Console.WriteLine($"Piece {owner}-{id} Attacked enemy {target.owner}-{target.id} for {damageDealt} damage!");
    }

    // 实现技能逻辑
    public override void UseSkill()
    {
        Console.WriteLine("Special skill not implemented yet.");
    }
}
