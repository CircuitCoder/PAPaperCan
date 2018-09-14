redis.call("zunionstore", "$$search", #KEYS, unpack(KEYS))
local len
local values
len = redis.call("zcard", "$$search")
values = redis.call("zrevrange", "$$search", ARGV[1], ARGV[2])
values[#values + 1] = len
return values
