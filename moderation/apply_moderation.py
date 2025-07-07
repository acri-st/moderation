from msfwk.desp.rabbitmq.mq_message import ModerationEventStatus
from msfwk.mqclient import RabbitMQConfig, send_mq_message
from msfwk.utils.logging import get_logger

from moderation.fetch_messages import get_message
from moderation.models.constants import ACCEPTED_HISTORY_MESSAGE, REJECTED_HISTORY_MESSAGE
from moderation.models.exceptions import MQMessageNotFoundError
from moderation.utils import connect_to_rabbitmq

logger = get_logger(__name__)


async def apply_moderation(message_id: str, status: ModerationEventStatus, history: str = "") -> None:
    """Apply moderation decision for the message at given ID

    Args:
        message_id (str): the id of the message
        status (ModerationEventStatus): moderation decision
        history (str): sentence to append in message history

    Raises:
        MQMessageNotFoundError: Message not found for given id
        MQServerConnectionError: Failed to connect to server
        MQQueueNotFoundError: _description_
    """
    client = await connect_to_rabbitmq()
    async with client.connection:
        mq_message_tuple = await get_message(message_id, RabbitMQConfig.MANUAL_MODERATION_QUEUE, client.connection)
        if mq_message_tuple is None:
            message = f"Failed to found message at id: {message_id}"
            raise MQMessageNotFoundError(message)
        mq_message, incoming_message = mq_message_tuple
        mq_message.status = status
        mq_message.history.append(history)
        await incoming_message.ack()
        logger.info("apply moderation on message: %s", str(mq_message.to_dict()))
        await send_mq_message(
            mq_message, exchange=RabbitMQConfig.MODERATION_EXCHANGE, routing_key=RabbitMQConfig.TO_HANDLING_RKEY
        )


async def accept_message(message_id: str) -> None:
    """Accept the message at given ID

    Args:
        message_id (str): the id of the message

    Raises:
        MQMessageNotFoundError: Message not found for given id
        MQServerConnectionError: Failed to connect to server
        MQQueueNotFoundError: _description_
    """
    await apply_moderation(message_id, ModerationEventStatus.Accepted, ACCEPTED_HISTORY_MESSAGE)


async def reject_message(message_id: str) -> None:
    """Reject the message at given ID

    Args:
        message_id (str): the id of the message

    Raises:
        MQMessageNotFoundError: Message not found for given id
        MQServerConnectionError: Failed to connect to server
        MQQueueNotFoundError: _description_
    """
    await apply_moderation(message_id, ModerationEventStatus.Rejected, REJECTED_HISTORY_MESSAGE)
