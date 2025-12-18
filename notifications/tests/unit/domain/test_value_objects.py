from string import ascii_lowercase, ascii_uppercase, digits

import pytest
from commons.ddd import ValueObjectValidationError
from hypothesis import given
from hypothesis import strategies as st

from notifications.domain.value_objects import Email, UserPassword

"""
Когда пишете юнит тесты на питоне у вас есть два концептуальных подхода:
- Табличные тесты
- Property-based тесты

Табличные тесты это те, которые вы привыкли писать, 
сами выбираем тестовые данные, которые подаем на вход,
Дальше запускаем код, который хотим протестить на этих данных,
Проверяем через assert, что с ожиданием. Здесь это тесты на email
"""


def test__Email__can_create_valid_email() -> None:
    # Arrange
    test_email = "example@email.com"

    # Act
    email = Email(test_email)

    # Assert
    assert email.value == test_email


def test__Email__invalid_email_raises_exception() -> None:
    # Arrange
    test_email = "invalid_email"

    # Act
    with pytest.raises(ValueObjectValidationError) as r:
        _ = Email(test_email)

    r.match(r"Must be a valid email")


"""
Второй подход это property-based testing. Он в питоне реализуется через библиотеку hypothesis.
Тут идея, что hypothesis сам генерирует нам тестовые данные по определенному шаблону (стратегии)
А мы создаем нужные нам объекты и проверяем, что они удовлетворяют некоторым свойствам.

Например, если бы мы хотели убедиться, что от перемены мест слагаемых сумма не менается, то могли бы написать следующий тест:
- попроисть у hypothesis два числа через st.integers()
- написать тест из одной строки assert a + b == b + a

@given(st.integers(), st.integers())
def test_sum_is_commutative(a: int, b: int) -> int:
    assert a + b == b + a

Такие тесты помогают нам искать крайние случаи, поэтому их уместно использовать там, где есть сложные валидации.
"""

valid_password_strategy = (
    st.text(min_size=8, max_size=32)
    .filter(lambda t: set(ascii_uppercase) & set(t))
    .filter(lambda t: set(ascii_lowercase) & set(t))
    .filter(lambda t: set(digits) & set(t))
    .filter(lambda t: set(r"!@#$%^&*(){}-_+=\|/") & set(t))
)


@given(valid_password_strategy)
def test__UserPassword__can_create_valid_password(valid_password: str) -> None:
    # Act
    _ = UserPassword(valid_password)
