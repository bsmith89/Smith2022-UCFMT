#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import pandas as pd
import numpy as np


if __name__ == "__main__":
    data = pd.read_excel(sys.argv[1], skiprows=1, index_col="#OTU ID")
    data.index.name = "otu_id"
    data.columns.name = "rrs_library_id"
    data = (
        data.drop(columns=["taxonomy"])
        .replace(0, np.nan)
        .stack()
        .astype(int)
        .reorder_levels(["rrs_library_id", "otu_id"])
    )
    data.name = "tally"
    data.to_csv(sys.stdout, sep="\t", header=True)
