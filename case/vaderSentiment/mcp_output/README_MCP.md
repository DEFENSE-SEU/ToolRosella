# VADER Sentiment Analysis Plugin

## Overview

VADER (Valence Aware Dictionary and sEntiment Reasoner) is a lexicon and rule-based sentiment analysis tool specifically designed for analyzing sentiments expressed in social media text. This plugin provides an integration of VADER for sentiment analysis tasks, enabling users to evaluate the sentiment of textual data efficiently.

Key features include:
- **Lexicon-based sentiment analysis**: Predefined sentiment scores for words and phrases.
- **Emoji sentiment processing**: Built-in support for analyzing emojis.
- **Rule-based sentiment adjustment**: Context-aware sentiment evaluation.
- **Ease of use**: Simple API for quick integration into projects.

For more details, visit the [official repository](https://github.com/cjhutto/vaderSentiment).

---

## Installation

To install the plugin, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/cjhutto/vaderSentiment.git
   ```

2. Navigate to the project directory:
   ```
   cd vaderSentiment
   ```

3. Install the required dependencies:
   ```
   pip install numpy requests
   ```

4. (Optional) Install the package using `setup.py`:
   ```
   python setup.py install
   ```

---

## Usage

### Basic Usage

The primary functionality of the plugin is provided by the `SentimentIntensityAnalyzer` class. Below is an example of how to use it:

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
text = "VADER is amazing! 😍"
sentiment = analyzer.polarity_scores(text)
print(sentiment)
```

The output will include sentiment scores for:
- **Positive** (`pos`)
- **Neutral** (`neu`)
- **Negative** (`neg`)
- **Compound** (`compound`): Overall sentiment score.

### Advanced Usage

You can customize the sentiment analysis by modifying the lexicon or adding new rules. For example:
- Extend the lexicon with custom sentiment scores.
- Adjust sentiment weights for specific contexts.

Refer to the `vaderSentiment/vaderSentiment.py` file for detailed implementation and customization options.

---

## Tool Endpoints

The plugin provides the following key components:

### Classes
- **SentimentIntensityAnalyzer**: Core class for sentiment analysis.

### Functions
- **append_to_file**: Utility function for file operations (found in `additional_resources/build_emoji_lexicon.py`).
- **get_list_from_file**: Reads and processes data from files.
- **pad_ref**: Helper function for formatting data.

### Lexicon Files
- **vader_lexicon.txt**: Contains predefined sentiment scores for words and phrases.
- **emoji_utf8_lexicon.txt**: Sentiment scores for emojis.

---

## Notes and Troubleshooting

### Common Issues
1. **Missing Dependencies**: Ensure `numpy` and `requests` are installed.
   ```
   pip install numpy requests
   ```
2. **File Encoding Errors**: If you encounter encoding issues, ensure your environment supports UTF-8.

### Tips
- For large-scale sentiment analysis, preprocess your data to remove unnecessary noise (e.g., HTML tags, special characters).
- Use the `emoji_utf8_lexicon.txt` file to enhance sentiment analysis for text containing emojis.

### Reporting Issues
If you encounter any problems, please report them on the [GitHub Issues page](https://github.com/cjhutto/vaderSentiment/issues).

---

## Development and Contribution

Contributions to the project are welcome! To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

---

## License

This project is licensed under the MIT License. See the [LICENSE.txt](LICENSE.txt) file for details.

---

## Additional Resources

- **Emoji Lexicon Builder**: `additional_resources/build_emoji_lexicon.py` provides tools for extending the emoji lexicon.
- **Documentation**: Refer to the `README.md` and `vaderSentiment/vaderSentiment.py` for detailed explanations of the system.

---

## Acknowledgments

VADER was developed by C.J. Hutto and Eric Gilbert. It is widely used in research and industry for sentiment analysis tasks. For more information, visit the [official repository](https://github.com/cjhutto/vaderSentiment).