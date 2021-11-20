import datetime
import logging
import os
import json
import tracing
from typing import List
from opentelemetry import trace

from lunchmoney_automate.task import Task

from lunchmoney_automate.link_transfers import LinkTransfersTask
from lunchmoney_automate.match_transfers import MatchTransfersTask
from lunchmoney_automate.link_spare_change import LinkSpareChangeTask

def main() -> None:
    tracer = trace.get_tracer("lunchmoney-automate")
    with tracer.start_as_current_span("main"):
        with tracer.start_as_current_span("configuration.load"):
            logging.info("Loading configuration...")
            config = json.loads(os.getenv("LUNCHMONEY_CONFIG", "{}"))

        with tracer.start_as_current_span("tasks.load"):
            tasks: List[Task] = []
            if "transfers" in config:
                logging.info("Link Transfers task enabled in configuration")
                tasks.append(LinkTransfersTask(**config["transfers"]))

            if "match_transfers" in config:
                logging.info("Match Transfers task enabled in configuration")
                tasks.append(MatchTransfersTask(**config["match_transfers"]))

            if "spare_change" in config:
                logging.info("Link Spare Change task enabled in configuration")
                tasks.extend([LinkSpareChangeTask(**item) for item in config["spare_change"]])

    with tracer.start_as_current_span("tasks.run"):
        logging.info("Running tasks...")
        for task in tasks:
            task.run()

if __name__ == '__main__':
    main()