import urllib.request
import urllib.parse
import json
import os

def main():
    token = "3da5350b4d7ba82b7a95e08fdcbc105254f20be3"
    params = {
        "since": "2026-06-09T00:00:00Z",
        "until": "2026-06-09T23:59:59Z",
        "limit": 100
    }
    url = "https://api.todoist.com/api/v1/tasks/completed/by_completion_date?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode("utf-8"))
        print(json.dumps(data))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
