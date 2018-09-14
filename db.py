from config import config
import redis

print(config)

conn = redis.StrictRedis(
        host = config['db']['host'],
        port = config['db']['port'],
        db = config['db']['use'])

wordConn = redis.StrictRedis(
        host = config['db']['host'],
        port = config['db']['port'],
        db = config['db']['wordUse'])

lookupConn = redis.StrictRedis(
        host = config['db']['host'],
        port = config['db']['port'],
        db = config['db']['lookupUse'])
