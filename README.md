# Reciprocal-RELION-3D-Classification-Analysis
This repository provides a Python CLI tool for reciprocal analysis of RELION 3D classification jobs. It automates particle splitting, cross-job class comparison, intersection analysis, and generation of RELION-readable STAR files for class intersections (for the last one, you may still need to manually add optics table)

Features

✔ Automatic detection of last iteration STAR file per 3D classification job
✔ Handles zero-padded job numbers (job085, job086, …)
✔ Automatically detects all classes in each job
✔ Splits particles into per-class STAR files
✔ Computes cross-job class intersections only (no self-comparisons)
✔ Generates:

raw particle intersection count matrix

fractional intersection matrix (normalized per source class)
✔ Saves RELION-importable STAR files for every class intersection
✔ Implemented as a single ready-to-run Python CLI script

<img width="1266" height="1047" alt="image" src="https://github.com/user-attachments/assets/ba2a0996-9690-4623-84c1-f711aca53ccf" />


🚫 Sankey plotting is currently disabled (will be added later)

Repository Structure

reciprocal_analysis/

├── reciprocal_analysis.py

├── environment.yml

└── README.md

**Requirements**

Software:
Python ≥ 3.9
RELION 3.1 or newer (for STAR file compatibility)
Python dependencies

The script requires only a small, stable Python stack:
python
pandas
numpy

All dependencies are defined in the provided Conda environment file.

**Installation**
1. Clone the repository
git clone https://github.com/<your-username>/reciprocal_analysis.git
cd reciprocal_analysis

2. Create the Conda environment
conda env create -f environment.yml

3. Activate the environment
conda activate relion-reciprocal

**Usage**

Basic command
python reciprocal_analysis.py \
  --class3d_dir /path/to/Relion/Class3D \
  --jobs 85,86,87

Arguments
Argument	Description
--class3d_dir	Path to the RELION Class3D directory
--jobs	Comma-separated list of RELION job numbers (auto zero-padded)

Example:

--jobs 85,86


will automatically resolve to:

job085
job086

**What the Script Does (Pipeline)**

_Step 1 — STAR file detection_
Finds the last run_itXXX_data.star file in each jobXXX folder

Reads only the data_particles table

Extracts _rlnImageName and _rlnClassNumber

_Step 2 — Particle splitting_
Automatically detects all class numbers

Saves per-class particle STAR files:

job085_class1.star
job085_class2.star
...

_Step 3 — Reciprocal comparison_
Compares all classes across different jobs

Skips comparisons from the same job

❌ job085 class1 vs job085 class2

✅ job085 class1 vs job086 class2


_Step 4 — Matrices_
Two CSV files are generated:

Raw particle counts
counts_matrix.csv

Fractional overlaps (normalized per source class)
fraction_matrix.csv




Each row contains:

job1,job2,class1,class2,value

_Step 5 — RELION-compatible intersection STAR files_

For every cross-job class pair with overlapping particles, the script generates:

job085_class1_vs_job086_class3.star



Each STAR file:

Contains data_optics copied from the original job

Contains data_particles with correct headers

Is directly importable into RELION

**Output Summary**

After running the script, you will obtain:

Per-class STAR files for each job

counts_matrix.csv

fraction_matrix.csv
RELION-readable STAR files for each class intersection

  **pysankey_input.csv** - this file can be directly used with the pysankey_exmpl_working.py script for generating the Sankey plot. To complete this last step, the pySanKey environment must be set up and activated (https://github.com/anazalea/pySankey/tree/master).




**Notes & Limitations**

Sankey diagrams are currently disabled

The script assumes standard RELION STAR formatting

Only cross-job comparisons are performed by design

**Planned Extensions**

Sankey diagrams (raw counts + normalized fractions)

Optional plotting backend selection

Packaging as a Conda package

Support for classifications on symmetry expanded particles


**Author**

Developed by Piotr Draczkowski
with iterative refinement and automation support.
