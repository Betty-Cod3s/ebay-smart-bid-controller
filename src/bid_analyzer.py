# src/bid_analyzer.py
"""
Bid analyzer for processing eBay ad reports and generating recommendations.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

from rule_engine import RuleEngine, BidRecommendation, BidAction

class BidAnalyzer:
    """Analyzes eBay ad performance and generates bid recommendations."""
    
    def __init__(self, rule_engine: Optional[RuleEngine] = None):
        """Initialize the analyzer with a rule engine."""
        self.rule_engine = rule_engine or RuleEngine()
        self.data = None
        self.recommendations = []
        
    def load_csv(self, filepath: str) -> pd.DataFrame:
        """Load eBay ad report from CSV file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    self.data = pd.read_csv(filepath, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            self._standardize_columns()
            print(f"✓ Loaded {len(self.data)} campaigns from CSV")
            return self.data
            
        except Exception as e:
            raise Exception(f"Error loading CSV: {e}")
    
    def load_json(self, filepath: str) -> pd.DataFrame:
        """Load eBay ad report from JSON file."""
        try:
            with open(filepath, 'r') as f:
                json_data = json.load(f)
            
            # Handle both array and object formats
            if isinstance(json_data, list):
                self.data = pd.DataFrame(json_data)
            elif isinstance(json_data, dict) and 'data' in json_data:
                self.data = pd.DataFrame(json_data['data'])
            else:
                self.data = pd.DataFrame([json_data])
            
            self._standardize_columns()
            print(f"✓ Loaded {len(self.data)} campaigns from JSON")
            return self.data
            
        except Exception as e:
            raise Exception(f"Error loading JSON: {e}")
    
    def load_sample_data(self) -> pd.DataFrame:
        """Generate sample data for testing."""
        np.random.seed(42)
        
        sample_data = {
            'campaign_id': [f'CAM_{i:03d}' for i in range(1, 21)],
            'sku': [f'SKU_{i:04d}' for i in range(1001, 1021)],
            'product_name': [f'Product {i}' for i in range(1, 21)],
            'current_bid': np.random.uniform(0.5, 5.0, 20).round(2),
            'impressions': np.random.randint(100, 10000, 20),
            'clicks': np.random.randint(0, 500, 20),
            'ad_spend': np.random.uniform(0, 100, 20).round(2),
            'sales': np.random.randint(0, 20, 20),
            'revenue': np.random.uniform(0, 500, 20).round(2)
        }
        
        # Ensure some specific scenarios
        sample_data['sales'][5] = 0  # No sales scenario
        sample_data['ad_spend'][5] = 15.00  # High spend, no sales
        
        sample_data['sales'][10] = 10  # High performance
        sample_data['revenue'][10] = 300
        sample_data['ad_spend'][10] = 30  # ACOS = 10%
        
        sample_data['sales'][15] = 2  # Poor performance
        sample_data['revenue'][15] = 50
        sample_data['ad_spend'][15] = 25  # ACOS = 50%
        
        self.data = pd.DataFrame(sample_data)
        print(f"✓ Generated {len(self.data)} sample campaigns")
        return self.data
    
    def _standardize_columns(self):
        """Standardize column names to expected format."""
        column_mapping = {
            # Common variations
            'Campaign ID': 'campaign_id',
            'campaign id': 'campaign_id',
            'Campaign': 'campaign_id',
            
            'SKU': 'sku',
            'Product SKU': 'sku',
            'Item Number': 'sku',
            
            'Current Bid': 'current_bid',
            'Max Bid': 'current_bid',
            'Bid': 'current_bid',
            
            'Ad Spend': 'ad_spend',
            'Spend': 'ad_spend',
            'Cost': 'ad_spend',
            
            'Sales': 'sales',
            'Orders': 'sales',
            'Conversions': 'sales',
            
            'Revenue': 'revenue',
            'Sales Revenue': 'revenue',
            'Total Sales': 'revenue',
            
            'Clicks': 'clicks',
            'Click': 'clicks',
            
            'Impressions': 'impressions',
            'Impression': 'impressions'
        }
        
        # Rename columns
        self.data.rename(columns=column_mapping, inplace=True)
        
        # Ensure numeric columns are numeric
        numeric_columns = ['current_bid', 'ad_spend', 'sales', 'revenue', 'clicks', 'impressions']
        for col in numeric_columns:
            if col in self.data.columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce').fillna(0)
    
    def analyze(self) -> List[BidRecommendation]:
        """Analyze all campaigns and generate recommendations."""
        if self.data is None:
            raise ValueError("No data loaded. Please load data first.")
        
        self.recommendations = []
        
        for _, row in self.data.iterrows():
            recommendation = self.rule_engine.evaluate_row(row)
            if recommendation and recommendation.action != BidAction.NO_CHANGE:
                self.recommendations.append(recommendation)
        
        print(f"✓ Generated {len(self.recommendations)} recommendations")
        return self.recommendations
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics of recommendations."""
        if not self.recommendations:
            return {"message": "No recommendations generated yet"}
        
        action_counts = {}
        total_current_spend = 0
        total_recommended_spend = 0
        
        for rec in self.recommendations:
            action = rec.action.value
            action_counts[action] = action_counts.get(action, 0) + 1
            total_current_spend += rec.current_bid
            total_recommended_spend += rec.recommended_bid
        
        return {
            'total_recommendations': len(self.recommendations),
            'actions': action_counts,
            'current_total_bid': round(total_current_spend, 2),
            'recommended_total_bid': round(total_recommended_spend, 2),
            'net_change': round(total_recommended_spend - total_current_spend, 2),
            'percent_change': round((total_recommended_spend - total_current_spend) / total_current_spend * 100, 2) if total_current_spend > 0 else 0
        }
    
    def export_recommendations(self, output_path: str = None) -> str:
        """Export recommendations to CSV file."""
        if not self.recommendations:
            raise ValueError("No recommendations to export")
        
        # Create DataFrame from recommendations
        export_data = []
        for rec in self.recommendations:
            export_data.append({
                'Campaign ID': rec.campaign_id,
                'SKU': rec.sku,
                'Current Bid': rec.current_bid,
                'Recommended Bid': rec.recommended_bid,
                'Action': rec.action.value.upper(),
                'Bid Change': round(rec.recommended_bid - rec.current_bid, 2),
                'Reason': rec.reason,
                'ACOS': round(rec.metrics.get('acos', 0), 2),
                'Ad Spend': round(rec.metrics.get('ad_spend', 0), 2),
                'Revenue': round(rec.metrics.get('revenue', 0), 2),
                'Sales': rec.metrics.get('sales', 0)
            })
        
        df = pd.DataFrame(export_data)
        
        # Generate filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'data/exports/bid_recommendations_{timestamp}.csv'
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        print(f"✓ Exported recommendations to {output_path}")
        
        return output_path
    
    def get_recommendations_by_action(self, action: BidAction) -> List[BidRecommendation]:
        """Filter recommendations by action type."""
        return [rec for rec in self.recommendations if rec.action == action]
    
    def print_summary_report(self):
        """Print a formatted summary report to console."""
        if not self.recommendations:
            print("No recommendations generated yet.")
            return
        
        print("\n" + "="*60)
        print("📊 BID ADJUSTMENT SUMMARY REPORT")
        print("="*60)
        
        stats = self.get_summary_statistics()
        
        print(f"\n📈 Total Recommendations: {stats['total_recommendations']}")
        print(f"💰 Current Total Bids: ${stats['current_total_bid']:.2f}")
        print(f"💡 Recommended Total Bids: ${stats['recommended_total_bid']:.2f}")
        print(f"📊 Net Change: ${stats['net_change']:.2f} ({stats['percent_change']:+.1f}%)")
        
        print("\n🎯 Actions Breakdown:")
        for action, count in stats['actions'].items():
            emoji = {
                'increase': '⬆️',
                'decrease': '⬇️',
                'pause': '⏸️'
            }.get(action, '•')
            print(f"  {emoji} {action.capitalize()}: {count} campaigns")
        
        # Show top recommendations
        print("\n🔝 Top 5 Recommendations:")
        print("-" * 60)
        
        for i, rec in enumerate(self.recommendations[:5], 1):
            action_symbol = {
                BidAction.INCREASE: '⬆️',
                BidAction.DECREASE: '⬇️',
                BidAction.PAUSE: '⏸️'
            }.get(rec.action, '•')
            
            print(f"\n{i}. {rec.sku} ({rec.campaign_id})")
            print(f"   {action_symbol} Action: {rec.action.value.upper()}")
            print(f"   💵 Bid: ${rec.current_bid:.2f} → ${rec.recommended_bid:.2f}")
            print(f"   📝 Reason: {rec.reason}")
        
        print("\n" + "="*60)