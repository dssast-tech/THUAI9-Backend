using System;
using System.Collections.Generic;

namespace Server
{
    /// <summary>
    /// DTO 定义，字段尽量按照 Protos/message.proto 中的结构与含义设计，
    /// 主要用于 JSON 序列化/反序列化。
    /// </summary>
    public class PointDto
    {
        public int x { get; set; }
        public int y { get; set; }
    }

    public class CellDto
    {
        public int state { get; set; }      // 对应 _Cell.state
        public int playerId { get; set; }   // 对应 _Cell.playerId
        public int pieceId { get; set; }    // 对应 _Cell.pieceId
    }

    public class BoardDto
    {
        public int width { get; set; }                      // 对应 _Board.width
        public int height { get; set; }                     // 对应 _Board.height
        public List<CellDto> grid { get; set; } = new();    // 对应 repeated _Cell grid
        public List<int> height_map { get; set; } = new();  // 对应 repeated int32 height_map
        public int boarder { get; set; }                    // 对应 _Board.boarder
    }

    public class AreaDto
    {
        public int x { get; set; }
        public int y { get; set; }
        public int radius { get; set; }
    }

    public class SpellContextDto
    {
        public int caster { get; set; }              // 使用棋子 id
        public int spellID { get; set; }             // 对应 _SpellContext.spellID
        public int targetType { get; set; }          // 对应 _TargetType（用 int 表示枚举）
        public int target { get; set; }              // 目标棋子 id
        public AreaDto targetArea { get; set; }      // 目标区域
        public int spellLifespan { get; set; }       // 剩余回合
    }

    public class AttackContextDto
    {
        public int attacker { get; set; }            // 攻击者棋子 id
        public int target { get; set; }              // 目标棋子 id
    }

    public class PieceDto
    {
        public int health { get; set; }
        public int max_health { get; set; }
        public int physical_resist { get; set; }
        public int magic_resist { get; set; }
        public int physical_damage { get; set; }
        public int magic_damage { get; set; }
        public int action_points { get; set; }
        public int max_action_points { get; set; }
        public int spell_slots { get; set; }
        public int max_spell_slots { get; set; }
        public float movement { get; set; }
        public float max_movement { get; set; }
        public int id { get; set; }
        public int strength { get; set; }
        public int dexterity { get; set; }
        public int intelligence { get; set; }
        public PointDto position { get; set; }
        public int height { get; set; }
        public int attack_range { get; set; }
        public List<int> spell_list { get; set; } = new();
        public int deathRound { get; set; }
        public int team { get; set; }
        public int queue_index { get; set; }
        public bool is_alive { get; set; }
        public bool is_in_turn { get; set; }
        public bool is_dying { get; set; }
        public double spell_range { get; set; }
    }

    /// <summary>
    /// 对应 _GameStateResponse，用于导出当前回合状态。
    /// </summary>
    public class GameStateDto
    {
        public int currentRound { get; set; }                   // 对应 currentRound
        public int currentPlayerId { get; set; }                // 对应 currentPlayerId
        public int currentPieceID { get; set; }                 // 对应 currentPieceID
        public List<PieceDto> actionQueue { get; set; } = new();// 对应 repeated _Piece actionQueue
        public BoardDto board { get; set; }                     // 对应 _Board board
        public List<SpellContextDto> delayedSpells { get; set; } = new(); // 对应 repeated _SpellContext delayedSpells
        public bool isGameOver { get; set; }                    // 对应 isGameOver
    }

    /// <summary>
    /// 对应 _actionSet，用于从 JSON 接收操作。
    /// </summary>
    public class ActionSetDto
    {
        public bool move { get; set; }
        public PointDto move_target { get; set; }
        public bool attack { get; set; }
        public AttackContextDto attack_context { get; set; }
        public bool spell { get; set; }
        public SpellContextDto spell_context { get; set; }
        public int playerId { get; set; }
    }
}


