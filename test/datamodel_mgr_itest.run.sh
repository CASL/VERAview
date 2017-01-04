#!/bin/bash -a
python test/datamodel_mgr_itest.py \
/Users/re7x/study/casl/andrew/L1_ALL_STATES.h5 \
/Users/re7x/study/casl/andrew/c1.h5_new.h5 \
-t exposure \
--time-values 0.0 0.5 1.0 2.0 5.0 7.0 10.0 100.0 250.0 \
--mesh-values 5.0 40.0 60.0 100.0 130.0 175.0 200.0 250.0 300.0 325.0 400.0 \
--mesh-indexes 0 5 10 20 30
#> /tmp/out

#core_map differs
#/Users/re7x/study/casl/andrew/c2c22_zinc.ppp.h5 \
#detector_map differs
#/Users/re7x/study/casl/andrew/wb2.h5 \

# /Users/re7x/study/casl/andrew/322depl_r1.h5		15x15x23x177/1
# /Users/re7x/study/casl/andrew/beavrs.h5		17x17x43x56/4
# /Users/re7x/study/casl/andrew/c1.h5			17x17x49x56/4
# /Users/re7x/study/casl/andrew/c1.h5_new.h5		17x17x49x56/4
# /Users/re7x/study/casl/andrew/c2c22_zinc.ppp.h5	17x17x99x56/4
# /Users/re7x/study/casl/andrew/hzp_test3.casl.h5	17x17x52x193/1
# /Users/re7x/study/casl/andrew/L1_ALL_STATESh5		17x17x49x56/4
# /Users/re7x/study/casl/andrew/maps.h5			17x17x1x193/1
# /Users/re7x/study/casl/andrew/maps-fixed.h5		17x17x1x193/1
# /Users/re7x/study/casl/andrew/o3c29nom.h5		15x15x23x177/1
# /Users/re7x/study/casl/andrew/o3c29nom-new.h5		15x15x23x177/1
# /Users/re7x/study/casl/andrew/wb2.h5			17x17x52x56/4
# /Users/re7x/study/casl/andrew/wb2c1_fluxmaps.h5	17x17x1x193/1
