from prometheus_client import Counter, start_http_server
from typing import Literal
import logging

class MetricsCollector:
    port: int

    def __init__(self, port=8000):
        self.port = port

        self.sites_returns_total = Counter(
            "telepromo_sites_returns_total", "Number of times each site was consumed and status",
            labelnames=["site", "status"]
        )

        self.product_counter = Counter(
            "telepromo_product_counter", "New products or prices",
            labelnames=["product_status"]
        )

        self.errors_counter = Counter(
            "telepromo_application_errors_total", "Number of errors in different application stages",
            labelnames=["stage"]
        )

        self.user_requests_total = Counter(
            "telepromo_user_requests_total", "Number of requests made by users",
            labelnames=["type"]
        )

        self.user_sents_total = Counter(
            "telepromo_user_sents_total", "Number of responses to users"
        )

        self.total_new_users = Counter(
            "telepromo_total_new_users", "Number of new users registered"
        )

        self.start_metrics_server()

    def start_metrics_server(self):
        start_http_server(addr="telepromo", port=self.port)
        self.handle_error("started")
        logging.info("Started prometheus server")

    def consume_site (
        self, site: str, status: Literal["Sucess", "Error"], amount: int = 1
    ):
        self.sites_returns_total.labels(site=site, status=status).inc(amount)

    def handle_product (
        self, product_status: Literal["new_product", "new_price"], amount: int = 1
    ):
        self.product_counter.labels(product_status=product_status).inc(amount)

    def handle_error (self, stage: str, amount: int = 1):
        self.errors_counter.labels(stage=stage).inc(amount=amount)

    def handle_user_request (self, req_type: Literal["new", "remove", "edit"]):
        self.user_requests_total.labels(type=req_type).inc()

    def handle_user_response (self):
        self.user_sents_total.inc()

    def register_new_user(self):
        self.total_new_users.inc()
