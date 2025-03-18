"""Entity class definitions for the Inference SDK."""


class Credential:
    """Credential to authenticate requests to a Server.

    Attributes:
        type (str): The credential type.
        secret (dict): Dictionary containing the secret data.
    """

    def __init__(self, type: str, secret: dict):
        """Initialize the Credential with type and secret.

        Args:
            type (str): The credential type.
            secret (dict): Dictionary containing the secret data.
        """
        self.type = type
        self.secret = secret


class Server:
    """Remote server with its connection details.

    Attributes:
        type (str): The server type.
        config (dict): Dictionary containing the configuration for the server.
        credential (Credential): Credential object for authentication.
    """

    def __init__(self, type: str, config: dict, credential: Credential = None):
        """Initialize the Server with type, config and credential.

        Args:
            type (str): The server type.
            config (dict): Dictionary containing the configuration for the server.
            credential (Credential): Credential object for authentication.
        """
        self.type = type
        self.config = config
        self.credential = credential


class Processor:
    """A processor to be executed.

    Attributes:
        type (str): The processor type.
        config (dict): Dictionary containing the configuration for the processor.
        server (Server): The server to be used during processor execution.
    """

    def __init__(self, type: str, config: dict, server: Server = None):
        """Initialize the Processor with type, config and server.

        Args:
            type (str): The processor type.
            config (dict): Dictionary containing the configuration for the processor.
            server (Server): The server to be used during processor execution.
        """
        self.type = type
        self.config = config
        self.server = server
