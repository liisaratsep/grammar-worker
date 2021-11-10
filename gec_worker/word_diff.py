from difflib import SequenceMatcher

from gec_worker.dataclasses import Response, Replacement, Correction, Span


def apply_weight(seq, weight):
    return [[[[elem], weight]] for elem in seq]


def to_str(seq):
    return ["|".join(["::".join(chunk) for chunk, w in alt_list]) for alt_list in seq]


def merge_linear_and_equal(ch1, ch2):
    if len(ch1) != len(ch2):
        return False

    result = []

    for e1, e2 in zip(ch1, ch2):
        if len(e1) != 1 or len(e2) != 1:
            return False

        seq1, w1 = e1[0]
        seq2, w2 = e2[0]

        if len(seq1) != 1 or len(seq2) != 1 or seq1[0] != seq2[0]:
            return False

        result.append([[[seq1[0]], w1 + w2]])

    return result


def accumulate(seq):
    prev = None

    res = []

    for elem, weight in sorted(seq, key=lambda x: str(x[0])):

        if prev is not None and prev == elem:
            res[-1][1] += weight
        else:
            res.append([elem, weight])
        prev = elem

    return res


def flatten_chunk(seq, finalize=True):
    if len(seq) == 0:
        return [[[], 1]]

    if finalize:
        return flatten_chunk(seq, False)

    if len(seq) == 1:
        return seq[0]
    else:
        res = [
            [list(curr_elem_seq) + list(branch_seq), min(curr_elem_weight, branch_weight)]
            for curr_elem_seq, curr_elem_weight in seq[0]
            for branch_seq, branch_weight in flatten_chunk(seq[1:], False)
        ]
        return res


def merge_different(chunk1, chunk2):
    flat1 = flatten_chunk(chunk1)
    flat2 = flatten_chunk(chunk2)

    pre_res = list(flat1) + list(flat2)

    res = accumulate(pre_res)

    return res


def merge_chunks(chunk1, chunk2):
    attempt = merge_linear_and_equal(chunk1, chunk2)

    if attempt:
        return attempt
    else:
        return merge_different(chunk1, chunk2)


def join_sequences(seq1, seq2):
    matcher = SequenceMatcher(None, to_str(seq1), to_str(seq2))

    prev1 = 0
    prev2 = 0

    result = []

    for begin1, begin2, chunk_size in matcher.get_matching_blocks():
        if begin1 - prev1 or begin2 - prev2:
            chunk1 = seq1[prev1:begin1]
            chunk2 = seq2[prev2:begin2]
            result.append(merge_chunks(chunk1, chunk2))

        if chunk_size > 0:
            result += merge_chunks(seq1[begin1:begin1 + chunk_size], seq2[begin2:begin2 + chunk_size])
            prev1 = begin1 + chunk_size
            prev2 = begin2 + chunk_size
    return result


def generate_spans(original: str, corrected: str) -> Response:
    response = Response(original_text=original, corrected_text=corrected)
    original_w = apply_weight(original.split(), 1)
    corrected_w = apply_weight(corrected.split(), 2)

    combined = join_sequences(original_w, corrected_w)

    character_idx = 0
    token_idx = 0
    for element in combined:
        if len(element) == 1:
            character_idx += len(' '.join(element[0][0])) + 1
        else:
            ordered = sorted(element, key=lambda x: x[1])
            original_text = ' '.join(ordered[0][0])
            correction_text = ' '.join(ordered[1][0])

            span_start = character_idx
            span_end = character_idx

            if original_text == '':  # addition
                if token_idx != 0:  # include previous word if exists
                    span_start -= len(original_w[token_idx - 1][0][0][0])
                    if correction_text:
                        correction_text = original[span_start:span_end] + ' ' + correction_text

                elif token_idx < len(original_w):  # include upcoming word if exists
                    span_end += len(original_w[token_idx][0][0][0])  # addition
                    if correction_text:
                        correction_text = correction_text + ' ' + original[span_start:span_end]

            else:
                # substitution
                span_end += len(original_text)
                character_idx += len(original_text) + 1

                if correction_text == '':  # deletion
                    correction_text = None
                    if token_idx < len(original_w):  # delete upcoming whitespace if exists
                        span_end += 1
                    elif token_idx != 0:  # delete previous whitespace if exists
                        span_start -= 1

                token_idx += 1

            replacements = [Replacement(correction_text)]

            correction = Correction(Span(span_start, span_end, original[span_start:span_end]), replacements)
            response.corrections.append(correction)
    return response
