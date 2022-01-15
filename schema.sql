CREATE TABLE subject
  ( subject_id PRIMARY KEY
  , recipient BOOL
      CHECK (recipient IN (0, 1))
  , sex
      CHECK (sex IN ('male', 'female'))
  , treatment_abx_pre
      CHECK (treatment_abx_pre IN (0, 1))
  , treatment_maintenance_method
      CHECK (treatment_maintenance_method IN ('enema', 'capsules'))
  , donor_subject_id REFERENCES subject(subject_id) DEFERRABLE INITIALLY DEFERRED
  , withdrawal_due_to_failure BOOL
      CHECK (withdrawal_due_to_failure IN (0, 1))
  , baseline_treatment_steroids BOOL
      CHECK (baseline_treatment_steroids IN (0, 1))
  , baseline_treatment_biologics BOOL
      CHECK (baseline_treatment_biologics IN (0, 1))
  , baseline_disease_location
  , followup_disease_location
  );

CREATE TABLE sample
  ( sample_id PRIMARY KEY
  , subject_id REFERENCES subject(subject_id)
  , collection_days_post_fmt FLOAT
  , received_days_post_fmt FLOAT
  , sample_group
      CHECK (sample_group
        IN ( 'donor'
           , 'baseline'
           , 'post_antibiotic'
           , 'maintenance'
           , 'followup'
           )
        )
  , sample_type
      CHECK (sample_type
        IN ( 'donor_initial'
           , 'donor_capsule'
           , 'donor_enema'
           , 'baseline'
           , 'post_antibiotic'
           , 'pre_maintenance_1'
           , 'pre_maintenance_2'
           , 'pre_maintenance_3'
           , 'pre_maintenance_4'
           , 'pre_maintenance_5'
           , 'pre_maintenance_6'
           , 'followup_1'
           , 'followup_2'
           , 'followup_3'
           ))
  , dna_extraction_days_post_fmt FLOAT
  , dna_sequencing_days_post_fmt FLOAT
  , plate_well
  , sample_weight
  , source_sample_id
  , sample_notes
  , biosample
  );

CREATE TABLE visit
  ( visit_id PRIMARY KEY
  , subject_id REFERENCES subject(subject_id)
  , visit_type
  , visit_type_specific
  , days_post_fmt FLOAT
  , status_stool_frequency
  , status_mayo_score_stool_frequency
  , status_mayo_score_rectal_bleeding
  , status_mayo_score_endoscopy_mucosa
  , status_mayo_score_global_physician_rating
  , donor_sample_id REFERENCES sample(sample_id) DEFERRABLE INITIALLY DEFERRED
  , visit_notes
  );

CREATE TABLE rrs
  ( rrs_id PRIMARY KEY
  , sample_id REFERENCES sample(sample_id)
  , filename_r1
  , filename_r2
  , rrs_notes
  , sra_accession
  );

CREATE TABLE mgen
  ( mgen_id PRIMARY KEY
  , sample_id REFERENCES sample(sample_id)
  , plate_number
  , plate_well
  , filename_r1
  , filename_r2
  , mgen_notes
  , sra_accession
  );

CREATE TABLE mgen_x_mgen_group
  ( mgen_id REFERENCES mgen(mgen_id)
  , mgen_group
  );

CREATE TABLE rotu
  ( rrs_otu_id PRIMARY KEY  -- FIXME: Rename to rotu_id
  , _sv_name
  , nsequence
  , kingdom_
  , phylum_
  , class_
  , order_
  , family_
  , genus_
  , species_
  , kingdom_confidence INT
  , phylum_confidence INT
  , class_confidence INT
  , order_confidence INT
  , family_confidence INT
  , genus_confidence INT
  );

CREATE TABLE rrs_x_rotu_count  -- FIXME: Rename to rrs_x_rotu
  ( rrs_id REFERENCES rrs(rrs_id)
  , rrs_otu_id REFERENCES rrs_otu(rrs_otu_id)  -- FIXME: Rename to rotu_id
  , tally INT

  , PRIMARY KEY (rrs_id, rrs_otu_id)  -- FIXME
  );

CREATE TABLE motu
  ( representative_genome_id  -- REFERENCES genome(genome_id)
  , motu_id PRIMARY KEY
  , taxonomy
  );

-- CREATE VIEW species_taxonomy AS
-- SELECT species_id, domain_, phylum_, class_, order_, family_, genus_, species_
-- FROM species
-- JOIN genome ON (genome_id = representative_genome_id)
-- ;

CREATE TABLE mgen_x_motu
  ( mgen_id REFERENCES mgen(mgen_id)
  , motu_id REFERENCES motu(motu_id)
  , coverage FLOAT

  , PRIMARY KEY (mgen_id, motu_id)
  );

CREATE TABLE mgen_x_sotu
  ( mgen_id REFERENCES mgen(mgen_id)
  , sotu_id
  , coverage FLOAT

  , PRIMARY KEY (mgen_id, sotu_id)
  );

CREATE TABLE chem
  ( chem_id PRIMARY KEY
  , chem_description
  , analysis_platform
  , refractive_index FLOAT
  , molar_mass FLOAT
  , superpathway
  , subpathway
  , pubchem_id
  , cas_number
  , kegg_id
  , hmdb_id
  );

CREATE TABLE sample_abt_chem
  ( sample_id PRIMARY KEY REFERENCES sample(sample_id)
  , extraction_volume FLOAT
  , extraction_mass FLOAT
  );

CREATE TABLE chem_abt_bile_acid
  ( chem_id PRIMARY KEY REFERENCES chem(chem_id)
  , abbreviation
  , name
  , trustworthy
  , hydroxylated_12 BOOL
  , hydroxylated_7 BOOL
  , conjugated BOOL
  , sulfated BOOL
  );

CREATE TABLE sample_x_chem
  ( chem_id REFERENCES chem(chem_id)
  , sample_id REFERENCES sample(sample_id)
  , peak_area FLOAT

  , PRIMARY KEY (chem_id, sample_id)
  );

CREATE TABLE mgen_x_annot
  ( mgen_id REFERENCES mgen(mgen_id)
  , annot_id  -- REFERENCES annot(annot_id)
  , tally
  , annot_type

  , PRIMARY KEY (mgen_id, annot_id, annot_type)
  );

CREATE VIEW sample_x_annot AS
SELECT sample_id, annot_id, SUM(tally) AS tally, annot_type
FROM mgen_x_annot
JOIN mgen USING (mgen_id)
GROUP BY sample_id, annot_id, annot_type
;

CREATE VIEW sample_x_motu AS
SELECT sample_id, motu_id, SUM(coverage) AS coverage
FROM mgen_x_motu
JOIN mgen USING (mgen_id)
GROUP BY sample_id, motu_id
;

CREATE VIEW sample_x_sotu AS
SELECT sample_id, sotu_id, SUM(coverage) AS coverage
FROM mgen_x_sotu
JOIN mgen USING (mgen_id)
GROUP BY sample_id, sotu_id
;
