from typing import Union, Iterable
import re
import queue

class SentenceParser:
    sentinel = None

    def __init__(self):
        self.tokens = []
        self.stack = []
        self.n_tokens = 0
        #self.q = queue.Queue()

    def _detect_sentence_end(self, text):
        # Define the regular expression pattern for sentence end detection
        # TODO: sentence can begin with a quote
        sentence_end_pattern = re.compile(r"""
            (?<!\b[A-Z])              # Negative lookbehind (e.g., "E.", "Q.") 
            (?<!\b[A-Z][a-z]\.)       # Negative lookbehind  (e.g., "Mr.", "Dr.")
            (?<!\b[A-Z][a-z][a-z]\.)  # Negative lookbehind (e.g., "Mrs.", "Drs.")
            (?<!\b[A-Z]{2})           # Negative lookbehind for two-letter abbreviations (e.g., "U.S.")
            (?<!\b[A-Z]{3})           # Negative lookbehind for three-letter abbreviations (e.g., "M.I.A.")
            (?<!\.\.\.)               # Negative lookbehind for ellipses
            (?<=[.?!])                # Lookbehind for sentence-ending punctuation
            \s+                       # Whitespace
            (?=[A-Z])                 # Lookahead for a capital letter (start of a new sentence)
        """, re.VERBOSE)

        # Find all sentence-ending positions
        matches = [match.end() for match in sentence_end_pattern.finditer(text)]
        return matches

    def get_sentences(self, token_seq: Iterable[bytes]) -> Iterable[str]:
        for token in token_seq:
            sentence = self.feed(token.decode("utf-8"))
            if sentence is not None:
                yield sentence
        last_sentence = self.end()
        self.n_tokens = len(self.tokens)
        self.reset()
        yield last_sentence

    def reset(self):
        self.tokens = []
        self.stack = []

    def end(self):
        last_sentence = ''.join(self.stack)
        self.tokens.extend(self.stack)
        #self.q.put(last_sentence)
        #self.q.put(SentenceParser.sentinel)
        return last_sentence

    def feed(self, token: str) -> Union[str, None]:
        self.stack.append(token)
        text = ''.join(self.stack)
        if self._detect_sentence_end(text):
            *sentence_tokens, next_start_token = self.stack
            text = ''.join(sentence_tokens)
            #self.q.put(text)
            self.tokens.extend(sentence_tokens)
            self.stack = [next_start_token]
            return text
        return None


