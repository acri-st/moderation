import time

from msfwk.exceptions import MQClientConnectionError
from msfwk.mqclient import MQClient, RabbitMQConfig
from msfwk.utils.logging import get_logger

from moderation.models.exceptions import MQServerConnectionError

logger = get_logger(__name__)


async def connect_to_rabbitmq(config: type[RabbitMQConfig] = RabbitMQConfig) -> MQClient | None:
    """Establishes an asynchronous connection to RabbitMQ.

    Raise:
        MQServerConnectionError: Error appended during connection with server

    Returns
        aio_pika.Connection | None: Connection object if successful, None if the connection fails.

    """
    try:
        client = MQClient()
        await client.setup(config)
    except MQClientConnectionError as ce:
        message = f"RabbitMQ connection failed: {ce}"
        logger.exception(message, exc_info=ce)
        raise MQServerConnectionError(message) from ce
    except TimeoutError as te:
        message = f"Connection timeout while connecting to RabbitMQ: {te}"
        logger.exception(message, exc_info=te)
        raise MQServerConnectionError(message) from te
    else:
        logger.info("Successfully connected to RabbitMQ.")
        return client


def time_calculator(func):  # noqa: ANN001, ANN201
    """Decorator to measure the execution time of a function."""

    def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        start_time = time.time()  # Start time
        try:
            return func(*args, **kwargs)
        except Exception as e:
            message = f"Error in function '{func.__name__}': {e}"
            logger.exception(message, exc_info=e)
            return None
        finally:
            end_time = time.time()  # End time
            execution_time = end_time - start_time
            message = f"Execution time of '{func.__name__}': {execution_time:.6f} seconds"
            logger.info(message)

    return wrapper
