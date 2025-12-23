from hexagonal.domain import HasTopic


def test_simple_topic():
    class A(HasTopic): ...

    assert A.TOPIC == "A"


def test_nested_topic():
    class A(HasTopic): ...

    class B(A): ...

    assert B.TOPIC == "A.B"


def test_override_topic():
    class A(HasTopic):
        TOPIC = "Custom"

    # override at root
    assert A.TOPIC == "Custom"

    class B(A): ...

    class C(B):
        TOPIC = "Custom2"

    class D(C, topic_suffix="De"): ...

    # inherits and appends when inherited TOPIC equals base_topic
    assert B.TOPIC == "Custom.B"
    assert C.TOPIC == "Custom2"
    assert D.TOPIC == "Custom2.De"


def test_topic_suffix_override():
    class A(HasTopic): ...

    class C(A, topic_suffix="Suffix"): ...

    # uses provided suffix instead of class name
    assert C.TOPIC == "A.Suffix"


def test_multilevel_hierarchy():
    class Root(HasTopic): ...

    class Mid(Root): ...

    class Leaf(Mid): ...

    assert Root.TOPIC == "Root"
    assert Mid.TOPIC == "Root.Mid"
    assert Leaf.TOPIC == "Root.Mid.Leaf"


# def test_generic_topic():
#     T = TypeVar("T")

#     class A(HasTopic): ...

#     class B(A): ...

#     class C(HasTopic, Generic[T]): ...

#     class D(C[B]): ...

#     assert A.TOPIC == "A"
#     assert B.TOPIC == "A.B"
#     assert C.TOPIC == "C"
#     assert D.TOPIC == "C[A.B].D"
#     assert C[B].TOPIC == "C[A.B]"
