from typing import TYPE_CHECKING

from msfwk.mqclient import RabbitMQConfig
from msfwk.utils.logging import get_logger

from moderation.fetch_messages import get_mq_queue, get_safe_message
from moderation.models.exceptions import MQQueueNotFoundError, MQServerConnectionError
from moderation.utils import connect_to_rabbitmq

if TYPE_CHECKING:
    from moderation.moderation.models.interfaces import MQLoadErrorMessage

logger = get_logger(__name__)


async def safe_delete_messages_from_queue(queue_name: str, message_id: str) -> bool:
    """Delete all messages matching id from a RabbitMQ queue.
    Stores only the body as a dictionary

    Args:
        queue_name (str): RabbitMQ queue name
        message_id (str): id ot the message to remove

    Return:
        if the delete has errors or not
    """
    logger.debug("Start deleting messages %s in queue %s", message_id, queue_name)
    errors: list[MQLoadErrorMessage] = []

    client = await connect_to_rabbitmq(RabbitMQConfig)
    if not client or not client.connection or client.connection.is_closed:
        message = "No connection for the rabbit_mq client"
        logger.error(message)
        return False
    try:
        async with client.connection:
            queue = await get_mq_queue(client.connection, queue_name)
            while mq_message_tuple := await get_safe_message(queue, errors):
                mq_message, incomming_message = mq_message_tuple
                if mq_message.id == message_id:
                    logger.debug("Deleted message %s", mq_message.id)
                    await incomming_message.ack()
        return len(errors) == 0
    except MQQueueNotFoundError as qnfe:
        message = f"Queue [{queue_name}] not found"
        logger.exception(message, exc_info=qnfe)
        return False
    except MQServerConnectionError as qnfe:
        message = "Could not connect to server"
        logger.exception(message, exc_info=qnfe)
        return False


async def delete_messages_from_queues(queue_list: list[str], message_id: str) -> bool:
    """Delete all message matching id from given queues

    Args:
        queue_list (list[str]): _description_
        message_id (str): _description_

    Returns:
        bool: if succeded for all
    """
    success = True
    for queue in queue_list:
        success &= await safe_delete_messages_from_queue(queue, message_id)
    return success
