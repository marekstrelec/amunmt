
import re
import collections


def get_stats(vocab):
    pairs = collections.defaultdict(int)
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols) - 1):
            pairs[symbols[i], symbols[i + 1]] += freq
    return pairs


def merge_vocab(pair, v_in):
    v_out = {}
    bigram = re.escape(' '.join(pair))
    p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
    for word in v_in:
        w_out = p.sub(''.join(pair), word)
        v_out[w_out] = v_in[word]
    return v_out

# vocab = {'l o w </w>': 5, 'l o w e r </w>': 2, 'n e w e s t </w>': 6, 'w i d e s t </w>': 3}
# vocab = {'u n l i k e </w>': 1, 'l i k e </w>': 3, 'd i s l i k e </w>': 2}
vocab = {'t a b l e </w>': 1, 's t a b l e </w>': 1, 'u n s t a b l e </w>': 1}
# vocab = {'l o w </w>': 1, 'l o w e r </w>': 1, 's l o w e r </w>': 1}


num_merges = 100
for i in range(num_merges):
    pairs = get_stats(vocab)
    # print(list(pairs.items()))
    if not len(pairs):
        break

    for w in vocab.keys():
        print("({0})  ".format(w), end='')
    best = max(pairs, key=pairs.get)

    print("\t\t({0} -> {1})".format(best[0], best[1]))
    print('')

    vocab = merge_vocab(best, vocab)
