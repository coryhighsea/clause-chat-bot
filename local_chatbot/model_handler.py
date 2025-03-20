import requests
import json

class ModelHandler:
    def __init__(self, model_name="gemma3:4b", base_url="http://localhost:11434"):
        """Initialize the model handler to communicate with Ollama's API server.
        
        Args:
            model_name: The name of the model to use (as loaded in Ollama)
            base_url: URL for the Ollama API server (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"
        
        # Check if the model is available
        try:
            self._check_model()
            print(f"Successfully connected to Ollama API server at {base_url}")
            print(f"Using model: {model_name}")
        except Exception as e:
            print(f"Error connecting to Ollama API: {e}")
            print("Make sure Ollama is running ('ollama serve') and the model is pulled")

    def _check_model(self):
        """Check if the model is available in Ollama."""
        response = requests.get(f"{self.base_url}/api/tags")
        if response.status_code != 200:
            raise Exception(f"Failed to connect to Ollama API: {response.status_code}")
        
        models = response.json().get("models", [])
        self.available_models = [model.get("name") for model in models]
        
        # Check if the exact model name is available
        if self.model_name not in self.available_models:
            # If not found with exact name, check if it's available with a different tag
            model_base_name = self.model_name.split(':')[0]
            matching_models = [m for m in self.available_models if m.startswith(f"{model_base_name}:")]
            
            if matching_models:
                print(f"Model '{self.model_name}' not found exactly, but related models exist: {matching_models}")
            else:
                print(f"Warning: Model '{self.model_name}' not found in Ollama.")
                print(f"Available models: {self.available_models}")

    def get_response(self, prompt):
        """Get a response from the model via Ollama API.
        
        Args:
            prompt: The user's input prompt
            
        Returns:
            The model's response text
        """
        try:
            # Create the payload - explicitly disable streaming to avoid JSON parsing issues
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,  # Explicitly disable streaming
                "options": {
                    "num_predict": 1024  # Limit response length
                }
            }
            
            # Make the API request
            response = requests.post(self.api_endpoint, json=payload)
            
            # Check response status
            if response.status_code != 200:
                return f"Error: Failed to get response (Status code: {response.status_code})"
                
            # Parse the response
            try:
                result = response.json()
                return result.get("response", "No response generated")
            except json.JSONDecodeError as json_err:
                # Handle JSON parsing errors
                print(f"JSON parsing error: {json_err}")
                print(f"Response content: {response.text[:200]}...")  # Print first 200 chars for debugging
                
                # Try to extract response using a different approach for streaming-like responses
                if "response" in response.text:
                    try:
                        # Get the first complete JSON object
                        first_json_str = response.text.split('}\n{')[0] + '}'
                        partial_result = json.loads(first_json_str)
                        return partial_result.get("response", "")
                    except:
                        pass
                
                return "Error parsing model response. Please try again."
                
        except Exception as e:
            return f"Error communicating with Ollama API: {str(e)}"