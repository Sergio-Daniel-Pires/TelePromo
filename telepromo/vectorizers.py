import pickle
import re

def normalize_str(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[ãâáàä]', 'a', text)
    text = re.sub(r'[êéèë]', 'e', text)
    text = re.sub(r'[îíìï]', 'i', text)
    text = re.sub(r'[õôóòö]', 'o', text)
    text = re.sub(r'[ûúùü]', 'u', text)
    text = re.sub(r',\s+|\.\s+|\s-\s', ' ', text)
    return text

class Vectorizers(object):
    eletronic_model: object

    def __init__(self, **kwargs):
        """
        Load models from training TL_IDF
        """
        # Paths
        #categorizer_model_path = kwargs.get('eletronic_model_path', 'trains/eletronic_train.tlp')
        eletronic_model_path = kwargs.get('eletronic_model_path', 'trains/eletronic_train.tlp')
        
        # Pickle load serialized trained model
        self.eletronic_model = pickle.load(open(eletronic_model_path, 'rb'))
        self.funcs = {
            'eletronics': self.eletronic_model
        }

    def select_category(self, name: str) -> list[float]:
        """
        Get a name and return a category
        """
        return 'eletronics'
    
    def select_vectorizer(self, category: str):
        """
        Get a category and returns model function
        """
        return self.funcs[category]

    def extract_tags(self, raw_product_name: str) -> list:
        product_name = normalize_str(raw_product_name)
        category = self.select_category(product_name)
        #for category in categories:
        vectorizer = self.select_vectorizer(category)
        tf_idf = vectorizer.transform(product_name.split())
        feature_names = vectorizer.get_feature_names_out()
        return [word for word in feature_names if sum(tf_idf[:, vectorizer.vocabulary_[word]].toarray())]