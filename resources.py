import json
drivetrains = {
     "FWD": 0,
     "RWD": 1,
     "AWD": 2
}

default_config = {"port": "",
                  "tcr_drop_rate": "0.005",
                  "tcr_minimum_coefficient": "0.5",
                  "tcr_threshold": "70"}

try:
    with open("config.json", "r") as f:
        config = json.load(f)
except:
    config = default_config
def write_config(new_config):
    with open("config.json", "w") as f:
        json.dump(new_config, f)