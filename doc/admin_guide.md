# Admin guide

## Loading chromosome information

Chromosome size information is required before any samples can be displayed. The data is downloaded from Ensembl.

```bash
gens load chromosomes --genome-build 38
```

This will fetch the karyotype for the selected build and replace any previous entries.

## Loading gene information

Genes and transcripts are loaded from a reference GTF together with a MANE summary. Download the files for the genome build you plan to use and run the loader.

```bash
curl -O https://ftp.ensembl.org/pub/release-113/gtf/homo_sapiens/Homo_sapiens.GRCh38.113.gtf.gz
curl -O https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/release_1.4/MANE.GRCh38.v1.4.summary.txt.gz

gens load transcripts --file Homo_sapiens.GRCh38.113.gtf.gz --mane MANE.GRCh38.v1.4.summary.txt.gz -b 38
```

## Loading annotations

Annotation tracks are stored in the database and can be provided as BED, AED or TSV files.

```bash
gens load annotations -b 38 -f /path/to/annotation_files
```

FIXME: How are existing tracks dealt with?

## Loading samples

Each sample requires a coverage file and BAF file (both tabix indexed). Provide a sample ID, case ID and genome build when loading. 

Sample type (proband/mother/father, tumor/normal) is needed when for Gens to understand what samples belong where in a case with multiple samples. 

Sex is not required but might enable optional functionalities in the future (such as adjusting sex chromosome coverage).

The input files can be prepared by running (FIXME).

```bash
gens load sample \
    --sample-id SAMPLE1 \
    --case-id CASE1 \
    --genome-build 38 \
    --baf SAMPLE1.baf.bed.gz \
    --coverage SAMPLE1.cov.bed.gz \
    --overview-json SAMPLE1.overview.json.gz
```

## Loading extra sample tracks

Additional tracks linked to a sample can be loaded similarly to the annotation tracks.

```bash
gens load sample-annotation \
    --sample-id SAMPLE1 \
    --case-id CASE1 \
    --genome-build 38 \
    --file extra_track.bed \
    --name "CNV calls"
```

## Meta data

Metadata files are TSV formatted. Currently, the data is expected in long format, i.e. one entry per row.

They must contain at least the columns `type` and `value`. A column not named `type`, `value` or `color` is treated as the row name header.

Example with row names:

```tsv
sample type value color
first  A    valA  rgb(1,2,3)
second B    valB  .
.      C    valC  rgb(4,5,6)
```

Example without row names (displayed as key-value pairs):

```tsv
type  value
... (FIXME: Fill in)
```

Provide one or more files with the `--meta` option when loading or updating a sample.

FIXME: Add example command