import os
import sys

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

# Import statements
from december_measurements.validators import check_empty, check_root_only
from december_measurements.CommunityCentricMeasurements import CommunityCentricMeasurements
from december_measurements.cascade_measurements import (
    get_original_tweet_ratio,
    igraph_add_edges_to_existing_graph,
    igraph_from_pandas_edgelist,
    Cascade,
    CascadeCollectionMeasurements,
    SingleCascadeMeasurements,
)
from december_measurements.ContentCentricMeasurements import ContentCentricMeasurements
from december_measurements.network_measurements import GithubNetworkMeasurements, NetworkMeasurements

class Adapter:
    """
    Adapter class for MCP plugin to integrate with the socialsim repository.
    This class provides methods to utilize the identified classes and functions from the analysis result.
    """

    def __init__(self):
        """
        Initialize the Adapter class with default mode and status.
        """
        self.mode = "import"
        self.status = {"status": "success", "message": "Adapter initialized successfully."}

    # -------------------------------------------------------------------------
    # Validators Module Methods
    # -------------------------------------------------------------------------

    def call_check_empty(self, data):
        """
        Call the check_empty function from the validators module.

        Args:
            data (any): The data to check for emptiness.

        Returns:
            dict: A dictionary containing the status and result.
        """
        try:
            result = check_empty(data)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": f"Error in call_check_empty: {str(e)}"}

    def call_check_root_only(self, data):
        """
        Call the check_root_only function from the validators module.

        Args:
            data (any): The data to check for root-only condition.

        Returns:
            dict: A dictionary containing the status and result.
        """
        try:
            result = check_root_only(data)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": f"Error in call_check_root_only: {str(e)}"}

    # -------------------------------------------------------------------------
    # CommunityCentricMeasurements Class Methods
    # -------------------------------------------------------------------------

    def create_community_centric_measurements_instance(self, *args, **kwargs):
        """
        Create an instance of the CommunityCentricMeasurements class.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            dict: A dictionary containing the status and the instance.
        """
        try:
            instance = CommunityCentricMeasurements(*args, **kwargs)
            return {"status": "success", "instance": instance}
        except Exception as e:
            return {"status": "error", "message": f"Error in creating CommunityCentricMeasurements instance: {str(e)}"}

    # -------------------------------------------------------------------------
    # CascadeMeasurements Module Methods
    # -------------------------------------------------------------------------

    def call_get_original_tweet_ratio(self, *args, **kwargs):
        """
        Call the get_original_tweet_ratio function from the cascade_measurements module.

        Args:
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            dict: A dictionary containing the status and result.
        """
        try:
            result = get_original_tweet_ratio(*args, **kwargs)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": f"Error in call_get_original_tweet_ratio: {str(e)}"}

    def call_igraph_add_edges_to_existing_graph(self, *args, **kwargs):
        """
        Call the igraph_add_edges_to_existing_graph function from the cascade_measurements module.

        Args:
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            dict: A dictionary containing the status and result.
        """
        try:
            result = igraph_add_edges_to_existing_graph(*args, **kwargs)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": f"Error in call_igraph_add_edges_to_existing_graph: {str(e)}"}

    def call_igraph_from_pandas_edgelist(self, *args, **kwargs):
        """
        Call the igraph_from_pandas_edgelist function from the cascade_measurements module.

        Args:
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            dict: A dictionary containing the status and result.
        """
        try:
            result = igraph_from_pandas_edgelist(*args, **kwargs)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": f"Error in call_igraph_from_pandas_edgelist: {str(e)}"}

    def create_cascade_instance(self, *args, **kwargs):
        """
        Create an instance of the Cascade class.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            dict: A dictionary containing the status and the instance.
        """
        try:
            instance = Cascade(*args, **kwargs)
            return {"status": "success", "instance": instance}
        except Exception as e:
            return {"status": "error", "message": f"Error in creating Cascade instance: {str(e)}"}

    def create_cascade_collection_measurements_instance(self, *args, **kwargs):
        """
        Create an instance of the CascadeCollectionMeasurements class.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            dict: A dictionary containing the status and the instance.
        """
        try:
            instance = CascadeCollectionMeasurements(*args, **kwargs)
            return {"status": "success", "instance": instance}
        except Exception as e:
            return {"status": "error", "message": f"Error in creating CascadeCollectionMeasurements instance: {str(e)}"}

    def create_single_cascade_measurements_instance(self, *args, **kwargs):
        """
        Create an instance of the SingleCascadeMeasurements class.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            dict: A dictionary containing the status and the instance.
        """
        try:
            instance = SingleCascadeMeasurements(*args, **kwargs)
            return {"status": "success", "instance": instance}
        except Exception as e:
            return {"status": "error", "message": f"Error in creating SingleCascadeMeasurements instance: {str(e)}"}

    # -------------------------------------------------------------------------
    # ContentCentricMeasurements Class Methods
    # -------------------------------------------------------------------------

    def create_content_centric_measurements_instance(self, *args, **kwargs):
        """
        Create an instance of the ContentCentricMeasurements class.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            dict: A dictionary containing the status and the instance.
        """
        try:
            instance = ContentCentricMeasurements(*args, **kwargs)
            return {"status": "success", "instance": instance}
        except Exception as e:
            return {"status": "error", "message": f"Error in creating ContentCentricMeasurements instance: {str(e)}"}

    # -------------------------------------------------------------------------
    # NetworkMeasurements Module Methods
    # -------------------------------------------------------------------------

    def create_github_network_measurements_instance(self, *args, **kwargs):
        """
        Create an instance of the GithubNetworkMeasurements class.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            dict: A dictionary containing the status and the instance.
        """
        try:
            instance = GithubNetworkMeasurements(*args, **kwargs)
            return {"status": "success", "instance": instance}
        except Exception as e:
            return {"status": "error", "message": f"Error in creating GithubNetworkMeasurements instance: {str(e)}"}

    def create_network_measurements_instance(self, *args, **kwargs):
        """
        Create an instance of the NetworkMeasurements class.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            dict: A dictionary containing the status and the instance.
        """
        try:
            instance = NetworkMeasurements(*args, **kwargs)
            return {"status": "success", "instance": instance}
        except Exception as e:
            return {"status": "error", "message": f"Error in creating NetworkMeasurements instance: {str(e)}"}