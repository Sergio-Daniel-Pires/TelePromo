from enum import Enum

import spacy

from project.utils import STOP_WORDS, normalize_str


class Vectorizers ():
    trained_model: spacy.language.Language

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
        # Pickle load serialized trained model
        # self.eletronic_model = pickle.load(open(eletronic_model_path, "rb"))
        _ = kwargs.get("eletronic_model_path", "trains/eletronic_train.tlp")

        self.trained_model = spacy.load("pt_core_news_sm")
        self.eletronic_model = None
        self.funcs = {
            self.categorys.ELETRONICS.value: self.eletronic_model
        }

    async def remove_stop_words (self, normalized_product_name: str) -> list[str]:
        """
        Remove stop words from product name

        :param normalized_product_name: _description_
        :return: _description_
        """
        tags = []
        doc = normalized_product_name.split(" ")

        for token in doc:
            if token in STOP_WORDS:
                continue

            else:
                tags.append(token)

        tags.sort()

        return tags

    async def extract_tags (self, raw_product_name: str, category: str) -> list[str]:
        """Split product name into tokens

        :param raw_product_name: Product name as strings
        :param category: Product category, like eletronics
        :return: product tags as str list
        """
        # Cutted function because vectorizer is not good (not enough data)

        normalized_product_name = normalize_str(raw_product_name)
        product_tags = await self.remove_stop_words(normalized_product_name)

        return product_tags