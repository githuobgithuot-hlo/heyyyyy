"""
Market matching logic using fuzzy string matching.
"""
from typing import List, Dict, Tuple, Optional
from rapidfuzz import fuzz, process

from .logger import setup_logger


class MarketMatcher:
    """Matches markets across different platforms using fuzzy matching."""
    
    def __init__(self, similarity_threshold: float = 85.0):
        """
        Initialize market matcher.
        
        Args:
            similarity_threshold: Minimum similarity percentage (0-100)
        """
        self.similarity_threshold = similarity_threshold
        self.logger = setup_logger("market_matcher")
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize market name for better matching.
        
        Args:
            name: Market name
        
        Returns:
            Normalized name
        """
        # Convert to lowercase and remove extra whitespace
        normalized = name.lower().strip()
        
        # Remove common punctuation
        for char in ['.', ',', '!', '?', ':', ';', '-', '_']:
            normalized = normalized.replace(char, ' ')
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two market names.
        
        Args:
            name1: First market name
            name2: Second market name
        
        Returns:
            Similarity score (0-100)
        """
        normalized1 = self._normalize_name(name1)
        normalized2 = self._normalize_name(name2)
        
        # Use token sort ratio for better matching of reordered words
        similarity = fuzz.token_sort_ratio(normalized1, normalized2)
        
        return similarity
    
    def _match_outcomes(
        self,
        outcomes1: List[Dict],
        outcomes2: List[Dict]
    ) -> List[Tuple[Dict, Dict]]:
        """
        Match outcomes between two markets.
        
        Args:
            outcomes1: Outcomes from first market
            outcomes2: Outcomes from second market
        
        Returns:
            List of matched outcome pairs
        """
        matched_pairs = []
        
        for outcome1 in outcomes1:
            name1 = outcome1.get('name', '').lower()
            
            for outcome2 in outcomes2:
                name2 = outcome2.get('name', '').lower()
                
                # Direct match
                if name1 == name2:
                    matched_pairs.append((outcome1, outcome2))
                    break
                
                # Fuzzy match for variations (YES/NO, Win/Lose, etc.)
                similarity = fuzz.ratio(name1, name2)
                if similarity >= 85:
                    matched_pairs.append((outcome1, outcome2))
                    break
                
                # Handle YES/NO vs Win/Lose variations
                yes_no_variants = {
                    'yes': ['win', 'victory', 'success', 'true'],
                    'no': ['lose', 'loss', 'defeat', 'false']
                }
                
                for key, variants in yes_no_variants.items():
                    if (name1 == key and name2 in variants) or (name2 == key and name1 in variants):
                        matched_pairs.append((outcome1, outcome2))
                        break
        
        return matched_pairs
    
    def find_matches(
        self,
        markets_a: List,
        markets_b: List,
        platform_a: str = "polymarket",
        platform_b: str = "cloudbet"
    ) -> List[Dict]:
        """
        Find matching markets between two platforms.
        
        Works with both Dict and NormalizedMarket objects.
        
        Args:
            markets_a: Markets from first platform
            markets_b: Markets from second platform
            platform_a: Name of first platform
            platform_b: Name of second platform
        
        Returns:
            List of matched market pairs with outcome matches
        """
        matches = []
        
        for market_a in markets_a:
            # Handle both dict and NormalizedMarket
            if hasattr(market_a, 'title'):
                name_a = market_a.title
                outcomes_a = market_a.outcomes
                market_a_dict = market_a.dict()
            else:
                name_a = market_a.get('title') or market_a.get('name', '')
                outcomes_a = market_a.get('outcomes', {})
                market_a_dict = market_a
            
            if not outcomes_a:
                continue
            
            # Find best matching market in platform B
            best_match = None
            best_similarity = 0
            
            for market_b in markets_b:
                # Handle both dict and NormalizedMarket
                if hasattr(market_b, 'title'):
                    name_b = market_b.title
                    outcomes_b = market_b.outcomes
                    market_b_dict = market_b.dict()
                else:
                    name_b = market_b.get('title') or market_b.get('name', '')
                    outcomes_b = market_b.get('outcomes', {})
                    market_b_dict = market_b
                
                if not outcomes_b:
                    continue
                
                similarity = self._calculate_similarity(name_a, name_b)
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    # Check if outcomes can be matched
                    # Convert outcomes dict to list format for matching
                    outcomes_a_list = [{'name': k, 'odds': v} for k, v in outcomes_a.items()]
                    outcomes_b_list = [{'name': k, 'odds': v} for k, v in outcomes_b.items()]
                    outcome_matches = self._match_outcomes(outcomes_a_list, outcomes_b_list)
                    
                    if len(outcome_matches) >= 2:  # Need at least 2 matched outcomes
                        best_similarity = similarity
                        best_match = {
                            'market_name': name_a,
                            'market_a': market_a_dict,
                            'market_b': market_b_dict,
                            'similarity': similarity,
                            'outcome_matches': outcome_matches,
                            'platform_a': platform_a,
                            'platform_b': platform_b
                        }
            
            if best_match:
                matches.append(best_match)
                self.logger.debug(
                    f"Matched: '{name_a}' (similarity: {best_similarity:.1f}%)"
                )
        
        self.logger.info(f"Found {len(matches)} market matches (threshold: {self.similarity_threshold}%)")
        return matches

