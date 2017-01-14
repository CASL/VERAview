#!/bin/bash -a
python test/differences_itest.py \
-b /Users/re7x/study/casl/andrew/L1_ALL_STATES.h5 pin_powers \
-s /Users/re7x/study/casl/andrew/L1_ALL_STATES.h5 pin_fueltemps \
-r diff_data \
-t exposure
