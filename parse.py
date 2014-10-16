from copy import *
from argparse import *
from collections import defaultdict

# The Grab class is necessary so that we can retrieve an element from a Python
# Set in O(1) time. We could also have used our own implementation of a set
# using a hash table.
class Grab:
    def __init__(self, value):
        self.search_value = value
    def __hash__(self):
        return hash(self.search_value)
    def __eq__(self, other):
        if self.search_value == other:
            self.actual_value = other
            return True
        return False

class Parser(object):
    def __init__(self, grammar_file_name):
        self.parse_table = None
        self.rules = defaultdict(list)
        with open(grammar_file_name, 'r') as f:
            for line in f.readlines():
                line = line.partition('#')[0]
                line = line.rstrip()
                if line == "":
                    continue
                groups = line.split()
                self.rules[groups[1]].append(ProductionRule(groups[1], tuple(groups[2:]), float(groups[0])))
   
    def add_state_to_column(self, state, column, column_set):
        if state not in column_set:
            column.append(state)
            column_set.add(state)
        else:
            grabber = Grab(state)             
            grabber in column_set
            if state.rule.weight < grabber.actual_value.rule.weight:
                grabber.actual_value.rule.weight = state.rule.weight

    def predict(self, predict_symbol, start_position, column, column_set):
        predict_rules = self.rules[predict_symbol]
        for predict_rule in predict_rules:
            new_state = ParseState(start_position, predict_rule)
            self.add_state_to_column(new_state, column, column_set)
    
    def scan(self, word, terminal, cur_state, next_column, next_column_set):
        if word == terminal:
            new_state = deepcopy(cur_state)
            new_state.adv_state() #terminals are free
            self.add_state_to_column(new_state, next_column, next_column_set)

    def attach(self, state, column, column_set):
        #for all incomplete states that end where this completed state starts
        for previous_state in self.parse_table[state.start_pos]:
            previous_symbols = previous_state.rule.symbols
            
            #This may be interesting if nonterinals are in the sentence.
            if previous_symbols and previous_symbols[0] == state.rule.nonterminal:
                new_state = deepcopy(previous_state)
                new_state.adv_state(state.rule.weight)
                self.add_state_to_column(new_state, column, column_set)

    def parse_sentence(self, sentence):
        self.parse_table = defaultdict(list)
        root_state = ParseState(0, self.rules['ROOT'][0])
        self.parse_table[0].append(root_state)

        for i, word in enumerate(sentence.split() + ['']):
            j = 0
            column = self.parse_table[i]
            column_set = set(column)
            next_column = self.parse_table[i+1]
            next_column_set = set(next_column)
            while j < len(column):
                state = column[j]
                symbols = state.rule.symbols
                if symbols:
                    next_symbol = symbols[0]
                    if next_symbol in self.rules:
                        #predict
                        self.predict(next_symbol, i, column, column_set)
                    else:
                        #scan
                        self.scan(word, next_symbol, state, next_column, next_column_set)
                else:
                    #complete
                    self.attach(state, column, column_set)
                                
                print 'column ' + str(i)
                for entry in column:
                    print entry, entry.rule.weight
                print
                j += 1

class ParseState(object):
    def __init__(self, start_pos, rule):
        self.start_pos = start_pos
        self.rule = deepcopy(rule)
    
    def __repr__(self):
        return 'ParseState(%s, %s)' % (self.start_pos, self.rule)

    def __hash__(self):
        return hash((self.start_pos, self.rule))

    def __eq__(self, other):
        if type(other) is not ParseState:
            return other == self
        return self.start_pos == other.start_pos and self.rule == other.rule

    def adv_state(self, weight=None):
        if weight:
            self.rule.weight += weight
        self.rule.symbols = self.rule.symbols[1:]

class ProductionRule(object):
    def __init__(self, nonterminal, symbols, weight):
        self.nonterminal = nonterminal
        self.symbols = symbols
        self.weight = weight
    
    def __iter__(self):
        return iter(self.symbols)

    def __eq__(self, other):
        return self.nonterminal == other.nonterminal and self.symbols == other.symbols
    
    def __hash__(self):
        return hash((self.nonterminal, self.symbols)) 
    
    def __repr__(self):
        return '%s -> .%s' % (self.nonterminal, ' '.join(self.symbols))

def main():
    parser = ArgumentParser()
    parser.add_argument("grammar_file", help="The name or path to the grammar file.")
    parser.add_argument("sentence_file", help="The name or path to the sentence file.")
    args = parser.parse_args()

    p = Parser(args.grammar_file)
    with open(args.sentence_file, 'r') as sen:
        for sentence in sen.readlines():
            if sentence:
                p.parse_sentence(sentence)

if __name__ == "__main__":
    main()
