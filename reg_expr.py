import re

def detect_sentence_end(text):
    # Define the regular expression pattern for sentence end detection
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

def test_regex(text, func=detect_sentence_end):
    results = []
    cursor = 0
    for end in func(text):
        sentence = text[cursor:end]
        results.append(sentence)
        cursor = end
    results.append(text[cursor:])
    return results
