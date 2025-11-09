# PhysicsNeMo

PhysicsNeMo is a comprehensive framework developed by NVIDIA for building, training, and deploying physics-informed machine learning models. It provides tools and modules for creating advanced neural operators, graph neural networks, diffusion models, and other state-of-the-art machine learning architectures. The framework is designed to facilitate research and development in scientific computing, weather modeling, structural mechanics, healthcare, and more.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Available CLI Commands](#available-cli-commands)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Notes and Troubleshooting](#notes-and-troubleshooting)
- [License](#license)

---

## Features

- **Physics-Informed Machine Learning**: Build models that incorporate physical laws and constraints.
- **Neural Operators**: Implement advanced neural operator architectures for scientific computing.
- **Graph Neural Networks**: Support for MeshGraphNet and other GNN-based models.
- **Diffusion Models**: Includes SongUNet, Diffusion Transformer (DiT), and preconditioning/sampling techniques.
- **Recurrent and Hybrid Models**: DLWP, SwinRNN, and other time-series models.
- **Active Learning**: Tools for active learning workflows to optimize data labeling and model training.
- **Data Management**: Comprehensive data pipelines for scientific datasets, including climate, CFD, and structural mechanics.
- **Deployment**: Integration with Triton inference server for seamless model deployment.

---

## Installation

### Prerequisites

Before installing PhysicsNeMo, ensure you have the following dependencies installed:

- Python 3.8 or later
- CUDA (if using GPU acceleration)
- PyTorch (compatible with your CUDA version)

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/NVIDIA/physicsnemo.git
   cd physicsnemo
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install the package:
   ```
   pip install .
   ```

4. (Optional) Install additional dependencies for optional features:
   ```
   pip install wandb mlflow dgl pyg vtk netCDF4
   ```

---

## Usage

PhysicsNeMo provides a variety of tools and modules for different use cases. Below are some common usage examples:

### Training a Model

To train a model with logging and checkpointing, use the `train_model` CLI command:

```
python -m source.physicsnemo.launch.logging.launch --config <path_to_config_file>
```

### Deploying a Model

To deploy a model using the Triton inference server, use the `deploy_model` CLI command:

```
python -m source.physicsnemo.deploy.triton --model <path_to_model>
```

### Running Active Learning

To run an active learning workflow, use the `run_active_learning` CLI command:

```
python -m source.physicsnemo.active_learning.driver --config <path_to_config_file>
```

---

## Available CLI Commands

PhysicsNeMo provides the following CLI commands:

1. **train_model**  
   - **Module**: `source.physicsnemo.launch.logging.launch`  
   - **Description**: CLI command for launching model training with logging and checkpointing.  

2. **deploy_model**  
   - **Module**: `source.physicsnemo.deploy.triton`  
   - **Description**: CLI command for deploying models using the Triton inference server.  

3. **run_active_learning**  
   - **Module**: `source.physicsnemo.active_learning.driver`  
   - **Description**: CLI command for running active learning workflows.  

---

## Project Structure

The repository is organized as follows:

- `source/physicsnemo`: Core framework modules, including active learning, data pipelines, distributed computing, models, metrics, and utilities.
- `examples`: Example use cases and applications, including weather modeling, structural mechanics, healthcare, and more.
- `test`: Unit tests for various modules and functionalities.
- `docs`: Documentation and configuration files for the project.

---

## Dependencies

### Required Dependencies

- `torch`
- `numpy`
- `scipy`
- `onnx`
- `tritonclient`
- `matplotlib`
- `pandas`
- `pyyaml`
- `cuml`

### Optional Dependencies

- `wandb`
- `mlflow`
- `dgl`
- `pyg`
- `vtk`
- `netCDF4`

---

## Notes and Troubleshooting

### Common Issues

1. **CUDA Compatibility**: Ensure that your CUDA version is compatible with the installed version of PyTorch. Refer to the [PyTorch installation guide](https://pytorch.org/get-started/locally/) for compatibility details.

2. **Missing Dependencies**: If you encounter missing dependencies, ensure you have installed all required and optional dependencies using `pip install`.

3. **Configuration Errors**: Double-check your configuration files for any syntax errors or missing parameters.

4. **Deployment Issues**: If deploying with Triton, ensure the Triton server is correctly set up and running. Refer to the [Triton documentation](https://github.com/triton-inference-server/server) for more details.

### Getting Help

If you encounter any issues or have questions, please refer to the following resources:

- [PhysicsNeMo GitHub Issues](https://github.com/NVIDIA/physicsnemo/issues): Report bugs or request features.
- [PhysicsNeMo Documentation](https://github.com/NVIDIA/physicsnemo): Detailed documentation and examples.
- NVIDIA Developer Forums: Engage with the community and get support.

---

## License

PhysicsNeMo is licensed under the [NVIDIA License](LICENSE.txt). Please refer to the license file for more details.