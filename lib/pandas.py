import pandas as pd


def idxwhere(condition):
    return list(condition[condition].index)


def normalize_rows(df):
    return df.divide(df.sum(1), axis=0)


def align_indexes(*args):
    a0, *aa = args
    idx = set(a0.index)
    for a in aa:
        idx &= set(a.index)

    assert idx
    idx = idxwhere(a0.index.to_series().isin(idx))
    return [a.reindex(idx) for a in args]


def invert_series(x):
    return pd.Series(x.index, index=x.values)
