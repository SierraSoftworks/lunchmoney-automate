import datetime
import logging
import os
import json
from typing import List

from .task import Task

from .link_transfers import LinkTransfersTask
from .link_spare_change import LinkSpareChangeTask


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    config = json.loads(os.getenv("LUNCHMONEY_CONFIG", "{}"))

    tasks: List[Task] = []
    if "transfers" in config:
        tasks.append(LinkTransfersTask(**config["transfers"]))

    if "spare_change" in config:
        tasks.extend([LinkSpareChangeTask(**item) for item in config["spare_change"]])

    for task in tasks:
        task.run()

if __name__ == '__main__':
    main()