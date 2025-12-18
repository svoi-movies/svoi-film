from datetime import timezone
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, HTTPException, Path
from commons.ddd.errors import DomainError

from payments.api import models
from payments.use_cases.commands import PaymentsCommands
from payments.use_cases.commands import PaymentsCommands
from payments.use_cases.queries import PaymentQueries
from commons.utils.common_providers import DateTimeProvider

router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/payments",
    response_model=models.PaymentResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_payment",
)
async def create_payment(
    req: Annotated[models.CreatePaymentRequest, Body()],
    commands: FromDishka[PaymentsCommands],
    dt_provider: FromDishka[DateTimeProvider],
) -> models.PaymentResponse:
    expires_at = req.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= dt_provider.now_utc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="expires_at must be in the future",
        )

    payment = await commands.create_payment(
        amount=req.amount,
        currency=req.currency,
        description=req.description,
        expires_at=expires_at,
    )
    return models.PaymentResponse.model_validate(payment, from_attributes=True)


@router.post(
    "/payments/{payment_id:uuid}/success",
    response_model=models.PaymentResponse,
    status_code=HTTPStatus.OK,
    operation_id="mark_payment_succeeded",
)
async def mark_payment_succeeded(
    payment_id: Annotated[UUID, Path()],
    commands: FromDishka[PaymentsCommands],
) -> models.PaymentResponse:
    try:
        payment = await commands.mark_payment_succeeded(payment_id)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.PaymentResponse.model_validate(payment, from_attributes=True)


@router.post(
    "/payments/{payment_id:uuid}/expire",
    response_model=models.PaymentResponse,
    status_code=HTTPStatus.OK,
    operation_id="mark_payment_expired",
)
async def mark_payment_expired(
    payment_id: Annotated[UUID, Path()],
    commands: FromDishka[PaymentsCommands],
) -> models.PaymentResponse:
    try:
        payment = await commands.mark_payment_expired(payment_id)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.PaymentResponse.model_validate(payment, from_attributes=True)


@router.get(
    "/payments/{payment_id:uuid}",
    response_model=models.PaymentResponse,
    status_code=HTTPStatus.OK,
    operation_id="get_payment",
)
async def get_payment(
    payment_id: Annotated[UUID, Path()],
    queries: FromDishka[PaymentQueries],
) -> models.PaymentResponse:
    payment = await queries.get_payment(payment_id)
    return models.PaymentResponse.model_validate(payment, from_attributes=True)
