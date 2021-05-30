import json
import os

config_file = 'config.json'
config = {}

    
def load_config():
    global config
    if os.path.exists(config_file):
        with open(config_file) as config_text:
            config = json.load(config_text)
    else:
        pass
            
def get_config():
    return config

load_config()

if __name__ == "__main__":
    print(get_config())