# {{{2 GT-PRO Analysis
rule run_gtpro:
    output:
        "{datadir}/{stem}.gtpro_raw.gz",
    input:
        "{datadir}/{stem}.fq.gz",
    params:
        db_l=32,
        db_m=36,
        db_name="ref/gtpro/20190723_881species",
    threads: 4
    resources:
        mem_mb=60000,
        pmem=60000 // 4,
        walltime_hr=4,
    shell:
        dd(
            """
        GT_Pro genotype -t {threads} -l {params.db_l} -m {params.db_m} -d {params.db_name} -f -o {output} {input}
        mv {output}.tsv.gz {output}
        """
        )


rule move_metagenotype_out_of_sdata:
    output:
        "data/{stem}.gtpro_raw.gz",
    input:
        "sdata/{stem}.gtpro_raw.gz",
    shell:
        "cp {input} {output}"


# NOTE: Comment-out this rule after files have been completed to
# save DAG processing time.
rule gtpro_finish_processing_reads:
    output:
        "data/{stem}.gtpro_parse.tsv.bz2",
    input:
        script="scripts/gtp_parse.py",
        gtpro="data/{stem}.gtpro_raw.gz",
    params:
        db="ref/gtpro/variants_main.covered.hq.snp_dict.tsv",
    shell:
        dd(
            """
        {input.script} --dict {params.db} --in <(zcat {input.gtpro}) --v2 \
                | bzip2 -c \
            > {output}
        """
        )


# NOTE: Comment out this rule to speed up DAG evaluation.
# Selects a single species from every file and concatenates.
rule concatenate_mgen_group_one_read_count_data_from_one_species:
    output:
        "data/{group}.a.{stem}.sp-{species}.gtpro_combine.tsv.bz2",
    input:
        script="scripts/select_gtpro_species_lines.sh",
        gtpro=lambda w: [
            f"data/{mgen}.{{stem}}.gtpro_parse.tsv.bz2"
            for mgen in config["mgen_group"][w.group]
        ],
    params:
        species=lambda w: w.species,
        args=lambda w: "\n".join(
            [
                f"{mgen}\tdata/{mgen}.{w.stem}.gtpro_parse.tsv.bz2"
                for mgen in config["mgen_group"][w.group]
            ]
        ),
    threads: 6
    shell:
        dd(
            """
        tmp=$(mktemp)
        cat >$tmp <<EOF
        {params.args}
        EOF
        parallel --colsep='\t' --bar -j {threads} \
                {input.script} {params.species} :::: $tmp \
            | bzip2 -c \
            > {output}
        """
        )


rule merge_both_reads_species_count_data:
    output:
        "data/{group}.a.{stem}.gtpro.sp-{species}.metagenotype.nc",
    input:
        script="scripts/merge_both_gtpro_reads_to_netcdf.py",
        r1="data/{group}.a.r1.{stem}.sp-{species}.gtpro_combine.tsv.bz2",
        r2="data/{group}.a.r2.{stem}.sp-{species}.gtpro_combine.tsv.bz2",
    threads: 4
    resources:
        mem_mb=100000,
        pmem=lambda w, threads: 100000 // threads,
    shell:
        "{input.script} {input.r1} {input.r2} {output}"


# NOTE: Hub-rule: Comment out this rule to reduce DAG-building time
# once it has been run for the focal group.
rule estimate_all_species_coverage_from_metagenotype:
    output:
        touch("data/{stem}.species_cvrg.tsv"),
    input:
        script="scripts/estimate_species_coverage_from_metagenotype.py",
        mgt=[
            f"data/{{stem}}.sp-{species}.metagenotype.nc"
            for species in config["species_list"]
        ],
    params:
        trim=0.05,
        mgt=[
            f"{species}=data/{{stem}}.sp-{species}.metagenotype.nc"
            for species in config["species_list"]
        ],
    shell:
        "{input.script} {params.trim} {params.mgt} > {output}"


rule gather_mgen_group_for_all_species:
    output:
        touch("data/{group}.a.{stemA}.ALL_SPECIES.{stemB}.flag"),
    input:
        [
            f"data/{{group}}.a.{{stemA}}.sp-{species}.{{stemB}}"
            for species in config["species_list"]
        ],
    shell:
        "touch {output}"


localrules:
    gather_mgen_group_for_all_species,


# {{{2 Strain Deconvolution


# NOTE: Hub-rule: Comment out this rule to reduce DAG-building time
# once it has been run for the focal group.
rule infer_strain_fractions_with_strainfinder:
    output:
        frac="data/{stem}.strain_finder-s{n}.sfrac.tsv",
    input:
        script="scripts/StrainFinderWrapper.py",
        mgt="data/{stem}.metagenotype.nc",
    params:
        npos=100,
        nstrains=lambda w: int(w.n),
        max_reps=10,
        max_time=3600,  # Time in seconds
        dtol=1,
        ntol=3,
    threads: 1
    resources:
        walltime_hr=2,
        mem_mb=int(5e3),
        pmem=int(5e3) // 1,
    conda:
        "conda/strain_finder.yaml"  # May require manual install of openopt, etc.
    shell:
        dd(
            """
        {input.script} {input.mgt} \
                {params.npos} \
                {params.nstrains} \
                {params.max_reps} \
                {params.max_time} \
                {params.dtol} \
                {params.ntol} \
                {output}
        """
        )


# NOTE: Hub-rule: Comment out this rule to reduce DAG-building time
# once it has been run for the focal group.
rule calculate_all_strain_coverages:
    output:
        "data/{stemA}.{stemB}.strain_cvrg.tsv",
    input:
        script="scripts/merge_all_strains_coverage.py",
        species="data/{stemA}.species_cvrg.tsv",
        strains=[
            f"data/{{stemA}}.sp-{species}.{{stemB}}.sfrac.tsv"
            for species in config["species_list"]
        ],
    params:
        args=[
            f"{species}=data/{{stemA}}.sp-{species}.{{stemB}}.sfrac.tsv"
            for species in config["species_list"]
        ],
    shell:
        dd(
            """
        {input.script} {input.species} {params.args} > {output}
        """
        )
