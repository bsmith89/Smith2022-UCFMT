#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from lib.util import info
import pandas as pd
from collections import defaultdict
from tqdm import tqdm


if __name__ == "__main__":
    mapper_path = sys.argv[1]

    info('Loading mapper.')
    with open(mapper_path) as f:
        mapper = dict(line.strip().split() for line in f)

    info('Aggregating input.')
    out = defaultdict(int)
    for line in tqdm(sys.stdin):
        in_id, tally = line.strip().split()
        tally = int(tally)
        if in_id in mapper:
            out[mapper[in_id]] += tally

    info('Writing output.')
    for k in tqdm(out):
        print(k, out[k], sep='\t')
