from commons.ddd.errors import DomainError
from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from auth.domain.user import PasswordHasher, User
from auth.domain.value_objects import Email, UserPassword

from .interfaces import JwtIssuer, Token, UserUnitOfWork


class UserCommands:

    def __init__(
        self,
        uow: UserUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
        password_hasher: PasswordHasher,
        jwt_issuer: JwtIssuer,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._uuid_provider = uuid_provider
        self._datetime_provider = datetime_provider
        self._jwt_issuer = jwt_issuer

    async def create_viewer(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> User:
        async with self._uow:
            user = User.create_viewer(
                user_id=self._uuid_provider.new_v4(),
                email=Email(email),
                first_name=first_name,
                last_name=last_name,
                password=UserPassword(password),
                hasher=self._password_hasher,
                created_at=self._datetime_provider.now_utc,
            )
            self._uow.users.add(user)
            await self._uow.commit()
            return user

    async def login(self, email: str, password: str) -> Token:
        async with self._uow:
            user = await self._uow.users.find_by_email(Email(email))
            if user is None:
                raise DomainError(f"User with email {email} not found")

            if not self._password_hasher.verify(password, user.password_hash):
                raise DomainError("User password is invalid")

            session = user.create_session(
                session_id=self._uuid_provider.new_v4(),
                now=self._datetime_provider.now_utc,
            )

            token_pair = self._jwt_issuer.issue_token(
                user_id=user.id,
                session_id=session.id,
                role=user.role,
                email=user.email.value,
                first_name=user.first_name,
                last_name=user.last_name,
            )

            await self._uow.users.save(user)
            await self._uow.commit()

            return token_pair
