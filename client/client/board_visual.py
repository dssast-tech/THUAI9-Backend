"""
本地模式（local_client / Environment.mode==0）下的棋盘彩色终端输出。
使用 colorama；本模块仅在该分支被 env 懒加载，main.py（Saiblo）路径不会 import 此处。
"""
from colorama import init, Fore, Back, Style

init(autoreset=True)


def visualize_board(env) -> None:
    """与 env.Environment.visualize_board 相同布局，带颜色（仅依赖 env 的公开字段）。"""
    print("\n当前棋盘:")
    print("   ", end="")
    for x in range(env.board.width):
        print(f"{x:2d} ", end="")
    print("\n")

    for y in range(env.board.height):
        print(f"{y:2d} ", end="")
        for x in range(env.board.width):
            cell = env.board.grid[x][y]
            if cell.state == 2:
                piece = next((p for p in env.action_queue if p.id == cell.piece_id), None)
                if piece:
                    if piece.team == 1:
                        print(f"{Fore.RED}{piece.id:2d} ", end="")
                    else:
                        print(f"{Fore.BLUE}{piece.id:2d} ", end="")
                else:
                    print("X  ", end="")
            elif cell.state == -1:
                print(f"{Fore.WHITE}{Back.BLACK}## ", end="")
            else:
                print(f"{Fore.GREEN}{cell.state:2d} ", end="")
        print(Style.RESET_ALL)
    print()
