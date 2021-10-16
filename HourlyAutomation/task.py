from abc import ABC, abstractclassmethod
import logging


class Task(ABC):
    def __init__(self) -> None:
        self.log = logging.getLogger(self.__class__.__name__)

    @abstractclassmethod
    def run(self):
        pass
