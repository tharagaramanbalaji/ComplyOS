from nlp.parser import NLPRuleParser

# Singleton instance of the NLP Parser
# We load it exactly once to prevent 10-second delays on every API request
parser_instance = None

def get_parser() -> NLPRuleParser:
    """
    Returns the loaded NLP parser. If it hasn't been loaded into RAM yet,
    it initializes it.
    """
    global parser_instance
    if parser_instance is None:
        parser_instance = NLPRuleParser()
    return parser_instance
