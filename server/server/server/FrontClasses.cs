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
        public MapData mapMetadata;
        public SoldiersDataWrapper soldiersData;
        public List<GameRound> gameRounds;
    }
    [System.Serializable]
    public class MapData
    {
        public string mapName;
        public string mapDescription;
        public int mapWidth;
        public float cubeSize;
        public List<MapRow> rows; // 使用列表存储行数据
    }
    // SoldierData.cs
    [System.Serializable]
    public class SoldierData
    {
        public int ID;
        public string soldierType;
        public string camp;
        public Vector3 position;
        public SoldierStats stats;

    }

    [System.Serializable]
    public class SoldierStats
    {
        public int health;
        public int strength;
        public int mana;
    }

    // JSON包装类
    [System.Serializable]
    public class SoldiersDataWrapper
    {
        //public SoldierData[] soldiers;
        public List<SoldierData> soldiers;
    }



    // 添加行数据的包装类
    [System.Serializable]
    public class MapRow
    {
        public List<int> row; // 每行的数据
    }

    [System.Serializable]
    public class InitialState
    {
        public List<SoldierData> soldiers;
    }

    [System.Serializable]
    public class GameRound
    {
        public int roundNumber;
        public InitialState initialState;
        public List<BattleAction> actions;
    }

    [System.Serializable]
    public class BattleAction
    {
        public string actionType;
        public int soldierId;

        // Movement
        public List<Vector3> path;
        public int remainingMovement;

        // Attack
        public int targetId;
        public int damageDealt;
        public SoldierStats newStats;

        // Ability
        public string ability;
        public Vector3 targetPosition;
        public int manaCost;
    }
}
