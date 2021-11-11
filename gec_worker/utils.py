from typing import List
import re

from nltk import sent_tokenize
from difflib import SequenceMatcher

from .dataclasses import Correction, Span, Replacement

splitter = re.compile(r'(\s+)')


def sentence_tokenize(text: str) -> (List, List):
    """
    Split text into sentences or tokens, and save info about delimiters between them to restore linebreaks,
    whitespaces, etc.
    """
    delimiters = []
    tokens = [sent.strip() for sent in sent_tokenize(text)]

    if len(tokens) == 0:
        return [''], ['']
    else:
        try:
            for sentence in tokens:
                idx = text.index(sentence)
                delimiters.append(text[:idx])
                text = text[idx + len(sentence):]
            delimiters.append(text)
        except ValueError:
            delimiters = ['', *[' ' for _ in range(len(tokens) - 1)], '']

    return tokens, delimiters


def generate_spans(source_sentences: List[str], target_sentences: List[str], delimiters: List[str]) -> List[Correction]:
    span_shift = len(delimiters.pop(0))
    sentence_pairs = zip(delimiters, source_sentences, target_sentences)
    corrections = []

    for delimiter, source, target in sentence_pairs:
        # split into tokens and token delimiters (whitespaces)
        source_tokens = splitter.split(source)
        target_tokens = splitter.split(target)

        source_lengths = [len(token) for token in source_tokens]

        sequence_matcher = SequenceMatcher(a=source_tokens, b=target_tokens)

        # 1 token is included as context,
        # this will group cases where delimiters (whitespaces) are equal, but surrounding tokens have differences
        for group in sequence_matcher.get_grouped_opcodes(n=1):
            # remove single whitespace padding
            for i in [0, -1]:
                operation, source_start, source_end, target_start, target_end = group[i]
                if operation == 'equal' and \
                        source_tokens[group[i][1]:group[i][2]] == target_tokens[group[i][3]:group[i][4]] == [' ']:
                    del group[i]

            source_value = ''.join(source_tokens[group[0][1]:group[-1][2]])
            target_value = ''.join(target_tokens[group[0][3]:group[-1][4]])

            target_value = None if target_value == '' else target_value

            span_start = sum(source_lengths[:group[0][1]]) + span_shift
            span_end = sum(source_lengths[:group[-1][2]]) + span_shift

            span = Span(start=span_start, end=span_end, value=source_value)
            replacements = [Replacement(value=target_value)]
            corrections.append(Correction(span=span, replacements=replacements))

        span_shift += len(source) + len(delimiter)

    return corrections
