#!/usr/bin/env python2

import pandas as pd
import numpy as np
from collections import namedtuple
from lib.StrainFinder import *
import xarray as xr


class EmptyPileupError(RuntimeError):
    pass


def info(*msg):
    now = datetime.now()
    print now, msg


def idxwhere(condition):
    return list(condition[condition].index)


def is_empty(x):
    return np.prod(x.shape) == 0


def normalize_rows(df):
    return df.divide(df.sum(1), axis=0)


def list_samples(pileup):
    return list(pileup.columns.get_level_values(level="sample_id").unique())


def list_bases(pileup):
    return list(pileup.columns.get_level_values(level="base").unique())


def load_pileup_data(pileup_path):
    flat_data = xr.open_dataarray(pileup_path)
    if is_empty(flat_data):
        raise EmptyPileupError("Pileup data loaded from file is empty.")
    pileup = (
        flat_data
        .isel(species_id=0)
        .to_series()
        .rename_axis(index=("sample_id", "position", "base"))
        .unstack("base")
        .assign(dummy_base_0=0, dummy_base_1=0)
        .unstack("sample_id")
        .reorder_levels(["sample_id", "base"], axis="columns")
        .fillna(0)
        .astype(int)
        .sort_index(axis="columns")
    )
    sample_list = list_samples(pileup)
    base_list = list_bases(pileup)
    assert pileup.shape[1] == len(sample_list) * len(base_list)
    return pileup


def filter_samples(pileup, min_median_coverage):
    median_coverage = pileup.groupby(level="sample_id", axis="columns").sum().median()
    return pileup.loc[:, idxwhere(median_coverage >= min_median_coverage)]


def sample_sites(pileup, n, random_state=0):
    return pileup.sample(n, random_state=random_state)


def get_pileup_dims(pileup):
    n = len(list_samples(pileup))
    a = len(list_bases(pileup))
    g = pileup.shape[0]
    return g, n, a


def pileup_to_model_input(pileup):
    g, n, a = get_pileup_dims(pileup)
    return pileup.values.reshape((g, n, a)).swapaxes(1, 0)


if __name__ == "__main__":
    pileup_path = sys.argv[1]  # 'data/core.100022.pileup.filt.tsv.gz'
    g_sample = int(sys.argv[2])  # 200
    n_strains = int(sys.argv[3])  # 30
    max_reps = int(sys.argv[4])  # 10
    max_time = float(sys.argv[5])  # 3600
    dtol = int(sys.argv[6])  # 1
    ntol = int(sys.argv[7])  # 3
    outpath = sys.argv[8]
    ftol = np.nan

    try:
        pileup = load_pileup_data(pileup_path)
        pileup = filter_samples(pileup, min_median_coverage=1)
        g, n, a = get_pileup_dims(pileup)

        g_sample = min(g_sample, g)
        pileup_sample = sample_sites(pileup, n=g_sample)

        sf_data = pileup_to_model_input(pileup_sample)
        if is_empty(sf_data):
            raise EmptyPileupError("Pileup data is empty after filtering.")
    except EmptyPileupError:
        estimate_strain_rabund = pd.DataFrame(
            [], index=[], columns=["s%0*d" % (3, i + 1) for i in range(n_strains)],
        )
    else:
        em = EM(data=Data(x=sf_data))
        em = em.clear_estimates(keep_n=n_strains)

        em = em.converge_search(
            n=n_strains,
            c=None,
            exhaustive=False,
            robust=False,
            penalty=1.25,
            random=False,
            dtol=dtol,
            ftol=ftol,
            ntol=ntol,
            max_reps=max_reps,
            max_time=max_time,
            log_fn=None,
            out_fn=None,
        )

        # Convergence?  TODO: How to use this result?
        min_fdist = 5e-1
        min_gdist = 5e-1
        detect_limit = 0.001
        converged = em.global_convergence(
            min_reps=3,
            min_gdist=min_gdist,
            min_fdist=min_fdist,
            detect_limit=detect_limit,
        )
        sys.stderr.write("Converged: " + str(converged) + "\n")

        freqs = em.select_best_estimates(1)[0].z
        estimate_strain_rabund = pd.DataFrame(
            freqs,
            index=pileup_sample.columns.get_level_values("sample_id").unique(),
            columns=["s%0*d" % (3, i + 1) for i in range(freqs.shape[1])],
        )

    # Write output
    out = (
        estimate_strain_rabund.stack()
        .rename_axis(index=["sample_id", "strain_id"])
        .rename("fraction")
    )
    out.to_csv(outpath, sep="\t", header=True)
