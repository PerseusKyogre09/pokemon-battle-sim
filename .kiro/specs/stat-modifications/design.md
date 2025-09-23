# Design Document

## Overview

The stat modifications system will implement Pokemon-style stat stages that temporarily modify a Pokemon's battle stats during combat. Each stat (Attack, Defense, Special Attack, Special Defense, Speed, Accuracy, Evasion) can be modified by up to 6 stages in either direction (-6 to +6), with each stage representing a specific multiplier applied to the base stat value.

This system integrates with the existing Pokemon class's stat stage tracking (`stat_stages` dictionary) and the move system's boost parsing capabilities, extending the current battle mechanics to support strategic stat manipulation through moves like Swords Dance (+2 Attack) and Leer (-1 Defense).

## Architecture

### Core Components

1. **Stat Stage Management** - Enhanced Pokemon class methods for applying and managing stat stage changes
2. **Stat Calculation Engine** - Updated stat calculation system that applies stage multipliers
3. **Move Integration** - Enhanced Move class to parse and apply stat modifications from move data
4. **Battle Integration** - Updated Battle class to handle stat modification messages and effects
5. **UI Feedback System** - Battle log messages and visual indicators for stat changes

### Data Flow

```
Move with boosts → Move.apply_stat_modifications() → Pokemon.modify_stat_stage() → Pokemon._recalculate_stats() → Battle displays messages
```

## Components and Interfaces

### Enhanced Pokemon Class

**New/Enhanced Methods:**
- `modify_stat_stage(stat_name: str, change: int) -> str` - Apply stat stage changes with validation
- `get_stat_stage_multiplier(stage: int) -> float` - Calculate multiplier for a given stage
- `get_current_stat_stages() -> dict` - Return current stat stages for UI display
- `reset_stat_stages()` - Reset all stat stages (existing method, ensure it works correctly)

**Enhanced Stat Calculation:**
- Update `_calculate_stat()` method to properly apply stat stage multipliers
- Ensure stat stages are applied before status effect modifiers

### Enhanced Move Class

**New Methods:**
- `_parse_stat_modifications() -> dict` - Parse "boosts" from move data during initialization
- `_apply_stat_modifications(user, target) -> list` - Apply stat changes and return messages
- `has_stat_modifications() -> bool` - Check if move modifies stats

**New Properties:**
- `stat_modifications: dict` - Parsed stat modifications from move data (e.g., {"atk": 2, "def": -1})
- `targets_self: bool` - Whether stat modifications target the user or opponent

### Enhanced Battle Class

**Enhanced Methods:**
- Update `_process_attack()` to handle stat modification messages
- Ensure stat modifications are processed for both damaging and status moves

## Data Models

### Stat Stage Multipliers

The standard Pokemon stat stage multiplier table:

| Stage | Multiplier | Percentage |
|-------|------------|------------|
| -6    | 2/8        | 25%        |
| -5    | 2/7        | ~28.6%     |
| -4    | 2/6        | 33.3%      |
| -3    | 2/5        | 40%        |
| -2    | 2/4        | 50%        |
| -1    | 2/3        | ~66.7%     |
| 0     | 2/2        | 100%       |
| +1    | 3/2        | 150%       |
| +2    | 4/2        | 200%       |
| +3    | 5/2        | 250%       |
| +4    | 6/2        | 300%       |
| +5    | 7/2        | 350%       |
| +6    | 8/2        | 400%       |

### Move Data Integration

Moves with stat modifications will be parsed from the existing `boosts` property in the moves dataset:

```json
{
  "swordsdance": {
    "boosts": {"atk": 2},
    "target": "self"
  },
  "leer": {
    "boosts": {"def": -1},
    "target": "allAdjacentFoes"
  }
}
```

### Stat Name Mapping

Map dataset stat abbreviations to Pokemon class stat names:
- `atk` → `attack`
- `def` → `defense`
- `spa` → `special_attack`
- `spd` → `special_defense`
- `spe` → `speed`
- `accuracy` → `accuracy`
- `evasion` → `evasion`

## Error Handling

### Validation Rules
1. **Stage Limits** - Stat stages cannot exceed -6 or +6
2. **Invalid Stats** - Ignore modifications to non-existent stats
3. **Move Parsing** - Handle missing or malformed boost data gracefully
4. **Pokemon State** - Ensure Pokemon has required attributes before modification

### Error Messages
- "X's [stat] won't go any higher!" (when at +6)
- "X's [stat] won't go any lower!" (when at -6)
- "X's [stat] rose!" / "X's [stat] fell!" (successful modifications)
- "X's [stat] rose sharply!" / "X's [stat] fell harshly!" (±2 stages)
- "X's [stat] rose drastically!" / "X's [stat] fell severely!" (±3+ stages)

### Failure Handling
- Invalid stat modifications are silently ignored
- Moves continue to execute even if stat modifications fail
- Battle log shows appropriate messages for both success and failure cases

## Testing Strategy

### Unit Tests
1. **Stat Stage Calculation** - Test multiplier calculations for all stages (-6 to +6)
2. **Move Parsing** - Test parsing of various boost configurations from move data
3. **Pokemon Integration** - Test stat stage application and stat recalculation
4. **Edge Cases** - Test stage limits, invalid stats, and error conditions

### Integration Tests
1. **Battle Flow** - Test stat modifications during actual battle scenarios
2. **Move Combinations** - Test multiple stat-modifying moves in sequence
3. **Status Interaction** - Ensure stat stages work correctly with status effects
4. **Switch Reset** - Test that stat stages reset when Pokemon switch out

### Functional Tests
1. **Swords Dance** - Verify +2 Attack stage increase
2. **Leer** - Verify -1 Defense stage decrease on opponent
3. **Stage Limits** - Verify proper handling of +6/-6 limits
4. **Battle Messages** - Verify correct battle log messages for all scenarios