#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

USAGE:

    parse_uhgp_eggnog_annot.py <INPUT> <KO> <COG> <EGGNOG>


Input file format:

COL    EXAMPLE                                                  INTERPRETATION
---    -------                                                  --------------
1      GUT_GENOME033876_02889                                   unique cluster identifier (seed sequence)
2      484018.BACPLE_01508                                      seed eggNOG ortholog
3      GUT_GENOME029360_02515;1.5e-187                          seed ortholog evalue
4      GUT_GENOME029360_02515;662.1                             seed ortholog score
5      Bacteroidaceae                                           Taxonomic family ("of best hit" assumed for all following fields)
6      glf                                                      Gene name
7      GO:0003674,GO:0003824,GO:0005575,[...]                   All GO terms assigned
8      5.4.99.9                                                 EC Number
9      ko:K01854                                                KO Number
10     ko00052,ko00520,map00052,map00520                        Kegg Pathways and Maps
11     <blank>                                                  KEGG module
12     R00505,R09009                                            KEGG reactions
13     RC00317,RC02396                                          KEGG rclass
14     ko00000,ko00001,ko01000                                  BRITE identifier
15     <blank>                                                  KEGG_TC
16     <blank>                                                  CAZY identifier
17     iNJ661.Rv3809c                                           BiGG Models identifier
18     Bacteria                                                 Domain
19     2FNRR@200643,4AKYR@815,4NGXU@976,COG0562@1,COG0562@2     eggNOG Orthologous Groups
20     NA|NA|NA                                                 best_OG|evalue|score: Best matching Orthologous Groups (only in HMM mode)
21     M                                                        COG Functional Category
22     UDP-galactopyranose mutase                               Product description

"""

import sys
from tqdm import tqdm


if __name__ == "__main__":
    inpath = sys.argv[1]

    seed_to_ko_all_outpath = sys.argv[2]
    seed_to_eggnog_root_outpath = sys.argv[3]
    seed_to_eggnog_all_outpath = sys.argv[4]
    seed_to_kegg_module_outpath = sys.argv[5]
    seed_to_seed_outpath = sys.argv[6]

    with open(inpath) as input_f, open(
        seed_to_ko_all_outpath, "w"
    ) as seed_to_ko_all_f, open(
        seed_to_eggnog_root_outpath, "w"
    ) as seed_to_eggnog_root_f, open(
        seed_to_eggnog_all_outpath, "w"
    ) as seed_to_eggnog_all_f, open(
        seed_to_kegg_module_outpath, "w"
    ) as seed_to_kegg_module_f, open(
        seed_to_seed_outpath, "w"
    ) as seed_to_seed_f:
        for line in tqdm(input_f):
            (
                seed,
                _,
                _,
                _,
                _,
                _,
                _,
                _,
                kegg_ko_ids,
                _,
                kegg_module_ids,
                _,
                _,
                _,
                _,
                _,
                _,
                tax_domain,
                eggnog_ids,
                *_,
            ) = line.split("\t")
            if tax_domain not in ("Bacteria", "Archaea"):
                continue

            print(seed, seed, sep="\t", file=seed_to_seed_f)

            eggnog_ids = eggnog_ids.split(",")
            found_root = False
            for og in eggnog_ids:
                print(seed, og, sep="\t", file=seed_to_eggnog_all_f)
                if og.endswith("@1"):
                    print(
                        seed,
                        og.split("@")[0],
                        sep="\t",
                        file=seed_to_eggnog_root_f,
                    )
                    found_root = True
            # FIXME: Consider how to check assumptions.
            # assert found_root, \
            #        (f"Found a Bacteria or Archaea record without a root "
            #         f"eggNOG (COG):\n{line}")

            for og in kegg_ko_ids.split(","):
                if og and og.startswith("ko:"):
                    print(seed, og[3:], sep="\t", file=seed_to_ko_all_f)

            for module in kegg_module_ids.split(","):
                if module:
                    print(seed, module, sep="\t", file=seed_to_kegg_module_f)
