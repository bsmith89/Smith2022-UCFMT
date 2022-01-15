#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from tqdm import tqdm
from collections import Counter


def cut_column(handle, j):
    for line in tqdm(handle):
        fields = line.split('\t')
        yield fields[j]


if __name__ == "__main__":
    tally = Counter(cut_column(sys.stdin, 1))
    for k in tally:
        print(k, tally[k], sep='\t')
