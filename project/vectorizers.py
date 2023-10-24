from enum import Enum

import spacy

from project.utils import STOP_WORDS, normalize_str


class Vectorizers (object):
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

    async def remove_stop_words (self, normalized_product_name: str) -> tuple[list[str], list[str]]:
        doc = self.trained_model(normalized_product_name)

        tags = []
        adjectives = []

        for token in doc:
            if token.text in STOP_WORDS:
                continue

            elif token.pos_ == "ADJ":
                adjectives.append(token.text)

            else:
                tags.append(token.text)

        tags.sort()
        adjectives.sort()

        return tags, adjectives

    async def extract_tags (self, raw_product_name: str, category: str) -> tuple[list[str], list[str]]:
        # Cutted function because vectorizer is not good (not enough data)

        normalized_product_name = normalize_str(raw_product_name)
        product_tags, adjectives = await self.remove_stop_words(normalized_product_name)

        return product_tags, adjectives