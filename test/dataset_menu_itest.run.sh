 #!/bin/bash -a
 test/dataset_menu_itest.py -f \
     /Users/re7x/study/casl/andrew/c1.h5_new.h5 \
     /Users/re7x/study/casl/andrew/L1_ALL_STATES.h5 \
     --pullright-mode 'subsingle' \
     --pullright-types channel detector pin :axial :radial :assembly :core scalar \
     --popup-mode 'selected' \
     --popup-types channel pin :axial :radial

#     --pullright-types channel detector pin pin:axial pin:radial pin:assembly pin:core scalar
#     --popup-types channel pin pin:axial pin:radial
