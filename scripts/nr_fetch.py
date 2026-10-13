#!/usr/bin/env python3
"""Fetch Nauru legislation (Acts and subsidiary 'laws') from RONLAW, the official online legal
database of the Republic of Nauru (https://ronlaw.gov.nr), via its public search API.
The API returns document metadata plus the per-page text extracted from each official PDF.
Usage: nr_fetch.py RAW_DIR
"""
import json, os, sys, time
import requests

API = "https://ronlaw.gov.nr/api/pdf/"
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
RAW = sys.argv[1]
S = requests.Session()
S.headers["User-Agent"] = UA


def call(method, path, body=None):
    for a in range(6):
        try:
            r = S.request(method, API + path, json=body, timeout=300)
            if r.status_code == 200:
                return r.json()
            print("HTTP", r.status_code, path, file=sys.stderr)
        except Exception as e:
            print("ERR", path, e, file=sys.stderr)
        time.sleep(3 * 2 ** a)
    raise RuntimeError(path)


def main():
    out = os.path.join(RAW, "api")
    os.makedirs(out, exist_ok=True)
    for cat in ("acts", "laws"):
        years = call("GET", f"availableyears/{cat}")
        total = 0
        for y in years:
            p = os.path.join(out, f"{cat}-{y}.json")
            if not os.path.exists(p):
                body = {"query": {"bool": {"must": [{"term": {"category": cat}}, {"term": {"year": y}}]}},
                        "size": 1000}
                d = call("POST", "search", body)
                with open(p, "w") as f:
                    json.dump(d, f)
                time.sleep(1)
            d = json.load(open(p))
            assert d["hits"]["total"]["value"] == len(d["hits"]["hits"]), p
            total += len(d["hits"]["hits"])
        print(cat, total)


if __name__ == "__main__":
    main()
