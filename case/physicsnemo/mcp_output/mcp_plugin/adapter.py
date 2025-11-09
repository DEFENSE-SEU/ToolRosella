import os
import sys
from typing import Dict, Any

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

# Import statements
from physicsnemo.constants import diff
from physicsnemo.metrics.general.mse import mse, rmse
from physicsnemo.metrics.general.histogram import cdf, histogram, linspace, normal_cdf, normal_pdf
from physicsnemo.metrics.general.power_spectrum import power_spectrum
from physicsnemo.metrics.general.wasserstein import wasserstein_from_cdf, wasserstein_from_normal, wasserstein_from_samples
from physicsnemo.metrics.general.crps import crps, kcrps
from physicsnemo.metrics.general.entropy import entropy_from_counts, relative_entropy_from_counts
from physicsnemo.metrics.general.calibration import find_rank, rank_probability_score
from physicsnemo.metrics.diffusion.fid import calculate_fid_from_inception_stats
from physicsnemo.metrics.cae.integral import line_integral, surface_integral
from physicsnemo.metrics.cae.cfd import compute_force_coefficients, compute_frontal_area, compute_p_q_r, compute_tke_spectrum, dominant_freq_calc
from physicsnemo.metrics.climate.efi import efi, efi_gaussian, normalized_entropy
from physicsnemo.metrics.climate.reduction import global_mean, global_var, zonal_mean, zonal_var
from physicsnemo.metrics.climate.acc import acc
from physicsnemo.utils.version_check import check_min_version, check_module_requirements, require_version
from physicsnemo.utils.filesystem import Package
from physicsnemo.utils.patching import image_batching, image_fuse
from physicsnemo.utils.capture import StaticCaptureEvaluateNoGrad, StaticCaptureTraining
from physicsnemo.utils.insolation import insolation
from physicsnemo.utils.zenith_angle import cos_zenith_angle, cos_zenith_angle_from_timestamp, irradiance, toa_incident_solar_radiation_accumulated
from physicsnemo.utils.sdf import signed_distance_field
from physicsnemo.utils.mesh.generate_stl import sdf_to_stl
from physicsnemo.utils.mesh.convert_file_formats import convert_obj_to_vtp, convert_tesselated_files_in_directory, convert_vtp_to_stl
from physicsnemo.utils.mesh.combine_vtp_files import combine_vtp_files
from physicsnemo.utils.domino.utils import (
    area_weighted_shuffle_array, calculate_center_of_mass, calculate_normal_positional_encoding, calculate_pos_encoding,
    combine_dict, create_directory, create_grid, dict_to_device, get_filenames, mean_std_sampling, nd_interpolator,
    normalize, pad, pad_inp, sample_points_on_mesh, shuffle_array, shuffle_array_without_sampling,
    solution_weighted_shuffle_array, standardize, unnormalize, unstandardize
)
from physicsnemo.utils.domino.vtk_file_utils import (
    convert_point_data_to_cell_data, convert_to_tet_mesh, extract_surface_triangles, get_fields, get_fields_from_cell,
    get_node_to_elem, get_surface_data, get_vertices, get_volume_data, write_to_vtp, write_to_vtu
)
from physicsnemo.utils.diffusion.utils import (
    assert_shape, call_func_by_name, check_ddp_consistency, constant, construct_class_by_name, convert_datetime_to_cftime,
    copy_files_and_create_dirs, copy_params_and_buffers, ddp_sync, format_time, format_time_brief, get_dtype_and_ctype,
    get_module_dir_by_obj_name, get_module_from_obj_name, get_obj_by_name, get_obj_from_module, get_top_level_function_name,
    is_top_level_function, list_dir_recursively_with_ignore, named_params_and_buffers, params_and_buffers, parse_int_list,
    print_module_summary, profiled_function, suppress_tracer_warnings, time_range, tuple_product
)
from physicsnemo.utils.diffusion.deterministic_sampler import deterministic_sampler
from physicsnemo.utils.diffusion.stochastic_sampler import stochastic_sampler
from physicsnemo.launch.utils.checkpoint import get_checkpoint_dir, load_checkpoint, save_checkpoint
from physicsnemo.launch.logging.mlflow import check_mlflow_logged_in, initialize_mlflow
from physicsnemo.launch.logging.wandb import alert, initialize_wandb, is_wandb_initialized
from physicsnemo.launch.logging.utils import create_ddp_group_tag

# MCP Service Tools
class MCPService:
    """
    MCP Service Tools for PhysicsNeMo repository integration.
    Provides tools for various functionalities including training, deployment, active learning, and more.
    """

    @staticmethod
    @mcp.tool(name="calculate_diff", description="Calculate the difference between two values.")
    def calculate_diff(a: float, b: float) -> Dict[str, Any]:
        try:
            result = diff(a, b)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="mean_squared_error", description="Calculate the mean squared error between two arrays.")
    def mean_squared_error(y_true: list, y_pred: list) -> Dict[str, Any]:
        try:
            result = mse(y_true, y_pred)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="root_mean_squared_error", description="Calculate the root mean squared error between two arrays.")
    def root_mean_squared_error(y_true: list, y_pred: list) -> Dict[str, Any]:
        try:
            result = rmse(y_true, y_pred)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="compute_cdf", description="Compute the cumulative distribution function (CDF) for given data.")
    def compute_cdf(data: list) -> Dict[str, Any]:
        try:
            result = cdf(data)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="compute_histogram", description="Compute the histogram for given data.")
    def compute_histogram(data: list, bins: int) -> Dict[str, Any]:
        try:
            result = histogram(data, bins)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="compute_power_spectrum", description="Calculate the power spectrum of a signal.")
    def compute_power_spectrum(signal: list) -> Dict[str, Any]:
        try:
            result = power_spectrum(signal)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="wasserstein_distance_from_samples", description="Calculate Wasserstein distance between two sample distributions.")
    def wasserstein_distance_from_samples(samples1: list, samples2: list) -> Dict[str, Any]:
        try:
            result = wasserstein_from_samples(samples1, samples2)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="compute_crps", description="Calculate the Continuous Ranked Probability Score (CRPS).")
    def compute_crps(observations: list, forecasts: list) -> Dict[str, Any]:
        try:
            result = crps(observations, forecasts)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="compute_entropy_from_counts", description="Calculate entropy from counts.")
    def compute_entropy_from_counts(counts: list) -> Dict[str, Any]:
        try:
            result = entropy_from_counts(counts)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="compute_relative_entropy_from_counts", description="Calculate relative entropy from counts.")
    def compute_relative_entropy_from_counts(counts1: list, counts2: list) -> Dict[str, Any]:
        try:
            result = relative_entropy_from_counts(counts1, counts2)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="compute_line_integral", description="Calculate the line integral of a vector field.")
    def compute_line_integral(vector_field: list, path: list) -> Dict[str, Any]:
        try:
            result = line_integral(vector_field, path)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="compute_surface_integral", description="Calculate the surface integral of a vector field.")
    def compute_surface_integral(vector_field: list, surface: list) -> Dict[str, Any]:
        try:
            result = surface_integral(vector_field, surface)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="initialize_mlflow", description="Initialize MLflow for experiment tracking.")
    def initialize_mlflow_tracking(experiment_name: str, tracking_uri: str) -> Dict[str, Any]:
        try:
            initialize_mlflow(experiment_name, tracking_uri)
            return {"success": True, "result": "MLflow initialized successfully.", "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="initialize_wandb", description="Initialize Weights & Biases for experiment tracking.")
    def initialize_wandb_tracking(project_name: str, entity: str) -> Dict[str, Any]:
        try:
            initialize_wandb(project_name, entity)
            return {"success": True, "result": "Weights & Biases initialized successfully.", "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="check_wandb_initialized", description="Check if Weights & Biases is initialized.")
    def check_wandb_initialized_status() -> Dict[str, Any]:
        try:
            result = is_wandb_initialized()
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="create_ddp_group_tag", description="Create a distributed data parallel group tag.")
    def create_ddp_group_tag(group_name: str) -> Dict[str, Any]:
        try:
            result = create_ddp_group_tag(group_name)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="get_checkpoint_directory", description="Get the directory for saving checkpoints.")
    def get_checkpoint_directory(base_dir: str, experiment_name: str) -> Dict[str, Any]:
        try:
            result = get_checkpoint_dir(base_dir, experiment_name)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="load_checkpoint", description="Load a checkpoint from a file.")
    def load_checkpoint_file(checkpoint_path: str) -> Dict[str, Any]:
        try:
            result = load_checkpoint(checkpoint_path)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="save_checkpoint", description="Save a checkpoint to a file.")
    def save_checkpoint_file(checkpoint_path: str, data: dict) -> Dict[str, Any]:
        try:
            save_checkpoint(checkpoint_path, data)
            return {"success": True, "result": "Checkpoint saved successfully.", "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    @mcp.tool(name="check_mlflow_logged_in", description="Check if MLflow is logged in.")
    def check_mlflow_logged_in_status() -> Dict[str, Any]:
        try:
            result = check_mlflow_logged_in()
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}