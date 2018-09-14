local interCount
local unionCount

redis.call("sunionstore", "$$coeff", #KEYS, unpack(KEYS))
unionCount = redis.call("scard", "$$coeff")
redis.call("sinterstore", "$$coeff", #KEYS, unpack(KEYS))
interCount = redis.call("scard", "$$coeff")
redis.call("del", "$$coeff")
return { interCount, unionCount }
