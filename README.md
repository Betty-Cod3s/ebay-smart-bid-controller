# eBay Smart Bid Controller 🎯

Automate your eBay ad bid adjustments with intelligent rule-based optimization. Save time and improve ROAS by letting the tool analyze your ad performance and recommend bid changes.

## 🌟 Features

- **Automated Analysis**: Process 30-day eBay ad reports automatically
- **Smart Rules**: Pre-configured rules based on ACOS, spend, and sales metrics
- **Clear Recommendations**: Get actionable insights with plain English explanations
- **Multiple Formats**: Support for CSV, JSON, and future API integration
- **Export Results**: Save recommendations to CSV for review or bulk upload
- **Customizable**: Add your own rules and thresholds

## 📋 Prerequisites

- Windows 11 (also works on Mac/Linux)
- Python 3.8 or higher
- Visual Studio Code (recommended)

## 🚀 Quick Start

### Step 1: Clone or Download the Project

```bash
git clone https://github.com/Betty-Cod3s/ebay-smart-bid-controller.git
cd ebay-smart-bid-controller
```

Or download and extract the ZIP file.

### Step 2: Set Up Python Environment

Open Terminal/Command Prompt in the project folder:

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Or on Mac/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install pandas numpy pyyaml python-dotenv streamlit openpyxl click colorama
```

### Step 4: Create the File Structure

```bash
# Windows Command Prompt
mkdir src config data data\sample data\exports ui tests

# Windows PowerShell or Mac/Linux
mkdir -p src config data/sample data/exports ui tests
```

### Step 5: Add the Python Files

1. Create `src/rule_engine.py` and paste the Rule Engine code
2. Create `src/bid_analyzer.py` and paste the Bid Analyzer code
3. Create `main.py` in the root directory and paste the CLI code
4. Create empty `src/__init__.py` file

### Step 6: Run Your First Analysis

```bash
# Test with sample data
python main.py analyze --sample

# See the quick start guide
python main.py quick-start

# View active rules
python main.py rules
```

## 📊 Using Your eBay Data

### Preparing Your eBay Ad Report

Your CSV should have these columns (common variations are auto-detected):
- Campaign ID / campaign_id
- SKU / Product SKU
- Current Bid / Max Bid
- Ad Spend / Spend / Cost
- Sales / Orders / Conversions
- Revenue / Sales Revenue
- Clicks
- Impressions

### Running Analysis

```bash
# Basic analysis
python main.py analyze -f your_ebay_report.csv

# With export
python main.py analyze -f your_ebay_report.csv --export recommendations.csv

# Verbose mode for details
python main.py analyze -f your_ebay_report.csv --verbose
```

## 📐 Default Bidding Rules

| Rule | Condition | Action | Explanation |
|------|-----------|--------|-------------|
| **High Performance** | ACOS < 30% | Increase 10% | Profitable ads, scale up |
| **Poor Performance** | ACOS > 30% | Decrease 10% | Unprofitable, reduce spend |
| **No Conversion** | Spend ≥ $10, 0 sales | Pause | Prevent further losses |
| **Low Spend Test** | Spend $5-10, 0 sales | Decrease 20% | Test lower bid |
| **Excellent Performance** | ACOS < 15%, Sales > 5 | Increase 20% | Maximize winners |

## 📁 Sample eBay Report Format

```csv
campaign_id,sku,current_bid,impressions,clicks,ad_spend,sales,revenue
CAM_001,SKU_1001,2.50,5000,150,37.50,5,125.00
CAM_002,SKU_1002,1.75,3000,75,13.13,1,35.00
CAM_003,SKU_1003,3.00,8000,200,60.00,0,0.00
```

## 🎯 Understanding ACOS

**ACOS (Advertising Cost of Sale)** = (Ad Spend ÷ Revenue) × 100

- **< 30%**: Profitable advertising
- **30-50%**: Break-even range
- **> 50%**: Likely unprofitable

## 🔧 Customizing Rules

### Adding Rules via CLI

```bash
python main.py add-rule
# Follow the prompts to add your custom rule
```

### Manual Rule Configuration (Coming Soon)

Edit `config/default_rules.yaml`:

```yaml
rules:
  - name: aggressive_scaling
    condition: "acos < 10 and sales > 10"
    action: increase
    adjustment_percent: 30
    explanation: "Extremely profitable - aggressive scaling"
```

## 📈 Example Output

```
📊 BID ADJUSTMENT SUMMARY REPORT
════════════════════════════════════════════════════════════

📈 Total Recommendations: 15
💰 Current Total Bids: $45.75
💡 Recommended Total Bids: $48.93
📊 Net Change: $3.18 (+6.9%)

🎯 Actions Breakdown:
  ⬆️ Increase: 8 campaigns
  ⬇️ Decrease: 5 campaigns
  ⏸️ Pause: 2 campaigns

🔝 Top 5 Recommendations:
────────────────────────────────────────────────────────────

1. SKU_1001 (CAM_001)
   ⬆️ Action: INCREASE
   💵 Bid: $2.50 → $2.75
   📝 Reason: ACOS is 25.0% (below 30% target), indicating profitable ads.
```

## 🚧 Roadmap

- [x] Core rule engine
- [x] CSV import
- [x] CLI interface
- [ ] Streamlit web UI
- [ ] eBay API integration
- [ ] One-click bid updates
- [ ] Historical tracking
- [ ] A/B testing support
- [ ] Machine learning recommendations

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

MIT License - feel free to use this for your eBay business!

## ⚠️ Disclaimer

This tool provides recommendations based on your configured rules. Always review suggestions before applying them to your live campaigns. The authors are not responsible for any financial outcomes from using this tool.

## 💡 Tips for Success

1. **Start Conservative**: Begin with small bid adjustments (5-10%)
2. **Monitor Daily**: Check results daily when first implementing
3. **Seasonal Adjustments**: Consider seasonal trends in your rules
4. **Product Categories**: Different products may need different ACOS targets
5. **Testing Period**: Allow 7-14 days after changes to see full impact

## 🆘 Troubleshooting

**Import Error**: Make sure you're in the project root directory and virtual environment is activated

**No Recommendations**: Your campaigns might be within target ranges. Check with `--verbose` flag

**CSV Format Issues**: Ensure your CSV has the required columns (see format section)

## 📧 Support

For issues or questions, please create an issue on GitHub or reach out to the community.

---

**Happy Selling! 🛍️** May your ACOS be low and your sales be high!

## 🌟 Installation from GitHub

```bash
# Clone the repository
git clone https://github.com/Betty-Cod3s/ebay-smart-bid-controller.git
cd ebay-smart-bid-controller

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Or on Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test with sample data
python main.py analyze --sample