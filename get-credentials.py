import gmusicapi

_CREDS_FILE = "./gcreds.json"

print("Performing OAuth authentication - a browser window should open...")
mc = gmusicapi.Mobileclient()
mc.perform_oauth(_CREDS_FILE, open_browser=True)


print(f"\nCredentials file stored at {_CREDS_FILE}\n")
print("Set the following environment variables before running g-monitor.py:\n")
print("   _PUSHOVER_USER_KEY=<your pushover user key>")
print("   _PUSHOVER_API_KEY=<your pushover api key>")
print(f"   _CREDS=$(<{_CREDS_FILE})\n")