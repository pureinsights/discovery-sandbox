# Copyright (c) 2025 Pureinsights Technology Ltd. All rights reserved.
#
# Permission to use, copy, modify or distribute this software and its
# documentation for any purpose is subject to a licensing agreement with
# Pureinsights Technology Ltd.
#
# All information contained within this file is the property of
# Pureinsights Technology Ltd. The distribution or reproduction of this
# file or any information contained within is strictly forbidden unless
# prior written permission has been granted by Pureinsights Technology Ltd.

"""Entity class definitions for the Inference SDK."""

import json

import httpx
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


class QueryFlowClient:
    """A client class to execute QueryFlow requests.

    Attributes:
        url (str): The base url for the request.
        api_key (str): The api key to use in the request.
        INFERENCE_PATH (str): The api path to use in the request.
    """

    INFERENCE_PATH = "/v2/inference/"

    def __init__(self, url: str, api_key: str):
        """Initialize the client with url and api key.

        Args:
            url (str): The base url for the request.
            api_key (str): The api key to use in the request.
        """
        self.url = url
        self.api_key = api_key

    @multimethod
    def text_to_text(self, processor: Processor, input: dict, timeout: str = None):
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
            url=self.url + self.INFERENCE_PATH,
            params={"timeout": timeout} if timeout is not None else {},
            content=request_data,
            headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
            timeout=None,
        )
        return response.json()

    @multimethod
    def text_to_text(self, processor_id: str, input: dict, timeout: str = None):
        """Execute a processor by ID with the given input.

        Args:
            processor_id (str): The UUID of the processor to execute.
            input (dict): The input to send to the processor.
            timeout (str): The timeout parameter for the request, in ISO 8601 format.

        Returns:
            dict: The response data from the request.
        """
        response = httpx.post(
            url=self.url + self.INFERENCE_PATH + processor_id,
            params={"timeout": timeout} if timeout is not None else {},
            json=input,
            headers={"x-api-key": self.api_key},
            timeout=None,
        )
        return response.json()
