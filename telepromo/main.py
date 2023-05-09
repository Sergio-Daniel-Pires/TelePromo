from database import Database
from monitor import Monitoring
from vectorizers import Vectorizers
import re
from nltk.util import ngrams

def normalize_str(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[ãâáàä]', 'a', text)
    text = re.sub(r'[êéèë]', 'e', text)
    text = re.sub(r'[îíìï]', 'i', text)
    text = re.sub(r'[õôóòö]', 'o', text)
    text = re.sub(r'[ûúùü]', 'u', text)
    text = re.sub(r',\s+|\.\s+|\s-\s', ' ', text)
    return text

def custom_analyzer(text: str):
    # substitui bigrams e trigrams por versões sem espaço
    text = normalize_str(text)
    # Create onegrams, bigrams and trigrams 
    all_ngrams = []
    #clean_splited = np.setdiff1d(text.split(' '), np.array(STOP_WORDS))
    splitted = text.split(' ')
    for num in range(1, 4):
        c_ngram = ngrams(splitted, num)
        all_ngrams += [''.join(grams) for grams in c_ngram]
    
    return all_ngrams

def main():
    db = Database()
    vectorizers = Vectorizers()
    monitor = Monitoring(
        retry = 3,
        database = db,
        vectorizer = vectorizers
    )
    db.new_wish(['computador'], 'eletronic', 'Sergio')
    db.new_wish(['Fone de ouvido'], 'eletronic', 'Walter')
    db.new_wish(['Monitor gamer'], 'eletronic', 'Andreias')
    db.new_wish(['Smartphone samsung'], 'eletronic', 'WalterS')
    links_cursor = db.get_links()
    for current_obj in links_cursor:
        url_list = current_obj['links']
        results = monitor.prices_from_url(url_list)
        monitor.verify_save_prices(results)

if __name__ == "__main__":
    main()