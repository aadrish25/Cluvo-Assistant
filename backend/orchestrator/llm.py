from agno.models.ollama import Ollama
from dotenv import load_dotenv

load_dotenv()


class Gemma4_31B:
    def __init__(self):
        self.model = Ollama(id="gemma4:31b-cloud")
        
    def get_model(self):
        return self.model
        
        
gemma4_31b = Gemma4_31B().get_model()