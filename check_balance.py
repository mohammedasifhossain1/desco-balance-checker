import os, sys, json, requests
URL = "https://prepaid.desco.org.bd/api/tkdes/customer/getBalance"

def fetch_json(account_no: str, timeout=20):
    params = {"accountNo": account_no}
    # 1) Try with TLS verification (uses REQUESTS_CA_BUNDLE/SSL_CERT_FILE if provided)
    try:
        r = requests.get(URL, params=params, timeout=timeout, verify=True)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[WARN] TLS verify or network error: {e}\n[WARN] Retrying WITHOUT certificate verification…")
        # 2) LAST-RESORT: proceed without verification (suppresses warnings)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(URL, params=params, timeout=timeout, verify=False)
        r.raise_for_status()
        return r.json()

def send_telegram(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=20)
    if not r.ok:
        sys.exit(f"[FATAL] Telegram failed: {r.status_code} {r.text[:200]}")

def main():
    acct   = os.environ["ACCOUNT_NO"]
    token  = os.environ["TELEGRAM_BOT_TOKEN"]
    chatid = os.environ["TELEGRAM_CHAT_ID"]

    data = fetch_json(acct)
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
    send_telegram(token, chatid, msg)

if __name__ == "__main__":
    main()
