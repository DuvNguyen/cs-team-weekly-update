"""Print every GSC property developers@ can access, with the EXACT siteUrl string to paste into config.json."""
import json
import auth

config = json.load(open("config.json"))
svc = auth.get_services(config)
sites = svc["webmasters"].sites().list().execute()
for s in sorted(sites.get("siteEntry", []), key=lambda x: x["siteUrl"]):
    print(f'{s["permissionLevel"]:20} {s["siteUrl"]}')
