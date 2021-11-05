import itertools
import logging
from typing import List
import word_diff

from nltk import sent_tokenize
from .utils import Response, Request, Correction, Replacement, Span

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

    @staticmethod
    def _generate_spans(original: str, corrected: str) -> Response:
        response = Response()
        original_w = word_diff.apply_weight(original.split(), 1)
        corrected_w = word_diff.apply_weight(corrected.split(), 2)
        combo = word_diff.join_sequences(original_w, corrected_w)
        beginning = ''
        for e in combo:
            if len(e) == 1:
                beginning += ' '.join(e[0][0]) + ' '
            else:
                ordered = sorted(e, key=lambda x: x[1])
                original_text = ' '.join(ordered[0][0]) + ' '
                correction_text = ' '.join(ordered[1][0]) + ' '

                start_in_original = len(beginning)
                if original_text != ' ':
                    beginning += original_text
                    end_in_original = len(beginning)
                else:
                    end_in_original = start_in_original + len(original_text)  # addition

                if correction_text != ' ':
                    replacements = [Replacement(correction_text)]
                else:
                    replacements = None  # deletion

                correction = Correction(Span(start_in_original, end_in_original), replacements)
                if response.corrections is None:
                    response.corrections = []
                response.corrections.append(correction)
        return response

    def correct(self, sentences: List[str], language) -> List[str]:
        return self.model.translate(sentences, src_language=language, tgt_language=language)

    def process_request(self, request: Request) -> Response:
        sentences, delimiters = self._sentence_tokenize(request.text)
        predictions = [correction if sentences[idx] != '' else '' for idx, correction in enumerate(
            self.correct(sentences, request.language))]
        corrected = ''.join(itertools.chain.from_iterable(zip(delimiters, predictions))) + delimiters[-1]

        response = self._generate_spans(original=request.text, corrected=corrected)

        return response
