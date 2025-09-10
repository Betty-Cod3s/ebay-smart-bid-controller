# src/rule_engine.py
"""
Core rule evaluation engine for eBay Smart Bid Controller.
Processes bidding rules and generates recommendations.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import pandas as pd

class BidAction(Enum):
    """Possible bid adjustment actions."""
    INCREASE = "increase"
    DECREASE = "decrease"
    PAUSE = "pause"
    NO_CHANGE = "no_change"

@dataclass
class Rule:
    """Represents a single bidding rule."""
    name: str
    condition: str  # e.g., "acos < 30"
    action: BidAction
    adjustment_percent: Optional[float] = None
    explanation_template: str = ""
    
    def get_explanation(self, **kwargs) -> str:
        """Generate human-readable explanation for the rule action."""
        return self.explanation_template.format(**kwargs)

@dataclass
class BidRecommendation:
    """Recommendation for a specific campaign/SKU."""
    campaign_id: str
    sku: str
    current_bid: float
    recommended_bid: float
    action: BidAction
    reason: str
    metrics: Dict[str, Any]

class RuleEngine:
    """Main engine for evaluating bidding rules."""
    
    def __init__(self):
        self.rules = self._initialize_default_rules()
        
    def _initialize_default_rules(self) -> List[Rule]:
        """Initialize default bidding rules."""
        return [
            Rule(
                name="high_performance",
                condition="acos < 30 and sales > 0",
                action=BidAction.INCREASE,
                adjustment_percent=10,
                explanation_template="ACOS is {acos:.1f}% (below 30% target), indicating profitable ads. Increasing bid by 10% to capture more traffic."
            ),
            Rule(
                name="poor_performance",
                condition="acos > 30 and sales > 0",
                action=BidAction.DECREASE,
                adjustment_percent=-10,
                explanation_template="ACOS is {acos:.1f}% (above 30% target), indicating unprofitable ads. Decreasing bid by 10% to improve efficiency."
            ),
            Rule(
                name="no_conversion",
                condition="ad_spend >= 10 and sales == 0",
                action=BidAction.PAUSE,
                adjustment_percent=0,
                explanation_template="Spent ${ad_spend:.2f} with 0 sales. Pausing to prevent further losses."
            ),
            Rule(
                name="low_spend_no_sales",
                condition="ad_spend >= 5 and ad_spend < 10 and sales == 0",
                action=BidAction.DECREASE,
                adjustment_percent=-20,
                explanation_template="Spent ${ad_spend:.2f} with no sales yet. Decreasing bid by 20% to test lower cost."
            ),
            Rule(
                name="excellent_performance",
                condition="acos < 15 and sales > 5",
                action=BidAction.INCREASE,
                adjustment_percent=20,
                explanation_template="Excellent ACOS of {acos:.1f}% with {sales} sales. Increasing bid by 20% to maximize profitable volume."
            )
        ]
    
    def evaluate_row(self, row: pd.Series) -> Optional[BidRecommendation]:
        """
        Evaluate a single row of data against all rules.
        Returns the first matching rule's recommendation.
        """
        # Calculate metrics
        metrics = self._calculate_metrics(row)
        
        # Evaluate each rule
        for rule in self.rules:
            if self._evaluate_condition(rule.condition, metrics):
                return self._create_recommendation(row, rule, metrics)
        
        # No rule matched
        return BidRecommendation(
            campaign_id=row.get('campaign_id', 'Unknown'),
            sku=row.get('sku', 'Unknown'),
            current_bid=row.get('current_bid', 0),
            recommended_bid=row.get('current_bid', 0),
            action=BidAction.NO_CHANGE,
            reason="No rules matched - maintaining current bid",
            metrics=metrics
        )
    
    def _calculate_metrics(self, row: pd.Series) -> Dict[str, Any]:
        """Calculate key metrics from row data."""
        ad_spend = float(row.get('ad_spend', 0))
        sales = float(row.get('sales', 0))
        revenue = float(row.get('revenue', 0))
        clicks = int(row.get('clicks', 0))
        impressions = int(row.get('impressions', 0))
        
        # Calculate ACOS (Advertising Cost of Sale)
        acos = (ad_spend / revenue * 100) if revenue > 0 else float('inf')
        
        # Calculate CTR (Click-Through Rate)
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        
        # Calculate CPC (Cost Per Click)
        cpc = (ad_spend / clicks) if clicks > 0 else 0
        
        return {
            'ad_spend': ad_spend,
            'sales': sales,
            'revenue': revenue,
            'clicks': clicks,
            'impressions': impressions,
            'acos': acos,
            'ctr': ctr,
            'cpc': cpc,
            'current_bid': float(row.get('current_bid', 0))
        }
    
    def _evaluate_condition(self, condition: str, metrics: Dict[str, Any]) -> bool:
        """
        Safely evaluate a condition string against metrics.
        Uses Python's eval with restricted namespace for safety.
        """
        try:
            # Create safe namespace with only metrics and comparison functions
            safe_namespace = {
                **metrics,
                '__builtins__': {},
                'min': min,
                'max': max,
                'abs': abs
            }
            return eval(condition, safe_namespace)
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _create_recommendation(self, row: pd.Series, rule: Rule, metrics: Dict[str, Any]) -> BidRecommendation:
        """Create a bid recommendation based on a matching rule."""
        current_bid = metrics['current_bid']
        
        # Calculate new bid based on action
        if rule.action == BidAction.INCREASE:
            new_bid = current_bid * (1 + rule.adjustment_percent / 100)
        elif rule.action == BidAction.DECREASE:
            new_bid = current_bid * (1 + rule.adjustment_percent / 100)
            new_bid = max(new_bid, 0.01)  # Ensure bid doesn't go below minimum
        elif rule.action == BidAction.PAUSE:
            new_bid = 0
        else:
            new_bid = current_bid
        
        # Generate explanation
        explanation = rule.get_explanation(**metrics)
        
        return BidRecommendation(
            campaign_id=row.get('campaign_id', 'Unknown'),
            sku=row.get('sku', 'Unknown'),
            current_bid=current_bid,
            recommended_bid=round(new_bid, 2),
            action=rule.action,
            reason=explanation,
            metrics=metrics
        )
    
    def add_custom_rule(self, rule: Rule):
        """Add a custom rule to the engine."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """Remove a rule by name."""
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def get_rules_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of all active rules."""
        return [
            {
                'name': rule.name,
                'condition': rule.condition,
                'action': rule.action.value,
                'adjustment': f"{rule.adjustment_percent:+.0f}%" if rule.adjustment_percent else "N/A"
            }
            for rule in self.rules
        ]