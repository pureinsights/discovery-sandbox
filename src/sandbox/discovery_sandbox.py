"""Entity class definitions for the Sandbox SDK."""

import sys
import json

import httpx
from httpx import HTTPStatusError
from multimethod import multimethod


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


class QueryFlowSequenceProcessor:
    """A processor to be executed as part of a QueryFlowSequence.

    Attributes:
        processor (str | Processor): A Processor entity or UUID of an existing processor to execute.
        timeout (str):  The timeout parameter for the processor execution, in ISO 8601 format.
    """

    def __init__(self, processor: str | Processor, timeout: str = None):
        """Initialize the QueryFlowSequenceProcessor with processor and timeout.

        Args:
            processor (str | Processor): A Processor entity or UUID of an existing processor to execute.
            timeout (str):  The timeout parameter for the processor execution, in ISO 8601 format.
        """
        self.processor = processor
        self.timeout = timeout


class QueryFlowSequence:
    """List of QueryFlow processors to be executed sequentially.

    Attributes:
        processors (list[QueryFlowSequenceProcessor]): The list of processors to execute.
    """

    def __init__(self, processors: list[QueryFlowSequenceProcessor]):
        """Initialize the QueryFlowSequence with processors.

        Args:
            processors (list[QueryFlowSequenceProcessor]): The list of processors to execute.
        """
        self.processors = processors


class QueryFlowClient:
    """A client class to execute QueryFlow requests.

    Attributes:
        url (str): The base url for the request.
        api_key (str): The api key to use in the request.
        SANDBOX_PATH (str): The api path to use in the request.
    """

    SANDBOX_PATH = "/v2/sandbox/"

    def __init__(self, url: str, api_key: str):
        """Initialize the client with url and api key.

        Args:
            url (str): The base url for the request.
            api_key (str): The api key to use in the request.
        """
        self.url = url
        self.api_key = api_key

    @multimethod
    def text_to_text(
        self, processor: Processor, input: dict, timeout: str | None = None
    ):
        """Execute a processor with the given input.

        Args:
            processor (Processor): The processor to execute.
            input (dict): The input to send to the processor.
            timeout (str): The timeout parameter for the request, in ISO 8601 format.

        Returns:
            dict: The response data from the request.
        """
        request_data = json.dumps(
            {
                "processor": processor,
                "input": input,
            },
            default=vars,
        )

        response = httpx.post(
            url=self.url + self.SANDBOX_PATH,
            params={"timeout": timeout} if timeout is not None else {},
            content=request_data,
            headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
            timeout=None,
        )

        if response.status_code == 204:
            return {}
        return response.raise_for_status().json()

    @multimethod
    def text_to_text(self, processor_id: str, input: dict, timeout: str | None = None):
        """Execute a processor by ID with the given input.

        Args:
            processor_id (str): The UUID of the processor to execute.
            input (dict): The input to send to the processor.
            timeout (str): The timeout parameter for the request, in ISO 8601 format.

        Returns:
            dict: The response data from the request.
        """
        response = httpx.post(
            url=self.url + self.SANDBOX_PATH + processor_id,
            params={"timeout": timeout} if timeout is not None else {},
            json=input,
            headers={"x-api-key": self.api_key},
            timeout=None,
        )

        if response.status_code == 204:
            return {}
        return response.raise_for_status().json()

    @multimethod
    def text_to_stream(self, processor: Processor, input: dict, timeout: str = None):
        """Execute a processor with the given input.

        Args:
            processor (Processor): The processor to execute.
            input (dict): The input to send to the processor.
            timeout (str): The timeout parameter for the request, in ISO 8601 format.

        Yields:
            str: Each response chunk's data field as decoded text.
        """
        request_data = json.dumps(
            {
                "processor": processor,
                "input": input,
            },
            default=vars,
        )

        with httpx.stream(
            "POST",
            url=self.url + self.SANDBOX_PATH,
            params={"timeout": timeout} if timeout is not None else {},
            content=request_data,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            timeout=None,
        ) as response:
            for chunk in response.iter_text():
                yield self._parse_data(chunk)

    @multimethod
    def text_to_stream(self, processor_id: str, input: dict, timeout: str = None):
        """Execute a processor by ID with the given input.

        Args:
            processor_id (str): The UUID of the processor to execute.
            input (dict): The input to send to the processor.
            timeout (str): The timeout parameter for the request, in ISO 8601 format.

        Yields:
            str: Each response chunk's data field as decoded text.
        """
        with httpx.stream(
            "POST",
            url=self.url + self.SANDBOX_PATH + processor_id,
            params={"timeout": timeout} if timeout is not None else {},
            json=input,
            headers={"x-api-key": self.api_key, "Accept": "text/event-stream"},
            timeout=None,
        ) as response:
            for chunk in response.iter_text():
                yield self._parse_data(chunk)

    def execute(self, sequence: QueryFlowSequence, input_data: dict):
        """Executes a QueryFlow processor sequence.

        Args:
            sequence (QueryFlowSequence): The sequence of QueryFlowSequenceProcessors to execute.
            input_data (dict): The initial input with which to start the execution.

        Returns:
            dict: The final response data from the sequence execution.

        Raises:
            SystemExit: If the execution of any processor fails.
        """
        for queryflow_processor in sequence.processors:
            try:
                input_data = self.text_to_text(
                    queryflow_processor.processor,
                    input_data,
                    queryflow_processor.timeout,
                )
            except HTTPStatusError as e:
                sys.exit(e.response.text)
        return input_data

    def _parse_data(self, event: str):
        """Return the data field from a SSE.

        Args:
            event (str): The original SSE string.

        Returns:
            str: The data field from the event content.
        """
        data = ""
        for line in event.splitlines():
            if line.startswith("data:"):
                content = line.split(":")[1]
                if content.startswith(" "):
                    content = content[1:]
                if data:
                    data += "\n" + content
                else:
                    data = content
        return data
