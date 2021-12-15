import itertools
import logging
import os
from typing import List
import warnings

from .config import ModelConfig
from .dataclasses import Response, Request
from .utils import sentence_tokenize, generate_spans
from .modular_interface import ModularHubInterface

logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore', '.*__floordiv__*', )


class GEC:
    model = None

    def __init__(self, model_config: ModelConfig):
        self.model_config = model_config

        sentencepiece_path = os.path.join(self.model_config.sentencepiece_dir, self.model_config.sentencepiece_prefix)
        self.model = ModularHubInterface.from_pretrained(
            model_path=self.model_config.checkpoint_path,
            sentencepiece_prefix=sentencepiece_path,
            dictionary_path=self.model_config.dict_dir)
        self.source_language = self.model_config.source_language
        self.target_language = self.model_config.target_language
        logger.info("All models loaded")

    def correct(self, sentences: List[str]) -> List[str]:
        return self.model.translate(sentences,
                                    src_language=self.model_config.source_language,
                                    tgt_language=self.model_config.target_language)

    def process_request(self, request: Request) -> Response:
        sentences, delimiters = sentence_tokenize(request.text)
        predictions = [correction.strip() if sentences[idx] != '' else '' for idx, correction in enumerate(
            self.correct(sentences))]

        corrected = ''.join(itertools.chain.from_iterable(zip(delimiters, predictions))) + delimiters[-1]
        logger.debug(corrected)

        corrections = generate_spans(sentences, predictions, delimiters)
        response = Response(corrections=corrections, original_text=request.text, corrected_text=corrected)

        logger.debug(response)

        return response
