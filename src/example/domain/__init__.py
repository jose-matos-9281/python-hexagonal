from eventsourcing.utils import get_topic, register_topic

from .example import ExampleAggregate


def register_topics():
    register_topic(get_topic(ExampleAggregate.Snapshot), ExampleAggregate.Snapshot)
