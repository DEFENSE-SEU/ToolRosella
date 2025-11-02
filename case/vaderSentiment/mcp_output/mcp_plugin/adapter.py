import os
import sys

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

# Import statements
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from additional_resources.build_emoji_lexicon import append_to_file, get_list_from_file, pad_ref

class Adapter:
    """
    Adapter class for MCP plugin integration with the VADER Sentiment Analysis tool.
    Provides methods to utilize identified classes and functions from the analysis result.
    """

    def __init__(self):
        """
        Initializes the Adapter class with default mode and checks for import feasibility.
        """
        self.mode = "import"
        self.status = {"status": "success", "message": "Adapter initialized successfully."}
        try:
            self.analyzer = SentimentIntensityAnalyzer()
        except ImportError as e:
            self.mode = "fallback"
            self.status = {"status": "error", "message": f"Failed to import SentimentIntensityAnalyzer: {str(e)}"}

    # -------------------------------------------------------------------------
    # SentimentIntensityAnalyzer Methods
    # -------------------------------------------------------------------------

    def analyze_sentiment(self, text):
        """
        Analyzes the sentiment of the given text using SentimentIntensityAnalyzer.

        Parameters:
            text (str): The text to analyze.

        Returns:
            dict: A dictionary containing sentiment scores or error status.
        """
        try:
            if self.mode == "fallback":
                return {"status": "error", "message": "Sentiment analysis unavailable in fallback mode."}
            sentiment_scores = self.analyzer.polarity_scores(text)
            return {"status": "success", "data": sentiment_scores}
        except Exception as e:
            return {"status": "error", "message": f"Error analyzing sentiment: {str(e)}"}

    # -------------------------------------------------------------------------
    # Build Emoji Lexicon Methods
    # -------------------------------------------------------------------------

    def append_to_file(self, file_path, content):
        """
        Appends content to a file using the append_to_file function.

        Parameters:
            file_path (str): Path to the file.
            content (str): Content to append.

        Returns:
            dict: A dictionary indicating success or error status.
        """
        try:
            append_to_file(file_path, content)
            return {"status": "success", "message": f"Content appended to {file_path} successfully."}
        except Exception as e:
            return {"status": "error", "message": f"Error appending to file: {str(e)}"}

    def get_list_from_file(self, file_path):
        """
        Retrieves a list of items from a file using the get_list_from_file function.

        Parameters:
            file_path (str): Path to the file.

        Returns:
            dict: A dictionary containing the list of items or error status.
        """
        try:
            data = get_list_from_file(file_path)
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": f"Error retrieving list from file: {str(e)}"}

    def pad_reference(self, reference, padding):
        """
        Pads a reference string using the pad_ref function.

        Parameters:
            reference (str): The reference string to pad.
            padding (int): The padding value.

        Returns:
            dict: A dictionary containing the padded reference or error status.
        """
        try:
            padded_ref = pad_ref(reference, padding)
            return {"status": "success", "data": padded_ref}
        except Exception as e:
            return {"status": "error", "message": f"Error padding reference: {str(e)}"}

    # -------------------------------------------------------------------------
    # Fallback Handling
    # -------------------------------------------------------------------------

    def fallback_message(self):
        """
        Provides a fallback message when the primary import mode fails.

        Returns:
            dict: A dictionary containing the fallback message.
        """
        if self.mode == "fallback":
            return {"status": "error", "message": "Primary import mode failed. Operating in fallback mode."}
        return {"status": "success", "message": "Primary import mode is active."}

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def check_status(self):
        """
        Checks the current status of the adapter.

        Returns:
            dict: A dictionary containing the adapter's status.
        """
        return self.status

    def reset_adapter(self):
        """
        Resets the adapter to its initial state.

        Returns:
            dict: A dictionary indicating the reset status.
        """
        try:
            self.__init__()
            return {"status": "success", "message": "Adapter reset successfully."}
        except Exception as e:
            return {"status": "error", "message": f"Error resetting adapter: {str(e)}"}