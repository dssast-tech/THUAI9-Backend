using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Numerics;
using System.Text;
using System.Threading.Tasks;

namespace server
{
    [System.Serializable]
    public class GameData
    {
        public MapData mapMetadata { get; set; }
        public SoldiersDataWrapper soldiersData { get; set; }
        public List<GameRound> gameRounds { get; set; }
    }

    [System.Serializable]
    public class MapData
    {
        public string mapName { get; set; }
        public string mapDescription { get; set; }
        public int mapWidth { get; set; }
        public float cubeSize { get; set; }
        public List<MapRow> rows { get; set; } // 使用列表存储行数据
    }
    // SoldierData.cs
    [System.Serializable]
    public class SoldierData
    {
        public int ID { get; set; }
        public string soldierType { get; set; }
        public string camp { get; set; }
        public Vector3Serializable position { get; set; }
        public SoldierStats stats { get; set; }

    }

    [System.Serializable]
    public class SoldierStats
    {
        public int health { get; set; }
        public int strength { get; set; }
        public int mana { get; set; }
    }

    // JSON包装类
    [System.Serializable]
    public class SoldiersDataWrapper
    {
        //public SoldierData[] soldiers;
        public List<SoldierData> soldiers { get; set; }
    }



    // 添加行数据的包装类
    [System.Serializable]
    public class MapRow
    {
        public List<int> row { get; set; } // 每行的数据
    }

    [System.Serializable]
    public class InitialState
    {
        public List<SoldierData> soldiers { get; set; }
    }

    [System.Serializable]
    public class GameRound
    {
        public int roundNumber { get; set; }
        //public InitialState initialState { get; set; }
        public List<BattleAction> actions { get; set; }
    }

    [System.Serializable]
    public class BattleAction
    {
        public string actionType { get; set; }
        public int soldierId { get; set; }

        // Movement
        public List<Vector3Serializable> path { get; set; }
        public int remainingMovement { get; set; }

        // Attack
        public int targetId { get; set; }
        public int damageDealt { get; set; }
        public SoldierStats newStats { get; set; }

        // Ability
        public string ability { get; set; }
        public Vector3Serializable targetPosition { get; set; }
        public int manaCost { get; set; }
    }

    public class Vector3Serializable
    {
        public int x { get; set; }
        public int y { get; set; }
        public int z { get; set; }

        public Vector3Serializable(int x, int y, int z)
        {
            this.x = x;
            this.y = y;
            this.z = z;
        }
    }
}
