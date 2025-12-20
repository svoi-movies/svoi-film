from datetime import timedelta
from uuid import UUID

from commons.ddd.errors import DomainError
from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from auth.domain.role import PasswordService, Role, User, VerificationCode
from auth.domain.service import UserService
from auth.domain.value_objects import Email, UserPassword
from auth.services.verification_code_generator import VerificationCodeGenerator

from .interfaces import JwtIssuer, Token, UserUnitOfWork


class UserCommands:
    def __init__(
        self,
        uow: UserUnitOfWork,
        user_service: UserService,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
        password_hasher: PasswordService,
        jwt_issuer: JwtIssuer,
        code_generator: VerificationCodeGenerator,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._uuid_provider = uuid_provider
        self._datetime_provider = datetime_provider
        self._jwt_issuer = jwt_issuer
        self._user_service = user_service
        self._code_generator = code_generator

    async def self_registrate(
        self,
        role: Role,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> User:
        async with self._uow:
            role = await self._uow.roles.get_by_id(role.id)

            user = self._user_service.self_registrate(
                role=role,
                email=Email(email),
                password=UserPassword(password),
                first_name=first_name,
                last_name=last_name,
            )

            self._uow.users.add(user)
            await self._uow.commit()
            return user

    async def login(self, email: str, password: str) -> Token:
        async with self._uow:
            user = await self._uow.users.find_by_email(Email(email))
            if user is None:
                raise DomainError(f"User with email {email} not found")

            role = await self._uow.roles.get_by_id(user.role_id)

            session = self._user_service.login(user, UserPassword(password))

            token_pair = self._jwt_issuer.issue_token(
                user_id=user.id,
                session_id=session.id,
                role=role.name,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
            )

            self._uow.sessions.add(session)
            await self._uow.users.save(user)
            await self._uow.commit()

            return token_pair

    async def verify_email(self, user_id: UUID, entered_code: str) -> None:
        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)
            code = await self._uow.verification_codes.get_by_user_id(user_id)
            self._user_service.verify_email(user, code, entered_code)
            await self._uow.users.save(user)
            await self._uow.commit()

    async def self_register(
        self,
        role_name: str,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> User:
        async with self._uow:
            # Получаем роль по имени
            role = await self._uow.roles.get_by_name(role_name)

            user = self._user_service.self_registrate(
                role=role,
                email=Email(email),
                password=UserPassword(password),
                first_name=first_name,
                last_name=last_name,
            )

            self._uow.users.add(user)
            await self._uow.commit()
            return user

    async def create_role(
        self,
        name: str,
        allow_self_registration: bool,
        creator_role_id: UUID | None,
    ) -> Role:
        async with self._uow:
            role = Role.new(
                role_id=self._uuid_provider.new_v4(),
                name=name,
                allow_self_registration=allow_self_registration,
                creator_role_id=creator_role_id,
            )

            self._uow.roles.add(role)
            await self._uow.commit()
            return role

    async def create_user(
        self,
        creator_user_id: UUID,
        target_role_name: str,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> User:
        async with self._uow:
            # Получаем пользователя-создателя и его роль
            creator_user = await self._uow.users.get_by_id(creator_user_id)
            creator_role = await self._uow.roles.get_by_id(creator_user.role_id)

            # Получаем целевую роль
            target_role = await self._uow.roles.get_by_name(target_role_name)

            # Создаем пользователя через сервис (с проверкой прав)
            user = self._user_service.create_user(
                target_role=target_role,
                creator_user=creator_user,
                creator_role=creator_role,
                email=Email(email),
                password=UserPassword(password),
                first_name=first_name,
                last_name=last_name,
            )

            self._uow.users.add(user)
            await self._uow.commit()
            return user

    async def create_verification_code(self, user_id: UUID) -> VerificationCode:
        """Создает код верификации для пользователя"""
        async with self._uow:
            code = self._code_generator.generate()
            now = self._datetime_provider.now_utc

            verification_code = VerificationCode(
                code_id=self._uuid_provider.new_v4(),
                user_id=user_id,
                code=code,
                valid_until=now + timedelta(hours=24),
                created_at=now,
            )

            self._uow.verification_codes.add(verification_code)
            await self._uow.commit()
            return verification_code
