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

"""Tests for the discovery_inference module."""

import json
import random
import string
import uuid

import httpx
import pytest
from httpx import Response
from mockito import unstub, when, mock

from inference.discovery_inference import *


class TestQueryFlowClient:
    """Tests for the QueryFlowClient class."""

    @pytest.fixture
    def queryflow_client(self):
        """Return a QueryFlowClient object."""
        client_url = "".join(random.choices(string.ascii_letters, k=5))
        client_api_key = "".join(random.choices(string.ascii_letters, k=5))
        return QueryFlowClient(client_url, client_api_key)

    def test_text_to_text_processor(self, queryflow_client):
        """Test the text_to_text method with a new Processor entity."""
        credential_type = "".join(random.choices(string.ascii_letters, k=5))
        credential_secret = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        credential = Credential(credential_type, credential_secret)

        server_type = "".join(random.choices(string.ascii_letters, k=5))
        server_config = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        server = Server(server_type, server_config, credential)

        processor_type = "".join(random.choices(string.ascii_letters, k=5))
        processor_config = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        processor = Processor(processor_type, processor_config, server)

        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        request_data = json.dumps(
            {"processor": processor, "input": request_input},
            default=vars,
        )
        response_data = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }

        when(httpx).post(
            url=queryflow_client.url + queryflow_client.INFERENCE_PATH,
            params={},
            content=request_data,
            headers={
                "x-api-key": queryflow_client.api_key,
                "Content-Type": "application/json",
            },
            timeout=None,
        ).thenReturn(Response(200, content=json.dumps(response_data)))

        result = queryflow_client.text_to_text(processor, request_input)
        assert result == response_data
        unstub()

    def test_text_to_text_uuid(self, queryflow_client):
        """Test the text_to_text method with the uuid of an existing Processor."""
        processor_id = str(uuid.uuid4())
        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        response_data = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }

        when(httpx).post(
            url=queryflow_client.url + queryflow_client.INFERENCE_PATH + processor_id,
            params={},
            json=request_input,
            headers={"x-api-key": queryflow_client.api_key},
            timeout=None,
        ).thenReturn(Response(200, content=json.dumps(response_data)))

        result = queryflow_client.text_to_text(processor_id, request_input)
        assert result == response_data
        unstub()

    def test_text_to_stream_processor(self, queryflow_client):
        """Test the text_to_stream method with a new Processor entity."""
        credential_type = "".join(random.choices(string.ascii_letters, k=5))
        credential_secret = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        credential = Credential(credential_type, credential_secret)

        server_type = "".join(random.choices(string.ascii_letters, k=5))
        server_config = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        server = Server(server_type, server_config, credential)

        processor_type = "".join(random.choices(string.ascii_letters, k=5))
        processor_config = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        processor = Processor(processor_type, processor_config, server)

        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        request_data = json.dumps(
            {"processor": processor, "input": request_input},
            default=vars,
        )

        stream_iterator = [
            "".join(random.choices(string.ascii_letters, k=5)) for i in range(5)
        ]

        response = mock(Response)
        stream_mock = mock()

        when(response).iter_text().thenReturn(stream_iterator)
        when(stream_mock).__enter__().thenReturn(response)
        when(stream_mock).__exit__().thenReturn()
        when(httpx).stream(
            "POST",
            url=queryflow_client.url + queryflow_client.INFERENCE_PATH,
            params={},
            content=request_data,
            headers={
                "x-api-key": queryflow_client.api_key,
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            timeout=None,
        ).thenReturn(stream_mock)

        result = queryflow_client.text_to_stream(processor, request_input)
        assert stream_iterator == [chunk for chunk in result]
        unstub()

    def test_text_to_stream_uuid(self, queryflow_client):
        """Test the text_to_stream method with the uuid of an existing Processor."""
        processor_id = str(uuid.uuid4())
        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }

        stream_iterator = [
            "".join(random.choices(string.ascii_letters, k=5)) for i in range(5)
        ]

        response = mock(Response)
        stream_mock = mock()

        when(response).iter_text().thenReturn(stream_iterator)
        when(stream_mock).__enter__().thenReturn(response)
        when(stream_mock).__exit__().thenReturn()
        when(httpx).stream(
            "POST",
            url=queryflow_client.url + queryflow_client.INFERENCE_PATH + processor_id,
            params={},
            json=request_input,
            headers={
                "x-api-key": queryflow_client.api_key,
                "Accept": "text/event-stream",
            },
            timeout=None,
        ).thenReturn(stream_mock)

        result = queryflow_client.text_to_stream(processor_id, request_input)
        assert stream_iterator == [chunk for chunk in result]
        unstub()
