from commons.ddd.errors import DomainError
from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from auth.domain.role import PasswordService, Role, Session, User, VerificationCode
from auth.domain.value_objects import Email, UserPassword


class UserService:

    def __init__(
        self,
        dt_provier: DateTimeProvider,
        uuid_provider: UUIDProvider,
        password_service: PasswordService,
    ) -> None:
        self._dt_provider = dt_provier
        self._uuid_provider = uuid_provider
        self._password_service = password_service

    def try_activate_user(self, user: User, user_role: Role) -> bool:
        assert user.role_id == user_role.id

        if not all(req.check(user) for req in user_role.activation_requirements):
            return False

        user.activate()

        return True

    def self_registrate(
        self,
        role: Role,
        email: Email,
        password: UserPassword,
        first_name: str,
        last_name: str,
    ) -> User:
        if not role.allow_self_registration:
            raise DomainError(f"Role {role.name} does not allow self-registration")

        password_hash = self._password_service.hash_password(password)

        user = User.new(
            user_id=self._uuid_provider.new_v4(),
            email=email,
            role_id=role.id,
            first_name=first_name,
            last_name=last_name,
            created_by=None,
            now=self._dt_provider.now_utc,
            password_hash=password_hash,
        )

        return user

    def verify_email(
        self, user: User, user_code: VerificationCode, entered_code: str
    ) -> None:
        now = self._dt_provider.now_utc

        user_code.verify(entered_code, now)
        user.verify_email(now)

    def login(self, user: User, entered_password: UserPassword) -> Session:
        if not self._password_service.verify(entered_password, user.password_hash):
            raise DomainError("Password is incorrect")

        session = Session.new(
            session_id=self._uuid_provider.new_v4(),
            user_id=user.id,
            now=self._dt_provider.now_utc,
        )

        return session

    def logout(self, session: Session) -> None:
        session.close(self._dt_provider.now_utc)

    def change_password(
        self,
        user: User,
        old_password: UserPassword,
        new_password: UserPassword,
        sessions: list[Session],
    ) -> None:
        now = self._dt_provider.now_utc
        user.change_password(self._password_service, old_password, new_password, now)

        for session in sessions:
            session.close(now)
