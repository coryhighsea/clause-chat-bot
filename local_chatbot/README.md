# Local LLM Chatbot with Ollama API

A simple graphical user interface to interact with local language models using the Ollama API.

## Prerequisites

1. Install [Ollama](https://ollama.ai/)
2. Pull your preferred model(s) with Ollama, for example:
   ```
   ollama pull gemma
   ollama pull llama3
   ollama pull mistral
   ```
3. Python 3.8+ with pip

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Make sure Ollama is running:
   ```
   ollama serve
   ```
   Note: This should be running in a separate terminal window while you use the chatbot.

## Usage

1. Start the chatbot application:
   ```
   python local_chatbot/main.py
   ```

2. The GUI will appear:
   - Use the model dropdown to select which model to use
   - Type your message in the bottom text area
   - Click "Send" to get a response from the selected model

3. If you've pulled new models after starting the application, click the "Refresh" button to update the model list.

## Troubleshooting

- If you see an error message about connecting to the Ollama API, make sure Ollama is running with `ollama serve`
- If a specific model isn't available in the dropdown, make sure you've pulled it with `ollama pull MODEL_NAME`

## License

MIT 