import os, sys, requests
from requests.exceptions import RequestException, SSLError

URL = "https://prepaid.desco.org.bd/api/tkdes/customer/getBalance"

def fetch_data(account_no: str):
    try:
        r = requests.get(URL, params={"accountNo": account_no}, timeout=20, verify=True)
        if not r.ok:
            sys.exit(f"[FATAL] DESCO HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        inner = data.get("data")
        if inner is None:
            sys.exit("[FATAL] DESCO returned data=null (check account number).")
        return inner
    except SSLError as e:
        # Fallback once without verify if their cert chain glitches
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(URL, params={"accountNo": account_no}, timeout=20, verify=False)
        if not r.ok:
            sys.exit(f"[FATAL] DESCO (no-verify) HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        inner = data.get("data")
        if inner is None:
            sys.exit("[FATAL] DESCO (no-verify) returned data=null.")
        return inner
    except RequestException as e:
        sys.exit(f"[FATAL] Request failed: {e}")

def telegram_send(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=20)
    if not r.ok:
        sys.exit(f"[FATAL] Telegram failed: {r.status_code} {r.text[:200]}")

def main():
    account_no = os.getenv("ACCOUNT_NO")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not account_no or not token or not chat_id:
        sys.exit("[FATAL] Missing ACCOUNT_NO / TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")

    d = fetch_data(account_no)
    balance = d.get("balance")
    msg = (
        "DESCO Balance Update\n"
        f"Account: {d.get('accountNo')}\n"
        f"Meter: {d.get('meterNo')}\n"
        f"Balance: {balance}\n"
        f"Month usage: {d.get('currentMonthConsumption')}\n"
        f"Reading: {d.get('readingTime')}"
    )

    print("[INFO] " + msg.replace("\n", " | "))
    telegram_send(token, chat_id, msg)

if __name__ == "__main__":
    main()
