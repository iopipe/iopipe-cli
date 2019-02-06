import json
import requests

def list(region):
    req = requests.get("https://%s.layers.api.iopipe.com/")
    return json.loads(req.content)