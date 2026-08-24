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
    SandboxAPIError
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
        response.is_error = False

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

    def test_execute_sandbox_api_error(self, queryflow_client):
        """Tests the execute method propagates SandboxAPIError when a processor fails."""
        request_input = {
            "".join(random.choices(string.ascii_letters, k=5)): "".join(
                random.choices(string.ascii_letters, k=5)
            )
        }

        processor = mock(Processor)
        api_error = SandboxAPIError("Error details")

        when(queryflow_client).text_to_text(processor, request_input, None).thenRaise(
            api_error
        )

        queryflow_sequence = QueryFlowSequence([QueryFlowSequenceProcessor(processor)])
        
        with pytest.raises(SandboxAPIError) as excinfo:
            queryflow_client.execute(queryflow_sequence, request_input)

        assert "Error details" in str(excinfo.value)
        unstub()

    def test_parse_data(self, queryflow_client):
        """Test the _parse_data method."""
        event_data = [
            "".join(random.choices(string.ascii_letters, k=5)) for _ in range(5)
        ]
        event_text = "\n".join(["data: " + content for content in event_data])
        assert "\n".join(event_data) == queryflow_client._parse_data(event_text)


    def test_text_to_text_processor_error(self, queryflow_client):
        """Test text_to_text raises SandboxAPIError with API details on failure."""
        processor = Processor(
            type="".join(random.choices(string.ascii_letters, k=5)),
            config={},
        )
        request_input = {"key": "value"}
        error_body = '{"messages": ["Evaluation error"]}'
        
        response = mock(Response)
        response.status_code = 422
        response.text = error_body
        
        status_error = HTTPStatusError(
            message="Client error '422'",
            request=mock(),
            response=response,
        )
        
        when(response).raise_for_status().thenRaise(status_error)
        when(httpx).post(...).thenReturn(response)

        with pytest.raises(SandboxAPIError) as excinfo:
            queryflow_client.text_to_text(processor, request_input)

        assert error_body in str(excinfo.value)
        unstub()

    def test_text_to_stream_processor_error(self, queryflow_client):
        """Test text_to_stream raises SandboxAPIError when stream returns an error."""
        processor = Processor(
            type="".join(random.choices(string.ascii_letters, k=5)),
            config={},
        )
        request_input = {"key": "value"}
        error_body = '{"error": "Stream failed"}'

        stream_mock = mock()
        response = mock(Response)
        response.is_error = True
        response.status_code = 400
        response.reason_phrase = "Bad Request"
        response.url = "http://mock-url"
        response.text = error_body

        when(response).read().thenReturn(b"")
        when(stream_mock).__enter__().thenReturn(response)
        when(stream_mock).__exit__().thenReturn()
        when(httpx).stream(...).thenReturn(stream_mock)

        stream_generator = queryflow_client.text_to_stream(processor, request_input)
        
        with pytest.raises(SandboxAPIError) as excinfo:
            list(stream_generator)

        assert error_body in str(excinfo.value)
        unstub()
