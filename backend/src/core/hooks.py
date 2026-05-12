from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


Hook = Callable[["BattleContext"], None]


@dataclass
class BattleContext:
    game: Any
    phase: str
    attacker: Any = None
    defender: Any = None
    move: Any = None
    is_player_attacking: bool = False
    
    # Calculation overrides/results
    base_power: int = 0
    accuracy: int | bool = 100
    actual_damage: int = 0
    substitute_damage: int = 0
    
    # State flags
    status_message: str | None = None
    hit_count: int = 1
    is_critical: bool = False
    effectiveness: float = 1.0
    
    events: List[Dict[str, Any]] = field(default_factory=list)
    flags: Dict[str, Any] = field(default_factory=dict)


class HookRegistry:
    PHASES = [
        "beforeTurn",
        "switchIn",
        "beforeMove",
        "modifyMove",
        "tryHit",
        "accuracy",
        "basePower",
        "damage",
        "onHit",
        "secondary",
        "afterMove",
        "forceSwitch",
        "residual",
        "formeChange",
        "faint",
        "endTurn",
    ]

    def __init__(self):
        self._hooks: Dict[str, List[Hook]] = {phase: [] for phase in self.PHASES}

    def register(self, phase: str, hook: Hook) -> None:
        if phase not in self._hooks:
            raise ValueError(f"Unknown battle hook phase: {phase}")
        self._hooks[phase].append(hook)

    def run(self, phase: str, context: BattleContext) -> BattleContext:
        context.phase = phase
        for hook in self._hooks.get(phase, []):
            hook(context)
        return context
