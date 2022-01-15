rule parse_metabolon_data:
    output:
        metab="meta/chem.tsv",
        sample_abt_chem="meta/sample_abt_chem.tsv",
        sample_x_chem="data/core.metab.peak_size.tsv",
    input:
        sample="meta/sample.tsv",
        xlsx="raw/UCSF-02-19MD CDT.XLSX",
    shell:
        "false  # TODO: See nb/prototype_parse_metabolon_data.ipynb"
