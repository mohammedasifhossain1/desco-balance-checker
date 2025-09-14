import os, sys, json, requests
from requests.exceptions import SSLError, RequestException
URL = "https://prepaid.desco.org.bd/api/tkdes/customer/getBalance"

def fetch(account_no: str):
    params = {"accountNo": account_no}
    try:
        # 1) Try with verification (uses REQUESTS_CA_BUNDLE/SSL_CERT_FILE if provided)
        r = requests.get(URL, params=params, timeout=20, verify=True)
        r.raise_for_status()
        return r.json()
    except SSLError as e:
        print(f"[WARN] SSL verify failed: {e}. Retrying without verification…")
        # 2) LAST-RESORT fallback without verify (suppresses warning)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(URL, params=params, timeout=20, verify=False)
        r.raise_for_status()
        return r.json()
    except RequestException as e:
        sys.exit(f"[FATAL] Request failed: {e}")

def send_telegram(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=20)
    if not r.ok:
        sys.exit(f"[FATAL] Telegram failed: {r.status_code} {r.text[:200]}")

def main():
    acct = os.environ["ACCOUNT_NO"]
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat  = os.environ["TELEGRAM_CHAT_ID"]

    data = fetch(acct)
    inner = data.get("data")
    if inner is None:
        sys.exit(f"[FATAL] DESCO returned data=null. Raw: {json.dumps(data)[:400]}")

    msg = (
        "DESCO Balance Update\n"
        f"Account: {inner.get('accountNo')}\n"
        f"Meter: {inner.get('meterNo')}\n"
        f"Balance: {inner.get('balance')}\n"
        f"Month usage: {inner.get('currentMonthConsumption')}\n"
        f"Reading: {inner.get('readingTime')}"
    )
    print("[INFO] " + msg.replace("\n", " | "))
    send_telegram(token, chat, msg)

if __name__ == "__main__":
    main()
