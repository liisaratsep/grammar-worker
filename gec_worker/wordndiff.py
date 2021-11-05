#!/usr/bin/env python3
# coding: utf-8

import sys

from difflib import SequenceMatcher

def loadfile(fn):
	res = []
	
	with open(fn, 'r') as fh:
		for l in fh:
			res += l.strip().split() + ["NEWLINE"]
		return res

def prettyPrintXML(seq):
	for e in seq:
		print(len(e))
		#print(e)

		for ee in e:
			print("   ", ee[0], "<", ee[1], ">")

def listsplit(lst, delim):
	res = []
	resl = []
	
	for e in lst:
		if e == delim:
			res.append(resl)
			resl = []
		else:
			resl.append(e)
	
	return res

def applyWeight(seq, weight):
	return [[[[elem], weight]] for elem in seq]

def toStr(seq, weights = False):
	return ["|".join(["::".join(chunk) for chunk, w in altList]) for altList in seq]

def prettyPrint(seq, title = None):
	output = []
	
	#TODO use toStr
	for e in seq:
		output.append("|".join(["::".join(ee[0]) + ("_" + str(ee[1]) if len(e) > 1 else "") for ee in e]))
	
	outputs = listsplit(output, 'NEWLINE')
	
	if title:
		print(title + ": ")
	for o in outputs:
		print(" ".join(o))

def tryMergeLinearAndEqual(ch1, ch2):
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

def getMaxLenAndCheck(chunk):
	resultLen = 1
	resultIdx = None
	
	nonOneCount = 0
	
	for i, e in enumerate(chunk):
		l = len(e)
		
		if l != 1:
			nonOneCount += 1
			resultLen = l
			resultIdx = i
		
		if nonOneCount > 1:
			print("ERR", chunk)
			raise Exception
	
	return resultLen, resultIdx

def accumulate(seq):
	prev = None
	
	res = []
	
	for elem, weight in sorted(seq, key = lambda x: str(x[0])):
		
		if prev is not None and prev == elem:
			res[-1][1] += weight
		else:
			res.append([elem, weight])
		prev = elem
	
	return res

def flattenChunk(seq, finalize = True):
	if len(seq) == 0:
		#return seq
		return [[[], 1]]

	if finalize:
		preRes = flattenChunk(seq, False)
		return preRes
	
	if len(seq) == 1:
		return seq[0]
	else:
		res = [[list(currElemSeq) + list(branchSeq), min(currElemWeight, branchWeight)] for currElemSeq, currElemWeight in seq[0] for branchSeq, branchWeight in flattenChunk(seq[1:], False)]
		return res

def mergeDifferent(chunk1, chunk2):
	#print("DDD 1", chunk1, "---", chunk2)
	
	flat1 = flattenChunk(chunk1)
	flat2 = flattenChunk(chunk2)

	#print("DDD 2", flat1, "===", flat2)
	
	preres = list(flat1) + list(flat2)
	
	#print("DDD 3", preres)
	
	res = accumulate(preres)
	
	#print("DDD 4", res)
	#print("")
	
	return res

def mergeChunks(chunk1, chunk2):
	attempt = tryMergeLinearAndEqual(chunk1, chunk2)
	
	if attempt:
		return attempt
	else:
		return mergeDifferent(chunk1, chunk2)

def joinseqs(seq1, seq2):
	matcher = SequenceMatcher(None, toStr(seq1), toStr(seq2))
	
	prev1 = None
	prev2 = None

	result = []

	for begin1, begin2, chunkSize in matcher.get_matching_blocks():	
		if chunkSize > 0:
			if prev1 and prev2:
				chunk1 = seq1[prev1:begin1]
				chunk2 = seq2[prev2:begin2]
				result.append(mergeChunks(chunk1, chunk2))
			
			result += mergeChunks(seq1[begin1:begin1+chunkSize], seq2[begin2:begin2+chunkSize])

			prev1 = begin1 + chunkSize
			prev2 = begin2 + chunkSize
	return result

def test():
	a = loadfile("a")
	b = loadfile("b")
	c = loadfile("c")

	#ab = joinseqs(applyWeight(a, 1), applyWeight(b, 1), 1, 1)
	#print(ab)

	ax = a
	bx = b
	cx = c

	aa = applyWeight(ax, 1)
	bb = applyWeight(bx, 1)
	cc = applyWeight(cx, 1)

	prettyPrint(aa, "a	")
	prettyPrint(bb, "b	")
	prettyPrint(cc, "c	")

	ab = joinseqs(aa, bb)
	prettyPrint(ab, "a+b  ")

	abc = joinseqs(ab, cc)
	prettyPrint(abc, "a+b+c")

if __name__ == "__main__":
	combo = None
	
	for filename in sys.argv[1:]:
		content = loadfile(filename) # result: content is a list of tokens (str)
		fmtContent = applyWeight(content, 1)
		
		if combo:
			newcombo = joinseqs(combo, fmtContent)
			
			combo = newcombo
		else:
			combo = fmtContent
	
	if combo:
		prettyPrint(combo)
	else:
		sys.stderr.write("Usage: wordndiff file1 file2 [file2 ...]\nDo a diff on word-level for all files and output the resulting finite automaton\n")
		sys.exit(-1)

