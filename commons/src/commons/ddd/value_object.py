import re
import warnings
from dataclasses import dataclass
from typing import Callable, Sequence, Type

from asyncpg import DivisionByZeroError

from commons.ddd.errors import DomainError

DEFAULT_CATCH_ERRORS = (
    DivisionByZeroError,
    ValueError,
    TypeError,
)


@dataclass(frozen=True, slots=True)
class ViolatedRule:
    message: str


class Validator:
    """
    Validator – это объект для валидации сущностей и объектов-значений.
    Предполагается вот такое использование:

    ```
    with Validator() as v:
        # define rules
        v.must(lambda: a > b, "a must be greater than b")
        v.must(lambda: x == y "x must be equal y")
        v.must(lambda: len(z) > 0, "z must be non empty")

    При выходе из with блока автоматически вызывается v.validate(),
    который генерирует ошибку ValueObjectValidationError, если хотя бы одно правило не прошло.
    Список нарушенных правил можно посмореть через ValueObjectValidationError.errors
    ```
    """

    def __init__(self) -> None:
        self.__validated = False
        self.__validation_errors: list[ViolatedRule] = []

    def must(
        self,
        condition: Callable[[], bool],
        message: str,
        catch_errors: tuple[Type[Exception], ...] = DEFAULT_CATCH_ERRORS,
    ) -> None:
        try:
            ok = condition()
            if not ok:
                self.__validation_errors.append(ViolatedRule(message))
        except catch_errors:
            self.__validation_errors.append(ViolatedRule(message))

    def validate(self) -> None:
        self.__validated = True
        if self.__validation_errors:
            raise ValueObjectValidationError(self.__validation_errors)

    def must_regexp_full_match(
        self,
        pattern: str,
        str_value: str,
        message: str,
        catch_errors: tuple[Type[Exception], ...] = DEFAULT_CATCH_ERRORS,
    ) -> None:
        self.must(
            condition=lambda: re.fullmatch(pattern, str_value) is not None,
            message=message,
            catch_errors=catch_errors,
        )

    def must_regexp_match(
        self,
        pattern: str,
        str_value: str,
        message: str,
        catch_errors: tuple[Type[Exception], ...] = DEFAULT_CATCH_ERRORS,
    ) -> None:
        self.must(
            condition=lambda: len(re.findall(pattern, str_value)) > 0,
            message=message,
            catch_errors=catch_errors,
        )

    def __del__(self) -> None:
        if not self.__validated:
            warnings.warn(
                "Validator object was deleted before .validate() is called. "
                "Checks were not ensured"
            )

    def __enter__(self) -> "Validator":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            raise exc
        self.validate()


class ValueObjectValidationError(DomainError):
    def __init__(self, violated_rules: Sequence[ViolatedRule]) -> None:
        self.errors = violated_rules[:]
        rules_str = "\n\t".join([e.message for e in self.errors])
        self.message = (
            f"Can't construct value object since it has violated {len(violated_rules)} rules:"
            f"\n\t{rules_str}"
        )
        super().__init__(self.message, self.errors)
