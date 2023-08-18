import logging

class Metrics:
    category: str
    offers: int
    sent: int
    news: int

    def __init__ (self, category: str, *args, **kwargs) -> None:
        self.category = category
        self.offers = kwargs.get("offers", 0)
        self.sent = kwargs.get("sent", 0)
        self.news = kwargs.get("news", 0)

    def __repr__(self) -> str:
        return (
            "New offers:    {}\n"
            "New procuts:   {}\n"
            "Sent products: {}"

        ).format(self.offers, self.sent, self.news)

    def update_values (self, offers: int = 0, sent: int = 0, news: int = 0):
        self.offers += offers
        self.sent += sent
        self.news += news

    def __eq__(self, __value: object) -> bool:
        return self.category == __value.category

class GroupMetrics:
    all_metrics: dict[str, list[Metrics]]

    def __init__ (self, first_metric: Metrics = None) -> None:
        self.all_metrics = {}
        if first_metric:
            self.add_or_update_one(first_metric)

    # ta ruim
    def add_or_update_one (self, new_metric: Metrics | dict):
        if isinstance(new_metric, dict):
            new_metric = Metrics(**new_metric)

        if new_metric.category not in self.all_metrics:
            self.all_metrics[new_metric.category] = []

        category = self.all_metrics[new_metric.category]
        logging.warning(category)
        try:
            idx = category.index(new_metric)
            category[idx].update_values(
                    new_metric.offers, new_metric.sent, new_metric.news
                )

        except Exception:
            category.append(new_metric)


    def show_all (self):
        ...

    def show_last (self):
        ...
