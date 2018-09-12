#!/bin/sh

echo "flushdb" | redis-cli
echo "flushall" | redis-cli

./seeder.py
./crawler.py
