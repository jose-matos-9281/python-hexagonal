import pytest
from pydantic import ValidationError

from hexagonal.domain import ValueObject


class TestValueObject:
    def test_value_str(self):
        class PruebaValueObject(ValueObject[str]): ...

        value = PruebaValueObject(value="test")

        assert value.value == "test"
        assert isinstance(value.value, str)

    def test_hash(self):
        class PruebaValueObject(ValueObject[str]): ...

        value = PruebaValueObject(value="test")
        value2 = PruebaValueObject(value="test")

        assert hash(value) == hash(value2)

        value3 = PruebaValueObject(value="test2")

        assert hash(value) != hash(value3)

    def test_inmutability(self):
        class PruebaValueObject(ValueObject[str]): ...

        value = PruebaValueObject(value="test")

        with pytest.raises(ValidationError):
            value.value = "test2"

    def test_free_side_effects(self):
        class PruebaValueObject(ValueObject[str]):
            def side_efect(self):
                self.value = "test2"

            def no_side_efect(self, new_value: str):
                return PruebaValueObject(value=new_value)

        value = PruebaValueObject(value="test")

        with pytest.raises(ValidationError):
            value.side_efect()

        assert value.value == "test"

        value2 = value.no_side_efect("test2")
        assert value2.value == "test2"
        assert value.value == "test"
