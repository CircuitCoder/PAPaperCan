redis.call("zunionstore", "$$search", #KEYS, unpack(KEYS))

local len
local values

-- Remove source id for recommendations
redis.call("zrem", "$$search", ARGV[3])

if #ARGV > 3 then
  for i, k in ipairs(redis.call('zrange', "$$search", 0, -1)) do
    redis.call('select', ARGV[6])
    local time
    time = redis.call("hget", "time", k)
    redis.call('select', ARGV[7])
    if (time < ARGV[4]) or (time > ARGV[5]) then
      redis.call("zrem", "$$search", k)
      redis.log(3, "REM")
    end
  end
end

len = redis.call("zcard", "$$search")
values = redis.call("zrevrange", "$$search", ARGV[1], ARGV[2])
values[#values + 1] = len
redis.call("del", "$$search")
return values
