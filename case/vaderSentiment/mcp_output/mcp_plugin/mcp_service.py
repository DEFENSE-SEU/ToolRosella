import os
import sys

source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
if source_path not in sys.path:
    sys.path.insert(0, source_path)

from fastmcp import FastMCP
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

mcp = FastMCP("vaderSentiment_service")

# Initialize the sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

@mcp.tool(name="analyze_sentiment", description="Analyze sentiment of text using VADER. Returns sentiment scores (positive, negative, neutral, compound)")
def analyze_sentiment(text: str):
    """
    Analyze the sentiment of the given text.

    Args:
        text: The text to analyze

    Returns:
        Dictionary with sentiment scores: neg, neu, pos, compound
        - neg: negative sentiment score (0 to 1)
        - neu: neutral sentiment score (0 to 1)
        - pos: positive sentiment score (0 to 1)
        - compound: overall sentiment score (-1 to 1, normalized)
    """
    try:
        scores = analyzer.polarity_scores(text)
        return {"success": True, "result": scores, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="get_word_valence", description="Get the sentiment valence score for a specific word from VADER lexicon")
def get_word_valence(word: str):
    """
    Look up the sentiment valence of a word in the VADER lexicon.

    Args:
        word: The word to look up (case-insensitive)

    Returns:
        Dictionary with the word's valence score or None if not found
    """
    try:
        word_lower = word.lower()
        if word_lower in analyzer.lexicon:
            valence = analyzer.lexicon[word_lower]
            return {"success": True, "result": {"word": word, "valence": valence}, "error": None}
        else:
            return {"success": True, "result": None, "error": f"Word '{word}' not found in VADER lexicon"}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="get_emoji_description", description="Get the textual description of an emoji from VADER emoji lexicon")
def get_emoji_description(emoji: str):
    """
    Look up the textual description of an emoji.

    Args:
        emoji: The emoji character to look up

    Returns:
        Dictionary with the emoji's description or None if not found
    """
    try:
        if emoji in analyzer.emojis:
            description = analyzer.emojis[emoji]
            return {"success": True, "result": {"emoji": emoji, "description": description}, "error": None}
        else:
            return {"success": True, "result": None, "error": f"Emoji '{emoji}' not found in VADER emoji lexicon"}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}



def create_app():
    """Create and return FastMCP application instance"""
    return mcp

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)