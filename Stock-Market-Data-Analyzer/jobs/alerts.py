"""Run one LOCAL alert check: python -m jobs.alerts"""
from src.store import check_alerts

if __name__ == "__main__":
    events = check_alerts()
    if not events:
        print("No new alerts for the last saved trading day.")
    for event in events:
        print("ALERT:", event["message"])
