# Pureinsights Discovery Platform: Inference SDK 
_Discovery Inference SDK_ is a Python package that allows developers to programatically access Discovery features. Currently, it supports executing one or multiple QueryFlow processors. 

## Requirements
- Python 3.13+ 
- `pip` 

## Installation 
To install the package, run `pip install` from the root folder:

```bash
pip install -e .[dev]

pip install -e . # To exclude test and development dependencies
```

## Testing
Testing is done using the `pytest` framework. These commands are run from the root folder.

To run the full test suite:
```bash
pytest --verbose
```
To run tests from a single file or directory:
```bash
pytest <path_to_test> --verbose
```
To generate a XML coverage report:
```bash
pytest --verbose --cov=. --cov-report xml:coverage.xml 
```
To generate a HTML coverage report:
```bash
pytest --cov=. --cov-report html
```
## Implementation
The SDK currently provides classes that represent PDP entities (`Server`, `Credential`, `Processor`) as well as clients to interact with distinct endpoints. The API requests are made using the [httpx](https://www.python-httpx.org/) library, and serialization is done using the `json` built-in module. 
This client does the following: 

- Provides methods to execute standalone QueryFlow processors using `text_to_text/text_to_stream` that return the JSON execution output as a dictionary or text stream respectively.
- Supports overloading with the [multimethod](https://pypi.org/project/multimethod/) library to allow the usage of UUIDs instead of full entity objects.
- Supports the execution of a sequence of processors using the `QueryFlowSequenceProcessor` and `QueryFlowSequence` classes and the `execute` method. 

Currently, the SDK provides a `QueryFlowClient` class, that can be instanced with the base url of the QueryFlow instance and an API key.