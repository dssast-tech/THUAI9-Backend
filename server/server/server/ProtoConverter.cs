using Server;
namespace Server
{
    static class Converter
    {

        public static T[] Flatten2DArray<T>(T[,] array)
        {
            int rows = array.GetLength(0);
            int cols = array.GetLength(1);
            T[] result = new T[rows * cols];

            int index = 0;
            for (int i = 0; i < rows; i++)
            {
                for (int j = 0; j < cols; j++)
                {
                    result[index++] = array[i, j];
                }
            }

            return result;
        }
        // ===========================
        // _Point ↔ Point
        // ===========================
        public static Point FromProto(_Point proto) => new Point { x = proto.X, y = proto.Y };
        public static _Point ToProto(Point csharp) => new _Point { X = csharp.x, Y = csharp.y };

        // ===========================
        // _Cell ↔ Cell
        // ===========================
        public static Cell FromProto(_Cell proto) => new Cell
        {
            state = proto.State,
            playerId = proto.PlayerId,
            pieceId = proto.PieceId
        };
        public static _Cell ToProto(Cell csharp) => new _Cell
        {
            State = csharp.state,
            PlayerId = csharp.playerId,
            PieceId = csharp.pieceId
        };

        // ===========================
        // _Board ↔ Board
        // ===========================
        //public static Board FromProto(_Board proto) => new Board
        //{
        //    width = proto.Width,
        //    height = proto.Height,
        //    grid = proto.Grid.Select(FromProto).ToList(),
        //    HeightMap = proto.HeightMap.ToList(),
        //    Boarder = proto.Boarder
        //};
        public static _Board ToProto(Board csharp)
        {
            var proto = new _Board
            {
                Width = csharp.width,
                Height = csharp.height,
                Boarder = csharp.boarder
            };
            proto.Grid.AddRange(Flatten2DArray(csharp.grid).Select(ToProto));
            proto.HeightMap.AddRange(Flatten2DArray(csharp.height_map));
            return proto;
        }

        // ===========================
        // _Spell ↔ Spell
        // ===========================
        
        // ===========================
        // _Area ↔ Area
        // ===========================
        public static Area FromProto(_Area proto) => new Area
        {
            x = proto.X,
            y = proto.Y,
            radius = proto.Radius
        };
        public static _Area ToProto(Area csharp) => new _Area
        {
            X = csharp.x,
            Y = csharp.y,
            Radius = csharp.radius
        };

        // ===========================
        // _Piece ↔ Piece
        // ===========================
       
        public static _Piece ToProto(Piece csharp)
        {
            var proto = new _Piece
            {
                Health = csharp.health,
                MaxHealth = csharp.max_health,
                PhysicalResist = csharp.physical_resist,
                MagicResist = csharp.magic_resist,
                PhysicalDamage = csharp.physical_damage,
                MagicDamage = csharp.magic_damage,
                ActionPoints = csharp.action_points,
                MaxActionPoints = csharp.max_action_points,
                SpellSlots = csharp.spell_slots,
                MaxSpellSlots = csharp.max_spell_slots,
                Movement = csharp.movement,
                MaxMovement = csharp.max_movement,
                Id = csharp.id,
                Strength = csharp.strength,
                Dexterity = csharp.dexterity,
                Intelligence = csharp.intelligence,
                Position = ToProto(csharp.position),
                Height = csharp.height,
                AttackRange = csharp.attack_range,
                DeathRound = csharp.deathRound,
                Team = csharp.team,
                QueueIndex = csharp.queue_index,
                IsAlive = csharp.is_alive,
                IsInTurn = csharp.is_in_turn,
                IsDying = csharp.is_dying,
                SpellRange = csharp.spell_range
            };
            List<int> spellIdList = new List<int>();
            foreach (Spell sp in csharp.spell_list) spellIdList.Add(sp.id);
            proto.SpellList.AddRange(spellIdList);
            return proto;
        }

        // ===========================
        // _Player ↔ Player
        // ===========================
        public static _Player ToProto(Player csharp)
        {
            var proto = new _Player
            {
                Id = csharp.id,
                FeatureTotal = csharp.feature_total,
                PieceNum = csharp.piece_num
            };
            proto.Pieces.AddRange(csharp.pieces.Select(ToProto));
            return proto;
        }

        // ===========================
        // _pieceArg ↔ PieceArg
        // ===========================
        public static pieceArg FromProto(_pieceArg proto) => new pieceArg
        {
            strength = proto.Strength,
            intelligence = proto.Intelligence,
            dexterity = proto.Dexterity,
            equip = FromProto(proto.Equip),
            pos = FromProto(proto.Pos)
        };
        public static _pieceArg ToProto(pieceArg csharp) => new _pieceArg
        {
            Strength = csharp.strength,
            Intelligence = csharp.intelligence,
            Dexterity = csharp.dexterity,
            Equip = ToProto(csharp.equip),
            Pos = ToProto(csharp.pos)
        };

        // 其它 message 类依此类推
    }
}
