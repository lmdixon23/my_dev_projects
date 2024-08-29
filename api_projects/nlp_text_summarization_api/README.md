# NLP Text Summarization CLI

## Overview

**NLP_Text_Summarization_CLI** is a Python-based command-line application that leverages the power of OpenAI's GPT models to generate concise summaries of large text inputs. The application is designed with user experience in mind, featuring intelligent rate limiting, batch processing, API key rotation, and a feedback system for continuous improvement. This project is ideal for applications in content management, news aggregation, educational tools, and more.

## Key Features

- **Intelligent Rate Limiting**: Automatically adjusts request frequency using exponential backoff and retry logic to avoid hitting API rate limits.
- **Batch Request Optimization**: Processes multiple text inputs in parallel to improve efficiency and reduce the chances of exceeding rate limits.
- **API Key Rotation**: Supports multiple API keys, rotating between them to ensure continuous operation even if one key hits its quota.
- **User Feedback Integration**: Collects and stores user feedback on the summaries to help fine-tune and personalize future results.
- **Advanced Data Analysis**: Analyzes trends in the text summaries over time, providing insights into patterns, token usage, and recurring themes.
- **Dynamic Model and Language Support**: Supports a variety of models and languages, manually configured to ensure users always have the most up-to-date options.

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Input Text**: Provide one or more blocks of text as input.
- **API Request**: The application sends the text to the OpenAI API for processing.
- **Summary Generation**: The API returns a concise summary of the input text, which is then displayed in the terminal.
- **User Feedback**: Provide feedback on the summaries, which is stored for further analysis.
- **Analysis**: Optionally analyze the stored summaries and their metadata to gain insights into the summarization process.

## Installation

### Prerequisites

- **Python**: Ensure you have Python 3.8 or higher installed. You can download Python from [python.org](https://www.python.org/).
- **OpenAI API Key**: You'll need an API key from OpenAI. Sign up and get your key from [platform.openai.com](https://platform.openai.com).

### Setup

1. **Clone the repository**:

    ```bash
    git clone https://github.com/lmdixon23/nlp_text_summarization_cli.git
    cd nlp_text_summarization_cli
    ```

2. **Create a virtual environment**:

    ```bash
    python -m venv venv
    ```

3. **Activate the virtual environment**:

    - On Windows:
        ```bash
        venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

5. **Set Up Environment Variables**:

    Create a `.env` file in the root directory and add your OpenAI API keys:

    ```env
    OPENAI_API_KEY=your_openai_api_key_here
    OPENAI_API_KEY_2=your_second_openai_api_key_here
    ```

## Usage

1. **Run the Application**:

    ```bash
    python main.py
    ```

2. **Follow the prompts** to select the model, set the maximum tokens, choose the language, and enter the text you want to summarize.

3. **Provide feedback** on the summaries if prompted.

4. **Analyze Summaries** (optional): After generating summaries, you have the option to analyze them to gain insights into token usage and summary content.

## Future Enhancements

- **Contextual Summarization**: Implement a feature that allows users to provide context or keywords that the summarization should focus on, enhancing the relevance of the generated summaries.
- **User Profile Management**: Allow users to create and save profiles with their preferred settings (e.g., model, max tokens, language) to streamline repeated use of the tool.
- **Voice Input and Output**: Integrate speech recognition and text-to-speech features to allow users to provide input and receive output via voice, making the tool accessible to a broader audience.
- **Cross-Platform GUI Application**: Develop a cross-platform graphical user interface (GUI) using frameworks like Electron or PyQt, making the application more accessible to users who prefer not to use the command line.
- **Adaptive Learning and Improvement**: Implement a machine learning model that continuously learns from user feedback to improve the accuracy and relevance of the summaries over time.
- **Summarization Metrics**: Add features that generate and display metrics related to the summarization, such as compression ratio, relevance score, and coherence score.
- **Multi-Language Summarization**: Allow users to input text in one language and get the summary in another, combining translation and summarization.
- **Integration with Content Management Systems (CMS)**: Develop plugins or integrations for popular CMS platforms like WordPress, enabling direct summarization within these systems.
- **API Versioning Support**: Implement support for different versions of the OpenAI API, allowing users to select which version they want to use, ensuring compatibility with future API changes.
- **Custom Model Support**: Allow users to upload and use their fine-tuned GPT models or other NLP models for specialized summarization tasks.
- **Real-Time Summarization**: Implement a real-time summarization feature that generates summaries on-the-fly as the user types or uploads content.
- **Collaboration and Sharing Features**: Enable users to collaborate on summarizations by sharing input texts, summaries, and feedback with others.
- **Data Export and Import**: Provide options for exporting and importing summaries and feedback in various formats (e.g., JSON, CSV, XML) for integration with other tools.
- **Enhanced Security and Privacy**: Implement advanced security measures such as end-to-end encryption, user authentication, and data anonymization to protect user data.
- **Scheduled Summarization**: Allow users to schedule summarization tasks to run at specific times or intervals, automating the process for regular content updates.
- **Mobile Application Development**: Develop a mobile app version of the tool, allowing users to summarize text on-the-go using their smartphones or tablets.
- **Interactive Summarization**: Implement a feature where users can interactively refine and adjust summaries by providing feedback in real-time.
- **API Integration for Third-Party Services**: Allow integration with third-party services like Slack, Google Docs, or Microsoft Word, enabling users to send content directly to the summarization tool from these platforms.
- **Advanced Logging and Monitoring**: Implement detailed logging and monitoring features that track API usage, performance metrics, and user interactions, with visualization options through dashboards.

## Contributing

I welcome contributions from the community to enhance the features, security, and performance of this project. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or partnership opportunities, please contact lmdixon23@gmail.com.