# {{{2 Gene analysis


rule download_uhgp_db:
    output:
        "raw/ref/uhgp-{level}.tar.gz",
    params:
        url="http://ftp.ebi.ac.uk/pub/databases/metagenomics/mgnify_genomes/human-gut/v1.0/uhgp_catalogue/uhgp-50.tar.gz",
    shell:
        curl_recipe


rule unpack_uhgp_db:
    output:
        annot="raw/ref/uhgp-{level}/uhgp-{level}_eggNOG.tsv",
        clust="raw/ref/uhgp-{level}/uhgp-{level}.tsv",
        fa="raw/ref/uhgp-{level}/uhgp-{level}.faa",
        clust_hq="raw/ref/uhgp-{level}/uhgp-{level}_hq.tsv",
        fa_hq="raw/ref/uhgp-{level}/uhgp-{level}_hq.faa",
    input:
        "ref/UHGG_v1/uhgp_catalogue/uhgp-{level}",
    wildcard_constraints:
        level=integer_wc,
    params:
        dir=directory("raw/ref/uhgp-{level}/"),
    shell:
        "tar -C {params.dir} -xzf {input}"


rule alias_uhgp_db:
    output:
        fa="ref/uhgp{level}.fa",
        annot="ref/uhgp{level}.eggNOG.tsv",
    input:
        "raw/ref/uhgp-{level}",
    params:
        fa="raw/ref/uhgp-{level}/uhgp-{level}.faa",
        annot="raw/ref/uhgp-{level}/uhgp-{level}_eggNOG.tsv",
    shell:
        dd(
            """
        ln -rs {params.fa} {output.fa}
        ln -rs {params.annot} {output.annot}
        """
        )


rule tally_blastqx_hits_from_both_reads:
    output:
        "data/{mgen}.r.proc.{db}-blastqx.tally.tsv.gz",
    input:
        script="scripts/tally_blast_hits.py",
        r1="data/{mgen}.r1.proc.{db}-blastqx.tsv.gz",
        r2="data/{mgen}.r2.proc.{db}-blastqx.tsv.gz",
    threads: 2
    shell:
        dd(
            """
        zcat {input.r1} {input.r2} | {input.script} | gzip > {output}
        """
        )


rule extract_uhgp_eggnog_annot:
    output:
        ko="ref/uhgp{thresh}_x_ko.tsv",
        cog="ref/uhgp{thresh}_x_cog.tsv",
        eggnog="ref/uhgp{thresh}_x_eggnog.tsv",
        keggmodule="ref/uhgp{thresh}_x_keggmodule.tsv",
        uhgp="ref/uhgp{thresh}_x_uhgp{thresh}.tsv",
    input:
        script="scripts/extract_uhgp_annot.py",
        annot="ref/uhgp{thresh}.eggNOG.tsv",
    shell:
        dd(
            """
        {input.script} {input.annot} {output.ko} {output.cog} {output.eggnog} {output.keggmodule} {output.uhgp}
        """
        )


rule aggregate_blastqx_tally:
    output:
        "data/{stem}.{db}-blastqx.{annot}-tally.tsv",
    input:
        script="scripts/aggregate_blast_tally.py",
        mapper="ref/{db}_x_{annot}.tsv",
        tally="data/{stem}.{db}-blastqx.tally.tsv.gz",
    threads: 2
    shell:
        dd(
            """
        zcat {input.tally} | {input.script} {input.mapper} > {output}
        """
        )


# NOTE: Hub-rule: Comment out this rule to reduce DAG-building time
# once it has been run for the focal group.
rule merge_mgen_tallies:
    output:
        "data/{group}.a.{stem}.{annot}-tally-merged.tsv",
    input:
        script="scripts/merge_tallies.py",
        tally=lambda w: [
            f"data/{mgen}.r.{{stem}}.{{annot}}-tally.tsv"
            for mgen in config["mgen_group"][w.group]
        ],
    params:
        args=lambda w: [
            f"{mgen}=data/{mgen}.r.{w.stem}.{w.annot}-tally.tsv"
            for mgen in config["mgen_group"][w.group]
        ],
    threads: 12
    shell:
        dd(
            """
        {input.script} {params.args} > {output}
        """
        )
