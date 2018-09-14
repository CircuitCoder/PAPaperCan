redis.call("zunionstore", "$$search", #KEYS, unpack(KEYS))

local len
local values

-- Remove source id for recommendations
redis.call("zrem", "$$search", ARGV[3])

len = redis.call("zcard", "$$search")
values = redis.call("zrevrange", "$$search", ARGV[1], ARGV[2])
values[#values + 1] = len
redis.call("del", "$$search")
return values
