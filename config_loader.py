import os
import yaml


def load_config():
    with open("config.yml", "r") as f:
        cfg = yaml.safe_load(f)
    
    # Override with local config if it exists
    if os.path.exists("config.local.yml"):
        with open("config.local.yml", "r") as f:
            local_cfg = yaml.safe_load(f)
            if local_cfg:
                cfg.update(local_cfg)
    
    return cfg
