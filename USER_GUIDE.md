# Investment Simulator - User Guide

## Welcome to Investment Simulator!

Investment Simulator is a one-year investment simulation game where you manage $10,000 and navigate the dynamic world of stocks, cryptocurrencies, bonds, and more. The goal is to maximize your portfolio value by the end of the year.

## Getting Started

### Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Game

#### GUI Version (Pygame)
```bash
python3 main.py
```

#### CLI Version (Text-based)
```bash
python3 cli_game.py
```

## Game Rules

### Starting Conditions
- **Starting Balance**: $10,000
- **Game Duration**: 365 days (1 year)
- **Operations Per Day**: Maximum 2 trades per day

### Trading

You can **buy** or **sell** various investment assets:

#### Available Asset Types

1. **Stocks** - Traditional company shares
   - AAPL (Apple)
   - GOOGL (Google)
   - MSFT (Microsoft)
   - TSLA (Tesla)
   - NVDA (NVIDIA)
   - AMZN (Amazon)
   - And more...

2. **Cryptocurrencies** - Digital assets
   - BTC (Bitcoin)
   - ETH (Ethereum)
   - SOL (Solana)
   - XRP (Ripple)
   - ADA (Cardano)

3. **Bonds** - Fixed income securities
   - USA3M (3-Month US Treasury)
   - AUS3M (3-Month Australian Government Bond)
   - GBR3M, JPN3M, DEU3M (3-Month UK, Japanese, and German Government Bonds)
   - Bonds cannot be sold until 90 simulated days after purchase.

4. **ETFs** - Exchange-traded funds
   - SPY (S&P 500)
   - QQQ (Nasdaq-100)
   - IWM (Russell 2000)

5. **Forex** - Currency pairs
   - EURUSD (Euro/Dollar)
   - GBPUSD (Pound/Dollar)

### Market Mechanics

- **Market Updates**: Prices update daily based on realistic market simulation
- **Market Trends**: Bull markets increase stock prices; bear markets decrease them
- **Volatility**: Some assets are more volatile than others (crypto > growth stocks > bonds)
- **Random Events**: Economic news, earnings surprises, and black swan events affect prices

### Portfolio Management

- **Long Positions**: Buy and hold assets for potential gains
- **Dividend Reinvestment**: Bonds provide steady income
- **Diversification**: Spread investments across different asset types to manage risk
- **Tax Considerations**: Game doesn't include taxes for simplicity

## Game Features

### Email System

You'll receive various types of emails throughout the game:

1. **News Emails** 🗞️
   - Market updates and economic data
   - Major news events affecting markets
   - These can signal good or bad trading opportunities

2. **Advertisements** 📢
   - Investment fund promotions
   - IPO announcements
   - Trading service offers

3. **Scam Emails** ⚠️
   - Suspicious investment schemes
   - Get-rich-quick offers
   - Fake insider trading tips
   - **Avoid these!**

4. **Reports** 📊
   - Weekly portfolio summaries
   - Monthly performance reviews
   - Year-end final report

### Market Events

Random events occur approximately every 10 days:

- **Bull Markets**: Tech and growth stocks surge
- **Bear Markets**: General market decline
- **Interest Rate Changes**: Affect bond and stock prices
- **Crypto Rallies**: Cryptocurrency prices surge
- **Black Swan Events**: Major negative market shocks

## Strategy Tips

### Beginner Tips
1. **Diversify**: Don't put all money in one asset
2. **Dollar Cost Averaging**: Buy regularly rather than all at once
3. **Long-term Focus**: Don't panic sell on bad days
4. **Read Your Emails**: Market news can signal good entry/exit points

### Intermediate Strategies
1. **Buy the Dip**: Wait for price drops to buy quality assets
2. **Profit Taking**: Sell winners when they've gained 20-30%
3. **Sector Rotation**: Switch between tech, bonds, and crypto based on market conditions
4. **Bonds as Stability**: Use bonds to hedge against stock market volatility

### Advanced Strategies
1. **Correlation Trading**: Buy assets that move opposite to each other
2. **Volatility Trading**: Make larger bets when VIX is high
3. **Event Driven**: React quickly to breaking news
4. **Rebalancing**: Regularly adjust portfolio to target allocations

## Frequently Asked Questions

**Q: Can I lose all my money?**
A: No, the game doesn't allow negative balances. If you don't have enough cash to buy, the transaction is rejected.

**Q: What if I miss the perfect trade?**
A: The game runs for a full year with many opportunities. Focus on consistent good decisions rather than perfect timing.

**Q: Are there real money losses?**
A: No, this is a simulation. Your real money is not at risk.

**Q: Can I save my progress?**
A: Yes! Use the save feature in the GUI or CLI version. Saves are stored locally.

**Q: What's the winning strategy?**
A: Aim to outperform the S&P 500 (~10% annual returns). The best strategy depends on market conditions!

## Technical Documentation

See `TECHNICAL.md` for developer information and API documentation.

## Credits

Investment Simulator - Academic Project
