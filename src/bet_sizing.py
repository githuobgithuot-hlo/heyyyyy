"""
Kelly Criterion bet sizing calculator.
"""
from typing import Dict
from .logger import setup_logger


class BetSizing:
    """Calculates optimal bet sizes using Kelly Criterion."""
    
    def __init__(self, bankroll: float, kelly_fraction: float = 0.5):
        """
        Initialize bet sizing calculator.
        
        Args:
            bankroll: Total available capital
            kelly_fraction: Kelly multiplier (1.0 = full Kelly, 0.5 = half Kelly, etc.)
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.logger = setup_logger("bet_sizing")
    
    def calculate_kelly(
        self,
        odds_a: float,
        odds_b: float,
        profit_percentage: float
    ) -> Dict:
        """
        Calculate optimal bet sizes using Kelly Criterion for arbitrage.
        
        For arbitrage, we want to maximize guaranteed profit while ensuring
        we win regardless of outcome.
        
        Args:
            odds_a: Decimal odds on platform A
            odds_b: Decimal odds on platform B
            profit_percentage: Expected profit percentage
        
        Returns:
            Dictionary with bet sizing information
        """
        # For arbitrage, we bet on both outcomes
        # We need to calculate bet amounts such that:
        # - If outcome A wins: bet_a * odds_a - bet_a - bet_b = profit
        # - If outcome B wins: bet_b * odds_b - bet_a - bet_b = profit
        
        # Calculate implied probabilities
        prob_a = 1.0 / odds_a
        prob_b = 1.0 / odds_b
        total_prob = prob_a + prob_b
        
        # For arbitrage, we want equal profit regardless of outcome
        # Optimal allocation: bet amounts proportional to inverse odds
        # This ensures equal profit regardless of which outcome wins
        
        # Calculate optimal bet ratios
        # bet_a / bet_b = odds_b / odds_a (for equal profit)
        
        # Using the formula for arbitrage:
        # Total capital = bet_a + bet_b
        # If A wins: profit = bet_a * odds_a - total_capital
        # If B wins: profit = bet_b * odds_b - total_capital
        # For equal profit: bet_a * odds_a = bet_b * odds_b
        
        # Therefore: bet_a = (total_capital * odds_b) / (odds_a + odds_b)
        #            bet_b = (total_capital * odds_a) / (odds_a + odds_b)
        
        # But we want to use Kelly fraction of bankroll
        kelly_bankroll = self.bankroll * self.kelly_fraction
        
        # Calculate bet amounts for equal profit
        bet_amount_a = (kelly_bankroll * odds_b) / (odds_a + odds_b)
        bet_amount_b = (kelly_bankroll * odds_a) / (odds_a + odds_b)
        
        # Ensure we don't exceed bankroll
        total_bet = bet_amount_a + bet_amount_b
        if total_bet > kelly_bankroll:
            # Scale down proportionally
            scale = kelly_bankroll / total_bet
            bet_amount_a *= scale
            bet_amount_b *= scale
            total_bet = kelly_bankroll
        
        # Calculate guaranteed profit
        # Profit if A wins: bet_a * odds_a - total_bet
        # Profit if B wins: bet_b * odds_b - total_bet
        profit_if_a_wins = bet_amount_a * odds_a - total_bet
        profit_if_b_wins = bet_amount_b * odds_b - total_bet
        
        # They should be equal (or very close due to rounding)
        guaranteed_profit = min(profit_if_a_wins, profit_if_b_wins)
        profit_percentage_actual = (guaranteed_profit / total_bet) * 100
        
        return {
            'bet_amount_a': round(bet_amount_a, 2),
            'bet_amount_b': round(bet_amount_b, 2),
            'total_capital': round(total_bet, 2),
            'guaranteed_profit': round(guaranteed_profit, 2),
            'profit_percentage': round(profit_percentage_actual, 2),
            'kelly_fraction_used': self.kelly_fraction,
            'bankroll_used': round(kelly_bankroll, 2)
        }
    
    def calculate_for_opportunity(self, opportunity: Dict) -> Dict:
        """
        Calculate bet sizing for an arbitrage opportunity.
        
        Args:
            opportunity: Arbitrage opportunity dictionary
        
        Returns:
            Opportunity dictionary with bet sizing added
        """
        odds_a = opportunity['odds_a']
        odds_b = opportunity['odds_b']
        profit_percentage = opportunity['profit_percentage']
        
        bet_sizing = self.calculate_kelly(odds_a, odds_b, profit_percentage)
        
        # Add bet sizing to opportunity
        opportunity.update(bet_sizing)
        
        self.logger.debug(
            f"Bet sizing calculated: "
            f"Bet A: ${bet_sizing['bet_amount_a']}, "
            f"Bet B: ${bet_sizing['bet_amount_b']}, "
            f"Profit: ${bet_sizing['guaranteed_profit']}"
        )
        
        return opportunity

