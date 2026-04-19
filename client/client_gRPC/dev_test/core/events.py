from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import time


class EventType(str, Enum):
	LOOP_STARTED = "loop_started"
	LOOP_STOPPED = "loop_stopped"
	GAME_LOADED = "game_loaded"
	ROUND_STARTED = "round_started"
	ROUND_FINISHED = "round_finished"
	GAME_OVER = "game_over"
	ACTION_SUBMITTED = "action_submitted"
	ERROR = "error"


@dataclass
class GameEvent:
	event_type: EventType
	payload: Dict[str, Any] = field(default_factory=dict)
	timestamp: float = field(default_factory=time.time)


EventHandler = Callable[[GameEvent], None]


class EventBus:
	"""极简事件总线：用于解耦 Controller、UI 和调试输出。"""

	def __init__(self):
		self._handlers: Dict[EventType, List[EventHandler]] = {}
		self._history: List[GameEvent] = []

	def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
		self._handlers.setdefault(event_type, []).append(handler)

	def publish(self, event_type: EventType, payload: Optional[Dict[str, Any]] = None) -> None:
		event = GameEvent(event_type=event_type, payload=payload or {})
		self._history.append(event)
		for handler in self._handlers.get(event_type, []):
			handler(event)

	def last_events(self, limit: int = 20) -> List[GameEvent]:
		if limit <= 0:
			return []
		return self._history[-limit:]


class BasicEventLoop:
	"""基础事件循环壳：控制步进执行和停止信号。"""

	def __init__(self, bus: EventBus):
		self.bus = bus
		self.running = False

	def run_steps(self, step_handler: Callable[[], bool], max_steps: Optional[int] = None) -> int:
		self.running = True
		executed = 0
		self.bus.publish(EventType.LOOP_STARTED, {"max_steps": max_steps})
		try:
			while self.running:
				should_continue = step_handler()
				if not should_continue:
					break
				executed += 1
				if max_steps is not None and executed >= max_steps:
					break
		finally:
			self.running = False
			self.bus.publish(EventType.LOOP_STOPPED, {"executed_steps": executed})
		return executed

	def stop(self) -> None:
		self.running = False