# _MaSIF-neosurf_ – Surface-based protein design for ternary complexes

[![DOI](https://zenodo.org/badge/DOI/10.1038/s41586-024-08435-4.svg)](https://doi.org/10.1038/s41586-024-08435-4)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

> **Note:** This is a fork maintained by the [Chemical Biology STP](https://intranet.crick.ac.uk/our-crick/chemical-biology) at The Francis Crick Institute. It includes additional features such as a web interface for HPC job submission and enhanced deployment options.
> 
> **Original repository:** [LPDI-EPFL/masif-neosurf](https://github.com/LPDI-EPFL/masif-neosurf)

Code repository for ["Targeting protein-ligand neosurfaces with a generalizable deep learning tool"](docs/citation.bib).

## Table of Contents

- [Description](#description)
- [Method overview](#method-overview)
- [System requirements](#system-requirements)
- [Installation with Docker](#installation-with-docker)
- [Preprocess a PDB file](#preprocess-a-pdb-file)
- [PyMOL plugin](#pymol-plugin)
- [Computational binder recovery benchmark](#computational-binder-recovery-benchmark)
- [Running a seed search](#running-a-seed-search)
- [Running a seed refinement and grafting](#running-a-seed-refinement-and-grafting)
- [License](#license)
- [Reference](#reference)

## Description

Molecular recognition events between proteins drive biological processes in living systems. However, higher levels of mechanistic regulation have emerged, where protein-protein interactions are conditioned to small molecules. Here, we present a computational strategy for the design of proteins that target neosurfaces, i.e. surfaces arising from protein-ligand complexes. To do so, we leveraged a deep learning approach based on learned molecular surface representations and experimentally validated binders against three drug-bound protein complexes. Remarkably, surface fingerprints trained only on proteins can be applied to neosurfaces emerging from small molecules, serving as a powerful demonstration of generalizability that is uncommon in deep learning approaches. The designed chemically-induced protein interactions hold the potential to expand the sensing repertoire and the assembly of new synthetic pathways in engineered cells.

## Method overview

![MaSIF-neosurf overview and pipeline](docs/method.png)

## System requirements
### Hardware
MaSIF-seed has been tested on Linux, and it is recommended to run on an x86-based linux Docker container. It is possible to run on an M1 Apple environment but it runs much more slowly. To reproduce the experiments in the paper, the entire datasets for all proteins consume several terabytes.

Currently, MaSIF takes a few seconds to preprocess every protein. We find the main bottleneck to be the APBS computation for surface charges, which can likely be optimized. Nevertheless, we recommend a distributed cluster to preprocess the data for large datasets of proteins.

### Software
MaSIF relies on external software/libraries to handle protein databank files and surface files, 
to compute chemical/geometric features and coordinates, and to perform neural network calculations. 
The following is the list of required libraries and programs, as well as the version on which it was tested (in parentheses).
* [Python](https://www.python.org/) (3.6)
* [reduce](http://kinemage.biochem.duke.edu/software/reduce.php) (3.23). To add protons to proteins. 
* [MSMS](http://mgltools.scripps.edu/packages/MSMS/) (2.6.1). To compute the surface of proteins. 
* [BioPython](https://github.com/biopython/biopython) (1.66). To parse PDB files. 
* [PyMesh](https://github.com/PyMesh/PyMesh) (0.1.14). To handle ply surface files, attributes, and to regularize meshes.
* PDB2PQR (2.1.1), multivalue, and [APBS](http://www.poissonboltzmann.org/) (1.5). These programs are necessary to compute electrostatics charges.
* [Open3D](https://github.com/IntelVCL/Open3D) (0.5.0.0). Mainly used for RANSAC alignment.
* [Tensorflow](https://www.tensorflow.org/) (1.9). Use to model, train, and evaluate the actual neural networks. Models were trained and evaluated on a NVIDIA Tesla K40 GPU.
* [StrBioInfo](https://pypi.org/project/StrBioInfo/). Used for parsing PDB files and generate biological assembly for MaSIF-ligand.
* [Dask](https://dask.org/) (2.2.0). Run function calls on multiple threads (optional for reproducing some benchmarks).
* [Pymol](https://pymol.org/2/) (2.5.0). This optional program allows one to visualize surface files.
* [RDKit](https://www.rdkit.org/) (2021.9.4). For handling small molecules, especially the proton donors and acceptors.
* [OpenBabel](https://github.com/openbabel/openbabel) (3.1.1.7). For handling small molecules, especially the conversion into MOL2 files for APBS.
* [ProDy](https://github.com/prody/ProDy) (2.0). For handling small molecules, especially the ligand extraction from a PDB.

## Installation

MaSIF-neosurf can be installed in several ways depending on your environment:

### Docker (Recommended for Development)
```bash
git clone https://github.com/LPDI-EPFL/masif-neosurf.git
cd masif-neosurf
docker build -f deployment/docker/Dockerfile . -t masif-neosurf 
docker run -it -v $PWD:/home/$(basename $PWD) masif-neosurf 
```

### Singularity (Recommended for HPC)
```bash
cd deployment/singularity
singularity build masif-neosurf.sif masif-neosurf.def
singularity exec masif-neosurf.sif masif-preprocess input.pdb CHAIN_ID
```
See [SINGULARITY_USAGE.md](docs/SINGULARITY_USAGE.md) for details.

### EasyBuild (For HPC Module Systems)
```bash
cd deployment/easybuild
bash install_masif_easybuild.sh
module load MaSIF-neosurf/1.0
```
See [EASYBUILD_INSTALLATION.md](docs/EASYBUILD_INSTALLATION.md) for details.

### Web Interface (For Non-Command-Line Users)
A user-friendly web interface is available for submitting jobs to HPC clusters:
```bash
cd ui
pixi install
pixi run python app.py
```
See [ui/README.md](ui/README.md) for details.

## Preprocess a PDB file

Before we can search for complementary binding sites/seeds, we need to triangulate the molecular surface and compute 
the initial surface features. The script `preprocess_pdb.sh` takes two required positional arguments: the PDB file and a 
definition of the chain(s) that will be included.

If a small molecule is part of the molecular surface, we need to tell MaSIF-neosurf where to find it in the PDB file 
(three letter code + chain) using the `-l` flag. Optionally, we can also provide an SDF file with the `-s` flag that 
will be used to infer the correct connectivity information (i.e. bond types). This SDF file can be downloaded from the 
PDB website for example.

Finally, we must specify an output directory with the `-o` flag, in which all the preprocessed files will be saved.

```bash
cd deployment/scripts
chmod +x ./preprocess_pdb.sh

# with ligand
./preprocess_pdb.sh ../../examples/1a7x.pdb 1A7X_A -l FKA_B -s ../../examples/1a7x_C_FKA.sdf -o output/

# without ligand
./preprocess_pdb.sh ../../examples/1a7x.pdb 1A7X_A -o output/
```

## PyMOL plugin

The [PyMOL plugin](src/masif_pymol_plugin.py) can be used to visualize preprocessed surface files (.ply file extension).
To install it, open the plugin manager in PyMOL, select `Install New Plugin -> Install from local file` and choose the `src/masif_pymol_plugin.py` file.
Once installed you can load MaSIF surface files in PyMOL with the following command:
```bash
loadply 1ABC.ply
```

## Computational binder recovery benchmark

For more details on the binder recovery benchmark, please consult the relevant [README](computational_benchmark/README.md).
The preprocessed dataset can be downloaded from [Zenodo](https://zenodo.org/records/14225758).

## Running a seed search

For more details on the seed search procedure, please consult the relevant [README](masif_seed_search/data/masif_targets/README.md)

## Running a seed refinement and grafting

For more details on the seed refinement and grafting procedure, please consult the relevant [README](rosetta_scripts/README.md)

## License

MaSIF-seed is released under an [Apache v2.0 license](LICENSE)

## Project Structure

```
masif-neosurf/
├── masif/                  # Core MaSIF codebase
├── src/                    # Source code and utilities
├── ui/                     # Web interface for HPC job submission
├── deployment/             # Deployment files (Docker, Singularity, EasyBuild)
├── docs/                   # Documentation
├── examples/               # Example input files
├── computational_benchmark/# Binder recovery benchmark
├── masif_seed_search/     # Seed search implementation
└── rosetta_scripts/       # Seed refinement and grafting
```

## Documentation

- [Installation Guides](docs/) - EasyBuild, Singularity, HPC usage
- [Web Interface](ui/README.md) - User-friendly job submission
- [Deployment](deployment/README.md) - Docker, Singularity, EasyBuild
- [Examples](examples/README.md) - Test files and usage examples

## Reference

```
@article{marchand2025,
  author={Marchand, Anthony and Buckley, Stephen and Schneuing, Arne and Pacesa, Martin and Elia, Maddalena and Gainza, Pablo and Elizarova, Evgenia and Neeser, Rebecca M. and Lee, Pao-Wan and Reymond, Luc and Miao, Yangyang and Scheller, Leo and Georgeon, Sandrine and Schmidt, Joseph and Schwaller, Philippe and Maerkl, Sebastian J. and Bronstein, Michael and Correia, Bruno E.},
  title={Targeting protein-ligand neosurfaces with a generalizable deep learning tool},
  journal={Nature},
  year={2025},
  month={Jan},
  day={15},
  issn={1476-4687},
  doi={10.1038/s41586-024-08435-4},
  url={https://doi.org/10.1038/s41586-024-08435-4}
}
```
