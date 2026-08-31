"""
Email and notification system for Investment Simulator
"""

import random
from typing import List
from dataclasses import dataclass
from enum import Enum


class EmailType(Enum):
    """Types of emails."""
    NEWS = "news"
    ADVERTISEMENT = "advertisement"
    SCAM = "scam"
    REPORT = "report"
    IPO = "ipo"


@dataclass
class Email:
    """Represents an email message."""
    subject: str
    content: str
    email_type: EmailType
    game_day: int
    read: bool = False


class EmailSystem:
    """Generates and manages in-game emails."""
    
    def __init__(self):
        """Initialize email system."""
        self.emails: List[Email] = []
        
        # Email templates
        self.news_headlines = [
            "MARKETS: Tech stocks surge on strong earnings beat",
            "ECONOMY: Fed maintains interest rate steady amid inflation concerns",
            "CRYPTO: Bitcoin rallies 15% on institutional adoption news",
            "MARKETS: S&P 500 reaches new all-time high",
            "ECONOMY: Jobs report beats expectations with 250K new hires",
            "TECH: Major acquisition sends acquirer stock up 8%",
            "MARKETS: Volatility index drops to 14-month low",
            "ECONOMY: GDP growth stronger than forecast in Q3",
            "COMMODITIES: Oil prices climb on geopolitical tensions",
            "EARNINGS: Tech giants report record quarterly profits",
            "MARKETS: Small-cap stocks outperform large-caps this week",
            "CRYPTO: Ethereum upgrade brings network improvements",
            "FOREX: Dollar strengthens against major currencies",
            "BONDS: Yield curve flattens on rate expectations",
            "HEALTH: Healthcare stocks rally on positive drug trial results",
        ]
        
        self.advertisements = [
            ("💼 Exclusive IPO Opportunity!", "Limited pre-IPO access to TechVision Corp. Early investors seeing 5x returns. Slots filling fast!"),
            ("📈 High-Yield Bond Fund", "Earn 7.5% guaranteed annual returns with our curated bond portfolio. Perfect for conservative investors."),
            ("📊 Daily Forex Trading Signals", "Get actionable forex signals with 87% historical win rate. $99/month subscription."),
            ("🚀 Crypto Wealth Mastery", "Learn the proven strategies successful traders use. 5-week online course, now 50% off!"),
            ("💰 Options Income Strategy", "Generate monthly income from options. Webinar on Thursday at 3 PM ET."),
            ("🏆 Investment Fund Manager", "Let our AI-powered algorithms manage your portfolio. Average returns: 18% annually."),
        ]
        
        self.scams = [
            ("💎 $1000 → $10000 in 30 Days", "Exclusive opportunity for serious investors only! Our secret system GUARANTEES triple digit returns."),
            ("🔐 Insider Trading Circle", "Get access to real insider information about upcoming stock movements. $500 one-time membership."),
            ("🤖 Automated Money Machine", "Set and forget! Our bot trades while you sleep. Guaranteed 50% monthly ROI or money back."),
            ("⚡ Pump & Dump Alert Service", "Get alerts on penny stocks about to explode 500%+. Past returns: 2000%+ annually!"),
            ("🎰 Risk-Free Crypto Arbitrage", "Exploit price differences across exchanges. Can't lose! Start with just $100."),
            ("💸 Inheritance Money Waiting", "You've been selected to receive $5M from an unclaimed estate. Verify with $2000 deposit."),
        ]
        
        self.ipo_announcements = [
            ("🚀 NextGen AI Corp IPO", "Revolutionary AI startup launches IPO next month. Expected to go public at $25/share. Pre-order available."),
            ("💚 GreenEnergy Solutions IPO", "Renewable energy leader going public. Analyst target: $150/share. Limited allocation."),
            ("🏦 FinTech Unicorn IPO Announcement", "Stripe-like fintech raising $1B at $20B valuation. Expected trading begins next quarter."),
            ("🛒 E-Commerce Platform IPO", "Hot new marketplace platform targeting $100M first-day trading. Underwriters suggest high demand."),
        ]
    
    def generate_daily_emails(self, game_day: int) -> List[Email]:
        """Generate random emails for a game day."""
        emails_today = []
        
        # Always get financial news
        subject = random.choice(self.news_headlines)
        content = f"Market Update (Day {game_day}): {subject}. Investors are closely monitoring market trends and economic indicators."
        emails_today.append(Email(
            subject=subject,
            content=content,
            email_type=EmailType.NEWS,
            game_day=game_day
        ))
        
        # 25% chance of additional news
        if random.random() < 0.25:
            subject = random.choice(self.news_headlines)
            content = f"Breaking News (Day {game_day}): {subject}. This could impact your portfolio."
            emails_today.append(Email(
                subject=f"[BREAKING] {subject}",
                content=content,
                email_type=EmailType.NEWS,
                game_day=game_day
            ))
        
        # 25% chance of advertisement (mostly legitimate)
        if random.random() < 0.25:
            subject, content = random.choice(self.advertisements)
            emails_today.append(Email(
                subject=subject,
                content=content,
                email_type=EmailType.ADVERTISEMENT,
                game_day=game_day
            ))
        
        # 8% chance of scam (beware!)
        if random.random() < 0.08:
            subject, content = random.choice(self.scams)
            emails_today.append(Email(
                subject=subject,
                content=f"⚠️ WARNING: This email appears to be a scam. {content}",
                email_type=EmailType.SCAM,
                game_day=game_day
            ))
        
        # 12% chance of IPO announcement
        if random.random() < 0.12:
            subject, content = random.choice(self.ipo_announcements)
            emails_today.append(Email(
                subject=subject,
                content=content,
                email_type=EmailType.IPO,
                game_day=game_day
            ))
        
        # Portfolio report every 7 days
        if game_day % 7 == 0:
            emails_today.append(Email(
                subject=f"📊 Weekly Portfolio Report - Day {game_day}",
                content=f"Review your performance and portfolio composition. Check your total net assets and recent trades.",
                email_type=EmailType.REPORT,
                game_day=game_day
            ))
        
        # Monthly milestone report
        if game_day % 30 == 0:
            month_num = game_day // 30
            emails_today.append(Email(
                subject=f"🎯 Monthly Summary Report - Month {month_num}",
                content=f"One month completed! Review your trading activity, gains/losses, and portfolio allocation.",
                email_type=EmailType.REPORT,
                game_day=game_day
            ))
        
        # Year-end summary
        if game_day == 365:
            emails_today.append(Email(
                subject="🏆 Year-End Summary & Game Complete",
                content="Your one-year investment journey is complete! Review your final portfolio value and see how you performed.",
                email_type=EmailType.REPORT,
                game_day=game_day
            ))
        
        return emails_today
    
    def add_email(self, email: Email):
        """Add an email to the inbox."""
        self.emails.append(email)
    
    def get_unread(self) -> List[Email]:
        """Get all unread emails."""
        return [e for e in self.emails if not e.read]
    
    def mark_as_read(self, email: Email):
        """Mark an email as read."""
        email.read = True
    
    def get_by_type(self, email_type: EmailType) -> List[Email]:
        """Get emails of a specific type."""
        return [e for e in self.emails if e.email_type == email_type]
