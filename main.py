import datetime
import logging
import os
import json
from typing import List

from lunchmoney_automate.task import Task

from lunchmoney_automate.link_transfers import LinkTransfersTask
from lunchmoney_automate.link_spare_change import LinkSpareChangeTask


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    logging.info("Loading configuration...")
    config = json.loads(os.getenv("LUNCHMONEY_CONFIG", "{}"))

    tasks: List[Task] = []
    if "transfers" in config:
        logging.info("Link Transfers task enabled in configuration")
        tasks.append(LinkTransfersTask(**config["transfers"]))

    if "spare_change" in config:
        logging.info("Link Spare Change task enabled in configuration")
        tasks.extend([LinkSpareChangeTask(**item) for item in config["spare_change"]])

    logging.info("Running tasks...")
    for task in tasks:
        task.run()

if __name__ == '__main__':
    main()