#!/bin/bash -l
#SBATCH --job-name=bpy-render
#SBATCH --output=/project/jacobcha/nk643/PyBlend/tmp/%x.%j.out # %x.%j expands to slurm JobName.JobID
#SBATCH --error=/project/jacobcha/nk643/PyBlend/tmp/%x.%j.err # prints the error message
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --exclude=n0088
#SBATCH --ntasks-per-node=4
#SBATCH --mem-per-cpu=4G # Maximum allowable mempry per CPU 4G
#SBATCH --qos=standard
#SBATCH --account=jacobcha # Replace PI_ucid which the NJIT UCID of PI
#SBATCH --time=04:00:00  # D-HH:MM:SS
#SBATCH --gres=gpu:1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=nk643@njit.edu

set -e

module purge
module load wulver # load slurn, easybuild
module load easybuild
module load git
# add any required module loads here, e.g. a specific Python
module load bright
module load GCCcore/11.2.0
module load CUDA/11.4.1
module load foss/2021b FFmpeg/4.3.2
module load Anaconda3
module load Mamba
#source ~/conda3.sh

/project/jacobcha/nk643/PyBlend/blender-3.6.0-linux-x64/blender -b -P google-renderer.py -- --data_dir "/project/jacobcha/nk643/PyBlend/data" --name "Weisshai_Great_White_Shark" --output_dir "/project/jacobcha/nk643/PyBlend/output" --split "test" --radius 2.0 --num 10