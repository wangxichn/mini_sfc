[中文](./README_zh.md) | [English](./README_en.md)

# Introduction

<img align="left" width="100" height="100" style="margin: 2px 2px 0 0;" src="https://raw.githubusercontent.com/wangxichn/image_hosting/refs/heads/main/minisfc/minisfc_logo_light.drawio.png" />

Mini-SFC is a simulation framework designed for Service Function Chain (SFC) orchestration algorithms. It supports both purely numerical simulations built on discrete events and container-based simulations that mimic real-time conditions, making it particularly suitable for studying SFC deployment and migration issues based on MANO architecture.The design of this simulation framework draws inspiration from several renowned network simulation tools such as [NS-3](https://www.nsnam.org/), [Mininet](https://github.com/mininet/mininet), [Containernet](https://github.com/containernet/containernet), [VirNE](https://github.com/GeminiLight/virne), [mini-nfv](https://github.com/josecastillolema/mini-nfv), among others. We extend our gratitude to the developers of these projects!

## Features

- Modular design including scenario scripts, simulation engines, algorithm templates, logging, etc.
- Supports both purely numerical simulations (for faster validation of algorithm performance in large-scale scenarios) and container-based simulations (for more realistic network topology, link, and service simulations).
- Integrates various template algorithms and supports users in developing custom algorithms through provided interfaces.
- Supports changes in the topology during simulation runs, including substrate network topology changes, addition and removal of VNF nodes, etc.

## Installation Guide

For those who wish to have flexible configurations and use artificial intelligence algorithms based on CUDA for research, bare-metal installation is recommended. Ensure your machine runs at least Ubuntu **22.04 LTS** or later, with **Python3.10** or newer installed.

First, clone the project repository:

```bash
git clone https://gitee.com/WangXi_Chn/mini_sfc.git
```

or 

```bash
git clone https://github.com/wangxichn/mini_sfc.git
```

Then install the relevant dependencies using the setup.py file (it's recommended to use a virtual environment and the -e option for developer mode installation):

```bash
pip install -e .
```

After completing these steps, you're ready to explore the capabilities of Mini-SFC.

## Getting Started

Using Mini-SFC is straightforward, similar to the operational flow of network simulation tools like Mininet and Containernet.

### Running Basic Examples

#### Pure Numerical Simulation Example

Navigate to the `mini_sfc/examples/simple_dynamictopo/` directory and execute the following command to start a pure numerical simulation example:

```bash
python simple_dynamictopo.py
```

#### Container-Based Simulation Example

Navigate to the `mini_sfc/examples/simple_container/` directory and execute the following command to start a container-based simulation example:

Given that container-based simulations require Docker, ensure it is installed on your machine. Additionally, since this example requires the containernet library for simulating container networks, make sure it is also installed. Due to the need for sudo privileges, please use the `which` command to get the absolute path of python and then run the example with sudo.

```bash
which python
sudo path/to/python simple_container.py
```

## Documentation

For more detailed documentation about Mini-SFC, visit our (TBD)[GitHub Pages](https://wangxichn.github.io/mini_sfc/) page.

## Research

If you have conducted research using Mini-SFC, we welcome you to share your findings!

### Citing This Framework

If you find Mini-SFC helpful for your research, please cite our related paper:

**[Drones, 2024] PSO "Based On Version 1.0 of Mini-SFC"**

```bibtex
@Article{drones8040117,
AUTHOR = {Wang, Xi and Shi, Shuo and Wu, Chenyu},
TITLE = {Research on Service Function Chain Embedding and Migration Algorithm for UAV IoT},
JOURNAL = {Drones},
VOLUME = {8},
YEAR = {2024},
NUMBER = {4},
ARTICLE-NUMBER = {117},
URL = {https://www.mdpi.com/2504-446X/8/4/117},
ISSN = {2504-446X},
DOI = {10.3390/drones8040117}
}
```

## Contact Us

### Project Support

Should you have any questions or suggestions, feel free to provide feedback through Gitee or GitHub via issues or pull requests.

### Developer Information

Wang Xi

- Email: <wangxi_chn@foxmail.com>
- Homepage: <https://www.yuque.com/wangxi_chn>