#!/bin/bash

set -m
  
python3 lb/launch_lb.py --strategy=$STRATEGY --server_count=$SERVER_COUNT &
  
cd lb/servers
python3 launch_lb_servers.py --server_count=$SERVER_COUNT
cd ../

fg %1