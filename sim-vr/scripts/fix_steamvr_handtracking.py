import json

path = "/home/user/.steam/debian-installation/config/steamvr.vrsettings"
with open(path) as f:
    cfg = json.load(f)
cfg.setdefault("driver_alvr_server", {})["handTrackingEnabled"] = True
cfg.setdefault("steamvr", {}).update({"enableHandTracking": True, "handTrackingEnabled": True})
with open(path, "w") as f:
    json.dump(cfg, f, indent=3)
print("Done - hand tracking enabled in steamvr.vrsettings")
