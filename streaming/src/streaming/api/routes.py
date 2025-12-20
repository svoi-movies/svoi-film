from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, HTTPException, Path
from commons.ddd.errors import DomainError

from streaming.api import models
from streaming.use_cases import ViewerCommands, TitleCommands, SessionCommands

router = APIRouter(route_class=DishkaRoute)


# Viewer endpoints
@router.post(
    "/viewers",
    response_model=models.ViewerResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_viewer",
)
async def create_viewer(
    commands: FromDishka[ViewerCommands],
) -> models.ViewerResponse:
    viewer = await commands.create_viewer()
    return models.ViewerResponse.model_validate(viewer, from_attributes=True)


@router.delete(
    "/viewers/{viewer_id:uuid}",
    response_model=models.ViewerResponse,
    status_code=HTTPStatus.OK,
    operation_id="delete_viewer",
)
async def delete_viewer(
    viewer_id: Annotated[UUID, Path()],
    commands: FromDishka[ViewerCommands],
) -> models.ViewerResponse:
    try:
        viewer = await commands.delete_viewer(viewer_id)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.ViewerResponse.model_validate(viewer, from_attributes=True)


# Title endpoints
@router.post(
    "/titles",
    response_model=models.TitleResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_title",
)
async def create_title(
    req: Annotated[models.CreateTitleRequest, Body()],
    commands: FromDishka[TitleCommands],
) -> models.TitleResponse:
    title = await commands.create_title(
        name=req.name,
        description=req.description,
        director=req.director,
    )
    return models.TitleResponse.model_validate(title, from_attributes=True)


# Episode endpoints
@router.post(
    "/episodes",
    response_model=models.CreateEpisodeResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_episode",
)
async def create_episode(
    req: Annotated[models.CreateEpisodeRequest, Body()],
    commands: FromDishka[TitleCommands],
) -> models.CreateEpisodeResponse:
    episode, upload_url = await commands.add_episode_draft(
        title_id=req.title_id,
        name=req.name,
        description=req.description,
        duration=req.duration,
    )
    return models.CreateEpisodeResponse(
        episode=models.EpisodeResponse.model_validate(episode, from_attributes=True),
        upload_url=upload_url,
    )


@router.post(
    "/episodes/{episode_id:uuid}/upload",
    response_model=models.EpisodeResponse,
    status_code=HTTPStatus.OK,
    operation_id="upload_episode_source",
)
async def upload_episode_source(
    episode_id: Annotated[UUID, Path()],
    commands: FromDishka[TitleCommands],
) -> models.EpisodeResponse:
    try:
        episode = await commands.upload_episode_source(episode_id)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.EpisodeResponse.model_validate(episode, from_attributes=True)


@router.post(
    "/episodes/{episode_id:uuid}/process",
    response_model=models.EpisodeResponse,
    status_code=HTTPStatus.OK,
    operation_id="process_episode_source",
)
async def process_episode_source(
    episode_id: Annotated[UUID, Path()],
    commands: FromDishka[TitleCommands],
) -> models.EpisodeResponse:
    try:
        episode = await commands.process_episode_source(episode_id)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.EpisodeResponse.model_validate(episode, from_attributes=True)


@router.post(
    "/episodes/{episode_id:uuid}/publish",
    response_model=models.EpisodeResponse,
    status_code=HTTPStatus.OK,
    operation_id="publish_episode",
)
async def publish_episode(
    episode_id: Annotated[UUID, Path()],
    commands: FromDishka[TitleCommands],
) -> models.EpisodeResponse:
    try:
        episode = await commands.publish_episode(episode_id)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.EpisodeResponse.model_validate(episode, from_attributes=True)


@router.post(
    "/episodes/{episode_id:uuid}/hide",
    response_model=models.EpisodeResponse,
    status_code=HTTPStatus.OK,
    operation_id="hide_episode",
)
async def hide_episode(
    episode_id: Annotated[UUID, Path()],
    commands: FromDishka[TitleCommands],
) -> models.EpisodeResponse:
    try:
        episode = await commands.hide_episode(episode_id)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.EpisodeResponse.model_validate(episode, from_attributes=True)


# Viewing Session endpoints
@router.post(
    "/sessions",
    response_model=models.ViewingSessionResponse,
    status_code=HTTPStatus.CREATED,
    operation_id="create_session",
)
async def create_session(
    req: Annotated[models.CreateSessionRequest, Body()],
    commands: FromDishka[SessionCommands],
) -> models.ViewingSessionResponse:
    session = await commands.create_session(
        viewer_id=req.viewer_id,
        episode_id=req.episode_id,
    )
    return models.ViewingSessionResponse.model_validate(session, from_attributes=True)


@router.patch(
    "/sessions/{session_id:uuid}/progress",
    response_model=models.ViewingSessionResponse,
    status_code=HTTPStatus.OK,
    operation_id="update_progress",
)
async def update_progress(
    session_id: Annotated[UUID, Path()],
    req: Annotated[models.UpdateProgressRequest, Body()],
    commands: FromDishka[SessionCommands],
) -> models.ViewingSessionResponse:
    try:
        session = await commands.update_progress(
            session_id=session_id,
            progress_seconds=req.progress_seconds,
        )
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.ViewingSessionResponse.model_validate(session, from_attributes=True)


@router.post(
    "/sessions/{session_id:uuid}/complete",
    response_model=models.ViewingSessionResponse,
    status_code=HTTPStatus.OK,
    operation_id="complete_session",
)
async def complete_session(
    session_id: Annotated[UUID, Path()],
    commands: FromDishka[SessionCommands],
) -> models.ViewingSessionResponse:
    try:
        session = await commands.complete_session(session_id)
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e))
    return models.ViewingSessionResponse.model_validate(session, from_attributes=True)


@router.post(
    "/streaming/url",
    response_model=models.StreamingUrlResponse,
    status_code=HTTPStatus.OK,
    operation_id="get_streaming_url",
)
async def get_streaming_url(
    req: Annotated[models.GetStreamingUrlRequest, Body()],
    commands: FromDishka[SessionCommands],
) -> models.StreamingUrlResponse:
    try:
        url = await commands.get_streaming_url(
            viewer_id=req.viewer_id,
            episode_id=req.episode_id,
        )
    except DomainError as e:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=str(e))
    return models.StreamingUrlResponse(streaming_url=url)
