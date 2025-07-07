class MQServerConnectionError(ConnectionError):
    """Failed to connect to server"""


class MQQueueNotFoundError(Exception):
    """Failed found the queue"""


class GetMessagesError(Exception):
    """Basic Error for Get messages"""


class MQMessageNotFoundError(Exception):
    """Wanted message not found"""
