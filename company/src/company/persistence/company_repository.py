from uuid import UUID

import sqlalchemy as sa
from commons.ddd.errors import DomainError
from sqlalchemy.ext.asyncio import AsyncSession

from company.domain.company import Company
from company.persistence.schema import companies
from company.use_cases.interfaces import CompanyRepository


class SqlAlchemyCompanyRepository(CompanyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, company: Company) -> None:
        self._session.add(company)

    async def save(self, company: Company) -> None:
        await self._session.merge(company)

    async def get_by_id(self, company_id: UUID) -> Company:
        result = await self._session.execute(
            sa.select(Company).where(companies.c.id == company_id)
        )
        company = result.scalar_one_or_none()
        if company is None:
            raise DomainError(f"Company {company_id} not found")
        return company
