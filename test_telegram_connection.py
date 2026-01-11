"""
Test Telegram API connectivity and diagnose connection issues.
"""
import asyncio
import requests
import time
from src.config_loader import load_config
from src.telegram_notifier import TelegramNotifier

def test_network_connectivity():
    """Test basic network connectivity to Telegram API."""
    print("=" * 60)
    print("Network Connectivity Test")
    print("=" * 60)
    
    # Test 1: DNS Resolution
    try:
        import socket
        ip = socket.gethostbyname('api.telegram.org')
        print(f"[OK] DNS Resolution: api.telegram.org -> {ip}")
    except Exception as e:
        print(f"[FAIL] DNS Resolution Failed: {e}")
        return False
    
    # Test 2: HTTP Connection
    print("\nTesting HTTPS connection to api.telegram.org:443...")
    start = time.time()
    try:
        response = requests.get('https://api.telegram.org', timeout=10)
        elapsed = time.time() - start
        print(f"[OK] HTTPS Connection: Success (Status: {response.status_code}, Time: {elapsed:.2f}s)")
        return True
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"[FAIL] HTTPS Connection: TIMEOUT after {elapsed:.2f}s")
        print("  -> This indicates a firewall/network block")
        return False
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start
        print(f"[FAIL] HTTPS Connection: FAILED ({type(e).__name__})")
        print(f"  -> Error: {e}")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"[FAIL] HTTPS Connection: UNEXPECTED ERROR ({type(e).__name__})")
        print(f"  -> Error: {e}")
        return False

async def test_telegram_bot():
    """Test Telegram bot connection."""
    print("\n" + "=" * 60)
    print("Telegram Bot Test")
    print("=" * 60)
    
    try:
        config = load_config()
        notifier = TelegramNotifier(config.telegram.bot_token, config.telegram.chat_id)
        
        print(f"Bot Token: {config.telegram.bot_token[:10]}...{config.telegram.bot_token[-5:]}")
        print(f"Chat ID: {config.telegram.chat_id}")
        print("\nAttempting to send test message...")
        
        start = time.time()
        result = await asyncio.wait_for(
            notifier.send_test_message(),
            timeout=15
        )
        elapsed = time.time() - start
        
        if result:
            print(f"[OK] Test Message: SENT successfully (Time: {elapsed:.2f}s)")
            return True
        else:
            print(f"[FAIL] Test Message: FAILED to send (Time: {elapsed:.2f}s)")
            return False
            
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"[FAIL] Test Message: TIMEOUT after {elapsed:.2f}s")
        print("  -> Network connectivity issue or firewall blocking")
        return False
    except Exception as e:
        elapsed = time.time() - start if 'start' in locals() else 0
        print(f"[FAIL] Test Message: ERROR ({type(e).__name__})")
        print(f"  -> Error: {e}")
        return False

def print_solutions():
    """Print solutions for connection issues."""
    print("\n" + "=" * 60)
    print("SOLUTIONS")
    print("=" * 60)
    print("""
If Telegram API is blocked, try these solutions:

1. CHECK FIREWALL/ANTIVIRUS:
   - Temporarily disable Windows Firewall
   - Check if antivirus is blocking HTTPS connections
   - Add Python to firewall exceptions

2. USE VPN/PROXY:
   - Connect to a VPN
   - Configure proxy in TelegramNotifier (requires code changes)
   - Use a different network (mobile hotspot)

3. NETWORK ADMINISTRATOR:
   - Contact network admin to unblock api.telegram.org:443
   - Request firewall rule for Telegram API

4. ALTERNATIVE NOTIFICATION:
   - Use email notifications instead
   - Use webhook/API to another service
   - Use local file logging for alerts

5. TEST FROM DIFFERENT NETWORK:
   - Try from mobile hotspot
   - Test from different location
   - Verify if issue is network-specific
""")

async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TELEGRAM CONNECTION DIAGNOSTICS")
    print("=" * 60)
    
    # Test 1: Network connectivity
    network_ok = test_network_connectivity()
    
    if not network_ok:
        print_solutions()
        return
    
    # Test 2: Telegram bot
    bot_ok = await test_telegram_bot()
    
    if not bot_ok:
        print_solutions()
    
    print("\n" + "=" * 60)
    if network_ok and bot_ok:
        print("[SUCCESS] ALL TESTS PASSED - Telegram is working!")
    else:
        print("[FAILED] SOME TESTS FAILED - See solutions above")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

