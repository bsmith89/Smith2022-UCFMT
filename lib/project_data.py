import pandas as pd
import sqlite3
from skbio.stats.distance import anosim as skb_anosim
from skbio.stats.distance import DistanceMatrix
import lib.stats
from lib.pandas import idxwhere


SAMPLE_TYPE_ORDER = [
    "baseline",
    "post_antibiotic",
    "pre_maintenance_1",
    "pre_maintenance_2",
    "pre_maintenance_3",
    "pre_maintenance_4",
    "pre_maintenance_5",
    "pre_maintenance_6",
    "followup_1",
    "followup_2",
    "followup_3",
]

SAMPLE_TYPE_ORDER_SIMPLE = [
    "baseline",
    "pre_maintenance_1",
    "pre_maintenance_2",
    "pre_maintenance_3",
    "pre_maintenance_4",
    "pre_maintenance_5",
    "pre_maintenance_6",
    "followup_1",
    "followup_2",
]

SAMPLE_TYPE_ORDER_WITH_DONOR = [
    "baseline",
    "post_antibiotic",
    "pre_maintenance_1",
    "pre_maintenance_2",
    "pre_maintenance_3",
    "pre_maintenance_4",
    "pre_maintenance_5",
    "pre_maintenance_6",
    "followup_1",
    "followup_2",
    "followup_3",
    "donor_initial",
    "donor_capsule",
    "donor_enema",
]


sample_type_to_sample_class = {
    "baseline": "baseline",
    "post_antibiotic": "post_antibiotic",
    "pre_maintenance_1": "maintenance",
    "pre_maintenance_2": "maintenance",
    "pre_maintenance_3": "maintenance",
    "pre_maintenance_4": "maintenance",
    "pre_maintenance_5": "maintenance",
    "pre_maintenance_6": "maintenance",
    "followup_1": "followup",
    "followup_2": "followup",
    "followup_3": "followup",
    "donor_initial": "donor",
    "donor_capsule": "donor",
    "donor_mean": "donor",
    "donor_enema": "donor",
}

VISIT_TYPE_ORDER = [
    "colonoscopy_1",
    "maintenance_1",
    "maintenance_2",
    "maintenance_3",
    "maintenance_4",
    "maintenance_5",
    "maintenance_6",
    "colonoscopy_2",
    "followup_1_month",
    "followup_3_month",
]


RECIPIENT_SUMMARIZE_COLUMNS = [
    "arm",
    "sex",
    "donor_subject_id",
    "withdrawal_due_to_failure",
    "mayo_total_start",
    "mayo_total_end",
    "remission",
    "responder",
]


def taxonomy_to_series(taxonomy):
    return (
        pd.Series(
            taxonomy.split(";"),
            index=["d__", "p__", "c__", "o__", "f__", "g__", "s__"],
        )
        + ";"
    ).cumsum()


def load_recipient_x_sample_type_table(con):
    subject_x_sample_type = pd.read_sql(
        """
    SELECT
        sample_id
      , subject_id
      , sample_type
      , collection_days_post_fmt AS days_post_fmt
    FROM sample JOIN subject USING (subject_id)
    WHERE recipient
        """,
        con=con,
        index_col=["subject_id", "sample_type"],
    ).sort_index()

    return subject_x_sample_type


def load_sample_table(con):
    sample = pd.read_sql(
        """
            SELECT
                sample_id
              , subject_id
              , sample_group
              , sample_type
              , sample_weight
              , sample_notes
              , collection_days_post_fmt AS days_post_fmt
            FROM sample
            JOIN subject USING (subject_id)

            UNION

            SELECT DISTINCT
                subject_id || '_mean' AS sample_id
              , subject_id
              , 'donor' AS sample_group
              , 'donor_mean' AS sample_type
              , NULL AS sample_weight
              , '' AS sample_notes
              , NULL AS days_post_fmt
            FROM sample
            JOIN subject USING (subject_id)
            WHERE NOT recipient
            GROUP BY subject_id
            """,
        con=con,
        index_col="sample_id",
    ).assign(sample_class=lambda x: x.sample_type.map(sample_type_to_sample_class))
    #     subject_x_sample_type = load_recipient_x_sample_type_table(con)

    #     sample = (
    #         subject_x_sample_type.reset_index()
    #         .set_index("sample_id")
    #         .sort_values(["subject_id", "days_post_fmt"])
    #         .assign(sample_class=lambda x: x.sample_type.map(sample_type_to_sample_class))
    #     )
    return sample


def load_subject_x_visit_type_table(con):
    subject_x_visit_type = (
        pd.read_sql(
            """
    SELECT
        visit_id
      , subject_id
      , visit_type AS visit_class
      , visit_type_specific AS visit_type
      , days_post_fmt
      , status_mayo_score_stool_frequency
      , status_mayo_score_rectal_bleeding
      , status_mayo_score_endoscopy_mucosa
      , status_mayo_score_global_physician_rating
      , visit_notes
    FROM visit JOIN subject USING (subject_id)
        """,
            con=con,
            index_col=["subject_id", "visit_type"],
        )
        .assign(
            status_mayo_score_total=lambda x: (
                x.status_mayo_score_rectal_bleeding
                + x.status_mayo_score_stool_frequency
                + x.status_mayo_score_endoscopy_mucosa
                + x.status_mayo_score_global_physician_rating
            ),
            status_mayo_score_partial=lambda x: (
                x.status_mayo_score_rectal_bleeding
                + x.status_mayo_score_stool_frequency
            ),
        )
        .sort_index()
    )

    return subject_x_visit_type


def load_sample_x_rotu_cvrg_table(con):
    sample_x_rotu = (
        pd.read_sql(
            """
    SELECT
        sample_id
      , rrs_otu_id AS rotu_id
      , SUM(tally) AS tally
    FROM rrs_x_rotu_count
    JOIN rrs USING (rrs_id)
    WHERE sample_id IS NOT NULL
    GROUP BY sample_id, rrs_otu_id

    UNION

    -- Construct donor means
    SELECT
        subject_id || '_mean' AS sample_id
      , rrs_otu_id AS rotu_id
      , SUM(tally) AS tally
    FROM rrs_x_rotu_count
    JOIN rrs USING (rrs_id)
    JOIN sample USING (sample_id)
    JOIN subject USING (subject_id)
    WHERE sample_id IS NOT NULL
      AND NOT recipient
    GROUP BY subject_id, rrs_otu_id
    """,
            con=con,
            index_col=["sample_id", "rotu_id"],
        )
        .squeeze()
        .unstack("rotu_id", fill_value=0)
    )
    return sample_x_rotu


def load_sample_x_rotu_rabund_table(con):
    return load_sample_x_rotu_cvrg_table(con).apply(lib.stats.normalize, axis=1)


def load_sample_x_ko_table(con):
    sample_x_ko = (
        pd.read_sql(
            """
    SELECT
        sample_id
      , annot_id
      , tally
    FROM sample_x_annot
    WHERE annot_type='ko'

    UNION

    -- Construct donor means
    SELECT
        subject_id || '_mean' AS sample_id
      , annot_id
      , SUM(tally) AS tally
    FROM sample_x_annot
    JOIN sample USING (sample_id)
    JOIN subject USING (subject_id)
    WHERE annot_type='ko'
      AND NOT recipient
    GROUP BY subject_id, annot_id
    """,
            con=con,
            index_col=["sample_id", "annot_id"],
        )
        .squeeze()
        .unstack("annot_id", fill_value=0)
    )
    return sample_x_ko


def load_sample_x_keggmodule_table(con):
    sample_x_keggmodule = (
        pd.read_sql(
            """
    SELECT
        sample_id
      , annot_id
      , tally
    FROM sample_x_annot
    WHERE annot_type='keggmodule'

    UNION

    -- Construct donor means
    SELECT
        subject_id || '_mean' AS sample_id
      , annot_id
      , SUM(tally) AS tally
    FROM sample_x_annot
    JOIN sample USING (sample_id)
    JOIN subject USING (subject_id)
    WHERE annot_type='keggmodule'
      AND NOT recipient
    GROUP BY subject_id, annot_id
    """,
            con=con,
            index_col=["sample_id", "annot_id"],
        )
        .squeeze()
        .unstack("annot_id", fill_value=0)
    )
    return sample_x_keggmodule


def load_sample_x_eggnog_table(con):
    sample_x_eggnog = (
        pd.read_sql(
            """
    SELECT
        sample_id
      , annot_id
      , tally
    FROM sample_x_annot
    WHERE annot_type='eggnog'

    UNION

    -- Construct donor means
    SELECT
        subject_id || '_mean' AS sample_id
      , annot_id
      , SUM(tally) AS tally
    FROM sample_x_annot
    JOIN sample USING (sample_id)
    JOIN subject USING (subject_id)
    WHERE annot_type='eggnog'
      AND NOT recipient
    GROUP BY subject_id, annot_id
    """,
            con=con,
            index_col=["sample_id", "annot_id"],
        )
        .squeeze()
        .unstack("annot_id", fill_value=0)
    )
    return sample_x_eggnog


def load_sample_x_motu_cvrg_table(con):
    sample_x_motu = (
        pd.read_sql(
            """
    SELECT sample_id, motu_id, coverage FROM sample_x_motu

    UNION

    -- Construct donor means
    SELECT
        subject_id || '_mean' AS sample_id
      , motu_id
      , SUM(coverage) AS coverage
    FROM sample_x_motu
    JOIN sample USING (sample_id)
    JOIN subject USING (subject_id)
    WHERE NOT recipient
    GROUP BY subject_id, motu_id
    """,
            con=con,
            index_col=["sample_id", "motu_id"],
        )
        .squeeze()
        .unstack("motu_id", fill_value=0)
    )
    return sample_x_motu


def load_sample_x_motu_rabund_table(con):
    return load_sample_x_motu_cvrg_table(con).apply(lib.stats.normalize, axis=1)


def load_sample_x_sotu_cvrg_table(con):
    sample_x_sotu = (
        pd.read_sql(
            """
    SELECT sample_id, sotu_id, coverage FROM sample_x_sotu

    UNION

    -- Construct donor means
    SELECT
        subject_id || '_mean' AS sample_id
      , sotu_id
      , SUM(coverage) AS coverage
    FROM sample_x_sotu
    JOIN sample USING (sample_id)
    JOIN subject USING (subject_id)
    WHERE NOT recipient
    GROUP BY subject_id, sotu_id
    """,
            con=con,
            index_col=["sample_id", "sotu_id"],
        )
        .squeeze()
        .unstack("sotu_id", fill_value=0)
    )
    return sample_x_sotu


def load_sample_x_sotu_rabund_table(con):
    return load_sample_x_sotu_cvrg_table(con).apply(lib.stats.normalize, axis=1)


def load_sample_x_chem_table(con):
    sample_x_chem = (
        pd.read_sql(
            """
    SELECT chem_id, sample_id, peak_area
    FROM sample_x_chem
    """,
            con=con,
            index_col=["chem_id", "sample_id"],
        )
        .squeeze()
        .unstack("chem_id", fill_value=0)
    )
    return sample_x_chem


def load_sample_x_chem_ba_table(con):
    sample_x_chem_ba = (
        pd.read_sql(
            """
    SELECT chem_id, sample_id, peak_area
    FROM chem_abt_bile_acid
    JOIN sample_x_chem USING (chem_id)
    """,
            con=con,
            index_col=["chem_id", "sample_id"],
        )
        .squeeze()
        .unstack("chem_id", fill_value=0)
    )
    return sample_x_chem_ba


def load_subject_table(con):
    visit = load_subject_x_visit_type_table(con)

    subject = pd.read_sql(
        """
    SELECT
        subject_id
      , recipient
      , sex
      , donor_subject_id
      , treatment_abx_pre
      , treatment_maintenance_method
      , withdrawal_due_to_failure
    FROM subject
    """,
        con=con,
        index_col="subject_id",
    )
    subject["recipient"] = subject["recipient"].astype(bool)
    subject["withdrawal_due_to_failure"] = subject["withdrawal_due_to_failure"].astype(
        "boolean"
    )
    subject["treatment_abx_pre"] = subject["treatment_abx_pre"].astype("boolean")
    subject["antibiotics_"] = subject["treatment_abx_pre"].map(
        {True: "ABX+", False: "ABX-"}
    )
    subject["maintenance_"] = subject["treatment_maintenance_method"].map(
        {"capsules": "CAPS", "enema": "ENMA"}
    )

    subject["arm"] = subject["antibiotics_"] + "/" + subject["maintenance_"]
    subject["mayo_total_start"] = visit.status_mayo_score_total.xs(
        "colonoscopy_1", level="visit_type"
    )
    subject["mayo_total_end"] = visit.status_mayo_score_total.xs(
        "colonoscopy_2", level="visit_type"
    )
    subject["mayo_total_change"] = subject.mayo_total_end - subject.mayo_total_start
    subject["mayo_endo_start"] = visit.status_mayo_score_endoscopy_mucosa.xs(
        "colonoscopy_1", level="visit_type"
    )
    subject["mayo_endo_end"] = visit.status_mayo_score_endoscopy_mucosa.xs(
        "colonoscopy_2", level="visit_type"
    )
    subject["mayo_endo_change"] = subject.mayo_endo_end - subject.mayo_endo_start

    def in_remission(x):
        out = (x.mayo_endo_change < 0) & (x.mayo_total_end <= 2)
        out.loc[x.mayo_endo_change.isna() | x.mayo_total_end.isna()] = float("nan")
        out.loc[x.withdrawal_due_to_failure] = False
        out = out.astype(float).astype("boolean")
        return out

    def is_responder(x):
        out = x.mayo_total_change <= -3
        out.loc[x.mayo_total_change.isna()] = float("nan")
        out.loc[x.withdrawal_due_to_failure] = False
        out = out.astype(float).astype("boolean")
        return out

    def mayo_endo_improved(x):
        out = x.mayo_endo_change < 0
        out.loc[x.mayo_endo_change.isna()] = float("nan")
        out.loc[x.withdrawal_due_to_failure] = False
        out = out.astype(float).astype("boolean")
        return out

    subject = subject.assign(
        remission=in_remission,
        responder=is_responder,
        mayo_endo_improved=mayo_endo_improved,
    )
    return subject


def load_motu_to_taxonomy_table(con):
    motu_x_taxonomy = (
        pd.read_sql("SELECT motu_id, taxonomy FROM motu", con=con, index_col="motu_id")
        .squeeze()
        .apply(taxonomy_to_series)
    )

    return motu_x_taxonomy


def load_mgen_table(con):
    mgen = pd.read_sql(
        "SELECT mgen_id, sample_id FROM mgen",
        con=con,
        index_col="mgen_id",
    ).squeeze()
    return mgen
