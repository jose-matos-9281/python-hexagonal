from typing import Tuple, Type

from eventsourcing.utils import SupportsTopic, register_topic

from hexagonal.domain import HasTopic

TRegistableTopics = Tuple[str, SupportsTopic] | Type[HasTopic] | Type["RegisterTopics"]


class RegisterTopics:
    topics: list[TRegistableTopics | "RegisterTopics"] = []

    def __init__(self, *topics: TRegistableTopics | "RegisterTopics"):
        self.topics += list(topics)

    def __call__(self):
        self.apply()

    @classmethod
    def _reduce(
        cls, topic: TRegistableTopics | "RegisterTopics"
    ) -> Tuple[str, SupportsTopic]:
        if isinstance(topic, tuple) and len(topic) == 2:
            return topic
        else:
            raise ValueError(f"Invalid topic: {topic}")

    @classmethod
    def apply(cls):
        for topic, obj in [cls._reduce(topic) for topic in cls.topics]:
            register_topic(topic, obj)

    def __or__(self, other: "RegisterTopics") -> "RegisterTopics":
        return RegisterTopics(*(self.topics + other.topics))

    def __add__(self, other: "RegisterTopics") -> "RegisterTopics":
        return RegisterTopics(*(self.topics + other.topics))

    @classmethod
    def register(cls, *topics: TRegistableTopics | "RegisterTopics"):
        cls.topics += list(topics)
