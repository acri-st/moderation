from datetime import datetime

from msfwk.desp.rabbitmq.mq_message import (
    DespFonctionnalArea,
    DespMQMessage,
    ModerationEventStatus,
    MQContentByTypeModel,
)
from pydantic import BaseModel


class Event(BaseModel):
    """Holds an event response"""

    id: str
    routing_key: str
    exchange: str
    status: ModerationEventStatus
    user_id: str
    date: datetime
    url: str | None
    fonctionnal_area: DespFonctionnalArea
    content_id: int | str | None
    content: MQContentByTypeModel
    history: list[str]

    @classmethod
    def from_message(cls, message: DespMQMessage) -> "Event":
        """Build an Event

        Args:
            message (DespMQMessage): __desc__
        """
        return Event(
            id=message.id,
            routing_key=message.routing_key,
            exchange=message.exchange,
            user_id=message.user_id,
            status=message.status,
            date=message.date,
            url=message.url,
            fonctionnal_area=message.fonctionnal_area,
            content_id=message.content_id,
            content=message.content,
            history=message.history,
        )


class MQLoadErrorMessage(BaseModel):
    """Model for message that failed to load during parsing or decode()"""

    content: str | bytes | None
    error: str


class GetEventResponse(BaseModel):
    """Hold the content of GetEvent"""

    event: Event


class GetEventsResponse(BaseModel):
    """Hold the content of GetEvents"""

    event_count: int
    events: list[Event]
    errors: list[MQLoadErrorMessage]

    @classmethod
    def from_message_list_and_error(
        cls, message_list: list[DespMQMessage], errors: list[MQLoadErrorMessage]
    ) -> "GetEventsResponse":
        """Generate this model

        Args:
            message_list (list[DespMQMessage]): list of message
            errors (list[MQLoadErrorMessage]): list of errors
        """
        return GetEventsResponse(
            event_count=len(message_list),
            events=[Event.from_message(message) for message in message_list],
            errors=errors,
        )


class ToHandlingResponse(BaseModel):
    """Response for accept and reject"""

    status: str = "accepted"
    message_id: str


class DeleteMessagesResponse(BaseModel):
    """Response for DELETE messages"""

    message: str = "success"
