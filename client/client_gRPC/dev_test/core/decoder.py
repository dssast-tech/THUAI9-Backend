from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Point3D:
    x: int
    y: int
    z: int


@dataclass
class SoldierInfo:
    ID: int
    soldierType: str
    camp: str
    position: Point3D
    stats: Dict[str, Any]


@dataclass
class ActionStep:
    actionType: str
    soldierId: int
    path: List[Point3D]
    damageDealt: List[Dict[str, Any]]


class GameDataDecoder:
    """从 JSON 游戏日志解码成可视化/引擎可用的结构。"""

    @staticmethod
    def decode_mapdata(raw: Dict[str, Any]) -> Dict[str, Any]:
        if 'mapdata' not in raw:
            raise KeyError('缺失 mapdata 字段')

        mapdata = raw['mapdata']
        return {
            'width': mapdata.get('mapWidth'),
            'height': len(mapdata.get('rows', [])),
            'rows': [r.get('row', []) for r in mapdata.get('rows', [])]
        }

    @staticmethod
    def decode_soldiers(raw: Dict[str, Any]) -> List[SoldierInfo]:
        soldiers = []
        for item in raw.get('soldiersData', []):
            pos = item.get('position', {})
            soldiers.append(SoldierInfo(
                ID=item.get('ID', -1),
                soldierType=item.get('soldierType', ''),
                camp=item.get('camp', ''),
                position=Point3D(x=int(pos.get('x', 0)), y=int(pos.get('y', 0)), z=int(pos.get('z', 0))),
                stats=item.get('stats', {})
            ))
        return soldiers

    @staticmethod
    def decode_rounds(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        rounds = []
        for r in raw.get('gameRounds', []):
            actions = []
            for a in r.get('actions', []) or []:
                action_path = a.get('path')
                if not action_path:
                    action_path = []
                path = [Point3D(x=int(p.get('x', 0)), y=int(p.get('y', 0)), z=int(p.get('z', 0))) for p in action_path]
                damage_dealt = a.get('damageDealt') if isinstance(a.get('damageDealt'), list) else []
                actions.append(
                    ActionStep(
                        actionType=a.get('actionType', ''),
                        soldierId=a.get('soldierId', -1),
                        path=path,
                        damageDealt=damage_dealt,
                    )
                )
            rounds.append(
                {
                    'roundNumber': r.get('roundNumber', -1),
                    'actions': actions,
                    'stats': r.get('stats', []),
                }
            )
        return rounds

    @staticmethod
    def decode(raw: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError('游戏数据结构必须为字典')
        return {
            'map': GameDataDecoder.decode_mapdata(raw),
            'players': raw.get('playerData', {}),
            'soldiers': GameDataDecoder.decode_soldiers(raw),
            'rounds': GameDataDecoder.decode_rounds(raw)
        }

