"""主界面入口。

该文件只负责“界面装配”：
1. 创建主窗口
2. 按 2:1 划分左右区域
3. 调用 components.py 中的可复用组件完成基础布局
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Optional
import numpy as np

import os
import sys
import copy
from types import SimpleNamespace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from env import ActionSet, Area, AttackContext, Environment, PieceArg, Player, Point, SpellContext, SpellFactory
from logic.controller import Controller
from core.events import EventType

from components import (
	ButtonPanel,
	ChessboardPanel,
	InfoPanel,
	PieceSquareCard,
	PlayerSummaryCard,
	RightTopCompositePanel,
)


class MainUI:
	"""测试后端逻辑用的基础界面。

	当前阶段目标：
	- 完成窗口基础骨架
	- 预留左上信息展示区域
	- 预留右侧按键区与信息展示区
	"""

	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("THUAI9 后端逻辑测试 UI")
		# 初始化状态基线：用于“初始化”按钮一键恢复。
		# 具体数值待定
		self.initial_player1_state = {
			"player_id": "P1",
			"position": "(3, 7)",
			"hp": "100",
			"power": "18",
			"agility": "12",
			"intelligence": "9",
			"weapon": "长枪",
			"armor": "轻甲",
		}
		# 具体数值待定
		self.initial_player2_state = {
			"player_id": "P2",
			"position": "(14, 11)",
			"hp": "95",
			"power": "14",
			"agility": "16",
			"intelligence": "11",
			"weapon": "弓",
			"armor": "中甲",
		}
		# 折中布局：适度增加默认宽度，给右侧信息区更多范围。
		# 同时配合最小尺寸约束，保证左侧棋盘在较小窗口下也能完整显示。
		self.root.geometry("1280x900")
		self.root.minsize(1200, 760)

		# 主容器填满整个窗口，并作为左右分栏的承载层。
		main_container = ttk.Frame(self.root, padding=12)
		main_container.pack(fill="both", expand=True)

		# 将左右列改为更接近 1:1，整体收窄左侧信息区与棋盘区宽度。
		main_container.columnconfigure(0, weight=6)
		main_container.columnconfigure(1, weight=6)
		main_container.rowconfigure(0, weight=1)

		left_frame = ttk.Frame(main_container)
		right_frame = ttk.Frame(main_container)
		left_frame.configure(width=620)
		left_frame.grid_propagate(False)

		left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
		right_frame.grid(row=0, column=1, sticky="nsew")

		self.controller = Controller(mode="manual")
		self.loaded = False
		self.running = False
		self.loop_job: Optional[str] = None
		self.replay_speed_ms = 1000
		self.replay_speed_var = tk.IntVar(value=self.replay_speed_ms)
		self.replay_round_var = tk.IntVar(value=0)
		self.replay_controls_visible = False
		self.replay_play_pause_button: ttk.Button | None = None
		self.selected_source = "runtime_custom"
		self.selected_mock_dataset: Optional[str] = None
		self.mock_initial_positions: dict[int, dict[str, Any]] = {}
		self.mock_piece_stats_by_id: dict[int, dict[str, Any]] = {}
		self.mock_last_health_by_id: dict[int, int] = {}
		self.mock_last_positions_by_id: dict[int, tuple[int, int]] = {}
		self.mock_piece_number_by_id: dict[int, int] = {}
		self.attribute_settings_window: tk.Toplevel | None = None
		self.attribute_settings_content_frame: ttk.LabelFrame | None = None
		self.attribute_settings_nav_buttons: dict[str, ttk.Button] = {}
		self.attribute_piece_vars: dict[str, dict[str, tk.StringVar]] = {}
		self.attribute_piece_entries: dict[str, dict[str, tk.Entry]] = {}
		self.attribute_piece_last_edit_tick: dict[str, int] = {}
		self.attribute_edit_tick_counter = 0
		self.attribute_internal_update = False
		self.attribute_piece_apply_status_label: ttk.Label | None = None
		self.attribute_piece_apply_status_job: Optional[str] = None
		self.attribute_piece_warning_label: ttk.Label | None = None
		self.attribute_piece_warning_job: Optional[str] = None
		self.attribute_piece_hp_hint_widgets: dict[str, tuple[tk.Label, tk.Label]] = {}
		self.attribute_action_apply_status_label: ttk.Label | None = None
		self.attribute_action_warning_label: ttk.Label | None = None
		self.attribute_action_attack_vars: dict[str, tk.Variable] = {}
		self.attribute_action_attack_defaults: dict[str, Any] = {}
		self.attribute_action_spell_enable_vars: dict[int, tk.BooleanVar] = {}
		self.attribute_action_spell_vars: dict[int, dict[str, tk.StringVar]] = {}
		self.action_settings_snapshot: dict[str, Any] = {}
		self.action_attribute_internal_update = False
		self._action_attribute_dirty_trace_bound = False
		self.attribute_map_x_var = tk.StringVar(value="")
		self.attribute_map_y_var = tk.StringVar(value="")
		self.attribute_map_height_var = tk.StringVar(value="")
		self.attribute_map_height_color_canvas: tk.Canvas | None = None
		self.attribute_map_height_var.trace_add("write", lambda *_args: self._update_map_height_preview())
		self.attribute_map_apply_status_label: ttk.Label | None = None
		self.attribute_map_pick_waiting = False
		self.attribute_map_pick_overlay: tk.Toplevel | None = None
		self.attribute_map_pick_invalid_popup: tk.Toplevel | None = None
		self.attribute_settings_force_init_mode = False
		self.runtime_init_config_ready = False
		self.runtime_piece_init_config: dict[str, dict[str, Any]] = {}
		self.runtime_piece_slot_binding: dict[int, str] = {}
		self._profession_derived_cache: dict[tuple[int, int, int, int, int], dict[str, str]] = {}
		self.mock_map_height_overrides: dict[tuple[int, int], int] = {}
		self.runtime_card_slots: list[dict[str, Any]] = []
		self.mock_card_slots: list[dict[str, Any]] = []
		self.runtime_initiative_snapshot: list[dict[str, Any]] = []
		self.pending_actions_by_piece_id: dict[int, ActionSet] = {}
		self.action_ui_mode = tk.StringVar(value="move")
		self.action_move_piece_var = tk.StringVar(value="当前棋子")
		self.action_move_x_var = tk.StringVar(value="")
		self.action_move_y_var = tk.StringVar(value="")
		self.action_move_x_var.trace_add("write", lambda *_args: self._refresh_board_view())
		self.action_move_y_var.trace_add("write", lambda *_args: self._refresh_board_view())
		self.action_attack_target_var = tk.StringVar(value="")
		self.action_attack_type_var = tk.StringVar(value="")
		self.action_custom_damage_var = tk.StringVar(value="10")
		self.action_custom_preview_var = tk.StringVar(value="")
		self.action_spell_target_var = tk.StringVar(value="")
		self.action_spell_type_var = tk.StringVar(value="")
		self.action_spell_point_x_var = tk.StringVar(value="")
		self.action_spell_point_y_var = tk.StringVar(value="")
		self.action_spell_option_map: dict[str, Any] = {}
		self.action_spell_target_option_map: dict[str, Any] = {}
		self.action_detail_container: ttk.Frame | None = None
		self.action_mode_body_container: ttk.Frame | None = None
		self.action_confirm_button: ttk.Button | None = None
		self.action_feedback_label: ttk.Label | None = None
		self.action_feedback_clear_job: Optional[str] = None
		self._rendering_action_mode_body = False
		self.action_panel_status_label: ttk.Label | None = None
		self.action_attack_target_var.trace_add("write", lambda *_args: self._refresh_custom_attack_preview())
		self.action_attack_target_var.trace_add("write", lambda *_args: self._refresh_board_view())
		self.action_attack_type_var.trace_add("write", lambda *_args: self._refresh_board_view())
		self.action_custom_damage_var.trace_add("write", lambda *_args: self._refresh_custom_attack_preview())
		self.action_spell_type_var.trace_add("write", lambda *_args: self._rerender_spell_mode_if_needed())
		self.action_spell_target_var.trace_add("write", lambda *_args: self._refresh_board_view())
		self.action_spell_point_x_var.trace_add("write", lambda *_args: self._refresh_board_view())
		self.action_spell_point_y_var.trace_add("write", lambda *_args: self._refresh_board_view())
		self.game_over_dialog_shown = False
		self.game_over_message_shown = False
		self.runtime_cycle_done_piece_ids: set[int] = set()
		self.runtime_completed_turns = 0
		self.runtime_last_round_info_line = ""
		self.action_move_pick_waiting = False
		self.action_move_pick_overlay: tk.Toplevel | None = None
		self.action_pick_mode = ""
		self.runtime_trap_effects: list[dict[str, Any]] = []

		self.controller.event_bus.subscribe(EventType.GAME_LOADED, self._on_event_game_loaded)
		self.controller.event_bus.subscribe(EventType.ROUND_STARTED, self._on_event_round_started)
		self.controller.event_bus.subscribe(EventType.ROUND_FINISHED, self._on_event_round_finished)
		self.controller.event_bus.subscribe(EventType.GAME_OVER, self._on_event_game_over)

		self._build_left_side(left_frame)
		self._build_right_side(right_frame)
		self.root.after(100, self._startup_load_with_source_dialog)

	def _normalize_selected_source_value(self, value: str) -> str:
		"""兼容旧值：将 runtime 归一到 runtime_custom。"""
		value_norm = str(value or "").strip().lower()
		if value_norm == "runtime":
			return "runtime_custom"
		if value_norm in ("runtime_custom", "runtime_profession", "mock"):
			return value_norm
		return "runtime_custom"

	def _is_runtime_selected_source(self) -> bool:
		return self._normalize_selected_source_value(self.selected_source) in ("runtime_custom", "runtime_profession")

	def _is_profession_mode(self) -> bool:
		return self._normalize_selected_source_value(self.selected_source) == "runtime_profession"

	def _weapon_label_to_weapon_id(self, weapon_label: str) -> int:
		label = str(weapon_label or "").strip()
		if label in ("长剑", "长"):
			return 1
		if label in ("短剑", "短剑🗡", "🗡", "短"):
			return 2
		if label == "弓":
			return 3
		if label == "法杖":
			return 4
		return 0

	def _armor_label_to_armor_id(self, armor_label: str) -> int:
		label = str(armor_label or "").strip()
		if label == "轻甲":
			return 1
		if label == "中甲":
			return 2
		if label == "重甲":
			return 3
		return 0

	def _weapon_id_to_weapon_label(self, weapon_id: int) -> str:
		wid = int(weapon_id)
		if wid == 1:
			return "长剑"
		if wid == 2:
			return "短剑"
		if wid == 3:
			return "弓"
		if wid == 4:
			return "法杖"
		return "自定义"

	def _armor_id_to_armor_label(self, armor_id: int) -> str:
		aid = int(armor_id)
		if aid == 1:
			return "轻甲"
		if aid == 2:
			return "中甲"
		if aid == 3:
			return "重甲"
		return "无甲"

	def _normalize_weapon_label(self, weapon_label: str) -> str:
		label = str(weapon_label or "").strip()
		if label in ("0", "自定义", "None"):
			return "自定义"
		if label == "长枪":
			return "长剑"
		if label == "短剑🗡":
			return "短剑"
		if label == "🗡":
			return "短剑"
		return label

	def _weapon_id_to_profession_display(self, weapon_id: int) -> str:
		wid = int(weapon_id)
		if wid == 1:
			return "战士(长)"
		if wid == 2:
			return "战士(短)"
		if wid == 3:
			return "射手"
		if wid == 4:
			return "法师"
		return "自定义"

	def _weapon_id_to_profession_label_simple(self, weapon_id: int) -> str:
		wid = int(weapon_id)
		if wid in (1, 2):
			return "战士"
		if wid == 3:
			return "射手"
		if wid == 4:
			return "法师"
		return "自定义"

	def _get_talent_total_cap(self) -> int:
		"""天赋总和上限（读取后端 env 的变量，避免 UI 写死常数）。"""
		env = getattr(self.controller, "environment", None)
		if env is not None:
			for player_attr in ("player1", "player2"):
				player = getattr(env, player_attr, None)
				cap = getattr(player, "feature_total", None) if player is not None else None
				try:
					cap_int = int(cap)
				except Exception:
					cap_int = 0
				if cap_int > 0:
					return cap_int
		try:
			cap_int = int(getattr(Player(), "feature_total", 0))
			if cap_int > 0:
				return cap_int
		except Exception:
			pass
		# 极端兜底：若后端结构变化导致无法读取，仍给出一个可用值。
		return 30

	def _parse_talent_int(self, raw: Any) -> int | None:
		text = str(raw if raw is not None else "").strip()
		if text in ("", "-", "-1", "None"):
			return None
		try:
			value = int(text)
		except Exception:
			return None
		return value if value >= 0 else None

	def _is_profession_slot_active_from_vars(self, vars_dict: dict[str, tk.StringVar] | None) -> bool:
		if not vars_dict:
			return False
		strength = self._parse_talent_int(vars_dict.get("strength").get() if vars_dict.get("strength") else None)
		dexterity = self._parse_talent_int(vars_dict.get("dexterity").get() if vars_dict.get("dexterity") else None)
		intelligence = self._parse_talent_int(vars_dict.get("intelligence").get() if vars_dict.get("intelligence") else None)
		if strength is None or dexterity is None or intelligence is None:
			return False
		cap = self._get_talent_total_cap()
		return (strength + dexterity + intelligence) <= cap

	def _is_profession_slot_active_from_cfg(self, cfg: dict[str, Any] | None) -> bool:
		if not cfg:
			return False
		strength = self._parse_talent_int(cfg.get("strength"))
		dexterity = self._parse_talent_int(cfg.get("dexterity"))
		intelligence = self._parse_talent_int(cfg.get("intelligence"))
		if strength is None or dexterity is None or intelligence is None:
			return False
		cap = self._get_talent_total_cap()
		return (strength + dexterity + intelligence) <= cap

	def _compute_equipment_only_stats(
		self,
		*,
		weapon_id: int,
		armor_id: int,
		strength: int | None = None,
		dexterity: int | None = None,
	) -> dict[str, str]:
		"""仅按武器/护甲更新对应数值，用于自定义模式。
		- 物伤/法伤/物抗/法抗：完全由装备决定
		- 移动力：若提供 strength/dexterity，则按后端公式 base + 护甲修正计算；否则不返回 movement
		"""
		physical_damage, magic_damage = 6, 6
		if int(weapon_id) == 1:
			physical_damage, magic_damage = 18, 0
		elif int(weapon_id) == 2:
			physical_damage, magic_damage = 24, 0
		elif int(weapon_id) == 3:
			physical_damage, magic_damage = 16, 0
		elif int(weapon_id) == 4:
			physical_damage, magic_damage = 0, 22

		physical_resist, magic_resist = 6, 6
		if int(armor_id) == 1:
			physical_resist, magic_resist = 8, 10
		elif int(armor_id) == 2:
			physical_resist, magic_resist = 15, 13
		elif int(armor_id) == 3:
			physical_resist, magic_resist = 23, 17

		result = {
			"physical_damage": str(int(physical_damage)),
			"magic_damage": str(int(magic_damage)),
			"physical_resist": str(int(physical_resist)),
			"magic_resist": str(int(magic_resist)),
		}
		if strength is not None and dexterity is not None:
			move_delta = 0.0
			if int(armor_id) == 1:
				move_delta = 3.0
			elif int(armor_id) == 3:
				move_delta = -3.0
			base_move = float(dexterity) + 0.5 * float(strength) + 10.0
			movement = max(0.0, base_move + move_delta)
			result["movement"] = f"{float(movement):.1f}".rstrip("0").rstrip(".")
		return result

	def _update_custom_mode_equipment_presets(self, slot_key: str, *, update_stats: bool) -> None:
		"""自定义模式：职业随武器变化且只读显示。
		- update_stats=True: 覆盖更新装备对应的附带属性值（物伤/法伤/物抗/法抗），但不锁死字段。
		- update_stats=False: 仅刷新职业显示，不改数值（避免打开窗口时覆盖玩家手调值）。
		"""
		if self._is_profession_mode():
			return
		vars_dict = self.attribute_piece_vars.get(slot_key)
		if not vars_dict:
			return
		weapon_label = self._normalize_weapon_label(str(vars_dict.get("weapon").get()).strip()) if vars_dict.get("weapon") else "自定义"
		armor_label = str(vars_dict.get("armor").get()).strip() if vars_dict.get("armor") else "无甲"
		weapon_id = self._weapon_label_to_weapon_id(weapon_label)
		armor_id = self._armor_label_to_armor_id(armor_label)

		profession_var = vars_dict.get("profession")
		if profession_var is not None:
			desired = self._weapon_id_to_profession_label_simple(weapon_id)
			if str(profession_var.get()).strip() != desired:
				self.attribute_internal_update = True
				try:
					profession_var.set(desired)
				finally:
					self.attribute_internal_update = False

		if update_stats:
			strength = self._safe_int(str(vars_dict.get("strength").get()).strip(), 10) if vars_dict.get("strength") else 10
			dexterity = self._safe_int(str(vars_dict.get("dexterity").get()).strip(), 10) if vars_dict.get("dexterity") else 10
			presets = self._compute_equipment_only_stats(
				weapon_id=weapon_id,
				armor_id=armor_id,
				strength=strength,
				dexterity=dexterity,
			)
			self.attribute_internal_update = True
			try:
				for key, value in presets.items():
					var = vars_dict.get(key)
					if var is not None:
						var.set(str(value))
			finally:
				self.attribute_internal_update = False

	def _update_equipment_dependent_fields(self, slot_key: str) -> None:
		if self._is_profession_mode():
			self._update_profession_display_and_presets(slot_key)
		else:
			self._update_custom_mode_equipment_presets(slot_key, update_stats=False)

	def _compute_custom_mode_stats_via_backend(
		self,
		*,
		strength: int,
		dexterity: int,
		intelligence: int,
		weapon_label: str,
		armor_label: str,
	) -> dict[str, str]:
		"""自定义模式：用后端 env.apply_init_policy 计算派生属性，避免 UI 自己写死规则。"""
		weapon_id = self._weapon_label_to_weapon_id(self._normalize_weapon_label(weapon_label))
		armor_id = self._armor_label_to_armor_id(str(armor_label).strip() or "无甲")
		if weapon_id == 4:
			# 后端规则：法杖会强制轻甲（与职业模式保持一致）。
			armor_id = 1
		env = Environment(local_mode=True, if_log=0)
		env.create_default_board()
		arg = PieceArg()
		arg.strength = int(strength)
		arg.dexterity = int(dexterity)
		arg.intelligence = int(intelligence)
		arg.equip = Point(int(weapon_id), int(armor_id))
		arg.pos = Point(0, 0)
		policy = SimpleNamespace(piece_args=[arg])
		env.apply_init_policy(1, policy)
		piece = env.player1.pieces[0]
		movement = float(getattr(piece, "max_movement", getattr(piece, "movement", 0.0)))
		result = {
			"hp": str(int(getattr(piece, "max_health", 0))),
			"physical_resist": str(int(getattr(piece, "physical_resist", 0))),
			"magic_resist": str(int(getattr(piece, "magic_resist", 0))),
			"physical_damage": str(int(getattr(piece, "physical_damage", 0))),
			"magic_damage": str(int(getattr(piece, "magic_damage", 0))),
			"max_action_points": str(int(getattr(piece, "max_action_points", 0))),
			"action_points": str(int(getattr(piece, "action_points", 0))),
			"max_spell_slots": str(int(getattr(piece, "max_spell_slots", 0))),
			"spell_slots": str(int(getattr(piece, "spell_slots", 0))),
			"movement": f"{float(movement):.1f}".rstrip("0").rstrip("."),
		}
		return result

	def _custom_init_hp_hint_value(self, slot_key: str) -> int:
		vars_dict = self.attribute_piece_vars.get(slot_key)
		if not vars_dict:
			return 50
		strength_raw = str(vars_dict.get("strength").get()).strip() if vars_dict.get("strength") is not None else "10"
		strength = self._safe_int(strength_raw, 10)
		return int(30 + strength * 2)

	def _refresh_custom_init_hp_hint(self, slot_key: str) -> None:
		widgets = self.attribute_piece_hp_hint_widgets.get(slot_key)
		if not widgets:
			return
		vars_dict = self.attribute_piece_vars.get(slot_key)
		if not vars_dict:
			return
		hp_var = vars_dict.get("hp")
		if hp_var is None:
			return
		hp_raw = str(hp_var.get()).strip()
		should_show = bool(
			hp_raw in ("", "-", "-1")
			and self.attribute_settings_force_init_mode
			and self._normalize_selected_source_value(self.selected_source) == "runtime_custom"
		)

		# 兼容：旧实现是 (dash_label, hint_label)；新实现是 (entry, overlay, dash_label, hint_label)
		if isinstance(widgets, tuple) and len(widgets) == 2:
			dash_label, hint_label = widgets
			if should_show:
				hint_value = self._custom_init_hp_hint_value(slot_key)
				hint_label.configure(text=f" ({hint_value})")
				dash_label.grid()
				hint_label.grid()
			else:
				dash_label.grid_remove()
				hint_label.grid_remove()
			return

		entry, overlay, dash_label, hint_label = widgets
		if should_show:
			hint_value = self._custom_init_hp_hint_value(slot_key)
			hint_label.configure(text=f" ({hint_value})")
			try:
				# 覆盖在 Entry 内部左侧，不占用 Entry 内容。
				overlay.place(in_=entry, x=4, y=1, relheight=1)
			except Exception:
				pass
		else:
			try:
				overlay.place_forget()
			except Exception:
				pass

	def _one_click_fill_custom_init(self) -> None:
		"""仅用于“后端模式初始化属性窗口”：一键写入 6 棋子经典配置。"""
		if not (
			self.attribute_settings_force_init_mode
			and self._normalize_selected_source_value(self.selected_source) in ("runtime_custom", "runtime_profession")
		):
			return
		fixed_positions: dict[str, tuple[int, int]] = {
			"p1_1": (3, 8),
			"p1_2": (8, 3),
			"p1_3": (17, 4),
			"p2_1": (16, 11),
			"p2_2": (11, 16),
			"p2_3": (2, 15),
		}
		preset: dict[str, dict[str, Any]] = {
			"p1_1": {"weapon": "长剑", "armor": "重甲", "strength": 20, "dexterity": 8, "intelligence": 2},
			"p1_2": {"weapon": "弓", "armor": "轻甲", "strength": 14, "dexterity": 16, "intelligence": 0},
			"p1_3": {"weapon": "短剑", "armor": "中甲", "strength": 16, "dexterity": 12, "intelligence": 2},
			"p2_1": {"weapon": "法杖", "armor": "轻甲", "strength": 14, "dexterity": 2, "intelligence": 14},
			"p2_2": {"weapon": "短剑", "armor": "轻甲", "strength": 14, "dexterity": 14, "intelligence": 2},
			"p2_3": {"weapon": "弓", "armor": "轻甲", "strength": 14, "dexterity": 16, "intelligence": 0},
		}
		self.attribute_internal_update = True
		try:
			for slot_key in self._piece_slot_keys():
				vars_dict = self.attribute_piece_vars.get(slot_key)
				if not vars_dict:
					continue
				conf = preset.get(slot_key, {})
				px, py = fixed_positions.get(slot_key, (0, 0))
				px, py = self._clamp_piece_position(px, py)
				weapon_label = str(conf.get("weapon", "自定义"))
				armor_label = str(conf.get("armor", "无甲"))
				strength = int(conf.get("strength", 10))
				dexterity = int(conf.get("dexterity", 10))
				intelligence = int(conf.get("intelligence", 10))

				if vars_dict.get("weapon") is not None:
					vars_dict["weapon"].set(weapon_label)
				if vars_dict.get("armor") is not None:
					vars_dict["armor"].set(armor_label)
				if vars_dict.get("strength") is not None:
					vars_dict["strength"].set(str(strength))
				if vars_dict.get("dexterity") is not None:
					vars_dict["dexterity"].set(str(dexterity))
				if vars_dict.get("intelligence") is not None:
					vars_dict["intelligence"].set(str(intelligence))

				weapon_id = self._weapon_label_to_weapon_id(self._normalize_weapon_label(weapon_label))
				if vars_dict.get("profession") is not None:
					vars_dict["profession"].set(self._weapon_id_to_profession_label_simple(weapon_id))

				derived = self._compute_custom_mode_stats_via_backend(
					strength=strength,
					dexterity=dexterity,
					intelligence=intelligence,
					weapon_label=weapon_label,
					armor_label=armor_label,
				)
				for key in (
					"hp",
					"physical_resist",
					"magic_resist",
					"physical_damage",
					"magic_damage",
					"action_points",
					"max_action_points",
					"spell_slots",
					"max_spell_slots",
					"movement",
				):
					if vars_dict.get(key) is not None and key in derived:
						vars_dict[key].set(str(derived[key]))
				if vars_dict.get("pos_x") is not None:
					vars_dict["pos_x"].set(str(px))
				if vars_dict.get("pos_y") is not None:
					vars_dict["pos_y"].set(str(py))
		finally:
			self.attribute_internal_update = False

		# 自定义初始化：hp 输入必须在 0-200（不自动夹紧），超范围/非法直接阻止开局。
		if (
			self.attribute_settings_force_init_mode
			and self._is_runtime_selected_source()
			and self._normalize_selected_source_value(self.selected_source) == "runtime_custom"
			and (not self._is_profession_mode())
		):
			for slot_key in self._piece_slot_keys():
				vars_dict = self.attribute_piece_vars.get(slot_key)
				if vars_dict is None:
					continue
				hp_raw = str(vars_dict.get("hp").get()).strip() if vars_dict.get("hp") is not None else ""
				if hp_raw in ("", "-", "-1"):
					continue
				try:
					hp_value = int(float(hp_raw))
				except Exception:
					slot_name = f"player{slot_key[1]}-{slot_key[-1]}"
					self._mark_attribute_field_error(slot_key, "hp")
					self._show_attribute_warning_feedback(f"{slot_name} 的血量必须是整数，且范围为 0-200")
					return
				if hp_value < 0 or hp_value > 200:
					slot_name = f"player{slot_key[1]}-{slot_key[-1]}"
					self._mark_attribute_field_error(slot_key, "hp")
					self._show_attribute_warning_feedback(f"{slot_name} 的血量超出范围：0-200")
					return

		for slot_key in self._piece_slot_keys():
			self._refresh_custom_init_hp_hint(slot_key)
		self.right_info_panel.append_content("\n[UI] 已填入经典 6 棋子配置，请点击“应用”开始")

	def _weapon_id_to_piece_type(self, weapon_id: int) -> str:
		wid = int(weapon_id)
		if wid in (1, 2):
			return "Warrior"
		if wid == 3:
			return "Archer"
		if wid == 4:
			return "Mage"
		return "Custom"

	def _compute_profession_mode_stats(
		self,
		*,
		strength: int,
		dexterity: int,
		intelligence: int,
		weapon_id: int,
		armor_id: int,
	) -> dict[str, str]:
		"""按后端 env.py 的初始化逻辑计算派生属性（字符串形式用于回填 UI）。

		说明：这里不在 UI 里复刻阈值/常数，直接调用 env.Environment.apply_init_policy
		来保证后端规则改动时测试端同步。
		"""
		cache_key = (int(strength), int(dexterity), int(intelligence), int(weapon_id), int(armor_id))
		cached = self._profession_derived_cache.get(cache_key)
		if cached is not None:
			return dict(cached)

		env = Environment(local_mode=True, if_log=0)
		env.create_default_board()
		arg = PieceArg()
		arg.strength = int(strength)
		arg.dexterity = int(dexterity)
		arg.intelligence = int(intelligence)
		arg.equip = Point(int(weapon_id), int(armor_id))
		arg.pos = Point(0, 0)
		policy = SimpleNamespace(piece_args=[arg])
		env.apply_init_policy(1, policy)
		piece = env.player1.pieces[0]

		movement = float(getattr(piece, "max_movement", getattr(piece, "movement", 0.0)))
		result = {
			"hp": str(int(getattr(piece, "max_health", 0))),
			"physical_resist": str(int(getattr(piece, "physical_resist", 0))),
			"magic_resist": str(int(getattr(piece, "magic_resist", 0))),
			"physical_damage": str(int(getattr(piece, "physical_damage", 0))),
			"magic_damage": str(int(getattr(piece, "magic_damage", 0))),
			"max_action_points": str(int(getattr(piece, "max_action_points", 0))),
			"action_points": str(int(getattr(piece, "action_points", 0))),
			"max_spell_slots": str(int(getattr(piece, "max_spell_slots", 0))),
			"spell_slots": str(int(getattr(piece, "spell_slots", 0))),
			"movement": f"{float(movement):.1f}".rstrip("0").rstrip("."),
		}
		self._profession_derived_cache[cache_key] = dict(result)
		return result

	def _update_profession_display_and_presets(self, slot_key: str) -> None:
		vars_dict = self.attribute_piece_vars.get(slot_key)
		if not vars_dict:
			return
		weapon_label = str(vars_dict.get("weapon").get()).strip() if vars_dict.get("weapon") else ""
		armor_label = str(vars_dict.get("armor").get()).strip() if vars_dict.get("armor") else ""
		weapon_id = self._weapon_label_to_weapon_id(weapon_label)
		armor_id = self._armor_label_to_armor_id(armor_label)

		# 仅职业模式：职业由武器决定；自定义模式下职业可自由编辑。
		if self._is_profession_mode():
			profession_var = vars_dict.get("profession")
			if profession_var is not None:
				profession_display = self._weapon_id_to_profession_display(weapon_id)
				if profession_var.get() != profession_display:
					self.attribute_internal_update = True
					try:
						profession_var.set(profession_display)
					finally:
						self.attribute_internal_update = False

		# 仅职业模式：法杖强制轻甲（与 env.py 规则对齐）。
		if self._is_profession_mode() and weapon_id == 4 and vars_dict.get("armor") is not None:
			if str(vars_dict["armor"].get()).strip() != "轻甲":
				self.attribute_internal_update = True
				try:
					vars_dict["armor"].set("轻甲")
				finally:
					self.attribute_internal_update = False
			armor_id = 1

		# 仅职业模式且在初始化配置阶段：自动填充派生属性（未点击“应用”前也生效）。
		if not (self._is_profession_mode() and self.attribute_settings_force_init_mode):
			return
		strength = self._parse_talent_int(vars_dict.get("strength").get() if vars_dict.get("strength") else None)
		dexterity = self._parse_talent_int(vars_dict.get("dexterity").get() if vars_dict.get("dexterity") else None)
		intelligence = self._parse_talent_int(vars_dict.get("intelligence").get() if vars_dict.get("intelligence") else None)
		if armor_id <= 0 and weapon_id in (1, 2, 3, 4):
			armor_id = 1

		derived_keys = (
			"hp",
			"physical_resist",
			"magic_resist",
			"physical_damage",
			"magic_damage",
			"max_action_points",
			"action_points",
			"max_spell_slots",
			"spell_slots",
			"movement",
		)
		if strength is None or dexterity is None or intelligence is None:
			self.attribute_internal_update = True
			try:
				for key in derived_keys:
					var = vars_dict.get(key)
					if var is not None:
						var.set("-")
			finally:
				self.attribute_internal_update = False
			return

		cap = self._get_talent_total_cap()
		if (int(strength) + int(dexterity) + int(intelligence)) > cap:
			self.attribute_internal_update = True
			try:
				for key in derived_keys:
					var = vars_dict.get(key)
					if var is not None:
						var.set("-")
			finally:
				self.attribute_internal_update = False
			return

		derived = self._compute_profession_mode_stats(
			strength=int(strength),
			dexterity=int(dexterity),
			intelligence=int(intelligence),
			weapon_id=weapon_id,
			armor_id=armor_id,
		)
		self.attribute_internal_update = True
		try:
			for key, value in derived.items():
				var = vars_dict.get(key)
				if var is not None:
					var.set(str(value))
		finally:
			self.attribute_internal_update = False

	def _sync_profession_equipment(self, slot_key: str, changed_field: str) -> None:
		"""将职业展示与属性联动到武器/护甲。职业模式=派生锁定；自定义模式=仅覆盖装备相关数值但不锁死。"""
		if changed_field not in ("weapon", "armor"):
			return
		if self._is_profession_mode():
			self._update_profession_display_and_presets(slot_key)
		else:
			# 自定义模式：只有在武器/护甲变更时才覆盖数值。
			self._update_custom_mode_equipment_presets(slot_key, update_stats=True)

	def _show_source_selection_dialog(self, title: str = "选择数据源") -> Optional[str]:
		"""弹窗选择数据源：后端玩法环境或 mock 回放。"""
		choice = {"value": None}
		# 这里是新增的独立弹窗逻辑：用 Toplevel 创建一个模式对话框。
		window = tk.Toplevel(self.root)
		window.title(title)
		window.transient(self.root)
		window.grab_set()
		window.resizable(False, False)

		frame = ttk.Frame(window, padding=12)
		frame.pack(fill="both", expand=True)

		ttk.Label(frame, text="请选择本次测试的数据源：").pack(anchor="w", pady=(0, 8))
		var = tk.StringVar(value=self._normalize_selected_source_value(self.selected_source))

		ttk.Radiobutton(frame, text="手动对局模式（自定义）", value="runtime_custom", variable=var).pack(anchor="w")
		ttk.Radiobutton(frame, text="手动对局模式（职业）", value="runtime_profession", variable=var).pack(anchor="w")
		ttk.Radiobutton(frame, text="mock数据模式", value="mock", variable=var).pack(anchor="w", pady=(0, 8))

		button_row = ttk.Frame(frame)
		button_row.pack(fill="x", pady=(8, 0))

		def on_ok() -> None:
			choice["value"] = self._normalize_selected_source_value(var.get())
			window.destroy()

		def on_cancel() -> None:
			choice["value"] = None
			window.destroy()

		ttk.Button(button_row, text="取消", command=on_cancel).pack(side="right")
		ttk.Button(button_row, text="确定", command=on_ok).pack(side="right", padx=(0, 6))

		# 将弹窗定位到主窗口中央，避免首次弹出时偏到屏幕角落。
		window.update_idletasks()
		parent_x = self.root.winfo_rootx()
		parent_y = self.root.winfo_rooty()
		parent_w = self.root.winfo_width()
		parent_h = self.root.winfo_height()
		win_w = window.winfo_width()
		win_h = window.winfo_height()
		target_x = parent_x + max((parent_w - win_w) // 2, 0)
		target_y = parent_y + max((parent_h - win_h) // 2, 0)
		window.geometry(f"+{target_x}+{target_y}")

		window.protocol("WM_DELETE_WINDOW", on_cancel)
		self.root.wait_window(window)
		return choice["value"]

	def _show_mock_dataset_dialog(self, title: str = "选择 mock 数据集") -> Optional[str]:
		"""弹窗选择 mock 数据集：用于回放不同测试样例。"""
		datasets = self.controller.list_mock_datasets()
		if not datasets:
			raise RuntimeError("当前没有可用的 mock 数据集")

		choice = {"value": None}
		# 这里是新增的第二个弹窗逻辑：当用户选择 mock 后继续细分数据集。
		window = tk.Toplevel(self.root)
		window.title(title)
		window.transient(self.root)
		window.grab_set()
		window.resizable(False, False)

		frame = ttk.Frame(window, padding=12)
		frame.pack(fill="both", expand=True)

		ttk.Label(frame, text="请选择要加载的 mock 回放数据集：").pack(anchor="w", pady=(0, 8))
		default_value = self.selected_mock_dataset if self.selected_mock_dataset in datasets else datasets[0]
		var = tk.StringVar(value=default_value)

		combo = ttk.Combobox(frame, textvariable=var, values=datasets, state="readonly", width=36)
		combo.pack(fill="x")
		combo.current(datasets.index(default_value))

		button_row = ttk.Frame(frame)
		button_row.pack(fill="x", pady=(8, 0))

		def on_ok() -> None:
			choice["value"] = var.get()
			window.destroy()

		def on_cancel() -> None:
			choice["value"] = None
			window.destroy()

		ttk.Button(button_row, text="取消", command=on_cancel).pack(side="right")
		ttk.Button(button_row, text="确定", command=on_ok).pack(side="right", padx=(0, 6))

		# 与数据源弹窗一致：数据集弹窗也保持在主窗口中央。
		window.update_idletasks()
		parent_x = self.root.winfo_rootx()
		parent_y = self.root.winfo_rooty()
		parent_w = self.root.winfo_width()
		parent_h = self.root.winfo_height()
		win_w = window.winfo_width()
		win_h = window.winfo_height()
		target_x = parent_x + max((parent_w - win_w) // 2, 0)
		target_y = parent_y + max((parent_h - win_h) // 2, 0)
		window.geometry(f"+{target_x}+{target_y}")

		window.protocol("WM_DELETE_WINDOW", on_cancel)
		self.root.wait_window(window)
		return choice["value"]

	def _startup_load_with_source_dialog(self) -> None:
		choice = self._show_source_selection_dialog("进入测试：选择数据源")
		if choice is None:
			self.right_info_panel.append_content("\n[UI] 未选择数据源，默认使用后端玩法环境")
			self.selected_source = "runtime_custom"
		else:
			self.selected_source = choice
		if self.selected_source == "mock":
			selected_dataset = self._show_mock_dataset_dialog("进入测试：选择 mock 数据集")
			if selected_dataset is not None:
				self.selected_mock_dataset = selected_dataset
			else:
				self.right_info_panel.append_content("\n[UI] 未选择 mock 数据集，保留当前未加载状态")
				return
		self._load_data_with_selected_source()

	def _load_data_with_selected_source(self) -> None:
		"""按当前 selected_source / selected_mock_dataset 直接加载，不弹模式选择框。"""
		if self.running:
			self._on_click_pause()
		# 进入新对局：清空行动面板的选点/预览状态，避免重开后目标框或火球 AOE 残留。
		self._stop_action_move_point_pick()
		self.action_ui_mode.set("move")
		self.action_move_x_var.set("")
		self.action_move_y_var.set("")
		self.action_spell_type_var.set("")
		self.action_spell_target_var.set("")
		self.action_spell_point_x_var.set("")
		self.action_spell_point_y_var.set("")
		self.action_spell_option_map = {}
		self.action_spell_target_option_map = {}
		self.runtime_card_slots = []
		self.mock_card_slots = []
		self.runtime_initiative_snapshot = []
		self.pending_actions_by_piece_id = {}
		self.runtime_cycle_done_piece_ids = set()
		self.runtime_completed_turns = 0
		self.runtime_last_round_info_line = ""
		self.game_over_dialog_shown = False
		self.game_over_message_shown = False
		self.action_panel_status_label = None
		try:
			self.controller.select_mode("manual")
			if self._is_runtime_selected_source():
				self.mock_map_height_overrides = {}
				self.controller.load_game_data(prefer_runtime=True)
				self._attach_runtime_input()
				env = self.controller.environment
				if env is not None:
					self._initialize_runtime_environment_with_initiative_capture(env, self.controller.runtime_board_file)
				self._set_runtime_board_all_walkable()
				self._refresh_board_view()
				self.runtime_init_config_ready = False
				self.runtime_piece_init_config = {}
				self.runtime_piece_slot_binding = {}
				self._prepare_runtime_piece_init_defaults()
				self._on_click_attribute_settings(force_runtime_init=True)
				if not self.runtime_init_config_ready:
					self.right_info_panel.append_content("\n[UI] 后端模式初始化配置未完成，取消加载")
					return

				if env is not None:
					self._initialize_runtime_environment_with_initiative_capture(env, self.controller.runtime_board_file)
					self._set_runtime_board_all_walkable()
					self._apply_runtime_piece_config_to_environment()
					self._initialize_runtime_card_slots()
					self._install_runtime_env_deathcheck_hook(env)
					self._check_and_announce_runtime_game_over(env, show_dialog=True)
					self._show_initiative_summary_popup()
				self.loaded = True
				self.left_board_panel.reset_board_state()
				self._initialize_mock_positions()
				self._refresh_piece_cards()
				self.root.update_idletasks()
				self._refresh_board_view()
				self._sync_replay_round_var()
				mode_desc = "后端模式（职业）" if self._is_profession_mode() else "后端模式（自定义）"
				self.right_info_panel.append_content(f"\n[UI] 已加载{mode_desc}")
				return

			if not self.selected_mock_dataset:
				self.right_info_panel.append_content("\n[UI] 缺少 mock 数据集，无法加载")
				return
			self.mock_map_height_overrides = {}
			self.controller.load_game_data(prefer_runtime=False, mock_dataset=self.selected_mock_dataset)
			self.runtime_card_slots = []
			self.mock_card_slots = []
			self.runtime_piece_slot_binding = {}
			self.loaded = True
			self.left_board_panel.reset_board_state()
			self._initialize_mock_positions()
			self._initialize_mock_card_slots()
			self._refresh_piece_cards()
			self._refresh_board_view()
			self._sync_replay_round_var()
			self.right_info_panel.append_content(f"\n[UI] 已加载 mock 模式: {self.selected_mock_dataset}")
		except Exception as e:
			self.right_info_panel.append_content(f"\n[UI] 加载失败: {e}")

	def _install_runtime_env_deathcheck_hook(self, env: Any) -> None:
		"""在不改 env.py 的前提下，为死亡检定增加 UI 可见的提示与掷骰结果。

		实现方式：运行时 monkeypatch env.roll_dice 与 env.handle_death_check，
		仅记录/展示信息，不改变任何判定分支。
		"""
		if env is None:
			return
		if bool(getattr(env, "_ui_deathcheck_hook_installed", False)):
			return

		setattr(env, "_ui_deathcheck_hook_installed", True)
		setattr(env, "_ui_in_deathcheck", False)
		setattr(env, "_ui_last_deathcheck_roll", None)

		orig_roll_dice = getattr(env, "roll_dice", None)
		orig_handle = getattr(env, "handle_death_check", None)
		if not callable(orig_roll_dice) or not callable(orig_handle):
			return

		def roll_dice_hook(n: int, sides: int):
			result = orig_roll_dice(n, sides)
			if bool(getattr(env, "_ui_in_deathcheck", False)) and int(n) == 1 and int(sides) == 20:
				try:
					setattr(env, "_ui_last_deathcheck_roll", int(result))
				except Exception:
					setattr(env, "_ui_last_deathcheck_roll", result)
			return result

		def handle_death_check_hook(target: Any):
			setattr(env, "_ui_in_deathcheck", True)
			setattr(env, "_ui_last_deathcheck_roll", None)
			try:
				return orig_handle(target)
			finally:
				setattr(env, "_ui_in_deathcheck", False)
				roll_value = getattr(env, "_ui_last_deathcheck_roll", None)
				piece_code = self._get_piece_short_code(target)
				if roll_value is None:
					self.right_info_panel.append_content(f"\n[死亡检定] {piece_code} 触发死亡检定：d20=?")
					return
				try:
					roll_int = int(roll_value)
				except Exception:
					roll_int = None

				if roll_int == 20:
					self.right_info_panel.append_content(f"\n[死亡检定] {piece_code} 掷 d20=20：恢复至 1HP")
				else:
					# 玩法文档存在“进入濒死”的期望，但当前 env 实现非 20 直接死亡。
					extra = "（当前实现：非20未进入濒死，直接死亡）" if roll_int is not None else ""
					self.right_info_panel.append_content(f"\n[死亡检定] {piece_code} 掷 d20={roll_value}{extra}")

		setattr(env, "roll_dice", roll_dice_hook)
		setattr(env, "handle_death_check", handle_death_check_hook)

	def _is_piece_alive_by_hp(self, piece: Any) -> bool:
		"""统一存活判定：仅 HP>0 视为存活；HP==0 视为死亡。

		说明：负 HP 在初始化输入阶段视为非法；在对局结算中若出现负值，这里按 0 处理。
		"""
		if piece is None:
			return False
		try:
			hp = int(getattr(piece, "health", 0))
		except Exception:
			hp = 0
		if hp < 0:
			hp = 0
		# 兼容 env 内部 is_alive 字段，但以 HP 为准。
		return hp > 0

	def _check_and_announce_runtime_game_over(self, env: Any, *, show_dialog: bool) -> None:
		"""在 UI 侧主动检查并播报胜负。

		用于：
		- 手动应用属性后（可能直接把某方全灭）
		- 初始化配置应用后（防止 0HP 开局未触发任何行动导致不结算）
		"""
		if env is None:
			return
		# 去重：若 env 或 UI 已标记结束，则不重复播报。
		if bool(getattr(env, "is_game_over", False)) or bool(getattr(self, "game_over_message_shown", False)):
			return
		p1_pieces = self._coerce_piece_list(getattr(getattr(env, "player1", None), "pieces", []))
		p2_pieces = self._coerce_piece_list(getattr(getattr(env, "player2", None), "pieces", []))
		p1_alive = any(self._is_piece_alive_by_hp(p) for p in p1_pieces)
		p2_alive = any(self._is_piece_alive_by_hp(p) for p in p2_pieces)
		if p1_alive and p2_alive:
			return
		winner = "玩家1" if p1_alive else ("玩家2" if p2_alive else "无人")
		setattr(env, "is_game_over", True)
		self.game_over_message_shown = True
		self.right_info_panel.append_content(f"\n游戏结束，胜者：{winner}")
		if show_dialog and self.controller.runtime_source == "runtime_env":
			self._show_game_over_reset_dialog()

	def _prepare_runtime_piece_init_defaults(self) -> None:
		"""准备后端模式初始化阶段的 6 槽位默认配置。"""
		if self.runtime_piece_init_config:
			return

		width = 20
		height = 20
		border = height // 2
		env = self.controller.environment
		if env is not None and getattr(env, "board", None) is not None:
			board = env.board
			width = int(getattr(board, "width", width))
			height = int(getattr(board, "height", height))
			border = int(getattr(board, "boarder", border))

		fixed_positions: dict[str, tuple[int, int]] = {
			"p1_1": (3, 8),
			"p1_2": (8, 3),
			"p1_3": (17, 4),
			"p2_1": (16, 11),
			"p2_2": (11, 16),
			"p2_3": (2, 15),
		}

		def clamp_pos(x: int, y: int) -> tuple[int, int]:
			cx = max(0, min(int(x), max(0, width - 1)))
			cy = max(0, min(int(y), max(0, height - 1)))
			return cx, cy

		for team in (1, 2):
			for idx in (1, 2, 3):
				slot_key = f"p{team}_{idx}"
				x, y = fixed_positions.get(slot_key, (0, 0))
				x, y = clamp_pos(x, y)
				if self._is_profession_mode():
					# 职业模式：天赋必须手动分配，默认空值；血量/派生属性由后端公式决定，不允许手填。
					self.runtime_piece_init_config[slot_key] = {
						"hp": "-",
						"strength": "-",
						"dexterity": "-",
						"intelligence": "-",
						"physical_resist": "-",
						"magic_resist": "-",
						"physical_damage": "-",
						"magic_damage": "-",
						"action_points": "-",
						"max_action_points": "-",
						"spell_slots": "-",
						"max_spell_slots": "-",
						"movement": "-",
						"weapon": "长剑",
						"armor": "轻甲",
						"profession": "战士(长)",
						"pos_x": str(x),
						"pos_y": str(y),
					}
				else:
					# 自定义模式默认数值：显示仍为“自定义/无甲”，但战斗属性默认对齐“长剑+中甲+天赋10”。
					self.runtime_piece_init_config[slot_key] = {
						"hp": "",
						"profession": "自定义",
						"weapon": "自定义",
						"armor": "无甲",
						"strength": "10",
						"dexterity": "10",
						"intelligence": "10",
						"physical_resist": "15",
						"magic_resist": "13",
						"physical_damage": "18",
						"magic_damage": "0",
						"action_points": "2",
						"max_action_points": "2",
						"spell_slots": "2",
						"max_spell_slots": "2",
						"movement": "25",
						"pos_x": str(x),
						"pos_y": str(y),
					}

	def _set_runtime_board_all_walkable(self) -> None:
		"""后端模式初始化前，将地图默认设置为全盘可走。"""
		env = self.controller.environment
		if env is None or getattr(env, "board", None) is None:
			return
		board = env.board
		width = int(getattr(board, "width", 0))
		height = int(getattr(board, "height", 0))
		if width <= 0 or height <= 0:
			return
		for x in range(width):
			for y in range(height):
				cell = board.grid[x][y]
				cell.state = 1
				cell.player_id = -1
				cell.piece_id = -1
		self.right_info_panel.append_content("\n[UI] 后端模式：地图已重置为全盘可走")

	def _clear_attribute_error_highlight(self) -> None:
		for slot_key, field_widgets in getattr(self, "attribute_piece_entries", {}).items():
			_ = slot_key
			for field, widget in field_widgets.items():
				is_disabled = str(widget.cget("state")) == "disabled"
				try:
					if is_disabled:
						widget.configure(fg="#9ca3af")
					else:
						widget.configure(fg="#111111")
				except Exception:
					pass
				_ = field

		# 同步清理：自定义初始化的 hp placeholder（浮空“-”）颜色。
		for slot_key, widgets in getattr(self, "attribute_piece_hp_hint_widgets", {}).items():
			_ = slot_key
			try:
				if isinstance(widgets, tuple) and len(widgets) == 4:
					_dash_label = widgets[2]
					_dash_label.configure(fg="#111111")
			except Exception:
				pass

	def _mark_hp_placeholder_error(self, slot_key: str) -> None:
		"""仅用于自定义初始化：将浮空 placeholder 的“-”标红。"""
		widgets = self.attribute_piece_hp_hint_widgets.get(slot_key)
		if not widgets:
			return
		try:
			if isinstance(widgets, tuple) and len(widgets) == 4:
				entry, overlay, dash_label, _hint_label = widgets
				# 确保 placeholder 可见，否则标红看不到。
				try:
					overlay.place(in_=entry, x=4, y=1, relheight=1)
				except Exception:
					pass
				dash_label.configure(fg="#dc2626")
				return
			if isinstance(widgets, tuple) and len(widgets) == 2:
				dash_label, _hint_label = widgets
				dash_label.configure(fg="#dc2626")
		except Exception:
			pass

	def _mark_attribute_field_error(self, slot_key: str, field: str) -> None:
		entry = getattr(self, "attribute_piece_entries", {}).get(slot_key, {}).get(field)
		if entry is None:
			return
		try:
			entry.configure(fg="#dc2626")
		except Exception:
			pass

	def _is_attribute_slot_enabled(self, slot_key: str) -> bool:
		field_widgets = getattr(self, "attribute_piece_entries", {}).get(slot_key, {})
		entry = field_widgets.get("pos_x") or field_widgets.get("hp")
		if entry is None:
			return False
		return str(entry.cget("state")) != "disabled"

	def _on_attribute_var_changed(self, slot_key: str, field: str) -> None:
		if self.attribute_internal_update:
			return
		if (
			field in ("hp", "strength")
			and self.attribute_settings_force_init_mode
			and self._normalize_selected_source_value(self.selected_source) == "runtime_custom"
		):
			self._refresh_custom_init_hp_hint(slot_key)
		if field in ("pos_x", "pos_y"):
			self.attribute_edit_tick_counter += 1
			self.attribute_piece_last_edit_tick[slot_key] = self.attribute_edit_tick_counter
			return
		if field in ("weapon", "armor"):
			self._sync_profession_equipment(slot_key, field)
			return
		if (
			self._is_profession_mode()
			and self.attribute_settings_force_init_mode
			and field in ("strength", "dexterity", "intelligence")
		):
			self._update_profession_display_and_presets(slot_key)
			return

	def _apply_runtime_piece_config_to_environment(self) -> None:
		"""将初始化配置应用到已初始化的后端环境。"""
		env = self.controller.environment
		if env is None:
			return

		runtime_map = self._runtime_piece_slot_map()
		board = getattr(env, "board", None)
		if board is not None and getattr(board, "grid", None) is not None:
			for x in range(int(getattr(board, "width", 0))):
				for y in range(int(getattr(board, "height", 0))):
					cell = board.grid[x][y]
					if int(getattr(cell, "state", 0)) == 2:
						cell.state = 1
						cell.player_id = -1
						cell.piece_id = -1

		for slot_key in self._piece_slot_keys():
			cfg = self.runtime_piece_init_config.get(slot_key, {})
			piece = runtime_map.get(slot_key)
			if piece is None:
				continue
			hp_raw = str(cfg.get("hp", "-")).strip()
			hp_value = self._safe_int(hp_raw, -1)
			if hp_raw in ("", "-", "-1") or hp_value <= 0:
				piece.is_alive = False
				piece.health = 0
				continue

			piece.is_alive = True
			piece.health = max(1, hp_value)
			piece.max_health = max(piece.health, self._safe_int(str(cfg.get("hp", piece.health)), piece.health))
			piece.strength = self._safe_int(str(cfg.get("strength", 10)), int(getattr(piece, "strength", 10)))
			piece.dexterity = self._safe_int(str(cfg.get("dexterity", 10)), int(getattr(piece, "dexterity", 10)))
			piece.intelligence = self._safe_int(str(cfg.get("intelligence", 10)), int(getattr(piece, "intelligence", 10)))
			piece.physical_resist = self._safe_int(str(cfg.get("physical_resist", 6)), int(getattr(piece, "physical_resist", 6)))
			piece.magic_resist = self._safe_int(str(cfg.get("magic_resist", 6)), int(getattr(piece, "magic_resist", 6)))
			piece.physical_damage = self._safe_int(str(cfg.get("physical_damage", 6)), int(getattr(piece, "physical_damage", 6)))
			piece.magic_damage = self._safe_int(str(cfg.get("magic_damage", 6)), int(getattr(piece, "magic_damage", 6)))
			piece.max_action_points = self._safe_int(str(cfg.get("max_action_points", 2)), int(getattr(piece, "max_action_points", 2)))
			piece.action_points = min(
				self._safe_int(str(cfg.get("action_points", 2)), int(getattr(piece, "action_points", 2))),
				int(piece.max_action_points),
			)
			piece.max_spell_slots = self._safe_int(str(cfg.get("max_spell_slots", 2)), int(getattr(piece, "max_spell_slots", 2)))
			piece.spell_slots = min(
				self._safe_int(str(cfg.get("spell_slots", 2)), int(getattr(piece, "spell_slots", 2))),
				int(piece.max_spell_slots),
			)
			piece.movement = self._safe_float(str(cfg.get("movement", 10)), float(getattr(piece, "movement", 10.0)))
			piece.max_movement = max(piece.movement, float(getattr(piece, "max_movement", piece.movement)))
			piece.position = Point(
				self._safe_int(str(cfg.get("pos_x", 0)), 0),
				self._safe_int(str(cfg.get("pos_y", 0)), 0),
			)

			weapon_label = self._normalize_weapon_label(str(cfg.get("weapon", "自定义")).strip() or "自定义")
			armor_label = str(cfg.get("armor", "无甲")).strip() or "无甲"
			weapon_id = self._weapon_label_to_weapon_id(weapon_label)
			armor_id = self._armor_label_to_armor_id(armor_label)
			# 兼容“自定义开局默认显示为自定义/无甲”：避免把初始化时的真实装备覆盖成 0/0。
			if not (
				self._normalize_selected_source_value(self.selected_source) == "runtime_custom"
				and weapon_label == "自定义"
				and armor_label == "无甲"
				and int(weapon_id) == 0
				and int(armor_id) == 0
			):
				piece.type = self._weapon_id_to_piece_type(weapon_id)
				setattr(piece, "weapon", int(weapon_id))
				setattr(piece, "armor", int(armor_id))

			if board is not None:
				x = int(piece.position.x)
				y = int(piece.position.y)
				if 0 <= x < int(getattr(board, "width", 0)) and 0 <= y < int(getattr(board, "height", 0)):
					board.grid[x][y].state = 2
					board.grid[x][y].player_id = int(getattr(piece, "team", 0))
					board.grid[x][y].piece_id = int(getattr(piece, "id", -1))

	def _auto_init_handler(self, init_message: Any):
		if self.runtime_piece_init_config:
			piece_args: list[Any] = []
			team_id = int(getattr(init_message, "id", 1))
			for idx in (1, 2, 3):
				slot_key = f"p{team_id}_{idx}"
				cfg = self.runtime_piece_init_config.get(slot_key, {})
				if self._is_profession_mode():
					strength = self._parse_talent_int(cfg.get("strength"))
					dexterity = self._parse_talent_int(cfg.get("dexterity"))
					intelligence = self._parse_talent_int(cfg.get("intelligence"))
					if strength is None or dexterity is None or intelligence is None:
						continue
					cap = self._get_talent_total_cap()
					if (strength + dexterity + intelligence) > cap:
						continue
				else:
					hp_raw = str(cfg.get("hp", "-")).strip()
					if hp_raw in ("", "-", "-1") or self._safe_int(hp_raw, -1) <= 0:
						continue
				arg = PieceArg()
				if self._is_profession_mode():
					arg.strength = int(strength)
					arg.dexterity = int(dexterity)
					arg.intelligence = int(intelligence)
				else:
					arg.strength = self._safe_int(str(cfg.get("strength", 10)), 10)
					arg.dexterity = self._safe_int(str(cfg.get("dexterity", 10)), 10)
					arg.intelligence = self._safe_int(str(cfg.get("intelligence", 10)), 10)
				weapon_raw = cfg.get("weapon", 1)
				weapon_id = self._safe_int(str(weapon_raw), 0)
				weapon_label = ""
				if weapon_id not in (1, 2, 3, 4):
					weapon_label = self._normalize_weapon_label(str(weapon_raw)) or "自定义"
					weapon_id = self._weapon_label_to_weapon_id(weapon_label)
					# 自定义模式默认：UI 显示“自定义”时，初始化仍按长剑生成（便于保持后端武器相关行为）。
					if int(weapon_id) == 0 and weapon_label == "自定义":
						weapon_id = 1
				armor_raw = cfg.get("armor", 1)
				armor_id = self._safe_int(str(armor_raw), 0)
				armor_label = ""
				if armor_id not in (1, 2, 3):
					armor_label = str(armor_raw or "无甲")
					armor_id = self._armor_label_to_armor_id(armor_label)
					# 自定义模式默认：UI 显示“无甲”时，初始化仍按中甲生成（与默认数值口径一致）。
					if int(armor_id) == 0 and armor_label == "无甲":
						armor_id = 2
				if weapon_id == 4:
					armor_id = 1
				arg.equip = Point(int(weapon_id), int(armor_id))
				arg.pos = Point(
					self._safe_int(str(cfg.get("pos_x", 0)), 0),
					self._safe_int(str(cfg.get("pos_y", 0)), 0),
				)
				piece_args.append(arg)
			if piece_args:
				return piece_args

		piece_args = []
		width = init_message.board.width
		height = init_message.board.height
		boarder = init_message.board.boarder

		candidates = []
		for y in range(height):
			if init_message.id == 1 and y >= boarder:
				continue
			if init_message.id == 2 and y <= boarder:
				continue
			for x in range(width):
				if init_message.board.grid[x][y].state == 1:
					candidates.append((x, y))

		for i in range(init_message.piece_cnt):
			x, y = candidates[i]
			arg = PieceArg()
			arg.strength = 10
			arg.dexterity = 10
			arg.intelligence = 10
			arg.equip = Point(1, 1)
			arg.pos = Point(x, y)
			piece_args.append(arg)
		return piece_args

	def _noop_action_handler(self, _env: Any) -> ActionSet:
		action = ActionSet()
		action.move = False
		action.attack = False
		action.spell = False
		return action

	def _get_runtime_current_piece(self, env: Any) -> Any:
		"""优先取 env.current_piece，缺失时回退 action_queue 队首。"""
		current_piece = getattr(env, "current_piece", None)
		if current_piece is not None and bool(getattr(current_piece, "is_alive", True)):
			if self.runtime_card_slots:
				slot_pieces = [s.get("piece") for s in self.runtime_card_slots]
				if current_piece not in slot_pieces:
					match_piece = next(
						(
							p
							for p in slot_pieces
							if int(getattr(p, "id", -1)) == int(getattr(current_piece, "id", -2))
						),
						None,
					)
					if match_piece is not None:
						setattr(env, "current_piece", match_piece)
						return match_piece
			return current_piece
		action_queue = [p for p in self._coerce_piece_list(getattr(env, "action_queue", [])) if bool(getattr(p, "is_alive", True))]
		if action_queue:
			setattr(env, "current_piece", action_queue[0])
			return action_queue[0]
		return None

	def _ui_action_handler(self, env: Any) -> ActionSet:
		"""运行时动作输入：严格按当前行动棋子 ID 消费 UI 提交动作。"""
		current_piece = self._get_runtime_current_piece(env)
		if current_piece is None:
			return self._noop_action_handler(env)

		piece_id = int(getattr(current_piece, "id", -1))
		if piece_id < 0:
			return self._noop_action_handler(env)

		action = self.pending_actions_by_piece_id.pop(piece_id, None)
		if action is None:
			return self._noop_action_handler(env)
		return action

	def _queue_action_for_current_piece(self, action: ActionSet) -> bool:
		env = self.controller.environment
		if env is None:
			return False
		current_piece = self._get_runtime_current_piece(env)
		if current_piece is None:
			return False
		piece_id = int(getattr(current_piece, "id", -1))
		if piece_id < 0:
			return False
		self.pending_actions_by_piece_id[piece_id] = action
		return True

	def _build_move_action_from_ui(self) -> tuple[Optional[ActionSet], str]:
		"""将移动 UI 输入转换成 ActionSet，并做最小合法性校验。"""
		if self.controller.runtime_source != "runtime_env":
			return None, "当前不是后端运行模式，移动提交仅在 runtime 模式可执行"

		env = self.controller.environment
		if env is None:
			return None, "环境未初始化，请先加载后端模式"

		current_piece = self._get_runtime_current_piece(env)
		if current_piece is None:
			return None, "当前无可行动棋子，请检查对局初始化是否完成"
		if int(getattr(current_piece, "action_points", 0)) <= 0:
			return None, "当前棋子行动位不足"

		try:
			target_x = int(self.action_move_x_var.get().strip())
			target_y = int(self.action_move_y_var.get().strip())
		except Exception:
			return None, "移动坐标必须是整数"

		board = getattr(env, "board", None)
		width = int(getattr(board, "width", 0)) if board is not None else 0
		height = int(getattr(board, "height", 0)) if board is not None else 0
		if target_x < 0 or target_y < 0 or target_x >= width or target_y >= height:
			return None, "目标坐标超出地图范围"

		if board is not None:
			height_map = getattr(board, "height_map", None)
			if height_map is None:
				return None, "地图高度数据不可用"
			try:
				if int(height_map[target_x][target_y]) == -1:
					return None, "目标为不可通行地块"
			except Exception:
				return None, "目标地块不可访问"

			try:
				cell = board.grid[target_x][target_y]
				if int(getattr(cell, "state", 0)) == 2 and int(getattr(cell, "piece_id", -1)) != int(getattr(current_piece, "id", -1)):
					return None, "目标格已有其他棋子占据"
			except Exception:
				return None, "目标地块不可访问"

		legal_moves = env.get_legal_moves(current_piece)
		legal_targets = {(int(getattr(p, "x", -1)), int(getattr(p, "y", -1))) for p in legal_moves}
		if (target_x, target_y) not in legal_targets:
			return None, "目标不在当前棋子的可移动范围内"

		action = ActionSet()
		action.move = True
		action.move_target = Point(target_x, target_y)
		action.attack = False
		action.spell = False
		piece_code = self._get_piece_short_code(current_piece)
		return action, f"已提交移动：{piece_code} -> ({target_x}, {target_y})"

	def _attach_runtime_input(self) -> None:
		self.controller.set_function_input_methods(self._auto_init_handler, self._ui_action_handler)

	def _initialize_runtime_environment_with_initiative_capture(self, env: Any, board_file: Optional[str]) -> None:
		"""捕获初始化阶段的先攻掷骰明细。"""
		self.runtime_initiative_snapshot = []
		if env is None:
			return

		captured_rolls: list[int] = []
		original_roll = getattr(env, "roll_dice", None)
		wrapped = False

		if callable(original_roll):
			def _roll_proxy(n: int, sides: int):
				value = original_roll(n, sides)
				if int(n) == 1 and int(sides) == 20:
					captured_rolls.append(int(value))
				return value

			setattr(env, "roll_dice", _roll_proxy)
			wrapped = True

		try:
			env.initialize_environment(board_file=board_file)
		finally:
			if wrapped:
				setattr(env, "roll_dice", original_roll)

		roll_idx = 0
		snapshot: list[dict[str, Any]] = []
		for piece in self._coerce_piece_list(getattr(getattr(env, "player1", None), "pieces", [])):
			roll_value = int(captured_rolls[roll_idx]) if roll_idx < len(captured_rolls) else 0
			roll_idx += 1
			attr_value = int(getattr(piece, "dexterity", 0))
			snapshot.append(
				{
					"piece": piece,
					"attr_name": "敏捷",
					"attr_value": attr_value,
					"roll": roll_value,
					"bonus": attr_value,
					"total": int(roll_value + attr_value),
				}
			)

		for piece in self._coerce_piece_list(getattr(getattr(env, "player2", None), "pieces", None)):
			roll_value = int(captured_rolls[roll_idx]) if roll_idx < len(captured_rolls) else 0
			roll_idx += 1
			attr_value = int(getattr(piece, "dexterity", 0))
			snapshot.append(
				{
					"piece": piece,
					"attr_name": "敏捷",
					"attr_value": attr_value,
					"roll": roll_value,
					"bonus": attr_value,
					"total": int(roll_value + attr_value),
				}
			)

		self.runtime_initiative_snapshot = snapshot

	def _update_cards_from_env(self) -> None:
		env = self.controller.environment
		if env is None:
			return

		p1_hp = "0"
		p2_hp = "0"
		if getattr(env.player1, "pieces", None) is not None:
			p1_hp = str(sum(getattr(p, "health", 0) for p in env.player1.pieces if getattr(p, "is_alive", False)))
		if getattr(env.player2, "pieces", None) is not None:
			p2_hp = str(sum(getattr(p, "health", 0) for p in env.player2.pieces if getattr(p, "is_alive", False)))

		curr = getattr(env, "current_piece", None)
		curr_pos = "-"
		if curr is not None and getattr(curr, "position", None) is not None:
			curr_pos = f"({curr.position.x}, {curr.position.y})"

		_ = (p1_hp, p2_hp, curr_pos)
		self._refresh_piece_action_status_line()

	def _get_piece_action_status_text(self) -> str:
		if self.controller.runtime_source == "runtime_env" and self.controller.environment is not None:
			piece = self._get_runtime_current_piece(self.controller.environment)
			if piece is not None:
				piece_code = self._get_piece_short_code(piece)
				pos = getattr(piece, "position", None)
				px = int(getattr(pos, "x", -1)) if pos is not None else -1
				py = int(getattr(pos, "y", -1)) if pos is not None else -1
				ap = int(getattr(piece, "action_points", 0))
				max_ap = int(getattr(piece, "max_action_points", ap))
				sp = int(getattr(piece, "spell_slots", 0))
				max_sp = int(getattr(piece, "max_spell_slots", sp))
				return (
					f"当前行动棋子: {piece_code} | 坐标({px}, {py})"
					f" | 行动{ap}/{max_ap} | 法术{sp}/{max_sp}"
				)
			return "当前行动棋子: 无"
		return "当前模式暂不提供行动时段驱动"

	def _refresh_piece_action_status_line(self) -> None:
		label = self.action_panel_status_label
		if label is None:
			return
		try:
			if not bool(label.winfo_exists()):
				self.action_panel_status_label = None
				return
			label.configure(text=self._get_piece_action_status_text())
		except Exception:
			pass

	def _build_team_piece_view_data_runtime(self) -> dict[int, list[dict[str, Any]]]:
		env = self.controller.environment
		data: dict[int, list[dict[str, Any]]] = {1: [], 2: []}
		if env is None:
			return data

		selected_piece = self._get_runtime_current_piece(env)
		selected_id = int(getattr(selected_piece, "id", -1))
		for team_id, player_attr in ((1, "player1"), (2, "player2")):
			player = getattr(env, player_attr, None)
			pieces = self._coerce_piece_list(getattr(player, "pieces", None) if player is not None else None)
			if not pieces:
				continue

			sorted_pieces = sorted(pieces, key=lambda p: int(getattr(p, "id", 0)))
			for idx, piece in enumerate(sorted_pieces, start=1):
				spell_cur = int(getattr(piece, "spell_slots", 0))
				spell_max = int(getattr(piece, "max_spell_slots", 0))
				action_cur = int(getattr(piece, "action_points", 0))
				action_max = int(getattr(piece, "max_action_points", 0))
				move_value = float(getattr(piece, "movement", 0.0))
				data[team_id].append(
					{
						"piece_id": int(getattr(piece, "id", -1)),
						"piece_no": idx,
						"hp": str(int(getattr(piece, "health", 0))),
						"physical_resist": str(int(getattr(piece, "physical_resist", 0))),
						"magic_resist": str(int(getattr(piece, "magic_resist", 0))),
						"spell_slots": f"{spell_cur}/{spell_max}",
						"action_points": f"{action_cur}/{action_max}",
						"movement": f"{move_value:.1f}",
						"is_selected": int(getattr(piece, "id", -1)) == selected_id,
					}
				)

			selected_items = [x for x in data[team_id] if x["is_selected"]]
			rest_items = [x for x in data[team_id] if not x["is_selected"]]
			ordered = (selected_items + rest_items)[:3]
			while len(ordered) < 3:
				ordered.append(
					{
						"piece_id": -1,
						"piece_no": len(ordered) + 1,
						"hp": "-",
						"physical_resist": "-",
						"magic_resist": "-",
						"spell_slots": "-/-",
						"action_points": "-/-",
						"movement": "-",
						"is_selected": False,
					}
				)
			data[team_id] = ordered

		return data

	def _get_mock_last_actor_id(self) -> int:
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return -1
		rounds = game_data.get("rounds", [])
		if not isinstance(rounds, list) or int(self.controller.current_round) <= 0:
			return -1
		idx = int(self.controller.current_round) - 1
		if idx < 0 or idx >= len(rounds):
			return -1
		round_info = rounds[idx]
		actions = round_info.get("actions", []) if isinstance(round_info, dict) else []
		if not isinstance(actions, list) or not actions:
			return -1
		first_action = actions[0]
		if isinstance(first_action, dict):
			return int(first_action.get("soldierId", -1))
		return int(getattr(first_action, "soldierId", -1))

	def _build_team_piece_view_data_mock(self) -> dict[int, list[dict[str, Any]]]:
		data: dict[int, list[dict[str, Any]]] = {1: [], 2: []}
		if not self.mock_initial_positions:
			return data

		selected_id = self._get_mock_last_actor_id()
		for soldier_id, state in self.mock_initial_positions.items():
			team = int(state.get("team", 1))
			if team not in data:
				team = 1
			piece_no = int(self.mock_piece_number_by_id.get(soldier_id, 0))
			stats = self.mock_piece_stats_by_id.get(soldier_id, {})
			spell_cur = stats.get("spell_slots", "-")
			spell_max = stats.get("max_spell_slots", "-")
			action_cur = stats.get("action_points", "-")
			action_max = stats.get("max_action_points", "-")
			hp_text = str(int(self.mock_last_health_by_id.get(soldier_id, 0)))
			data[team].append(
				{
					"piece_id": int(soldier_id),
					"piece_no": piece_no if piece_no > 0 else 0,
					"hp": hp_text,
					"physical_resist": str(stats.get("physical_resist", "-")),
					"magic_resist": str(stats.get("magic_resist", "-")),
					"spell_slots": f"{spell_cur}/{spell_max}" if spell_cur != "-" and spell_max != "-" else "-/-",
					"action_points": f"{action_cur}/{action_max}" if action_cur != "-" and action_max != "-" else "-/-",
					"movement": str(stats.get("movement", "-")),
					"is_selected": int(soldier_id) == int(selected_id),
				}
			)

		for team in (1, 2):
			sorted_items = sorted(data[team], key=lambda x: int(x["piece_no"]) if int(x["piece_no"]) > 0 else 99)
			selected_items = [x for x in sorted_items if x["is_selected"]]
			rest_items = [x for x in sorted_items if not x["is_selected"]]
			ordered = (selected_items + rest_items)[:3]
			while len(ordered) < 3:
				ordered.append(
					{
						"piece_id": -1,
						"piece_no": len(ordered) + 1,
						"hp": "-",
						"physical_resist": "-",
						"magic_resist": "-",
						"spell_slots": "-/-",
						"action_points": "-/-",
						"movement": "-",
						"is_selected": False,
					}
				)
			data[team] = ordered

		return data

	def _slot_code(self, team: int, piece_no: int) -> str:
		letter = chr(ord("A") + max(0, piece_no - 1))
		return f"{team}{letter}"

	def _initialize_runtime_card_slots(self) -> None:
		"""按开局行动队列固定 6 个卡槽顺序；缺失棋子补到末尾。"""
		env = self.controller.environment
		self.runtime_card_slots = []
		if env is None:
			return

		piece_identity_to_slot: dict[int, tuple[int, int, str]] = {}
		slot_code_to_piece: dict[str, Any] = {}
		runtime_map = self._runtime_piece_slot_map()
		for slot_key, piece in runtime_map.items():
			team_id = int(slot_key[1])
			idx = int(slot_key[-1])
			code = self._slot_code(team_id, idx)
			piece_identity_to_slot[id(piece)] = (team_id, idx, code)
			slot_code_to_piece[code] = piece

		action_queue = self._coerce_piece_list(getattr(env, "action_queue", []))
		seen_codes: set[str] = set()
		for piece in action_queue:
			slot_meta = piece_identity_to_slot.get(id(piece))
			if slot_meta is None:
				continue
			team_id, piece_no, code = slot_meta
			if code in seen_codes:
				continue
			self.runtime_card_slots.append(
				{
					"team": team_id,
					"piece_no": piece_no,
					"slot_code": code,
					"piece": piece,
				}
			)
			seen_codes.add(code)

		for team_id in (1, 2):
			for piece_no in (1, 2, 3):
				code = self._slot_code(team_id, piece_no)
				if code in seen_codes:
					continue
				self.runtime_card_slots.append(
					{
						"team": team_id,
						"piece_no": piece_no,
						"slot_code": code,
						"piece": slot_code_to_piece.get(code),
					}
				)
				seen_codes.add(code)

		self.runtime_card_slots = self.runtime_card_slots[:6]

	def _initialize_mock_card_slots(self) -> None:
		"""mock 模式下固定 6 卡槽顺序：按回放首次行动顺序，缺失棋子补尾。"""
		self.mock_card_slots = []
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return

		code_to_soldier_id: dict[str, int] = {}
		for soldier_id, state in self.mock_initial_positions.items():
			team = int(state.get("team", 1))
			piece_no = int(self.mock_piece_number_by_id.get(soldier_id, 0))
			if team not in (1, 2) or piece_no not in (1, 2, 3):
				continue
			code = self._slot_code(team, piece_no)
			code_to_soldier_id[code] = int(soldier_id)

		ordered_codes: list[str] = []
		seen_ids: set[int] = set()
		rounds = game_data.get("rounds", [])
		if isinstance(rounds, list):
			for round_info in rounds:
				actions = round_info.get("actions", []) if isinstance(round_info, dict) else []
				if not isinstance(actions, list):
					continue
				for action in actions:
					soldier_id = int(action.get("soldierId", -1)) if isinstance(action, dict) else int(getattr(action, "soldierId", -1))
					if soldier_id < 0 or soldier_id in seen_ids:
						continue
					team = int(self.mock_initial_positions.get(soldier_id, {}).get("team", 1))
					piece_no = int(self.mock_piece_number_by_id.get(soldier_id, 0))
					if team not in (1, 2) or piece_no not in (1, 2, 3):
						continue
					ordered_codes.append(self._slot_code(team, piece_no))
					seen_ids.add(soldier_id)

		for team in (1, 2):
			for piece_no in (1, 2, 3):
				code = self._slot_code(team, piece_no)
				if code not in ordered_codes:
					ordered_codes.append(code)

		for code in ordered_codes[:6]:
			team = int(code[0]) if code and code[0].isdigit() else 1
			piece_no = ord(code[1]) - ord("A") + 1 if len(code) >= 2 else 1
			self.mock_card_slots.append(
				{
					"team": team,
					"piece_no": piece_no,
					"slot_code": code,
					"soldier_id": code_to_soldier_id.get(code),
				}
			)

	def _refresh_piece_cards(self) -> None:
		if not hasattr(self, "piece_cards"):
			return

		if self.controller.runtime_source == "runtime_env" and self.controller.environment is not None:
			if not self.runtime_card_slots:
				self._initialize_runtime_card_slots()

			current_piece = self._get_runtime_current_piece(self.controller.environment)

			def _role_display(piece_obj: Any) -> str:
				role_norm = str(getattr(piece_obj, "type", "") or "").strip().lower()
				weapon_id = self._safe_int(str(getattr(piece_obj, "weapon", 0)), 0)
				if role_norm == "warrior":
					return "战士(短)" if weapon_id == 2 else "战士(长)"
				if role_norm == "mage":
					return "法师"
				if role_norm == "archer":
					return "射手"
				if role_norm == "custom":
					return "自定义"
				return str(getattr(piece_obj, "type", "") or "").strip()
			for idx, card in enumerate(self.piece_cards):
				slot = self.runtime_card_slots[idx] if idx < len(self.runtime_card_slots) else None
				if slot is None:
					card.set_piece_state(
						team=1,
						piece_no=idx + 1,
						hp="-",
						physical_resist="-",
						magic_resist="-",
						spell_slots="-/-",
						action_points="-/-",
						movement="-",
						is_selected=False,
						header_text="--",
						position_text="(-,-)",
						physical_damage="-",
						magic_damage="-",
						dexterity="-",
						intelligence="-",
						strength="-",
						is_inactive=True,
					)
					continue

				team = int(slot.get("team", 1))
				piece_no = int(slot.get("piece_no", idx + 1))
				slot_code = str(slot.get("slot_code", self._slot_code(team, piece_no)))
				header_text = slot_code
				piece = slot.get("piece")

				if piece is None:
					card.set_piece_state(
						team=team,
						piece_no=piece_no,
						hp="-",
						physical_resist="-",
						magic_resist="-",
						spell_slots="-/-",
						action_points="-/-",
						movement="-",
						is_selected=False,
						header_text=header_text,
						position_text="(-,-)",
						physical_damage="-",
						magic_damage="-",
						dexterity="-",
						intelligence="-",
						strength="-",
						is_inactive=True,
					)
					continue

				alive = bool(getattr(piece, "is_alive", True))
				role_text = _role_display(piece)
				dy = bool(getattr(piece, "is_dying", False))
				if role_text:
					header_text = f"{slot_code} {role_text}"
				if dy:
					header_text = f"{header_text} [濒死]"
				hp_cur = int(getattr(piece, "health", 0)) if alive else 0
				hp_max = int(getattr(piece, "max_health", hp_cur))
				spell_cur = int(getattr(piece, "spell_slots", 0))
				spell_max = int(getattr(piece, "max_spell_slots", 0))
				action_cur = int(getattr(piece, "action_points", 0))
				action_max = int(getattr(piece, "max_action_points", 0))
				move_value = float(getattr(piece, "movement", 0.0))
				pos = getattr(piece, "position", None)
				pos_text = f"({int(getattr(pos, 'x', -1))},{int(getattr(pos, 'y', -1))})" if pos is not None else "(-,-)"
				current_id = int(getattr(current_piece, "id", -1)) if current_piece is not None else -1
				is_selected = int(getattr(piece, "id", -1)) == current_id and alive

				card.set_piece_state(
					team=team,
					piece_no=piece_no,
					hp=f"{hp_cur}/{hp_max}",
					position_text=pos_text,
					physical_damage=str(int(getattr(piece, "physical_damage", 0))),
					physical_resist=str(int(getattr(piece, "physical_resist", 0))),
					magic_damage=str(int(getattr(piece, "magic_damage", 0))),
					magic_resist=str(int(getattr(piece, "magic_resist", 0))),
					spell_slots=f"{spell_cur}/{spell_max}",
					action_points=f"{action_cur}/{action_max}",
					movement=f"{move_value:.1f}",
					dexterity=str(int(getattr(piece, "dexterity", 0))),
					intelligence=str(int(getattr(piece, "intelligence", 0))),
					strength=str(int(getattr(piece, "strength", 0))),
					is_selected=is_selected,
					header_text=header_text,
					is_dying=dy,
					is_inactive=not alive,
				)
			return

		# mock 模式：统一为固定顺序 6 槽位显示。
		if not self.mock_card_slots:
			self._initialize_mock_card_slots()

		selected_id = self._get_mock_last_actor_id()
		for idx, card in enumerate(self.piece_cards):
			slot = self.mock_card_slots[idx] if idx < len(self.mock_card_slots) else None
			if slot is None:
				card.set_piece_state(
					team=1,
					piece_no=idx + 1,
					hp="-",
					physical_resist="-",
					magic_resist="-",
					spell_slots="-/-",
					action_points="-/-",
					movement="-",
					is_selected=False,
					header_text="--",
					position_text="(-,-)",
					physical_damage="-",
					magic_damage="-",
					dexterity="-",
					intelligence="-",
					strength="-",
					is_inactive=True,
				)
				continue

			team = int(slot.get("team", 1))
			piece_no = int(slot.get("piece_no", idx + 1))
			header_text = str(slot.get("slot_code", self._slot_code(team, piece_no)))
			soldier_id = slot.get("soldier_id")

			if soldier_id is None:
				card.set_piece_state(
					team=team,
					piece_no=piece_no,
					hp="-",
					physical_resist="-",
					magic_resist="-",
					spell_slots="-/-",
					action_points="-/-",
					movement="-",
					is_selected=False,
					header_text=header_text,
					position_text="(-,-)",
					physical_damage="-",
					magic_damage="-",
					dexterity="-",
					intelligence="-",
					strength="-",
					is_inactive=True,
				)
				continue

			stats = self.mock_piece_stats_by_id.get(int(soldier_id), {})
			hp_value = int(self.mock_last_health_by_id.get(int(soldier_id), int(stats.get("health", 0) if isinstance(stats, dict) else 0)))
			hp_max = hp_value
			if isinstance(stats, dict):
				for key in ("max_health", "maxHealth", "health"):
					if key in stats:
						try:
							hp_max = int(stats.get(key, hp_value))
						except Exception:
							hp_max = hp_value
						break
			alive = hp_value > 0
			spell_cur = stats.get("spell_slots", "-") if isinstance(stats, dict) else "-"
			spell_max = stats.get("max_spell_slots", "-") if isinstance(stats, dict) else "-"
			action_cur = stats.get("action_points", "-") if isinstance(stats, dict) else "-"
			action_max = stats.get("max_action_points", "-") if isinstance(stats, dict) else "-"
			move_val = stats.get("movement", "-") if isinstance(stats, dict) else "-"
			is_selected = int(soldier_id) == int(selected_id) and alive

			card.set_piece_state(
				team=team,
				piece_no=piece_no,
				hp=f"{int(hp_value)}/{int(hp_max)}",
				position_text=f"({int(self.mock_last_positions_by_id.get(int(soldier_id), (-1, -1))[0])},{int(self.mock_last_positions_by_id.get(int(soldier_id), (-1, -1))[1])})",
				physical_damage=str(stats.get("physical_damage", "-") if isinstance(stats, dict) else "-"),
				physical_resist=str(stats.get("physical_resist", "-") if isinstance(stats, dict) else "-"),
				magic_damage=str(stats.get("magic_damage", "-") if isinstance(stats, dict) else "-"),
				magic_resist=str(stats.get("magic_resist", "-") if isinstance(stats, dict) else "-"),
				spell_slots=f"{spell_cur}/{spell_max}" if spell_cur != "-" and spell_max != "-" else "-/-",
				action_points=f"{action_cur}/{action_max}" if action_cur != "-" and action_max != "-" else "-/-",
				movement=str(move_val),
				dexterity=str(stats.get("dexterity", "-") if isinstance(stats, dict) else "-"),
				intelligence=str(stats.get("intelligence", "-") if isinstance(stats, dict) else "-"),
				strength=str(stats.get("strength", "-") if isinstance(stats, dict) else "-"),
				is_selected=is_selected,
				header_text=header_text,
				is_inactive=not alive,
			)

	def _camp_to_team(self, camp: str, players: dict[str, Any]) -> int:
		camp_lower = str(camp).strip().lower()
		player1_camp = str(players.get("player1", "")).strip().lower()
		player2_camp = str(players.get("player2", "")).strip().lower()
		if camp_lower and camp_lower == player1_camp:
			return 1
		if camp_lower and camp_lower == player2_camp:
			return 2
		if camp_lower in ("red", "player1", "p1", "team1", "1"):
			return 1
		if camp_lower in ("blue", "player2", "p2", "team2", "2"):
			return 2
		return 1

	def _extract_runtime_map_rows(self) -> list[list[int]]:
		env = self.controller.environment
		if env is None or not hasattr(env, "board"):
			return []
		board = env.board
		width = int(getattr(board, "width", 0))
		height = int(getattr(board, "height", 0))
		height_map = getattr(board, "height_map", None)
		if height_map is None or width <= 0 or height <= 0:
			return []

		rows: list[list[int]] = []
		for y in range(height):
			row: list[int] = []
			for x in range(width):
				try:
					row.append(int(height_map[x][y]))
				except Exception:
					row.append(0)
			rows.append(row)
		return rows

	def _extract_mock_visual_rows(self) -> list[list[int]]:
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return []
		board = game_data.get("map", {})
		raws = board.get("rows", []) if isinstance(board, dict) else []
		if not isinstance(raws, list):
			return []

		rows: list[list[int]] = []
		for y, raw_row in enumerate(raws):
			if not isinstance(raw_row, list):
				continue
			row: list[int] = []
			for x, raw_value in enumerate(raw_row):
				base_height = int(raw_value)
				override = self.mock_map_height_overrides.get((x, y))
				row.append(int(override) if override is not None else int(base_height))
			rows.append(row)
		return rows

	def _extract_runtime_pieces(self) -> list[dict[str, Any]]:
		env = self.controller.environment
		if env is None:
			return []
		current_piece = self._get_runtime_current_piece(env)
		current_id = int(getattr(current_piece, "id", -1)) if current_piece is not None else -1

		def _role_short(role_text: str) -> str:
			role_norm = str(role_text or "").strip().lower()
			if role_norm == "warrior":
				weapon_id = self._safe_int(str(getattr(piece, "weapon", 0)), 0)
				return "🗡" if weapon_id == 2 else "⚔️"
			if role_norm == "mage":
				return "🪄"
			if role_norm == "archer":
				return "🏹"
			if role_norm in ("custom", "自定义"):
				return "📝"
			return str(role_text or "")[:1].upper() if role_text else ""

		team_pieces: dict[int, list[Any]] = {1: [], 2: []}
		for team_id, player_attr in ((1, "player1"), (2, "player2")):
			player = getattr(env, player_attr, None)
			pieces = self._coerce_piece_list(getattr(player, "pieces", None) if player is not None else None)
			if not pieces:
				continue
			for piece in pieces:
				if not bool(getattr(piece, "is_alive", True)):
					continue
				team_pieces[team_id].append(piece)

		render_pieces: list[dict[str, Any]] = []
		for team_id in (1, 2):
			sorted_pieces = sorted(team_pieces[team_id], key=lambda p: int(getattr(p, "id", 0)))
			for piece in sorted_pieces:
				pos = getattr(piece, "position", None)
				x = int(getattr(pos, "x", -1)) if pos is not None else -1
				y = int(getattr(pos, "y", -1)) if pos is not None else -1
				base_label = self._get_piece_short_code(piece)
				role = str(getattr(piece, "type", "") or "").strip()
				dy = bool(getattr(piece, "is_dying", False))
				role_tag = _role_short(role)
				if role_tag or dy:
					base_label = f"{base_label}\n{role_tag}{'!' if dy else ''}".rstrip()
				render_pieces.append(
					{
						"team": team_id,
						"x": x,
						"y": y,
						"label": base_label,
						"is_current": int(getattr(piece, "id", -1)) == current_id,
					}
				)
		return render_pieces

	def _initialize_mock_positions(self) -> None:
		self.mock_initial_positions = {}
		self.mock_piece_stats_by_id = {}
		self.mock_last_health_by_id = {}
		self.mock_last_positions_by_id = {}
		self.mock_piece_number_by_id = {}
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return

		players = game_data.get("players", {})
		soldiers = game_data.get("soldiers", [])
		for soldier in soldiers:
			soldier_id = int(getattr(soldier, "ID", -1))
			camp = getattr(soldier, "camp", "")
			team = self._camp_to_team(camp, players if isinstance(players, dict) else {})
			position = getattr(soldier, "position", None)
			x = int(getattr(position, "x", -1)) if position is not None else -1
			y = int(getattr(position, "y", -1)) if position is not None else -1
			stats = getattr(soldier, "stats", {})
			health = int(stats.get("health", 0)) if isinstance(stats, dict) else 0
			self.mock_initial_positions[soldier_id] = {"team": team, "x": x, "y": y}
			self.mock_piece_stats_by_id[soldier_id] = stats if isinstance(stats, dict) else {}
			self.mock_last_positions_by_id[soldier_id] = (x, y)
			self.mock_last_health_by_id[soldier_id] = health

		team_to_ids: dict[int, list[int]] = {1: [], 2: []}
		for soldier_id, state in self.mock_initial_positions.items():
			team_id = int(state.get("team", 1))
			if team_id not in team_to_ids:
				team_id = 1
			team_to_ids[team_id].append(soldier_id)

		for team_id in (1, 2):
			for index, soldier_id in enumerate(sorted(team_to_ids[team_id]), start=1):
				self.mock_piece_number_by_id[soldier_id] = index

	def _format_team_piece_name(self, team: int, piece_no: int) -> str:
		index = piece_no if piece_no > 0 else "?"
		return f"player{team}-{index}"

	def _extract_mock_round_stats_health(self, round_info: Any) -> dict[int, int]:
		health_by_id: dict[int, int] = {}
		stats = round_info.get("stats", []) if isinstance(round_info, dict) else []
		if not isinstance(stats, list):
			return health_by_id

		for item in stats:
			if not isinstance(item, dict):
				continue
			soldier_id = int(item.get("soldierId", -1))
			stats_obj = item.get("Stats", {})
			if soldier_id < 0 or not isinstance(stats_obj, dict):
				continue
			health_by_id[soldier_id] = int(stats_obj.get("health", 0))
		return health_by_id

	def _append_mock_round_details(self, round_number: int) -> None:
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return

		rounds = game_data.get("rounds", [])
		idx = int(round_number) - 1
		if idx < 0 or idx >= len(rounds):
			return

		round_info = rounds[idx]
		if not isinstance(round_info, dict):
			return

		team_lines: dict[int, list[str]] = {1: [], 2: []}
		actions = round_info.get("actions", [])
		if isinstance(actions, list):
			for action in actions:
				soldier_id = int(getattr(action, "soldierId", -1))
				action_type = str(getattr(action, "actionType", ""))
				path = getattr(action, "path", [])
				damage_dealt = getattr(action, "damageDealt", [])

				if isinstance(action, dict):
					soldier_id = int(action.get("soldierId", soldier_id))
					action_type = str(action.get("actionType", action_type))
					path = action.get("path", path)
					damage_dealt = action.get("damageDealt", damage_dealt)

				piece_state = self.mock_initial_positions.get(soldier_id, {})
				team = int(piece_state.get("team", 1))
				if team not in team_lines:
					team = 1

				piece_no = int(self.mock_piece_number_by_id.get(soldier_id, 0))
				piece_name = self._format_team_piece_name(team, piece_no)
				action_lower = action_type.strip().lower()

				if isinstance(path, list) and len(path) > 0 and "move" in action_lower:
					start_pos = self.mock_last_positions_by_id.get(soldier_id)
					last_point = path[-1]
					end_x = int(getattr(last_point, "x", -1))
					end_y = int(getattr(last_point, "y", -1))
					if isinstance(last_point, dict):
						end_x = int(last_point.get("x", end_x))
						end_y = int(last_point.get("y", end_y))

					if start_pos is not None:
						team_lines[team].append(
							f"{piece_name} 移动: ({start_pos[0]}, {start_pos[1]}) -> ({end_x}, {end_y})"
						)
					else:
						team_lines[team].append(f"{piece_name} 移动到: ({end_x}, {end_y})")
					self.mock_last_positions_by_id[soldier_id] = (end_x, end_y)
				else:
					team_lines[team].append(f"{piece_name} 行动: {action_type or '未知'}")

				if isinstance(damage_dealt, list):
					for dmg in damage_dealt:
						if not isinstance(dmg, dict):
							continue
						target_id = int(dmg.get("targetId", -1))
						damage = int(dmg.get("damage", 0))
						target_team = int(self.mock_initial_positions.get(target_id, {}).get("team", 1))
						target_no = int(self.mock_piece_number_by_id.get(target_id, 0))
						target_name = self._format_team_piece_name(target_team, target_no)
						team_lines[team].append(f"{piece_name} 对 {target_name} 造成伤害: {damage}")

		new_health_by_id = self._extract_mock_round_stats_health(round_info)
		for soldier_id, new_hp in new_health_by_id.items():
			old_hp = int(self.mock_last_health_by_id.get(soldier_id, new_hp))
			if old_hp != new_hp:
				team = int(self.mock_initial_positions.get(soldier_id, {}).get("team", 1))
				if team not in team_lines:
					team = 1
				piece_no = int(self.mock_piece_number_by_id.get(soldier_id, 0))
				piece_name = self._format_team_piece_name(team, piece_no)
				delta = old_hp - new_hp
				if delta > 0:
					team_lines[team].append(f"{piece_name} 血量变化: {old_hp} -> {new_hp} (受到伤害 {delta})")
				else:
					team_lines[team].append(f"{piece_name} 血量变化: {old_hp} -> {new_hp}")

		self.mock_last_health_by_id.update(new_health_by_id)

		self.right_info_panel.append_content(f"\n[回合 {round_number} 详细信息]")
		for team in (1, 2):
			if team_lines[team]:
				for line in team_lines[team]:
					self.right_info_panel.append_content(f"\n  player{team}: {line}")
			else:
				self.right_info_panel.append_content(f"\n  player{team}: 本回合无行动信息")

	def _snapshot_runtime_piece_states(self) -> dict[int, dict[str, Any]]:
		env = self.controller.environment
		if env is None:
			return {}

		states: dict[int, dict[str, Any]] = {}
		for team_id, player_attr in ((1, "player1"), (2, "player2")):
			player = getattr(env, player_attr, None)
			pieces = self._coerce_piece_list(getattr(player, "pieces", None) if player is not None else None)
			if not pieces:
				continue
			for piece in pieces:
				piece_id = int(getattr(piece, "id", -1))
				if piece_id < 0:
					continue
				pos = getattr(piece, "position", None)
				x = int(getattr(pos, "x", -1)) if pos is not None else -1
				y = int(getattr(pos, "y", -1)) if pos is not None else -1
				states[piece_id] = {
					"team": team_id,
					"x": x,
					"y": y,
					"hp": int(getattr(piece, "health", 0)),
					"alive": bool(getattr(piece, "is_alive", True)),
				}
		return states

	def _append_runtime_round_details(
		self,
		round_number: int,
		before_states: dict[int, dict[str, Any]],
		after_states: dict[int, dict[str, Any]],
	) -> None:
		team_lines: dict[int, list[str]] = {1: [], 2: []}
		team_piece_ids: dict[int, list[int]] = {1: [], 2: []}

		for piece_id, state in after_states.items():
			team = int(state.get("team", 1))
			if team not in team_piece_ids:
				team = 1
			team_piece_ids[team].append(piece_id)

		piece_no_map: dict[int, int] = {}
		for team in (1, 2):
			for idx, piece_id in enumerate(sorted(team_piece_ids[team]), start=1):
				piece_no_map[piece_id] = idx

		for piece_id, after_state in after_states.items():
			before_state = before_states.get(piece_id)
			team = int(after_state.get("team", 1))
			if team not in team_lines:
				team = 1
			piece_name = self._format_team_piece_name(team, int(piece_no_map.get(piece_id, 0)))

			if before_state is None:
				continue

			old_x, old_y = int(before_state.get("x", -1)), int(before_state.get("y", -1))
			new_x, new_y = int(after_state.get("x", -1)), int(after_state.get("y", -1))
			if old_x != new_x or old_y != new_y:
				team_lines[team].append(f"{piece_name} 移动: ({old_x}, {old_y}) -> ({new_x}, {new_y})")

			old_hp = int(before_state.get("hp", 0))
			new_hp = int(after_state.get("hp", 0))
			if old_hp != new_hp:
				delta = old_hp - new_hp
				if delta > 0:
					team_lines[team].append(f"{piece_name} 血量变化: {old_hp} -> {new_hp} (受到伤害 {delta})")
				else:
					team_lines[team].append(f"{piece_name} 血量变化: {old_hp} -> {new_hp}")

		self.right_info_panel.append_content(f"\n[回合 {round_number} 详细信息]")
		for team in (1, 2):
			if team_lines[team]:
				for line in team_lines[team]:
					self.right_info_panel.append_content(f"\n  player{team}: {line}")
			else:
				self.right_info_panel.append_content(f"\n  player{team}: 本回合无明显状态变化")

	def _append_round_details_after_step(self, runtime_before_states: Optional[dict[int, dict[str, Any]]] = None) -> None:
		if self.controller.runtime_source == "runtime_env":
			env = self.controller.environment
			if env is None:
				return
			after_states = self._snapshot_runtime_piece_states()
			round_number = int(getattr(env, "round_number", 0))
			self._append_runtime_round_details(round_number, runtime_before_states or {}, after_states)
			return

		round_number = int(self.controller.current_round)
		self._append_mock_round_details(round_number)

	def _build_mock_pieces_for_current_round(self) -> list[dict[str, Any]]:
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return []
		if not self.mock_initial_positions:
			self._initialize_mock_positions()

		positions: dict[int, dict[str, Any]] = {
			sid: {"team": state["team"], "x": state["x"], "y": state["y"]}
			for sid, state in self.mock_initial_positions.items()
		}

		rounds = game_data.get("rounds", [])
		current_round = max(0, min(int(self.controller.current_round), len(rounds)))
		for idx in range(current_round):
			round_info = rounds[idx]
			actions = getattr(round_info, "actions", None)
			if actions is None and isinstance(round_info, dict):
				actions = round_info.get("actions", [])
			if not isinstance(actions, list):
				continue

			for action in actions:
				soldier_id = int(getattr(action, "soldierId", -1))
				path = getattr(action, "path", None)
				if path is None and isinstance(action, dict):
					soldier_id = int(action.get("soldierId", -1))
					path = action.get("path", [])
				if not isinstance(path, list) or not path:
					continue
				last_point = path[-1]
				x = int(getattr(last_point, "x", -1))
				y = int(getattr(last_point, "y", -1))
				if soldier_id in positions:
					positions[soldier_id]["x"] = x
					positions[soldier_id]["y"] = y

		team_to_ids: dict[int, list[int]] = {1: [], 2: []}
		for soldier_id, state in positions.items():
			team = int(state.get("team", 1))
			if team not in team_to_ids:
				team = 1
			team_to_ids[team].append(soldier_id)

		render_pieces: list[dict[str, Any]] = []
		for team_id in (1, 2):
			sorted_ids = sorted(team_to_ids[team_id])
			for index, soldier_id in enumerate(sorted_ids, start=1):
				state = positions[soldier_id]
				render_pieces.append(
					{
						"team": team_id,
						"x": int(state.get("x", -1)),
						"y": int(state.get("y", -1)),
						"label": f"player{team_id}\n{index}",
					}
				)
		return render_pieces

	def _refresh_board_view(self) -> None:
		"""刷新棋盘底图和棋子位置。"""
		# 地图属性选点时，棋盘点击由透明覆盖层接管。
		# 为避免行动面板残留的“移动目标/火球 AOE”干扰地图编辑，这里暂时屏蔽行动预览绘制。
		if self.attribute_map_pick_waiting:
			move_target = None
			spell_overlay = ([], "#f97316")
			target_markers: list[dict[str, Any]] = []
		else:
			move_target = self._get_move_target_highlight()
			spell_overlay = self._build_spell_aoe_overlay()
			target_markers = self._build_target_markers_for_board()
		trap_markers = self._build_runtime_trap_markers()
		if self.controller.runtime_source == "runtime_env" and self.controller.environment is not None:
			map_rows = self._extract_runtime_map_rows()
			pieces = self._extract_runtime_pieces()
			self.left_board_panel.set_board_state(map_rows, pieces)
			self.left_board_panel.set_move_target_highlight(move_target)
			self.left_board_panel.set_spell_aoe_overlay(spell_overlay[0], spell_overlay[1])
			self.left_board_panel.set_trap_markers(trap_markers)
			# 🎯 目标标记（只在可执行的锁定行动下展示）
			if hasattr(self.left_board_panel, "set_target_markers"):
				self.left_board_panel.set_target_markers(target_markers)
			return

		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			self.left_board_panel.set_board_state([], [])
			return

		map_rows = self._extract_mock_visual_rows()
		pieces = self._build_mock_pieces_for_current_round()
		self.left_board_panel.set_board_state(map_rows if isinstance(map_rows, list) else [], pieces)
		self.left_board_panel.set_move_target_highlight(move_target)
		self.left_board_panel.set_spell_aoe_overlay([], "#f97316")
		self.left_board_panel.set_trap_markers([])
		if hasattr(self.left_board_panel, "set_target_markers"):
			self.left_board_panel.set_target_markers([])

	def _build_target_markers_for_board(self) -> list[dict[str, Any]]:
		"""根据当前行动面板状态，判断是否应对目标棋子绘制🎯。"""
		if self.controller.runtime_source != "runtime_env":
			return []
		env = self.controller.environment
		if env is None:
			return []
		mode = self.action_ui_mode.get().strip().lower()
		if mode not in ("attack", "spell"):
			return []

		actor = self._get_runtime_current_piece(env)
		if actor is None:
			return []
		# 资源：攻击仅看 AP；法术额外看 SP。
		ap = int(getattr(actor, "action_points", 0))
		if ap <= 0:
			return []

		# 攻击：锁定目标+范围判定。
		if mode == "attack":
			target_label = self.action_attack_target_var.get().strip()
			target_piece = self._resolve_action_target_piece(target_label)
			if target_piece is None:
				return []
			attack_type = (self.action_attack_type_var.get().strip() or "物理攻击")
			# 定制攻击也视为“锁定行动”，但仍按用户期望要求 AP 且要求输入合法。
			if attack_type == "定制攻击":
				try:
					custom_damage = int(self.action_custom_damage_var.get().strip())
				except Exception:
					return []
				if custom_damage <= 0:
					return []
			else:
				try:
					if not bool(env.is_in_attack_range(actor, target_piece)):
						return []
				except Exception:
					# 若后端环境不支持该判断，则不绘制（避免误导）。
					return []

			pos = getattr(target_piece, "position", None)
			x = int(getattr(pos, "x", -1)) if pos is not None else -1
			y = int(getattr(pos, "y", -1)) if pos is not None else -1
			if x < 0 or y < 0:
				return []
			return [{"x": x, "y": y, "text": "🎯"}]

		# 法术：仅对“锁定法术”显示，且需满足 AP/SP 与射程。
		spell = self._resolve_selected_spell()
		if spell is None:
			return []
		if self._is_teleport_spell(spell) or self._is_trap_spell(spell):
			return []
		is_locking = bool(getattr(spell, "is_locking_spell", False))
		if not is_locking:
			return []
		sp = int(getattr(actor, "spell_slots", 0))
		spell_cost = int(getattr(spell, "spell_cost", 1))
		if sp < spell_cost:
			return []

		target_text = self.action_spell_target_var.get().strip()
		target_piece = self._resolve_spell_target_piece(target_text, spell, actor)
		if target_piece is None:
			return []
		actor_pos = getattr(actor, "position", None)
		target_pos = getattr(target_piece, "position", None)
		ax = int(getattr(actor_pos, "x", -1)) if actor_pos is not None else -1
		ay = int(getattr(actor_pos, "y", -1)) if actor_pos is not None else -1
		tx = int(getattr(target_pos, "x", -1)) if target_pos is not None else -1
		ty = int(getattr(target_pos, "y", -1)) if target_pos is not None else -1
		if ax < 0 or ay < 0 or tx < 0 or ty < 0:
			return []
		spell_range = float(getattr(spell, "range", 0.0))
		distance = ((ax - tx) ** 2 + (ay - ty) ** 2) ** 0.5
		if distance > spell_range:
			return []
		return [{"x": tx, "y": ty, "text": "🎯"}]

	def _build_runtime_trap_markers(self) -> list[dict[str, Any]]:
		markers: list[dict[str, Any]] = []
		for trap in self.runtime_trap_effects:
			remaining = int(trap.get("remaining", 0))
			if remaining <= 0:
				continue
			markers.append(
				{
					"x": int(trap.get("x", -1)),
					"y": int(trap.get("y", -1)),
					"remaining": remaining,
				}
			)
		return markers

	def _spell_preview_color(self, spell: Any) -> str:
		name = str(getattr(spell, "name", "")).strip().lower()
		effect_key = self._spell_effect_key(spell)
		if "fire" in name or "火" in name:
			return "#fb7185"
		if effect_key == "heal":
			return "#34d399"
		if effect_key == "move":
			return "#60a5fa"
		if effect_key in ("debuff", "damage"):
			return "#f97316"
		return "#f59e0b"

	def _build_spell_aoe_overlay(self) -> tuple[list[tuple[int, int]], str]:
		env = self.controller.environment
		if self.controller.runtime_source != "runtime_env" or env is None:
			return [], "#f97316"
		if self.action_ui_mode.get().strip().lower() != "spell":
			return [], "#f97316"
		spell = self._resolve_selected_spell()
		if spell is None:
			return [], "#f97316"
		if self._is_teleport_spell(spell):
			return [], self._spell_preview_color(spell)
		if bool(getattr(spell, "is_locking_spell", False)):
			return [], self._spell_preview_color(spell)
		try:
			center_x = int(self.action_spell_point_x_var.get().strip())
			center_y = int(self.action_spell_point_y_var.get().strip())
		except Exception:
			return [], self._spell_preview_color(spell)
		board = getattr(env, "board", None)
		width = int(getattr(board, "width", 0)) if board is not None else 0
		height = int(getattr(board, "height", 0)) if board is not None else 0
		if width <= 0 or height <= 0:
			return [], self._spell_preview_color(spell)
		radius = max(0, int(getattr(spell, "area_radius", 0)))
		cells: list[tuple[int, int]] = []
		for x in range(width):
			for y in range(height):
				if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
					cells.append((x, y))
		return cells, self._spell_preview_color(spell)

	def _get_move_target_highlight(self) -> tuple[int, int] | None:
		"""返回需要在棋盘高亮的目标格（移动或法术）。"""
		env = self.controller.environment
		if self.controller.runtime_source != "runtime_env" or env is None:
			return None

		mode = self.action_ui_mode.get().strip().lower()
		if mode == "spell":
			selected_spell = self._resolve_selected_spell()
			if selected_spell is None:
				return None
			is_locking_spell = bool(getattr(selected_spell, "is_locking_spell", False)) and not self._is_teleport_spell(selected_spell)
			if is_locking_spell:
				target_text = self.action_spell_target_var.get().strip()
				target_piece = self._resolve_spell_target_piece(target_text, selected_spell, self._get_runtime_current_piece(env))
				if target_piece is None:
					return None
				pos = getattr(target_piece, "position", None)
				tx = int(getattr(pos, "x", -1)) if pos is not None else -1
				ty = int(getattr(pos, "y", -1)) if pos is not None else -1
				return (tx, ty) if tx >= 0 and ty >= 0 else None
			try:
				target_x = int(self.action_spell_point_x_var.get().strip())
				target_y = int(self.action_spell_point_y_var.get().strip())
			except Exception:
				return None
			board = getattr(env, "board", None)
			width = int(getattr(board, "width", 0)) if board is not None else 0
			height = int(getattr(board, "height", 0)) if board is not None else 0
			if 0 <= target_x < width and 0 <= target_y < height:
				return (target_x, target_y)
			return None

		if mode != "move":
			return None
		try:
			target_x = int(self.action_move_x_var.get().strip())
			target_y = int(self.action_move_y_var.get().strip())
		except Exception:
			return None
		board = getattr(env, "board", None)
		width = int(getattr(board, "width", 0)) if board is not None else 0
		height = int(getattr(board, "height", 0)) if board is not None else 0
		if not (0 <= target_x < width and 0 <= target_y < height):
			return None
		piece = self._get_runtime_current_piece(env)
		if piece is None:
			return None
		pos = getattr(piece, "position", None)
		curr_x = int(getattr(pos, "x", -1)) if pos is not None else -1
		curr_y = int(getattr(pos, "y", -1)) if pos is not None else -1
		if (target_x, target_y) == (curr_x, curr_y):
			return None
		return (target_x, target_y)

	def _event_loop_tick(self) -> None:
		if not self.running:
			return
		try:
			runtime_before_states = self._snapshot_runtime_piece_states() if self.controller.runtime_source == "runtime_env" else None
			should_continue = self.controller.run_round()
			self._update_cards_from_env()
			self._refresh_piece_cards()
			self._refresh_board_view()
			self._append_round_details_after_step(runtime_before_states=runtime_before_states)
			self._sync_replay_round_var()
			if should_continue:
				self.loop_job = self.root.after(max(50, int(self.replay_speed_ms)), self._event_loop_tick)
			else:
				self.running = False
				self.loop_job = None
				self._update_replay_play_pause_button_text()
				self.right_info_panel.append_content("\n对局结束")
				if self.controller.runtime_source == "runtime_env":
					self._show_game_over_reset_dialog()
		except Exception as e:
			self.running = False
			self.loop_job = None
			self._update_replay_play_pause_button_text()
			self.right_info_panel.append_content(f"\n[UI] 循环执行异常: {e}")

	def _run_single_round_once(self, source_tag: str = "UI") -> None:
		"""执行一回合并刷新 UI，用于行动提交后立即生效。"""
		if not self.loaded:
			self.right_info_panel.append_content("\n[UI] 尚未加载数据，无法执行回合")
			return
		try:
			runtime_before_states = self._snapshot_runtime_piece_states() if self.controller.runtime_source == "runtime_env" else None
			ok = self.controller.run_round()
			self._update_cards_from_env()
			self._refresh_piece_cards()
			self._refresh_board_view()
			self._append_round_details_after_step(runtime_before_states=runtime_before_states)
			self._sync_replay_round_var()
			self.right_info_panel.append_content(f"\n[UI] {source_tag}触发单回合完成, continue={ok}")
		except Exception as e:
			self.right_info_panel.append_content(f"\n[UI] {source_tag}触发单回合失败: {e}")

	def _build_left_side(self, parent: ttk.Frame) -> None:
		"""构建左侧区域。

		左侧分为上下两块：
		- 上方：信息展示区域（已明确需求）
		- 下方：主内容预留区（后续可放棋盘/地图/时序面板）
		"""
		parent.columnconfigure(0, weight=1)
		parent.rowconfigure(0, weight=0)  # 顶部信息区固定预留高度
		parent.rowconfigure(1, weight=1)  # 下方主区域占据剩余空间

		# 左上信息区：6 个等尺寸卡片，保持区域总体宽高不变。
		self.left_top_info = ttk.LabelFrame(parent, text="信息展示区", padding=8)
		self.left_top_info.configure(height=180)
		self.left_top_info.configure(width=620)
		self.left_top_info.grid_propagate(False)
		self.left_top_info.grid(row=0, column=0, sticky="ew", pady=(0, 10))

		square_row = ttk.Frame(self.left_top_info)
		square_row.pack(fill="both", expand=True)

		# 六卡等权横向排列。
		for idx in range(6):
			square_row.columnconfigure(idx, weight=1, uniform="piece_col")
		square_row.rowconfigure(0, weight=1)
		card_height = 128

		self.piece_cards: list[PieceSquareCard] = []
		for idx in range(6):
			card = PieceSquareCard(
				square_row,
				width=96,
				height=card_height,
				is_large=True,
			)
			pad_left = 0 if idx == 0 else 3
			pad_right = 0 if idx == 5 else 3
			card.grid(row=0, column=idx, sticky="sew", padx=(pad_left, pad_right), pady=(0, 0))
			self.piece_cards.append(card)

		self._refresh_piece_cards()

		# 左下区域改为真实棋盘组件：20x20 正方形网格。
		# 棋盘绘制逻辑放在 components.py，主界面只负责装配与摆放。
		self.left_board_panel = ChessboardPanel(parent, title="棋盘区域（20 x 20）", grid_size=20)
		self.left_board_panel.configure(width=620)
		self.left_board_panel.grid(row=1, column=0, sticky="nsew")

	def _build_right_side(self, parent: ttk.Frame) -> None:
		"""构建右侧区域。

		右侧主要用于：
		- 新增上方复合区域
		- 操作按钮
		- 信息展示
		"""
		parent.columnconfigure(0, weight=1)
		parent.rowconfigure(0, weight=0)  # 新增上方区域
		parent.rowconfigure(1, weight=0)  # 操作区下移
		parent.rowconfigure(2, weight=1)  # 信息区吃满剩余空间（可被适当压缩）

		# 在操作区上方插入与操作区同量级高度的新区域。
		self.right_top_composite_panel = RightTopCompositePanel(
			parent,
			title="复合展示区",
			on_initialize=self._on_right_composite_panel_initialize,
		)
		self.right_top_composite_panel.configure(height=320)
		self.right_top_composite_panel.grid_propagate(False)
		self.right_top_composite_panel.grid(row=0, column=0, sticky="ew", pady=(0, 6))

		buttons = [
			("模式选择", self._on_click_mode_selection),
			("回放模式", self._on_click_replay_mode),
			("棋子行动", self._on_click_piece_action),
			("属性设置", self._on_click_attribute_settings),
			("系统设置", lambda: None),
			("退出测试", self._on_click_exit),
		]
		self.right_button_panel = ButtonPanel(parent, title="操作区", buttons=buttons)
		self.right_button_panel.configure(height=250)
		self.right_button_panel.grid_propagate(False)
		self.right_button_panel.grid(row=1, column=0, sticky="ew", pady=(0, 6))

		# 右侧信息区保留在最下方，因新增区域和操作区下移，纵向空间会适度压缩。
		self.right_info_panel = InfoPanel(parent, title="右侧信息展示区", height=150)
		self.right_info_panel.grid(row=2, column=0, sticky="nsew")
		self.right_info_panel.set_content(
			"这里预留用于显示操作反馈、错误提示、关键变量与日志。\n"
			"按钮点击后会向此处追加示例文本，便于联调界面流程。"
		)

	def _sync_replay_round_var(self) -> None:
		"""同步回放区显示的当前回合。"""
		if self.controller.runtime_source == "runtime_env" and self.controller.environment is not None:
			round_number = int(getattr(self.controller.environment, "round_number", 0))
			self.replay_round_var.set(max(1, round_number + 1))
			return
		total = self._get_mock_total_rounds()
		next_round = int(self.controller.current_round) + 1
		if total > 0:
			next_round = max(1, min(next_round, total))
		else:
			next_round = max(1, next_round)
		self.replay_round_var.set(next_round)

	def _get_mock_total_rounds(self) -> int:
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return 0
		rounds = game_data.get("rounds", [])
		return len(rounds) if isinstance(rounds, list) else 0

	def _show_interval_range_warning(self) -> None:
		"""弹窗提示播放间隔输入越界。"""
		window = tk.Toplevel(self.root)
		window.title("提示")
		window.transient(self.root)
		window.resizable(False, False)
		window.grab_set()
		frame = ttk.Frame(window, padding=12)
		frame.pack(fill="both", expand=True)
		ttk.Label(frame, text="间隔的合法范围是100-2000ms！").pack(anchor="w")
		window.update_idletasks()
		parent_x = self.root.winfo_rootx()
		parent_y = self.root.winfo_rooty()
		parent_w = self.root.winfo_width()
		parent_h = self.root.winfo_height()
		win_w = window.winfo_width()
		win_h = window.winfo_height()
		target_x = parent_x + max((parent_w - win_w) // 2, 0)
		target_y = parent_y + max((parent_h - win_h) // 2, 0)
		window.geometry(f"+{target_x}+{target_y}")

	def _apply_replay_speed_from_input(self, *, from_text_input: bool = False) -> None:
		"""从输入框读取回放间隔（毫秒）。"""
		try:
			raw_value = int(self.replay_speed_var.get())
		except Exception:
			raw_value = self.replay_speed_ms

		if from_text_input and (raw_value < 100 or raw_value > 2000):
			self._show_interval_range_warning()

		value = max(100, min(raw_value, 2000))
		self.replay_speed_ms = value
		self.replay_speed_var.set(value)

	def _rebuild_mock_state_to_round(self, target_round: int) -> None:
		"""重建 mock 缓存到指定回合（用于后退/跳转）。"""
		self._initialize_mock_positions()
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return

		rounds = game_data.get("rounds", [])
		if not isinstance(rounds, list):
			return

		for idx in range(max(0, min(target_round, len(rounds)))):
			round_info = rounds[idx]
			if not isinstance(round_info, dict):
				continue

			actions = round_info.get("actions", [])
			if isinstance(actions, list):
				for action in actions:
					soldier_id = int(getattr(action, "soldierId", -1))
					path = getattr(action, "path", [])
					if isinstance(action, dict):
						soldier_id = int(action.get("soldierId", soldier_id))
						path = action.get("path", path)
					if soldier_id < 0 or not isinstance(path, list) or not path:
						continue
					last_point = path[-1]
					x = int(getattr(last_point, "x", -1))
					y = int(getattr(last_point, "y", -1))
					if isinstance(last_point, dict):
						x = int(last_point.get("x", x))
						y = int(last_point.get("y", y))
					self.mock_last_positions_by_id[soldier_id] = (x, y)

			health_map = self._extract_mock_round_stats_health(round_info)
			if health_map:
				self.mock_last_health_by_id.update(health_map)

	def _apply_round_for_replay(self, target_round: int) -> None:
		"""设置目标回合并刷新界面（回合号语义为“该回合开始前”）。"""
		if self.controller.runtime_source == "runtime_env":
			self.right_info_panel.append_content("\n[UI] 后端实时环境暂不支持跳转/回退回合")
			self._sync_replay_round_var()
			return

		total = self._get_mock_total_rounds()
		target_display = max(1, min(int(target_round), total if total > 0 else 1))
		target_index = max(0, target_display - 1)
		self.controller.current_round = target_index
		self._rebuild_mock_state_to_round(target_index)
		self._sync_replay_round_var()
		self._refresh_piece_cards()
		self._refresh_board_view()

	def _update_replay_play_pause_button_text(self) -> None:
		if self.replay_play_pause_button is None:
			return
		self.replay_play_pause_button.configure(text="暂停" if self.running else "播放")

	def _on_replay_back(self) -> None:
		if self.running:
			self._on_click_pause()
		self._apply_round_for_replay(int(self.replay_round_var.get()) - 1)

	def _on_replay_forward(self) -> None:
		if self.running:
			self._on_click_pause()
		if not self.loaded:
			self.right_info_panel.append_content("\n[UI] 请先选择模式并加载数据")
			return
		if self.controller.runtime_source == "runtime_env":
			self._on_click_step()
			return
		self._apply_round_for_replay(int(self.replay_round_var.get()) + 1)

	def _on_replay_restart(self) -> None:
		if self.running:
			self._on_click_pause()
		self._apply_round_for_replay(1)

	def _on_replay_jump_to_round(self) -> None:
		try:
			target = int(self.replay_round_var.get())
		except Exception:
			target = int(self.controller.current_round)
		self._apply_round_for_replay(target)

	def _on_replay_toggle_play_pause(self) -> None:
		self._apply_replay_speed_from_input(from_text_input=False)
		if self.running:
			self._on_click_pause()
		else:
			self._on_click_start()
		self._update_replay_play_pause_button_text()

	def _collect_action_target_options(self) -> list[str]:
		"""收集可用于攻击/法术下拉框的目标候选。"""
		env = self.controller.environment
		if env is not None:
			current_piece = self._get_runtime_current_piece(env)
			current_team = int(getattr(current_piece, "team", -1)) if current_piece is not None else -1
			options: list[str] = []
			for piece in self._coerce_piece_list(getattr(env, "action_queue", [])):
				if not bool(getattr(piece, "is_alive", False)):
					continue
				piece_team = int(getattr(piece, "team", -1))
				if piece_team == current_team:
					continue
				options.append(self._format_action_target_option(piece))
			if options:
				return options

		if self.mock_initial_positions:
			return [
				f"ID{int(pid)} ({int(state.get('x', -1))}, {int(state.get('y', -1))})"
				for pid, state in sorted(self.mock_initial_positions.items())
			]

		return ["目标A", "目标B"]

	def _format_action_target_option(self, piece: Any) -> str:
		piece_code = self._get_piece_short_code(piece)
		x = int(getattr(getattr(piece, "position", None), "x", -1))
		y = int(getattr(getattr(piece, "position", None), "y", -1))
		return f"{piece_code} ({x}, {y})"

	def _resolve_action_target_piece(self, selected_text: str) -> Any:
		env = self.controller.environment
		if env is None:
			return None
		current_piece = self._get_runtime_current_piece(env)
		current_team = int(getattr(current_piece, "team", -1)) if current_piece is not None else -1
		for piece in self._coerce_piece_list(getattr(env, "action_queue", [])):
			if not bool(getattr(piece, "is_alive", False)):
				continue
			if int(getattr(piece, "team", -1)) == current_team:
				continue
			if self._format_action_target_option(piece) == selected_text:
				return piece
		return None

	def _get_piece_short_code(self, piece: Any) -> str:
		"""返回棋子简称（如 1A、2C），找不到时回退为 ?。"""
		if piece is None:
			return "?"

		if not self.runtime_card_slots and self.controller.environment is not None:
			self._initialize_runtime_card_slots()

		for slot in self.runtime_card_slots:
			if slot.get("piece") is piece:
				return str(slot.get("slot_code", "?"))

		env = self.controller.environment
		if env is not None:
			for team_id, player_attr in ((1, "player1"), (2, "player2")):
				player = getattr(env, player_attr, None)
				pieces = self._coerce_piece_list(getattr(player, "pieces", None) if player is not None else None)
				for idx, p in enumerate(pieces[:3], start=1):
					if p is piece:
						return self._slot_code(team_id, idx)

		return "?"

	def _get_current_actor_text(self) -> str:
		env = self.controller.environment
		if env is not None:
			curr = self._get_runtime_current_piece(env)
			if curr is not None:
				piece_code = self._get_piece_short_code(curr)
				pos = getattr(curr, "position", None)
				if pos is not None:
					return f"棋子{piece_code}({int(pos.x)},{int(pos.y)})"
				return f"棋子{piece_code}"
		return "棋子?(-,-)"

	def _stop_action_move_point_pick(self) -> None:
		self.action_move_pick_waiting = False
		self.action_pick_mode = ""
		overlay = self.action_move_pick_overlay
		self.action_move_pick_overlay = None
		if overlay is not None and overlay.winfo_exists():
			overlay.destroy()

	def _resolve_piece_at_board_xy(self, x: int, y: int) -> Any:
		env = self.controller.environment
		if env is None:
			return None
		for piece in self._coerce_piece_list(getattr(env, "action_queue", [])):
			if not bool(getattr(piece, "is_alive", False)):
				continue
			pos = getattr(piece, "position", None)
			px = int(getattr(pos, "x", -1)) if pos is not None else -1
			py = int(getattr(pos, "y", -1)) if pos is not None else -1
			if px == x and py == y:
				return piece
		return None

	def _on_action_move_pick_overlay_click(self, event: tk.Event) -> str:
		if not self.action_move_pick_waiting:
			return "break"
		board_x, board_y = self.left_board_panel.get_board_xy_from_root(int(event.x_root), int(event.y_root))
		if board_x is None or board_y is None:
			self.right_info_panel.append_content("\n[UI] 请选择棋盘中的合法格子")
			return "break"
		if self.action_pick_mode == "move":
			self.action_move_x_var.set(str(board_x))
			self.action_move_y_var.set(str(board_y))
			self.right_info_panel.append_content(f"\n[UI] 已选定移动目标: ({board_x}, {board_y})")
		elif self.action_pick_mode == "spell_point":
			self.action_spell_point_x_var.set(str(board_x))
			self.action_spell_point_y_var.set(str(board_y))
			self.right_info_panel.append_content(f"\n[UI] 已选定法术施用坐标: ({board_x}, {board_y})")
		elif self.action_pick_mode == "spell_target":
			selected_piece = self._resolve_piece_at_board_xy(board_x, board_y)
			if selected_piece is None:
				self.right_info_panel.append_content("\n[UI] 所点格子没有存活棋子")
				return "break"
			selected_option = self._format_action_target_option(selected_piece)
			if selected_option not in self.action_spell_target_option_map:
				self.right_info_panel.append_content("\n[UI] 所点棋子不是该法术合法目标")
				return "break"
			self.action_spell_target_var.set(selected_option)
			self.right_info_panel.append_content(f"\n[UI] 已选定法术目标: {selected_option}")
		else:
			self.right_info_panel.append_content("\n[UI] 当前不在选点模式")
			return "break"
		self._stop_action_move_point_pick()
		return "break"

	def _begin_action_move_point_pick(self) -> None:
		if self.controller.runtime_source != "runtime_env" or self.controller.environment is None:
			self._set_action_feedback("当前模式不支持棋盘选点", False)
			return
		self._stop_action_move_point_pick()
		self.action_move_pick_waiting = True
		self.action_pick_mode = "move"
		overlay = tk.Toplevel(self.root)
		overlay.overrideredirect(True)
		overlay.attributes("-alpha", 0.01)
		overlay.attributes("-topmost", True)
		overlay.lift(self.root)
		overlay.geometry(
			f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_rootx()}+{self.root.winfo_rooty()}"
		)
		overlay.bind("<Button-1>", self._on_action_move_pick_overlay_click)
		overlay.bind("<ButtonRelease-1>", lambda _e: "break")
		self.action_move_pick_overlay = overlay
		self.right_info_panel.append_content("\n[UI] 棋盘选点模式：请点击一个目标格")

	def _begin_action_spell_point_pick(self) -> None:
		if self.controller.runtime_source != "runtime_env" or self.controller.environment is None:
			self._set_action_feedback("当前模式不支持法术棋盘选点", False)
			return
		self._stop_action_move_point_pick()
		self.action_move_pick_waiting = True
		self.action_pick_mode = "spell_point"
		overlay = tk.Toplevel(self.root)
		overlay.overrideredirect(True)
		overlay.attributes("-alpha", 0.01)
		overlay.attributes("-topmost", True)
		overlay.lift(self.root)
		overlay.geometry(
			f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_rootx()}+{self.root.winfo_rooty()}"
		)
		overlay.bind("<Button-1>", self._on_action_move_pick_overlay_click)
		overlay.bind("<ButtonRelease-1>", lambda _e: "break")
		self.action_move_pick_overlay = overlay
		self.right_info_panel.append_content("\n[UI] 法术坐标选点：请点击施法中心格")

	def _begin_action_spell_target_pick(self) -> None:
		if self.controller.runtime_source != "runtime_env" or self.controller.environment is None:
			self._set_action_feedback("当前模式不支持法术目标选定", False)
			return
		if not self.action_spell_target_option_map:
			self._set_action_feedback("当前法术无有效目标，无法点选", False)
			return
		self._stop_action_move_point_pick()
		self.action_move_pick_waiting = True
		self.action_pick_mode = "spell_target"
		overlay = tk.Toplevel(self.root)
		overlay.overrideredirect(True)
		overlay.attributes("-alpha", 0.01)
		overlay.attributes("-topmost", True)
		overlay.lift(self.root)
		overlay.geometry(
			f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_rootx()}+{self.root.winfo_rooty()}"
		)
		overlay.bind("<Button-1>", self._on_action_move_pick_overlay_click)
		overlay.bind("<ButtonRelease-1>", lambda _e: "break")
		self.action_move_pick_overlay = overlay
		self.right_info_panel.append_content("\n[UI] 法术目标选定：请点击合法目标棋子所在格")

	def _build_runtime_turn_round_status(self) -> str:
		"""构造 runtime 模式下简洁回合信息文本。"""
		env = self.controller.environment
		if self.controller.runtime_source != "runtime_env" or env is None:
			return "【回合信息】当前为非 runtime 模式"

		alive_queue = [
			p
			for p in self._coerce_piece_list(getattr(env, "action_queue", []))
			if bool(getattr(p, "is_alive", True))
		]
		total_alive = len(alive_queue)
		round_display = max(1, int(getattr(env, "round_number", 0)) + 1)

		if total_alive <= 0:
			return f"【回合信息】第{round_display}轮第0/0手，(总共)第{max(0, int(self.runtime_completed_turns))}回合，当前行动：无"

		alive_ids = {int(getattr(p, "id", -1)) for p in alive_queue if int(getattr(p, "id", -1)) >= 0}
		done_count = len(alive_ids.intersection(self.runtime_cycle_done_piece_ids))
		piece_turn_index = min(total_alive, done_count + 1)
		current_piece = self._get_runtime_current_piece(env)
		current_code = self._get_piece_short_code(current_piece) if current_piece is not None else "无"
		total_turn_display = max(1, int(self.runtime_completed_turns) + 1)
		return (
			f"【回合信息】第{round_display}轮第{piece_turn_index}/{total_alive}手，"
			f"(总共)第{total_turn_display}回合，当前行动：{current_code}"
		)

	def _append_runtime_turn_round_status(self) -> None:
		"""将 runtime 回合信息追加到右下区（去重，避免刷屏）。"""
		line = self._build_runtime_turn_round_status()
		if line == self.runtime_last_round_info_line:
			return
		self.runtime_last_round_info_line = line
		self.right_info_panel.append_content(f"\n{line}")

	def _append_runtime_action_log(
		self,
		actor_code: str,
		action_label: str,
		summary: str,
		targets: Optional[list[str]] = None,
		damage_by_target: Optional[dict[str, int]] = None,
	) -> None:
		"""输出简洁行动记录（黑色默认文本），并预留多目标伤害展示。"""
		parts = [f"行动记录：{actor_code} {action_label}，{summary}"]
		if targets:
			if damage_by_target:
				segments = []
				for target in targets:
					dmg = damage_by_target.get(target)
					segments.append(f"{target}({dmg})" if dmg is not None else f"{target}(?)")
				parts.append(f"受击：{'、'.join(segments)}")
			else:
				parts.append(f"目标：{'、'.join(targets)}")
		self.right_info_panel.append_content(f"\n{'；'.join(parts)}")

	def _set_action_feedback(self, message: str, success: bool) -> None:
		label = self.action_feedback_label
		if label is None:
			return
		if self.action_feedback_clear_job is not None:
			try:
				self.root.after_cancel(self.action_feedback_clear_job)
			except Exception:
				pass
			self.action_feedback_clear_job = None
		label.configure(text=message, foreground="#059669" if success else "#dc2626")
		if message:
			self.action_feedback_clear_job = self.root.after(5000, self._clear_action_feedback)

	def _clear_action_feedback(self) -> None:
		self.action_feedback_clear_job = None
		if self.action_feedback_label is not None:
			self.action_feedback_label.configure(text="")

	def _collapse_action_detail(self) -> None:
		self._stop_action_move_point_pick()
		container = self.action_detail_container
		if container is not None:
			for widget in container.winfo_children():
				widget.destroy()
		self.action_mode_body_container = None
		if self.action_confirm_button is not None:
			self.action_confirm_button.pack_forget()
		self.action_ui_mode.set("")
		self.action_spell_target_option_map = {}
		self._refresh_board_view()

	def _switch_action_mode(self, mode: str, body_container: ttk.Frame) -> None:
		self._stop_action_move_point_pick()
		self.action_spell_target_option_map = {}
		self.action_ui_mode.set(mode)
		self.action_mode_body_container = body_container
		for widget in body_container.winfo_children():
			widget.destroy()
		self._render_action_mode_body(body_container)
		if self.action_confirm_button is not None:
			self.action_confirm_button.pack(side="left", padx=(8, 0))
		self._set_action_feedback("", True)
		self._refresh_board_view()

	def _rerender_attack_mode_if_needed(self) -> None:
		if self._rendering_action_mode_body:
			return
		if self.action_ui_mode.get().strip().lower() != "attack":
			return
		container = self.action_mode_body_container
		if container is None:
			return
		for widget in container.winfo_children():
			widget.destroy()
		self._render_action_mode_body(container)
		self._refresh_board_view()

	def _refresh_custom_attack_preview(self) -> None:
		self.action_custom_preview_var.set("")

	def _on_open_custom_attack_advanced_settings(self) -> None:
		return

	def _rerender_spell_mode_if_needed(self) -> None:
		if self._rendering_action_mode_body:
			return
		if self.action_ui_mode.get().strip().lower() != "spell":
			return
		container = self.action_mode_body_container
		if container is None:
			return
		for widget in container.winfo_children():
			widget.destroy()
		self._render_action_mode_body(container)
		self._refresh_board_view()

	def _spell_display_name(self, spell: Any) -> str:
		name = str(getattr(spell, "name", "法术"))
		name_map = {
			"fireball": "火球术",
			"heal": "治疗术",
			"arrow hit": "箭击",
			"arrowhit": "箭击",
			"trap": "陷阱",
			"move": "瞬移",
			"teleport": "瞬移",
		}
		alias = name_map.get(name.lower(), "")
		if alias and alias != name:
			return f"{alias} ({name})"
		return name

	def _spell_effect_key(self, spell: Any) -> str:
		effect = getattr(spell, "effect_type", "")
		text = str(getattr(effect, "value", effect)).strip()
		return text.lower()

	def _collect_available_spell_options(self, caster: Any) -> tuple[list[str], dict[str, Any]]:
		env = self.controller.environment
		if env is None or caster is None:
			return ["法术A"], {}
		fetcher = getattr(env, "get_available_spells", None)
		if not callable(fetcher):
			return ["法术A"], {}
		spells = [s for s in self._coerce_piece_list(fetcher(caster)) if s is not None]
		if not spells:
			return ["法术A"], {}
		option_map: dict[str, Any] = {}
		options: list[str] = []
		for spell in spells:
			name = self._spell_display_name(spell)
			is_locking = bool(getattr(spell, "is_locking_spell", False))
			target_text = "锁定" if is_locking else "非锁定"
			option = f"{name} [{target_text}]"
			option_map[option] = spell
			options.append(option)
		return options, option_map

	def _resolve_selected_spell(self) -> Any:
		selected = self.action_spell_type_var.get().strip()
		return self.action_spell_option_map.get(selected)

	def _collect_spell_target_options(self, spell: Any, caster: Any) -> list[str]:
		env = self.controller.environment
		if env is None or spell is None or caster is None:
			return []
		fetcher = getattr(env, "get_spell_targets", None)
		if callable(fetcher):
			targets = [t for t in self._coerce_piece_list(fetcher(spell, caster)) if t is not None]
			return [self._format_action_target_option(t) for t in targets]
		return []

	def _resolve_spell_target_piece(self, selected_text: str, spell: Any, caster: Any) -> Any:
		mapped_piece = self.action_spell_target_option_map.get(selected_text)
		if mapped_piece is not None:
			return mapped_piece
		env = self.controller.environment
		if env is None:
			return None
		fetcher = getattr(env, "get_spell_targets", None)
		candidates: list[Any] = []
		if callable(fetcher):
			candidates = [t for t in self._coerce_piece_list(fetcher(spell, caster)) if t is not None]
		else:
			candidates = [p for p in self._coerce_piece_list(getattr(env, "action_queue", [])) if bool(getattr(p, "is_alive", False))]
		for piece in candidates:
			if self._format_action_target_option(piece) == selected_text:
				return piece
		return None

	def _collect_area_spell_targets(self, env: Any, caster: Any, spell: Any, area: Any) -> list[Any]:
		effect_key = self._spell_effect_key(spell)
		targets: list[Any] = []
		for piece in self._coerce_piece_list(getattr(env, "action_queue", [])):
			if not bool(getattr(piece, "is_alive", False)):
				continue
			contains = bool(getattr(area, "contains", lambda _p: False)(getattr(piece, "position", None)))
			if not contains:
				continue
			if effect_key in ("damage", "debuff"):
				if int(getattr(piece, "team", -1)) != int(getattr(caster, "team", -2)):
					targets.append(piece)
			elif effect_key in ("heal", "buff"):
				if int(getattr(piece, "team", -1)) == int(getattr(caster, "team", -2)):
					targets.append(piece)
			elif effect_key == "move":
				if piece is caster:
					targets.append(piece)
			else:
				targets.append(piece)
		return targets

	def _is_teleport_spell(self, spell: Any) -> bool:
		effect_key = self._spell_effect_key(spell)
		name = str(getattr(spell, "name", "")).strip().lower()
		return effect_key == "move" or name in ("teleport", "move")

	def _is_trap_spell(self, spell: Any) -> bool:
		name = str(getattr(spell, "name", "")).strip().lower()
		return bool(getattr(spell, "is_delay_spell", False)) or "trap" in name

	def _apply_custom_teleport_spell(self, env: Any, caster: Any, spell: Any, spell_cost: int) -> tuple[bool, str, list[str], dict[str, int]]:
		try:
			tx = int(self.action_spell_point_x_var.get().strip())
			ty = int(self.action_spell_point_y_var.get().strip())
		except Exception:
			return False, "行动失败：请输入合法瞬移坐标", [], {}

		board = getattr(env, "board", None)
		width = int(getattr(board, "width", 0)) if board is not None else 0
		height = int(getattr(board, "height", 0)) if board is not None else 0
		if not (0 <= tx < width and 0 <= ty < height):
			return False, "行动失败：瞬移坐标越界", [], {}

		if board is not None:
			try:
				height_map = getattr(board, "height_map", None)
				if height_map is not None and int(height_map[tx][ty]) == -1:
					return False, "行动失败：目标地块不可传送", [], {}
			except Exception:
				return False, "行动失败：目标地块不可访问", [], {}

		occupant = self._resolve_piece_at_board_xy(tx, ty)
		if occupant is not None and occupant is not caster:
			return False, "行动失败：目标格已有其他棋子", [], {}

		old_pos = getattr(caster, "position", None)
		old_x = int(getattr(old_pos, "x", -1)) if old_pos is not None else -1
		old_y = int(getattr(old_pos, "y", -1)) if old_pos is not None else -1
		if (old_x, old_y) == (tx, ty):
			return False, "行动失败：当前已在目标格", [], {}

		if board is not None:
			try:
				old_cell = board.grid[old_x][old_y]
				new_cell = board.grid[tx][ty]
				old_cell.state = 1
				old_cell.player_id = 0
				old_cell.piece_id = -1
				new_cell.state = 2
				new_cell.player_id = int(getattr(caster, "team", 0))
				new_cell.piece_id = int(getattr(caster, "id", -1))
			except Exception:
				pass

		caster.get_accessor().set_position(Point(tx, ty))
		caster.get_accessor().change_action_points_by(-1)
		caster.get_accessor().change_spell_slots_by(-spell_cost)
		summary = f"瞬移到({tx},{ty})，AP/SP 已消耗"
		return True, summary, [], {}

	def _place_runtime_trap_spell(self, env: Any, caster: Any, spell: Any, spell_cost: int) -> tuple[bool, str, list[str], dict[str, int]]:
		try:
			tx = int(self.action_spell_point_x_var.get().strip())
			ty = int(self.action_spell_point_y_var.get().strip())
		except Exception:
			return False, "行动失败：请输入合法陷阱坐标", [], {}

		board = getattr(env, "board", None)
		width = int(getattr(board, "width", 0)) if board is not None else 0
		height = int(getattr(board, "height", 0)) if board is not None else 0
		if not (0 <= tx < width and 0 <= ty < height):
			return False, "行动失败：陷阱坐标越界", [], {}

		base_lifespan = max(1, int(getattr(spell, "base_lifespan", 1)))
		base_value = max(0, int(getattr(spell, "base_value", 0)))
		trap = {
			"x": tx,
			"y": ty,
			"remaining": base_lifespan,
			"damage": base_value,
			"spell_name": self._spell_display_name(spell),
			"caster_team": int(getattr(caster, "team", -1)),
		}
		self.runtime_trap_effects.append(trap)
		caster.get_accessor().change_action_points_by(-1)
		caster.get_accessor().change_spell_slots_by(-spell_cost)

		# 若该格已有“非当前行动”的棋子，则陷阱在施放完成后立即触发并消失。
		occupant = self._resolve_piece_at_board_xy(tx, ty)
		if occupant is not None and occupant is not caster and bool(getattr(occupant, "is_alive", True)):
			self._try_trigger_runtime_trap_on_piece(
				env,
				occupant,
				reason="施放完成触发",
			)

		summary = f"在({tx},{ty})放置陷阱，持续{base_lifespan}回合"
		return True, summary, [], {}

	def _pop_runtime_trap_at_xy(self, x: int, y: int) -> dict[str, Any] | None:
		for trap in list(self.runtime_trap_effects):
			if int(trap.get("remaining", 0)) <= 0:
				continue
			if int(trap.get("x", -1)) == int(x) and int(trap.get("y", -1)) == int(y):
				try:
					self.runtime_trap_effects.remove(trap)
				except ValueError:
					pass
				return trap
		return None

	def _handle_death_check_if_possible(self, env: Any, piece: Any) -> None:
		if env is None or piece is None:
			return
		try:
			hp = int(getattr(piece, "health", 0))
		except Exception:
			hp = 0
		if hp < 0:
			try:
				piece.get_accessor().set_health_to(0)
			except Exception:
				setattr(piece, "health", 0)
			hp = 0
		# 仅当 HP==0 才触发死亡检定（0 才是死亡；负数视为非法并夹到 0）。
		if hp != 0:
			return
		try:
			if callable(getattr(env, "handle_death_check", None)):
				env.handle_death_check(piece)
		except Exception:
			return

	def _try_trigger_runtime_trap_on_piece(self, env: Any, piece: Any, *, reason: str) -> int | None:
		if piece is None or not bool(getattr(piece, "is_alive", True)):
			return None
		pos = getattr(piece, "position", None)
		x = int(getattr(pos, "x", -1)) if pos is not None else -1
		y = int(getattr(pos, "y", -1)) if pos is not None else -1
		trap = self._pop_runtime_trap_at_xy(x, y)
		if trap is None:
			return None

		damage = max(0, int(trap.get("damage", 0)))
		old_hp = int(getattr(piece, "health", 0))
		try:
			if callable(getattr(piece, "receive_damage", None)):
				piece.receive_damage(damage, "physical")
			else:
				setattr(piece, "health", max(0, old_hp - damage))
		except Exception:
			setattr(piece, "health", max(0, old_hp - damage))
		new_hp = int(getattr(piece, "health", 0))
		if new_hp < 0:
			try:
				piece.get_accessor().set_health_to(0)
			except Exception:
				setattr(piece, "health", 0)
			new_hp = 0
		real = max(0, old_hp - new_hp)
		code = self._get_piece_short_code(piece)

		self._handle_death_check_if_possible(env, piece)
		self._append_runtime_action_log(
			actor_code="TRAP",
			action_label=f"触发@({x},{y})",
			summary=f"{reason}，造成{real}点伤害，陷阱消失",
			targets=[code],
			damage_by_target={code: real},
		)
		self._append_runtime_death_and_game_over_info(piece, code)
		return real

	def _tick_runtime_traps(self, env: Any, *, round_advanced: bool) -> None:
		"""按“回合”更新陷阱寿命。

		- 每进入新一轮(所有存活棋子行动时段结束一次)才递减 remaining
		- remaining 归零的陷阱自动消散
		- 触发伤害由动作执行后/行动时段结束时单独判定
		"""
		if not round_advanced or not self.runtime_trap_effects:
			return
		next_traps: list[dict[str, Any]] = []
		for trap in self.runtime_trap_effects:
			remaining = int(trap.get("remaining", 0)) - 1
			if remaining <= 0:
				continue
			trap["remaining"] = remaining
			next_traps.append(trap)
		self.runtime_trap_effects = next_traps

	def _append_attack_formula_info(
		self,
		attack_type: str,
		attacker: Any,
		target: Any,
		*,
		attack_roll: int | None,
		raw_damage: int,
		real_damage: int,
		is_hit: bool,
	) -> None:
		env = self.controller.environment
		if env is None:
			return
		step_func = getattr(env, "step_modified_func", None)
		if not callable(step_func):
			return

		snapshot = getattr(env, "_ui_action_settings_snapshot", None)
		if not isinstance(snapshot, dict) or not snapshot:
			snapshot = self.action_settings_snapshot if isinstance(self.action_settings_snapshot, dict) else self._default_action_settings_snapshot()
		attack_model = snapshot.get("attack_model", {}) if isinstance(snapshot, dict) else {}
		enable_d20 = bool(attack_model.get("enable_d20", True))
		hit_cfg = attack_model.get("hit", {}) if isinstance(attack_model.get("hit"), dict) else {}
		magic_hit_cfg = attack_model.get("magic_hit", {}) if isinstance(attack_model.get("magic_hit"), dict) else {}
		phy_dmg_cfg = attack_model.get("physical_damage", {}) if isinstance(attack_model.get("physical_damage"), dict) else {}
		mag_dmg_cfg = attack_model.get("magic_damage", {}) if isinstance(attack_model.get("magic_damage"), dict) else {}
		fail_on_1 = bool(hit_cfg.get("fail_on_1", True))
		crit_on_20 = bool(hit_cfg.get("crit_on_20", True))

		advantage_func = getattr(env, "calculate_advantage_value", None)
		advantage_impl = callable(advantage_func)
		adv_value = 0
		if advantage_impl:
			try:
				adv_value = int(advantage_func(attacker, target))
			except Exception:
				adv_value = 0

		attack_name = "物理攻击" if attack_type == "物理攻击" else "普通法术攻击"
		roll_value = int(attack_roll) if (attack_roll is not None and enable_d20) else (0 if not enable_d20 else -1)

		if attack_type == "普通法术攻击":
			bonus_flat = float(magic_hit_cfg.get("bonus_flat", 0.0) or 0.0)
			coeff_int = float(magic_hit_cfg.get("coeff_intelligence", 1.0) or 1.0)
			adv_coeff = float(magic_hit_cfg.get("coeff_advantage", 1.0) or 1.0)
			def_attr = magic_hit_cfg.get("defense_modifier_attr", None)
			def_base_coeff = float(magic_hit_cfg.get("defense_base_coeff", 1.0) or 1.0)
			def_attr_coeff = float(magic_hit_cfg.get("defense_attr_coeff", 1.0) or 1.0)
			def_flat_bonus = float(magic_hit_cfg.get("defense_flat_bonus", 0.0) or 0.0)
			attack_part = int(step_func(int(getattr(attacker, "intelligence", 0))))
			attack_score = (float(max(0, roll_value)) + bonus_flat + coeff_int * float(attack_part) + adv_coeff * float(adv_value)) if roll_value >= 0 else None
			base_def = float(getattr(target, "magic_resist", 0))
			attr_def = float(step_func(int(getattr(target, str(def_attr), 0)))) if def_attr not in (None, "", "none") else 0.0
			defense_score = def_base_coeff * base_def + def_attr_coeff * attr_def + def_flat_bonus
			symbol = ">" if (attack_score is not None and attack_score > defense_score) else "<="

			if enable_d20 and roll_value == 1 and fail_on_1:
				self.right_info_panel.append_content(
					f"\n[公式] {attack_name}命中判定：天然1直接未命中（roll=1）"
				)
			elif enable_d20 and roll_value == 20 and crit_on_20:
				self.right_info_panel.append_content(
					f"\n[公式] {attack_name}命中判定：天然20直接命中（roll=20）"
				)
			elif attack_score is not None:
				self.right_info_panel.append_content(
					f"\n[公式] {attack_name}命中判定：{roll_value}(投掷)+{bonus_flat:.1f}(加值)+{coeff_int:.1f}*{attack_part}(智力修正)+{adv_coeff:.1f}*{adv_value:.0f}(优势) {symbol} "
					f"{def_base_coeff:.1f}*{int(base_def)}(法抗)+{def_attr_coeff:.1f}*{int(attr_def)}(防御修正)+{def_flat_bonus:.1f}(加值)；即 {attack_score:.1f} {symbol} {defense_score:.1f}"
				)
			else:
				self.right_info_panel.append_content(f"\n[公式] {attack_name}命中判定：未捕获到投掷值")

			if not advantage_impl:
				self.right_info_panel.append_content("\n[公式] 优势值：未实现，按 0 处理")

			resist_part = int(getattr(target, "magic_resist", 0))
			base_from_piece = bool(mag_dmg_cfg.get("base_from_piece", True))
			base_override = mag_dmg_cfg.get("base_override", None)
			if base_from_piece:
				base_damage = int(getattr(attacker, "magic_damage", 0))
				base_label = "法伤"
			else:
				try:
					base_damage = int(float(base_override)) if base_override is not None else 0
				except Exception:
					base_damage = 0
				base_label = "设定值"
			if not is_hit:
				self.right_info_panel.append_content(f"\n[公式] 伤害计算：未命中，本次原始伤害=0；实际伤害=0")
			else:
				crit_text = " x2(暴击)" if (enable_d20 and roll_value == 20 and crit_on_20) else ""
				self.right_info_panel.append_content(
					f"\n[公式] 伤害计算：原始伤害={base_damage}({base_label}){crit_text}={raw_damage}；实际伤害=max(0, {raw_damage}-{resist_part})={real_damage}"
				)
			return

		bonus_flat = float(hit_cfg.get("bonus_flat", 0.0) or 0.0)
		coeff_strength = float(hit_cfg.get("coeff_strength", 1.0) or 1.0)
		adv_coeff = float(hit_cfg.get("coeff_advantage", 1.0) or 1.0)
		def_attr = hit_cfg.get("defense_modifier_attr", "dexterity")
		def_base_coeff = float(hit_cfg.get("defense_base_coeff", 1.0) or 1.0)
		def_attr_coeff = float(hit_cfg.get("defense_attr_coeff", 1.0) or 1.0)
		def_flat_bonus = float(hit_cfg.get("defense_flat_bonus", 0.0) or 0.0)
		strength_part = int(step_func(int(getattr(attacker, "strength", 0))))
		resist_part = int(getattr(target, "physical_resist", 0))
		attack_score = (float(max(0, roll_value)) + bonus_flat + coeff_strength * float(strength_part) + adv_coeff * float(adv_value)) if roll_value >= 0 else None
		attr_def = float(step_func(int(getattr(target, str(def_attr), 0)))) if def_attr not in (None, "", "none") else 0.0
		defense_score = def_base_coeff * float(resist_part) + def_attr_coeff * float(attr_def) + def_flat_bonus
		symbol = ">" if (attack_score is not None and attack_score > defense_score) else "<="

		if enable_d20 and roll_value == 1 and fail_on_1:
			self.right_info_panel.append_content(
				f"\n[公式] {attack_name}命中判定：天然1直接未命中（roll=1）"
			)
		elif enable_d20 and roll_value == 20 and crit_on_20:
			self.right_info_panel.append_content(
				f"\n[公式] {attack_name}命中判定：天然20直接命中（roll=20）"
			)
		elif attack_score is not None:
			self.right_info_panel.append_content(
				f"\n[公式] {attack_name}命中判定：{roll_value}(投掷)+{bonus_flat:.1f}(加值)+{coeff_strength:.1f}*{strength_part}(力量修正)+{adv_coeff:.1f}*{adv_value:.0f}(优势) {symbol} "
				f"{def_base_coeff:.1f}*{resist_part}(物抗)+{def_attr_coeff:.1f}*{int(attr_def)}(防御修正)+{def_flat_bonus:.1f}(加值)；即 {attack_score:.1f} {symbol} {defense_score:.1f}"
			)
		else:
			self.right_info_panel.append_content(f"\n[公式] {attack_name}命中判定：未捕获到投掷值")

		if not advantage_impl:
			self.right_info_panel.append_content("\n[公式] 优势值：未实现，按 0 处理")

		base_from_piece = bool(phy_dmg_cfg.get("base_from_piece", True))
		base_override = phy_dmg_cfg.get("base_override", None)
		if base_from_piece:
			base_damage = int(getattr(attacker, "physical_damage", 0))
			base_label = "物伤"
		else:
			try:
				base_damage = int(float(base_override)) if base_override is not None else 0
			except Exception:
				base_damage = 0
			base_label = "设定值"
		if not is_hit:
			self.right_info_panel.append_content(
				f"\n[公式] 伤害计算：未命中，本次原始伤害=0；实际伤害=0"
			)
		else:
			crit_text = " x2(暴击)" if (enable_d20 and roll_value == 20 and crit_on_20) else ""
			self.right_info_panel.append_content(
				f"\n[公式] 伤害计算：原始伤害={base_damage}({base_label}){crit_text}={raw_damage}；"
				f"实际伤害=max(0, {raw_damage}-{resist_part})={real_damage}"
			)

	def _append_runtime_death_and_game_over_info(self, target_piece: Any, target_code: str) -> None:
		env = self.controller.environment
		if env is None:
			return
		if target_piece is not None and (not self._is_piece_alive_by_hp(target_piece)):
			self.right_info_panel.append_content(f"\n棋子 {target_code} 已死亡")
		self._check_and_announce_runtime_game_over(env, show_dialog=True)

	def _render_action_mode_body(self, body_container: ttk.Frame) -> None:
		self._rendering_action_mode_body = True
		try:
			mode = self.action_ui_mode.get().strip().lower()

			if mode == "move":
				row = ttk.Frame(body_container)
				row.pack(fill="x")
				actor_text = self._get_current_actor_text()
				self.action_move_piece_var.set(actor_text)
				ttk.Label(row, text="移动").pack(side="left")
				ttk.Entry(row, textvariable=self.action_move_piece_var, width=12, state="readonly").pack(side="left", padx=(4, 4))
				ttk.Label(row, text="到 (").pack(side="left")
				tk.Entry(row, textvariable=self.action_move_x_var, width=3).pack(side="left")
				ttk.Label(row, text=", ").pack(side="left")
				tk.Entry(row, textvariable=self.action_move_y_var, width=3).pack(side="left")
				ttk.Label(row, text=")").pack(side="left")
				ttk.Button(row, text="棋盘选点", command=self._begin_action_move_point_pick).pack(side="left", padx=(6, 0))
				return

			target_options = self._collect_action_target_options()

			if mode == "attack":
				attack_types = ["物理攻击", "普通法术攻击", "定制攻击"]
				if not self.action_attack_target_var.get().strip() or self.action_attack_target_var.get() not in target_options:
					self.action_attack_target_var.set(target_options[0])
				if not self.action_attack_type_var.get().strip() or self.action_attack_type_var.get() not in attack_types:
					self.action_attack_type_var.set(attack_types[0])

				row = ttk.Frame(body_container)
				row.pack(fill="x")
				ttk.Label(row, text="对").pack(side="left")
				ttk.Combobox(
					row,
					textvariable=self.action_attack_target_var,
					values=target_options,
					state="readonly",
					width=18,
				).pack(side="left", padx=(4, 4))
				ttk.Label(row, text="使用").pack(side="left")
				attack_type_combo = ttk.Combobox(
					row,
					textvariable=self.action_attack_type_var,
					values=attack_types,
					state="readonly",
					width=12,
				)
				attack_type_combo.pack(side="left", padx=(4, 4))
				attack_type_combo.bind("<<ComboboxSelected>>", lambda _e: self._rerender_attack_mode_if_needed())
				ttk.Label(row, text="。").pack(side="left")

				if self.action_attack_type_var.get().strip() == "定制攻击":
					row2 = ttk.Frame(body_container)
					row2.pack(fill="x", pady=(6, 0))
					ttk.Label(row2, text="造成").pack(side="left")
					tk.Entry(row2, textvariable=self.action_custom_damage_var, width=6).pack(side="left", padx=(4, 4))
					ttk.Label(row2, text="真实伤害").pack(side="left", padx=(0, 8))
					ttk.Button(row2, text="高级设置", command=self._on_open_custom_attack_advanced_settings).pack(side="left", padx=(0, 8))
					ttk.Label(row2, text="(测试用)", foreground="#6b7280").pack(side="left")
				return

			env = self.controller.environment
			caster = self._get_runtime_current_piece(env) if env is not None else None
			spell_options, spell_option_map = self._collect_available_spell_options(caster)
			self.action_spell_option_map = spell_option_map
			if not self.action_spell_type_var.get().strip() or self.action_spell_type_var.get() not in spell_options:
				self.action_spell_type_var.set(spell_options[0])

			row1 = ttk.Frame(body_container)
			row1.pack(fill="x")
			ttk.Label(row1, text="施用").pack(side="left")
			spell_combo = ttk.Combobox(
				row1,
				textvariable=self.action_spell_type_var,
				values=spell_options,
				state="readonly",
				width=26,
			)
			spell_combo.pack(side="left", padx=(4, 4))
			spell_combo.bind("<<ComboboxSelected>>", lambda _e: self._rerender_spell_mode_if_needed())
			ttk.Label(row1, text="法术。").pack(side="left")

			selected_spell = self._resolve_selected_spell()
			if selected_spell is None:
				return

			is_locking_spell = bool(getattr(selected_spell, "is_locking_spell", False)) and not self._is_teleport_spell(selected_spell)
			row2 = ttk.Frame(body_container)
			row2.pack(fill="x", pady=(6, 0))
			if is_locking_spell:
				target_candidates = self._collect_spell_target_options(selected_spell, caster)
				self.action_spell_target_option_map = {}
				for option in target_candidates:
					piece = self._resolve_spell_target_piece(option, selected_spell, caster)
					if piece is not None:
						self.action_spell_target_option_map[option] = piece
				if not target_candidates:
					target_candidates = ["无有效目标"]
				if not self.action_spell_target_var.get().strip() or self.action_spell_target_var.get() not in target_candidates:
					self.action_spell_target_var.set(target_candidates[0])
				ttk.Label(row2, text="对").pack(side="left")
				ttk.Combobox(
					row2,
					textvariable=self.action_spell_target_var,
					values=target_candidates,
					state="readonly",
					width=18,
				).pack(side="left", padx=(4, 4))
				ttk.Button(row2, text="棋子点选", command=self._begin_action_spell_target_pick).pack(side="left", padx=(4, 4))
				ttk.Label(row2, text="施用").pack(side="left")
			else:
				self.action_spell_target_option_map = {}
				ttk.Label(row2, text="在 (").pack(side="left")
				tk.Entry(row2, textvariable=self.action_spell_point_x_var, width=4).pack(side="left")
				ttk.Label(row2, text=", ").pack(side="left")
				tk.Entry(row2, textvariable=self.action_spell_point_y_var, width=4).pack(side="left")
				ttk.Label(row2, text=") 处施用").pack(side="left")
				ttk.Button(row2, text="棋盘选点", command=self._begin_action_spell_point_pick).pack(side="left", padx=(4, 4))
			ttk.Label(row2, text="。", foreground="#6b7280").pack(side="left")
		finally:
			self._rendering_action_mode_body = False

	def _on_preview_submit_action(self) -> None:
		mode = self.action_ui_mode.get().strip().lower()
		if mode not in ("move", "attack", "spell"):
			self._set_action_feedback("请先选择行动类型", False)
			return
		if mode == "move":
			action, message = self._build_move_action_from_ui()
			if action is None:
				self.right_info_panel.append_content(f"\n[UI] 移动提交失败：{message}")
				self._set_action_feedback(f"行动失败：{message}", False)
				return
			env = self.controller.environment
			if env is None:
				self._set_action_feedback("行动失败：环境未初始化", False)
				return
			current_piece = self._get_runtime_current_piece(env)
			if current_piece is None:
				self._set_action_feedback("行动失败：未定位到当前行动棋子", False)
				return

			old_pos = getattr(current_piece, "position", None)
			old_x = int(getattr(old_pos, "x", -1)) if old_pos is not None else -1
			old_y = int(getattr(old_pos, "y", -1)) if old_pos is not None else -1
			old_ap = int(getattr(current_piece, "action_points", 0))
			setattr(env, "current_piece", current_piece)
			target_x = int(getattr(action.move_target, "x", -1))
			target_y = int(getattr(action.move_target, "y", -1))

			env.execute_player_action(action)

			# 仅在 UI 层兜底：若 env 只更新棋盘占位而未同步 piece.position，则在这里补齐。
			board_after = getattr(env, "board", None)
			try:
				if board_after is not None:
					cell_after = board_after.grid[target_x][target_y]
					if int(getattr(cell_after, "state", 0)) == 2 and int(getattr(cell_after, "piece_id", -1)) == int(getattr(current_piece, "id", -2)):
						accessor = current_piece.get_accessor()
						accessor.set_position(Point(target_x, target_y))
			except Exception:
				pass

			new_pos = getattr(current_piece, "position", None)
			new_x = int(getattr(new_pos, "x", -1)) if new_pos is not None else -1
			new_y = int(getattr(new_pos, "y", -1)) if new_pos is not None else -1
			new_ap = int(getattr(current_piece, "action_points", 0))

			if (new_x, new_y) != (target_x, target_y):
				self._set_action_feedback("行动失败：移动未生效（非法路径或规则限制）", False)
				self.right_info_panel.append_content(
					f"\n[UI] 移动失败：{self._get_piece_short_code(current_piece)} 仍在 ({new_x}, {new_y})"
				)
				return

			self._append_runtime_action_log(
				actor_code=self._get_piece_short_code(current_piece),
				action_label="移动",
				summary=f"({old_x}, {old_y}) -> ({new_x}, {new_y})，AP {old_ap}->{new_ap}",
			)
			self._try_trigger_runtime_trap_on_piece(env, current_piece, reason="移动完成触发")
			self._set_action_feedback("行动成功", True)
			self._update_cards_from_env()
			self._refresh_piece_cards()
			self._refresh_board_view()
			return
		elif mode == "attack":
			env = self.controller.environment
			if env is None:
				self._set_action_feedback("行动失败：环境未初始化", False)
				return

			current_piece = self._get_runtime_current_piece(env)
			if current_piece is None:
				self._set_action_feedback("行动失败：未定位到当前行动棋子", False)
				return

			target_label = self.action_attack_target_var.get().strip()
			target_piece = self._resolve_action_target_piece(target_label)
			if target_piece is None:
				self._set_action_feedback("行动失败：攻击目标无效", False)
				self.right_info_panel.append_content(f"\n[UI] 攻击失败：无法识别目标 {target_label or '目标'}")
				return

			attack_type = self.action_attack_type_var.get().strip() or "物理攻击"
			target_code = self._get_piece_short_code(target_piece)
			old_ap = int(getattr(current_piece, "action_points", 0))
			old_hp = int(getattr(target_piece, "health", 0))

			if attack_type == "定制攻击":
				try:
					custom_damage = int(self.action_custom_damage_var.get().strip())
				except Exception:
					self._set_action_feedback("行动失败：真实伤害必须是整数", False)
					return
				if custom_damage <= 0:
					self._set_action_feedback("行动失败：真实伤害必须大于 0", False)
					return

				target_piece.get_accessor().set_health_to(max(old_hp - custom_damage, 0))
				if int(getattr(target_piece, "health", 0)) == 0:
					env.handle_death_check(target_piece)
				self._append_runtime_action_log(
					actor_code=self._get_piece_short_code(current_piece),
					action_label="定制攻击",
					summary=f"对{target_code}造成{custom_damage}点真实伤害（不受AP/范围限制）",
					targets=[target_code],
					damage_by_target={target_code: custom_damage},
				)
				self._append_runtime_death_and_game_over_info(target_piece, target_code)
				self._set_action_feedback("行动成功", True)
				self._update_cards_from_env()
				self._refresh_piece_cards()
				self._refresh_board_view()
				return

			if int(getattr(current_piece, "action_points", 0)) <= 0:
				self._set_action_feedback("行动失败：当前棋子行动位不足", False)
				return

			if not bool(env.is_in_attack_range(current_piece, target_piece)):
				self._set_action_feedback("行动失败：本次攻击无法执行，超出攻击范围", False)
				self.right_info_panel.append_content("\n[UI] 攻击失败：本次攻击无法执行，超出攻击范围")
				return

			attack_label = "物理攻击" if attack_type == "物理攻击" else "普通法术攻击"
			attack_roll: int | None = None
			raw_damage = 0
			is_hit: bool | None = None
			# 读取“行动设置（本局）”快照：若未应用则使用默认。
			snapshot = getattr(env, "_ui_action_settings_snapshot", None)
			if not isinstance(snapshot, dict) or not snapshot:
				snapshot = self.action_settings_snapshot if isinstance(self.action_settings_snapshot, dict) else self._default_action_settings_snapshot()
			attack_model = snapshot.get("attack_model", {}) if isinstance(snapshot, dict) else {}
			enable_d20 = bool(attack_model.get("enable_d20", True))
			hit_cfg = attack_model.get("hit", {}) if isinstance(attack_model.get("hit"), dict) else {}
			magic_hit_cfg = attack_model.get("magic_hit", {}) if isinstance(attack_model.get("magic_hit"), dict) else {}
			phy_dmg_cfg = attack_model.get("physical_damage", {}) if isinstance(attack_model.get("physical_damage"), dict) else {}
			mag_dmg_cfg = attack_model.get("magic_damage", {}) if isinstance(attack_model.get("magic_damage"), dict) else {}
			fail_on_1 = bool(hit_cfg.get("fail_on_1", True))
			crit_on_20 = bool(hit_cfg.get("crit_on_20", True))

			if attack_type == "物理攻击":
				attack_context = AttackContext()
				attack_context.attacker = current_piece
				attack_context.target = target_piece

				action = ActionSet()
				action.move = False
				action.attack = True
				action.attack_context = attack_context
				action.spell = False

				setattr(env, "current_piece", current_piece)
				captured_rolls: list[int] = []
				original_roll = getattr(env, "roll_dice", None)
				wrapped_roll = False
				if callable(original_roll):
					def _roll_proxy(n: int, sides: int):
						value = original_roll(n, sides)
						if int(n) == 1 and int(sides) == 20:
							captured_rolls.append(int(value))
						return value
					setattr(env, "roll_dice", _roll_proxy)
					wrapped_roll = True
				try:
					env.execute_player_action(action)
				finally:
					if wrapped_roll:
						setattr(env, "roll_dice", original_roll)

				attack_roll = int(captured_rolls[0]) if captured_rolls else None
				raw_damage = int(getattr(attack_context, "damage_dealt", 0))
				# 说明：伤害可能为 0（例如基础伤害为 0），但仍可能“命中”。命中判定按行动设置公式计算。
				try:
					step_func = getattr(env, "step_modified_func", None)
					advantage_func = getattr(env, "calculate_advantage_value", None)
					if not callable(step_func):
						is_hit = None
					else:
						roll_val = int(attack_roll or 0) if enable_d20 else 0
						bonus_flat = float(hit_cfg.get("bonus_flat", 0.0) or 0.0)
						coeff_strength = float(hit_cfg.get("coeff_strength", 1.0) or 1.0)
						adv_coeff = float(hit_cfg.get("coeff_dexterity", 1.0) or 1.0)
						def_attr = hit_cfg.get("defense_modifier_attr", "dexterity")
						def_base_coeff = float(hit_cfg.get("defense_base_coeff", 1.0) or 1.0)
						def_attr_coeff = float(hit_cfg.get("defense_attr_coeff", 1.0) or 1.0)
						def_flat_bonus = float(hit_cfg.get("defense_flat_bonus", 0.0) or 0.0)
						adv_value = 0.0
						if callable(advantage_func):
							try:
								adv_value = float(advantage_func(current_piece, target_piece))
							except Exception:
								adv_value = 0.0
						if enable_d20 and roll_val == 1 and fail_on_1:
							is_hit = False
						elif enable_d20 and roll_val == 20 and crit_on_20:
							is_hit = True
						else:
							attack_score = float(roll_val) + bonus_flat + coeff_strength * float(step_func(int(getattr(current_piece, "strength", 0)))) + adv_coeff * float(adv_value)
							base_def = float(getattr(target_piece, "physical_resist", 0))
							attr_def = 0.0
							if def_attr not in (None, "", "none"):
								attr_def = float(step_func(int(getattr(target_piece, str(def_attr), 0))))
							defense_score = def_base_coeff * base_def + def_attr_coeff * attr_def + def_flat_bonus
							is_hit = bool(attack_score > defense_score)
				except Exception:
					is_hit = None
			else:
				step_func = getattr(env, "step_modified_func", None)
				if not callable(step_func):
					self._set_action_feedback("行动失败：普通法术攻击缺少规则函数", False)
					return
				advantage_func = getattr(env, "calculate_advantage_value", None)
				adv_value = 0.0
				if callable(advantage_func):
					try:
						adv_value = float(advantage_func(current_piece, target_piece))
					except Exception:
						adv_value = 0.0

				roll_val = 0
				if enable_d20 and callable(getattr(env, "roll_dice", None)):
					roll_val = int(getattr(env, "roll_dice")(1, 20))
				attack_roll = roll_val if enable_d20 else None

				bonus_flat = float(magic_hit_cfg.get("bonus_flat", 0.0) or 0.0)
				coeff_int = float(magic_hit_cfg.get("coeff_intelligence", 1.0) or 1.0)
				adv_coeff = float(magic_hit_cfg.get("coeff_advantage", 1.0) or 1.0)
				def_attr = magic_hit_cfg.get("defense_modifier_attr", None)
				def_base_coeff = float(magic_hit_cfg.get("defense_base_coeff", 1.0) or 1.0)
				def_attr_coeff = float(magic_hit_cfg.get("defense_attr_coeff", 1.0) or 1.0)
				def_flat_bonus = float(magic_hit_cfg.get("defense_flat_bonus", 0.0) or 0.0)

				is_critical = False
				if enable_d20 and roll_val == 1 and fail_on_1:
					is_hit = False
				elif enable_d20 and roll_val == 20 and crit_on_20:
					is_hit = True
					is_critical = True
				else:
					attack_score = float(roll_val if enable_d20 else 0) + bonus_flat + coeff_int * float(step_func(int(getattr(current_piece, "intelligence", 0)))) + adv_coeff * float(adv_value)
					base_def = float(getattr(target_piece, "magic_resist", 0))
					attr_def = 0.0
					if def_attr not in (None, "", "none"):
						attr_def = float(step_func(int(getattr(target_piece, str(def_attr), 0))))
					defense_score = def_base_coeff * base_def + def_attr_coeff * attr_def + def_flat_bonus
					is_hit = bool(attack_score > defense_score)

				if is_hit:
					base_from_piece = bool(mag_dmg_cfg.get("base_from_piece", True))
					base_override = mag_dmg_cfg.get("base_override", None)
					flat_bonus = float(mag_dmg_cfg.get("flat_bonus", 0.0) or 0.0)
					if base_from_piece:
						base = float(getattr(current_piece, "magic_damage", 0))
					else:
						try:
							base = float(base_override) if base_override is not None else 0.0
						except Exception:
							base = 0.0
					damage = max(0.0, base + flat_bonus)
					if is_critical:
						damage *= 2
					int_damage = int(round(damage))
					raw_damage = int_damage
					target_piece.receive_damage(int_damage, "magic")
					new_hp_tmp = int(getattr(target_piece, "health", 0))
					if new_hp_tmp < 0:
						try:
							target_piece.get_accessor().set_health_to(0)
						except Exception:
							setattr(target_piece, "health", 0)
						new_hp_tmp = 0
					if new_hp_tmp == 0:
						env.handle_death_check(target_piece)

				current_piece.get_accessor().change_action_points_by(-1)

			new_ap = int(getattr(current_piece, "action_points", 0))
			new_hp = int(getattr(target_piece, "health", 0))
			real_damage = max(0, old_hp - new_hp)

			# 命中与否不能用 raw_damage>0 推断（基础伤害可能为 0）。
			resolved_hit = bool(is_hit) if isinstance(is_hit, bool) else bool(raw_damage != 0 or real_damage != 0)
			if resolved_hit:
				summary = f"命中，造成{real_damage}点伤害，AP {old_ap}->{new_ap}"
			else:
				summary = f"未命中，AP {old_ap}->{new_ap}"

			self._append_runtime_action_log(
				actor_code=self._get_piece_short_code(current_piece),
				action_label=attack_label,
				summary=summary,
				targets=[target_code],
				damage_by_target={target_code: real_damage},
			)
			self._append_attack_formula_info(
				attack_label,
				current_piece,
				target_piece,
				attack_roll=attack_roll,
				raw_damage=raw_damage,
				real_damage=real_damage,
				is_hit=resolved_hit,
			)
			self._append_runtime_death_and_game_over_info(target_piece, target_code)
			self._set_action_feedback("行动成功", True)
			self._update_cards_from_env()
			self._refresh_piece_cards()
			self._refresh_board_view()
			return
		else:
			env = self.controller.environment
			if env is None:
				self._set_action_feedback("行动失败：环境未初始化", False)
				return

			caster = self._get_runtime_current_piece(env)
			if caster is None:
				self._set_action_feedback("行动失败：未定位到当前行动棋子", False)
				return

			spell = self._resolve_selected_spell()
			if spell is None:
				self._set_action_feedback("行动失败：法术无效", False)
				return

			old_ap = int(getattr(caster, "action_points", 0))
			old_sp = int(getattr(caster, "spell_slots", 0))
			if old_ap <= 0:
				self._set_action_feedback("行动失败：当前棋子行动位不足", False)
				return

			spell_cost = int(getattr(spell, "spell_cost", 1))
			if old_sp < spell_cost:
				self._set_action_feedback("行动失败：当前棋子法术位不足", False)
				return

			spell_name = self._spell_display_name(spell)
			spell_range = float(getattr(spell, "range", 0.0))
			is_locking_spell = bool(getattr(spell, "is_locking_spell", False))
			area_radius = int(getattr(spell, "area_radius", 0))
			is_teleport_spell = self._is_teleport_spell(spell)
			is_trap_spell = self._is_trap_spell(spell)

			target_piece = None
			target_area = None
			target_codes: list[str] = []
			target_pieces: list[Any] = []
			before_hp: dict[int, int] = {}

			caster_pos = getattr(caster, "position", None)
			caster_x = int(getattr(caster_pos, "x", -1)) if caster_pos is not None else -1
			caster_y = int(getattr(caster_pos, "y", -1)) if caster_pos is not None else -1

			if is_teleport_spell:
				success, summary, target_codes, damage_by_target = self._apply_custom_teleport_spell(env, caster, spell, spell_cost)
				if not success:
					self._set_action_feedback(summary, False)
					return
				self._append_runtime_action_log(
					actor_code=self._get_piece_short_code(caster),
					action_label=f"法术:{spell_name}",
					summary=summary,
					targets=target_codes,
					damage_by_target=damage_by_target,
				)
				self._try_trigger_runtime_trap_on_piece(env, caster, reason="位移完成触发")
				self._set_action_feedback("行动成功", True)
				self._update_cards_from_env()
				self._refresh_piece_cards()
				self._refresh_board_view()
				return

			if is_trap_spell:
				success, summary, target_codes, damage_by_target = self._place_runtime_trap_spell(env, caster, spell, spell_cost)
				if not success:
					self._set_action_feedback(summary, False)
					return
				self._append_runtime_action_log(
					actor_code=self._get_piece_short_code(caster),
					action_label=f"法术:{spell_name}",
					summary=summary,
					targets=target_codes,
					damage_by_target=damage_by_target,
				)
				self._set_action_feedback("行动成功", True)
				self._update_cards_from_env()
				self._refresh_piece_cards()
				self._refresh_board_view()
				return

			if is_locking_spell:
				target_text = self.action_spell_target_var.get().strip()
				target_piece = self._resolve_spell_target_piece(target_text, spell, caster)
				if target_piece is None:
					self._set_action_feedback("行动失败：法术目标无效", False)
					return
				target_pos = getattr(target_piece, "position", None)
				tx = int(getattr(target_pos, "x", -1)) if target_pos is not None else -1
				ty = int(getattr(target_pos, "y", -1)) if target_pos is not None else -1
				distance = ((caster_x - tx) ** 2 + (caster_y - ty) ** 2) ** 0.5
				if distance > spell_range:
					self._set_action_feedback("行动失败：目标超出施法范围", False)
					return
				target_area = Area(tx, ty, 0)
				target_codes = [self._get_piece_short_code(target_piece)]
				target_pieces = [target_piece]
				before_hp[id(target_piece)] = int(getattr(target_piece, "health", 0))
			else:
				try:
					tx = int(self.action_spell_point_x_var.get().strip())
					ty = int(self.action_spell_point_y_var.get().strip())
				except Exception:
					self._set_action_feedback("行动失败：请输入合法施法坐标", False)
					return
				board = getattr(env, "board", None)
				width = int(getattr(board, "width", 0)) if board is not None else 0
				height = int(getattr(board, "height", 0)) if board is not None else 0
				if not (0 <= tx < width and 0 <= ty < height):
					self._set_action_feedback("行动失败：施法坐标越界", False)
					return
				distance = ((caster_x - tx) ** 2 + (caster_y - ty) ** 2) ** 0.5
				if distance > spell_range:
					self._set_action_feedback("行动失败：施法点超出施法范围", False)
					return
				target_area = Area(tx, ty, max(0, area_radius))
				area_targets = self._collect_area_spell_targets(env, caster, spell, target_area)
				target_codes = [self._get_piece_short_code(p) for p in area_targets]
				target_pieces = list(area_targets)
				for p in area_targets:
					before_hp[id(p)] = int(getattr(p, "health", 0))

			spell_context = SpellContext()
			spell_context.caster = caster
			spell_context.target = target_piece
			spell_context.spell = spell
			spell_context.target_area = target_area
			spell_context.is_delay_spell = bool(getattr(spell, "is_delay_spell", False))
			spell_context.delay_add = False
			spell_context.spell_cost = spell_cost
			spell_context.spell_lifespan = int(getattr(spell, "base_lifespan", 0))

			action = ActionSet()
			action.move = False
			action.attack = False
			action.spell = True
			action.spell_context = spell_context

			setattr(env, "current_piece", caster)
			env.execute_player_action(action)

			new_ap = int(getattr(caster, "action_points", 0))
			new_sp = int(getattr(caster, "spell_slots", 0))
			damage_by_target: dict[str, int] = {}
			for code in target_codes:
				piece = None
				for p in self._coerce_piece_list(getattr(env, "action_queue", [])):
					if self._get_piece_short_code(p) == code:
						piece = p
						break
				if piece is None:
					continue
				old_hp = before_hp.get(id(piece), int(getattr(piece, "health", 0)))
				new_hp = int(getattr(piece, "health", 0))
				delta = max(0, old_hp - new_hp)
				if delta > 0:
					damage_by_target[code] = delta

			if new_ap == old_ap and new_sp == old_sp:
				self._set_action_feedback("行动失败：法术未生效（目标/范围/资源不满足）", False)
				return

			self.right_info_panel.append_content(
				f"\n[公式] 资源消耗：AP {old_ap}->{new_ap}，SP {old_sp}->{new_sp}"
			)
			for p in target_pieces:
				if p is None:
					continue
				code = self._get_piece_short_code(p)
				old_hp = before_hp.get(id(p), int(getattr(p, "health", 0)))
				new_hp = int(getattr(p, "health", 0))
				delta = int(old_hp - new_hp)
				if delta > 0:
					self.right_info_panel.append_content(
						f"\n[公式] 结算：{spell_name} 对 {code} 造成 {delta} 点伤害（HP {old_hp}->{new_hp}）"
					)
				elif delta < 0:
					heal = -delta
					self.right_info_panel.append_content(
						f"\n[公式] 结算：{spell_name} 为 {code} 恢复 {heal} 点生命（HP {old_hp}->{new_hp}）"
					)
				if new_hp < 0:
					try:
						p.get_accessor().set_health_to(0)
					except Exception:
						setattr(p, "health", 0)
					new_hp = 0
				if new_hp == 0:
					self._handle_death_check_if_possible(env, p)

			summary_targets = ",".join(target_codes) if target_codes else "无"
			summary = f"目标[{summary_targets}]，AP {old_ap}->{new_ap}，SP {old_sp}->{new_sp}"
			self._append_runtime_action_log(
				actor_code=self._get_piece_short_code(caster),
				action_label=f"法术:{spell_name}",
				summary=summary,
				targets=target_codes,
				damage_by_target=damage_by_target,
			)
			for p in target_pieces:
				if p is None:
					continue
				self._append_runtime_death_and_game_over_info(p, self._get_piece_short_code(p))

			# 清理施法点坐标与 AOE 预览，避免火球术等范围可视化残留。
			if not bool(getattr(spell, "is_locking_spell", False)):
				try:
					self.action_spell_point_x_var.set("")
					self.action_spell_point_y_var.set("")
				except Exception:
					pass
				try:
					self.left_board_panel.set_spell_aoe_overlay([], "#f97316")
				except Exception:
					pass
			self._set_action_feedback("行动成功", True)
			self._update_cards_from_env()
			self._refresh_piece_cards()
			self._refresh_board_view()
			return

		self.right_info_panel.append_content(f"\n{message}")
		self.right_info_panel.append_content("\n[UI] 当前模式尚为预览，后续会接入规则校验与真实执行")

	def _on_finish_current_piece_turn(self) -> None:
		"""结束当前棋子行动时段：若未提交动作，则按空行动推进到下一棋子。"""
		self._stop_action_move_point_pick()
		if self.controller.runtime_source != "runtime_env" or self.controller.environment is None:
			self.right_info_panel.append_content("\n[UI] 仅 runtime 模式支持“行动完毕”")
			return
		env = self.controller.environment
		piece = self._get_runtime_current_piece(env)
		if piece is None:
			self.right_info_panel.append_content("\n[UI] 当前无可行动棋子")
			self._set_action_feedback("行动失败：当前无可行动棋子", False)
			return
		piece_code = self._get_piece_short_code(piece)
		self.right_info_panel.append_content(f"\n[UI] 行动完毕：结束 {piece_code} 的行动时段")
		self.runtime_completed_turns += 1
		curr_id = int(getattr(piece, "id", -1))
		if curr_id >= 0:
			self.runtime_cycle_done_piece_ids.add(curr_id)
		ended_piece = piece

		alive_queue = [p for p in self._coerce_piece_list(getattr(env, "action_queue", [])) if bool(getattr(p, "is_alive", True))]
		if not alive_queue:
			self._set_action_feedback("行动失败：当前无可行动棋子", False)
			return

		try:
			idx = next(i for i, p in enumerate(alive_queue) if p is piece)
		except StopIteration:
			idx = 0
		rotated = alive_queue[idx + 1 :] + alive_queue[: idx + 1]
		setattr(env, "action_queue", np.array(rotated, dtype=object))
		setattr(env, "current_piece", rotated[0] if rotated else None)

		alive_ids = {int(getattr(p, "id", -1)) for p in rotated if int(getattr(p, "id", -1)) >= 0}
		round_advanced = False
		if alive_ids and self.runtime_cycle_done_piece_ids.issuperset(alive_ids):
			for p in rotated:
				if bool(getattr(p, "is_alive", True)):
					p.set_action_points(int(getattr(p, "max_action_points", getattr(p, "action_points", 0))))
			self.runtime_cycle_done_piece_ids.clear()
			setattr(env, "round_number", int(getattr(env, "round_number", 0)) + 1)
			round_advanced = True
			self.right_info_panel.append_content("\n[UI] 新一轮开始：已重置全部存活棋子的行动位")

		# 行动时段结束后：若结束行动的棋子站在陷阱上，且此刻不再是当前行动，则触发并消失。
		if ended_piece is not getattr(env, "current_piece", None):
			self._try_trigger_runtime_trap_on_piece(env, ended_piece, reason="行动完毕触发")

		self._tick_runtime_traps(env, round_advanced=round_advanced)

		self._append_runtime_turn_round_status()

		self._collapse_action_detail()
		self._set_action_feedback("已结束当前行动时段", True)
		self._update_cards_from_env()
		self._refresh_piece_cards()
		self._refresh_board_view()
		self._on_click_piece_action()

	def _on_click_piece_action(self) -> None:
		"""点击“棋子行动”后，在可变区显示行动编辑面板。"""
		self.right_top_composite_panel.clear_variable_area()
		self.action_panel_status_label = None

		container = ttk.Frame(self.right_top_composite_panel.variable_frame)
		container.pack(fill="both", expand=True)
		container.columnconfigure(0, weight=1)

		self.action_panel_status_label = ttk.Label(container, text="", foreground="#374151")
		self.action_panel_status_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
		self._refresh_piece_action_status_line()

		row1 = ttk.Frame(container)
		row1.grid(row=1, column=0, sticky="ew", pady=(0, 6))
		row1.columnconfigure(0, weight=1)
		row1.columnconfigure(1, weight=1)
		row1.columnconfigure(2, weight=1)

		ttk.Button(row1, text="移动", command=lambda: self._switch_action_mode("move", row2)).grid(
			row=0, column=0, sticky="ew", padx=(0, 4)
		)
		ttk.Button(row1, text="攻击", command=lambda: self._switch_action_mode("attack", row2)).grid(
			row=0, column=1, sticky="ew", padx=4
		)
		ttk.Button(row1, text="法术", command=lambda: self._switch_action_mode("spell", row2)).grid(
			row=0, column=2, sticky="ew", padx=(4, 0)
		)

		row2 = ttk.Frame(container)
		row2.grid(row=2, column=0, sticky="ew")
		self.action_detail_container = row2

		submit_row = ttk.Frame(container)
		submit_row.grid(row=3, column=0, sticky="ew", pady=(6, 0))
		self.action_confirm_button = ttk.Button(submit_row, text="确认行动", command=self._on_preview_submit_action)
		ttk.Button(submit_row, text="行动完毕", command=self._on_finish_current_piece_turn).pack(side="left", padx=(8, 0))

		feedback_row = ttk.Frame(container)
		feedback_row.grid(row=4, column=0, sticky="w", pady=(4, 0))
		self.action_feedback_label = ttk.Label(feedback_row, text="", foreground="#059669")
		self.action_feedback_label.pack(side="left")

		self.right_info_panel.append_content("\n[UI] 已进入棋子行动面板：请选择移动/攻击/法术，或点击行动完毕")
		self._append_runtime_turn_round_status()

	def _close_replay_mode_ui(self) -> None:
		"""关闭回放模式并清理可变区。"""
		if self.running:
			self._on_click_pause()
		self.replay_controls_visible = False
		self.replay_play_pause_button = None
		self.right_top_composite_panel.clear_variable_area()
		ttk.Label(
			self.right_top_composite_panel.variable_frame,
			text="（可变区占位，后续根据模式放置内容）",
			anchor="center",
			foreground="#999999",
		).pack(fill="both", expand=True)

	def _on_click_replay_mode(self) -> None:
		"""点击“回放模式”后，显示回放控制区并接入功能。"""
		self.right_top_composite_panel.clear_variable_area()

		container = ttk.Frame(self.right_top_composite_panel.variable_frame)
		container.pack(fill="both", expand=True)
		container.columnconfigure(0, weight=1)

		player_row = ttk.Frame(container)
		player_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
		player_row.columnconfigure(0, weight=1)
		player_row.columnconfigure(1, weight=1)
		player_row.columnconfigure(2, weight=1)
		player_row.columnconfigure(3, weight=1)

		ttk.Button(player_row, text="重新开始", command=self._on_replay_restart).grid(row=0, column=0, sticky="ew", padx=(0, 4))
		ttk.Button(player_row, text="后退", command=self._on_replay_back).grid(row=0, column=1, sticky="ew", padx=4)
		self.replay_play_pause_button = ttk.Button(player_row, text="播放", command=self._on_replay_toggle_play_pause)
		self.replay_play_pause_button.grid(row=0, column=2, sticky="ew", padx=4)
		ttk.Button(player_row, text="前进", command=self._on_replay_forward).grid(row=0, column=3, sticky="ew", padx=(4, 0))

		speed_row = ttk.Frame(container)
		speed_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
		ttk.Label(speed_row, text="播放间隔(ms):").pack(side="left")
		speed_spin = tk.Spinbox(
			speed_row,
			from_=100,
			to=2000,
			increment=50,
			width=8,
			textvariable=self.replay_speed_var,
			command=lambda: self._apply_replay_speed_from_input(from_text_input=False),
		)
		speed_spin.pack(side="left", padx=(6, 6))
		speed_spin.bind("<Return>", lambda _e: self._apply_replay_speed_from_input(from_text_input=True))
		speed_spin.bind("<FocusOut>", lambda _e: self._apply_replay_speed_from_input(from_text_input=True))

		round_row = ttk.Frame(container)
		round_row.grid(row=2, column=0, sticky="ew")
		ttk.Label(round_row, text="第").pack(side="left")
		round_spin = tk.Spinbox(
			round_row,
			from_=1,
			to=max(1, self._get_mock_total_rounds()),
			increment=1,
			width=8,
			textvariable=self.replay_round_var,
			command=self._on_replay_jump_to_round,
		)
		round_spin.pack(side="left", padx=(4, 4))
		ttk.Label(round_row, text="回合").pack(side="left", padx=(0, 8))
		ttk.Button(round_row, text="跳转", command=self._on_replay_jump_to_round).pack(side="left")

		round_spin.bind("<Return>", lambda _e: self._on_replay_jump_to_round())
		round_spin.bind("<FocusOut>", lambda _e: self._on_replay_jump_to_round())

		self.replay_controls_visible = True
		self._sync_replay_round_var()
		self._update_replay_play_pause_button_text()
		self.right_info_panel.append_content("\n[UI] 已进入回放模式：可变区显示回放控制")

	# 以下按钮回调先提供最小可用行为，后续在 logic/controller.py 中接入真实逻辑。
	def _on_click_load_data(self) -> None:
		"""模式选择按钮点击事件。
		
		逻辑流程：
		1. 弹出源选择对话框（后端 or mock）
		2. 如果用户取消或关闭，返回不做任何改变
		3. 如果选择后端，直接加载后端数据
		4. 如果选择 mock，继续弹出数据集选择对话框
		   - 如果用户取消或关闭，返回不做任何改变
		   - 如果用户确定，加载该数据集
		5. 成功加载后，重置棋盘并显示新数据
		"""
		try:
			selected_source = self._show_source_selection_dialog("模式选择")
			if selected_source is None:
				self.right_info_panel.append_content("\n[UI] 模式选择已取消，无任何改变")
				return

			next_dataset: Optional[str] = self.selected_mock_dataset
			if selected_source == "mock":
				selected_dataset = self._show_mock_dataset_dialog("模式选择 - 选择数据集")
				if selected_dataset is None:
					self.right_info_panel.append_content("\n[UI] 数据集选择已取消，无任何改变")
					return
				next_dataset = selected_dataset

			# 用户完整确认后才提交变更
			self.selected_source = selected_source
			self.selected_mock_dataset = next_dataset
			self._load_data_with_selected_source()
		except Exception as e:
			self.right_info_panel.append_content(f"\n[UI] 模式选择出错: {e}")

	def _on_click_mode_selection(self) -> None:
		"""'模式选择'按钮的回调（新命名）。"""
		self._close_replay_mode_ui()
		self._on_click_load_data()

	def _on_click_attribute_settings(self, force_runtime_init: bool = False) -> None:
		"""打开属性设置窗口。"""
		if force_runtime_init:
			self.attribute_settings_force_init_mode = True
			self.runtime_init_config_ready = False
		else:
			self.attribute_settings_force_init_mode = False

		if hasattr(self, "attribute_settings_window") and self.attribute_settings_window is not None:
			try:
				if self.attribute_settings_window.winfo_exists():
					self.attribute_settings_window.deiconify()
					self.attribute_settings_window.lift()
					self.attribute_settings_window.focus_force()
					self._switch_attribute_settings_page("piece")
					if force_runtime_init:
						self.root.wait_window(self.attribute_settings_window)
					return
			except Exception:
				pass

		window = tk.Toplevel(self.root)
		window.title("属性设置")
		window.transient(self.root)
		window.resizable(True, True)
		window.geometry("860x460")
		window.minsize(760, 380)
		self.attribute_settings_window = window

		main = ttk.Frame(window, padding=10)
		main.pack(fill="both", expand=True)
		main.columnconfigure(0, weight=0)
		main.columnconfigure(1, weight=1)
		main.rowconfigure(0, weight=1)

		nav = ttk.LabelFrame(main, text="分类", padding=8)
		nav.grid(row=0, column=0, sticky="ns", padx=(0, 10))
		nav.columnconfigure(0, weight=1)

		content = ttk.LabelFrame(main, text="属性内容", padding=10)
		content.grid(row=0, column=1, sticky="nsew")
		content.columnconfigure(0, weight=1)
		content.rowconfigure(0, weight=1)
		self.attribute_settings_content_frame = content

		self.attribute_settings_nav_buttons: dict[str, ttk.Button] = {}
		nav_items = [
			("piece", "棋子"),
			("map", "地图"),
			("action", "行动"),
		]
		for row_idx, (page_key, title) in enumerate(nav_items):
			btn = ttk.Button(nav, text=title, command=lambda key=page_key: self._switch_attribute_settings_page(key))
			btn.grid(row=row_idx, column=0, sticky="ew", pady=(0, 8))
			self.attribute_settings_nav_buttons[page_key] = btn
			if self.attribute_settings_force_init_mode and page_key != "piece":
				btn.configure(state="disabled")

		def on_close() -> None:
			if self.attribute_settings_force_init_mode and not self.runtime_init_config_ready:
				msg = self._runtime_init_incomplete_message()
				self._show_notice_popup("提示", msg)
				self._switch_attribute_settings_page("piece")
				return

			self._stop_map_point_pick()
			self.attribute_settings_force_init_mode = False
			self.attribute_settings_window = None
			self.attribute_settings_content_frame = None
			self.attribute_piece_apply_status_label = None
			self.attribute_piece_apply_status_job = None
			self.attribute_piece_warning_label = None
			self.attribute_piece_warning_job = None
			self.attribute_map_apply_status_label = None
			window.destroy()

		window.protocol("WM_DELETE_WINDOW", on_close)
		self._center_popup_window(window)
		self._switch_attribute_settings_page("piece")
		if force_runtime_init:
			self.root.wait_window(window)

	def _center_popup_window(self, window: tk.Toplevel) -> None:
		"""将弹窗居中到主窗口。"""
		window.update_idletasks()
		parent_x = self.root.winfo_rootx()
		parent_y = self.root.winfo_rooty()
		parent_w = self.root.winfo_width()
		parent_h = self.root.winfo_height()
		win_w = window.winfo_width()
		win_h = window.winfo_height()
		target_x = parent_x + max((parent_w - win_w) // 2, 0)
		target_y = parent_y + max((parent_h - win_h) // 2, 0)
		window.geometry(f"+{target_x}+{target_y}")

	def _show_notice_popup(self, title: str, message: str, modal: bool = True) -> None:
		"""显示仅可关闭（右上角叉）的提示弹窗。"""
		window = tk.Toplevel(self.root)
		window.title(title)
		window.transient(self.root)
		window.resizable(False, False)
		if modal:
			window.grab_set()
		else:
			window.attributes("-topmost", True)
		frame = ttk.Frame(window, padding=12)
		frame.pack(fill="both", expand=True)
		ttk.Label(frame, text=message, justify="left").pack(anchor="w")
		window.protocol("WM_DELETE_WINDOW", window.destroy)
		self._center_popup_window(window)
		if not modal:
			window.lift()

	def _show_game_over_reset_dialog(self) -> None:
		"""游戏结束后弹窗确认：是否重置游戏。"""
		if self.game_over_dialog_shown:
			return
		self.game_over_dialog_shown = True

		window = tk.Toplevel(self.root)
		window.title("游戏结束")
		window.transient(self.root)
		window.resizable(False, False)
		window.grab_set()

		frame = ttk.Frame(window, padding=12)
		frame.pack(fill="both", expand=True)
		ttk.Label(frame, text="是否重置游戏？", justify="left").pack(anchor="w")

		button_row = ttk.Frame(frame)
		button_row.pack(fill="x", pady=(10, 0))

		def _show_no_warning() -> None:
			self._show_notice_popup(
				"提示",
				"目前在开发阶段，不重置可能存在bug，如想正常重开一局，请点击\"模式选择\"",
			)

		def on_yes() -> None:
			window.destroy()
			self._on_click_reset()

		def on_no_like_close() -> None:
			window.destroy()
			_show_no_warning()

		ttk.Button(button_row, text="否", command=on_no_like_close).pack(side="right")
		ttk.Button(button_row, text="是", command=on_yes).pack(side="right", padx=(0, 6))

		window.protocol("WM_DELETE_WINDOW", on_no_like_close)
		self._center_popup_window(window)

	def _show_initiative_summary_popup(self) -> None:
		"""显示开局先攻详情：属性值、随机值、总值、序号与最终顺序。"""
		env = self.controller.environment
		if env is None:
			return

		details = list(self.runtime_initiative_snapshot)
		if not details:
			self.right_info_panel.append_content("\n[UI] 先攻详情不可用：未捕获到初始化掷骰信息")
			return

		slot_by_piece: dict[int, str] = {}
		for slot in self.runtime_card_slots:
			piece = slot.get("piece")
			if piece is not None:
				slot_by_piece[id(piece)] = str(slot.get("slot_code", "?"))

		action_queue = self._coerce_piece_list(getattr(env, "action_queue", []))
		order_by_piece: dict[int, int] = {}
		overall_codes: list[str] = []
		for idx, piece in enumerate(action_queue, start=1):
			if not bool(getattr(piece, "is_alive", True)):
				continue
			pid = id(piece)
			order_by_piece[pid] = idx
			overall_codes.append(slot_by_piece.get(pid, f"ID{int(getattr(piece, 'id', -1))}"))

		rows: list[tuple[int, str, int, int, int, int]] = []
		for item in details:
			piece = item.get("piece")
			if piece is None or not bool(getattr(piece, "is_alive", True)):
				continue
			pid = id(piece)
			seq = int(order_by_piece.get(pid, 999))
			code = slot_by_piece.get(pid, f"ID{int(getattr(piece, 'id', -1))}")
			attr_name = str(item.get("attr_name", "属性"))
			attr_value = int(item.get("attr_value", 0))
			roll_value = int(item.get("roll", 0))
			bonus_value = int(item.get("bonus", 0))
			total_value = int(item.get("total", roll_value + bonus_value))
			rows.append((seq, code, attr_name, attr_value, roll_value, bonus_value, total_value))

		rows.sort(key=lambda x: x[0])
		if not rows:
			return

		window = tk.Toplevel(self.root)
		window.title("开局先攻顺序信息")
		window.resizable(False, False)
		window.transient(self.root)
		window.attributes("-topmost", True)

		container = ttk.Frame(window, padding=12)
		container.pack(fill="both", expand=True)

		ttk.Label(container, text="先攻计算（按当前 env 实现）", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
		text = tk.Text(container, width=76, height=12, wrap="none")
		text.pack(fill="both", expand=True, pady=(8, 8))
		text.insert("end", "序号  棋子  属性  属性值  随机(d20)  调整值  总值\n")
		text.insert("end", "------------------------------------------------\n")
		for seq, code, attr_name, attr_value, roll_value, bonus_value, total_value in rows:
			text.insert("end", f"{seq:>2}    {code:<3}   {attr_name:<2}    {attr_value:>2}      {roll_value:>2}       {bonus_value:>2}    {total_value:>2}\n")
		text.insert("end", "\n")
		text.insert("end", f"最终顺序：{' -> '.join(overall_codes)}")
		text.configure(state="disabled")

		button_row = ttk.Frame(container)
		button_row.pack(anchor="e")

		def _close() -> None:
			window.destroy()

		ttk.Button(button_row, text="确定", command=_close).pack(side="right")
		window.protocol("WM_DELETE_WINDOW", _close)
		window.grab_set()
		self._center_popup_window(window)
		self.root.wait_window(window)

	def _show_attribute_warning_feedback(self, message: str) -> None:
		"""在属性窗口下方显示 5 秒范围提示。"""
		label = self.attribute_piece_warning_label
		if label is None:
			return
		label.configure(text=message, foreground="#b45309")
		if self.attribute_piece_warning_job is not None:
			try:
				self.root.after_cancel(self.attribute_piece_warning_job)
			except Exception:
				pass
		self.attribute_piece_warning_job = self.root.after(5000, lambda: label.configure(text=""))

	def _runtime_init_incomplete_message(self) -> str:
		"""返回后端初始化未完成时的具体提示。"""
		team1_count = 0
		team2_count = 0
		for slot_key in self._piece_slot_keys():
			vars_dict = self.attribute_piece_vars.get(slot_key)
			if vars_dict is None:
				continue
			hp_raw = str(vars_dict.get("hp").get()).strip()
			if hp_raw in ("", "-", "-1"):
				continue
			if self._safe_int(hp_raw, -1) <= 0:
				continue
			if int(slot_key[1]) == 1:
				team1_count += 1
			else:
				team2_count += 1

		if team1_count == 0 and team2_count == 0:
			return "当前场上未有有效棋子！"
		if team1_count == 0:
			return "当前场上未有有效棋子！player1阵营未设置棋子"
		if team2_count == 0:
			return "当前场上未有有效棋子！player2阵营未设置棋子"
		return "当前场上未有有效棋子！请先完成属性配置并应用"

	def _switch_attribute_settings_page(self, page_key: str) -> None:
		"""切换属性设置窗口的页面。"""
		content = getattr(self, "attribute_settings_content_frame", None)
		if content is None:
			return

		for widget in content.winfo_children():
			widget.destroy()

		titles = {
			"piece": "棋子属性",
			"map": "地图属性",
			"action": "行动属性",
		}

		if page_key == "piece":
			self._build_attribute_piece_page(content)
			self.right_info_panel.append_content("\n[UI] 属性设置页面切换: 棋子属性")
			return
		if page_key == "map":
			self._build_attribute_map_page(content)
			self.right_info_panel.append_content("\n[UI] 属性设置页面切换: 地图属性")
			return
		if page_key == "action":
			self._build_attribute_action_page(content)
			self.right_info_panel.append_content("\n[UI] 属性设置页面切换: 行动属性")
			return

		desc = {
			"map": "这里将用于设置地图属性（重点：高度/可通行性）。",
			"action": "这里将用于设置行动属性（如攻击、法术、技能数值）。",
		}

		wrapper = ttk.Frame(content)
		wrapper.grid(row=0, column=0, sticky="nsew")
		wrapper.columnconfigure(0, weight=1)
		wrapper.rowconfigure(2, weight=1)

		ttk.Label(wrapper, text=titles.get(page_key, "属性设置"), font=("Microsoft YaHei UI", 12, "bold")).grid(
			row=0, column=0, sticky="w", pady=(0, 8)
		)
		ttk.Label(
			wrapper,
			text=desc.get(page_key, "待实现"),
			justify="left",
			foreground="#4b5563",
		).grid(row=1, column=0, sticky="nw")

		self.right_info_panel.append_content(f"\n[UI] 属性设置页面切换: {titles.get(page_key, page_key)}")

	def _default_action_settings_snapshot(self) -> dict[str, Any]:
		return {
			"attack_model": {
				"enable_d20": True,
				"hit": {
					"bonus_flat": 0.0,
					"coeff_strength": 1.0,
					"coeff_dexterity": 1.0,
					"defense_modifier_attr": "dexterity",
					"defense_base_coeff": 1.0,
					"defense_attr_coeff": 1.0,
					"defense_flat_bonus": 0.0,
					"crit_on_20": True,
					"fail_on_1": True,
				},
				"magic_hit": {
					"bonus_flat": 0.0,
					"coeff_intelligence": 1.0,
					"coeff_advantage": 1.0,
					"defense_modifier_attr": None,
					"defense_base_coeff": 1.0,
					"defense_attr_coeff": 1.0,
					"defense_flat_bonus": 0.0,
				},
				"physical_damage": {
					"base_from_piece": True,
					"base_override": None,
					"flat_bonus": 0.0,
					"resist_mode": "subtract",
				},
				"magic_damage": {
					"base_from_piece": True,
					"base_override": None,
					"flat_bonus": 0.0,
					"resist_mode": "subtract",
				},
			},
			"spell_overrides": {},
		}

	def _ensure_action_settings_initialized(self) -> None:
		if not isinstance(self.action_settings_snapshot, dict) or not self.action_settings_snapshot:
			self.action_settings_snapshot = self._default_action_settings_snapshot()
		if "attack_model" not in self.action_settings_snapshot:
			self.action_settings_snapshot["attack_model"] = self._default_action_settings_snapshot()["attack_model"]
		if "spell_overrides" not in self.action_settings_snapshot:
			self.action_settings_snapshot["spell_overrides"] = {}
		attack_model = self.action_settings_snapshot.get("attack_model")
		if not isinstance(attack_model, dict):
			self.action_settings_snapshot["attack_model"] = self._default_action_settings_snapshot()["attack_model"]
			return
		if "hit" not in attack_model or not isinstance(attack_model.get("hit"), dict):
			attack_model["hit"] = self._default_action_settings_snapshot()["attack_model"]["hit"]
		if "magic_hit" not in attack_model or not isinstance(attack_model.get("magic_hit"), dict):
			attack_model["magic_hit"] = self._default_action_settings_snapshot()["attack_model"]["magic_hit"]
		if "physical_damage" not in attack_model or not isinstance(attack_model.get("physical_damage"), dict):
			attack_model["physical_damage"] = self._default_action_settings_snapshot()["attack_model"]["physical_damage"]
		if "magic_damage" not in attack_model or not isinstance(attack_model.get("magic_damage"), dict):
			attack_model["magic_damage"] = self._default_action_settings_snapshot()["attack_model"]["magic_damage"]

		hit = attack_model.get("hit")
		if isinstance(hit, dict):
			for k, v in (
				("defense_base_coeff", 1.0),
				("defense_attr_coeff", 1.0),
				("defense_flat_bonus", 0.0),
			):
				if k not in hit:
					hit[k] = v
		magic_hit = attack_model.get("magic_hit")
		if isinstance(magic_hit, dict):
			for k, v in (
				("defense_base_coeff", 1.0),
				("defense_attr_coeff", 1.0),
				("defense_flat_bonus", 0.0),
			):
				if k not in magic_hit:
					magic_hit[k] = v

	def _sync_action_settings_vars_from_snapshot(self) -> None:
		"""将 snapshot 同步到界面变量（仅用于属性设置-行动页）。"""
		self._ensure_action_settings_initialized()
		self.action_attribute_internal_update = True
		try:
			attack_model = self.action_settings_snapshot.get("attack_model", {})
			hit = attack_model.get("hit", {}) if isinstance(attack_model, dict) else {}
			magic_hit = attack_model.get("magic_hit", {}) if isinstance(attack_model, dict) else {}
			physical_damage = attack_model.get("physical_damage", {}) if isinstance(attack_model, dict) else {}
			magic_damage = attack_model.get("magic_damage", {}) if isinstance(attack_model, dict) else {}

			def _get_bool(d: dict[str, Any], key: str, default: bool) -> bool:
				val = d.get(key, default)
				return bool(val) if isinstance(val, (bool, int)) else default

			def _get_float(d: dict[str, Any], key: str, default: float) -> float:
				val = d.get(key, default)
				try:
					return float(val)
				except Exception:
					return float(default)

			self.attribute_action_attack_vars.setdefault("enable_d20", tk.BooleanVar())
			self.attribute_action_attack_vars.setdefault("hit_bonus_flat", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("hit_coeff_strength", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("hit_coeff_dexterity", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("magic_hit_bonus_flat", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("magic_hit_coeff_intelligence", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("magic_hit_coeff_advantage", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("phy_defense_modifier", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("phy_def_base_coeff", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("phy_def_attr_coeff", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("phy_def_flat_bonus", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("mag_defense_modifier", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("mag_def_base_coeff", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("mag_def_attr_coeff", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("mag_def_flat_bonus", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("hit_crit_on_20", tk.BooleanVar())
			self.attribute_action_attack_vars.setdefault("hit_fail_on_1", tk.BooleanVar())
			self.attribute_action_attack_vars.setdefault("phy_base_from_piece", tk.BooleanVar())
			self.attribute_action_attack_vars.setdefault("phy_base_override", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("phy_flat_bonus", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("mag_base_from_piece", tk.BooleanVar())
			self.attribute_action_attack_vars.setdefault("mag_base_override", tk.StringVar())
			self.attribute_action_attack_vars.setdefault("mag_flat_bonus", tk.StringVar())

			attack_dict = attack_model if isinstance(attack_model, dict) else {}
			hit_dict = hit if isinstance(hit, dict) else {}
			magic_hit_dict = magic_hit if isinstance(magic_hit, dict) else {}
			phy_dict = physical_damage if isinstance(physical_damage, dict) else {}
			mag_dict = magic_damage if isinstance(magic_damage, dict) else {}

			# 顶层
			self.attribute_action_attack_vars["enable_d20"].set(_get_bool(attack_dict, "enable_d20", True))

			# 命中
			self.attribute_action_attack_vars["hit_bonus_flat"].set(str(_get_float(hit_dict, "bonus_flat", 0.0)))
		# 系数输入框允许留空=默认，因此这里不直接回填数值，只缓存默认值供公式显示与 apply 使用。
			self.attribute_action_attack_defaults["hit_coeff_strength"] = _get_float(hit_dict, "coeff_strength", 1.0)
		# 这里的 coeff_dexterity 作为“优势值系数”使用（历史遗留字段名），默认取 1。
			self.attribute_action_attack_defaults["hit_coeff_dexterity"] = _get_float(hit_dict, "coeff_dexterity", 1.0)
			self.attribute_action_attack_vars["hit_coeff_strength"].set("")
			self.attribute_action_attack_vars["hit_coeff_dexterity"].set("")
			self.attribute_action_attack_vars["hit_crit_on_20"].set(_get_bool(hit_dict, "crit_on_20", True))
			self.attribute_action_attack_vars["hit_fail_on_1"].set(_get_bool(hit_dict, "fail_on_1", True))
			phy_def_attr = hit_dict.get("defense_modifier_attr", "dexterity")
			phy_def_label = {None: "无", "": "无", "none": "无", "strength": "力量修正", "dexterity": "敏捷修正", "intelligence": "智力修正"}.get(
				phy_def_attr,
				"敏捷修正",
			)
			self.attribute_action_attack_vars["phy_defense_modifier"].set(phy_def_label)
			self.attribute_action_attack_defaults["phy_def_base_coeff"] = _get_float(hit_dict, "defense_base_coeff", 1.0)
			self.attribute_action_attack_defaults["phy_def_attr_coeff"] = _get_float(hit_dict, "defense_attr_coeff", 1.0)
			self.attribute_action_attack_defaults["phy_def_flat_bonus"] = _get_float(hit_dict, "defense_flat_bonus", 0.0)
			self.attribute_action_attack_vars["phy_def_base_coeff"].set("")
			self.attribute_action_attack_vars["phy_def_attr_coeff"].set("")
			self.attribute_action_attack_vars["phy_def_flat_bonus"].set("")

			# 普通法术攻击命中
			self.attribute_action_attack_vars["magic_hit_bonus_flat"].set(str(_get_float(magic_hit_dict, "bonus_flat", 0.0)))
			self.attribute_action_attack_defaults["magic_hit_coeff_intelligence"] = _get_float(
				magic_hit_dict, "coeff_intelligence", 1.0
			)
			self.attribute_action_attack_defaults["magic_hit_coeff_advantage"] = _get_float(
				magic_hit_dict, "coeff_advantage", 1.0
			)
			self.attribute_action_attack_vars["magic_hit_coeff_intelligence"].set("")
			self.attribute_action_attack_vars["magic_hit_coeff_advantage"].set("")
			mag_def_attr = magic_hit_dict.get("defense_modifier_attr", None)
			mag_def_label = {None: "无", "": "无", "none": "无", "strength": "力量修正", "dexterity": "敏捷修正", "intelligence": "智力修正"}.get(
				mag_def_attr,
				"无",
			)
			self.attribute_action_attack_vars["mag_defense_modifier"].set(mag_def_label)
			self.attribute_action_attack_defaults["mag_def_base_coeff"] = _get_float(magic_hit_dict, "defense_base_coeff", 1.0)
			self.attribute_action_attack_defaults["mag_def_attr_coeff"] = _get_float(magic_hit_dict, "defense_attr_coeff", 1.0)
			self.attribute_action_attack_defaults["mag_def_flat_bonus"] = _get_float(magic_hit_dict, "defense_flat_bonus", 0.0)
			self.attribute_action_attack_vars["mag_def_base_coeff"].set("")
			self.attribute_action_attack_vars["mag_def_attr_coeff"].set("")
			self.attribute_action_attack_vars["mag_def_flat_bonus"].set("")

			# 物理伤害
			self.attribute_action_attack_vars["phy_base_from_piece"].set(_get_bool(phy_dict, "base_from_piece", True))
			phy_base_override = phy_dict.get("base_override") if isinstance(phy_dict, dict) else None
			self.attribute_action_attack_vars["phy_base_override"].set("" if phy_base_override is None else str(phy_base_override))
			self.attribute_action_attack_vars["phy_flat_bonus"].set(str(_get_float(phy_dict, "flat_bonus", 0.0)))
			# 伤害系数（力量/敏捷）不参与后端真实伤害结算，已从 UI 收敛移除。

			# 普通法术攻击伤害
			self.attribute_action_attack_vars["mag_base_from_piece"].set(_get_bool(mag_dict, "base_from_piece", True))
			mag_base_override = mag_dict.get("base_override") if isinstance(mag_dict, dict) else None
			self.attribute_action_attack_vars["mag_base_override"].set("" if mag_base_override is None else str(mag_base_override))
			self.attribute_action_attack_vars["mag_flat_bonus"].set(str(_get_float(mag_dict, "flat_bonus", 0.0)))
			# 伤害系数（智力）不参与后端真实伤害结算，已从 UI 收敛移除。

			# 法术覆盖
			overrides = self.action_settings_snapshot.get("spell_overrides", {})
			if not isinstance(overrides, dict):
				overrides = {}
			for spell in SpellFactory.get_all_spells():
				sid = int(getattr(spell, "id", 0))
				if sid <= 0:
					continue
				override = overrides.get(str(sid)) or overrides.get(sid)
				enabled = isinstance(override, dict)
				self.attribute_action_spell_enable_vars.setdefault(sid, tk.BooleanVar(value=enabled))
				vars_map = self.attribute_action_spell_vars.setdefault(
					sid,
					{
						"base_value": tk.StringVar(),
						"range": tk.StringVar(),
						"area_radius": tk.StringVar(),
						"spell_cost": tk.StringVar(),
						"base_lifespan": tk.StringVar(),
					},
				)
				def_val = {
					"base_value": int(getattr(spell, "base_value", 0)),
					"range": int(getattr(spell, "range", 0)),
					"area_radius": int(getattr(spell, "area_radius", 0)),
					"spell_cost": int(getattr(spell, "spell_cost", 0)),
					"base_lifespan": int(getattr(spell, "base_lifespan", 0)),
				}
				if isinstance(override, dict):
					for k in list(def_val.keys()):
						if k in override:
							try:
								def_val[k] = int(float(override.get(k)))
							except Exception:
								pass
				for k, v in def_val.items():
					vars_map[k].set(str(v))
		finally:
			self.action_attribute_internal_update = False

	def _collect_action_settings_snapshot_from_vars(self) -> dict[str, Any]:
		"""从界面变量读取配置，生成 snapshot（不接入后端，仅测试端内存保存）。"""
		self._ensure_action_settings_initialized()

		def _bool(key: str, default: bool = False) -> bool:
			var = self.attribute_action_attack_vars.get(key)
			if var is None:
				return default
			try:
				return bool(var.get())
			except Exception:
				return default

		def _float(key: str, default: float = 0.0) -> float:
			var = self.attribute_action_attack_vars.get(key)
			if var is None:
				return default
			return self._safe_float(str(var.get()), default)

		def _float_or_default_from_blank(key: str, default: float) -> float:
			var = self.attribute_action_attack_vars.get(key)
			if var is None:
				return default
			raw = str(var.get()).strip()
			if raw == "":
				return default
			return self._safe_float(raw, default)

		phy_base_from_piece = _bool("phy_base_from_piece", True)
		phy_base_override_raw = (
			str(self.attribute_action_attack_vars.get("phy_base_override").get()).strip()
			if self.attribute_action_attack_vars.get("phy_base_override")
			else ""
		)
		phy_base_override: float | None
		if (not phy_base_from_piece) and phy_base_override_raw == "":
			raise ValueError("物理攻击伤害：请填写“覆盖基础值”，或勾选“以棋子物伤作为原伤害基础值”。")
		if phy_base_override_raw == "":
			phy_base_override = None
		else:
			phy_base_override = self._safe_float(phy_base_override_raw, 0.0)
		if phy_base_from_piece:
			phy_base_override = None

		mag_base_from_piece = _bool("mag_base_from_piece", True)
		mag_base_override_raw = (
			str(self.attribute_action_attack_vars.get("mag_base_override").get()).strip()
			if self.attribute_action_attack_vars.get("mag_base_override")
			else ""
		)
		mag_base_override: float | None
		if (not mag_base_from_piece) and mag_base_override_raw == "":
			raise ValueError("普通法术攻击伤害：请填写“覆盖基础值”，或勾选“以棋子法伤作为原伤害基础值”。")
		if mag_base_override_raw == "":
			mag_base_override = None
		else:
			mag_base_override = self._safe_float(mag_base_override_raw, 0.0)
		if mag_base_from_piece:
			mag_base_override = None

		snapshot: dict[str, Any] = {
			"attack_model": {
				"enable_d20": _bool("enable_d20", True),
				"hit": {
					"bonus_flat": _float("hit_bonus_flat", 0.0),
					"coeff_strength": _float_or_default_from_blank(
						"hit_coeff_strength",
						float(self.attribute_action_attack_defaults.get("hit_coeff_strength", 1.0)),
					),
					"coeff_dexterity": _float_or_default_from_blank(
						"hit_coeff_dexterity",
						float(self.attribute_action_attack_defaults.get("hit_coeff_dexterity", 1.0)),
					),
					"defense_modifier_attr": None,
					"defense_base_coeff": _float_or_default_from_blank(
						"phy_def_base_coeff",
						float(self.attribute_action_attack_defaults.get("phy_def_base_coeff", 1.0)),
					),
					"defense_attr_coeff": _float_or_default_from_blank(
						"phy_def_attr_coeff",
						float(self.attribute_action_attack_defaults.get("phy_def_attr_coeff", 1.0)),
					),
					"defense_flat_bonus": _float_or_default_from_blank(
						"phy_def_flat_bonus",
						float(self.attribute_action_attack_defaults.get("phy_def_flat_bonus", 0.0)),
					),
					"crit_on_20": _bool("hit_crit_on_20", True),
					"fail_on_1": _bool("hit_fail_on_1", True),
				},
				"magic_hit": {
					"bonus_flat": _float("magic_hit_bonus_flat", 0.0),
					"coeff_intelligence": _float_or_default_from_blank(
						"magic_hit_coeff_intelligence",
						float(self.attribute_action_attack_defaults.get("magic_hit_coeff_intelligence", 1.0)),
					),
					"coeff_advantage": _float_or_default_from_blank(
						"magic_hit_coeff_advantage",
						float(self.attribute_action_attack_defaults.get("magic_hit_coeff_advantage", 1.0)),
					),
					"defense_modifier_attr": None,
					"defense_base_coeff": _float_or_default_from_blank(
						"mag_def_base_coeff",
						float(self.attribute_action_attack_defaults.get("mag_def_base_coeff", 1.0)),
					),
					"defense_attr_coeff": _float_or_default_from_blank(
						"mag_def_attr_coeff",
						float(self.attribute_action_attack_defaults.get("mag_def_attr_coeff", 1.0)),
					),
					"defense_flat_bonus": _float_or_default_from_blank(
						"mag_def_flat_bonus",
						float(self.attribute_action_attack_defaults.get("mag_def_flat_bonus", 0.0)),
					),
				},
				"physical_damage": {
					"base_from_piece": phy_base_from_piece,
					"base_override": phy_base_override,
					"flat_bonus": _float("phy_flat_bonus", 0.0),
					"resist_mode": "subtract",
				},
				"magic_damage": {
					"base_from_piece": mag_base_from_piece,
					"base_override": mag_base_override,
					"flat_bonus": _float("mag_flat_bonus", 0.0),
					"resist_mode": "subtract",
				},
			},
			"spell_overrides": {},
		}

		def _def_mod_to_key(label: str, default_key: str | None) -> str | None:
			label = str(label or "").strip()
			mapping = {
				"无": None,
				"力量修正": "strength",
				"敏捷修正": "dexterity",
				"智力修正": "intelligence",
			}
			return mapping.get(label, default_key)

		phy_def_label = ""
		mag_def_label = ""
		try:
			phy_def_label = str(self.attribute_action_attack_vars.get("phy_defense_modifier").get()).strip()
		except Exception:
			phy_def_label = ""
		try:
			mag_def_label = str(self.attribute_action_attack_vars.get("mag_defense_modifier").get()).strip()
		except Exception:
			mag_def_label = ""

		snapshot["attack_model"]["hit"]["defense_modifier_attr"] = _def_mod_to_key(phy_def_label, "dexterity")
		snapshot["attack_model"]["magic_hit"]["defense_modifier_attr"] = _def_mod_to_key(mag_def_label, None)

		spell_overrides: dict[str, dict[str, int]] = {}
		for spell in SpellFactory.get_all_spells():
			sid = int(getattr(spell, "id", 0))
			if sid <= 0:
				continue
			enable_var = self.attribute_action_spell_enable_vars.get(sid)
			if enable_var is None:
				continue
			try:
				enabled = bool(enable_var.get())
			except Exception:
				enabled = False
			if not enabled:
				continue
			vars_map = self.attribute_action_spell_vars.get(sid, {})
			override: dict[str, int] = {}
			for key in ("base_value", "range", "area_radius", "spell_cost", "base_lifespan"):
				var = vars_map.get(key)
				if var is None:
					continue
				override[key] = self._safe_int(str(var.get()), 0)
			spell_overrides[str(sid)] = override
		snapshot["spell_overrides"] = spell_overrides
		return snapshot

	def _show_action_apply_feedback(self, message: str) -> None:
		label = self.attribute_action_apply_status_label
		if label is None or not label.winfo_exists():
			return
		label.configure(text=message, foreground="#059669")

		def _clear() -> None:
			try:
				if label.winfo_exists():
					label.configure(text="")
			except Exception:
				pass

		self.root.after(2000, _clear)

	def _show_action_warning_feedback(self, message: str) -> None:
		label = self.attribute_action_warning_label
		if label is None or not label.winfo_exists():
			return
		label.configure(text=message, foreground="#b45309")

		def _clear() -> None:
			try:
				if label.winfo_exists():
					label.configure(text="")
			except Exception:
				pass

		self.root.after(5000, _clear)

	def _apply_action_attribute_changes(self) -> None:
		"""应用行动属性（本局临时生效）：运行时猴子补丁覆写 env 公式，不改后端文件。"""
		try:
			snapshot = self._collect_action_settings_snapshot_from_vars()
			self.action_settings_snapshot = snapshot
			# 先放入 controller 的 custom_config，便于后续在逻辑层统一取配置。
			try:
				self.controller.apply_environment_config({"action_settings": snapshot})
			except Exception:
				pass
			self._apply_action_settings_to_runtime_environment(snapshot)
			self.right_info_panel.append_content("\n[UI] 行动属性已应用（本局临时生效）：攻击模型 + 法术数值覆盖")
			self._show_action_apply_feedback("应用成功")
		except Exception as e:
			self._show_action_warning_feedback(f"应用失败：{e}")
			self.right_info_panel.append_content(f"\n[UI] 行动属性应用失败: {e}")

	def _reset_action_attribute_to_defaults(self) -> None:
		self.action_settings_snapshot = self._default_action_settings_snapshot()
		self._sync_action_settings_vars_from_snapshot()
		for sid, var in self.attribute_action_spell_enable_vars.items():
			try:
				var.set(False)
			except Exception:
				pass
		self._apply_action_settings_to_runtime_environment(self.action_settings_snapshot)
		self._show_action_apply_feedback("已恢复默认")

	def _apply_action_settings_to_runtime_environment(self, snapshot: dict[str, Any]) -> None:
		"""将行动属性设置注入到 runtime env（仅本局内存生效）。"""
		if self.controller.runtime_source != "runtime_env":
			return
		env = getattr(self.controller, "environment", None)
		if env is None:
			return
		# 存到 env 上，供钩子读取。
		setattr(env, "_ui_action_settings_snapshot", snapshot if isinstance(snapshot, dict) else {})
		if bool(getattr(env, "_ui_action_settings_hook_installed", False)):
			return
		setattr(env, "_ui_action_settings_hook_installed", True)
		default_snapshot = self._default_action_settings_snapshot()

		orig_execute_attack = getattr(env, "execute_attack", None)
		orig_get_available_spells = getattr(env, "get_available_spells", None)
		if callable(orig_execute_attack):
			setattr(env, "_ui_orig_execute_attack", orig_execute_attack)
		if callable(orig_get_available_spells):
			setattr(env, "_ui_orig_get_available_spells", orig_get_available_spells)

		def _get_snapshot() -> dict[str, Any]:
			snap = getattr(env, "_ui_action_settings_snapshot", None)
			return snap if isinstance(snap, dict) else default_snapshot

		def _step_mod(value: Any) -> int:
			step_func = getattr(env, "step_modified_func", None)
			if callable(step_func):
				try:
					return int(step_func(int(value)))
				except Exception:
					return 0
			return 0

		def _adv_value(attacker: Any, target: Any) -> float:
			adv_func = getattr(env, "calculate_advantage_value", None)
			if callable(adv_func):
				try:
					return float(adv_func(attacker, target))
				except Exception:
					return 0.0
			return 0.0

		def execute_attack_hook(attack_context: Any):
			# 仅覆盖“物理攻击”的命中与伤害；其余逻辑保持与原 env 一致（AP、范围等）。
			try:
				attacker = getattr(attack_context, "attacker", None)
				target = getattr(attack_context, "target", None)
				if attacker is None or target is None:
					return
				if int(getattr(attacker, "action_points", 0)) <= 0:
					return
				if not bool(getattr(attacker, "is_alive", True)) or int(getattr(attacker, "health", 0)) <= 0:
					return
				if not bool(getattr(target, "is_alive", True)) or int(getattr(target, "health", 0)) <= 0:
					return
				if not bool(getattr(env, "is_in_attack_range", lambda a, t: True)(attacker, target)):
					return

				snap = _get_snapshot()
				attack_model = snap.get("attack_model", {}) if isinstance(snap, dict) else {}
				enable_d20 = bool(attack_model.get("enable_d20", True))
				hit_cfg = attack_model.get("hit", {}) if isinstance(attack_model.get("hit"), dict) else {}
				dmg_cfg = attack_model.get("physical_damage", {}) if isinstance(attack_model.get("physical_damage"), dict) else {}

				roll_value = 0
				if enable_d20 and callable(getattr(env, "roll_dice", None)):
					try:
						roll_value = int(getattr(env, "roll_dice")(1, 20))
					except Exception:
						roll_value = 0

				fail_on_1 = bool(hit_cfg.get("fail_on_1", True))
				crit_on_20 = bool(hit_cfg.get("crit_on_20", True))
				bonus_flat = float(hit_cfg.get("bonus_flat", 0.0) or 0.0)
				coeff_strength = float(hit_cfg.get("coeff_strength", 1.0) or 1.0)
				adv_coeff = float(hit_cfg.get("coeff_dexterity", 1.0) or 1.0)

				def_attr = hit_cfg.get("defense_modifier_attr", "dexterity")
				def_base_coeff = float(hit_cfg.get("defense_base_coeff", 1.0) or 1.0)
				def_attr_coeff = float(hit_cfg.get("defense_attr_coeff", 1.0) or 1.0)
				def_flat_bonus = float(hit_cfg.get("defense_flat_bonus", 0.0) or 0.0)

				is_critical = False
				if enable_d20 and roll_value == 1 and fail_on_1:
					is_hit = False
				elif enable_d20 and roll_value == 20 and crit_on_20:
					is_hit = True
					is_critical = True
				else:
					adv = _adv_value(attacker, target)
					attack_score = float(roll_value) + bonus_flat + coeff_strength * float(_step_mod(getattr(attacker, "strength", 0))) + adv_coeff * float(adv)
					base_def = float(getattr(target, "physical_resist", 0))
					attr_def = 0.0
					if def_attr not in (None, "", "none"):
						attr_def = float(_step_mod(getattr(target, str(def_attr), 0)))
					defense_score = def_base_coeff * base_def + def_attr_coeff * attr_def + def_flat_bonus
					is_hit = bool(attack_score > defense_score)

				# 命中才结算伤害
				setattr(attack_context, "damage_dealt", 0)
				if is_hit:
					base_from_piece = bool(dmg_cfg.get("base_from_piece", True))
					base_override = dmg_cfg.get("base_override", None)
					flat_bonus = float(dmg_cfg.get("flat_bonus", 0.0) or 0.0)
					if base_from_piece:
						base = float(getattr(attacker, "physical_damage", 0))
					else:
						try:
							base = float(base_override) if base_override is not None else 0.0
						except Exception:
							base = 0.0
					damage = max(0, base + flat_bonus)
					if is_critical:
						damage *= 2
					int_damage = int(round(damage))
					try:
						target.receive_damage(int_damage, "physical")
					except Exception:
						try:
							old_hp = int(getattr(target, "health", 0))
							setattr(target, "health", old_hp - int_damage)
						except Exception:
							pass
					# 夹到 0，避免出现负血。
					try:
						cur_hp = int(getattr(target, "health", 0))
					except Exception:
						cur_hp = 0
					if cur_hp < 0:
						try:
							target.get_accessor().set_health_to(0)
						except Exception:
							setattr(target, "health", 0)
						cur_hp = 0
					setattr(attack_context, "damage_dealt", int_damage)
					if cur_hp == 0 and callable(getattr(env, "handle_death_check", None)):
						env.handle_death_check(target)

				# 消耗 AP
				try:
					attacker.get_accessor().change_action_points_by(-1)
				except Exception:
					setattr(attacker, "action_points", int(getattr(attacker, "action_points", 0)) - 1)
			except Exception:
				# 回退：若 hook 出错，尽量调用原实现。
				orig = getattr(env, "_ui_orig_execute_attack", None)
				if callable(orig):
					return orig(attack_context)
				return

		def get_available_spells_hook(piece: Any = None):
			orig = getattr(env, "_ui_orig_get_available_spells", None)
			if not callable(orig):
				return []
			spells = [s for s in self._coerce_piece_list(orig(piece)) if s is not None]
			snap = _get_snapshot()
			overrides = snap.get("spell_overrides", {}) if isinstance(snap, dict) else {}
			if not isinstance(overrides, dict) or not overrides:
				return spells
			out: list[Any] = []
			for spell in spells:
				sid = getattr(spell, "id", None)
				key1 = str(sid) if sid is not None else ""
				override = overrides.get(key1) or overrides.get(sid)
				if not isinstance(override, dict):
					out.append(spell)
					continue
				try:
					new_spell = copy.copy(spell)
				except Exception:
					new_spell = spell
				for k, attr_name in (
					("base_value", "base_value"),
					("range", "range"),
					("area_radius", "area_radius"),
					("spell_cost", "spell_cost"),
					("base_lifespan", "base_lifespan"),
				):
					if k not in override:
						continue
					try:
						setattr(new_spell, attr_name, int(float(override.get(k))))
					except Exception:
						pass
				out.append(new_spell)
			return out

		# 安装 hook
		setattr(env, "execute_attack", execute_attack_hook)
		setattr(env, "get_available_spells", get_available_spells_hook)

	def _build_attribute_action_page(self, content: ttk.LabelFrame) -> None:
		"""构建行动属性页：仅用于调参（已实现、非自定义行动），先做 UI 骨架。"""
		self._sync_action_settings_vars_from_snapshot()

		wrapper = ttk.Frame(content)
		wrapper.grid(row=0, column=0, sticky="nsew")
		wrapper.columnconfigure(0, weight=1)
		wrapper.rowconfigure(2, weight=1)

		ttk.Label(wrapper, text="行动属性", font=("Microsoft YaHei UI", 12, "bold")).grid(
			row=0, column=0, sticky="w", pady=(0, 6)
		)
		note = (
			"用于修改已实现（非自定义）行动的数值：攻击模型、法术模板参数。\n"
			"点击“应用（本局）”即生效（仅本局内存）；关闭程序即清空。"
		)
		ttk.Label(wrapper, text=note, foreground="#4b5563", justify="left", wraplength=640).grid(
			row=1, column=0, sticky="w", pady=(0, 8)
		)

		# Notebook（攻击/法术）冻结：tab 选择条不随内容滚动。
		nb = ttk.Notebook(wrapper)
		nb.grid(row=2, column=0, sticky="nsew")

		active_scroll_canvas: dict[str, Any] = {"canvas": None}

		def _on_mousewheel(event: Any) -> None:
			canvas = active_scroll_canvas.get("canvas")
			if canvas is None or (hasattr(canvas, "winfo_exists") and not canvas.winfo_exists()):
				return
			try:
				delta = int(getattr(event, "delta", 0))
				if delta == 0:
					return
			except Exception:
				return
			# 内容不足一屏时，不滚动，避免出现“空白滚动”。
			try:
				sr = str(canvas.cget("scrollregion") or "").strip()
				parts = [float(x) for x in sr.split()] if sr else []
				content_h = float(parts[3] - parts[1]) if len(parts) == 4 else 0.0
				view_h = float(canvas.winfo_height())
				if content_h <= view_h + 2:
					return
			except Exception:
				pass
			try:
				canvas.yview_scroll(-int(delta / 120), "units")
				# 夹紧到顶/底，避免能滚到无内容区域。
				first, last = canvas.yview()
				if first < 0:
					canvas.yview_moveto(0)
				elif last > 1:
					span = max(1e-9, last - first)
					canvas.yview_moveto(max(0.0, 1.0 - span))
			except Exception:
				return

		wrapper.bind_all("<MouseWheel>", _on_mousewheel)
		wrapper.bind("<Destroy>", lambda _e: wrapper.unbind_all("<MouseWheel>"))

		attack_tab = ttk.Frame(nb)
		spell_tab = ttk.Frame(nb)
		nb.add(attack_tab, text="攻击")
		nb.add(spell_tab, text="法术")

		# --- 攻击 TAB ---
		attack_tab.columnconfigure(0, weight=1)
		attack_tab.rowconfigure(0, weight=1)

		attack_scroll_host = ttk.Frame(attack_tab)
		attack_scroll_host.grid(row=0, column=0, sticky="nsew")
		attack_scroll_host.columnconfigure(0, weight=1)
		attack_scroll_host.rowconfigure(0, weight=1)

		attack_canvas = tk.Canvas(attack_scroll_host, highlightthickness=0, borderwidth=0)
		attack_v_scroll = ttk.Scrollbar(attack_scroll_host, orient="vertical", command=attack_canvas.yview)
		attack_canvas.configure(yscrollcommand=attack_v_scroll.set)
		attack_canvas.grid(row=0, column=0, sticky="nsew")
		attack_v_scroll.grid(row=0, column=1, sticky="ns")

		attack_content = ttk.Frame(attack_canvas, padding=10)
		attack_canvas_window = attack_canvas.create_window((0, 0), window=attack_content, anchor="nw")
		attack_content.columnconfigure(0, weight=1)

		def _sync_attack_scroll_region(_event: Any = None) -> None:
			try:
				attack_content.update_idletasks()
				req_w = int(attack_content.winfo_reqwidth())
				req_h = int(attack_content.winfo_reqheight())
				attack_canvas.configure(scrollregion=(0, 0, max(req_w, 1), max(req_h, 1)))
			except Exception:
				attack_canvas.configure(scrollregion=attack_canvas.bbox("all"))

		def _fit_attack_content_width(event: Any) -> None:
			attack_canvas.itemconfigure(attack_canvas_window, width=int(event.width))

		attack_content.bind("<Configure>", _sync_attack_scroll_region)
		attack_canvas.bind("<Configure>", _fit_attack_content_width)
		attack_canvas.bind("<Enter>", lambda _e: active_scroll_canvas.__setitem__("canvas", attack_canvas))
		attack_content.bind("<Enter>", lambda _e: active_scroll_canvas.__setitem__("canvas", attack_canvas))
		active_scroll_canvas["canvas"] = attack_canvas

		# 公式显示帮助：系数输入框可留空，表示使用默认系数。
		helper = "说明：公式中的【系数】输入框可以留空，表示使用默认系数值。"
		ttk.Label(attack_content, text=helper, foreground="#4b5563").grid(row=0, column=0, sticky="w", pady=(0, 8))

		# ---- 命中判定 ----
		hit_box = ttk.LabelFrame(attack_content, text="命中判定", padding=10)
		hit_box.grid(row=1, column=0, sticky="ew")
		hit_box.columnconfigure(0, weight=1)

		rule_note = "说明：\n- 优势值 = 2×(攻击者高度-受击者高度) + 3×(攻击者环境值-受击者环境值)\n- 环境值：不在任何延时法术/BUFF 中为 0；处在伤害法术范围为 -1；处在 BUFF 范围为 +1（可叠加）"
		ttk.Label(hit_box, text=rule_note, foreground="#4b5563", justify="left", wraplength=640).grid(
			row=0, column=0, sticky="w"
		)

		phy_hit_formula_var = tk.StringVar(value="")
		mag_hit_formula_var = tk.StringVar(value="")
		ttk.Label(hit_box, text="物理攻击：", font=("Microsoft YaHei UI", 10, "bold")).grid(
			row=1, column=0, sticky="w", pady=(8, 0)
		)
		ttk.Label(hit_box, textvariable=phy_hit_formula_var, justify="left", wraplength=640).grid(
			row=2, column=0, sticky="w"
		)

		hit_edit = ttk.Frame(hit_box)
		hit_edit.grid(row=3, column=0, sticky="w", pady=(8, 0))
		ttk.Checkbutton(hit_edit, text="启用 d20", variable=self.attribute_action_attack_vars["enable_d20"]).grid(
			row=0, column=0, sticky="w", padx=(0, 14)
		)
		ttk.Checkbutton(hit_edit, text="d20=20 大成功", variable=self.attribute_action_attack_vars["hit_crit_on_20"]).grid(
			row=0, column=1, sticky="w", padx=(0, 14)
		)
		ttk.Checkbutton(hit_edit, text="d20=1 大失败", variable=self.attribute_action_attack_vars["hit_fail_on_1"]).grid(
			row=0, column=2, sticky="w"
		)

		hit_line = ttk.Frame(hit_box)
		hit_line.grid(row=4, column=0, sticky="w", pady=(8, 0))
		ttk.Label(hit_line, text="攻击投掷 = ").grid(row=0, column=0, sticky="w")
		ttk.Label(hit_line, text="d20 +").grid(row=0, column=1, sticky="w")
		tk.Entry(hit_line, textvariable=self.attribute_action_attack_vars["hit_coeff_strength"], width=7).grid(
			row=0, column=2, sticky="w", padx=(6, 4)
		)
		ttk.Label(hit_line, text="×力量修正 +").grid(row=0, column=3, sticky="w")
		tk.Entry(hit_line, textvariable=self.attribute_action_attack_vars["hit_coeff_dexterity"], width=7).grid(
			row=0, column=4, sticky="w", padx=(6, 4)
		)
		ttk.Label(hit_line, text="×优势值 + 固定加值").grid(row=0, column=5, sticky="w")
		tk.Entry(hit_line, textvariable=self.attribute_action_attack_vars["hit_bonus_flat"], width=8).grid(
			row=0, column=6, sticky="w", padx=(6, 0)
		)

		phy_def_line = ttk.Frame(hit_box)
		phy_def_line.grid(row=5, column=0, sticky="w", pady=(8, 0))
		ttk.Label(phy_def_line, text="豁免值 = ").grid(row=0, column=0, sticky="w")
		tk.Entry(phy_def_line, textvariable=self.attribute_action_attack_vars["phy_def_base_coeff"], width=7).grid(
			row=0, column=1, sticky="w", padx=(6, 4)
		)
		ttk.Label(phy_def_line, text="×目标物理豁免值(物抗) +").grid(row=0, column=2, sticky="w")
		tk.Entry(phy_def_line, textvariable=self.attribute_action_attack_vars["phy_def_attr_coeff"], width=7).grid(
			row=0, column=3, sticky="w", padx=(6, 4)
		)
		ttk.Label(phy_def_line, text="×").grid(row=0, column=4, sticky="w")
		def_mod_values = ["无", "力量修正", "敏捷修正", "智力修正"]
		phy_def_combo = ttk.Combobox(
			phy_def_line,
			textvariable=self.attribute_action_attack_vars["phy_defense_modifier"],
			values=def_mod_values,
			state="readonly",
			width=10,
		)
		phy_def_combo.grid(row=0, column=5, sticky="w", padx=(6, 18))
		ttk.Label(phy_def_line, text="+ 固定加值").grid(row=0, column=6, sticky="w")
		tk.Entry(phy_def_line, textvariable=self.attribute_action_attack_vars["phy_def_flat_bonus"], width=8).grid(
			row=0, column=7, sticky="w", padx=(6, 0)
		)

		ttk.Label(hit_box, text="普通法术攻击：", font=("Microsoft YaHei UI", 10, "bold")).grid(
			row=6, column=0, sticky="w", pady=(10, 0)
		)
		ttk.Label(hit_box, textvariable=mag_hit_formula_var, justify="left", wraplength=640).grid(
			row=7, column=0, sticky="w"
		)

		mag_hit_line = ttk.Frame(hit_box)
		mag_hit_line.grid(row=8, column=0, sticky="w", pady=(8, 0))
		ttk.Label(mag_hit_line, text="攻击投掷 = ").grid(row=0, column=0, sticky="w")
		ttk.Label(mag_hit_line, text="d20 +").grid(row=0, column=1, sticky="w")
		tk.Entry(mag_hit_line, textvariable=self.attribute_action_attack_vars["magic_hit_coeff_intelligence"], width=7).grid(
			row=0, column=2, sticky="w", padx=(6, 4)
		)
		ttk.Label(mag_hit_line, text="×智力修正 +").grid(row=0, column=3, sticky="w")
		tk.Entry(mag_hit_line, textvariable=self.attribute_action_attack_vars["magic_hit_coeff_advantage"], width=7).grid(
			row=0, column=4, sticky="w", padx=(6, 4)
		)
		ttk.Label(mag_hit_line, text="×优势值 + 固定加值").grid(row=0, column=5, sticky="w")
		tk.Entry(mag_hit_line, textvariable=self.attribute_action_attack_vars["magic_hit_bonus_flat"], width=8).grid(
			row=0, column=6, sticky="w", padx=(6, 0)
		)

		mag_def_line = ttk.Frame(hit_box)
		mag_def_line.grid(row=9, column=0, sticky="w", pady=(8, 0))
		ttk.Label(mag_def_line, text="豁免值 = ").grid(row=0, column=0, sticky="w")
		tk.Entry(mag_def_line, textvariable=self.attribute_action_attack_vars["mag_def_base_coeff"], width=7).grid(
			row=0, column=1, sticky="w", padx=(6, 4)
		)
		ttk.Label(mag_def_line, text="×目标法术豁免值(法抗) +").grid(row=0, column=2, sticky="w")
		tk.Entry(mag_def_line, textvariable=self.attribute_action_attack_vars["mag_def_attr_coeff"], width=7).grid(
			row=0, column=3, sticky="w", padx=(6, 4)
		)
		ttk.Label(mag_def_line, text="×").grid(row=0, column=4, sticky="w")
		mag_def_combo = ttk.Combobox(
			mag_def_line,
			textvariable=self.attribute_action_attack_vars["mag_defense_modifier"],
			values=def_mod_values,
			state="readonly",
			width=10,
		)
		mag_def_combo.grid(row=0, column=5, sticky="w", padx=(6, 18))
		ttk.Label(mag_def_line, text="+ 固定加值").grid(row=0, column=6, sticky="w")
		tk.Entry(mag_def_line, textvariable=self.attribute_action_attack_vars["mag_def_flat_bonus"], width=8).grid(
			row=0, column=7, sticky="w", padx=(6, 0)
		)

		# ---- 物理攻击伤害 ----
		phy_box = ttk.LabelFrame(attack_content, text="物理攻击伤害", padding=10)
		phy_box.grid(row=2, column=0, sticky="ew", pady=(10, 0))
		phy_box.columnconfigure(0, weight=1)

		phy_template_var = tk.StringVar(value="")
		phy_effective_var = tk.StringVar(value="")
		ttk.Label(phy_box, textvariable=phy_template_var, justify="left", wraplength=640).grid(
			row=0, column=0, sticky="w"
		)
		ttk.Label(phy_box, textvariable=phy_effective_var, justify="left", wraplength=640).grid(
			row=1, column=0, sticky="w", pady=(4, 0)
		)

		phy_line = ttk.Frame(phy_box)
		phy_line.grid(row=2, column=0, sticky="w", pady=(8, 0))
		ttk.Checkbutton(
			phy_line,
			text="以棋子物伤作为原伤害基础值",
			variable=self.attribute_action_attack_vars["phy_base_from_piece"],
		).grid(row=0, column=0, sticky="w", padx=(0, 12))
		ttk.Label(phy_line, text="覆盖基础值(未勾选时必填)").grid(row=0, column=1, sticky="w")
		phy_base_override_entry = tk.Entry(
			phy_line,
			textvariable=self.attribute_action_attack_vars["phy_base_override"],
			width=10,
		)
		phy_base_override_entry.grid(
			row=0, column=2, sticky="w", padx=(6, 12)
		)
		ttk.Label(phy_line, text="固定加值").grid(row=0, column=3, sticky="w")
		tk.Entry(phy_line, textvariable=self.attribute_action_attack_vars["phy_flat_bonus"], width=8).grid(
			row=0, column=4, sticky="w", padx=(6, 0)
		)

		phy_line2 = ttk.Frame(phy_box)
		phy_line2.grid(row=3, column=0, sticky="w", pady=(8, 0))
		ttk.Label(phy_line2, text="原始伤害 = 基础值 + 固定加值").grid(row=0, column=0, sticky="w")

		# ---- 普通法术攻击伤害 ----
		mag_box = ttk.LabelFrame(attack_content, text="普通法术攻击伤害", padding=10)
		mag_box.grid(row=3, column=0, sticky="ew", pady=(10, 0))
		mag_box.columnconfigure(0, weight=1)

		mag_template_var = tk.StringVar(value="")
		mag_effective_var = tk.StringVar(value="")
		ttk.Label(mag_box, textvariable=mag_template_var, justify="left", wraplength=640).grid(
			row=0, column=0, sticky="w"
		)
		ttk.Label(mag_box, textvariable=mag_effective_var, justify="left", wraplength=640).grid(
			row=1, column=0, sticky="w", pady=(4, 0)
		)

		mag_line = ttk.Frame(mag_box)
		mag_line.grid(row=2, column=0, sticky="w", pady=(8, 0))
		ttk.Checkbutton(
			mag_line,
			text="以棋子法伤作为原伤害基础值",
			variable=self.attribute_action_attack_vars["mag_base_from_piece"],
		).grid(row=0, column=0, sticky="w", padx=(0, 12))
		ttk.Label(mag_line, text="覆盖基础值(未勾选时必填)").grid(row=0, column=1, sticky="w")
		mag_base_override_entry = tk.Entry(
			mag_line,
			textvariable=self.attribute_action_attack_vars["mag_base_override"],
			width=10,
		)
		mag_base_override_entry.grid(
			row=0, column=2, sticky="w", padx=(6, 12)
		)
		ttk.Label(mag_line, text="固定加值").grid(row=0, column=3, sticky="w")
		tk.Entry(mag_line, textvariable=self.attribute_action_attack_vars["mag_flat_bonus"], width=8).grid(
			row=0, column=4, sticky="w", padx=(6, 0)
		)

		mag_line2 = ttk.Frame(mag_box)
		mag_line2.grid(row=3, column=0, sticky="w", pady=(8, 0))
		ttk.Label(mag_line2, text="原始伤害 = 基础值 + 固定加值").grid(row=0, column=0, sticky="w")

		def _effective_float(var_key: str, default_key: str, fallback: float) -> float:
			var = self.attribute_action_attack_vars.get(var_key)
			if var is None:
				return float(self.attribute_action_attack_defaults.get(default_key, fallback))
			raw = str(var.get()).strip()
			if raw == "":
				return float(self.attribute_action_attack_defaults.get(default_key, fallback))
			return self._safe_float(raw, float(self.attribute_action_attack_defaults.get(default_key, fallback)))

		def _refresh_formulas(*_args: Any) -> None:
			use_d20 = bool(self.attribute_action_attack_vars.get("enable_d20").get())
			crit_on_20 = bool(self.attribute_action_attack_vars.get("hit_crit_on_20").get())
			fail_on_1 = bool(self.attribute_action_attack_vars.get("hit_fail_on_1").get())

			d20_rule: list[str] = []
			if use_d20:
				d20_rule.append("使用 d20")
				if fail_on_1:
					d20_rule.append("1 大失败")
				if crit_on_20:
					d20_rule.append("20 大成功且暴击")
				else:
					d20_rule.append("20 大成功")
			else:
				d20_rule.append("不使用 d20")
			d20_rule_text = "；".join(d20_rule)

			def _def_mod_desc(label: str, default_label: str) -> str:
				label = str(label or "").strip() or default_label
				if label == "无":
					return "无"
				return f"{label}"

			def _defense_formula_text(
				base_coeff: float,
				base_name: str,
				attr_coeff: float,
				attr_name: str,
				flat_bonus: float,
			) -> str:
				parts: list[str] = []
				if abs(base_coeff) > 1e-9:
					parts.append(f"{base_coeff:g}×{base_name}")
				if attr_name != "无" and abs(attr_coeff) > 1e-9:
					parts.append(f"{attr_coeff:g}×{attr_name}")
				if abs(flat_bonus) > 1e-9:
					parts.append(f"{flat_bonus:g}（固定加值）")
				return " + ".join(parts) if parts else "0"

			# --- 物理攻击命中 ---
			hit_a = _effective_float("hit_coeff_strength", "hit_coeff_strength", 1.0)
			hit_adv = _effective_float("hit_coeff_dexterity", "hit_coeff_dexterity", 1.0)
			hit_bonus = self._safe_float(str(self.attribute_action_attack_vars.get("hit_bonus_flat").get()).strip(), 0.0)
			phy_def_mod = _def_mod_desc(
				str(self.attribute_action_attack_vars.get("phy_defense_modifier").get()),
				"敏捷修正",
			)
			phy_def_base_coeff = _effective_float("phy_def_base_coeff", "phy_def_base_coeff", 1.0)
			phy_def_attr_coeff = _effective_float("phy_def_attr_coeff", "phy_def_attr_coeff", 1.0)
			phy_def_flat = _effective_float("phy_def_flat_bonus", "phy_def_flat_bonus", 0.0)
			phy_def_text = _defense_formula_text(
				phy_def_base_coeff,
				"目标物理豁免值(物抗)",
				phy_def_attr_coeff,
				phy_def_mod,
				phy_def_flat,
			)

			hit_parts: list[str] = []
			if use_d20:
				hit_parts.append("d20")
			if abs(hit_a) > 1e-9:
				hit_parts.append(f"{hit_a:g}×力量修正")
			if abs(hit_adv) > 1e-9:
				hit_parts.append(f"{hit_adv:g}×优势值")
			if abs(hit_bonus) > 1e-9:
				hit_parts.append(f"{hit_bonus:g}（固定加值）")
			attack_throw_text = " + ".join(hit_parts) if hit_parts else "0"
			phy_hit_formula_var.set(
				"\n".join(
					[
						f"命中判定（是否命中）：攻击投掷 > 豁免值(防御值)",
						f"d20 规则：{d20_rule_text}",
						f"攻击投掷 = {attack_throw_text}",
						f"豁免值(防御值) = {phy_def_text}",
					]
				)
			)

			# --- 普通法术攻击命中 ---
			mag_hit_int = _effective_float(
				"magic_hit_coeff_intelligence", "magic_hit_coeff_intelligence", 1.0
			)
			mag_hit_adv = _effective_float(
				"magic_hit_coeff_advantage", "magic_hit_coeff_advantage", 1.0
			)
			mag_hit_bonus = self._safe_float(
				str(self.attribute_action_attack_vars.get("magic_hit_bonus_flat").get()).strip(), 0.0
			)
			mag_def_mod = _def_mod_desc(
				str(self.attribute_action_attack_vars.get("mag_defense_modifier").get()),
				"无",
			)
			mag_def_base_coeff = _effective_float("mag_def_base_coeff", "mag_def_base_coeff", 1.0)
			mag_def_attr_coeff = _effective_float("mag_def_attr_coeff", "mag_def_attr_coeff", 1.0)
			mag_def_flat = _effective_float("mag_def_flat_bonus", "mag_def_flat_bonus", 0.0)
			mag_def_text = _defense_formula_text(
				mag_def_base_coeff,
				"目标法术豁免值(法抗)",
				mag_def_attr_coeff,
				mag_def_mod,
				mag_def_flat,
			)

			mag_hit_parts: list[str] = []
			if use_d20:
				mag_hit_parts.append("d20")
			if abs(mag_hit_int) > 1e-9:
				mag_hit_parts.append(f"{mag_hit_int:g}×智力修正")
			if abs(mag_hit_adv) > 1e-9:
				mag_hit_parts.append(f"{mag_hit_adv:g}×优势值")
			if abs(mag_hit_bonus) > 1e-9:
				mag_hit_parts.append(f"{mag_hit_bonus:g}（固定加值）")
			mag_attack_throw_text = " + ".join(mag_hit_parts) if mag_hit_parts else "0"
			mag_hit_formula_var.set(
				"\n".join(
					[
						f"命中判定（是否命中）：攻击投掷 > 豁免值(防御值)",
						f"d20 规则：{d20_rule_text}",
						f"攻击投掷 = {mag_attack_throw_text}",
						f"豁免值(防御值) = {mag_def_text}",
					]
				)
			)

			phy_flat = self._safe_float(str(self.attribute_action_attack_vars.get("phy_flat_bonus").get()).strip(), 0.0)
			use_piece_phy = bool(self.attribute_action_attack_vars.get("phy_base_from_piece").get())
			phy_base_src = "棋子物伤" if use_piece_phy else "覆盖基础值"
			phy_base_override = str(self.attribute_action_attack_vars.get("phy_base_override").get()).strip()
			if (not use_piece_phy) and phy_base_override != "":
				phy_base_src = f"覆盖基础值={phy_base_override}"
			phy_parts = [phy_base_src]
			if abs(phy_flat) > 1e-9:
				phy_parts.append(f"{phy_flat:g}（固定加值）")
			raw_phy = " + ".join(phy_parts) if phy_parts else "0"
			phy_template_var.set(
				"\n".join(
					[
						"规则说明（应用时生效）：",
						"原始伤害 = 基础值 + 固定加值",
						"说明：基础值为“棋子物伤”或“覆盖基础值”（由下方勾选决定）",
					]
				)
			)
			phy_effective_var.set(
				"\n".join(
					[
						"生效式（应用时生效）：",
						f"原始伤害 = {raw_phy}",
						"暴击：原始伤害 × 2",
					]
				)
			)

			mag_flat = self._safe_float(str(self.attribute_action_attack_vars.get("mag_flat_bonus").get()).strip(), 0.0)
			use_piece_mag = bool(self.attribute_action_attack_vars.get("mag_base_from_piece").get())
			mag_base_src = "棋子法伤" if use_piece_mag else "覆盖基础值"
			mag_base_override = str(self.attribute_action_attack_vars.get("mag_base_override").get()).strip()
			if (not use_piece_mag) and mag_base_override != "":
				mag_base_src = f"覆盖基础值={mag_base_override}"
			mag_parts = [mag_base_src]
			if abs(mag_flat) > 1e-9:
				mag_parts.append(f"{mag_flat:g}（固定加值）")
			raw_mag = " + ".join(mag_parts) if mag_parts else "0"
			mag_template_var.set(
				"\n".join(
					[
						"规则说明（应用时生效）：",
						"原始伤害 = 基础值 + 固定加值",
						"说明：基础值为“棋子法伤”或“覆盖基础值”（由下方勾选决定）",
					]
				)
			)
			mag_effective_var.set(
				"\n".join(
					[
						"生效式（应用时生效）：",
						f"原始伤害 = {raw_mag}",
						"暴击：原始伤害 × 2",
					]
				)
			)

		# 绑定刷新
		for key in (
			"enable_d20",
			"hit_crit_on_20",
			"hit_fail_on_1",
			"hit_coeff_strength",
			"hit_coeff_dexterity",
			"hit_bonus_flat",
			"phy_defense_modifier",
			"phy_def_base_coeff",
			"phy_def_attr_coeff",
			"phy_def_flat_bonus",
			"magic_hit_coeff_intelligence",
			"magic_hit_coeff_advantage",
			"magic_hit_bonus_flat",
			"mag_defense_modifier",
			"mag_def_base_coeff",
			"mag_def_attr_coeff",
			"mag_def_flat_bonus",
			"phy_base_from_piece",
			"phy_base_override",
			"phy_flat_bonus",
			"mag_base_from_piece",
			"mag_base_override",
			"mag_flat_bonus",
		):
			var = self.attribute_action_attack_vars.get(key)
			if var is None:
				continue
			try:
				var.trace_add("write", _refresh_formulas)
			except Exception:
				pass
		_refresh_formulas()

		def _refresh_base_override_state(*_args: Any) -> None:
			try:
				use_piece_phy = bool(self.attribute_action_attack_vars.get("phy_base_from_piece").get())
			except Exception:
				use_piece_phy = True
			try:
				use_piece_mag = bool(self.attribute_action_attack_vars.get("mag_base_from_piece").get())
			except Exception:
				use_piece_mag = True
			try:
				phy_base_override_entry.configure(state=("disabled" if use_piece_phy else "normal"))
			except Exception:
				pass
			try:
				mag_base_override_entry.configure(state=("disabled" if use_piece_mag else "normal"))
			except Exception:
				pass

		for k in ("phy_base_from_piece", "mag_base_from_piece"):
			var = self.attribute_action_attack_vars.get(k)
			if var is None:
				continue
			try:
				var.trace_add("write", _refresh_base_override_state)
			except Exception:
				pass
		_refresh_base_override_state()

		# --- 法术 TAB ---
		spell_tab.columnconfigure(0, weight=1)
		spell_tab.rowconfigure(1, weight=1)
		spell_tab.configure(padding=10)
		ttk.Label(
			spell_tab,
			text="勾选‘覆盖’后，应用时才会生效（未勾选则使用后端默认值）。",
			foreground="#4b5563",
		).grid(
			row=0, column=0, sticky="w", pady=(0, 8)
		)

		scroll_host = ttk.Frame(spell_tab)
		scroll_host.grid(row=1, column=0, sticky="nsew")
		scroll_host.columnconfigure(0, weight=1)
		scroll_host.rowconfigure(0, weight=1)

		spell_canvas = tk.Canvas(scroll_host, highlightthickness=0, borderwidth=0)
		v_scroll = ttk.Scrollbar(scroll_host, orient="vertical", command=spell_canvas.yview)
		spell_canvas.configure(yscrollcommand=v_scroll.set)
		spell_canvas.grid(row=0, column=0, sticky="nsew")
		v_scroll.grid(row=0, column=1, sticky="ns")

		scroll_content = ttk.Frame(spell_canvas)
		canvas_window = spell_canvas.create_window((0, 0), window=scroll_content, anchor="nw")

		def _sync_scroll_region(_event: Any = None) -> None:
			# 用内容的 req 尺寸精确设置滚动区域，避免能滚到空白。
			try:
				scroll_content.update_idletasks()
				req_w = int(scroll_content.winfo_reqwidth())
				req_h = int(scroll_content.winfo_reqheight())
				spell_canvas.configure(scrollregion=(0, 0, max(req_w, 1), max(req_h, 1)))
			except Exception:
				spell_canvas.configure(scrollregion=spell_canvas.bbox("all"))

		def _fit_scroll_content_width(event: Any) -> None:
			spell_canvas.itemconfigure(canvas_window, width=int(event.width))

		scroll_content.bind("<Configure>", _sync_scroll_region)
		spell_canvas.bind("<Configure>", _fit_scroll_content_width)
		spell_canvas.bind("<Enter>", lambda _e: active_scroll_canvas.__setitem__("canvas", spell_canvas))
		scroll_content.bind("<Enter>", lambda _e: active_scroll_canvas.__setitem__("canvas", spell_canvas))

		head = ttk.Frame(scroll_content)
		head.grid(row=0, column=0, sticky="ew")
		cols = [
			("覆盖", 6),
			("法术", 16),
			("基础值", 8),
			("距离", 6),
			("半径", 6),
			("消耗", 6),
			("寿命", 6),
		]
		for cidx, (title, w) in enumerate(cols):
			ttk.Label(head, text=title, width=w).grid(row=0, column=cidx, sticky="w", padx=(0, 6))

		for ridx, spell in enumerate(SpellFactory.get_all_spells(), start=1):
			sid = int(getattr(spell, "id", 0))
			if sid <= 0:
				continue
			enable_var = self.attribute_action_spell_enable_vars.get(sid)
			vars_map = self.attribute_action_spell_vars.get(sid)
			if enable_var is None or vars_map is None:
				continue

			rowf = ttk.Frame(scroll_content)
			rowf.grid(row=ridx, column=0, sticky="ew", pady=(0, 4))
			ttk.Checkbutton(rowf, variable=enable_var).grid(row=0, column=0, sticky="w", padx=(0, 6))
			name = f"{sid}:{getattr(spell, 'name', '')}"
			ttk.Label(rowf, text=name, width=16).grid(row=0, column=1, sticky="w", padx=(0, 6))
			tk.Entry(rowf, textvariable=vars_map["base_value"], width=8).grid(row=0, column=2, sticky="w", padx=(0, 6))
			tk.Entry(rowf, textvariable=vars_map["range"], width=6).grid(row=0, column=3, sticky="w", padx=(0, 6))
			tk.Entry(rowf, textvariable=vars_map["area_radius"], width=6).grid(row=0, column=4, sticky="w", padx=(0, 6))
			tk.Entry(rowf, textvariable=vars_map["spell_cost"], width=6).grid(row=0, column=5, sticky="w", padx=(0, 6))
			tk.Entry(rowf, textvariable=vars_map["base_lifespan"], width=6).grid(row=0, column=6, sticky="w")

		# --- 底部按钮（冻结） ---
		btn_row = ttk.Frame(wrapper)
		btn_row.grid(row=3, column=0, sticky="ew", pady=(10, 0))
		btn_row.columnconfigure(0, weight=1)
		left = ttk.Frame(btn_row)
		left.grid(row=0, column=0, sticky="w")
		ttk.Button(left, text="恢复默认", command=self._reset_action_attribute_to_defaults).pack(side="left")
		ttk.Button(left, text="应用（本局）", command=self._apply_action_attribute_changes).pack(side="left", padx=(8, 0))

		right = ttk.Frame(btn_row)
		right.grid(row=0, column=1, sticky="e")
		self.attribute_action_warning_label = ttk.Label(right, text="")
		self.attribute_action_warning_label.pack(side="right", padx=(8, 0))
		self.attribute_action_apply_status_label = ttk.Label(right, text="")
		self.attribute_action_apply_status_label.pack(side="right")

		def _mark_dirty(*_args: Any) -> None:
			if bool(getattr(self, "action_attribute_internal_update", False)):
				return
			label = self.attribute_action_apply_status_label
			if label is None or (hasattr(label, "winfo_exists") and not label.winfo_exists()):
				return
			try:
				label.configure(text="未应用（有修改）", foreground="#b45309")
			except Exception:
				return

		if not bool(getattr(self, "_action_attribute_dirty_trace_bound", False)):
			# 仅绑定一次，避免每次切换页面重复 trace 导致回调叠加。
			for var in self.attribute_action_attack_vars.values():
				try:
					var.trace_add("write", _mark_dirty)
				except Exception:
					pass
			for var in self.attribute_action_spell_enable_vars.values():
				try:
					var.trace_add("write", _mark_dirty)
				except Exception:
					pass
			for vars_map in self.attribute_action_spell_vars.values():
				for var in vars_map.values():
					try:
						var.trace_add("write", _mark_dirty)
					except Exception:
						pass
			self._action_attribute_dirty_trace_bound = True

	def _is_map_edit_available(self) -> bool:
		if self.controller.runtime_source == "runtime_env":
			return self.controller.environment is not None
		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return False
		board = game_data.get("map", {})
		rows = board.get("rows", []) if isinstance(board, dict) else []
		return isinstance(rows, list) and len(rows) > 0

	def _get_current_map_height(self, x: int, y: int) -> int | None:
		if self.controller.runtime_source == "runtime_env":
			env = self.controller.environment
			if env is None or getattr(env, "board", None) is None:
				return None
			board = env.board
			width = int(getattr(board, "width", 0))
			height = int(getattr(board, "height", 0))
			if not (0 <= x < width and 0 <= y < height):
				return None
			height_map = getattr(board, "height_map", None)
			if height_map is None:
				return None
			try:
				return int(height_map[x][y])
			except Exception:
				return None

		rows = self._extract_mock_visual_rows()
		if y < 0 or y >= len(rows):
			return None
		row = rows[y]
		if x < 0 or x >= len(row):
			return None
		return int(row[x])

	def _show_map_apply_feedback(self, message: str) -> None:
		label = self.attribute_map_apply_status_label
		if label is None:
			return
		label.configure(text=message, foreground="#059669")

	def _map_height_to_color(self, height_value: int) -> str:
		if height_value == -1:
			return "#6B7280"
		if height_value == 0:
			return "#B7E4C7"
		if height_value == 1:
			return "#B08968"
		if height_value == 2:
			return "#5B3A29"
		return "#6b7280"

	def _update_map_height_preview(self) -> None:
		canvas = self.attribute_map_height_color_canvas
		if canvas is None or not canvas.winfo_exists():
			return
		height_value = self._safe_int(self.attribute_map_height_var.get(), 0)
		fill = self._map_height_to_color(height_value)
		canvas.delete("all")
		canvas.create_rectangle(2, 2, 20, 20, fill=fill, outline="#374151", width=1)

	def _apply_map_height_change(self) -> None:
		if not self._is_map_edit_available():
			self._show_notice_popup("提示", "当前数据源不支持地图高度编辑")
			return
		x = self._safe_int(self.attribute_map_x_var.get(), -1)
		y = self._safe_int(self.attribute_map_y_var.get(), -1)
		h = self._safe_int(self.attribute_map_height_var.get(), -999)
		if x < 0 or y < 0:
			self._show_notice_popup("提示", "请先输入合法坐标 (X,Y)")
			return
		if h not in (-1, 0, 1, 2):
			self._show_notice_popup("提示", "高度仅支持 -1/0/1/2（-1=不可行，0=地面，1/2=高地）")
			return

		if self.controller.runtime_source == "runtime_env":
			env = self.controller.environment
			board = env.board if env is not None else None
			if board is None:
				self._show_notice_popup("提示", "地图未初始化，无法应用高度")
				return
			width = int(getattr(board, "width", 0))
			height = int(getattr(board, "height", 0))
			if not (0 <= x < width and 0 <= y < height):
				self._show_notice_popup("提示", "坐标越界，请修改后重试")
				return
			try:
				board.height_map[x][y] = int(h)
			except Exception as e:
				self._show_notice_popup("提示", f"高度写入失败: {e}")
				return
		else:
			rows = self._extract_mock_visual_rows()
			if y < 0 or y >= len(rows) or x < 0 or x >= len(rows[y]):
				self._show_notice_popup("提示", "坐标越界，请修改后重试")
				return
			self.mock_map_height_overrides[(x, y)] = int(h)

		self._show_map_apply_feedback("应用成功")
		self.right_info_panel.append_content(f"\n[UI] 地图高度已更新: ({x}, {y}) -> {h}")
		self._refresh_board_view()

	def _stop_map_point_pick(self) -> None:
		self.attribute_map_pick_waiting = False
		overlay = self.attribute_map_pick_overlay
		self.attribute_map_pick_overlay = None
		if overlay is not None and overlay.winfo_exists():
			overlay.destroy()
		popup = self.attribute_map_pick_invalid_popup
		self.attribute_map_pick_invalid_popup = None
		if popup is not None and popup.winfo_exists():
			popup.destroy()

	def _restore_map_attribute_page_after_pick(self) -> None:
		"""结束选点并回到地图属性页，不修改本次坐标。"""
		self._stop_map_point_pick()
		if self.attribute_settings_window is not None and self.attribute_settings_window.winfo_exists():
			self.attribute_settings_window.deiconify()
			self.attribute_settings_window.lift()
			self.attribute_settings_window.focus_force()
			self._switch_attribute_settings_page("map")

	def _show_map_pick_invalid_popup(self) -> None:
		"""地图选点时点击非法区域后的引导弹窗。"""
		existing = self.attribute_map_pick_invalid_popup
		if existing is not None and existing.winfo_exists():
			existing.lift()
			return

		window = tk.Toplevel(self.root)
		window.title("提示")
		window.transient(self.root)
		window.resizable(False, False)
		window.attributes("-topmost", True)
		self.attribute_map_pick_invalid_popup = window

		frame = ttk.Frame(window, padding=12)
		frame.pack(fill="both", expand=True)
		ttk.Label(frame, text="请选择合法位置", justify="left").pack(anchor="w")

		button_row = ttk.Frame(frame)
		button_row.pack(anchor="e", pady=(10, 0))

		def _resume_pick_overlay() -> None:
			"""继续选点时恢复覆盖层焦点，避免点击穿透。"""
			self.attribute_map_pick_waiting = True
			overlay = self.attribute_map_pick_overlay
			if overlay is None or not overlay.winfo_exists():
				self._begin_map_point_pick()
				return
			overlay.attributes("-topmost", True)
			overlay.lift(self.root)
			self.right_info_panel.append_content("\n[UI] 继续地图选点：请点击棋盘中的一个格子")

		def on_continue_pick() -> None:
			if self.attribute_map_pick_invalid_popup is not None:
				self.attribute_map_pick_invalid_popup = None
			window.destroy()
			_resume_pick_overlay()

		def on_exit_pick() -> None:
			if self.attribute_map_pick_invalid_popup is not None:
				self.attribute_map_pick_invalid_popup = None
			window.destroy()
			self._restore_map_attribute_page_after_pick()
			self.right_info_panel.append_content("\n[UI] 已退出地图选点，返回地图属性页")

		ttk.Button(button_row, text="继续选点", command=on_continue_pick).pack(side="left")
		ttk.Button(button_row, text="退出选点", command=on_exit_pick).pack(side="left", padx=(8, 0))
		window.protocol("WM_DELETE_WINDOW", on_exit_pick)

		self._center_popup_window(window)
		window.lift()

	def _on_map_pick_overlay_click(self, event: tk.Event) -> str:
		if not self.attribute_map_pick_waiting:
			return "break"
		board_x, board_y = self.left_board_panel.get_board_xy_from_root(int(event.x_root), int(event.y_root))
		if board_x is None or board_y is None:
			self._show_map_pick_invalid_popup()
			return "break"

		h = self._get_current_map_height(board_x, board_y)
		self.attribute_map_x_var.set(str(board_x))
		self.attribute_map_y_var.set(str(board_y))
		self.attribute_map_height_var.set(str(h if h is not None else 0))
		self._stop_map_point_pick()
		if self.attribute_settings_window is not None and self.attribute_settings_window.winfo_exists():
			self.attribute_settings_window.deiconify()
			self.attribute_settings_window.lift()
			self.attribute_settings_window.focus_force()
			self._switch_attribute_settings_page("map")
		self._show_map_apply_feedback(f"已选定坐标 ({board_x}, {board_y})")
		self.right_info_panel.append_content(f"\n[UI] 已选定地图坐标: ({board_x}, {board_y})")
		return "break"

	def _begin_map_point_pick(self) -> None:
		if not self._is_map_edit_available():
			self._show_notice_popup("提示", "当前数据源不支持地图选点")
			return
		self._stop_map_point_pick()
		self.attribute_map_pick_waiting = True
		if self.attribute_settings_window is not None and self.attribute_settings_window.winfo_exists():
			self.attribute_settings_window.withdraw()

		overlay = tk.Toplevel(self.root)
		overlay.overrideredirect(True)
		overlay.attributes("-alpha", 0.01)
		overlay.attributes("-topmost", True)
		overlay.lift(self.root)
		overlay.geometry(
			f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_rootx()}+{self.root.winfo_rooty()}"
		)
		overlay.bind("<Button-1>", self._on_map_pick_overlay_click)
		overlay.bind("<ButtonRelease-1>", lambda _e: "break")
		self.attribute_map_pick_overlay = overlay
		self.right_info_panel.append_content("\n[UI] 地图选点模式：请点击棋盘中的一个格子")

	def _build_attribute_map_page(self, content: ttk.LabelFrame) -> None:
		wrapper = ttk.Frame(content)
		wrapper.grid(row=0, column=0, sticky="nsew")
		wrapper.columnconfigure(0, weight=1)
		wrapper.rowconfigure(4, weight=1)

		ttk.Label(wrapper, text="地图属性", font=("Microsoft YaHei UI", 12, "bold")).grid(
			row=0, column=0, sticky="w", pady=(0, 8)
		)

		note_text = "高度说明：-1=不可行，0=地面，1=黄棕高地，2=深棕高地"
		ttk.Label(wrapper, text=note_text, foreground="#4b5563").grid(row=1, column=0, sticky="w", pady=(0, 8))

		form = ttk.Frame(wrapper)
		form.grid(row=2, column=0, sticky="w")

		ttk.Label(form, text="将（").grid(row=0, column=0, sticky="w")
		tk.Entry(form, textvariable=self.attribute_map_x_var, width=4).grid(row=0, column=1, sticky="w")
		ttk.Label(form, text="，").grid(row=0, column=2, sticky="w")
		tk.Entry(form, textvariable=self.attribute_map_y_var, width=4).grid(row=0, column=3, sticky="w")
		ttk.Label(form, text="）处的高度更改为").grid(row=0, column=4, sticky="w")
		tk.Entry(form, textvariable=self.attribute_map_height_var, width=4).grid(row=0, column=5, sticky="w")
		self.attribute_map_height_color_canvas = tk.Canvas(form, width=22, height=22, highlightthickness=0, bg="#f8fafc")
		self.attribute_map_height_color_canvas.grid(row=0, column=6, sticky="w", padx=(8, 0))
		self._update_map_height_preview()

		btn_row = ttk.Frame(wrapper)
		btn_row.grid(row=3, column=0, sticky="w", pady=(10, 0))
		ttk.Button(btn_row, text="地图选点", command=self._begin_map_point_pick).pack(side="left")
		ttk.Button(btn_row, text="应用高度", command=self._apply_map_height_change).pack(side="left", padx=(8, 0))
		self.attribute_map_apply_status_label = ttk.Label(btn_row, text="", foreground="#059669")
		self.attribute_map_apply_status_label.pack(side="left", padx=(10, 0))

		if not self._is_map_edit_available():
			ttk.Label(
				wrapper,
				text="当前数据源不支持高度编辑。",
				foreground="#b45309",
			).grid(row=4, column=0, sticky="w", pady=(8, 0))

	def _piece_slot_keys(self) -> list[str]:
		return [f"p{team}_{idx}" for team in (1, 2) for idx in (1, 2, 3)]

	def _coerce_piece_list(self, pieces_obj: Any) -> list[Any]:
		if isinstance(pieces_obj, list):
			return pieces_obj
		if isinstance(pieces_obj, tuple):
			return list(pieces_obj)
		if pieces_obj is None or isinstance(pieces_obj, (str, bytes, dict)):
			return []
		try:
			return list(pieces_obj)
		except Exception:
			return []

	def _runtime_piece_slot_map(self) -> dict[str, Any]:
		result: dict[str, Any] = {}
		env = self.controller.environment
		if env is None:
			return result
		if self.runtime_piece_init_config and not self.runtime_piece_slot_binding:
			self._capture_runtime_piece_slot_binding_from_init_config()

		for team_id, player_attr in ((1, "player1"), (2, "player2")):
			player = getattr(env, player_attr, None)
			pieces = self._coerce_piece_list(getattr(player, "pieces", None) if player is not None else None)
			if not pieces:
				continue
			sorted_pieces = sorted(pieces, key=lambda p: int(getattr(p, "id", 0)))
			used_slots: set[str] = set()

			for piece in sorted_pieces:
				slot_key = self.runtime_piece_slot_binding.get(id(piece), "")
				if not slot_key.startswith(f"p{team_id}_"):
					continue
				if slot_key in used_slots:
					continue
				result[slot_key] = piece
				used_slots.add(slot_key)

			fallback_slots = [f"p{team_id}_{idx}" for idx in (1, 2, 3) if f"p{team_id}_{idx}" not in used_slots]
			fallback_idx = 0
			for piece in sorted_pieces:
				bound_slot = self.runtime_piece_slot_binding.get(id(piece), "")
				if bound_slot in used_slots:
					continue
				if fallback_idx >= len(fallback_slots):
					break
				slot_key = fallback_slots[fallback_idx]
				fallback_idx += 1
				result[slot_key] = piece
				used_slots.add(slot_key)
		return result

	def _capture_runtime_piece_slot_binding_from_init_config(self) -> None:
		"""按初始化配置建立棋子与槽位的一次性绑定，避免非连续槽位被重排。"""
		env = self.controller.environment
		if env is None:
			return

		new_binding: dict[int, str] = {}
		for team_id, player_attr in ((1, "player1"), (2, "player2")):
			player = getattr(env, player_attr, None)
			pieces = self._coerce_piece_list(getattr(player, "pieces", None) if player is not None else None)
			if not pieces:
				continue

			expected_slots: list[tuple[str, int, int]] = []
			for idx in (1, 2, 3):
				slot_key = f"p{team_id}_{idx}"
				cfg = self.runtime_piece_init_config.get(slot_key, {})
				if self._is_profession_mode():
					if not self._is_profession_slot_active_from_cfg(cfg):
						continue
				else:
					hp_raw = str(cfg.get("hp", "-")).strip()
					if hp_raw in ("", "-", "-1") or self._safe_int(hp_raw, -1) <= 0:
						continue
				x = self._safe_int(str(cfg.get("pos_x", 0)), 0)
				y = self._safe_int(str(cfg.get("pos_y", 0)), 0)
				expected_slots.append((slot_key, x, y))

			remaining_pieces = list(pieces)
			used_slots: set[str] = set()

			for slot_key, x, y in expected_slots:
				matched_piece = next(
					(
						piece
						for piece in remaining_pieces
						if int(getattr(getattr(piece, "position", None), "x", -9999)) == x
						and int(getattr(getattr(piece, "position", None), "y", -9999)) == y
					),
					None,
				)
				if matched_piece is None:
					continue
				new_binding[id(matched_piece)] = slot_key
				used_slots.add(slot_key)
				remaining_pieces.remove(matched_piece)

			remaining_slots = [slot for slot, _x, _y in expected_slots if slot not in used_slots]
			remaining_pieces.sort(key=lambda p: int(getattr(p, "id", 0)))
			for slot_key, piece in zip(remaining_slots, remaining_pieces):
				new_binding[id(piece)] = slot_key

		self.runtime_piece_slot_binding = new_binding

	def _mock_piece_slot_map(self) -> dict[str, int]:
		result: dict[str, int] = {}
		for soldier_id, state in self.mock_initial_positions.items():
			team = int(state.get("team", 1))
			piece_no = int(self.mock_piece_number_by_id.get(soldier_id, 0))
			if team not in (1, 2) or piece_no not in (1, 2, 3):
				continue
			result[f"p{team}_{piece_no}"] = int(soldier_id)
		return result

	def _get_piece_row_values(self, slot_key: str, runtime_map: dict[str, Any], mock_map: dict[str, int]) -> dict[str, str]:
		if self.attribute_settings_force_init_mode and self._is_runtime_selected_source():
			fixed_positions: dict[str, tuple[int, int]] = {
				"p1_1": (3, 8),
				"p1_2": (8, 3),
				"p1_3": (17, 4),
				"p2_1": (16, 11),
				"p2_2": (11, 16),
				"p2_3": (2, 15),
			}
			px, py = fixed_positions.get(slot_key, (0, 0))
			px, py = self._clamp_piece_position(px, py)
			if self._is_profession_mode():
				default_cfg = {
					"hp": "-",
					"profession": "战士(长)",
					"weapon": "长剑",
					"armor": "轻甲",
					"strength": "-",
					"dexterity": "-",
					"intelligence": "-",
					"physical_resist": "-",
					"magic_resist": "-",
					"physical_damage": "-",
					"magic_damage": "-",
					"action_points": "-",
					"max_action_points": "-",
					"spell_slots": "-",
					"max_spell_slots": "-",
					"movement": "-",
					"pos_x": str(px),
					"pos_y": str(py),
				}
			else:
				default_cfg = {
					"hp": "",
					"profession": "自定义",
					"weapon": "自定义",
					"armor": "无甲",
					"strength": "10",
					"dexterity": "10",
					"intelligence": "10",
					"physical_resist": "15",
					"magic_resist": "13",
					"physical_damage": "18",
					"magic_damage": "0",
					"action_points": "2",
					"max_action_points": "2",
					"spell_slots": "2",
					"max_spell_slots": "2",
					"movement": "25",
					"pos_x": str(px),
					"pos_y": str(py),
				}
			cfg = self.runtime_piece_init_config.get(slot_key, {})
			for key, val in cfg.items():
				default_cfg[key] = str(val)
			return default_cfg

		default_values = {
			"hp": "0",
			"profession": "自定义",
			"weapon": "自定义",
			"armor": "无甲",
			"strength": "0",
			"dexterity": "0",
			"intelligence": "0",
			"physical_resist": "0",
			"magic_resist": "0",
			"physical_damage": "0",
			"magic_damage": "0",
			"action_points": "0",
			"max_action_points": "0",
			"spell_slots": "0",
			"max_spell_slots": "0",
			"movement": "0",
			"pos_x": "0",
			"pos_y": "0",
		}
		if self.controller.runtime_source == "runtime_env":
			piece = runtime_map.get(slot_key)
			if piece is None:
				return default_values
			pos = getattr(piece, "position", None)
			px = int(getattr(pos, "x", 0)) if pos is not None else 0
			py = int(getattr(pos, "y", 0)) if pos is not None else 0
			weapon_raw = getattr(piece, "weapon", "自定义")
			weapon_id = self._safe_int(str(weapon_raw), 0)
			if weapon_id in (1, 2, 3, 4):
				weapon_label = self._weapon_id_to_weapon_label(weapon_id)
			else:
				weapon_label = self._normalize_weapon_label(str(weapon_raw)) or "自定义"
				weapon_id = self._weapon_label_to_weapon_id(weapon_label)

			armor_raw = getattr(piece, "armor", "无甲")
			armor_id = self._safe_int(str(armor_raw), 0)
			if armor_id in (1, 2, 3):
				armor_label = self._armor_id_to_armor_label(armor_id)
			else:
				armor_label = str(armor_raw or "无甲")
				armor_id = self._armor_label_to_armor_id(armor_label)

			profession_label = self._weapon_id_to_profession_display(weapon_id)
			return {
				"hp": str(int(getattr(piece, "health", 0))),
				"profession": profession_label,
				"weapon": weapon_label,
				"armor": armor_label,
				"strength": str(int(getattr(piece, "strength", 0))),
				"dexterity": str(int(getattr(piece, "dexterity", 0))),
				"intelligence": str(int(getattr(piece, "intelligence", 0))),
				"physical_resist": str(int(getattr(piece, "physical_resist", 0))),
				"magic_resist": str(int(getattr(piece, "magic_resist", 0))),
				"physical_damage": str(int(getattr(piece, "physical_damage", 0))),
				"magic_damage": str(int(getattr(piece, "magic_damage", 0))),
				"action_points": str(int(getattr(piece, "action_points", 0))),
				"max_action_points": str(int(getattr(piece, "max_action_points", 0))),
				"spell_slots": str(int(getattr(piece, "spell_slots", 0))),
				"max_spell_slots": str(int(getattr(piece, "max_spell_slots", 0))),
				"movement": str(float(getattr(piece, "movement", 0.0))),
				"pos_x": str(px),
				"pos_y": str(py),
			}

		soldier_id = mock_map.get(slot_key)
		if soldier_id is None:
			return default_values
		stats = self.mock_piece_stats_by_id.get(soldier_id, {})
		weapon_label = self._normalize_weapon_label(str(stats.get("weapon", "自定义"))) or "自定义"
		weapon_id = self._weapon_label_to_weapon_id(weapon_label)
		armor_label = str(stats.get("armor", "无甲")) or "无甲"
		profession_label = self._weapon_id_to_profession_display(weapon_id)
		return {
			"hp": str(int(self.mock_last_health_by_id.get(soldier_id, stats.get("health", 0)))),
			"profession": profession_label,
			"weapon": weapon_label,
			"armor": armor_label,
			"strength": str(int(stats.get("strength", 0))),
			"dexterity": str(int(stats.get("dexterity", 0))),
			"intelligence": str(int(stats.get("intelligence", 0))),
			"physical_resist": str(int(stats.get("physical_resist", 0))),
			"magic_resist": str(int(stats.get("magic_resist", 0))),
			"physical_damage": str(int(stats.get("physical_damage", 0))),
			"magic_damage": str(int(stats.get("magic_damage", 0))),
			"action_points": str(int(stats.get("action_points", 0))),
			"max_action_points": str(int(stats.get("max_action_points", 0))),
			"spell_slots": str(int(stats.get("spell_slots", 0))),
			"max_spell_slots": str(int(stats.get("max_spell_slots", 0))),
			"movement": str(float(stats.get("movement", 0.0))),
			"pos_x": str(int(self.mock_initial_positions.get(soldier_id, {}).get("x", 0))),
			"pos_y": str(int(self.mock_initial_positions.get(soldier_id, {}).get("y", 0))),
		}

	def _piece_attr_range(self, field: str) -> tuple[float, float]:
		ranges: dict[str, tuple[float, float]] = {
			"hp": (0, 200),
			"strength": (0, 30),
			"dexterity": (0, 30),
			"intelligence": (0, 30),
			"physical_resist": (0, 50),
			"magic_resist": (0, 50),
			"physical_damage": (0, 100),
			"magic_damage": (0, 100),
			"action_points": (0, 10),
			"max_action_points": (0, 10),
			"spell_slots": (0, 20),
			"max_spell_slots": (0, 20),
			"movement": (0, 40),
		}
		return ranges.get(field, (0, 9999))

	def _normalize_piece_value(
		self,
		*,
		slot_display_name: str,
		field: str,
		raw_value: str,
		allow_unset_hp: bool,
	) -> tuple[str, str | None]:
		value = str(raw_value).strip()
		field_labels = {
			"hp": "血量",
			"strength": "力量",
			"dexterity": "敏捷",
			"intelligence": "智力",
			"physical_resist": "物抗",
			"magic_resist": "法抗",
			"physical_damage": "物伤",
			"magic_damage": "法伤",
			"action_points": "行动位",
			"max_action_points": "行动位上限",
			"spell_slots": "法术位",
			"max_spell_slots": "法术位上限",
			"movement": "移动力",
			"pos_x": "X坐标",
			"pos_y": "Y坐标",
		}
		if field == "hp" and allow_unset_hp and value in ("", "-", "-1"):
			return "", None
		if field == "hp" and allow_unset_hp:
			# 初始化窗口：不自动修正到边界值，保留原始输入，让应用时可以标红并给出简要提示。
			_ = value
			return value, None

		if field in ("movement",):
			parsed = self._safe_float(value, -99999.0)
			lo, hi = self._piece_attr_range(field)
			clamped = max(lo, min(parsed, hi))
			out_str = f"{clamped:.1f}".rstrip("0").rstrip(".")
			if parsed != clamped:
				return out_str, f"{slot_display_name}的{field_labels.get(field, field)}合理范围是{int(lo)}-{int(hi)}"
			return out_str, None

		if field in ("pos_x", "pos_y"):
			parsed_i = self._safe_int(value, -99999)
			if self.controller.runtime_source == "runtime_env" and self.controller.environment is not None:
				board = getattr(self.controller.environment, "board", None)
				if board is not None:
					max_x = max(0, int(getattr(board, "width", 1)) - 1)
					max_y = max(0, int(getattr(board, "height", 1)) - 1)
				else:
					max_x, max_y = 19, 19
			else:
				max_x, max_y = 19, 19
			max_v = max_x if field == "pos_x" else max_y
			clamped_i = max(0, min(parsed_i, max_v))
			if parsed_i != clamped_i:
				return str(clamped_i), f"{slot_display_name}的{field_labels.get(field, field)}合理范围是0-{max_v}"
			return str(clamped_i), None

		parsed_i = self._safe_int(value, -99999)
		lo, hi = self._piece_attr_range(field)
		clamped_i = int(max(lo, min(parsed_i, hi)))
		if parsed_i != clamped_i:
			return str(clamped_i), f"{slot_display_name}的{field_labels.get(field, field)}合理范围是{int(lo)}-{int(hi)}"
		return str(clamped_i), None

	def _is_walkable_for_piece(self, x: int, y: int) -> bool:
		if self.controller.runtime_source == "runtime_env" and self.controller.environment is not None:
			board = getattr(self.controller.environment, "board", None)
			if board is None:
				return False
			width = int(getattr(board, "width", 0))
			height = int(getattr(board, "height", 0))
			if not (0 <= x < width and 0 <= y < height):
				return False
			height_map = getattr(board, "height_map", None)
			if height_map is None:
				return False
			try:
				if int(height_map[x][y]) == -1:
					return False
			except Exception:
				return False
			# 注：部分地图/实现可能会使用 state=0 表示“空地”，但仍可作为落点。
			# 这里对属性编辑放宽：只要不是禁止格(state=-1)且高度不为-1即可。
			cell = board.grid[x][y]
			return int(getattr(cell, "state", 0)) != -1

		game_data = self.controller.game_data
		if not isinstance(game_data, dict):
			return False
		board = game_data.get("map", {})
		rows = board.get("rows", []) if isinstance(board, dict) else []
		if not isinstance(rows, list) or not rows:
			return False
		if y < 0 or y >= len(rows):
			return False
		row = rows[y]
		if not isinstance(row, list) or x < 0 or x >= len(row):
			return False
		visual_rows = self._extract_mock_visual_rows()
		if y < 0 or y >= len(visual_rows):
			return False
		visual_row = visual_rows[y]
		if not isinstance(visual_row, list) or x < 0 or x >= len(visual_row):
			return False
		return int(visual_row[x]) != -1

	def _runtime_border_line(self) -> int:
		env = self.controller.environment
		if env is not None and getattr(env, "board", None) is not None:
			return int(getattr(env.board, "boarder", 0))
		return 10

	def _clamp_piece_position(self, x: int, y: int) -> tuple[int, int]:
		"""将坐标限制在当前地图范围内。"""
		width = 20
		height = 20
		if self.controller.runtime_source == "runtime_env" and self.controller.environment is not None:
			board = getattr(self.controller.environment, "board", None)
			if board is not None:
				width = int(getattr(board, "width", width))
				height = int(getattr(board, "height", height))
		else:
			game_data = self.controller.game_data
			if isinstance(game_data, dict):
				board = game_data.get("map", {})
				rows = board.get("rows", []) if isinstance(board, dict) else []
				if isinstance(rows, list) and rows:
					height = len(rows)
					first_row = rows[0]
					if isinstance(first_row, list) and first_row:
						width = len(first_row)

		cx = max(0, min(int(x), max(0, width - 1)))
		cy = max(0, min(int(y), max(0, height - 1)))
		return cx, cy

	def _show_attribute_apply_feedback(self, message: str) -> None:
		label = self.attribute_piece_apply_status_label
		if label is None:
			return
		label.configure(text=message, foreground="#059669")
		if self.attribute_piece_apply_status_job is not None:
			try:
				self.root.after_cancel(self.attribute_piece_apply_status_job)
			except Exception:
				pass
		self.attribute_piece_apply_status_job = self.root.after(2000, lambda: label.configure(text=""))

	def _safe_int(self, value: str, default: int = 0) -> int:
		try:
			return int(float(value))
		except Exception:
			return default

	def _safe_float(self, value: str, default: float = 0.0) -> float:
		try:
			return float(value)
		except Exception:
			return default

	def _apply_piece_attribute_changes(self) -> None:
		if not self.loaded:
			self.right_info_panel.append_content("\n[UI] 当前未加载对局，无法应用棋子属性")
			if not (self.attribute_settings_force_init_mode and self._is_runtime_selected_source()):
				return

		runtime_map = self._runtime_piece_slot_map()
		mock_map = self._mock_piece_slot_map()
		applied_count = 0
		warnings: list[str] = []
		active_slots_by_team: dict[int, list[str]] = {1: [], 2: []}
		planned_positions: dict[str, tuple[int, int]] = {}
		allow_unset_hp = bool(self.attribute_settings_force_init_mode and self._is_runtime_selected_source())
		self._clear_attribute_error_highlight()

		# 先做输入规范化（含范围夹紧）并回填到界面。
		self.attribute_internal_update = True
		try:
			for slot_key in self._piece_slot_keys():
				vars_dict = self.attribute_piece_vars.get(slot_key)
				if vars_dict is None:
					continue
				if not self.attribute_settings_force_init_mode and not self._is_attribute_slot_enabled(slot_key):
					continue
				slot_name = f"player{slot_key[1]}-{slot_key[-1]}"
				slot_hp_raw = str(vars_dict["hp"].get()).strip()
				if allow_unset_hp and self._is_profession_mode() and self._is_runtime_selected_source():
					strength = self._parse_talent_int(vars_dict.get("strength").get() if vars_dict.get("strength") else None)
					dexterity = self._parse_talent_int(vars_dict.get("dexterity").get() if vars_dict.get("dexterity") else None)
					intelligence = self._parse_talent_int(vars_dict.get("intelligence").get() if vars_dict.get("intelligence") else None)
					slot_unset = strength is None and dexterity is None and intelligence is None
				else:
					slot_unset = allow_unset_hp and slot_hp_raw in ("", "-", "-1")
				for field, var in vars_dict.items():
					if slot_unset and field != "hp":
						continue
					# 职业模式初始化：天赋/派生字段允许保持为“-”（未分配/未派生），不做整数夹紧。
					if (
						allow_unset_hp
						and self._is_profession_mode()
						and self._is_runtime_selected_source()
						and field not in ("profession", "weapon", "armor", "pos_x", "pos_y")
					):
						raw_norm = str(var.get()).strip()
						if raw_norm in ("", "-", "-1"):
							if var.get() != "-":
								var.set("-")
							continue
					if field in ("profession", "weapon", "armor"):
						normalized = str(var.get()).strip()
						if not normalized:
							if field == "armor":
								normalized = "无甲"
							else:
								normalized = "自定义"
						if var.get() != normalized:
							var.set(normalized)
						continue
					normalized, warn = self._normalize_piece_value(
						slot_display_name=slot_name,
						field=field,
						raw_value=var.get(),
						allow_unset_hp=allow_unset_hp,
					)
					if var.get() != normalized:
						var.set(normalized)
					if warn is not None:
						warnings.append(warn)

			# 额外约束：当前行动位/法术位不能超过其上限。
			for slot_key in self._piece_slot_keys():
				vars_dict = self.attribute_piece_vars.get(slot_key)
				if vars_dict is None:
					continue
				if not self.attribute_settings_force_init_mode and not self._is_attribute_slot_enabled(slot_key):
					continue
				slot_hp_raw = str(vars_dict["hp"].get()).strip()
				if allow_unset_hp and self._is_profession_mode() and self._is_runtime_selected_source():
					strength = self._parse_talent_int(vars_dict.get("strength").get() if vars_dict.get("strength") else None)
					dexterity = self._parse_talent_int(vars_dict.get("dexterity").get() if vars_dict.get("dexterity") else None)
					intelligence = self._parse_talent_int(vars_dict.get("intelligence").get() if vars_dict.get("intelligence") else None)
					slot_unset = strength is None and dexterity is None and intelligence is None
				else:
					slot_unset = allow_unset_hp and slot_hp_raw in ("", "-", "-1")
				if slot_unset:
					continue

				slot_name = f"player{slot_key[1]}-{slot_key[-1]}"
				action_max = self._safe_int(vars_dict["max_action_points"].get(), 0)
				action_cur = self._safe_int(vars_dict["action_points"].get(), 0)
				if action_cur > action_max:
					vars_dict["action_points"].set(str(action_max))
					warnings.append(f"{slot_name}的行动位不能超过行动位上限")

				spell_max = self._safe_int(vars_dict["max_spell_slots"].get(), 0)
				spell_cur = self._safe_int(vars_dict["spell_slots"].get(), 0)
				if spell_cur > spell_max:
					vars_dict["spell_slots"].set(str(spell_max))
					warnings.append(f"{slot_name}的法术位不能超过法术位上限")
		finally:
			self.attribute_internal_update = False

		# 构建“有效棋子”集合，并检查坐标合法性（不可重叠、不可走）。
		invalid_coordinate_slots: list[tuple[str, str]] = []
		position_to_slots: dict[str, list[str]] = {}
		use_talent_validity = bool(
			self._is_profession_mode() and self.attribute_settings_force_init_mode and self._is_runtime_selected_source()
		)
		talent_cap = self._get_talent_total_cap() if use_talent_validity else 0
		for slot_key in self._piece_slot_keys():
			vars_dict = self.attribute_piece_vars.get(slot_key)
			if vars_dict is None:
				continue
			if not self.attribute_settings_force_init_mode and not self._is_attribute_slot_enabled(slot_key):
				continue
			if not self.attribute_settings_force_init_mode:
				if self.controller.runtime_source == "runtime_env" and slot_key not in runtime_map:
					continue
				if self.controller.runtime_source != "runtime_env" and slot_key not in mock_map:
					continue
			team = int(slot_key[1])
			if use_talent_validity:
				strength = self._parse_talent_int(vars_dict.get("strength").get() if vars_dict.get("strength") else None)
				dexterity = self._parse_talent_int(vars_dict.get("dexterity").get() if vars_dict.get("dexterity") else None)
				intelligence = self._parse_talent_int(vars_dict.get("intelligence").get() if vars_dict.get("intelligence") else None)
				if strength is None or dexterity is None or intelligence is None:
					continue
				if (strength + dexterity + intelligence) > int(talent_cap):
					self._mark_attribute_field_error(slot_key, "strength")
					self._mark_attribute_field_error(slot_key, "dexterity")
					self._mark_attribute_field_error(slot_key, "intelligence")
					self._show_attribute_warning_feedback(f"天赋总和不能超过 {int(talent_cap)}")
					return
			else:
				hp_raw = str(vars_dict["hp"].get()).strip()
				if hp_raw in ("", "-", "-1"):
					continue
				hp_value = self._safe_int(hp_raw, -1)
				if hp_value < 0:
					slot_name = f"player{slot_key[1]}-{slot_key[-1]}"
					self._mark_attribute_field_error(slot_key, "hp")
					self._show_attribute_warning_feedback(f"{slot_name} 的血量不能小于 0")
					return
				if hp_value == 0:
					continue
				if (
					self.attribute_settings_force_init_mode
					and self._is_runtime_selected_source()
					and (not self._is_profession_mode())
					and self._normalize_selected_source_value(self.selected_source) == "runtime_custom"
				):
					strength_raw = str(vars_dict.get("strength").get()).strip() if vars_dict.get("strength") is not None else "10"
					strength = self._safe_int(strength_raw, 10)
					max_hp = int(200)
					if int(hp_value) > int(max_hp):
						slot_name = f"player{slot_key[1]}-{slot_key[-1]}"
						self._mark_attribute_field_error(slot_key, "hp")
						self._show_attribute_warning_feedback(f"{slot_name} 的血量不能超过上限 ({max_hp})")
						return

			x = self._safe_int(vars_dict["pos_x"].get(), -1)
			y = self._safe_int(vars_dict["pos_y"].get(), -1)
			if not self._is_walkable_for_piece(x, y):
				invalid_coordinate_slots.append((slot_key, "walkable"))
				continue

			pos_key = f"{x},{y}"
			position_to_slots.setdefault(pos_key, []).append(slot_key)
			planned_positions[pos_key] = (x, y)
			active_slots_by_team[team].append(slot_key)

		for pos_key, slots in position_to_slots.items():
			if len(slots) <= 1:
				continue
			sorted_slots = sorted(slots, key=lambda s: int(self.attribute_piece_last_edit_tick.get(s, 0)))
			for duplicate_slot in sorted_slots[1:]:
				invalid_coordinate_slots.append((duplicate_slot, "duplicate"))

		if invalid_coordinate_slots:
			for slot_key, _reason in invalid_coordinate_slots:
				self._mark_attribute_field_error(slot_key, "pos_x")
				self._mark_attribute_field_error(slot_key, "pos_y")
			self._show_attribute_warning_feedback("存在非法坐标（重合/越界/不可走），请修改红色坐标")
			return

		team1_count = len(active_slots_by_team[1])
		team2_count = len(active_slots_by_team[2])

		# 后端强制初始化：必须双方至少各有一个有效棋子。
		if self.attribute_settings_force_init_mode and self._is_runtime_selected_source():
			if team1_count == 0 and team2_count == 0:
				if use_talent_validity:
					for field in ("strength", "dexterity", "intelligence"):
						self._mark_attribute_field_error("p1_1", field)
						self._mark_attribute_field_error("p2_1", field)
					self._show_attribute_warning_feedback(
						f"当前场上未有有效棋子！请为双方至少各一个棋子分配天赋（力量/敏捷/智力，且总和≤{int(talent_cap)}）"
					)
					return
				for sk in ("p1_1", "p2_1"):
					vars_dict = self.attribute_piece_vars.get(sk) or {}
					hp_raw = str(vars_dict.get("hp").get()).strip() if vars_dict.get("hp") is not None else ""
					if hp_raw in ("", "-", "-1"):
						self._mark_hp_placeholder_error(sk)
					else:
						self._mark_attribute_field_error(sk, "hp")
				self._show_attribute_warning_feedback("当前场上未有有效棋子！请设置双方至少各一个棋子的血量")
				return

		# 职业模式：有效棋子必须选择非“自定义”职业。
		if self._is_profession_mode():
			invalid_slots: list[str] = []
			for team_id in (1, 2):
				for slot_key in active_slots_by_team[team_id]:
					vars_dict = self.attribute_piece_vars.get(slot_key)
					if vars_dict is None:
						continue
					prof_var = vars_dict.get("profession")
					profession = str(prof_var.get()).strip() if prof_var is not None else ""
					if profession in ("", "自定义"):
						invalid_slots.append(slot_key)
			if invalid_slots:
				for slot_key in invalid_slots:
					self._mark_attribute_field_error(slot_key, "profession")
				self._show_attribute_warning_feedback("职业模式：有效棋子必须选择武器以确定职业，职业不能为自定义")
				return
			if team1_count == 0:
				if use_talent_validity:
					for field in ("strength", "dexterity", "intelligence"):
						self._mark_attribute_field_error("p1_1", field)
					self._show_attribute_warning_feedback("player1阵营未设置有效棋子，请先分配天赋（力量/敏捷/智力）")
					return
				self._mark_attribute_field_error("p1_1", "hp")
				self._show_attribute_warning_feedback("player1阵营未设置有效棋子，请先设置血量")
				return
			if team2_count == 0:
				if use_talent_validity:
					for field in ("strength", "dexterity", "intelligence"):
						self._mark_attribute_field_error("p2_1", field)
					self._show_attribute_warning_feedback("player2阵营未设置有效棋子，请先分配天赋（力量/敏捷/智力）")
					return
				self._mark_attribute_field_error("p2_1", "hp")
				self._show_attribute_warning_feedback("player2阵营未设置有效棋子，请先设置血量")
				return

		for slot_key in self._piece_slot_keys():
			vars_dict = self.attribute_piece_vars.get(slot_key)
			if vars_dict is None:
				continue

			if self.attribute_settings_force_init_mode and self._is_runtime_selected_source():
				cfg = self.runtime_piece_init_config.setdefault(slot_key, {})
				for field, var in vars_dict.items():
					cfg[field] = var.get()
				applied_count += 1
				continue

			if self.controller.runtime_source == "runtime_env":
				piece = runtime_map.get(slot_key)
				if piece is None:
					continue
				px, py = self._clamp_piece_position(
					self._safe_int(vars_dict["pos_x"].get(), 0),
					self._safe_int(vars_dict["pos_y"].get(), 0),
				)
				piece.health = max(0, self._safe_int(vars_dict["hp"].get(), int(getattr(piece, "health", 0))))
				piece.is_alive = bool(int(getattr(piece, "health", 0)) > 0)
				piece.strength = self._safe_int(vars_dict["strength"].get(), int(getattr(piece, "strength", 0)))
				piece.dexterity = self._safe_int(vars_dict["dexterity"].get(), int(getattr(piece, "dexterity", 0)))
				piece.intelligence = self._safe_int(vars_dict["intelligence"].get(), int(getattr(piece, "intelligence", 0)))
				piece.physical_resist = self._safe_int(vars_dict["physical_resist"].get(), int(getattr(piece, "physical_resist", 0)))
				piece.magic_resist = self._safe_int(vars_dict["magic_resist"].get(), int(getattr(piece, "magic_resist", 0)))
				piece.physical_damage = self._safe_int(vars_dict["physical_damage"].get(), int(getattr(piece, "physical_damage", 0)))
				piece.magic_damage = self._safe_int(vars_dict["magic_damage"].get(), int(getattr(piece, "magic_damage", 0)))
				piece.max_action_points = self._safe_int(
					vars_dict["max_action_points"].get(), int(getattr(piece, "max_action_points", 0))
				)
				piece.action_points = min(
					self._safe_int(vars_dict["action_points"].get(), int(getattr(piece, "action_points", 0))),
					int(piece.max_action_points),
				)
				piece.max_spell_slots = self._safe_int(
					vars_dict["max_spell_slots"].get(), int(getattr(piece, "max_spell_slots", 0))
				)
				piece.spell_slots = min(
					self._safe_int(vars_dict["spell_slots"].get(), int(getattr(piece, "spell_slots", 0))),
					int(piece.max_spell_slots),
				)
				piece.movement = self._safe_float(vars_dict["movement"].get(), float(getattr(piece, "movement", 0.0)))
				if self._is_runtime_selected_source():
					weapon_label = (
						self._normalize_weapon_label(str(vars_dict.get("weapon").get()).strip())
						if vars_dict.get("weapon")
						else "自定义"
					)
					armor_label = str(vars_dict.get("armor").get()).strip() if vars_dict.get("armor") else "无甲"
					weapon_id = self._weapon_label_to_weapon_id(weapon_label)
					armor_id = self._armor_label_to_armor_id(armor_label)
					piece.type = self._weapon_id_to_piece_type(weapon_id)
					setattr(piece, "weapon", int(weapon_id))
					setattr(piece, "armor", int(armor_id))
				if getattr(piece, "position", None) is not None:
					piece.position.x = px
					piece.position.y = py
				else:
					piece.position = Point(px, py)
				applied_count += 1
				continue

			soldier_id = mock_map.get(slot_key)
			if soldier_id is None:
				continue
			stats = self.mock_piece_stats_by_id.setdefault(soldier_id, {})
			if self._is_runtime_selected_source():
				stats["profession"] = str(vars_dict.get("profession").get()).strip() if vars_dict.get("profession") else "自定义"
				stats["weapon"] = str(vars_dict.get("weapon").get()).strip() if vars_dict.get("weapon") else "自定义"
				stats["armor"] = str(vars_dict.get("armor").get()).strip() if vars_dict.get("armor") else "无甲"
			px, py = self._clamp_piece_position(
				self._safe_int(vars_dict["pos_x"].get(), int(self.mock_initial_positions.get(soldier_id, {}).get("x", 0))),
				self._safe_int(vars_dict["pos_y"].get(), int(self.mock_initial_positions.get(soldier_id, {}).get("y", 0))),
			)
			self.mock_last_health_by_id[soldier_id] = self._safe_int(
				vars_dict["hp"].get(), int(self.mock_last_health_by_id.get(soldier_id, 0))
			)
			stats["strength"] = self._safe_int(vars_dict["strength"].get(), int(stats.get("strength", 0)))
			stats["dexterity"] = self._safe_int(vars_dict["dexterity"].get(), int(stats.get("dexterity", 0)))
			stats["intelligence"] = self._safe_int(vars_dict["intelligence"].get(), int(stats.get("intelligence", 0)))
			stats["physical_resist"] = self._safe_int(vars_dict["physical_resist"].get(), int(stats.get("physical_resist", 0)))
			stats["magic_resist"] = self._safe_int(vars_dict["magic_resist"].get(), int(stats.get("magic_resist", 0)))
			stats["physical_damage"] = self._safe_int(vars_dict["physical_damage"].get(), int(stats.get("physical_damage", 0)))
			stats["magic_damage"] = self._safe_int(vars_dict["magic_damage"].get(), int(stats.get("magic_damage", 0)))
			stats["max_action_points"] = self._safe_int(
				vars_dict["max_action_points"].get(), int(stats.get("max_action_points", 0))
			)
			stats["action_points"] = min(
				self._safe_int(vars_dict["action_points"].get(), int(stats.get("action_points", 0))),
				int(stats["max_action_points"]),
			)
			stats["max_spell_slots"] = self._safe_int(
				vars_dict["max_spell_slots"].get(), int(stats.get("max_spell_slots", 0))
			)
			stats["spell_slots"] = min(
				self._safe_int(vars_dict["spell_slots"].get(), int(stats.get("spell_slots", 0))),
				int(stats["max_spell_slots"]),
			)
			stats["movement"] = self._safe_float(vars_dict["movement"].get(), float(stats.get("movement", 0.0)))
			if soldier_id in self.mock_initial_positions:
				self.mock_initial_positions[soldier_id]["x"] = px
				self.mock_initial_positions[soldier_id]["y"] = py
			self.mock_last_positions_by_id[soldier_id] = (px, py)
			applied_count += 1

		if warnings:
			self._show_attribute_warning_feedback(f"{warnings[0]}（自动修正为最近边界值）")

		if self.attribute_settings_force_init_mode and self._is_runtime_selected_source():
			self.runtime_init_config_ready = True
			self.right_info_panel.append_content("\n[UI] 后端模式初始化属性已确认")
			self._show_attribute_apply_feedback("应用成功")
			if self.attribute_settings_window is not None and self.attribute_settings_window.winfo_exists():
				win = self.attribute_settings_window
				self.attribute_settings_window = None
				self.attribute_settings_content_frame = None
				self.attribute_settings_force_init_mode = False
				win.destroy()
			return

		self._refresh_piece_cards()
		self._refresh_board_view()
		# 手动应用属性可能直接导致某一方全灭（例如 0HP vs 50HP），这里主动检查胜负。
		if self.controller.runtime_source == "runtime_env" and self.controller.environment is not None:
			self._check_and_announce_runtime_game_over(self.controller.environment, show_dialog=True)
		self.right_info_panel.append_content(f"\n[UI] 棋子属性已应用（本局临时生效），影响棋子数: {applied_count}")
		self._show_attribute_apply_feedback("应用成功")

	def _build_attribute_piece_page(self, content: ttk.LabelFrame) -> None:
		"""构建棋子属性页：固定 6 槽位，矩阵化布局并支持纵向滚动。"""
		wrapper = ttk.Frame(content)
		wrapper.grid(row=0, column=0, sticky="nsew")
		wrapper.columnconfigure(0, weight=1)
		wrapper.rowconfigure(1, weight=1)

		ttk.Label(wrapper, text="棋子属性", font=("Microsoft YaHei UI", 12, "bold")).grid(
			row=0, column=0, sticky="w", pady=(0, 8)
		)

		scroll_host = ttk.Frame(wrapper)
		scroll_host.grid(row=1, column=0, sticky="nsew")
		scroll_host.columnconfigure(0, weight=1)
		scroll_host.rowconfigure(0, weight=1)

		canvas = tk.Canvas(scroll_host, highlightthickness=0, borderwidth=0)
		v_scroll = ttk.Scrollbar(scroll_host, orient="vertical", command=canvas.yview)
		canvas.configure(yscrollcommand=v_scroll.set)
		canvas.grid(row=0, column=0, sticky="nsew")
		v_scroll.grid(row=0, column=1, sticky="ns")

		scroll_content = ttk.Frame(canvas)
		canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")

		def _sync_scroll_region(_event: Any = None) -> None:
			canvas.configure(scrollregion=canvas.bbox("all"))

		def _fit_scroll_content_width(event: Any) -> None:
			canvas.itemconfigure(canvas_window, width=int(event.width))

		scroll_content.bind("<Configure>", _sync_scroll_region)
		canvas.bind("<Configure>", _fit_scroll_content_width)

		def _on_mousewheel(event: Any) -> None:
			if int(event.delta) == 0:
				return
			canvas.yview_scroll(-int(event.delta / 120), "units")

		canvas.bind_all("<MouseWheel>", _on_mousewheel)
		canvas.bind("<Destroy>", lambda _e: canvas.unbind_all("<MouseWheel>"))

		runtime_map = self._runtime_piece_slot_map()
		mock_map = self._mock_piece_slot_map()
		slot_keys = self._piece_slot_keys()

		self.attribute_piece_vars = {}
		self.attribute_piece_entries = {}
		self.attribute_piece_last_edit_tick = {}
		self.attribute_piece_hp_hint_widgets = {}

		enabled_map: dict[str, bool] = {}
		for slot_key in slot_keys:
			if self.attribute_settings_force_init_mode and self._is_runtime_selected_source():
				enabled_map[slot_key] = True
			else:
				enabled_map[slot_key] = slot_key in runtime_map if self.controller.runtime_source == "runtime_env" else slot_key in mock_map
			self.attribute_piece_vars[slot_key] = {}
			self.attribute_piece_entries[slot_key] = {}
			self.attribute_piece_last_edit_tick[slot_key] = 0

		weapon_values = ["自定义", "长剑", "短剑", "弓", "法杖"]
		armor_values = ["无甲", "轻甲", "中甲", "重甲"]
		if self._is_profession_mode():
			weapon_values = ["长剑", "短剑", "弓", "法杖"]
			armor_values = ["轻甲", "中甲", "重甲"]
		combo_values: dict[str, list[str]] = {
			"weapon": weapon_values,
			"armor": armor_values,
		}

		field_groups: list[tuple[str, list[tuple[str, str]]]] = [
			(
				"职业与装备",
				[
					("profession", "职业"),
					("weapon", "武器"),
					("armor", "护甲"),
				],
			),
			(
				"天赋属性",
				[
					("strength", "力量"),
					("dexterity", "敏捷"),
					("intelligence", "智力"),
				],
			),
			(
				"基础与战斗属性",
				[
					("hp", "血量"),
					("physical_resist", "物抗"),
					("magic_resist", "法抗"),
					("physical_damage", "物伤"),
					("magic_damage", "法伤"),
					("action_points", "行动位"),
					("max_action_points", "行动位上限"),
					("spell_slots", "法术位"),
					("max_spell_slots", "法术位上限"),
					("movement", "移动力"),
					("pos_x", "X坐标"),
					("pos_y", "Y坐标"),
				],
			),
		]
		show_profession_section = self._normalize_selected_source_value(self.selected_source) in (
			"runtime_custom",
			"runtime_profession",
		)
		if not show_profession_section:
			field_groups = field_groups[1:]

		derived_fields: set[str] = {
			"hp",
			"physical_resist",
			"magic_resist",
			"physical_damage",
			"magic_damage",
			"action_points",
			"max_action_points",
			"spell_slots",
			"max_spell_slots",
			"movement",
		}
		lock_all_stats = self._is_profession_mode() and not self.attribute_settings_force_init_mode

		def render_matrix(
			parent: ttk.Frame,
			fields: list[tuple[str, str]],
			*,
			start_row: int,
			title: str | None = None,
			highlight: str | None = None,
		) -> int:
			row_idx = start_row
			if title is not None:
				title_fg = highlight if highlight is not None else "#111827"
				ttk.Label(parent, text=title, font=("Microsoft YaHei UI", 10, "bold"), foreground=title_fg).grid(
					row=row_idx, column=0, columnspan=len(slot_keys) + 1, sticky="w", pady=(0, 6)
				)
				row_idx += 1

			table = ttk.Frame(parent)
			table.grid(row=row_idx, column=0, sticky="ew")
			table.columnconfigure(0, weight=0)
			for col_idx in range(1, len(slot_keys) + 1):
				table.columnconfigure(col_idx, weight=1)

			ttk.Label(table, text="属性\\棋子", font=("Microsoft YaHei UI", 9, "bold")).grid(
				row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
			)
			for col_idx, slot_key in enumerate(slot_keys, start=1):
				team = int(slot_key[1])
				num = int(slot_key[-1])
				ttk.Label(table, text=f"P{team}-{num}", font=("Microsoft YaHei UI", 9, "bold")).grid(
					row=0, column=col_idx, sticky="w", padx=(0, 6), pady=(0, 6)
				)

			for field_row, (field, field_label) in enumerate(fields, start=1):
				ttk.Label(table, text=field_label).grid(row=field_row, column=0, sticky="w", padx=(0, 8), pady=3)
				for col_idx, slot_key in enumerate(slot_keys, start=1):
					values = self._get_piece_row_values(slot_key, runtime_map, mock_map)
					var = tk.StringVar(value=values[field])
					var.trace_add("write", lambda *_args, sk=slot_key, fd=field: self._on_attribute_var_changed(sk, fd))
					state = "normal" if enabled_map.get(slot_key, False) else "disabled"
					if lock_all_stats and field not in ("pos_x", "pos_y"):
						state = "disabled"
					widget: Any
					if field == "profession":
						entry_state = "readonly" if state == "normal" else "disabled"
						entry = tk.Entry(
							table,
							textvariable=var,
							width=9,
							state=entry_state,
							fg="#111111",
							disabledforeground="#9ca3af",
							readonlybackground="#f3f4f6",
						)
						entry.grid(row=field_row, column=col_idx, sticky="ew", padx=(0, 6), pady=3)
						widget = entry
					elif field in ("weapon", "armor"):
						combo_state = "readonly" if state == "normal" else "disabled"
						combo = ttk.Combobox(
							table,
							textvariable=var,
							values=combo_values.get(field, []),
							state=combo_state,
							width=9,
						)
						combo.grid(row=field_row, column=col_idx, sticky="ew", padx=(0, 6), pady=3)
						widget = combo
					else:
						if self._is_profession_mode() and field in derived_fields:
							state = "disabled"
						if (
							field == "hp"
							and self.attribute_settings_force_init_mode
							and self._normalize_selected_source_value(self.selected_source) == "runtime_custom"
							and not self._is_profession_mode()
						):
							cell = ttk.Frame(table)
							cell.grid(row=field_row, column=col_idx, sticky="ew", padx=(0, 6), pady=3)
							cell.columnconfigure(0, weight=1)
							entry = tk.Entry(
								cell,
								textvariable=var,
								width=6,
								state=state,
								fg="#111111",
								disabledforeground="#9ca3af",
							)
							entry.grid(row=0, column=0, sticky="ew")

							# placeholder：覆盖在 Entry 内部，但不写入 Entry 内容。
							try:
								entry_bg = str(entry.cget("background"))
							except Exception:
								entry_bg = "#ffffff"
							overlay = tk.Frame(cell, bg=entry_bg, highlightthickness=0, bd=0)
							dash_label = tk.Label(overlay, text="-", fg="#111111", bg=entry_bg)
							hint_label = tk.Label(overlay, text="", fg="#9ca3af", bg=entry_bg)
							dash_label.pack(side="left")
							hint_label.pack(side="left")
							# 默认先隐藏，交给 _refresh_custom_init_hp_hint 控制显示。
							overlay.place_forget()
							# 点击 placeholder 时也能聚焦输入框。
							overlay.bind("<Button-1>", lambda _e, ent=entry: ent.focus_set())
							dash_label.bind("<Button-1>", lambda _e, ent=entry: ent.focus_set())
							hint_label.bind("<Button-1>", lambda _e, ent=entry: ent.focus_set())
							self.attribute_piece_hp_hint_widgets[slot_key] = (entry, overlay, dash_label, hint_label)
							widget = entry
						else:
							entry = tk.Entry(
								table,
								textvariable=var,
								width=9,
								state=state,
								fg="#111111",
								disabledforeground="#9ca3af",
							)
							entry.grid(row=field_row, column=col_idx, sticky="ew", padx=(0, 6), pady=3)
							widget = entry
					self.attribute_piece_vars[slot_key][field] = var
					self.attribute_piece_entries[slot_key][field] = widget

			return row_idx + 1

		row_cursor = 0
		for group_title, group_fields in field_groups:
			display_title = group_title
			highlight = None
			row_cursor = render_matrix(
				scroll_content,
				group_fields,
				start_row=row_cursor,
				title=display_title,
				highlight=highlight,
			)
			row_cursor += 1
		for slot_key in slot_keys:
			if self._is_profession_mode():
				self._update_profession_display_and_presets(slot_key)
			else:
				# 注意：初始化窗口的 custom 默认战斗数值是硬编码写入 cfg 的，不应再被装备预设覆盖。
				self._update_custom_mode_equipment_presets(slot_key, update_stats=False)
			if (
				self.attribute_settings_force_init_mode
				and self._normalize_selected_source_value(self.selected_source) == "runtime_custom"
				and not self._is_profession_mode()
			):
				self._refresh_custom_init_hp_hint(slot_key)

		if self.attribute_settings_force_init_mode and self._is_runtime_selected_source():
			cap = self._get_talent_total_cap() if self._is_profession_mode() else None
			ttk.Label(
				scroll_content,
				text=(
					f"后端模式初始化：请至少为双方各配置一个有效棋子（力量/敏捷/智力均填写且总和≤{cap}）。"
					if self._is_profession_mode()
					else "后端模式初始化：请至少为双方各配置一个有效棋子（血量非“-”且 > 0）。"
				),
				foreground="#7c3aed",
			).grid(row=row_cursor + 1, column=0, sticky="w", pady=(10, 0))
		elif not self.loaded:
			ttk.Label(
				scroll_content,
				text="当前未加载对局，6个棋子槽位均不可编辑。",
				foreground="#6b7280",
			).grid(row=row_cursor + 1, column=0, sticky="w", pady=(10, 0))
		else:
			ttk.Label(
				scroll_content,
				text="注：仅当前开局存在的棋子可编辑，未上场棋子槽位会禁用。",
				foreground="#6b7280",
			).grid(row=row_cursor + 1, column=0, sticky="w", pady=(10, 0))

		button_row = ttk.Frame(wrapper)
		button_row.grid(row=2, column=0, sticky="e", pady=(10, 0))
		self.attribute_piece_apply_status_label = ttk.Label(button_row, text="", foreground="#059669")
		self.attribute_piece_apply_status_label.pack(side="right", padx=(0, 8))
		if self.attribute_settings_force_init_mode and self._normalize_selected_source_value(self.selected_source) in (
			"runtime_custom",
			"runtime_profession",
		):
			ttk.Button(button_row, text="一键开始", command=self._one_click_fill_custom_init).pack(
				side="right", padx=(0, 8)
			)
		ttk.Button(button_row, text="应用", command=self._apply_piece_attribute_changes).pack(side="right")

		self.attribute_piece_warning_label = ttk.Label(wrapper, text="", foreground="#b45309")
		self.attribute_piece_warning_label.grid(row=3, column=0, sticky="w", pady=(8, 0))

	def _on_click_start(self) -> None:
		if not self.loaded:
			self.right_info_panel.append_content("\n[UI] 尚未加载数据，请先点击“模式选择”")
			return
		if self.running:
			self.right_info_panel.append_content("\n[UI] 已在运行中")
			return
		self.running = True
		self.right_info_panel.append_content("\n[UI] 开始运行")
		self._update_replay_play_pause_button_text()
		self._event_loop_tick()

	def _on_click_pause(self) -> None:
		self.running = False
		if self.loop_job is not None:
			self.root.after_cancel(self.loop_job)
			self.loop_job = None
		self._update_replay_play_pause_button_text()
		self.right_info_panel.append_content("\n[UI] 已暂停")

	def _on_click_step(self) -> None:
		if not self.loaded:
			self.right_info_panel.append_content("\n[UI] 尚未加载数据，请先点击“模式选择”")
			return
		try:
			runtime_before_states = self._snapshot_runtime_piece_states() if self.controller.runtime_source == "runtime_env" else None
			ok = self.controller.run_round()
			self._update_cards_from_env()
			self._refresh_piece_cards()
			self._refresh_board_view()
			self._append_round_details_after_step(runtime_before_states=runtime_before_states)
			self._sync_replay_round_var()
			self.right_info_panel.append_content(f"\n[UI] 单步执行完成, continue={ok}")
		except Exception as e:
			self.right_info_panel.append_content(f"\n[UI] 单步执行失败: {e}")

	def _on_click_reset(self) -> None:
		self._close_replay_mode_ui()
		self._on_click_pause()
		try:
			if self.controller.runtime_source == "runtime_env":
				self.controller.reset_environment()
			self.loaded = False
			self.runtime_card_slots = []
			self.mock_card_slots = []
			self.mock_initial_positions = {}
			self.mock_piece_stats_by_id = {}
			self.mock_last_health_by_id = {}
			self.mock_last_positions_by_id = {}
			self.mock_piece_number_by_id = {}
			self.runtime_piece_slot_binding = {}
			self.runtime_trap_effects = []
			# 重置行动选择状态，避免重开后棋盘仍残留目标高亮/施法点。
			self.action_ui_mode.set("move")
			self.action_move_x_var.set("")
			self.action_move_y_var.set("")
			self.action_spell_type_var.set("")
			self.action_spell_target_var.set("")
			self.action_spell_point_x_var.set("")
			self.action_spell_point_y_var.set("")
			self.action_spell_option_map = {}
			self.action_spell_target_option_map = {}
			self.action_panel_status_label = None
			self.game_over_message_shown = False
			self.left_board_panel.reset_board_state()
			self._refresh_piece_cards()
			choice = self._show_source_selection_dialog("重置后：选择数据源")
			if choice is not None:
				self.selected_source = choice
			if self.selected_source == "mock":
				selected = self._show_mock_dataset_dialog("重置后：选择 mock 数据集")
				if selected is not None:
					self.selected_mock_dataset = selected
			self.right_info_panel.append_content("\n[UI] 重置完成，正在按选择加载数据")
			# 这里已完成 source/dataset 选择，直接加载，避免再次弹出“模式选择”弹窗。
			self._load_data_with_selected_source()
		except Exception as e:
			self.right_info_panel.append_content(f"\n[UI] 重置失败: {e}")

	def _on_event_game_loaded(self, event) -> None:
		self.runtime_trap_effects = []
		self.game_over_message_shown = False
		self.right_info_panel.append_content(
			f"\n[EVENT] GAME_LOADED source={event.payload.get('source')} mode={event.payload.get('mode')}"
		)

	def _on_event_round_started(self, event) -> None:
		self.right_info_panel.append_content(
			f"\n[EVENT] ROUND_STARTED round={event.payload.get('round_number')} source={event.payload.get('source')}"
		)

	def _on_event_round_finished(self, event) -> None:
		self.right_info_panel.append_content(
			f"\n[EVENT] ROUND_FINISHED round={event.payload.get('round_number')} game_over={event.payload.get('is_game_over')}"
		)

	def _on_event_game_over(self, _event) -> None:
		if bool(getattr(self, "game_over_message_shown", False)):
			return
		env = self.controller.environment
		winner = "未知"
		if env is not None:
			p1_alive = any(bool(getattr(p, "is_alive", False)) for p in self._coerce_piece_list(getattr(getattr(env, "player1", None), "pieces", [])))
			p2_alive = any(bool(getattr(p, "is_alive", False)) for p in self._coerce_piece_list(getattr(getattr(env, "player2", None), "pieces", [])))
			winner = "玩家1" if p1_alive else ("玩家2" if p2_alive else "无人")
		self.game_over_message_shown = True
		self.right_info_panel.append_content(f"\nGAME_OVER，胜者：{winner}")

	def _on_click_initialize(self) -> None:
		"""退出测试。
		
		关闭应用程序，结束当前测试会话。
		后续可选择添加：
		- 确认对话框（询问用户是否要保存数据）
		- 清理资源（关闭后端连接、释放线程等）
		"""
		self.right_info_panel.append_content("\n[UI] 退出测试...")
		self.root.quit()

	def _on_click_exit(self) -> None:
		"""'退出测试'按钮的回调。"""
		self._on_click_initialize()

	def _on_right_composite_panel_initialize(self) -> None:
		"""右侧复合展示区的初始化回调。
		
		该区域目前用于显示 logo 和可变内容。
		此方法为占位实现，后续可根据需求扩展。
		"""
		self.right_info_panel.append_content("\n[UI] 复合展示区已初始化")


def launch() -> None:
	"""单独提供启动函数，便于 main.py 调用。"""
	root = tk.Tk()
	MainUI(root)
	root.mainloop()


if __name__ == "__main__":
	launch()