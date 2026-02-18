"""
Onboarding Helper Functions for Dalio Lite

Utilities for checking setup status, validating configurations,
and providing guidance to new users.

Usage:
    from onboarding_helpers import check_env_file, generate_env_template

    exists, message = check_env_file()
    if not exists:
        template = generate_env_template()
        # Show template to user
"""

import os
from pathlib import Path
from typing import Tuple, List


def check_env_file() -> Tuple[bool, str]:
    """
    Check if .env file exists and has required keys.

    Returns:
        Tuple of (exists: bool, message: str)
    """
    env_file = Path(".env")

    if not env_file.exists():
        return False, ".env file not found. Create it in the root directory."

    # Check for required keys
    required_keys = ["ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ALPACA_PAPER"]
    missing_keys: List[str] = []

    try:
        with open(env_file, 'r') as f:
            content = f.read()

        for key in required_keys:
            if key not in content or f"{key}=" not in content:
                missing_keys.append(key)

        if missing_keys:
            return False, f"Missing required keys: {', '.join(missing_keys)}"

        return True, "All required keys present"

    except Exception as e:
        return False, f"Error reading .env file: {str(e)}"


def generate_env_template() -> str:
    """
    Generate .env file template for copy-paste.

    Returns:
        String containing complete .env template
    """
    return """# Alpaca API Configuration
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_PAPER=true  # Set to 'false' for live trading

# Optional: Notifications (uncomment to enable)
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional: Logging
# LOG_LEVEL=INFO
"""


def validate_api_key_format(api_key: str, secret_key: str) -> Tuple[bool, str]:
    """
    Validate API key format (not actual connection test).

    Basic validation checks for common formatting issues.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    # Check if keys are empty or just placeholders
    if not api_key or api_key.strip() in ["", "your_api_key_here"]:
        return False, "API key is empty or contains placeholder text"

    if not secret_key or secret_key.strip() in ["", "your_secret_key_here"]:
        return False, "Secret key is empty or contains placeholder text"

    # Check minimum length (Alpaca keys are typically 20+ characters)
    if len(api_key.strip()) < 20:
        return False, "API key appears too short (should be 20+ characters)"

    if len(secret_key.strip()) < 40:
        return False, "Secret key appears too short (should be 40+ characters)"

    # Check for whitespace issues
    if api_key != api_key.strip():
        return False, "API key contains leading or trailing whitespace"

    if secret_key != secret_key.strip():
        return False, "Secret key contains leading or trailing whitespace"

    return True, "Format looks correct (connection test required for full validation)"


def get_setup_progress() -> dict:
    """
    Get current setup progress for onboarding checklist.

    Returns:
        Dictionary with setup status for each step
    """
    progress = {
        "env_file_exists": False,
        "env_file_valid": False,
        "keys_format_ok": False,
        "message": ""
    }

    # Check if .env exists
    env_file = Path(".env")
    progress["env_file_exists"] = env_file.exists()

    if not progress["env_file_exists"]:
        progress["message"] = "Step 3: Create .env file"
        return progress

    # Check if .env is valid
    exists, message = check_env_file()
    progress["env_file_valid"] = exists

    if not exists:
        progress["message"] = message
        return progress

    # Try to validate key formats
    try:
        api_key = os.getenv("ALPACA_API_KEY", "")
        secret_key = os.getenv("ALPACA_SECRET_KEY", "")

        is_valid, validation_msg = validate_api_key_format(api_key, secret_key)
        progress["keys_format_ok"] = is_valid
        progress["message"] = validation_msg if not is_valid else "Ready to connect"
    except Exception:
        progress["message"] = "Unable to read environment variables"

    return progress
