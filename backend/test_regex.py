import re
from parser.template_matcher import TemplateMatcher
from parser.normalizer import Normalizer
from parser.synonym_mapper import SynonymMapper

n = Normalizer()
s = SynonymMapper()
t = TemplateMatcher()

text1 = "Tax amount should be greater than 0"
norm1 = n.normalize(text1)
syn1 = s.map_synonyms(norm1)
print(f"1: {syn1}")
print(t.match(syn1))

text2 = "Any invoice with tax amount greater than zero requires tax category"
norm2 = n.normalize(text2)
syn2 = s.map_synonyms(norm2)
print(f"2: {syn2}")
print(t.match(syn2))
