#!/bin/bash

set -m
  
python3 launch_lb.py &
  
cd servers
python3 launch_lb_servers.py
cd ../

fg %1