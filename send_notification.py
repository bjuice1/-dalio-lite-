"""
Email notification system for Dalio Lite
Sends daily summaries and rebalance alerts
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import json

def load_notification_config():
    """Load notification configuration"""
    config_file = Path(".notification_config")
    if not config_file.exists():
        return {"ENABLE_EMAIL": False, "USER_EMAIL": ""}

    config = {}
    with open(config_file, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value.lower() == 'true' if value.lower() in ['true', 'false'] else value
    return config

def send_email(subject, body, to_email):
    """Send email notification using Gmail SMTP"""
    # Get credentials from environment
    from_email = os.getenv('NOTIFICATION_EMAIL', 'daliolite@gmail.com')
    password = os.getenv('NOTIFICATION_PASSWORD')

    if not password:
        print("⚠️  NOTIFICATION_PASSWORD not set in .env - email not sent")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Dalio Lite <{from_email}>"
        msg['To'] = to_email

        # Create HTML version
        html = f"""
        <html>
        <body style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;'>
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; color: white; border-radius: 10px 10px 0 0;'>
                <h1 style='margin: 0;'>💰 Dalio Lite</h1>
                <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>{subject}</p>
            </div>
            <div style='padding: 2rem; background: #f7fafc; border-radius: 0 0 10px 10px;'>
                {body}
            </div>
            <div style='text-align: center; padding: 1rem; color: #718096; font-size: 0.875rem;'>
                <p>Dalio Lite Auto-Pilot | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, password)
            server.send_message(msg)

        print(f"✅ Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def send_daily_summary(status, portfolio_value, daily_change, rebalanced=False):
    """Send daily summary email"""
    config = load_notification_config()

    if not config.get("ENABLE_EMAIL"):
        return

    to_email = config.get("USER_EMAIL")
    if not to_email:
        return

    # Create summary
    change_emoji = "📈" if daily_change >= 0 else "📉"
    status_emoji = "✅" if status == "healthy" else "⚠️"

    if rebalanced:
        subject = "🔄 Portfolio Rebalanced Today"
        body = f"""
        <h2>Portfolio Rebalanced</h2>
        <p>Your portfolio was rebalanced today to maintain target allocation.</p>

        <div style='background: white; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <p style='font-size: 1.5rem; margin: 0;'><strong>${portfolio_value:,.2f}</strong></p>
            <p style='color: #718096; margin: 0.25rem 0 0 0;'>Current Portfolio Value</p>
        </div>

        <div style='background: white; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <p style='font-size: 1.5rem; margin: 0; color: {"#48bb78" if daily_change >= 0 else "#f56565"};'>
                <strong>{change_emoji} {daily_change:+.2f}%</strong>
            </p>
            <p style='color: #718096; margin: 0.25rem 0 0 0;'>Today's Change</p>
        </div>

        <p><strong>What happened:</strong> Your portfolio drifted more than 10% from target allocation,
        so the system automatically rebalanced. You're now back on track.</p>

        <p><a href='http://localhost:8502' style='display: inline-block; background: #667eea; color: white;
        padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 8px; margin-top: 1rem;'>
        View Dashboard</a></p>
        """
    else:
        subject = f"{status_emoji} Daily Check Complete - All Good"
        body = f"""
        <h2>Daily Portfolio Check</h2>
        <p>{status_emoji} <strong>Status:</strong> Everything on track. No rebalancing needed.</p>

        <div style='background: white; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <p style='font-size: 1.5rem; margin: 0;'><strong>${portfolio_value:,.2f}</strong></p>
            <p style='color: #718096; margin: 0.25rem 0 0 0;'>Current Portfolio Value</p>
        </div>

        <div style='background: white; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <p style='font-size: 1.5rem; margin: 0; color: {"#48bb78" if daily_change >= 0 else "#f56565"};'>
                <strong>{change_emoji} {daily_change:+.2f}%</strong>
            </p>
            <p style='color: #718096; margin: 0.25rem 0 0 0;'>Today's Change</p>
        </div>

        <p style='color: #718096;'><em>Your portfolio is automatically managed. You don't need to do anything.</em></p>
        """

    send_email(subject, body, to_email)

def send_circuit_breaker_alert(reason):
    """Send alert when circuit breaker is triggered"""
    config = load_notification_config()

    if not config.get("ENABLE_EMAIL"):
        return

    to_email = config.get("USER_EMAIL")
    if not to_email:
        return

    subject = "🛑 CIRCUIT BREAKER TRIGGERED"
    body = f"""
    <h2 style='color: #f56565;'>⚠️ Circuit Breaker Activated</h2>

    <div style='background: #fed7d7; padding: 1rem; border-left: 4px solid #f56565; border-radius: 4px; margin: 1rem 0;'>
        <p style='margin: 0; color: #742a2a;'><strong>Reason:</strong> {reason}</p>
    </div>

    <p>The system has paused all rebalancing to protect your portfolio during unusual market conditions.</p>

    <p><strong>What this means:</strong> Your portfolio experienced significant movement that triggered safety
    protocols. This is designed to prevent trading during extreme volatility when prices may be distorted.</p>

    <p><strong>What to do:</strong></p>
    <ul>
        <li>Review your portfolio in the dashboard</li>
        <li>System will resume normal operations after 24 hours</li>
        <li>Consider if any manual action is needed</li>
    </ul>

    <p><a href='http://localhost:8502' style='display: inline-block; background: #f56565; color: white;
    padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 8px; margin-top: 1rem;'>
    Review Dashboard</a></p>
    """

    send_email(subject, body, to_email)

if __name__ == "__main__":
    # Test notification
    print("Testing notification system...")
    send_daily_summary("healthy", 100000, 0.5, rebalanced=False)
