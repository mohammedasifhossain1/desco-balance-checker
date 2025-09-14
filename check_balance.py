import requests, os, sys
from requests.exceptions import RequestException

def fetch_data():
    ACCOUNT_NO = os.environ["ACCOUNT_NO"]
    URL = "https://prepaid.desco.org.bd/api/tkdes/customer/getBalance"
    params = {"accountNo": ACCOUNT_NO}
    try:
        # Prefer verify=True; if their cert breaks, use False temporarily.
        res = requests.get(URL, params=params, timeout=20, verify=True)
        if not res.ok:
            print(f"[ERROR] DESCO HTTP {res.status_code}: {res.text[:300]}")
            return None
        data = res.json()
        inner = data.get("data")
        if inner is None:
            print(f"[ERROR] No 'data' in response: {data}")
            return None
        balance = inner.get("balance")
        print(f"[INFO] Parsed balance: {balance}")
        return balance
    except RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected: {e}")
        return None

def telegram_notify(balance):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False, "Telegram not configured (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID)"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": f"The current DESCO balance is {balance}"
        }, timeout=20)
        if r.ok:
            return True, "Telegram sent"
        return False, f"Telegram failed: HTTP {r.status_code} {r.text[:300]}"
    except Exception as e:
        return False, f"Telegram failed: {e}"

def main():
    balance = fetch_data()
    if balance is None:
        # Fail the job so you notice in Actions UI
        sys.exit("[FATAL] Balance not found; see logs above.")
    ok, msg = telegram_notify(balance)
    print(f"[TELEGRAM] {msg}")
    if not ok:
        sys.exit("[FATAL] Telegram send failed.")

if __name__ == "__main__":
    main()
