import pickle
from utils import normalize_str
from enum import Enum

class Vectorizers(object):
    class Categorys(Enum):
        ELETRONICS = 'eletronics'
        OTHERS = 'others'

    eletronic_model: object
    categorys: Categorys

    def __init__(self, **kwargs):
        """
        Load models from training TL_IDF
        """
        # Paths
        #categorizer_model_path = kwargs.get('eletronic_model_path', 'trains/eletronic_train.tlp')
        self.categorys = self.Categorys
        eletronic_model_path = kwargs.get('eletronic_model_path', 'trains/eletronic_train.tlp')
        
        # Pickle load serialized trained model
        self.eletronic_model = pickle.load(open(eletronic_model_path, 'rb'))
        self.funcs = {
            self.categorys.ELETRONICS.value: self.eletronic_model
        }

    def select_category(self, name: str) -> list[float]:
        """
        Get a name and return a category
        """
        return self.categorys.ELETRONICS.value
    
    def select_vectorizer(self, category: str):
        """
        Get a category and returns model function
        """
        return self.funcs[category]

    def extract_tags(self, raw_product_name: str) -> list:
        product_name = normalize_str(raw_product_name)
        category = self.select_category(product_name)
        import logging
        logging.warning(category)
        #for category in categories:
        vectorizer = self.select_vectorizer(category)
        tf_idf = vectorizer.transform(product_name.split())
        feature_names = vectorizer.get_feature_names_out()
        result = [word for word in feature_names if sum(tf_idf[:, vectorizer.vocabulary_[word]].toarray())]
        if result == []:
            result = product_name.split()
        return result