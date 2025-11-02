# MCP Plugin README

## Overview

The MCP Plugin is a comprehensive tool designed to facilitate the analysis and measurement of social simulation data. It provides a suite of functionalities for extracting, processing, and analyzing data from various sources, including Twitter, Reddit, and GitHub. The plugin includes modules for cascade reconstruction, community-centric measurements, content-centric measurements, network analysis, and more. It is built to support researchers and developers working on social network analysis, data extraction, and metrics computation.

This repository is based on the [SocialSim project](https://github.com/pnnl/socialsim) and includes a variety of tools and configurations to enable detailed analysis of social simulation data.

---

## Features

- **Data Extraction**: Tools for extracting ground truth data and reconstructing cascades from social media platforms.
- **Cascade Measurements**: Analyze cascades with metrics such as original tweet ratio and graph-based measurements.
- **Community-Centric Measurements**: Analyze community structures and interactions within social networks.
- **Content-Centric Measurements**: Evaluate content propagation and engagement metrics.
- **Network Measurements**: Perform network analysis on GitHub repositories and other social networks.
- **Plotting and Visualization**: Generate charts and visualizations for data insights.
- **Configurable Metrics**: Predefined configurations for various platforms (Twitter, Reddit, GitHub) and topics (e.g., cybersecurity, cryptocurrency).

---

## Installation

### Prerequisites

Ensure you have the following installed on your system:

- Python 3.7 or higher
- Conda (optional, for environment management)

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/pnnl/socialsim.git
   cd socialsim
   ```

2. Install dependencies using `pip`:
   ```
   pip install -r pip_requirements.txt
   ```

   Alternatively, you can use Conda:
   ```
   conda create --name mcp_plugin_env --file conda_requirements.txt
   conda activate mcp_plugin_env
   ```

3. Verify the installation:
   ```
   python -m december-measurements.run_measurements_and_metrics --help
   ```

---

## Usage

### Running Measurements and Metrics

The main entry point for executing measurements and metrics is the `run_measurements_and_metrics` command. Use the following syntax:

```
python december-measurements/run_measurements_and_metrics.py --config <path_to_config_file>
```

Replace `<path_to_config_file>` with the path to the desired configuration file. Example configuration files are available in the `december-measurements/config` directory.

### Example Usage

To run baseline metrics for Twitter data:

```
python december-measurements/run_measurements_and_metrics.py --config december-measurements/config/baseline_metrics_config_twitter.py
```

To reconstruct cascades from Twitter data:

```
python december-measurements/cascade_reconstruction/twitter_cascade_reconstruction.py --input <input_file> --output <output_file>
```

---

## Available Tool Endpoints

### Core Modules

1. **Validators** (`december-measurements/validators.py`)
   - `check_empty`: Validates if the input data is empty.
   - `check_root_only`: Validates if the input data contains only root nodes.

2. **Community-Centric Measurements** (`december-measurements/CommunityCentricMeasurements.py`)
   - Class: `CommunityCentricMeasurements`

3. **Cascade Measurements** (`december-measurements/cascade_measurements.py`)
   - Functions:
     - `get_original_tweet_ratio`
     - `igraph_add_edges_to_existing_graph`
     - `igraph_from_pandas_edgelist`
   - Classes:
     - `Cascade`
     - `CascadeCollectionMeasurements`
     - `SingleCascadeMeasurements`

4. **Content-Centric Measurements** (`december-measurements/ContentCentricMeasurements.py`)
   - Class: `ContentCentricMeasurements`

5. **Network Measurements** (`december-measurements/network_measurements.py`)
   - Classes:
     - `GithubNetworkMeasurements`
     - `NetworkMeasurements`

### CLI Commands

- **Run Measurements and Metrics** (`december-measurements/run_measurements_and_metrics.py`)
  - Main entry point for executing measurement and metrics calculations.

---

## Configuration Files

The repository includes a variety of configuration files for different platforms and topics. These files are located in the `december-measurements/config` directory. Below is a list of available configurations:

- `baseline_metrics_config_twitter.py`
- `baseline_metrics_config_reddit.py`
- `baseline_metrics_config_github.py`
- `cascade_metrics_config.py`
- `network_metrics_config.py`

Each configuration file is tailored for specific platforms or analysis types. Modify these files to suit your data and analysis requirements.

---

## Notes and Troubleshooting

1. **Python Version**: Ensure you are using Python 3.7 or higher. Older versions may not support some dependencies.
2. **Dependencies**: If you encounter issues with missing libraries, ensure all required dependencies are installed using `pip_requirements.txt` or `conda_requirements.txt`.
3. **Configuration Files**: Double-check the paths and parameters in the configuration files before running any commands.
4. **Data Format**: Ensure your input data is in the correct format as expected by the tools. Refer to the example files in the repository for guidance.
5. **Visualization Issues**: If you encounter issues with plotting, ensure that `matplotlib` and `seaborn` are installed and updated to the latest versions.

---

## License

This project is licensed under the terms of the [license.txt](license.txt) file included in the repository.

---

## Contributing

Contributions are welcome! If you would like to contribute to the MCP Plugin, please fork the repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss your ideas.

---

## Support

For any issues or questions, please open an issue in the [GitHub repository](https://github.com/pnnl/socialsim).