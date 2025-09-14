import os, sys, requests
from requests.exceptions import SSLError, RequestException

URL = "https://prepaid.desco.org.bd/api/tkdes/customer/getBalance"
LOW_BALANCE = float(os.getenv("LOW_BALANCE", "100"))  # set via secret if you like

def get(url, params, ca_bundle=None):
    try:
        return requests.get(url, params=params, timeout=20, verify=(ca_bundle or True))
    except SSLError as e:
        print(f"[WARN] SSL verify failed: {e}. Retrying without verification...")
        # LAST RESORT fallback (not ideal, but unblocks you if server chain is broken)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return requests.get(url, params=params, timeout=20, verify=False)

def fetch_data():
    acct = os.environ["ACCOUNT_NO"]
    ca_bundle = os.getenv("CA_BUNDLE_PATH") or None  # optional
    r = get(URL, {"accountNo": acct}, ca_bundle=ca_bundle)
    if not r.ok:
        sys.exit(f"[FATAL] DESCO HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    inner = data.get("data")
    if inner is None:
        sys.exit("[FATAL] DESCO returned data=null.")
    return inner

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
