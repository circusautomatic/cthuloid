#!/bin/bash

python 3tcp_serial_redirect.py -P 1338 /dev/limbs 38400 &
python 3tcp_serial_redirect.py -P 1339 /dev/motors 38400

