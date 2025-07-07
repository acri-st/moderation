from msfwk.application import app, openapi_extra
from msfwk.context import register_init
from msfwk.exceptions import MQClientConnectionError
from msfwk.models import BaseDespResponse, DespResponse
from msfwk.mqclient import RabbitMQConfig, load_default_rabbitmq_config
from msfwk.utils.logging import get_logger

from moderation.apply_moderation import accept_message, reject_message
from moderation.delete_messages import delete_messages_from_queues
from moderation.error_handlers import handle_mq_errors
from moderation.fetch_messages import get_messages_from_queue, retrieve_message
from moderation.models.constants import MESSAGE_NOT_FOUND
from moderation.models.interfaces import (
    DeleteMessagesResponse,
    Event,
    GetEventsResponse,
    ToHandlingResponse,
)

logger = get_logger("application")


async def init(app_config: dict) -> bool:  # noqa: ARG001
    """_init rabbitmq_config"""
    try:
        load_default_rabbitmq_config()
        # add_reliability_check("rabbitmq", app_config.get("rabbitmq", {}).get("mq_host"))
    except MQClientConnectionError as mqce:
        message = "Failed to connect to mq"
        logger.exception(message, exc_info=mqce)
        return False
    return True


@app.get(
    "/moderation_content",
    summary="Returns the events in moderation",
    response_model=BaseDespResponse[GetEventsResponse],
    tags=["moderation"],
    openapi_extra=openapi_extra(secured=True, roles=["moderator", "admin"]),
)
@handle_mq_errors
async def get_moderation_content() -> DespResponse[GetEventsResponse]:
    """Return the list of moderations events

    Returns
        DespResponse[GetEventsResponse]: _description_
    """
    messages, errors = await get_messages_from_queue(RabbitMQConfig.MANUAL_MODERATION_QUEUE)
    return DespResponse(data=GetEventsResponse.from_message_list_and_error(messages, errors))


@app.get(
    "/moderation_content/{event_id}",
    summary="Returns the wanted event in moderation",
    response_model=BaseDespResponse[Event],
    tags=["moderation"],
    openapi_extra=openapi_extra(secured=True, roles=["moderator", "admin"]),
)
@handle_mq_errors
async def get_moderation_content_from_id(event_id: str) -> DespResponse[Event]:
    """Return the list of moderations events

    Returns
        DespResponse[GetEventsResponse]: _description_
    """
    messages = await retrieve_message(event_id, RabbitMQConfig.MANUAL_MODERATION_QUEUE)
    if messages is None:
        message = "Event not found"
        logger.error(message)
        return DespResponse(error=message, code=MESSAGE_NOT_FOUND, http_status=404)
    mq_message, _ = messages
    return DespResponse(data=Event.from_message(mq_message))


@app.post(
    "/accept/{message_id}",
    summary="Accept an event",
    response_model=BaseDespResponse[ToHandlingResponse],
    tags=["moderation"],
    openapi_extra=openapi_extra(secured=True, roles=["moderator", "admin"]),
)
@handle_mq_errors
async def handle_accept_message(message_id: str) -> DespResponse[ToHandlingResponse]:
    """API route to accept a message by its ID."""
    await accept_message(message_id)
    return DespResponse(
        data=ToHandlingResponse(message_id=message_id, status="accepted"),
    )


@app.post(
    "/reject/{message_id}",
    summary="Reject an event",
    response_model=BaseDespResponse[ToHandlingResponse],
    tags=["moderation"],
    openapi_extra=openapi_extra(secured=True, roles=["moderator", "admin"]),
)
@handle_mq_errors
async def handle_reject_message(message_id: str) -> DespResponse[ToHandlingResponse]:
    """API route to accept a message by its ID."""
    await reject_message(message_id)
    return DespResponse(
        data=ToHandlingResponse(message_id=message_id, status="rejected"),
    )


@app.delete(
    "/messages/{message_id}",
    summary="delete all events with given id from queues ",
    response_model=BaseDespResponse[DeleteMessagesResponse],
    tags=["moderation"],
    openapi_extra=openapi_extra(secured=True, roles=["moderator", "admin"], internal=True),
)
@handle_mq_errors
async def delete_messages(message_id: str) -> DespResponse[DeleteMessagesResponse]:
    """Delete all messages with id = message_id from all the queues
    Args:
        message_id (str): _description_
    Returns:
        BaseDespResponse[ToHandlingResponse]: _description_
    """
    queues = [
        RabbitMQConfig.MANUAL_MODERATION_QUEUE,
    ]
    success = await delete_messages_from_queues(queues, message_id)
    if success:
        return DespResponse(
            data=DeleteMessagesResponse(message=f"Successfully removed all messages with id {message_id}")
        )
    return DespResponse(data=DeleteMessagesResponse(message=f"Partially removed all messages with id {message_id}"))


register_init(init)
