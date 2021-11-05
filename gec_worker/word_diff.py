from difflib import SequenceMatcher


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
        # return seq
        return [[[], 1]]

    if finalize:
        return flatten_chunk(seq, False)

    if len(seq) == 1:
        return seq[0]
    else:
        res = [[list(currElemSeq) + list(branchSeq), min(currElemWeight, branchWeight)] for currElemSeq, currElemWeight
               in seq[0] for branchSeq, branchWeight in flatten_chunk(seq[1:], False)]
        return res


def merge_different(chunk1, chunk2):
    flat1 = flatten_chunk(chunk1)
    flat2 = flatten_chunk(chunk2)

    preres = list(flat1) + list(flat2)

    res = accumulate(preres)

    return res


def merge_chunks(chunk1, chunk2):
    attempt = merge_linear_and_equal(chunk1, chunk2)

    if attempt:
        return attempt
    else:
        return merge_different(chunk1, chunk2)


def join_sequences(seq1, seq2):
    matcher = SequenceMatcher(None, to_str(seq1), to_str(seq2))

    prev1 = None
    prev2 = None

    result = []

    for begin1, begin2, chunkSize in matcher.get_matching_blocks():
        if chunkSize > 0:
            if prev1 and prev2:
                chunk1 = seq1[prev1:begin1]
                chunk2 = seq2[prev2:begin2]
                result.append(merge_chunks(chunk1, chunk2))

            result += merge_chunks(seq1[begin1:begin1 + chunkSize], seq2[begin2:begin2 + chunkSize])

            prev1 = begin1 + chunkSize
            prev2 = begin2 + chunkSize
    return result
