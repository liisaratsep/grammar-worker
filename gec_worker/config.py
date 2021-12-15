import yaml
from yaml.loader import SafeLoader

from pydantic import BaseSettings, BaseModel


class MQConfig(BaseSettings):
    """
    Imports MQ configuration from environment variables
    """
    host: str = 'localhost'
    port: int = 5672
    username: str = 'guest'
    password: str = 'guest'
    exchange: str = 'grammar'
    heartbeat: int = 60
    connection_name: str = 'Grammar worker'

    class Config:
        env_prefix = 'mq_'


class ModelConfig(BaseModel):
    language: str  # actual ISO input language code
    checkpoint_path: str = "models/checkpoint_best.pt"
    dict_dir: str = "models/dicts/"
    sentencepiece_dir: str = "models/sentencepiece/"
    sentencepiece_prefix: str = "sp-model"
    source_language: str = "et0"  # input language code
    target_language: str = "et1"  # target language code


def read_model_config(file_path: str) -> ModelConfig:
    with open(file_path, 'r', encoding='utf-8') as f:
        model_config = ModelConfig(**yaml.load(f, Loader=SafeLoader))

    return model_config
