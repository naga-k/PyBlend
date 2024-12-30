import os
import subprocess
import time

# Parameters
RADIUS = 2.0
NUM_IMAGES = 162
METHOD = "random"  # Specify 'random' or 'icosphere'
NU = 3  # Number of icosphere points, e.g., 42 for nu=2
PI = "jacobcha"
USER = "nk643"

# Base paths
OUTPUT_DIR = f"/scratch/{PI}/{USER}/PyBlend/renders/{RADIUS}_{METHOD}_{NUM_IMAGES}"
DATA_DIR = "/project/jacobcha/nk643/PyBlend/data"
JOB_DIR = "/project/jacobcha/nk643/PyBlend/jobs"
BLENDER_EXEC = "/project/jacobcha/nk643/PyBlend/blender-3.6.0-linux-x64/blender"
PYTHON_SCRIPT = "google-renderer.py"

# Ensure the jobs directory exists
os.makedirs(JOB_DIR, exist_ok=True)

# Loop over each object in the data directory
for object_dir in os.listdir(DATA_DIR):
    object_name = os.path.basename(object_dir)

    # Create a unique job script for each object and each method
    for split in ["train"]:
        job_script = os.path.join(JOB_DIR, f"job_{object_name}_{split}.sh")

        # Write the job script
        with open(job_script, 'w') as f:
            f.write(f"""#!/bin/bash -l
#SBATCH --job-name=r_{object_name}
#SBATCH --output=/project/jacobcha/nk643/PyBlend/tmp/%x.%j.out
#SBATCH --error=/project/jacobcha/nk643/PyBlend/tmp/%x.%j.err
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --exclude=n0088
#SBATCH --ntasks-per-node=4
#SBATCH --mem-per-cpu=4G
#SBATCH --qos=standard
#SBATCH --account=jacobcha
#SBATCH --time=04:00:00
#SBATCH --gres=gpu:1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=nk643@njit.edu

set -e

module purge
module load wulver
module load easybuild
module load git
module load bright
module load GCCcore/11.2.0
module load CUDA/11.4.1
module load foss/2021b FFmpeg/4.3.2
module load Anaconda3
module load Mamba

{BLENDER_EXEC} -b -P {PYTHON_SCRIPT} -- --data_dir "{DATA_DIR}" --name "{object_name}" --output_dir "{OUTPUT_DIR}" --split "{split}" --radius {RADIUS} --num {NUM_IMAGES} --method "{METHOD}" --nu {NU}
""")

        # Adding delay as there is a race between the job submission and the file creation
        time.sleep(1)

        # Submit the job script
        subprocess.run(["sbatch", job_script])