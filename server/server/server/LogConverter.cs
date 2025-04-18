using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace server
{
    internal class LogConverter
    {
        public GameData gamedata;

        public void init(List<Piece> init_queue, Board board)
        {
            gamedata = new GameData();
            gamedata.mapMetadata = new MapData();
            gamedata.mapMetadata.mapName = "Default Map";
            gamedata.mapMetadata.mapDescription = "Default Description";
            gamedata.mapMetadata.mapWidth = board.width;
            gamedata.mapMetadata.cubeSize = 1.0f; // 默认立方体大小!!!!!暂不明确意义
            gamedata.mapMetadata.rows = new List<MapRow>();
            gamedata.mapMetadata.rows = ConvertHeightMapToRows(board);
            gamedata.soldiersData = new SoldiersDataWrapper();
            gamedata.soldiersData.soldiers = ConvertPieceToSoldier(init_queue);
            gamedata.gameRounds = new List<GameRound>();
        }

        List<MapRow> ConvertHeightMapToRows(Board board)
        {
            throw new NotImplementedException(); 
        }

        List<SoldierData> ConvertPieceToSoldier(List<Piece> pieces)
        {
            List<SoldierData> soldiers = new List<SoldierData>();
            foreach (Piece piece in pieces)
            {
                SoldierData temp = new SoldierData();
                temp.ID = piece.id;
                temp.camp = piece.team == 0 ? "Red" : "Blue";
                temp.position = new Vector3(piece.position.x, piece.position.y, piece.height);
                temp.stats = new SoldierStats();
                temp.stats.health = piece.health;
                temp.stats.strength = piece.strength;
                temp.stats.mana = piece.intelligence;
                soldiers.Add(temp);
            }
            return soldiers;
        }

        public void addRound(int roundCnt)
        {
            gamedata.gameRounds.Add(new GameRound());
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].roundNumber = roundCnt;
        }

        public void addMove(Piece p, List<Vector3> path)
        {
            BattleAction temp = new BattleAction();
            temp.actionType = "Movement";
            temp.soldierId = p.id;
            temp.path = path;
            temp.remainingMovement =(int) p.movement;
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].actions.Add(temp);
        }

        public void addAttack(AttackContext context)
        {
            //即使攻击未命中也会传递一个Attack行为
            BattleAction temp = new BattleAction();
            temp.actionType = "Attack";
            temp.soldierId = context.attacker.id;
            temp.targetId = context.target.id;
            temp.damageDealt = context.damageDealt;
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].actions.Add(temp);
        }

        public void addSpell(SpellContext context)
        {
            //TODO
        }

        public void save()
        {
            // 将类对象序列化为JSON
            string json = JsonSerializer.Serialize(gamedata, new JsonSerializerOptions { WriteIndented = true });

            // 获取当前目录
            string currentDirectory = Directory.GetCurrentDirectory();

            // 定义文件路径
            string filePath = Path.Combine(currentDirectory, "log.json");

            // 将JSON写入文件
            File.WriteAllText(filePath, json);

            Console.WriteLine($"JSON已保存到: {filePath}");
        }
    }
}
