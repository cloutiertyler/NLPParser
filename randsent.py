import sys
import random
from argparse import *
from collections import defaultdict

def index_choice(odds):
    rand = random.random() * sum(odds)
    threshold = 0
    for i, odd in enumerate(odds):
        threshold += odd
        if threshold > rand:
            return i

class SentenceGenerator(object):
    def __init__(self, grammar_file_name):
        self.nonterminal_dict = defaultdict(list)
        with open(grammar_file_name, 'r') as f:
            for line in f.readlines():
                line = line.partition('#')[0]
                line = line.rstrip()
                if line == "":
                    continue
                groups = line.split()
                self.nonterminal_dict[groups[1]].append(ProductionSequence(float(groups[0]), groups[2:]))

    def generate_from_symbol(self, symbol):
        sequence = []
        production_sequences = self.nonterminal_dict[symbol]
        i = index_choice([ps.odds for ps in production_sequences])
        for sub_symbol in production_sequences[i]:
            if sub_symbol not in self.nonterminal_dict:
                sequence.append(sub_symbol)
            else:
                sequence.append(self.generate_from_symbol(sub_symbol))
        return (symbol, sequence)
    
    def generate_tree(self):
        return self.generate_from_symbol("ROOT")
    
    def generate_string(self, tree_format=False):
        return self.tree_string(self.generate_tree()) if tree_format else self.string(self.generate_tree())

    def string(self, tree):
        return ' '.join(self.string(sub_tree) for sub_tree in tree[1]) if type(tree) is tuple else tree

    def tree_string(self, tree, depth = 0):
        spaces = depth+len(tree[0])+2
        s = "(" + tree[0]
        for i, sub_tree in enumerate(tree[1]):
            s += " " + self.tree_string(sub_tree, spaces) if type(sub_tree) is tuple else " " + sub_tree
            s += "\n" + " "*(spaces-1) if i != len(tree[1])-1 else ""
        s += ")"
        return s

class ProductionSequence(object):
    def __init__(self, odds, symbols):
        self.odds = odds
        self.symbols = symbols
    
    def __iter__(self):
        return iter(self.symbols)

def main():
    parser = ArgumentParser()
    parser.add_argument("grammar_file", help="The name or path to the grammar file.")
    parser.add_argument("num_sentences", nargs='?',type=int, default=1, help="The number of sentences you would like the generator to generate. The default is 1.")
    parser.add_argument("-t", action="store_true")
    args = parser.parse_args()

    g = SentenceGenerator(args.grammar_file)
    for i in xrange(args.num_sentences):
        print g.generate_string(args.t)

if __name__ == "__main__":
    main()
