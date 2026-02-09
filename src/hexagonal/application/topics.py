from typing import Tuple

from eventsourcing.utils import SupportsTopic, register_topic


class RegisterTopics:
    topics: list[Tuple[str, SupportsTopic]]

    def __init__(self, *topics: Tuple[str, SupportsTopic]):
        self.topics = list(topics)

    def __call__(self):
        for topic, obj in self.topics:
            register_topic(topic, obj)

    def __or__(self, other: "RegisterTopics") -> "RegisterTopics":
        return RegisterTopics(*(self.topics + other.topics))

    def __add__(self, other: "RegisterTopics") -> "RegisterTopics":
        return RegisterTopics(*(self.topics + other.topics))
