"""可复用 UI 组件定义。

本文件只放可复用的界面组件，不放具体业务逻辑：
1. 信息展示框（标题 + 文本展示区）
2. 统一风格按钮区（纵向按钮列表）
3. 棋盘绘制组件（20x20 正方形网格）
4. 玩家信息卡片（摘要分块 + 悬停详情）
5. 右侧上方复合区域（几何分区示意）
"""

from __future__ import annotations

import os
import tkinter as tk
from collections.abc import Callable
from typing import Any, Sequence
from tkinter import ttk


class InfoPanel(ttk.LabelFrame):
	"""通用信息展示面板。

	该组件用于显示文本信息，例如：
	- 对局状态
	- 日志摘要
	- 回合信息
	- 调试提示

	参数说明：
	- parent: 父容器
	- title: 面板标题
	- height: 期望高度（像素），通过禁止自动收缩来保证预留区域可见
	"""

	def __init__(self, parent: tk.Misc, title: str, height: int = 180) -> None:
		super().__init__(parent, text=title, padding=10)

		# 固定预留高度，防止内容较少时区域被压缩到几乎不可见。
		self.configure(height=height)
		self.pack_propagate(False)

		# 文本框用于展示可滚动信息，默认只读。
		self.text = tk.Text(self, wrap="word", font=("Microsoft YaHei UI", 10), relief="flat")
		self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
		self.text.configure(yscrollcommand=self.scrollbar.set)

		self._tag_default = "log_default"
		self._tag_system = "log_system"
		self._tag_player = "log_player"
		self._tag_round = "log_round"
		self._tag_important = "log_important"
		self.text.tag_configure(self._tag_default, foreground="#111111")
		self.text.tag_configure(self._tag_system, foreground="#6b7280")
		self.text.tag_configure(self._tag_player, foreground="#111111")
		self.text.tag_configure(self._tag_round, foreground="#f97316")
		self.text.tag_configure(self._tag_important, foreground="#dc2626")

		self.text.pack(side="left", fill="both", expand=True)
		self.scrollbar.pack(side="right", fill="y")

		# 初始设置为只读，避免用户误编辑展示内容。
		self.set_readonly(True)

	def set_content(self, content: str) -> None:
		"""覆盖式写入内容，用于刷新展示文本。"""
		self.set_readonly(False)
		self.text.delete("1.0", "end")
		self._insert_colored(content)
		self.set_readonly(True)

	def append_content(self, content: str) -> None:
		"""追加内容，用于持续输出日志或状态流。"""
		self.set_readonly(False)
		self._insert_colored(content)
		self.text.see("end")
		self.set_readonly(True)

	def _insert_colored(self, content: str) -> None:
		for line in content.splitlines(keepends=True):
			tag = self._pick_tag(line)
			self.text.insert("end", line, (tag,))

	def _pick_tag(self, line: str) -> str:
		line_lower = line.lower()
		if any(keyword in line for keyword in ("对局结束", "游戏结束", "已死亡", "死亡", "胜者", "已暂停", "濒死", "死亡检定")):
			return self._tag_important
		if "[deathcheck]" in line_lower:
			return self._tag_important
		if "game_over" in line_lower:
			return self._tag_important
		if "[公式]" in line:
			return self._tag_system
		if "[ui]" in line_lower or "[event]" in line_lower:
			return self._tag_system
		if "player" in line_lower:
			return self._tag_player
		if "回合" in line:
			return self._tag_round
		return self._tag_default

	def set_readonly(self, readonly: bool = True) -> None:
		"""切换文本框是否可编辑。"""
		self.text.configure(state="disabled" if readonly else "normal")


class ButtonPanel(ttk.LabelFrame):
	"""通用按钮面板。

	通过传入按钮配置列表快速生成统一风格的按钮区域，
	便于在主界面中复用并集中管理控件样式。
	"""

	def __init__(
		self,
		parent: tk.Misc,
		title: str,
		buttons: Sequence[tuple[str, Callable[[], None] | None]],
	) -> None:
		super().__init__(parent, text=title, padding=10)

		# 纵向布局按钮，每个按钮占满一行，保持视觉整齐。
		self.columnconfigure(0, weight=1)

		for row_idx, (label, command) in enumerate(buttons):
			# 当未提供回调时，使用空函数占位，避免类型与运行时报错。
			safe_command = command if command is not None else (lambda: None)
			btn = ttk.Button(self, text=label, command=safe_command)
			btn.grid(row=row_idx, column=0, sticky="ew", pady=(0, 8))


class HoverTip:
	"""悬停提示弹窗。

	用于在鼠标停留时弹出详细信息，鼠标移出后自动关闭。
	这里使用 Toplevel 而不是 Tooltip 库，避免额外依赖，便于后续项目内复用。
	"""

	def __init__(self, owner: tk.Widget, text: str) -> None:
		self.owner = owner
		self.text = text
		self.tip_window: tk.Toplevel | None = None
		self.pinned = False

	def show(self) -> None:
		"""显示提示框。"""
		if self.tip_window is not None:
			return

		x = self.owner.winfo_rootx() + 14
		y = self.owner.winfo_rooty() + self.owner.winfo_height() + 8

		self.tip_window = tk.Toplevel(self.owner)
		self.tip_window.wm_overrideredirect(True)
		self.tip_window.wm_geometry(f"+{x}+{y}")

		# 采用简洁高对比样式，保证提示内容可读。
		label = tk.Label(
			self.tip_window,
			text=self.text,
			justify="left",
			background="#fffbe6",
			relief="solid",
			borderwidth=1,
			padx=12,
			pady=10,
			font=("Microsoft YaHei UI", 10),
			wraplength=320,
		)
		label.pack()

	def hide(self) -> None:
		"""关闭提示框。"""
		# 已固定时不随鼠标移出而隐藏。
		if self.pinned:
			return

		if self.tip_window is None:
			return
		self.tip_window.destroy()
		self.tip_window = None

	def toggle_pin(self) -> None:
		"""切换固定状态。

		- 第一次点击：固定并显示详细信息
		- 第二次点击：取消固定并关闭详细信息
		"""
		if not self.pinned:
			self.pinned = True
			self.show()
			return

		self.pinned = False
		if self.tip_window is not None:
			self.tip_window.destroy()
			self.tip_window = None


class PlayerSummaryCard(ttk.LabelFrame):
	"""玩家摘要信息卡片。

	卡片内容分为两层：
	1. 常驻展示（分块展示）：ID、棋子位置、HP
	2. 悬停展示（详细信息）：力量、敏捷、智力、武器、防具
	"""

	def __init__(
		self,
		parent: tk.Misc,
		title: str,
		player_id: str,
		position: str,
		hp: str,
		power: str,
		agility: str,
		intelligence: str,
		weapon: str,
		armor: str,
	) -> None:
		super().__init__(parent, text=title, padding=6)
		self.title_name = title

		# 目标布局：
		# 1. 卡片先分左右两栏（1:1）
		# 2. 右栏再分上下（3:5）
		# 3. 右栏下半再分左右（1:1）
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)

		root_layout = ttk.Frame(self)
		root_layout.grid(row=0, column=0, sticky="nsew")
		root_layout.columnconfigure(0, weight=1)
		root_layout.columnconfigure(1, weight=1)
		root_layout.rowconfigure(0, weight=1)

		# 左栏（完整一列）：放 ID 信息块。
		id_block, self.id_value_label = self._create_value_block(root_layout, "ID", player_id)
		id_block.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

		# 右栏：上下 3:5。
		right_column = ttk.Frame(root_layout)
		right_column.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
		right_column.columnconfigure(0, weight=1)
		right_column.rowconfigure(0, weight=3)
		right_column.rowconfigure(1, weight=5)

		# 右栏上半：棋子位置。
		position_block, self.position_value_label = self._create_value_block(right_column, "棋子位置", position)
		position_block.grid(row=0, column=0, sticky="nsew", pady=(0, 4))

		# 右栏下半：再分左右 1:1。
		right_bottom = ttk.Frame(right_column)
		right_bottom.grid(row=1, column=0, sticky="nsew")
		right_bottom.columnconfigure(0, weight=1)
		right_bottom.columnconfigure(1, weight=1)
		right_bottom.rowconfigure(0, weight=1)

		# 右下区域左格：HP。
		hp_block, self.hp_value_label = self._create_value_block(right_bottom, "HP", hp)
		hp_block.grid(row=0, column=0, sticky="nsew", padx=(0, 3))

		# 右下区域右格：详细信息按钮，放在该格子的右下角。
		action_block = ttk.LabelFrame(right_bottom, text="操作", padding=(6, 3))
		action_block.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
		action_block.columnconfigure(0, weight=1)
		action_block.rowconfigure(0, weight=1)

		detail_btn = ttk.Button(action_block, text="详细信息")
		detail_btn.grid(row=0, column=0, sticky="se")

		# 保存详细属性，初始化及后续更新会统一刷新悬停文案。
		self.power = power
		self.agility = agility
		self.intelligence = intelligence
		self.weapon = weapon
		self.armor = armor

		self._tip = HoverTip(detail_btn, "")
		self._refresh_detail_text()
		detail_btn.configure(command=self._tip.toggle_pin)
		detail_btn.bind("<Enter>", lambda _event: self._tip.show())
		detail_btn.bind("<Leave>", lambda _event: self._tip.hide())

	def _create_value_block(self, parent: ttk.Frame, title: str, value: str) -> tuple[ttk.LabelFrame, ttk.Label]:
		"""创建单个摘要信息块，并返回块与值标签引用（便于后续更新）。"""
		block = ttk.LabelFrame(parent, text=title, padding=(6, 3))
		value_label = ttk.Label(block, text=value, anchor="center", justify="center")
		value_label.pack(fill="both", expand=True)
		return block, value_label

	def _refresh_detail_text(self) -> None:
		"""根据当前字段刷新悬停详情文本。"""
		self._tip.text = (
			f"Player: {self.title_name}\n"
			f"ID: {self.id_value_label.cget('text')}\n"
			f"棋子位置: {self.position_value_label.cget('text')}\n"
			f"HP: {self.hp_value_label.cget('text')}\n"
			f"力量: {self.power}\n"
			f"敏捷: {self.agility}\n"
			f"智力: {self.intelligence}\n"
			f"武器: {self.weapon}\n"
			f"防具: {self.armor}"
		)

	def set_player_state(
		self,
		*,
		player_id: str,
		position: str,
		hp: str,
		power: str,
		agility: str,
		intelligence: str,
		weapon: str,
		armor: str,
	) -> None:
		"""更新玩家卡片状态。

		用于接收初始化/回放等流程传入的新状态并刷新：
		- 左上摘要字段
		- 悬停详细字段
		"""
		self.id_value_label.configure(text=player_id)
		self.position_value_label.configure(text=position)
		self.hp_value_label.configure(text=hp)
		self.power = power
		self.agility = agility
		self.intelligence = intelligence
		self.weapon = weapon
		self.armor = armor
		self._refresh_detail_text()


class PieceSquareCard(tk.Frame):
	"""左上信息区用的棋子信息卡片（长方形）。"""

	def __init__(self, parent: tk.Misc, width: int = 150, height: int = 120, is_large: bool = False) -> None:
		super().__init__(parent, width=width, height=height, bd=2, relief="ridge", background="#f3f4f6")
		self.is_large = is_large
		self.pack_propagate(False)

		header_font = ("Microsoft YaHei UI", 10 if is_large else 9, "bold")
		body_font = ("Microsoft YaHei UI", 9 if is_large else 8)
		small_font = ("Microsoft YaHei UI", 8 if is_large else 7)

		self.header_container = tk.Frame(self, bg="#f3f4f6")
		self.header_id_label = tk.Label(self.header_container, text="-", font=header_font, bg="#f3f4f6", fg="#111827", anchor="w")
		self.header_extra_label = tk.Label(self.header_container, text="", font=header_font, bg="#f3f4f6", fg="#111827", anchor="w")
		self.status_label = tk.Label(self, text="HP:-  (-,-)", font=body_font, bg="#f3f4f6", fg="#1f2937", anchor="w")
		self.combat_label = tk.Label(self, text="⚔️ - 🛡 - ✨️ - 🔮 -", font=body_font, bg="#f3f4f6", fg="#1f2937", anchor="w")
		self.talent_label = tk.Label(self, text="敏- 智- 力-", font=body_font, bg="#f3f4f6", fg="#1f2937", anchor="w")
		self.resource_label = tk.Label(self, text="法-/- 行-/- 移-", font=small_font, bg="#f3f4f6", fg="#334155", anchor="w")

		self.header_container.pack(fill="x", padx=6, pady=(4, 1))
		self.header_id_label.pack(side="left")
		self.header_extra_label.pack(side="left", padx=(4, 0))
		self.status_label.pack(fill="x", padx=6, pady=0)
		self.combat_label.pack(fill="x", padx=6, pady=0)
		self.talent_label.pack(fill="x", padx=6, pady=0)
		self.resource_label.pack(fill="x", padx=6, pady=(1, 6))

	def _apply_colors(self, bg: str, fg: str) -> None:
		self.configure(background=bg)
		self.header_container.configure(bg=bg)
		self.header_id_label.configure(bg=bg, fg=fg)
		self.header_extra_label.configure(bg=bg, fg=fg)
		self.status_label.configure(bg=bg, fg=fg)
		self.combat_label.configure(bg=bg, fg=fg)
		self.talent_label.configure(bg=bg, fg=fg)
		self.resource_label.configure(bg=bg, fg=fg)

	def set_piece_state(
		self,
		*,
		team: int,
		piece_no: int,
		hp: str,
		physical_resist: str,
		magic_resist: str,
		spell_slots: str,
		action_points: str,
		movement: str,
		is_selected: bool,
		position_text: str = "(-,-)",
		physical_damage: str = "-",
		magic_damage: str = "-",
		dexterity: str = "-",
		intelligence: str = "-",
		strength: str = "-",
		header_text: str | None = None,
		is_dying: bool = False,
		is_inactive: bool = False,
	) -> None:
		"""更新卡片显示信息与高亮状态。"""
		header_raw = header_text if header_text is not None else f"player{team}-{piece_no}"
		header_raw = str(header_raw)
		id_part, extra_part = header_raw, ""
		if " " in header_raw:
			id_part, extra_part = header_raw.split(" ", 1)
		self.header_id_label.configure(text=id_part)
		self.header_extra_label.configure(text=extra_part)
		self.status_label.configure(text=f"HP:{hp}  {position_text}")
		self.combat_label.configure(
			text=f"⚔️{physical_damage} 🛡{physical_resist} ✨️{magic_damage} 🔮{magic_resist}"
		)
		self.talent_label.configure(text=f"敏{dexterity} 智{intelligence} 力{strength}")
		self.resource_label.configure(text=f"法{spell_slots} 行{action_points} 移{movement}")

		if is_inactive:
			self._apply_colors("#e5e7eb", "#6b7280")
			return

		if team == 1:
			base_bg = "#fee2e2"
			base_fg = "#7f1d1d"
			focus_bg = "#fecaca"
		else:
			base_bg = "#dbeafe"
			base_fg = "#1e3a8a"
			focus_bg = "#bfdbfe"

		if is_selected:
			self._apply_colors(focus_bg, base_fg)
		else:
			self._apply_colors(base_bg, base_fg)

		if is_dying:
			# 濒死态：简写 ID 变灰，HP 行文字变深棕色。
			self.header_id_label.configure(fg="#6b7280")
			self.status_label.configure(fg="#7f1d1d")


class RightTopCompositePanel(ttk.LabelFrame):
	"""右侧上方复合区域。

	上下分布设计：
	1. 上部（固定高度）：显示 THU AI logo
	2. 下部（可变高度）：可变区，用于在不同模式下动态放置不同的内容
	   - 模型：模式切换时自动刷新此区域的子组件
	   - 可在 variable_frame 中动态添加/移除控件
	"""

	def __init__(
		self,
		parent: tk.Misc,
		title: str = "状态区",
		on_initialize: Callable[[], None] | None = None,
	) -> None:
		super().__init__(parent, text=title, padding=8)
		self.on_initialize = on_initialize

		# 上下两行布局
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=0)  # 上部 logo 固定高度
		self.rowconfigure(1, weight=1)  # 下部可变区吃满空间

		# 上部：logo 区（固定显示）
		logo_frame = ttk.LabelFrame(self, text="logo 区", padding=6)
		logo_frame.configure(height=72)
		logo_frame.grid_propagate(False)
		logo_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
		logo_frame.columnconfigure(0, weight=1)
		ttk.Label(logo_frame, text="DSSAST\nTHUAI大赛", anchor="center", justify="center", font=("Arial", 11, "bold")).pack(fill="both", expand=True)

		# 下部：可变区（容纳动态内容）
		self.variable_frame = ttk.LabelFrame(self, text="可变区", padding=6)
		self.variable_frame.grid(row=1, column=0, sticky="nsew")
		self.variable_frame.columnconfigure(0, weight=1)
		self.variable_frame.rowconfigure(0, weight=1)

		# 预留占位内容
		self._placeholder_label = ttk.Label(
			self.variable_frame,
			text="（可变区占位，后续根据模式放置内容）",
			anchor="center",
			foreground="#999999"
		)
		self._placeholder_label.pack(fill="both", expand=True)

	def clear_variable_area(self) -> None:
		"""清空可变区所有子组件。"""
		for widget in self.variable_frame.winfo_children():
			widget.pack_forget()
			widget.destroy()

	def set_variable_content(self, widget: tk.Widget) -> None:
		"""向可变区放置新的内容控件。"""
		self.clear_variable_area()
		widget.pack(fill="both", expand=True, parent=self.variable_frame)

	def _initialize(self) -> None:
		"""初始化按钮回调。

		若外部提供 on_initialize 回调，则调用外部初始化流程。
		否则回退到本地空实现，避免按钮点击报错。
		"""
		if self.on_initialize is not None:
			self.on_initialize()
			return

		# 具体数值待定：此处仅保留兜底占位行为。
		pass



class ChessboardPanel(ttk.LabelFrame):
	"""棋盘绘制组件（默认20x20，可随地图自适应）。

	设计目标：
	- 无地图数据时使用默认网格边长
	- 有地图数据时根据地图尺寸自适应网格边长
	- 绘制区域始终保持“正方形”
	- 当父容器尺寸变化时自动重绘，保证棋盘清晰且居中
	"""

	def __init__(self, parent: tk.Misc, title: str = "棋盘区域", grid_size: int = 20) -> None:
		super().__init__(parent, text=title, padding=10)

		# grid_size 表示默认棋盘边长格数。
		# 注意：不能命名为 grid_size，该名字与 Tk 内置方法同名。
		self.default_board_grid_size = max(1, int(grid_size))
		self.board_grid_size = self.default_board_grid_size

		# 使用 Canvas 承担图形绘制工作，背景设为浅色便于观察网格线。
		self.canvas = tk.Canvas(self, background="#f9f9f9", highlightthickness=0)
		self.canvas.pack(fill="both", expand=True)

		# 记录当前棋盘的绘制参数，后续若要绘制棋子可直接复用。
		self.board_origin_x = 0
		self.board_origin_y = 0
		self.board_pixel_size = 0
		self.cell_size = 0.0
		self.map_rows: list[list[int]] = []
		self.pieces: list[dict[str, Any]] = []
		self.move_target_highlight: tuple[int, int] | None = None
		self.spell_aoe_cells: list[tuple[int, int]] = []
		self.spell_aoe_color = "#f97316"
		self.trap_markers: list[dict[str, Any]] = []
		self.target_markers: list[dict[str, Any]] = []
		self.click_handler: Callable[[int | None, int | None], None] | None = None
		self._trap_image_raw: tk.PhotoImage | None = None
		self._trap_image_cache: dict[int, tk.PhotoImage] = {}

		# 监听尺寸变化：窗口拉伸时自动重绘，保持棋盘为正方形。
		self.canvas.bind("<Configure>", self._on_canvas_resize)
		self.canvas.bind("<Button-1>", self._on_canvas_click)

	def _load_trap_image_raw(self) -> tk.PhotoImage | None:
		if self._trap_image_raw is not None:
			return self._trap_image_raw
		try:
			asset_path = os.path.join(os.path.dirname(__file__), "assets", "trap_pixel.png")
			if not os.path.exists(asset_path):
				self._trap_image_raw = None
				return None
			self._trap_image_raw = tk.PhotoImage(file=asset_path)
			return self._trap_image_raw
		except Exception:
			self._trap_image_raw = None
			return None

	def _get_scaled_trap_image(self, target_px: int) -> tk.PhotoImage | None:
		target_px = int(target_px)
		if target_px <= 0:
			return None
		cached = self._trap_image_cache.get(target_px)
		if cached is not None:
			return cached
		raw = self._load_trap_image_raw()
		if raw is None:
			return None
		try:
			raw_w = int(raw.width())
			raw_h = int(raw.height())
			base = max(raw_w, raw_h)
			if base <= 0:
				return None
			ratio = float(target_px) / float(base)
			img = raw
			if ratio >= 1.0:
				zoom = max(1, int(round(ratio)))
				img = raw.zoom(zoom, zoom)
				if img.width() > int(target_px * 1.3):
					sub = max(1, int(round(img.width() / target_px)))
					img = img.subsample(sub, sub)
			else:
				sub = max(1, int(round(1.0 / ratio)))
				img = raw.subsample(sub, sub)
			if img is raw:
				# 未发生缩放，仍然缓存一份，避免反复计算。
				self._trap_image_cache[target_px] = raw
				return raw
			self._trap_image_cache[target_px] = img
			return img
		except Exception:
			return None

	def set_click_handler(self, handler: Callable[[int | None, int | None], None] | None) -> None:
		"""设置棋盘点击回调。合法格返回(x,y)，非棋盘区域返回(None,None)。"""
		self.click_handler = handler

	def set_move_target_highlight(self, target: tuple[int, int] | None) -> None:
		"""设置移动目标高亮格（黄色细框）。"""
		self.move_target_highlight = target
		self._draw_board(self.canvas.winfo_width(), self.canvas.winfo_height())

	def set_spell_aoe_overlay(self, cells: list[tuple[int, int]] | None, color: str = "#f97316") -> None:
		"""设置法术 AOE 滤镜叠层。"""
		self.spell_aoe_cells = list(cells) if isinstance(cells, list) else []
		self.spell_aoe_color = str(color or "#f97316")
		self._draw_board(self.canvas.winfo_width(), self.canvas.winfo_height())

	def set_trap_markers(self, markers: list[dict[str, Any]] | None) -> None:
		"""设置陷阱标记列表，元素包含 x/y/remaining。"""
		self.trap_markers = list(markers) if isinstance(markers, list) else []
		self._draw_board(self.canvas.winfo_width(), self.canvas.winfo_height())

	def set_target_markers(self, markers: list[dict[str, Any]] | None) -> None:
		"""设置目标标记列表。

		元素最小包含：x/y（棋盘格坐标）。可选：text（默认🎯）。
		"""
		self.target_markers = list(markers) if isinstance(markers, list) else []
		self._draw_board(self.canvas.winfo_width(), self.canvas.winfo_height())

	def set_board_state(self, map_rows: list[list[int]] | None, pieces: list[dict[str, Any]] | None) -> None:
		"""设置地图与棋子状态并触发重绘。"""
		self.map_rows = map_rows if isinstance(map_rows, list) else []
		self.pieces = pieces if isinstance(pieces, list) else []

		# 地图是 15x15 时，若仍按 20x20 绘制，会在 15 处出现明显分界观感。
		# 这里按地图数据自适应边长，避免额外补出的 -1 区域形成“十字分界”。
		detected_height = len(self.map_rows)
		detected_width = 0
		for row in self.map_rows:
			if isinstance(row, list):
				detected_width = max(detected_width, len(row))
		detected_grid = max(detected_width, detected_height)
		self.board_grid_size = detected_grid if detected_grid > 0 else self.default_board_grid_size

		self._draw_board(self.canvas.winfo_width(), self.canvas.winfo_height())

	def _on_canvas_resize(self, event: tk.Event) -> None:
		"""Canvas 尺寸变化时触发重绘。"""
		self._draw_board(event.width, event.height)

	def _on_canvas_click(self, event: tk.Event) -> None:
		if self.click_handler is None:
			return
		x, y = self._canvas_to_board_xy(int(event.x), int(event.y))
		self.click_handler(x, y)

	def get_board_xy_from_root(self, root_x: int, root_y: int) -> tuple[int | None, int | None]:
		"""将屏幕绝对坐标转换为棋盘格坐标。"""
		canvas_x = int(root_x - self.canvas.winfo_rootx())
		canvas_y = int(root_y - self.canvas.winfo_rooty())
		return self._canvas_to_board_xy(canvas_x, canvas_y)

	def _canvas_to_board_xy(self, canvas_x: int, canvas_y: int) -> tuple[int | None, int | None]:
		if self.cell_size <= 0 or self.board_pixel_size <= 0:
			return None, None
		x0 = self.board_origin_x
		y0 = self.board_origin_y
		x1 = x0 + self.board_pixel_size
		y1 = y0 + self.board_pixel_size
		if not (x0 <= canvas_x < x1 and y0 <= canvas_y < y1):
			return None, None
		col = int((canvas_x - x0) / self.cell_size)
		row = int((canvas_y - y0) / self.cell_size)
		if not (0 <= col < self.board_grid_size and 0 <= row < self.board_grid_size):
			return None, None
		return col, row

	def _draw_board(self, canvas_width: int, canvas_height: int) -> None:
		"""绘制 20x20 正方形棋盘。

		关键计算：
		- board_pixel_size = min(canvas_width, canvas_height)
		  取最小边长，确保棋盘不会超出可用区域。
		- board_origin_x / board_origin_y
		  用于将棋盘在 Canvas 中居中显示。
		"""
		self.canvas.delete("all")

		if canvas_width <= 2 or canvas_height <= 2:
			return

		# 为行列号预留边距，避免上侧列号压在棋盘内部。
		padding = 8
		top_label_space = 14
		left_label_space = 10
		usable_width = max(canvas_width - 2 * padding - left_label_space, 1)
		usable_height = max(canvas_height - 2 * padding - top_label_space, 1)

		self.board_pixel_size = min(usable_width, usable_height)
		self.board_origin_x = (canvas_width - self.board_pixel_size) // 2 + left_label_space // 2
		self.board_origin_y = (canvas_height - self.board_pixel_size) // 2 + top_label_space // 2
		self.cell_size = self.board_pixel_size / self.board_grid_size

		x0 = self.board_origin_x
		y0 = self.board_origin_y
		x1 = x0 + self.board_pixel_size
		y1 = y0 + self.board_pixel_size

		# 先画格子底色。边界对齐到整数像素，减少缩放时偶发细缝。
		x_bounds = [int(round(x0 + i * self.cell_size)) for i in range(self.board_grid_size + 1)]
		y_bounds = [int(round(y0 + i * self.cell_size)) for i in range(self.board_grid_size + 1)]
		for row in range(self.board_grid_size):
			for col in range(self.board_grid_size):
				cell_value = self._get_map_value(col, row)
				# 地图高度语义：-1=不可行(灰), 0=浅绿, 1=黄棕, 2=深棕。
				if cell_value == -1:
					fill_color = "#6B7280"
				elif cell_value == 0:
					fill_color = "#B7E4C7"
				elif cell_value == 1:
					fill_color = "#B08968"
				elif cell_value == 2:
					fill_color = "#5B3A29"
				else:
					fill_color = "#6b7280"
				cx0 = x_bounds[col]
				cy0 = y_bounds[row]
				cx1 = x_bounds[col + 1]
				cy1 = y_bounds[row + 1]
				self.canvas.create_rectangle(cx0, cy0, cx1, cy1, fill=fill_color, outline="")

		# 绘制行列索引，便于地图坐标编辑。
		font_size = max(7, int(self.cell_size * 0.24))
		for col in range(self.board_grid_size):
			cx = x0 + (col + 0.5) * self.cell_size
			self.canvas.create_text(cx, max(4, y0 - 10), text=str(col), fill="#374151", font=("Microsoft YaHei UI", font_size))
		for row in range(self.board_grid_size):
			cy = y0 + (row + 0.5) * self.cell_size
			self.canvas.create_text(max(8, x0 - 8), cy, text=str(row), fill="#374151", font=("Microsoft YaHei UI", font_size))

		# 先画棋盘外框，线条稍粗，便于与内部网格区分。
		self.canvas.create_rectangle(x0, y0, x1, y1, outline="#1f2937", width=2)

		# 逐条绘制内部网格线：
		# board_grid_size=20 时，需要 19 条内部竖线 + 19 条内部横线。
		for i in range(1, self.board_grid_size):
			line_offset = i * self.cell_size

			# 线条对齐到半像素，减少缩放时偶发“粗横线/粗竖线”。
			vx = int(round(x0 + line_offset)) + 0.5
			self.canvas.create_line(vx, y0, vx, y1, fill="#9ca3af", width=1)

			hy = int(round(y0 + line_offset)) + 0.5
			self.canvas.create_line(x0, hy, x1, hy, fill="#9ca3af", width=1)

		# 法术 AOE 预览：用点状半透明滤镜覆盖范围格。
		for cell in self.spell_aoe_cells:
			if not isinstance(cell, tuple) or len(cell) != 2:
				continue
			tx, ty = int(cell[0]), int(cell[1])
			if 0 <= tx < self.board_grid_size and 0 <= ty < self.board_grid_size:
				tx0 = self.board_origin_x + tx * self.cell_size
				ty0 = self.board_origin_y + ty * self.cell_size
				tx1 = tx0 + self.cell_size
				ty1 = ty0 + self.cell_size
				self.canvas.create_rectangle(
					tx0,
					ty0,
					tx1,
					ty1,
					fill=self.spell_aoe_color,
					outline="",
					stipple="gray25",
				)

		# 移动时目标格高亮：黄色细框。
		target = self.move_target_highlight
		if target is not None:
			tx, ty = target
			if 0 <= tx < self.board_grid_size and 0 <= ty < self.board_grid_size:
				tx0 = self.board_origin_x + tx * self.cell_size
				ty0 = self.board_origin_y + ty * self.cell_size
				tx1 = tx0 + self.cell_size
				ty1 = ty0 + self.cell_size
				pad = max(1.0, self.cell_size * 0.08)
				self.canvas.create_rectangle(
					tx0 + pad,
					ty0 + pad,
					tx1 - pad,
					ty1 - pad,
					outline="#facc15",
					width=1,
				)

		self._draw_pieces()
		self._draw_target_markers()
		self._draw_trap_markers()

	def _draw_target_markers(self) -> None:
		"""在棋子格左上角绘制🎯标记。"""
		if self.cell_size <= 0:
			return
		for marker in self.target_markers:
			if not isinstance(marker, dict):
				continue
			x = marker.get("x")
			y = marker.get("y")
			text = marker.get("text", "🎯")
			if not isinstance(x, int) or not isinstance(y, int):
				continue
			if x < 0 or y < 0 or x >= self.board_grid_size or y >= self.board_grid_size:
				continue

			cx0 = self.board_origin_x + x * self.cell_size
			cy0 = self.board_origin_y + y * self.cell_size
			# 更贴近格子左上角（而不是棋子矩形）。
			pad = max(0.0, self.cell_size * 0.01)
			font_size = max(9, int(self.cell_size * 0.26))
			self.canvas.create_text(
				cx0 + pad,
				cy0 + pad,
				text=str(text or "🎯"),
				fill="#facc15",
				font=("Microsoft YaHei UI", font_size, "bold"),
				anchor="nw",
			)

	def _get_map_value(self, x: int, y: int) -> int:
		"""获取地图格值。越界或缺失时按不可行处理。"""
		if y < 0 or y >= len(self.map_rows):
			return -1
		row = self.map_rows[y]
		if not isinstance(row, list) or x < 0 or x >= len(row):
			return -1
		value = row[x]
		return value if isinstance(value, int) else -1

	def _draw_pieces(self) -> None:
		"""在对应格子绘制棋子与白字标注。"""
		if self.cell_size <= 0:
			return

		for piece in self.pieces:
			x = piece.get("x")
			y = piece.get("y")
			team = piece.get("team")
			label = piece.get("label")
			is_current = bool(piece.get("is_current", False))
			if not isinstance(x, int) or not isinstance(y, int):
				continue
			if x < 0 or y < 0 or x >= self.board_grid_size or y >= self.board_grid_size:
				continue

			cx0 = self.board_origin_x + x * self.cell_size
			cy0 = self.board_origin_y + y * self.cell_size
			cx1 = cx0 + self.cell_size
			cy1 = cy0 + self.cell_size
			if team == 1:
				piece_color = "#9F1239" if is_current else "#D62828"
			else:
				piece_color = "#1E3A8A" if is_current else "#1D4ED8"

			pad = self.cell_size * 0.12
			self.canvas.create_rectangle(
				cx0 + pad,
				cy0 + pad,
				cx1 - pad,
				cy1 - pad,
				fill=piece_color,
				outline="#111827",
				width=1,
			)

			if isinstance(label, str) and label:
				font_size = max(7, int(self.cell_size * 0.22))
				emoji_font_size = max(7, int(self.cell_size * 0.18))
				cx = (cx0 + cx1) / 2
				cy = (cy0 + cy1) / 2
				if "\n" in label:
					line1, line2 = label.split("\n", 1)
					offset_y = max(3.0, self.cell_size * 0.14)
					self.canvas.create_text(
						cx,
						cy - offset_y,
						text=line1,
						fill="#FFFFFF",
						font=("Microsoft YaHei UI", font_size, "bold"),
						justify="center",
					)
					if line2.strip():
						self.canvas.create_text(
							cx,
							cy + offset_y,
							text=line2,
							fill="#FFFFFF",
							font=("Microsoft YaHei UI", emoji_font_size, "normal"),
							justify="center",
						)
				else:
					self.canvas.create_text(
						cx,
						cy,
						text=label,
						fill="#FFFFFF",
						font=("Microsoft YaHei UI", font_size, "bold"),
						justify="center",
					)

	def _draw_trap_markers(self) -> None:
		if self.cell_size <= 0:
			return
		for marker in self.trap_markers:
			x = marker.get("x")
			y = marker.get("y")
			remaining = int(marker.get("remaining", 0))
			if not isinstance(x, int) or not isinstance(y, int) or remaining <= 0:
				continue
			if x < 0 or y < 0 or x >= self.board_grid_size or y >= self.board_grid_size:
				continue

			cx0 = self.board_origin_x + x * self.cell_size
			cy0 = self.board_origin_y + y * self.cell_size
			cx1 = cx0 + self.cell_size
			cy1 = cy0 + self.cell_size

			trap_img = self._get_scaled_trap_image(int(self.cell_size * 0.65))
			if trap_img is not None:
				self.canvas.create_image((cx0 + cx1) / 2, (cy0 + cy1) / 2, image=trap_img, anchor="center")
				font_size = max(7, int(self.cell_size * 0.2))
				pad = max(1.0, self.cell_size * 0.1)
				x_text = cx0 + pad
				y_text = cy0 + pad
				# 轻量描边：先画一层黑字做阴影，再画白字。
				self.canvas.create_text(
					x_text + 1,
					y_text + 1,
					text=str(remaining),
					fill="#111827",
					font=("Microsoft YaHei UI", font_size, "bold"),
					anchor="nw",
				)
				self.canvas.create_text(
					x_text,
					y_text,
					text=str(remaining),
					fill="#FFFFFF",
					font=("Microsoft YaHei UI", font_size, "bold"),
					anchor="nw",
				)
				continue

			size = max(6.0, self.cell_size * 0.28)
			pad = max(1.0, self.cell_size * 0.08)
			sx0 = cx0 + pad
			sy0 = cy0 + pad
			sx1 = sx0 + size
			sy1 = sy0 + size
			self.canvas.create_rectangle(sx0, sy0, sx1, sy1, fill="#111827", outline="#f59e0b", width=1)
			font_size = max(7, int(self.cell_size * 0.2))
			self.canvas.create_text(
				(sx0 + sx1) / 2,
				(sy0 + sy1) / 2,
				text=str(remaining),
				fill="#FFFFFF",
				font=("Microsoft YaHei UI", font_size, "bold"),
			)

	def reset_board_state(self) -> None:
		"""重置棋盘到初始状态。

		当前版本的棋盘仅包含网格，因此重置逻辑为“清空并重绘网格”。
		后续若加入棋子/障碍绘制，可在这里统一清理并恢复初始局面。
		"""
		self.map_rows = []
		self.pieces = []
		self.trap_markers = []
		self.target_markers = []
		self.spell_aoe_cells = []
		self.move_target_highlight = None
		self.board_grid_size = self.default_board_grid_size
		self._draw_board(self.canvas.winfo_width(), self.canvas.winfo_height())