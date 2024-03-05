import logging
import time


class Timer:
    started: int
    timers: dict[str, list[int, int]]

    def __init__(self) -> None:
        self.started = int(time.time())
        self.timers = {}

    def next (self, task: str):
        if task not in self.timers:
            self.timers[task] = []

        self.timers[task].append(int(time.time()))

        if len(self.timers[task]) == 2:
            started, finished = self.timers[task]
            logging.debug(f"{task}\t{finished - started}s")

    def finish (self):
        total = int(time.time()) - self.started
        logging.debug(f"Total: {total}s")

        for task in self.timers.keys():
            if len(self.timers[task]) == 2:
                started, finished = self.timers[task]
                logging.debug(f"{task}\t{finished - started}s")

            else:
                logging.debug(f"{task} {len(self.timers[task])} times")
