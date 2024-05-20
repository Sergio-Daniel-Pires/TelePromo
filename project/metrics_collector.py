import logging
from typing import Literal

from prometheus_client import Counter, start_http_server


class MetricsCollector:
    port: int

    def __init__(self, port: int = 8000):
        self.port = port

        self.sites_returns_total = Counter(
            "telepromo_sites_returns_total", "Number of times each site was consumed and status",
            labelnames=[ "site", "result_type" ]
        )

        self.errors_counter = Counter(
            "telepromo_application_errors_total",
            "Number of errors in different application stages",
            labelnames=[ "stage" ]
        )

        self.user_requests_total = Counter(
            "telepromo_user_requests_total", "Number of requests made by users",
            labelnames=[ "type" ]
        )

        self.user_sents_total = Counter(
            "telepromo_user_sents_total", "Number of responses to users"
        )

        self.total_new_users = Counter(
            "telepromo_new_users_total", "Number of new users registered"
        )

        self.start_metrics_server()

    def start_metrics_server(self):
        start_http_server(
            port=self.port
        )

        self.handle_error("started")
        logging.warning("Started prometheus server")

    def handle_site_results (
        self, site: str, result_type: Literal["new_product", "new_price", "error"], amount: int = 1
    ):
        self.sites_returns_total.labels(site=site, result_type=result_type).inc(amount)

    def handle_error (self, stage: str, amount: int = 1):
        self.errors_counter.labels(stage=stage).inc(amount=amount)

    def handle_user_request (self, req_type: Literal["new", "remove", "edit"]):
        self.user_requests_total.labels(type=req_type).inc()

    def handle_user_response (self):
        self.user_sents_total.inc()

    def register_new_user(self):
        self.total_new_users.inc()
