using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Numerics;
using System.Text;
using System.Threading.Tasks;

namespace Server
{
    [Serializable]
    public class SoldierStats
    {
        public int health { get; set; }
        public int strength { get; set; }
        public int intelligence { get; set; } // 已将 mana 改为 intelligence
    }

    [Serializable]
    public class SoldierData
    {
        public int ID { get; set; }
        public string soldierType { get; set; }
        public string camp { get; set; }
        public Vector3Serializable position { get; set; }
        public SoldierStats stats { get; set; }
    }

    [Serializable]
    public class MapRow
    {
        public List<int> row { get; set; }
    }

    [Serializable]
    public class MapData
    {
        public int mapWidth { get; set; }
        public List<MapRow> rows { get; set; }
    }

    [Serializable]
    public class PlayerData
    {
        public string player1 { get; set; }
        public string player2 { get; set; }
    }

    [Serializable]
    public class GameScore
    {
        public int redScore { get; set; }
        public int blueScore { get; set; }
    }

    [Serializable]
    public class DamageInfo
    {
        public int targetId { get; set; }
        public int damage { get; set; }
    }

    [Serializable]
    public class BattleAction
    {
        public string actionType { get; set; }
        public int soldierId { get; set; }

        // Movement
        public List<Vector3Serializable> path { get; set; }
        public int remainingMovement { get; set; }

        // Attack/Ability
        public List<DamageInfo> damageDealt { get; set; }
        public SoldierStats oldStats { get; set; }
        public SoldierStats newStats { get; set; }
        public int targetId { get; set; } // 旧版本兼容

        // Ability
        public string ability { get; set; }
        public Vector3Serializable targetPosition { get; set; }
        public int intelligenceCost { get; set; }

        // Score
        public int oldRedScore { get; set; }
        public int oldBlueScore { get; set; }
        public int newRedScore { get; set; }
        public int newBlueScore { get; set; }

        // End
        public string winner { get; set; }

        // Death
        public string cause { get; set; }
    }

    [Serializable]
    public class RoundStatData
    {
        public int soldierId { get; set; }
        public string survived { get; set; }
        public Vector3Serializable position { get; set; }
        public SoldierStats Stats { get; set; }
    }

    [Serializable]
    public class GameRound
    {
        public int roundNumber { get; set; }
        public List<BattleAction> actions { get; set; }
        public List<RoundStatData> stats { get; set; }
        public GameScore score { get; set; }
        public string end { get; set; }
    }

    [Serializable]
    public class GameData
    {
        public MapData mapdata { get; set; }
        public PlayerData playerData { get; set; }
        public List<SoldierData> soldiersData { get; set; } // 直接使用数组而非包装类
        public List<GameRound> gameRounds { get; set; }
    }

    public class Vector3Serializable
    {
        public int x { get; set; }
        public int y { get; set; }
        public int z { get; set; }

        public Vector3Serializable(int x, int y, int z)
        {
            this.x = x;
            this.y = y + 1;
            this.z = z;
        }
    }
}
