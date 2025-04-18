using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Text;
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
            throw new 
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

        void addRound(int roundCnt)
        {
            gamedata.gameRounds.Add(new GameRound());
            gamedata.gameRounds[gamedata.gameRounds.Count - 1].roundNumber = roundCnt;
        }

        void addMove(Piece p, Point target)
        {
            BattleAction temp = new BattleAction();
            temp.actionType = "Movement";
            temp.soldierId = p.id;
            

        }

        void addAttack()


        //        public static GameData ConvertToFrontendFormat(Env env, Board board)
        //        {
        //            return new GameData
        //            {
        //                mapMetadata = EnhanceMapConversion(board),
        //                soldiersData = EnhanceSoldierConversion(env),
        //                gameRounds = EnhanceRoundConversion(env)
        //            };
        //        }

        //        private static MapData EnhanceMapConversion(Board board)
        //        {
        //            return new MapData
        //            {
        //                mapName = DEFAULT_MAP_NAME,
        //                mapDescription = DEFAULT_MAP_DESC,
        //                mapWidth = board.width,
        //                cubeSize = CalculateCubeSize(board), // 智能计算立方体尺寸
        //                rows = ConvertHeightMapToRows(board)
        //            };
        //        }

        //        private static float CalculateCubeSize(Board board)
        //        {
        //            // 根据棋盘尺寸动态计算立方体大小（示例逻辑）
        //            return Mathf.Clamp(10f / board.width, 0.5f, 2.0f);
        //        }

        //        private static List<MapRow> ConvertHeightMapToRows(Board board)
        //        {
        //            List<MapRow> rows = new List<MapRow>();
        //            for (int y = 0; y < board.height; y++)
        //            {
        //                var rowData = new MapRow { row = new List<int>() };
        //                for (int x = 0; x < board.width; x++)
        //                {
        //                    // 融合地形高度和网格类型生成复合数据
        //                    int terrainCode = board.grid[x, y] + board.height_map[x, y] * 10;
        //                    rowData.row.Add(terrainCode);
        //                }
        //                rows.Add(rowData);
        //            }
        //            return rows;
        //        }

        //        private static SoldiersDataWrapper EnhanceSoldierConversion(Env env)
        //        {
        //            return new SoldiersDataWrapper
        //            {
        //                soldiers = env.action_queue.ConvertAll(p => new SoldierData
        //                {
        //                    ID = p.queue_index,
        //                    soldierType = DetermineSoldierType(p),
        //                    camp = GetCampName(p.team),
        //                    position = ConvertTo3DPosition(p),
        //                    stats = new SoldierStats
        //                    {
        //                        health = p.is_dying ? 0 : p.health,  // 濒死状态特殊处理
        //                        strength = CalculateEffectiveStrength(p),
        //                        mana = p.spell_slots
        //                    }
        //                })
        //            };
        //        }

        //        private static string DetermineSoldierType(Piece piece)
        //        {
        //            // 智能兵种类型判断逻辑
        //            if (piece.magic_damage != null && piece.magic_damage.value > piece.physical_damage.value)
        //                return "Mage";
        //            if (piece.attack_range > 2)
        //                return "Archer";
        //            return "Warrior";
        //        }

        //        private static Vector3 ConvertTo3DPosition(Piece piece)
        //        {
        //            // 三维坐标系转换（XZ平面为战场平面，Y轴为高度）
        //            return new Vector3(
        //                piece.position.X * 2f,  // 根据实际棋盘比例调整
        //                piece.height * 0.5f,
        //                piece.position.Y * 2f
        //            );
        //        }

        //        private static string GetCampName(int teamId)
        //        {
        //            return teamId switch
        //            {
        //                0 => "Red",
        //                1 => "Blue",
        //                _ => "Neutral"
        //            };
        //        }

        //        private static int CalculateEffectiveStrength(Piece piece)
        //        {
        //            // 计算考虑行动点数的实际强度
        //            return (int)(piece.strength * (piece.action_points / (float)piece.max_action_points));
        //        }

        //        private static List<GameRound> EnhanceRoundConversion(Env env)
        //        {
        //            var rounds = new List<GameRound>();

        //            // 历史回合处理
        //            for (int i = 0; i <= env.round_number; i++)
        //            {
        //                rounds.Add(new GameRound
        //                {
        //                    roundNumber = i,
        //                    initialState = new InitialState
        //                    {
        //                        soldiers = GetHistoricalSoldierStates(i) // 需要历史状态追踪系统
        //                    },
        //                    actions = ReconstructRoundActions(i) // 需要动作记录系统
        //                });
        //            }

        //            return rounds;
        //        }

        //        // 需要实现的扩展点（需接入游戏的状态记录系统）
        //        private static List<SoldierData> GetHistoricalSoldierStates(int round) => new List<SoldierData>();
        //        private static List<BattleAction> ReconstructRoundActions(int round) => new List<BattleAction>();
    }
}
