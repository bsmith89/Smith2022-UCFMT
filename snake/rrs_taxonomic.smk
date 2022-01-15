rule process_rrs_table:
    output:
        "data/rrs_x_rotu_count.tsv",
    input:
        script="scripts/convert_xlsx_community_matrix_to_tsv.py",
        xlsx="sraw/2020-12-30-Dose_Finding_Study_Box_mirror/16S data files/DFS_ASV-table_no-contam_062519.xlsx",
    shell:
        dd(
            """
        {input.script} "{input.xlsx}" > {output}
        """
        )


rule alias_otu_table:
    output:
        "data/rotu_details.tsv",
    input:
        "sraw/2020-12-30-Dose_Finding_Study_Box_mirror/16S data files/seqtabTaxa2GenusSpec_withBoot_May2019_OTUID.txt",
    shell:
        "ln -rs '{input}' {output}"
