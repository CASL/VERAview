#!/bin/bash -a
python test/differences_itest.py \
--ref /Users/re7x/study/casl/andrew/L1_ALL_STATES.h5 pin_powers \
--comp /Users/re7x/study/casl/andrew/L1_ALL_STATES.h5 pin_fueltemps \
-r diff_data \
-t exposure
