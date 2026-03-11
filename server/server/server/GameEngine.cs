using System;
using System.Linq;
using System.Text.Json;

namespace Server
{
    /// <summary>
    /// GameEngine：对外暴露的轻量级游戏引擎封装。
    /// Python 侧通过 JSON 与该类交互。
    /// </summary>
    public class GameEngine
    {
        private Env env;

        /// <summary>
        /// 初始化游戏。当前版本暂不解析 configJson，仅完成内部环境初始化。
        /// </summary>
        public void Initialize(string configJson)
        {
            env = new Env();
            // 目前暂不使用配置，后续可根据需要从 configJson 中读入参数
            env.initialize().Wait();
        }

        /// <summary>
        /// 通过 JSON 为某个玩家配置棋子。
        /// JSON 应序列化为 pieceArg 列表（字段同 message.proto/_pieceArg）。
        /// </summary>
        public bool SetPlayerPieces(int playerId, string piecesJson)
        {
            if (env == null) throw new InvalidOperationException("Engine not initialized.");

            try
            {
                var pieceArgs = JsonSerializer.Deserialize<pieceArg[]>(piecesJson);
                if (pieceArgs == null)
                {
                    return false;
                }

                var initMsg = new InitPolicyMessage
                {
                    pieceArgs = pieceArgs.ToList()
                };

                if (playerId == 0 || playerId == 1)
                {
                    // 兼容 Saiblo 0/1 习惯：内部 player1.id = 1, player2.id = 2
                    playerId += 1;
                }

                if (playerId == env.player1.id)
                {
                    env.player1.localInit(initMsg, env.board);
                }
                else if (playerId == env.player2.id)
                {
                    env.player2.localInit(initMsg, env.board);
                }
                else
                {
                    throw new ArgumentOutOfRangeException(nameof(playerId));
                }

                // 双方棋子都已配置后，初始化战斗
                if (!env.isBattleInitialized &&
                    env.player1.pieces != null && env.player1.pieces.Count > 0 &&
                    env.player2.pieces != null && env.player2.pieces.Count > 0)
                {
                    env.SetupBattle();
                }

                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 导出当前游戏状态为 JSON，结构参考 message.proto 的 _GameStateResponse。
        /// </summary>
        public string GetStateJson()
        {
            if (env == null) throw new InvalidOperationException("Engine not initialized.");

            var dto = new GameStateDto
            {
                currentRound = env.round_number,
                currentPlayerId = env.current_piece?.team ?? 0,
                currentPieceID = env.current_piece?.id ?? -1,
                isGameOver = env.isGameOver,
                board = ConvertBoard(env.board)
            };

            // 行动队列
            dto.actionQueue = env.action_queue?
                .Select(ConvertPiece)
                .ToList() ?? [];

            // 延时法术
            dto.delayedSpells = env.delayed_spells?
                .Select(ConvertSpellContext)
                .ToList() ?? [];

            return JsonSerializer.Serialize(dto);
        }

        /// <summary>
        /// 执行玩家操作（JSON），JSON 结构参考 ActionSetDto / message.proto/_actionSet。
        /// 约定：应在调用 NextTurn()（即 Env.BeginTurn）之后调用本方法。
        /// </summary>
        public bool ExecuteAction(int playerId, string actionJson)
        {
            if (env == null) throw new InvalidOperationException("Engine not initialized.");
            if (!env.isBattleInitialized || env.isGameOver) return false;

            try
            {
                var dto = JsonSerializer.Deserialize<ActionSetDto>(actionJson);
                if (dto == null) return false;

                // playerId 兼容处理
                if (playerId == 0 || playerId == 1)
                {
                    playerId += 1;
                }

                if (env.current_piece == null)
                {
                    // 尚未开始任何回合
                    return false;
                }

                if (playerId != env.current_piece.team)
                {
                    // 非当前行动方的操作，直接拒绝
                    return false;
                }

                var action = new actionSet
                {
                    move = dto.move,
                    attack = dto.attack,
                    spell = dto.spell
                };

                if (dto.move && dto.move_target != null)
                {
                    action.move_target = new Point(dto.move_target.x, dto.move_target.y);
                }

                if (dto.attack && dto.attack_context != null)
                {
                    var atkCtx = new AttackContext
                    {
                        attacker = env.current_piece,
                        attackType = AttackType.Physical,
                        isCritical = false,
                        isHit = false,
                        damageDealt = 0,
                        attackPosition = env.current_piece.position
                    };

                    // 根据 target id 查找棋子
                    var target = env.action_queue.FirstOrDefault(p => p.id == dto.attack_context.target);
                    atkCtx.target = target;
                    action.attack_context = atkCtx;
                }

                if (dto.spell && dto.spell_context != null)
                {
                    var spellTemplate = SpellFactory.GetSpellById(dto.spell_context.spellID);
                    if (spellTemplate.HasValue)
                    {
                        var spellCtx = new SpellContext
                        {
                            caster = env.current_piece,
                            spell = spellTemplate.Value,
                            spellPower = 0,
                            targetType = (TargetType)dto.spell_context.targetType,
                            target = env.action_queue.FirstOrDefault(p => p.id == dto.spell_context.target),
                            targetArea = dto.spell_context.targetArea != null
                                ? new Area
                                {
                                    x = dto.spell_context.targetArea.x,
                                    y = dto.spell_context.targetArea.y,
                                    radius = dto.spell_context.targetArea.radius
                                }
                                : null,
                            spellRange = spellTemplate.Value.range,
                            effectType = spellTemplate.Value.effectType,
                            damageType = spellTemplate.Value.damageType,
                            spellLifespan = dto.spell_context.spellLifespan,
                            baseLifespan = spellTemplate.Value.baseLifespan,
                            spellCost = spellTemplate.Value.spellCost,
                            isAreaEffect = spellTemplate.Value.isAreaEffect,
                            isDelaySpell = spellTemplate.Value.isDelaySpell,
                            isLockingSpell = spellTemplate.Value.isLockingSpell,
                            actionCost = 1,
                            isHit = false,
                            isCritical = false,
                            delayAdd = false,
                            hitPiecies = []
                        };

                        action.spell_context = spellCtx;
                    }
                }

                // 执行当前棋子行动并结束本回合
                env.ApplyAction(action);
                env.EndTurn();

                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 开始下一回合：内部调用 Env.BeginTurn。
        /// 通信侧典型调用顺序为：NextTurn -> GetStateJson -> ExecuteAction。
        /// </summary>
        public void NextTurn()
        {
            if (env == null) throw new InvalidOperationException("Engine not initialized.");
            if (!env.isBattleInitialized || env.isGameOver) return;

            env.BeginTurn();
        }

        public bool IsGameOver()
        {
            if (env == null) return true;
            return env.isGameOver;
        }

        /// <summary>
        /// 简单胜者判定：player1 全灭则 2 胜，player2 全灭则 1 胜，双方都存活或都死则 -1（平局或未结束）。
        /// </summary>
        public int GetWinner()
        {
            if (env == null) return -1;

            bool p1Alive = env.player1.pieces.Any(p => p.is_alive);
            bool p2Alive = env.player2.pieces.Any(p => p.is_alive);

            if (p1Alive && !p2Alive) return env.player1.id;
            if (!p1Alive && p2Alive) return env.player2.id;
            return -1;
        }

        public string GetReplayJson()
        {
            if (env == null || env.logdata == null) return "{}";
            return env.logdata.ToJson();
        }

        // =================== 内部辅助 ===================

        private static PieceDto ConvertPiece(Piece p)
        {
            return new PieceDto
            {
                health = p.health,
                max_health = p.max_health,
                physical_resist = p.physical_resist,
                magic_resist = p.magic_resist,
                physical_damage = p.physical_damage,
                magic_damage = p.magic_damage,
                action_points = p.action_points,
                max_action_points = p.max_action_points,
                spell_slots = p.spell_slots,
                max_spell_slots = p.max_spell_slots,
                movement = p.movement,
                max_movement = p.max_movement,
                id = p.id,
                strength = p.strength,
                dexterity = p.dexterity,
                intelligence = p.intelligence,
                position = new PointDto { x = p.position.x, y = p.position.y },
                height = p.height,
                attack_range = p.attack_range,
                // 当前 Piece 没有显式 spell_list，先留空
                deathRound = p.deathRound,
                team = p.team,
                queue_index = p.queue_index,
                is_alive = p.is_alive,
                is_in_turn = p.is_in_turn,
                is_dying = p.is_dying,
                spell_range = p.spell_range
            };
        }

        private static BoardDto ConvertBoard(Board b)
        {
            var dto = new BoardDto
            {
                width = b.width,
                height = b.height,
                boarder = b.boarder
            };

            for (int x = 0; x < b.width; x++)
            {
                for (int y = 0; y < b.height; y++)
                {
                    var cell = b.grid[x, y];
                    dto.grid.Add(new CellDto
                    {
                        state = cell.state,
                        playerId = cell.playerId,
                        pieceId = cell.pieceId
                    });

                    dto.height_map.Add(b.height_map[x, y]);
                }
            }

            return dto;
        }

        private static SpellContextDto ConvertSpellContext(SpellContext ctx)
        {
            return new SpellContextDto
            {
                caster = ctx.caster?.id ?? -1,
                spellID = ctx.spell.id,
                targetType = (int)ctx.targetType,
                target = ctx.target?.id ?? -1,
                targetArea = ctx.targetArea == null
                    ? null
                    : new AreaDto
                    {
                        x = ctx.targetArea.x,
                        y = ctx.targetArea.y,
                        radius = ctx.targetArea.radius
                    },
                spellLifespan = ctx.spellLifespan
            };
        }

    }
}
