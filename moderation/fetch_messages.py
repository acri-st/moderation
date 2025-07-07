import json

from aio_pika import Connection, IncomingMessage, RobustConnection, RobustQueue
from aio_pika import exceptions as aio_pika_exceptions
from msfwk.desp.rabbitmq.mq_message import DespMQMessage
from msfwk.mqclient import RabbitMQConfig
from msfwk.utils.logging import get_logger

from moderation.models.exceptions import MQQueueNotFoundError, MQServerConnectionError
from moderation.models.interfaces import MQLoadErrorMessage
from moderation.utils import connect_to_rabbitmq, time_calculator

logger = get_logger(__name__)


async def get_messages_from_queue(queue_name: str) -> tuple[list[DespMQMessage], list[MQLoadErrorMessage]]:
    """Retrieves all messages from a RabbitMQ queue without acknowledging them.
    Will remove the duplicate message (with same id)

    Args:
        queue_name (str): RabbitMQ queue name

    Raises:
        MQServerConnectionError: Error appended during connection with server
        MQQueueNotFoundError: queue_name not found in MQ server
    """
    messages: list[DespMQMessage] = []
    errors: list[MQLoadErrorMessage] = []

    id_message_dict: dict[str, tuple[DespMQMessage, IncomingMessage]] = {}

    client = await connect_to_rabbitmq(RabbitMQConfig)
    if not client or not client.connection or client.connection.is_closed:
        message = "No connection for the rabbit_mq client"
        logger.error(message)
        raise MQServerConnectionError(message)
    async with client.connection:
        queue = await get_mq_queue(client.connection, queue_name)
        while mq_message_tuple := await get_safe_message(queue, errors):
            mq_message, incomming_message = mq_message_tuple
            if id_message_dict.get(mq_message.id) is not None:
                _, inc = id_message_dict[mq_message.id]
                await inc.ack()
            id_message_dict[mq_message.id] = mq_message, incomming_message

    messages = [msg[0] for msg in id_message_dict.values()]
    return messages, errors


@time_calculator
async def get_safe_message(
    queue: RobustQueue, errors: list[MQLoadErrorMessage] | None = None
) -> tuple[DespMQMessage, IncomingMessage] | None:
    """_summary_

    Args:
        queue (RobustQueue): _description_
        errors (list[MQLoadErrorMessage] | None, optional): _description_. Defaults to None.

    Raises:
        MQServerConnectionError: Failed to connect to server

    Returns:
        tuple[DespMQMessage, IncomingMessage] | None: _description_
    """
    try:
        #  Set fail=False to prevent the raise of QueueEmpty exception
        message = await queue.get(no_ack=False, fail=False)
        if not message:
            return None
        # convert in dict and generate the message
        decoded_message = message.body.decode()
        return DespMQMessage.from_dict(json.loads(decoded_message)), message

    except ConnectionError as ce:  # noqa: PERF203
        err_message = f"Connection lost while fetching messages: {ce}"
        logger.exception(err_message, exc_info=ce)
        raise MQServerConnectionError(err_message) from ce

    except aio_pika_exceptions.QueueEmpty as qe:
        err_message = "Queue is empty."
        logger.info(err_message, exc_info=qe)
        return None

    except json.JSONDecodeError as je:
        err_message = f"Invalid message (JSON incorrect): {decoded_message}"
        logger.exception(err_message, exc_info=je)
        if errors is not None:
            errors.append(MQLoadErrorMessage(content=decoded_message, error=err_message))


async def get_message(
    message_id: str, queue_name: str, connection: RobustConnection
) -> tuple[DespMQMessage, IncomingMessage] | None:
    """Retrieve the message with given ID, or None if not found

    Args:
        message_id (str): _description_
        connection (RobustConnection): client connection
        queue_name (str): _description_

    Raises:
        MQServerConnectionError: Failed to connect to server
        MQQueueNotFoundError: _description_


    Returns:
        tuple[DespMQMessage, IncomingMessage] | None: _description_
    """
    queue = await get_mq_queue(connection, queue_name)
    while mq_message_tuple := await get_safe_message(queue):
        mq_message, incomming_message = mq_message_tuple
        if mq_message.id != message_id:
            continue
        return mq_message, incomming_message
    return None


async def retrieve_message(message_id: str, queue_name: str) -> tuple[DespMQMessage, IncomingMessage] | None:
    """Create a client and retrieve the message with ID

    Args:
        queue_name (str): _description_
        message_id (_type_, optional): _description_

    Raises:
        MQServerConnectionError: _description_
    """
    client = await connect_to_rabbitmq(RabbitMQConfig)
    if not client or not client.connection or client.connection.is_closed:
        message = "No connection for the rabbit_mq client"
        logger.error(message)
        raise MQServerConnectionError(message)
    async with client.connection:
        return await get_message(message_id, queue_name, client.connection)


async def get_mq_queue(connection: Connection, queue_name: str) -> RobustQueue:
    """Return the given queue in the given connection

    Args:
        connection (Connection): _description_
        queue_name (str): _description_

    Raises:
        MQQueueNotFoundError: _description_
    """
    try:
        channel = await connection.channel()
        return await channel.get_queue(queue_name, ensure=False)

    except aio_pika_exceptions.ChannelNotFound as cnf:
        err_message = f"Queue '{queue_name}' not found: {cnf}"
        logger.exception(err_message, exc_info=cnf)
        raise MQQueueNotFoundError(err_message) from cnf
