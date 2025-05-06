using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace Server
{
    internal class LogConverter
    {
        public GameData gamedata;

        public void init(List<Piece> init_queue, Board board)
        {
            gamedata = new GameData();
            gamedata.mapdata = new MapData();
            gamedata.mapdata.mapWidth = board.width;
            gamedata.mapdata.rows = new List<MapRow>();
            gamedata.mapdata.rows = ConvertHeightMapToRows(board);
            gamedata.playerData = new PlayerData();
            gamedata.playerData.player1 = "Red";
            gamedata.playerData.player2 = "Blue";
            gamedata.soldiersData = ConvertPieceToSoldier(init_queue);
            gamedata.gameRounds = new List<GameRound>();
        }

        List<MapRow> ConvertHeightMapToRows(Board board)
        {
            List<MapRow> rows = new List<Server.MapRow>();

            // 遍历二维数组的每一行
            for (int i = 0; i < board.height_map.GetLength(0); i++)
            {
                MapRow mapRow = new MapRow
                {
                    row = new List<int>()
                };

                // 遍历当前行的每一列
                for (int j = 0; j < board.height_map.GetLength(1); j++)
                {
                    // 将高度值+1后添加到MapRow
                    mapRow.row.Add(board.height_map[i, j] + 1);
                }

                // 将MapRow添加到列表
                rows.Add(mapRow);
            }

            return rows;
        }

        List<SoldierData> ConvertPieceToSoldier(List<Piece> pieces)
        {
            List<SoldierData> soldiers = new List<SoldierData>();
            foreach (Piece piece in pieces)
            {
                SoldierData temp = new SoldierData();
                temp.ID = piece.id;
                temp.camp = piece.team == 1 ? "Red" : "Blue";
                temp.position = new Vector3Serializable(piece.position.x, piece.height, piece.position.y );
                temp.soldierType = piece.type;
                temp.stats = new SoldierStats();
                temp.stats.health = piece.health;
                temp.stats.strength = piece.strength;
                temp.stats.intelligence = piece.intelligence;
                soldiers.Add(temp);
            }
            return soldiers;
        }

        public void addRound(int roundCnt,List<Piece> pieces)
        {
            gamedata.gameRounds.Add(new GameRound());
            var curRound = gamedata.gameRounds[gamedata.gameRounds.Count - 1];
            curRound.roundNumber = roundCnt;
            curRound.actions = new List<BattleAction>();
            //curRound.initialState = new InitialState();
            //curRound.initialState.soldiers = new List<SoldierData>(gamedata.soldiersData.soldiers);
            //foreach (SoldierData i in curRound.initialState.soldiers)
            //{
            //    i.stats.health = 0;
            //}

            //foreach(Piece piece in pieces)
            //{
            //    SoldierData temp = new SoldierData();
            //    temp.ID = piece.id;
            //    temp.camp = piece.team == 1 ? "Red" : "Blue";
            //    temp.position = new Vector3Serializable(piece.position.x, piece.position.y, piece.height);
            //    temp.stats = new SoldierStats();
            //    temp.stats.health = piece.health;
            //    temp.stats.strength = piece.strength;
            //    temp.stats.mana = piece.intelligence;
            //    curRound.initialState.soldiers[temp.ID] = temp;
            //}
        }

        public void finishRound(int roundCnt, List<Piece> pieces, int redLeft, int blueLeft, bool isGameOver)
        {
            List<RoundStatData> tempStat = new List<RoundStatData>();
            foreach (var piece in pieces)
            {
                RoundStatData tempStatData = new RoundStatData();
                tempStatData.soldierId = piece.id;
                tempStatData.position = new Vector3Serializable(piece.position.x, piece.height, piece.position.y);
                tempStatData.survived = "true";
                tempStatData.Stats = new SoldierStats();
                tempStatData.Stats.health = piece.health;
                tempStatData.Stats.strength = piece.strength;
                tempStatData.Stats.intelligence = piece.intelligence;
                tempStat.Add(tempStatData);
            }
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].stats = tempStat;
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].score = new GameScore();
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].score.redScore = Player.PIECECNT - blueLeft;
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].score.blueScore = Player.PIECECNT - redLeft;
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].end = isGameOver == true ? "true" : "false";
        }

        public void addMove(Piece p, List<Vector3Serializable> path)
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
            temp.damageDealt = new List<DamageInfo>();
            DamageInfo damageInfo = new DamageInfo();
            damageInfo.targetId = context.target.id;
            damageInfo.damage = context.damageDealt;
            temp.damageDealt.Add(damageInfo);
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].actions.Add(temp);
        }

        public void addSpell(SpellContext context, Board board)
        {
            //TODO
            BattleAction temp = new BattleAction();
            temp.actionType = "Ability";
            temp.soldierId = context.caster.id;
            temp.damageDealt = new List<DamageInfo>();

            int spellType;
            if (context.spell.effectType == SpellEffectType.Damage) spellType = 1;
            else if (context.spell.effectType == SpellEffectType.Heal) spellType = -1;
            else spellType = 0;

            if (context.target != null)
            {
                temp.targetPosition = new Vector3Serializable(context.target.position.x, context.target.height, context.target.position.y);
                DamageInfo tempinfo = new DamageInfo();
                tempinfo.targetId = context.target.id;

                tempinfo.damage = context.spell.baseValue*spellType;
                temp.damageDealt.Add(tempinfo); 
            }
            else
            {
                int height = board.height_map[(int)context.targetArea.x, (int)context.targetArea.y];
                temp.targetPosition = new Vector3Serializable(context.targetArea.x, height, context.targetArea.y);
                foreach (Piece piece in context.hitPiecies)
                {
                    DamageInfo tempinfo = new DamageInfo();
                    tempinfo.targetId = piece.id;
                    tempinfo.damage = context.spell.baseValue * spellType;
                    temp.damageDealt.Add(tempinfo);
                }
            }
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].actions.Add(temp);
        }

        public void addDeath(Piece p)
        {
            BattleAction temp = new BattleAction();
            temp.actionType = "Death";
            temp.soldierId = p.id;
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].actions.Add(temp);
        }

        public void save()
        {
            // 将类对象序列化为JSON

            //Console.WriteLine(gamedata.soldiersData.soldiers[1].ID);

            string json = JsonSerializer.Serialize(gamedata, new JsonSerializerOptions { WriteIndented = true });

            // 获取当前目录
            string currentDirectory = Directory.GetCurrentDirectory();

            // 定义文件路径
            string filePath = Path.Combine(currentDirectory, "log.json");

            // 将JSON写入文件
            File.WriteAllText(filePath, json);

            Console.WriteLine($"JSON已保存到: {filePath}");
            Console.WriteLine("按下回车键继续...");
            Console.ReadLine();
        }
    }
}
