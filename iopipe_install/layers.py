import json
import requests

def list(region, runtime):
    req = requests.get("https://%s.layers.iopipe.com/get-layers?CompatibleRuntime=%s" % (region, runtime))
    layers_response = json.loads(req.content)
    def get_arn(layer):
        return layer.get("LatestMatchingVersion", {}).get("LayerVersionArn", None)
    return list(map(get_arn, layers_response.get("Layers", [])))