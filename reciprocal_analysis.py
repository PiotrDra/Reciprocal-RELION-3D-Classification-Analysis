#!/usr/bin/env python3

import argparse
import os
import glob
import sys
from collections import defaultdict
import pandas as pd
import numpy as np

# -----------------------------
# STAR file parsing
# -----------------------------
def read_star_file(star_file):
    """
    Read only the data_particles table from a RELION STAR file.
    Returns a pandas DataFrame.
    """
    headers = []
    data = []
    in_particles = False
    in_loop = False

    with open(star_file, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("data_particles"):
                in_particles = True
                continue

            if in_particles and line.startswith("loop_"):
                in_loop = True
                continue

            if in_loop and line.startswith("_"):
                headers.append(line.split()[0].lstrip("_"))
                continue

            if in_loop:
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) == len(headers):
                    data.append(parts)

    if not headers or not data:
        raise ValueError(f"Failed to parse data_particles from {star_file}")

    df = pd.DataFrame(data, columns=headers)

    if "rlnImageName" not in df.columns:
        raise ValueError(f"'rlnImageName' column missing in {star_file}")
    if "rlnClassNumber" not in df.columns:
        raise ValueError(f"'rlnClassNumber' column missing in {star_file}")

    df["rlnClassNumber"] = df["rlnClassNumber"].astype(int)

    return df

# -----------------------------
# Write per-class STAR files
# -----------------------------
def write_per_class_star(df, job_number, outdir):
    """
    Writes STAR files for each class in a job.
    """
    class_dir = os.path.join(outdir, "per_class_star")
    os.makedirs(class_dir, exist_ok=True)

    for cls in sorted(df["rlnClassNumber"].unique()):
        cls_df = df[df["rlnClassNumber"] == cls]
        filename = os.path.join(class_dir, f"job{job_number:03d}_class{cls}.star")

        with open(filename, "w") as f:
            # Write header
            f.write("# version 50001\n\n")
            f.write("data_particles\n\n")
            f.write("loop_\n")
            for col in df.columns:
                f.write(f"_{col} \n")
            # Write data
            for _, row in cls_df.iterrows():
                f.write(" ".join(str(x) for x in row.values) + "\n")
        print(f"Written per-class STAR: {filename}")

# -----------------------------
# Main logic
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Reciprocal analysis of RELION 3D classification jobs"
    )

    parser.add_argument(
        "--relion_dir",
        required=True,
        help="Path to RELION project directory (Class3D will be appended automatically)",
    )

    parser.add_argument(
        "--jobs",
        type=int,
        nargs="+",
        required=True,
        help="RELION job numbers (e.g. 85 86)",
    )

    parser.add_argument(
        "--outdir",
        default="reciprocal_analysis_out",
        help="Output directory",
    )

    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # ---------------------------------------
    # Always work inside Class3D
    # ---------------------------------------
    class3d_dir = os.path.join(args.relion_dir, "Class3D")

    if not os.path.isdir(class3d_dir):
        raise FileNotFoundError(
            f"Expected Class3D directory not found at: {class3d_dir}"
        )

    # ---------------------------------------
    # Read and split STAR files per job/class
    # ---------------------------------------
    job_class_particles = {}

    for job in args.jobs:
        job_str = f"{job:03d}"
        job_dir = os.path.join(class3d_dir, f"job{job_str}")

        star_candidates = sorted(
            glob.glob(os.path.join(job_dir, "run_it*_data.star"))
        )

        if not star_candidates:
            print(
                f"Warning: No STAR file found for job {job_str} in {job_dir}",
                file=sys.stderr,
            )
            continue

        last_star = star_candidates[-1]
        print(f"Job {job_str}: using STAR file {last_star}")

        df = read_star_file(last_star)

        # Write per-class STAR files
        write_per_class_star(df, job, args.outdir)

        class_dict = {}
        for cls in sorted(df["rlnClassNumber"].unique()):
            class_dict[cls] = set(
                df[df["rlnClassNumber"] == cls]["rlnImageName"]
            )

        job_class_particles[job] = class_dict

    if len(job_class_particles) < 2:
        raise RuntimeError("Need at least two valid jobs for reciprocal analysis")

    # ---------------------------------------
    # Compute cross-job intersection matrices
    # ---------------------------------------
    count_matrix = defaultdict(dict)
    fraction_matrix = defaultdict(dict)

    for job_a, classes_a in job_class_particles.items():
        for cls_a, particles_a in classes_a.items():
            label_a = f"job{job_a:03d}_class{cls_a}"

            for job_b, classes_b in job_class_particles.items():
                if job_a == job_b:
                    continue  # omit within-job comparisons

                for cls_b, particles_b in classes_b.items():
                    label_b = f"job{job_b:03d}_class{cls_b}"

                    intersect = particles_a & particles_b
                    count = len(intersect)
                    frac = count / len(particles_a) if particles_a else 0.0

                    count_matrix[label_a][label_b] = count
                    fraction_matrix[label_a][label_b] = frac

    # ---------------------------------------
    # Save matrices
    # ---------------------------------------
    count_df = pd.DataFrame.from_dict(count_matrix, orient="index").fillna(0).astype(int)
    frac_df = pd.DataFrame.from_dict(fraction_matrix, orient="index").fillna(0.0)

    count_df.to_csv(os.path.join(args.outdir, "intersection_counts.csv"))
    frac_df.to_csv(os.path.join(args.outdir, "intersection_fractions.csv"))

    # ---------------------------------------
    # Save pysankey input (long format) without reciprocal duplicates
    # ---------------------------------------
    pysankey_rows = []
    idx = 0
    for jobA_class, targets in count_matrix.items():
        jobA_no = int(jobA_class.split("_")[0].replace("job", ""))
        for jobB_class, count in targets.items():
            jobB_no = int(jobB_class.split("_")[0].replace("job", ""))
            if jobA_no >= jobB_no:
                continue  # skip reciprocal / redundant pairs
            pysankey_rows.append([idx, jobA_class, jobB_class, count])
            idx += 1

    pysankey_df = pd.DataFrame(
        pysankey_rows, columns=["id", "jobANo_class", "jobBNo_class", "#particles"]
    )
    pysankey_df.to_csv(os.path.join(args.outdir, "pysankey_input.csv"), index=False)

    print("Reciprocal analysis complete.")
    print(f"Results written to: {args.outdir}")
    print("Sankey plotting is currently disabled.")


if __name__ == "__main__":
    main()
