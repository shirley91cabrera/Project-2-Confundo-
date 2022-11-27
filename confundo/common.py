# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# Copyright 2019 Alex Afanasyev
#

MTU = 412
HEADER_SIZE = 12
MAX_PKT_SIZE = MTU + HEADER_SIZE
MAX_SEQNO = 50000
RETX_TIME = 0.5
FIN_WAIT_TIME = 2.0
SYN_WAIT_TIME = 10.0
INIT_SSTHRESH = 12000
GLOBAL_TIMEOUT = 10.0
READ_BUFFER = 50000
