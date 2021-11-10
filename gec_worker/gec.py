import itertools
import logging
from typing import List

from nltk import sent_tokenize

from .dataclasses import Response, Request
from .word_diff import generate_spans

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

    @staticmethod
    def _sentence_tokenize(text: str) -> (List, List):
        """
        Split text into sentences and save info about delimiters between them to restore linebreaks,
        whitespaces, etc.
        """
        delimiters = []
        sentences = [sent.strip() for sent in sent_tokenize(text)]
        if len(sentences) == 0:
            return [''], ['']
        else:
            try:
                for sentence in sentences:
                    idx = text.index(sentence)
                    delimiters.append(text[:idx])
                    text = text[idx + len(sentence):]
                delimiters.append(text)
            except ValueError:
                delimiters = ['', *[' ' for _ in range(len(sentences) - 1)], '']

        return sentences, delimiters

    def correct(self, sentences: List[str], source_language, target_language) -> List[str]:
        return self.model.translate(sentences, src_language=source_language, tgt_language=target_language)

    def process_request(self, request: Request) -> Response:
        sentences, delimiters = self._sentence_tokenize(request.text)
        predictions = [correction if sentences[idx] != '' else '' for idx, correction in enumerate(
            self.correct(sentences, self.source_language, self.target_language))]
        corrected = ''.join(itertools.chain.from_iterable(zip(delimiters, predictions))) + delimiters[-1]
        logger.debug(corrected)

        response = generate_spans(original=request.text, corrected=corrected)
        logger.debug(response)

        return response
