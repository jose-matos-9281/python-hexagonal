from .application import register_topics as register_topics_example
from .domain import register_topics as register_topics_domain


def register_topics():
    register_topics_example()
    register_topics_domain()


register_topics()
