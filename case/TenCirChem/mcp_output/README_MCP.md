# TenCirChem MCP Plugin

## Overview

TenCirChem is a quantum computational chemistry package built on TensorCircuit, designed for efficient calculation of molecular properties using both static and dynamic approaches. It provides tools for ground state calculations, time evolution simulations, and molecular property analysis using advanced quantum algorithms. The package is optimized for performance and flexibility, offering significant speed advantages over comparable tools.

### Key Features

- **Static Module**:
  - Ground state calculations using Unitary Coupled Cluster (UCC) methods such as UCCSD, kUpCCGSD, and pUCCD.
  - Hardware Efficient Ansatz (HEA) with support for noisy circuit simulations.
  - Custom integrals, active space approximation, and reduced density matrices (RDMs).

- **Dynamic Module**:
  - Time evolution simulations for quantum systems.
  - Transformation from models to qubit representation.
  - Variational quantum algorithms based on JAX.
  - Support for models like spin-boson and pyrazine S1/S2 internal conversion dynamics.

- **Performance**:
  - Up to 10,000× speedup for certain UCC calculations.
  - Efficient analytical expansion of UCC factors and exploitation of symmetry.

- **Design Philosophy**:
  - Simplicity and hackability with minimal class inheritance hierarchy.
  - Direct access to internal variables through class attributes.

## Installation

TenCirChem can be installed via pip:

```
pip install tencirchem
```

This installs the minimal version with NumPy backend. For GPU support and advanced features, install additional dependencies:

```
pip install jax[cpu]
pip install cupy
```

For development purposes, you may also need:

```
pip install pytest sphinx
```

## Usage

### Basic Example: UCCSD Calculation

```python
from tencirchem import UCCSD, M

# Create a molecule - H4 chain
d = 0.8  # distance in angstrom
h4 = M(atom=[["H", 0, 0, d * i] for i in range(4)])

# Configure and run UCCSD calculation
uccsd = UCCSD(h4)
uccsd.kernel()  # runs VQE optimization
uccsd.print_summary(include_circuit=True)
```

### Example Applications

TenCirChem includes various examples for different applications:

- **Static Calculations**:
  - UCCSD, kUpCCGSD, and pUCCD calculations.
  - Hardware efficient ansatz with various configurations.
  - Noisy circuit simulations.
  - Molecular geometry optimization.

- **Dynamic Simulations**:
  - Spin-boson model dynamics.
  - Pyrazine absorption spectrum.
  - Variational basis state encoder (VBE) applications.

Refer to the `example/` directory for detailed examples and walkthroughs.

## Available Tools and Endpoints

### Core Components

- **Static Module**:
  - `UCCSD`: Unitary Coupled Cluster Single and Double.
  - `kUpCCGSD`: k-UpCCGSD ansatz.
  - `pUCCD`: Pair Unitary Coupled Cluster Doubles.
  - `HEA`: Hardware Efficient Ansatz.

- **Dynamic Module**:
  - `TimeEvolution`: Time evolution simulations.
  - `Transformation`: Qubit encoding and transformation.
  - `Molecule`: Molecular representation and manipulation.

### Backends and Engines

TenCirChem supports multiple backends and simulation engines:

- **Backends**:
  - NumPy
  - JAX
  - CuPy

- **Engines**:
  - `civector-large`
  - `statevector`
  - `tensornetwork`
  - `tensornetwork-noise`
  - `tensornetwork-shot`
  - `tensornetwork-noise&shot`

## Notes and Troubleshooting

### Common Issues

1. **Installation Errors**:
   - Ensure Python version is 3.7 or higher.
   - Use `pip install jax[cpu]` for CPU-based JAX installation or `pip install jax[cuda]` for GPU support.

2. **Backend Compatibility**:
   - For GPU acceleration, ensure CuPy is installed and compatible with your CUDA version.

3. **Performance**:
   - For large-scale simulations, use JAX or CuPy backends for optimal performance.

### Debugging Tips

- Use `uccsd.print_summary()` to inspect the results and circuit details.
- Enable verbose logging for detailed error messages:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

### Reporting Issues

If you encounter any issues, please report them on the [GitHub repository](https://github.com/tencent-quantum-lab/TenCirChem).

## Contributing

We welcome contributions to TenCirChem! To get started:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

For development setup, install the dependencies listed in `requirements-dev.txt` and use `pytest` for testing.

## License

TenCirChem is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Resources

- [GitHub Repository](https://github.com/tencent-quantum-lab/TenCirChem)
- [Documentation](docs/source/)
- [Examples](example/README.md)

---

For further assistance, please refer to the [documentation](docs/source/) or contact the development team via GitHub.