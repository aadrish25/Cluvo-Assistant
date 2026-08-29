from agno.models.ollama import Ollama
from backend.config import OLLAMA_API_KEY
from dotenv import load_dotenv

load_dotenv()


class Gemma4_31B:
    def __init__(self):
        self.model = Ollama(id="gemma4:31b-cloud",api_key=OLLAMA_API_KEY)
        
    def get_model(self):
        return self.model
        
        
gemma4_31b = Gemma4_31B().get_model()