import os, sys, json, time, requests

URL = "https://prepaid.desco.org.bd/api/tkdes/customer/getBalance"

def fetch_json(account_no: str, timeout=20):
    params = {"accountNo": str(account_no)}
    # Try verified TLS first (uses REQUESTS_CA_BUNDLE/SSL_CERT_FILE if provided)
    try:
        r = requests.get(URL, params=params, timeout=timeout, verify=True)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[WARN] TLS verify/network error for {account_no}: {e}")
        print("[WARN] Retrying WITHOUT certificate verification…")
        # Last-resort fallback
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(URL, params=params, timeout=timeout, verify=False)
        r.raise_for_status()
        return r.json()

def send_telegram(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": str(chat_id), "text": text}, timeout=20)
    if not r.ok:
        raise RuntimeError(f"Telegram failed: {r.status_code} {r.text[:200]}")

def load_meters():
    """
    Load meters mapping from:
      1) METERS_JSON (secret with a JSON array), or
      2) meters.json file in repo (if METERS_JSON not set).
    Schema:
      [{"name":"Home","account_no":"31363981","chat_id":"1921759057","token":"<optional>"}]
    """
    meters_json = os.getenv("METERS_JSON")
    if meters_json:
        return json.loads(meters_json)
    path = os.getenv("METERS_FILE", "meters.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    default_token = os.environ["TELEGRAM_BOT_TOKEN"]  # fallback token
    meters = load_meters()

    if not isinstance(meters, list) or not meters:
        sys.exit("[FATAL] No meters found. Provide METERS_JSON secret or meters.json file.")

    sent = 0
    failures = []

    for m in meters:
        name = m.get("name") or m.get("account_no")
        acct = m.get("account_no")
        chat = m.get("chat_id")
        token = m.get("token") or default_token

        if not acct or not chat or not token:
            failures.append((name, "missing account_no/chat_id/token"))
            print(f"[WARN] Skipping {name}: missing data")
            continue

        try:
            data = fetch_json(acct)
            inner = data.get("data")
            if inner is None:
                raise RuntimeError(f"DESCO returned data=null (acct={acct})")

            msg = (
                f"DESCO Balance Update — {name}\n"
                f"Account: {inner.get('accountNo')}\n"
                f"Meter: {inner.get('meterNo')}\n"
                f"Balance: {inner.get('balance')}\n"
                f"Month usage: {inner.get('currentMonthConsumption')}\n"
                f"Reading: {inner.get('readingTime')}"
            )

            print(f"[INFO] {name}: balance={inner.get('balance')}")
            send_telegram(token, chat, msg)
            sent += 1
            time.sleep(0.5)  # tiny gap for Telegram rate limits

        except Exception as e:
            failures.append((name, str(e)))
            print(f"[WARN] {name} failed: {e}")

    if sent == 0:
        sys.exit("[FATAL] All meters failed.")
    if failures:
        print(f"[WARN] {len(failures)} meter(s) failed: {failures}")
    else:
        print("[INFO] All meters notified successfully.")

if __name__ == "__main__":
    main()
