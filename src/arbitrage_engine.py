"""
Arbitrage detection engine.
"""
from typing import List, Dict, Optional
from .logger import setup_logger


class ArbitrageEngine:
    """Detects arbitrage opportunities from matched markets."""
    
    def __init__(self, min_profit_threshold: float = 0.5):
        """
        Initialize arbitrage engine.
        
        Args:
            min_profit_threshold: Minimum profit percentage to consider (e.g., 0.5 = 0.5%)
        """
        self.min_profit_threshold = min_profit_threshold
        self.logger = setup_logger("arbitrage_engine")
    
    def _calculate_arbitrage(
        self,
        odds_a: float,
        odds_b: float
    ) -> Optional[Dict]:
        """
        Calculate arbitrage opportunity between two odds.
        
        Args:
            odds_a: Decimal odds on platform A
            odds_b: Decimal odds on platform B
        
        Returns:
            Arbitrage data dictionary or None if no arbitrage
        """
        if odds_a <= 1.0 or odds_b <= 1.0:
            return None
        
        # Calculate implied probabilities
        prob_a = 1.0 / odds_a
        prob_b = 1.0 / odds_b
        
        # Check for arbitrage (sum of probabilities < 1)
        total_prob = prob_a + prob_b
        
        if total_prob >= 1.0:
            return None
        
        # Calculate profit percentage
        profit_percentage = ((1.0 - total_prob) / total_prob) * 100
        
        if profit_percentage < self.min_profit_threshold:
            return None
        
        return {
            'odds_a': odds_a,
            'odds_b': odds_b,
            'prob_a': prob_a,
            'prob_b': prob_b,
            'total_prob': total_prob,
            'profit_percentage': profit_percentage
        }
    
    def detect_arbitrage(self, matched_markets: List[Dict]) -> List[Dict]:
        """
        Detect arbitrage opportunities from matched markets.
        
        Args:
            matched_markets: List of matched market pairs
        
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        for match in matched_markets:
            market_a = match['market_a']
            market_b = match['market_b']
            
            market_name = market_a.get('title') or market_a.get('name', 'Unknown Market')
            
            # Get all outcomes from both markets
            outcomes_a = market_a.get('outcomes', {})
            outcomes_b = market_b.get('outcomes', {})
            
            if not outcomes_a or not outcomes_b:
                continue
            
            # Convert to list format for processing
            outcomes_a_list = [{'name': k, 'odds': v} for k, v in outcomes_a.items()]
            outcomes_b_list = [{'name': k, 'odds': v} for k, v in outcomes_b.items()]
            
            # Check ALL combinations for arbitrage (not just matched pairs)
            # For arbitrage, we need opposite outcomes (YES from A vs NO from B, etc.)
            for outcome_a in outcomes_a_list:
                for outcome_b in outcomes_b_list:
                    odds_a = outcome_a.get('odds')
                    odds_b = outcome_b.get('odds')
                    
                    if not odds_a or not odds_b:
                        continue
                    
                    # For arbitrage, we need opposite outcomes (YES/NO)
                    name_a = outcome_a.get('name', '').upper()
                    name_b = outcome_b.get('name', '').upper()
                    
                    # Valid opposite pairs: YES/NO, WIN/LOSE, etc.
                    valid_pairs = [
                        ('YES', 'NO'),
                        ('NO', 'YES'),
                        ('WIN', 'LOSE'),
                        ('LOSE', 'WIN'),
                        ('TRUE', 'FALSE'),
                        ('FALSE', 'TRUE')
                    ]
                    
                    is_valid_pair = any(
                        (name_a == pair[0] and name_b == pair[1]) or
                        (name_a == pair[1] and name_b == pair[0])
                        for pair in valid_pairs
                    )
                    
                    if not is_valid_pair:
                        # If names are the same, skip (not opposite)
                        if name_a == name_b:
                            continue
                        # For other cases, assume they might be opposite if names differ
                        # This handles cases like "Trump" vs "Biden" or other variations
                    
                    # Calculate arbitrage for this outcome pair
                    arb_data = self._calculate_arbitrage(odds_a, odds_b)
                    
                    if arb_data:
                        opportunity = {
                            'market_name': market_name,
                            'outcome_name': f"{outcome_a.get('name')} vs {outcome_b.get('name')}",
                            'platform_a': match['platform_a'],
                            'platform_b': match['platform_b'],
                            'market_a': market_a,
                            'market_b': market_b,
                            'outcome_a': outcome_a,
                            'outcome_b': outcome_b,
                            'odds_a': odds_a,
                            'odds_b': odds_b,
                            'profit_percentage': arb_data['profit_percentage'],
                            'similarity': match['similarity']
                        }
                        
                        opportunities.append(opportunity)
                        self.logger.info(
                            f"Arbitrage found: {market_name} - "
                            f"{outcome_a.get('name')} @ {odds_a:.2f} vs {outcome_b.get('name')} @ {odds_b:.2f} - "
                            f"Profit: {arb_data['profit_percentage']:.2f}%"
                        )
        
        self.logger.info(f"Detected {len(opportunities)} arbitrage opportunities")
        return opportunities

