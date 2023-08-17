import re
from nltk.util import ngrams

DAYS_IN_YEAR = 365
MINUTES_IN_DAY = 1440
SECONDS_IN_DAY = 86400

def normalize_str (text: str) -> str:
  text = text.lower()
  text = re.sub(r"[ãâáàä]", "a", text)
  text = re.sub(r"[êéèë]", "e", text)
  text = re.sub(r"[îíìï]", "i", text)
  text = re.sub(r"[õôóòö]", "o", text)
  text = re.sub(r"[ûúùü]", "u", text)
  text = re.sub(r",\s+|\.\s+|\s-\s", " ", text)
  return text

# Model Training
def custom_analyzer (text):
  # substitui bigrams e trigrams por versões sem espaço
  text = normalize_str(text)
  # Create onegrams, bigrams and trigrams
  all_ngrams = []
  #clean_splited = np.setdiff1d(text.split(" "), np.array(STOP_WORDS))
  splitted = text.split(" ")
  for num in range(1, 4):
    c_ngram = ngrams(splitted, num)
    all_ngrams += ["".join(grams) for grams in c_ngram]

  return all_ngrams
