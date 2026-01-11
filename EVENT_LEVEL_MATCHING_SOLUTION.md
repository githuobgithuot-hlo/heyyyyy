# Event-Level Matching Solution

## Problem Statement

The system was showing 0 matches because it was trying to match markets directly, but Polymarket and Cloudbet use fundamentally different market structures:

- **Polymarket**: Binary prediction markets (YES/NO contracts) with probability-based pricing
- **Cloudbet**: Traditional sportsbook odds (moneyline, spreads, totals)

Matching at the market level doesn't work because:
- Polymarket: "Will Lakers beat Warriors?" (YES/NO)
- Cloudbet: "Lakers vs Warriors" (Lakers/Warriors moneyline)

## Solution

Implemented **event-level matching** with **probability-based value detection**:

### 1. Event-Level Matching (`src/event_matcher.py`)

Matches events by:
- **Teams**: Both teams must match (order-independent)
- **Sport/League**: Same sport category
- **Date/Time**: Events within a configurable time window (default: 48 hours)

This ensures we're comparing the same actual event, not just similar-sounding markets.

### 2. Probability Conversion (`src/probability_engine.py`)

Converts all outcomes to implied probabilities:
- **Polymarket YES/NO** → Team probabilities
  - "Will Lakers beat Warriors?" (YES: 60%, NO: 40%)
  - Maps to: Lakers: 60%, Warriors: 40%
- **Cloudbet Moneyline** → Team probabilities
  - Lakers: 2.0 odds → 50% probability
  - Warriors: 1.8 odds → 55.6% probability

### 3. Value Detection

Detects two types of opportunities:

#### A. Arbitrage Opportunities
- Sum of probabilities < 1.0
- Guaranteed profit regardless of outcome
- Example: PM says 60% Lakers, CB says 35% Warriors = 95% total = 5% arbitrage

#### B. Value Edges
- One platform has significantly better odds than the other
- Example: PM says 60% Lakers, CB says 50% Lakers = 10% edge on Polymarket
- Not guaranteed profit, but better expected value

## Implementation Details

### New Files

1. **`src/event_matcher.py`**
   - `EventMatcher` class
   - Matches events by teams, sport, and time
   - Team name normalization and fuzzy matching
   - Time window validation

2. **`src/probability_engine.py`**
   - `ProbabilityEngine` class
   - Converts odds to probabilities
   - Maps Polymarket YES/NO to teams
   - Detects arbitrage and value edges

### Modified Files

1. **`src/sports_arbitrage_engine.py`**
   - Now uses `ProbabilityEngine` for detection
   - Handles both arbitrage and value edge opportunities
   - Returns formatted opportunities for the rest of the system

2. **`src/main.py`**
   - Added `EventMatcher` initialization
   - Updated sports matching to use event-level matching first
   - Keeps legacy matching as fallback

### Configuration

```python
# Event matcher settings
team_similarity_threshold=80.0  # Minimum team name match (0-100)
time_window_hours=48  # Maximum time difference for matching

# Probability engine settings
min_value_edge=0.05  # 5% minimum edge for value bets
min_arbitrage_profit=0.5  # 0.5% minimum for arbitrage alerts
```

## How It Works

### Step 1: Event Matching
```
Polymarket: "Will Lakers beat Warriors?" (Teams: Lakers, Warriors)
Cloudbet: "Lakers - Warriors" (Teams: Lakers, Warriors)
Sport: basketball
Time: Within 48 hours
→ MATCH! ✅
```

### Step 2: Probability Conversion
```
Polymarket:
  YES: 2.0 odds → 50% probability → Maps to Lakers: 50%
  NO: 2.0 odds → 50% probability → Maps to Warriors: 50%

Cloudbet:
  Lakers: 2.1 odds → 47.6% probability
  Warriors: 1.9 odds → 52.6% probability
```

### Step 3: Value Detection
```
Check arbitrage:
  Lakers (PM) + Warriors (CB) = 50% + 52.6% = 102.6% (no arbitrage)
  Warriors (PM) + Lakers (CB) = 50% + 47.6% = 97.6% (arbitrage! 2.4% profit)

Check value edges:
  Lakers: PM 50% vs CB 47.6% = 2.4% edge on PM
  Warriors: PM 50% vs CB 52.6% = 2.6% edge on CB
```

## Testing

Run the test script:
```bash
python test_event_matching.py
```

This will:
1. Fetch real data from both APIs
2. Normalize and group by events
3. Perform event-level matching
4. Convert to probabilities
5. Detect value opportunities

## Expected Results

With the new system:
- ✅ Events are matched by actual teams, not just similar names
- ✅ Probabilities are compared accurately
- ✅ Both arbitrage and value edges are detected
- ✅ Real opportunities will appear when matching events exist

## Why This Works

The key insight is that **Polymarket and Cloudbet represent the same events differently**:

- Polymarket: "Will Team A beat Team B?" (YES/NO)
- Cloudbet: "Team A vs Team B" (Team A / Team B moneyline)

By matching at the **event level** (same teams, sport, time) and converting everything to **probabilities**, we can accurately compare them and find real opportunities.

## Next Steps

1. **Run the test**: `python test_event_matching.py`
2. **Monitor logs**: Check for event matches and value opportunities
3. **Adjust thresholds**: Fine-tune `team_similarity_threshold` and `time_window_hours` if needed
4. **Review opportunities**: When matches are found, verify they're correct

## Configuration Tuning

If you're getting too many false positives:
- Increase `team_similarity_threshold` (e.g., 85.0)
- Decrease `time_window_hours` (e.g., 24)

If you're missing valid matches:
- Decrease `team_similarity_threshold` (e.g., 75.0)
- Increase `time_window_hours` (e.g., 72)

## Summary

✅ **Event-level matching** ensures we compare the same actual events
✅ **Probability conversion** makes different market types comparable
✅ **Value detection** finds both arbitrage and value edges
✅ **Real opportunities** will now appear when matching events exist

The system is now correctly structured to find opportunities between Polymarket and Cloudbet!

