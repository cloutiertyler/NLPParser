import sys
import math
from copy import *
from argparse import *
from collections import defaultdict

class Parser(object):
    """
    A Parser is an object that will parse sentences in accordance with a
    provided grammar. The grammar must be provided to the parser upon
    initialization.
    """
    def __init__(self, grammar_file_name):
        """Builds data structures and preprocesses the grammar."""
        self.parse_table = None
        self.parse_table_size = 0
        self.left_parent_table = defaultdict(set) 
        self.rules = defaultdict(list)
        with open(grammar_file_name, 'r') as f:
            for line in f.readlines():
                line = line.partition('#')[0]
                line = line.rstrip()
                if line == "":
                    continue
                groups = line.split()
                prod_rule = ProductionRule(groups[1], tuple(groups[2:]), -math.log(float(groups[0]), 2))
                self.left_parent_table[prod_rule.symbols[0]].add(prod_rule.nonterminal)
                self.rules[prod_rule.nonterminal].append(prod_rule)
   
    def add_state_to_column(self, state, column, column_set):
        """Adds a state to the column if that state does not already exist.
        If the new state has a lower weight, the old state is updated with the
        new state."""
        if state not in column_set:
            column.append(state)
            column_set[state] = state
        else:
            old_state = column_set[state]
            if state.rule.weight < old_state.rule.weight:
                old_state.rule.weight = state.rule.weight
                old_state.previous_state = state.previous_state
                old_state.new_constituent = state.new_constituent

    def predict(self, predict_symbol, start_position, column, column_set, left_ancestors):
        """Predicts a new rule for a column based on the left_ancestors."""
        predict_rules = self.rules[predict_symbol]
        for predict_rule in predict_rules:
            if predict_rule.symbols[0] in left_ancestors:
                new_state = ParseState(start_position, predict_rule)
                self.add_state_to_column(new_state, column, column_set)
    
    def scan(self, word, terminal, cur_state, next_column, next_column_set):
        """Scans the current word and adds a new state if the word matches the terminal."""
        if word == terminal:
            new_state = ParseState(cur_state.start_pos, cur_state.rule)
            new_state.adv_state() #terminals are free
            new_state.previous_state = cur_state
            new_state.new_constituent = terminal
            self.add_state_to_column(new_state, next_column, next_column_set)

    def attach(self, state, column, column_set):
        """Completes a state and attaches all previous states who needed
        the completed state in order to continue."""
        #for all incomplete states that end where this completed state starts
        for previous_state in self.parse_table[state.start_pos]:
            previous_symbols = previous_state.rule.symbols
            
            #This may be interesting if nonterinals are in the sentence.
            if previous_symbols and previous_symbols[0] == state.rule.nonterminal:
                new_state = ParseState(previous_state.start_pos, previous_state.rule)
                new_state.adv_state(state.rule.weight)
                new_state.previous_state = previous_state
                new_state.new_constituent = state
                self.add_state_to_column(new_state, column, column_set)

    def parse_sentence(self, sentence):
        """Parses a sentence and stores the results in self.parse_table."""
        self.parse_table = defaultdict(list)
        for root_rule in self.rules['ROOT']:
            self.parse_table[0].append(ParseState(0, root_rule)) 

        for i, word in enumerate(sentence.split() + ['']):
            j = 0
            column = self.parse_table[i]
            column_set = {}
            next_column = self.parse_table[i+1]
            next_column_set = {}
            symbols_predicted = set()
            left_ancestors = set()
            left_ancestors.add(word)
            self.add_ancestors(left_ancestors, word)
            while j < len(column):
                state = column[j]
                symbols = state.rule.symbols
                if symbols:
                    next_symbol = symbols[0]
                    if next_symbol in self.rules and next_symbol not in symbols_predicted:
                        #predict
                        symbols_predicted.add(next_symbol)
                        self.predict(next_symbol, i, column, column_set, left_ancestors)
                    else:
                        #scan
                        self.scan(word, next_symbol, state, next_column, next_column_set)
                else:
                    #complete
                    self.attach(state, column, column_set)
                #self.print_column_states(i)
                j += 1
        self.parse_table_size = i

    def add_ancestors(self, left_ancestors, child):
        """Creates a set of all left_ancestors of a child symbol."""
        for left_parent in self.left_parent_table[child]:
            if left_parent not in left_ancestors:
                left_ancestors.add(left_parent)
                self.add_ancestors(left_ancestors, left_parent)

    def print_column_states(self, column_num):
        """Prints all of the states or entries in a specific column."""
        column = self.parse_table[column_num]
        print 'column ' + str(column_num)
        for entry in column:
            print entry, entry.rule.weight
        print

    def print_best_parse(self):
        """Prints the back trace of the best parse in the last column
        of the parse_table."""
        lowest_weight = 0
        best_parse = None
        for state in self.parse_table[self.parse_table_size]:
            if state.rule.nonterminal == "ROOT" and not state.rule.symbols:
                if not best_parse or state.rule.weight < lowest_weight:
                    best_parse = state
                    lowest_weight = state.rule.weight
        sys.stdout.write(str(lowest_weight) + ' ')
        self.print_entry(best_parse)
        sys.stdout.write('\n')

    def print_entry(self, state):
        """Recursively prints a given state."""
        if type(state) is not ParseState:
            sys.stdout.write(state)
        elif not state.rule.symbols:
            sys.stdout.write('(')
            sys.stdout.write(state.rule.nonterminal)
            sys.stdout.write(' ')
            self.print_entry(state.previous_state) 
            self.print_entry(state.new_constituent)
            sys.stdout.write(')')
        elif state.previous_state:
            self.print_entry(state.previous_state) 
            self.print_entry(state.new_constituent)

class ParseState(object):
    """
    An object that holds all the information necessary for 
    an entry in the parse table.
    """
    def __init__(self, start_pos, rule):
        self.start_pos = start_pos
        self.rule = deepcopy(rule)
        self.previous_state = None
        self.new_constituent = None
    
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
    """
    A production rule as specified by the grammar file.
    These may be modified by parse states.
    """
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
                p.print_best_parse()

if __name__ == "__main__":
    main()
