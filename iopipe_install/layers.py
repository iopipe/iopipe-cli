import json
import requests

def list(region, runtime):
    req = requests.get("https://%s.layers.api.iopipe.com/get-layers?CompatibleRuntime=%s" % (region, runtime))
    return json.loads(req.content)