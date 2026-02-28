#!/usr/bin/env python3
"""
OAuth 1.0a Authorization Helper
================================
Authorizes any persona account to post via the @devunfiltered_ developer app.
The resulting Access Token + Secret are saved directly to .env.

Usage:
    python3 authorize_persona.py <persona_name>

Examples:
    python3 authorize_persona.py zawadi   → authorize @nakszawadi
    python3 authorize_persona.py baraka   → authorize @barak00254
    python3 authorize_persona.py zuri     → authorize @zuriadhiambo_
    python3 authorize_persona.py john     → authorize @njuguna_atl
    python3 authorize_persona.py karen    → authorize @karenkips_

How it works:
    1. Opens X's authorization URL in your browser
    2. You log in as the PERSONA's Twitter account (e.g. @nakszawadi)
    3. X shows you a 7-digit PIN → paste it here
    4. Access Token + Secret are saved to .env automatically

Prerequisites:
    • Each persona's app must have "Read and Write" permissions on developer.x.com
    • OAuth 1.0a must be enabled on the app (User Authentication Settings)
    • Callback URL can be anything or set to "https://x.com" — PIN flow doesn't use it
"""

import os
import re
import sys
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Mapping: persona name → .env prefix and X handle ─────────────────────────
PERSONAS = {
    "juma":    {"prefix": "KAMAU",   "handle": "@kamaukeeeraw"},
    "kamau":   {"prefix": "KAMAU",   "handle": "@kamaukeeeraw"},
    "amani":   {"prefix": "WANJIKU", "handle": "@wanjikusagee"},
    "wanjiku": {"prefix": "WANJIKU", "handle": "@wanjikusagee"},
    "baraka":  {"prefix": "BARAKA",  "handle": "@barak00254"},
    "zawadi":  {"prefix": "ZAWADI",  "handle": "@nakszawadi"},
    "zuri":    {"prefix": "ZURI",    "handle": "@zuriadhiambo_"},
    "john":    {"prefix": "JOHN",    "handle": "@njuguna_atl"},
    "karen":   {"prefix": "KAREN",   "handle": "@karenkips_"},
}


def save_tokens_to_env(prefix: str, access_token: str, access_token_secret: str) -> bool:
    """Overwrite the ACCESS_TOKEN and ACCESS_TOKEN_SECRET lines in .env."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found in current directory.")
        return False

    content = env_path.read_text()

    # Replace existing token lines (placeholder or real)
    content = re.sub(
        rf"^{prefix}_ACCESS_TOKEN=.*$",
        f"{prefix}_ACCESS_TOKEN={access_token}",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        rf"^{prefix}_ACCESS_TOKEN_SECRET=.*$",
        f"{prefix}_ACCESS_TOKEN_SECRET={access_token_secret}",
        content,
        flags=re.MULTILINE,
    )

    env_path.write_text(content)
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print(f"Available personas: {', '.join(sorted(set(v['handle'] for v in PERSONAS.values())))}")
        sys.exit(1)

    persona_name = sys.argv[1].lower().strip()
    info = PERSONAS.get(persona_name)

    if not info:
        print(f"❌ Unknown persona: '{persona_name}'")
        print(f"   Available: {', '.join(sorted(PERSONAS.keys()))}")
        sys.exit(1)

    prefix = info["prefix"]
    handle = info["handle"]

    consumer_key = os.getenv(f"{prefix}_CONSUMER_KEY", "")
    consumer_secret = os.getenv(f"{prefix}_CONSUMER_SECRET", "")

    if not consumer_key or not consumer_secret:
        print(f"❌ Missing {prefix}_CONSUMER_KEY or {prefix}_CONSUMER_SECRET in .env")
        sys.exit(1)

    print()
    print("=" * 60)
    print(f"  🔑 OAuth Authorization: {persona_name.title()} ({handle})")
    print(f"     App prefix : {prefix}")
    print(f"     Consumer   : {consumer_key[:8]}...")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT — Before the browser opens:")
    print(f"   Make sure you are logged into X as {handle}")
    print(f"   (NOT as @devunfiltered_ or any other account)")
    print(f"   Switch accounts on x.com first if needed.")
    print()
    input("Press Enter when you're ready to open the browser...")

    try:
        import tweepy
    except ImportError:
        print("❌ tweepy not installed. Run: pip install tweepy")
        sys.exit(1)

    # ── Step 1: Get request token + authorization URL ──────────────────────────
    handler = tweepy.OAuth1UserHandler(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        callback="oob",   # PIN-based flow (out-of-band)
    )

    try:
        auth_url = handler.get_authorization_url(signin_with_twitter=False)
    except tweepy.TweepyException as e:
        print(f"❌ Could not get authorization URL: {e}")
        print()
        print("Possible causes:")
        print("  • The app doesn't have OAuth 1.0a enabled")
        print("  • The app permissions are set to 'Read only' (needs Read+Write)")
        print(f"  → Fix at: https://developer.x.com/en/portal/apps")
        sys.exit(1)

    print()
    print(f"Opening browser to authorize {handle}...")
    print(f"URL: {auth_url}")
    print()
    webbrowser.open(auth_url)

    # ── Step 2: User gets the PIN ──────────────────────────────────────────────
    print("After you approve in the browser, X will show a 7-digit PIN.")
    print()
    pin = input("Enter the PIN: ").strip()

    if not pin or not pin.isdigit():
        print("❌ Invalid PIN. Aborting.")
        sys.exit(1)

    # ── Step 3: Exchange PIN for Access Token ──────────────────────────────────
    print()
    print("Exchanging PIN for Access Token...")
    try:
        access_token, access_token_secret = handler.get_access_token(pin)
    except tweepy.TweepyException as e:
        print(f"❌ Failed to get Access Token: {e}")
        print("   Make sure the PIN is correct and was entered quickly (they expire).")
        sys.exit(1)

    print(f"✅ Got Access Token!")
    print(f"   Token  : {access_token[:25]}...")
    print(f"   Secret : {access_token_secret[:12]}...")

    # ── Step 4: Quick verify — who are we? ────────────────────────────────────
    print()
    print("Verifying account identity...")
    try:
        client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        me = client.get_me()
        verified_username = f"@{me.data.username}" if me and me.data else "unknown"
        print(f"   Authenticated as: {verified_username}")

        if verified_username.lower() != handle.lower():
            print()
            print(f"⚠️  WARNING: Expected {handle} but got {verified_username}")
            print(f"   You may have been logged in as the wrong account.")
            confirm = input("   Save anyway? (y/N): ").strip().lower()
            if confirm != "y":
                print("Aborted. Please switch to the correct account and try again.")
                sys.exit(1)
    except Exception as e:
        print(f"   (Could not verify account: {e} — saving anyway)")

    # ── Step 5: Save to .env ───────────────────────────────────────────────────
    print()
    if save_tokens_to_env(prefix, access_token, access_token_secret):
        print(f"✅ Saved to .env:")
        print(f"   {prefix}_ACCESS_TOKEN={access_token[:25]}...")
        print(f"   {prefix}_ACCESS_TOKEN_SECRET={access_token_secret[:12]}...")
    else:
        print("❌ Could not save to .env — here are your tokens to add manually:")
        print(f"   {prefix}_ACCESS_TOKEN={access_token}")
        print(f"   {prefix}_ACCESS_TOKEN_SECRET={access_token_secret}")

    print()
    print("=" * 60)
    print(f"🎉 {persona_name.title()} ({handle}) is now authorized!")
    print(f"   Test with: python3 dry_run.py")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
