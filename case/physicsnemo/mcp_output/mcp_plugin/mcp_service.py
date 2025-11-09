import os
import sys

source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

from fastmcp import FastMCP
from physicsnemo.active_learning.driver import Driver
from physicsnemo.launch.logging.launch import LaunchLogger
from physicsnemo.deploy.triton import deploy_model

mcp = FastMCP("physicsnemo_service")

@mcp.tool(name="run_active_learning", description="Run the active learning process using the Driver class.")
def run_active_learning_tool(config: dict, learner: object, strategies_config: dict, training_config: dict = None, inference_fn: object = None) -> dict:
    """
    Execute the active learning process using the Driver class.

    Parameters:
        config (dict): Configuration for the active learning driver.
        learner (object): Learner module for the active learning process.
        strategies_config (dict): Configuration for active learning strategies.
        training_config (dict, optional): Configuration for training components.
        inference_fn (object, optional): Custom inference function.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        driver = Driver(config, learner, strategies_config, training_config, inference_fn)
        result = driver.run()
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="log_minibatch", description="Log metrics for a mini-batch during training.")
def log_minibatch_tool(name_space: str, losses: dict, epoch: int = 1, num_mini_batch: int = None, profile: bool = False, mini_batch_log_freq: int = 100, epoch_alert_freq: int = None) -> dict:
    """
    Log metrics for a mini-batch during training.

    Parameters:
        name_space (str): Namespace of the logger.
        losses (dict): Dictionary containing loss metrics for the mini-batch.
        epoch (int, optional): Current epoch. Default is 1.
        num_mini_batch (int, optional): Number of mini-batches for epoch progress calculation.
        profile (bool, optional): Enable profiling using NVTX markers. Default is False.
        mini_batch_log_freq (int, optional): Frequency to log mini-batch losses. Default is 100.
        epoch_alert_freq (int, optional): Frequency to send training alerts. Default is None.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        logger = LaunchLogger(name_space, epoch, num_mini_batch, profile, mini_batch_log_freq, epoch_alert_freq)
        logger.log_minibatch(losses)
        return {"success": True, "result": "Mini-batch logged successfully.", "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="deploy_model", description="Deploy models using Triton inference server.")
def deploy_model_tool(model_path: str, config_path: str) -> dict:
    """
    Deploy models using Triton inference server.

    Parameters:
        model_path (str): Path to the model file to be deployed.
        config_path (str): Path to the configuration file for deployment.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        result = deploy_model(model_path, config_path)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="read_readme", description="Read the README file from the source directory.")
def read_readme_tool() -> dict:
    """
    Read the README file from the source directory.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        readme_path = os.path.join(source_path, "README.md")
        with open(readme_path, "r") as file:
            content = file.read()
        return {"success": True, "result": content, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="list_files", description="List all files in the source directory.")
def list_files_tool() -> dict:
    """
    List all files in the source directory.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        files = os.listdir(source_path)
        return {"success": True, "result": files, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

def create_app() -> FastMCP:
    """
    Create and return the FastMCP service application.

    Returns:
        FastMCP: The FastMCP instance for the service.
    """
    return mcp