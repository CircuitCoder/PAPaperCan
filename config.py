import os
import yaml

curpath = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(curpath, "config.yml")

with open(configPath, 'r') as configFile:
    configStr = configFile.read()
    global config
    config = yaml.load(configStr)
