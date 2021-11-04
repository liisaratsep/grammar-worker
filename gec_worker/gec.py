import itertools
import logging
from typing import List

from nltk import sent_tokenize
from .utils import Response, Request

logger = logging.getLogger("gec_worker")


class GEC:
    model = None

    def __init__(self, checkpoint_path: str, spm_prefix: str):
        from .modular_interface import ModularHubInterface
        self.model = ModularHubInterface.from_pretrained(
            model_path=f'{checkpoint_path}/checkpoint_best.pt',
            sentencepiece_prefix=spm_prefix,
            dictionary_path=checkpoint_path)
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

    def _generate_spans(self, original: str, corrected: str) -> Response:
        pass  # TODO

    def correct(self, sentences: List[str], language) -> List[str]:
        return self.model.translate(sentences, src_language=language, tgt_language=language)

    def process_request(self, request: Request) -> Response:
        sentences, delimiters = self._sentence_tokenize(request.text)
        predictions = [correction if sentences[idx] != '' else '' for idx, correction in enumerate(
            self.correct(sentences, request.language))]
        corrected = ''.join(itertools.chain.from_iterable(zip(delimiters, predictions))) + delimiters[-1]

        response = self._generate_spans(original=request.text, corrected=corrected)

        return response
