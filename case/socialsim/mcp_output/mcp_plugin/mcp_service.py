import os
import sys
import importlib

source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
if source_path not in sys.path:
    sys.path.insert(0, source_path)

from fastmcp import FastMCP

# ==================== Import modules with hyphens in their names ====================

# Load december-measurements modules
validators = importlib.import_module('december-measurements.validators')
fn_check_root_only = validators.check_root_only
fn_check_empty = validators.check_empty

ccm = importlib.import_module('december-measurements.CommunityCentricMeasurements')
cls_CommunityCentricMeasurements = ccm.CommunityCentricMeasurements

cascade_measurements = importlib.import_module('december-measurements.cascade_measurements')
fn_igraph_from_pandas_edgelist = cascade_measurements.igraph_from_pandas_edgelist
fn_igraph_add_edges_to_existing_graph = cascade_measurements.igraph_add_edges_to_existing_graph
cls_CascadeCollectionMeasurements = cascade_measurements.CascadeCollectionMeasurements
fn_get_original_tweet_ratio = cascade_measurements.get_original_tweet_ratio
cls_Cascade = cascade_measurements.Cascade
cls_SingleCascadeMeasurements = cascade_measurements.SingleCascadeMeasurements
fn_igraph_wiener_index = cascade_measurements.igraph_wiener_index
fn_palma_ratio = cascade_measurements.palma_ratio

ccm_content = importlib.import_module('december-measurements.ContentCentricMeasurements')
cls_ContentCentricMeasurements = ccm_content.ContentCentricMeasurements

network_measurements = importlib.import_module('december-measurements.network_measurements')
cls_GithubNetworkMeasurements = network_measurements.GithubNetworkMeasurements
cls_NetworkMeasurements = network_measurements.NetworkMeasurements
cls_RedditNetworkMeasurements = network_measurements.RedditNetworkMeasurements
cls_TwitterNetworkMeasurements = network_measurements.TwitterNetworkMeasurements

user_centric = importlib.import_module('december-measurements.UserCentricMeasurements')
cls_UserCentricMeasurements = user_centric.UserCentricMeasurements

baseline_measurements = importlib.import_module('december-measurements.BaselineMeasurements')
cls_BaselineMeasurements = baseline_measurements.BaselineMeasurements

# ==================== Create FastMCP instance ====================
mcp = FastMCP("socialsim_mcp")

# ==================== December Measurements Validators ====================

@mcp.tool(name="check_empty", description="Check if data is empty")
def tool_check_empty(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        result = fn_check_empty(*args, **kwargs)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="check_root_only", description="Check if root only")
def tool_check_root_only(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        result = fn_check_root_only(*args, **kwargs)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

# ==================== December Measurements Cascade Functions ====================

@mcp.tool(name="igraph_from_pandas_edgelist", description="Create igraph from pandas edgelist")
def tool_igraph_from_pandas_edgelist(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        result = fn_igraph_from_pandas_edgelist(*args, **kwargs)
        return {"success": True, "result": str(result), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="igraph_add_edges_to_existing_graph", description="Add edges to igraph")
def tool_igraph_add_edges_to_existing_graph(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        result = fn_igraph_add_edges_to_existing_graph(*args, **kwargs)
        return {"success": True, "result": str(result), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="igraph_wiener_index", description="Calculate Wiener index for igraph")
def tool_igraph_wiener_index(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        result = fn_igraph_wiener_index(*args, **kwargs)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="get_original_tweet_ratio", description="Get original tweet ratio")
def tool_get_original_tweet_ratio(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        result = fn_get_original_tweet_ratio(*args, **kwargs)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="palma_ratio", description="Calculate Palma ratio")
def tool_palma_ratio(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        result = fn_palma_ratio(*args, **kwargs)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

# ==================== Classes ====================

@mcp.tool(name="communitycentricmeasurements", description="CommunityCentricMeasurements class constructor")
def tool_communitycentricmeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_CommunityCentricMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="cascade", description="Cascade class constructor")
def tool_cascade(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_Cascade(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="cascadecollectionmeasurements", description="CascadeCollectionMeasurements class constructor")
def tool_cascadecollectionmeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_CascadeCollectionMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="singlecascademeasurements", description="SingleCascadeMeasurements class constructor")
def tool_singlecascademeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_SingleCascadeMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="contentcentricmeasurements", description="ContentCentricMeasurements class constructor")
def tool_contentcentricmeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_ContentCentricMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="githubnetworkmeasurements", description="GithubNetworkMeasurements class constructor")
def tool_githubnetworkmeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_GithubNetworkMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="networkmeasurements", description="NetworkMeasurements class constructor")
def tool_networkmeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_NetworkMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="redditnetworkmeasurements", description="RedditNetworkMeasurements class constructor")
def tool_redditnetworkmeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_RedditNetworkMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="twitternetworkmeasurements", description="TwitterNetworkMeasurements class constructor")
def tool_twitternetworkmeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_TwitterNetworkMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="usercentricmeasurements", description="UserCentricMeasurements class constructor")
def tool_usercentricmeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_UserCentricMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="baselinemeasurements", description="BaselineMeasurements class constructor")
def tool_baselinemeasurements(payload: dict):
    try:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        instance = cls_BaselineMeasurements(*args, **kwargs)
        return {"success": True, "result": str(instance), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

def create_app():
    """Create and return FastMCP application instance"""
    return mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
