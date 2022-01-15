import lib.project_data
import pandas as pd
import numpy as np


DEFAULT_COLOR_PALETTE = {
    "baseline": "darkred",
    "initial_fmt": "blue",
    "followup": "darkgrey",
    "post_antibiotic": "sandybrown",
    "maintenance": "darkslateblue",
    "donor": "purple",
    "ABX+/ENMA": "mediumorchid",
    "ABX-/ENMA": "skyblue",
    "ABX+/CAPS": "darkmagenta",
    "ABX-/CAPS": "royalblue",
    "ABX+": "darkorchid",
    "ABX-": "steelblue",
    "CAPS": "purple",
    "ENMA": "blue",
    "responder": "firebrick",
    "nonresponder": "darkolivegreen",
    'sotu': 'lightcoral',
    'motu': 'dodgerblue',
    'rotu': 'mediumseagreen',
    'ko': 'peru',
    'chem_ba': 'mediumpurple',
    #     "D0044": "green",
    #     "D0485": "orange",
    #     "D0097": "steelblue",
    #     "D0065": "darkmagenta",
    1.0: "pink",
    0.0: "lightblue",
    True: "pink",
    False: "lightblue",
    np.nan: "grey",
    float("nan"): "grey",
}

DEFAULT_MARKER_PALETTE = {
    "baseline": "s",
    "post_antibiotic": "d",
    "maintenance": "o",
    "pre_maintenance_1": "o",
    "pre_maintenance_2": "o",
    "pre_maintenance_3": "o",
    "pre_maintenance_4": "o",
    "pre_maintenance_5": "o",
    "pre_maintenance_6": "o",
    "followup": "X",
    "followup_1": "^",
    "followup_2": "X",
    "followup_3": "X",
    "donor": "D",
    "donor_initial": "D",
    "donor_capsule": "D",
    "donor_mean": "D",
    "donor_enema": "D",
    "D0044": "o",
    "D0097": ">",
    "D0485": "d",
    "D0065": "X",
}

DEFAULT_LINESTYLE_PALETTE = {
    "baseline": ":",
    "maintenance": "None",
    "followup": "-",
}

ARM_ORDER = [
    "ABX-/ENMA",
    "ABX-/CAPS",
    "ABX+/ENMA",
    "ABX+/CAPS",
]

ANTIBIOTICS_ORDER = [
    "ABX-",
    "ABX+",
]

MAINTENANCE_ORDER = [
    "ENMA",
    "CAPS",
]

SAMPLE_TYPE_LABELS = {
    "baseline": "B",
    "pre_maintenance_1": "D1",
    "pre_maintenance_2": "D2",
    "pre_maintenance_3": "D3",
    "pre_maintenance_4": "D4",
    "pre_maintenance_5": "D5",
    "pre_maintenance_6": "D6",
    "followup_1": "F1",
    "followup_2": "F2",
    "followup_3": "F3",
}

OMICS_NAME = {
    "sotu": "Taxonomic (Strain)",
    "motu": "Taxonomic (Species)",
    "rotu": "Taxonomic (ASV)",
    "ko": "Functional (KO)",
    "chem_ba": "BA",
    "family": "Taxonomic (Family)",
}

SAMPLE_TYPE_INDEX = pd.Series(
    {k: v for v, k in enumerate(lib.project_data.SAMPLE_TYPE_ORDER_SIMPLE)}
)


def pvalue_to_annotation(p):
    if np.isnan(p):
        return ""
    elif p > 0.1:
        return ""
    elif p > 0.05:
        return "∙"
    elif p > 0.001:
        return "*"
    else:
        return "**"
