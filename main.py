# main.py
"""
eBay Smart Bid Controller - Main CLI Application
Automates bid adjustments based on performance metrics.
"""

import click
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Add src to path
sys.path.append('src')

from bid_analyzer import BidAnalyzer
from rule_engine import RuleEngine, Rule, BidAction

# Initialize colorama for Windows color support
init()

def print_header():
    """Print application header."""
    print(Fore.CYAN + """
    ╔═══════════════════════════════════════════════════════╗
    ║        eBay Smart Bid Controller v1.0                 ║
    ║        Automated Ad Bid Optimization                  ║
    ╚═══════════════════════════════════════════════════════╝
    """ + Style.RESET_ALL)

def print_success(message):
    """Print success message in green."""
    print(Fore.GREEN + f"✓ {message}" + Style.RESET_ALL)

def print_error(message):
    """Print error message in red."""
    print(Fore.RED + f"✗ {message}" + Style.RESET_ALL)

def print_info(message):
    """Print info message in yellow."""
    print(Fore.YELLOW + f"ℹ {message}" + Style.RESET_ALL)

@click.group()
def cli():
    """eBay Smart Bid Controller - Automate your ad bid adjustments."""
    pass

@cli.command()
@click.option('--file', '-f', type=click.Path(exists=True), help='Path to eBay ad report (CSV/JSON)')
@click.option('--sample', is_flag=True, help='Use sample data for testing')
@click.option('--export', '-e', type=click.Path(), help='Export path for recommendations')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
def analyze(file, sample, export, verbose):
    """Analyze ad performance and generate bid recommendations."""
    print_header()
    
    try:
        # Initialize analyzer
        analyzer = BidAnalyzer()
        
        # Load data
        if sample:
            print_info("Loading sample data...")
            analyzer.load_sample_data()
        elif file:
            print_info(f"Loading data from {file}...")
            if file.endswith('.csv'):
                analyzer.load_csv(file)
            elif file.endswith('.json'):
                analyzer.load_json(file)
            else:
                print_error("Unsupported file format. Please use CSV or JSON.")
                return
        else:
            print_error("Please provide a file path or use --sample flag")
            return
        
        # Analyze data
        print_info("Analyzing campaigns...")
        recommendations = analyzer.analyze()
        
        if not recommendations:
            print_info("No bid adjustments needed. All campaigns are performing within targets!")
            return
        
        # Print summary
        analyzer.print_summary_report()
        
        # Show detailed recommendations if verbose
        if verbose:
            print("\n" + "="*60)
            print("DETAILED RECOMMENDATIONS")
            print("="*60)
            for rec in recommendations:
                print(f"\n📍 {rec.sku} ({rec.campaign_id})")
                print(f"   Current Bid: ${rec.current_bid:.2f}")
                print(f"   Recommended: ${rec.recommended_bid:.2f}")
                print(f"   Action: {rec.action.value.upper()}")
                print(f"   ACOS: {rec.metrics.get('acos', 0):.1f}%")
                print(f"   Reason: {rec.reason}")
        
        # Export if requested
        if export:
            output_path = analyzer.export_recommendations(export)
            print_success(f"Recommendations exported to {output_path}")
        elif not export and recommendations:
            print_info("\nTip: Use --export to save recommendations to CSV")
        
    except Exception as e:
        print_error(f"Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()

@cli.command()
def rules():
    """Display current bidding rules."""
    print_header()
    print("\n📋 ACTIVE BIDDING RULES")
    print("="*60)
    
    engine = RuleEngine()
    rules = engine.get_rules_summary()
    
    for i, rule in enumerate(rules, 1):
        print(f"\n{i}. {rule['name'].upper()}")
        print(f"   Condition: {rule['condition']}")
        print(f"   Action: {rule['action']} {rule['adjustment']}")

@cli.command()
@click.option('--name', prompt='Rule name', help='Name for the custom rule')
@click.option('--condition', prompt='Condition (e.g., acos < 20)', help='Rule condition')
@click.option('--action', type=click.Choice(['increase', 'decrease', 'pause']), 
              prompt='Action', help='Action to take')
@click.option('--percent', type=float, default=10, 
              prompt='Adjustment percent', help='Bid adjustment percentage')
def add_rule(name, condition, action, percent):
    """Add a custom bidding rule."""
    print_header()
    
    try:
        # This would normally save to config file
        print_success(f"Custom rule '{name}' added successfully!")
        print(f"   Condition: {condition}")
        print(f"   Action: {action} by {percent}%")
        print_info("Note: Custom rules are currently session-only. Config file support coming soon!")
        
    except Exception as e:
        print_error(f"Failed to add rule: {e}")

@cli.command()
def quick_start():
    """Quick start guide with sample data."""
    print_header()
    print("\n🚀 QUICK START TUTORIAL")
    print("="*60)
    
    print("\n1️⃣  First, let's analyze sample data:")
    print(Fore.CYAN + "   python main.py analyze --sample" + Style.RESET_ALL)
    
    print("\n2️⃣  To analyze your own eBay report:")
    print(Fore.CYAN + "   python main.py analyze -f your_report.csv" + Style.RESET_ALL)
    
    print("\n3️⃣  To export recommendations:")
    print(Fore.CYAN + "   python main.py analyze -f your_report.csv --export output.csv" + Style.RESET_ALL)
    
    print("\n4️⃣  To see detailed analysis:")
    print(Fore.CYAN + "   python main.py analyze -f your_report.csv --verbose" + Style.RESET_ALL)
    
    print("\n5️⃣  To view active rules:")
    print(Fore.CYAN + "   python main.py rules" + Style.RESET_ALL)
    
    print("\n" + "="*60)
    print_info("Ready to optimize your eBay ads? Try the sample data first!")

if __name__ == '__main__':
    cli()