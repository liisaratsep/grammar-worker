import itertools
import logging
from typing import List

from .dataclasses import Response, Request
from .utils import sentence_tokenize, generate_spans

logger = logging.getLogger("gec_worker")


class GEC:
    model = None

    def __init__(self, checkpoint_path: str, source_language: str, target_language: str):
        from .modular_interface import ModularHubInterface
        self.model = ModularHubInterface.from_pretrained(
            model_path=f'{checkpoint_path}/checkpoint_best.pt',
            sentencepiece_prefix=f'{checkpoint_path}/spm',
            dictionary_path=checkpoint_path)
        self.source_language = source_language
        self.target_language = target_language
        logger.info("All models loaded")

    def correct(self, sentences: List[str], source_language, target_language) -> List[str]:
        return self.model.translate(sentences, src_language=source_language, tgt_language=target_language)

    def process_request(self, request: Request) -> Response:
        sentences, delimiters = sentence_tokenize(request.text)
        predictions = [correction.strip() if sentences[idx] != '' else '' for idx, correction in enumerate(
            self.correct(sentences, self.source_language, self.target_language))]

        corrected = ''.join(itertools.chain.from_iterable(zip(delimiters, predictions))) + delimiters[-1]
        logger.debug(corrected)

        corrections = generate_spans(sentences, predictions, delimiters)
        response = Response(corrections=corrections, original_text=request.text, corrected_text=corrected)

        logger.debug(response)

        return response
