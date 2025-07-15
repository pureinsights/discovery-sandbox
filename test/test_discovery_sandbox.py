"""Tests for the discovery_sandbox module."""

import json
import random
import string
import uuid

import httpx
import pytest
from httpx import HTTPStatusError, Response
from mockito import mock, unstub, when

from sandbox.discovery_sandbox import (
    Credential,
    Processor,
    QueryFlowClient,
    QueryFlowSequence,
    QueryFlowSequenceProcessor,
    Server,
)


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
        response = Response(200, content=json.dumps(response_data))

        when(response).raise_for_status().thenReturn(response)
        when(httpx).post(
            url=queryflow_client.url + queryflow_client.SANDBOX_PATH,
            params={},
            content=request_data,
            headers={
                "x-api-key": queryflow_client.api_key,
                "Content-Type": "application/json",
            },
            timeout=None,
        ).thenReturn(response)

        result = queryflow_client.text_to_text(processor, request_input)
        assert result == response_data
        unstub()

    def test_text_to_text_processor_no_content(self, queryflow_client):
        """Test the text_to_text method with a new Processor that returns 204."""
        processor_type = "".join(random.choices(string.ascii_letters, k=5))
        processor_config = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        processor = Processor(processor_type, processor_config)

        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        request_data = json.dumps(
            {"processor": processor, "input": request_input},
            default=vars,
        )
        response = Response(204)

        when(httpx).post(
            url=queryflow_client.url + queryflow_client.SANDBOX_PATH,
            params={},
            content=request_data,
            headers={
                "x-api-key": queryflow_client.api_key,
                "Content-Type": "application/json",
            },
            timeout=None,
        ).thenReturn(response)

        result = queryflow_client.text_to_text(processor, request_input)
        assert result == {}
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
        response = Response(200, content=json.dumps(response_data))
        when(response).raise_for_status().thenReturn(response)

        when(httpx).post(
            url=queryflow_client.url + queryflow_client.SANDBOX_PATH + processor_id,
            params={},
            json=request_input,
            headers={"x-api-key": queryflow_client.api_key},
            timeout=None,
        ).thenReturn(response)

        result = queryflow_client.text_to_text(processor_id, request_input)
        assert result == response_data
        unstub()

    def test_text_to_text_uuid_no_content(self, queryflow_client):
        """Tests the text_to_text method with the uuid of a Processor that returns 204."""
        processor_id = str(uuid.uuid4())
        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        response = Response(204)
        when(response).raise_for_status().thenReturn(response)

        when(httpx).post(
            url=queryflow_client.url + queryflow_client.SANDBOX_PATH + processor_id,
            params={},
            json=request_input,
            headers={"x-api-key": queryflow_client.api_key},
            timeout=None,
        ).thenReturn(response)

        result = queryflow_client.text_to_text(processor_id, request_input)
        assert result == {}
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
        event_data = [
            "".join(random.choices(string.ascii_letters, k=5)) for _ in range(5)
        ]

        stream_mock = mock()
        response = mock(Response)

        when(response).iter_text().thenReturn(event_data)
        when(stream_mock).__enter__().thenReturn(response)
        when(stream_mock).__exit__().thenReturn()
        when(httpx).stream(
            "POST",
            url=queryflow_client.url + queryflow_client.SANDBOX_PATH,
            params={},
            content=request_data,
            headers={
                "x-api-key": queryflow_client.api_key,
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            timeout=None,
        ).thenReturn(stream_mock)

        for event in event_data:
            when(queryflow_client)._parse_data(event).thenReturn(event)

        result = queryflow_client.text_to_stream(processor, request_input)
        assert event_data == [chunk for chunk in result]
        unstub()

    def test_text_to_stream_uuid(self, queryflow_client):
        """Test the text_to_stream method with the uuid of an existing Processor."""
        processor_id = str(uuid.uuid4())
        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }
        event_data = [
            "".join(random.choices(string.ascii_letters, k=5)) for _ in range(5)
        ]

        stream_mock = mock()
        response = mock(Response)

        when(response).iter_text().thenReturn(event_data)
        when(stream_mock).__enter__().thenReturn(response)
        when(stream_mock).__exit__().thenReturn()
        when(httpx).stream(
            "POST",
            url=queryflow_client.url + queryflow_client.SANDBOX_PATH + processor_id,
            params={},
            json=request_input,
            headers={
                "x-api-key": queryflow_client.api_key,
                "Accept": "text/event-stream",
            },
            timeout=None,
        ).thenReturn(stream_mock)

        for event in event_data:
            when(queryflow_client)._parse_data(event).thenReturn(event)

        result = queryflow_client.text_to_stream(processor_id, request_input)
        assert event_data == [chunk for chunk in result]
        unstub()

    def test_execute(self, queryflow_client):
        """Tests the execute method."""
        original_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }

        current_input = original_input
        processors = [mock(Processor) for _ in range(5)]
        for processor in processors:
            output = {
                "".join(random.choices(string.ascii_letters, k=5)): "".join(
                    random.choices(string.ascii_letters, k=5)
                )
            }
            when(queryflow_client).text_to_text(
                processor, current_input, None
            ).thenReturn(output)
            current_input = output

        queryflow_sequence = QueryFlowSequence(
            [QueryFlowSequenceProcessor(processor) for processor in processors]
        )

        assert output == queryflow_client.execute(queryflow_sequence, original_input)
        unstub()

    def test_execute_system_exit(self, queryflow_client):
        """Tests the execute method when a processor execution fails."""
        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }

        response_text = "".join(random.choices(string.ascii_letters, k=5))
        processor = mock(Processor)
        response = mock(Response)
        status_error = HTTPStatusError(response=response, message="", request=None)

        response.text = response_text
        status_error.response = response

        when(queryflow_client).text_to_text(processor, request_input, None).thenRaise(
            status_error
        )

        with pytest.raises(SystemExit) as excinfo:
            queryflow_client.execute(
                QueryFlowSequence([QueryFlowSequenceProcessor(processor)]),
                request_input,
            )

        assert response_text == excinfo.value.code
        unstub()

    def test_parse_data(self, queryflow_client):
        """Test the _parse_data method."""
        event_data = [
            "".join(random.choices(string.ascii_letters, k=5)) for _ in range(5)
        ]
        event_text = "\n".join(["data: " + content for content in event_data])
        assert "\n".join(event_data) == queryflow_client._parse_data(event_text)
