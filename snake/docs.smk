rule sort_bib_from_raw:
    output: 'doc/bibliography.bib'
    input:
        script='scripts/sort_bib.py',
        bib=['doc/bibliography_raw.bib'],
    shell:
        "{input.script} {input.bib} > {output}"


rule render_figure_to_png:
    output:
        "fig/{stem}_figure.w{width}.png",
    input:
        "doc/static/{stem}_figure.svg",
    params:
        width=lambda w: int(w.width),
    shell:
        """
        inkscape {input} --export-width={params.width} --export-filename {output}
        """

rule render_figure_to_pdf:
    output:
        "fig/{stem}_figure.pdf",
    input:
        "doc/static/{stem}_figure.svg",
    shell:
        """
        inkscape {input} --export-filename {output}
        """



rule build_submission_docx:
    output:
        "build/submission.docx",
    input:
        source="doc/submission.md",
        bib="doc/bibliography.bib",
        template="doc/static/example_style.docx",
        csl="doc/static/style.csl",
        figs=[
            "fig/design_and_efficacy_figure.pdf",
            "fig/multiomics_clustering_optionA_figure.pdf",
            "fig/engraftment_figure.pdf",
            "fig/correlated_multiomics_figure.pdf",
            "fig/multiomics_ordination_by_subject_figure.pdf",
            "fig/donor_taxa_venn_diagram_figure.pdf",
            "fig/engraftment_extended_figure.pdf",
            "fig/multiomics_anosim_by_sex_figure.pdf",
            "fig/strain_coexistence_figure.pdf",
        ],
    shell:
        """
        pandoc --from markdown --to docx \
               --standalone --self-contained --reference-doc {input.template} \
               --filter pandoc-crossref --csl {input.csl} --citeproc \
               --bibliography={input.bib} -s {input.source} -o {output}
        """


localrules:
    build_submission_docx,


rule build_submission_pdf:
    output:
        "build/submission.pdf",
    input:
        source="doc/submission.md",
        bib="doc/bibliography.bib",
        csl="doc/static/style.csl",
        figs=[
            "fig/design_and_efficacy_figure.pdf",
            "fig/multiomics_clustering_optionA_figure.pdf",
            "fig/engraftment_figure.pdf",
            "fig/correlated_multiomics_figure.pdf",
            "fig/multiomics_ordination_by_subject_figure.pdf",
            "fig/donor_taxa_venn_diagram_figure.pdf",
            "fig/engraftment_extended_figure.pdf",
            "fig/multiomics_anosim_by_sex_figure.pdf",
            "fig/strain_coexistence_figure.pdf",
        ],
    shell:
        """
        pandoc --from markdown --to pdf \
               --filter pandoc-crossref --csl {input.csl} --citeproc \
               --pdf-engine=xelatex \
               --bibliography={input.bib} -s {input.source} -o {output}
        """


localrules:
    build_submission_pdf,
