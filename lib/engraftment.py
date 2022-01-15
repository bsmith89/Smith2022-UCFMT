from lib.pandas import idxwhere
import pandas as pd

TAXON_CLASS_ORDER = ["subject", "donor", "shared", "other_donor", "other_nodonor"]


def classify_taxon_sets(sample_x_taxon, subject_sample_id, donor_sample_id, other_donor_samples=None, thresh=0):
    if other_donor_samples is None:
        other_donor_samples = []
    assert subject_sample_id in sample_x_taxon.index
    assert donor_sample_id in sample_x_taxon.index
    taxon_class = pd.DataFrame(
        dict(
            subject=(
                (sample_x_taxon.loc[subject_sample_id] > thresh)
                & (sample_x_taxon.loc[donor_sample_id] <= thresh)
            ),
            donor=(
                (sample_x_taxon.loc[subject_sample_id] <= thresh)
                & (sample_x_taxon.loc[donor_sample_id] > thresh)
            ),
            shared=(
                (sample_x_taxon.loc[subject_sample_id] > thresh)
                & (sample_x_taxon.loc[donor_sample_id] > thresh)
            ),
            other_nodonor=(
                (sample_x_taxon.loc[subject_sample_id] <= thresh)
                & (sample_x_taxon.loc[donor_sample_id] <= thresh)
                & (sample_x_taxon.loc[other_donor_samples] <= thresh).all()
            ),
            other_donor=(
                (sample_x_taxon.loc[subject_sample_id] <= thresh)
                & (sample_x_taxon.loc[donor_sample_id] <= thresh)
                & (sample_x_taxon.loc[other_donor_samples] > thresh).any()
            ),
        )
    )
    assert (taxon_class.sum(1) == 1).all()
    return taxon_class.idxmax(axis=1)
