from datetime import timezone
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, HTTPException, Path
from commons.ddd.errors import DomainError

from subscriptions.api import models
from subscriptions.use_cases.commands import SubscriptionCommands
from subscriptions.use_cases.queries import SubscriptionQueries
from commons.utils.common_providers import DateTimeProvider

router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/subscriptions",
    response_model=models.SubscriptionResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_subscription",
)
async def create_subscription(
    req: Annotated[models.CreateSubscriptionRequest, Body()],
    commands: FromDishka[SubscriptionCommands],
    dt_provider: FromDishka[DateTimeProvider],
) -> models.SubscriptionResponse:
    expires_at = req.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= dt_provider.now_utc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="expires_at must be in the future",
        )

    subscription = await commands.create_subscription(
        level=req.level,
        expires_at=expires_at,
    )
    return models.SubscriptionResponse.model_validate(
        subscription, from_attributes=True
    )


@router.post(
    "/subscriptions/{subscription_id:uuid}/renew",
    response_model=models.SubscriptionResponse,
    status_code=HTTPStatus.OK,
    operation_id="renew_subscription",
)
async def renew_subscription(
    subscription_id: Annotated[UUID, Path()],
    req: Annotated[models.RenewSubscriptionRequest, Body()],
    commands: FromDishka[SubscriptionCommands],
    dt_provider: FromDishka[DateTimeProvider],
) -> models.SubscriptionResponse:
    new_expires_at = req.new_expires_at
    if new_expires_at.tzinfo is None:
        new_expires_at = new_expires_at.replace(tzinfo=timezone.utc)

    if new_expires_at <= dt_provider.now_utc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="new expires_at must be in the future",
        )

    try:
        subscription = await commands.renew_subscription(
            subscription_id, new_expires_at
        )
    except DomainError as e:
        status = HTTPStatus.NOT_FOUND if "not found" in str(e).lower() else HTTPStatus.CONFLICT
        raise HTTPException(status_code=status, detail=str(e))
    return models.SubscriptionResponse.model_validate(
        subscription, from_attributes=True
    )


@router.post(
    "/subscriptions/{subscription_id:uuid}/cancel",
    response_model=models.SubscriptionResponse,
    status_code=HTTPStatus.OK,
    operation_id="cancel_subscription",
)
async def cancel_subscription(
    subscription_id: Annotated[UUID, Path()],
    commands: FromDishka[SubscriptionCommands],
) -> models.SubscriptionResponse:
    try:
        subscription = await commands.cancel_subscription(subscription_id)
    except DomainError as e:
        status = HTTPStatus.NOT_FOUND if "not found" in str(e).lower() else HTTPStatus.CONFLICT
        raise HTTPException(status_code=status, detail=str(e))
    return models.SubscriptionResponse.model_validate(
        subscription, from_attributes=True
    )


@router.post(
    "/subscriptions/{subscription_id:uuid}/level-change/request",
    response_model=models.SubscriptionResponse,
    status_code=HTTPStatus.OK,
    operation_id="request_subscription_level_change",
)
async def request_subscription_level_change(
    subscription_id: Annotated[UUID, Path()],
    req: Annotated[models.RequestLevelChange, Body()],
    commands: FromDishka[SubscriptionCommands],
) -> models.SubscriptionResponse:
    try:
        subscription = await commands.initiate_level_change(
            subscription_id, req.target_level
        )
    except DomainError as e:
        status = HTTPStatus.NOT_FOUND if "not found" in str(e).lower() else HTTPStatus.CONFLICT
        raise HTTPException(status_code=status, detail=str(e))
    return models.SubscriptionResponse.model_validate(
        subscription, from_attributes=True
    )


@router.post(
    "/subscriptions/{subscription_id:uuid}/level-change/apply",
    response_model=models.SubscriptionResponse,
    status_code=HTTPStatus.OK,
    operation_id="apply_subscription_level_change",
)
async def apply_subscription_level_change(
    subscription_id: Annotated[UUID, Path()],
    commands: FromDishka[SubscriptionCommands],
) -> models.SubscriptionResponse:
    try:
        subscription = await commands.apply_level_change(subscription_id)
    except DomainError as e:
        status = HTTPStatus.NOT_FOUND if "not found" in str(e).lower() else HTTPStatus.CONFLICT
        raise HTTPException(status_code=status, detail=str(e))
    return models.SubscriptionResponse.model_validate(
        subscription, from_attributes=True
    )


@router.get(
    "/subscriptions/{subscription_id:uuid}",
    response_model=models.SubscriptionResponse,
    status_code=HTTPStatus.OK,
    operation_id="get_subscription",
)
async def get_subscription(
    subscription_id: Annotated[UUID, Path()],
    queries: FromDishka[SubscriptionQueries],
) -> models.SubscriptionResponse:
    subscription = await queries.get_subscription(subscription_id)
    return models.SubscriptionResponse.model_validate(
        subscription, from_attributes=True
    )
