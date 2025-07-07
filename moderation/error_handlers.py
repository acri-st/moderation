"""Moderation error handlers"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from msfwk.models import DespResponse
from msfwk.utils.logging import get_logger

from moderation.models.constants import MESSAGE_NOT_FOUND, MESSAGE_RETRIEVE_FAILED, MQCONNECTION_FAILED, QUEUE_NOT_FOUND
from moderation.models.exceptions import (
    GetMessagesError,
    MQMessageNotFoundError,
    MQQueueNotFoundError,
    MQServerConnectionError,
)

logger = get_logger("error_handlers")

T = TypeVar("T")


def handle_mq_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to handle common MQ-related errors in the moderation service.

    Args:
        func: The function to wrap with error handling

    Returns:
        Wrapped function with standardized error handling
    """

    @wraps(func)
    async def wrapper(*args: object, **kwargs: object) -> DespResponse[T]:
        try:
            return await func(*args, **kwargs)
        except MQServerConnectionError as msce:
            message = "Error appended during connection with server"
            logger.exception(message, exc_info=msce)
            return DespResponse(error=message, code=MQCONNECTION_FAILED, http_status=500)
        except GetMessagesError as gme:
            message = "An error occurred during messages retrieval"
            logger.exception(message, exc_info=gme)
            return DespResponse(error=message, code=MESSAGE_RETRIEVE_FAILED, http_status=500)
        except MQQueueNotFoundError as mqnf:
            message = "Event queue for moderation not found"
            logger.exception(message, exc_info=mqnf)
            return DespResponse(error=message, code=QUEUE_NOT_FOUND, http_status=404)
        except MQMessageNotFoundError as e:
            message = f"Message not found: {e}"
            logger.exception(message, exc_info=e)
            return DespResponse(error=message, http_status=404, code=MESSAGE_NOT_FOUND)

    return wrapper
