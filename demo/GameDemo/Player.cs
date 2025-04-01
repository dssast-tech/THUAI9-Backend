using System;

public class Player
{
    public int id { get; private set; }

    public Player(int id)
    {
        this.id = id;
    }

    // 玩家选择动作
    public actionSet policy(Piece next)
    {
        Console.WriteLine($"Player {id}'s turn");
        Console.WriteLine($"Movable Piece: {next.owner}-{next.id}");

        int tmp_x = 0, tmp_y = 0;
        while (true)
        {
            Console.WriteLine("Please key in the target coordinate: (separate x and y with space)");
            string input = Console.ReadLine();
            string[] parts = input.Split(' ');

            if (parts.Length == 2 && int.TryParse(parts[0], out tmp_x) && int.TryParse(parts[1], out tmp_y))
            {
                Console.WriteLine($"Coordinate: {tmp_x} 和 {tmp_y}");
                break;  // 输入有效，跳出循环
            }
            else
            {
                Console.WriteLine("输入无效，请确保输入两个用空格分隔的数字。");
            }
        }

        int attak = 0;
        while (true)
        {
            // 输入攻击操作
            Console.WriteLine("Please key in the Attack Operation: (0: no op, 1: attack)");
            string input = Console.ReadLine();
            if (int.TryParse(input, out attak) && (attak == 0 || attak == 1))
            {
                Console.WriteLine($"Attack Operation: {attak}");
                break;  // 输入有效，跳出循环
            }
            else
            {
                Console.WriteLine("输入无效，请确保输入 0 或 1。");
            }
        }

        int skill = 0;
        while (true)
        {
            // 输入技能操作
            Console.WriteLine("Please key in the Skill Operation: (0: no op, 1: skill)");
            string input = Console.ReadLine();
            if (int.TryParse(input, out skill) && (skill == 0 || skill == 1))
            {
                Console.WriteLine($"Skill Operation: {skill}");
                break;  // 输入有效，跳出循环
            }
            else
            {
                Console.WriteLine("输入无效，请确保输入 0 或 1。");
            }
        }

        return new actionSet { move_target = new Point { x = tmp_x, y = tmp_y }, attack = attak, skill = skill };
    }
}
