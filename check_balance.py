import os, sys, requests
from requests.exceptions import RequestException

URL = "https://prepaid.desco.org.bd/api/tkdes/customer/getBalance"
LOW_BALANCE = float(os.getenv("LOW_BALANCE", "100"))  # set via secret if you like

def fetch_data():
    acct = os.environ["ACCOUNT_NO"]
    try:
        r = requests.get(URL, params={"accountNo": acct}, timeout=20, verify=True)
        print(f"[DEBUG] GET {r.url} -> {r.status_code}")
        if not r.ok:
            sys.exit(f"[FATAL] DESCO HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        if data.get("data") is None:
            sys.exit("[FATAL] DESCO returned data=null (check account number / prepaid status).")
        return data["data"]
    except RequestException as e:
        sys.exit(f"[FATAL] Request failed: {e}")

def telegram_send(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat  = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.exit("[FATAL] Telegram secrets missing.")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat, "text": text}, timeout=20)
    print(f"[DEBUG] Telegram -> {r.status_code} {r.text[:200]}")
    if not r.ok:
        sys.exit("[FATAL] Telegram send failed.")

def main():
    d = fetch_data()
    balance = d.get("balance")
    info = (
        f"DESCO Balance Update\n"
        f"Account: {d.get('accountNo')}\n"
        f"Meter: {d.get('meterNo')}\n"
        f"Balance: {balance}\n"
        f"Month usage: {d.get('currentMonthConsumption')}\n"
        f"Reading: {d.get('readingTime')}"
    )
    print("[INFO] " + info.replace("\n", " | "))

    # Always send (or make this conditional)
    telegram_send(info)

    # Optional: extra alert if balance is low
    if balance is not None and float(balance) < LOW_BALANCE:
        telegram_send(f"⚠️ Low DESCO balance: {balance} (threshold {LOW_BALANCE})")

if __name__ == "__main__":
    main()
