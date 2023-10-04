from enum import Enum

from project.utils import normalize_str, remove_stop_words


class Vectorizers (object):
    class Categorys (Enum):
        ELETRONICS = "eletronics"
        OTHERS = "others"

    eletronic_model: object
    categorys: Categorys

    def __init__ (self, **kwargs):
        """
        Load models from training TL_IDF
        """
        # Paths
        self.categorys = self.Categorys
        _ = kwargs.get("eletronic_model_path", "trains/eletronic_train.tlp")

        # Pickle load serialized trained model
        # self.eletronic_model = pickle.load(open(eletronic_model_path, "rb"))
        self.eletronic_model = None
        self.funcs = {
            self.categorys.ELETRONICS.value: self.eletronic_model
        }

    def select_category (self, name: str) -> list[float]:
        """
        Get a name and return a category
        """
        return "diversified"

    def select_vectorizer (self, category: str):
        """
        Get a category and returns model function
        """
        return self.funcs[category]

    @classmethod
    def extract_tags (cls, raw_product_name: str, category: str) -> tuple[list[str], list[str]]:
        # Cutted function because vectorizer is not good (not enough data)

        normalized_product_name = normalize_str(raw_product_name)
        product_tags, adjectives = remove_stop_words(normalized_product_name)

        return product_tags, adjectives