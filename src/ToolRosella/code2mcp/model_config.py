from dataclasses import dataclass
@dataclass
class ModelConfig:
    provider: str  
    model_version: str
    api_key: str
    base_url: str
    temperature: float = 0.1
    max_tokens: int = 8192
    timeout: int = 180  
    max_retries: int = 10 