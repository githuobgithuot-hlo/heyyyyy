"""
Unit tests for arbitrage detection logic.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arbitrage_engine import ArbitrageEngine
from bet_sizing import BetSizing


class TestArbitrageEngine:
    """Test arbitrage detection logic."""
    
    def test_arbitrage_detection_valid(self):
        """Test detection of valid arbitrage opportunity."""
        engine = ArbitrageEngine(min_profit_threshold=0.5)
        
        # Example: odds where 1/odds_a + 1/odds_b < 1
        # odds_a = 2.0 (50%), odds_b = 2.1 (47.6%) -> total = 97.6% < 100%
        result = engine._calculate_arbitrage(2.0, 2.1)
        
        assert result is not None
        assert result['profit_percentage'] > 0
        assert result['total_prob'] < 1.0
    
    def test_arbitrage_detection_invalid(self):
        """Test that non-arbitrage odds return None."""
        engine = ArbitrageEngine(min_profit_threshold=0.5)
        
        # Example: odds where 1/odds_a + 1/odds_b >= 1
        # odds_a = 2.0 (50%), odds_b = 2.0 (50%) -> total = 100%
        result = engine._calculate_arbitrage(2.0, 2.0)
        
        assert result is None
    
    def test_min_profit_threshold(self):
        """Test that opportunities below threshold are filtered."""
        engine = ArbitrageEngine(min_profit_threshold=5.0)  # 5% minimum
        
        # Small arbitrage opportunity (~2.4% profit)
        result = engine._calculate_arbitrage(2.0, 2.1)
        
        # Should be None because profit is below 5%
        assert result is None
    
    def test_invalid_odds(self):
        """Test handling of invalid odds."""
        engine = ArbitrageEngine(min_profit_threshold=0.5)
        
        # Odds <= 1.0 should return None
        assert engine._calculate_arbitrage(1.0, 2.0) is None
        assert engine._calculate_arbitrage(2.0, 1.0) is None
        assert engine._calculate_arbitrage(0.5, 2.0) is None


class TestBetSizing:
    """Test Kelly Criterion bet sizing."""
    
    def test_bet_sizing_calculation(self):
        """Test bet sizing calculation."""
        bet_sizing = BetSizing(bankroll=10000.0, kelly_fraction=0.5)
        
        # Example arbitrage: odds_a = 2.0, odds_b = 2.1
        result = bet_sizing.calculate_kelly(2.0, 2.1, 2.5)
        
        assert result['bet_amount_a'] > 0
        assert result['bet_amount_b'] > 0
        assert result['total_capital'] > 0
        assert result['guaranteed_profit'] > 0
        assert result['profit_percentage'] > 0
    
    def test_bet_sizing_within_bankroll(self):
        """Test that bet sizes don't exceed bankroll."""
        bet_sizing = BetSizing(bankroll=1000.0, kelly_fraction=1.0)
        
        result = bet_sizing.calculate_kelly(2.0, 2.1, 2.5)
        
        assert result['total_capital'] <= 1000.0
        assert result['bet_amount_a'] + result['bet_amount_b'] <= 1000.0
    
    def test_kelly_fraction(self):
        """Test that Kelly fraction is applied correctly."""
        bankroll = 10000.0
        
        full_kelly = BetSizing(bankroll=bankroll, kelly_fraction=1.0)
        half_kelly = BetSizing(bankroll=bankroll, kelly_fraction=0.5)
        
        result_full = full_kelly.calculate_kelly(2.0, 2.1, 2.5)
        result_half = half_kelly.calculate_kelly(2.0, 2.1, 2.5)
        
        # Half Kelly should use approximately half the capital
        assert result_half['total_capital'] < result_full['total_capital']
        assert abs(result_half['total_capital'] / result_full['total_capital'] - 0.5) < 0.1
    
    def test_equal_profit_guarantee(self):
        """Test that profit is equal regardless of outcome."""
        bet_sizing = BetSizing(bankroll=10000.0, kelly_fraction=0.5)
        
        result = bet_sizing.calculate_kelly(2.0, 2.1, 2.5)
        
        # Calculate profit for both outcomes
        profit_if_a = result['bet_amount_a'] * 2.0 - result['total_capital']
        profit_if_b = result['bet_amount_b'] * 2.1 - result['total_capital']
        
        # Should be approximately equal (within rounding error)
        assert abs(profit_if_a - profit_if_b) < 0.01
        assert abs(profit_if_a - result['guaranteed_profit']) < 0.01


class TestProfitThreshold:
    """Test profit threshold validation."""
    
    def test_profit_threshold_filtering(self):
        """Test that opportunities below threshold are filtered."""
        engine = ArbitrageEngine(min_profit_threshold=1.0)
        
        # Create a small arbitrage opportunity
        result = engine._calculate_arbitrage(2.05, 2.05)
        
        # Should be None if profit is below 1%
        if result:
            assert result['profit_percentage'] >= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

