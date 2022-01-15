#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
from lib.util import info


if __name__ == "__main__":
    path_map = {}
    for arg in sys.argv[1:]:
        library_id, path = arg.split('=')
        path_map[library_id] = path

    npaths = len(path_map)
    info(f'Loading data from {npaths} files.')
    series_list = []
    for library_id in path_map:
        path = path_map[library_id]
        series = (pd.read_table(path,
                                names=['key', 'tally'],
                                index_col=['key'],
                                squeeze=True)
                  .rename(library_id))
        series_list.append(series)

    info('Concatenating input data.')
    data = pd.concat(series_list, axis=1, sort=True)
    data = data.fillna(0).astype(int)

    info('Writing output.')
    (data
     .T
     .stack()
     [lambda x: x > 0]
     .to_csv(sys.stdout, sep='\t', header=False))
