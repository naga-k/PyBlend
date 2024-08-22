<h1 align="center"> PyBlend </h1>

<p align="center">
    <b>This is a fork of the original PyBlend project, adapted for rendering images of OBJ files.</b>
</p>

<p align="center">
    <b>PyBlend is a Python library for <a href="https://www.blender.org/">Blender</a>. It provides a variety of valuable functions for Blender scripting.</b>
</p>
<p align="center">
    <img src="docs/teaser.gif" width=80%>
    <p align="center">
        <b>Figure 1.</b> <i>Depth maps, random material images, and normal maps rendered using PyBlend with the Stanford Bunny.</i>
    </p>
</p>

## Installation

Setting up the environment for Python in Blender can be challenging. However, following these steps will help you configure the environment easily.

1. Download Blender from [here](https://www.blender.org/download/).

    Note: If your project has strict environmental requirements, you must carefully select the version of Blender. Currently, there appears to be **NO** official release of Blender that directly supports Python 3.8, which can be verified from [blender/tags](https://github.com/blender/blender/tags). Here, I use `blender-3.6.0-linux-x64` for Linux users with Python 3.10.2. Once you unzip the file, you will find a folder structured like this:

    ```bash
    ./blender-3.6.0-linux-x64
    ├── blender
    ├── 3.6
    ...
    ```
    where `blender` is the executable file (I will use `{path/to/blender}` or `blender_app` to represent this path in the following) and `3.6` contains the Python environment for Blender.

2. Download `get-pip.py` and install pip for Blender Python.

    ```bash
    $ wget https://bootstrap.pypa.io/get-pip.py

    $ ./blender-3.6.0-linux-x64/3.6/python/bin/python3.10 get-pip.py
    ```

      Note: The Blender version used to adapt PyBlend (Blender 3.6.0) is compatible only with CUDA 11.4. Ensure your system meets this requirement for optimal performance.


3. Install PyBlend.

    ```bash
    $ ./blender-3.6.0-linux-x64/3.6/python/bin/pip install git+https://github.com/anyeZHY/PyBlend.git
    ```

4. You can install other packages in the same way. For example:

    ```bash
    $ ./blender-3.6.0-linux-x64/3.6/python/bin/pip install torch
    ```

## Usage

Some functions of this package are used in the following papers:
- [3D-LLM: Injecting the 3D World into Large Language Models](https://vis-www.cs.umass.edu/3dllm/) [NeurIPS 2023].
- [CHORD: Category-level in-Hand Object Reconstruction via Shape Deformation](https://arxiv.org/pdf/2308.10574.pdf) [ICCV 2023].

I suggest using the following alias to simplify the command: `alias blender_app='{path/to/blender}'`.

### 1. Render Normal and Depth Images

Like `teaser.gif`, you can use PyBlend to render normal and depth images. By using the following command, you can generate 60 images ranging from 0 to 60 degrees.

```shell
$ blender_app -b -P scripts/teaser.py -- --begin 0 --end 60
```

### 2. Render Google Scanned Objects Dataset

To render images for each object in the dataset using PyBlend, follow these steps:

#### 2.1 Single Job for Each Object

To render images for the "Weisshai_Great_White_Shark" dataset, use the following command:

```bash
$ blender_app -b -P google-renderer-2.py -- --data_dir "/path/to/data" --name "Weisshai_Great_White_Shark" --output_dir "/path/to/output" --split "train" --radius 2.5 --num 100
```


### 2.2 Submit Parallel Jobs
To render images for all objects in the dataset in parallel, make sure you have created the submit_jobs.sh script. Then, execute the following command to submit all jobs:

```bash
$ bash submit_jobs.sh
```

This will generate and submit a separate SLURM job for each object directory, allowing for parallel rendering of images.
