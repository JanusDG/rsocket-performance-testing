#!/bin/bash

set -m
  
python3 lb/launch_lb.py &
  
cd lb/servers
python3 launch_lb_servers.py
cd ../

fg %1