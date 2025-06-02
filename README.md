# Pureinsights Discovery Platform: Inference SDK 
_Discovery Inference SDK_ is a Python package that allows developers to programatically access Discovery features. Currently, it supports executing one or multiple QueryFlow processors. 

## Requirements
- Python 3.13+ 
- `pip` 

## Installation 
To install the package, run `pip install` inside the `pdp-inference` directory:

```bash
pip install -e .[dev]

pip install -e . # To exclude test and development dependencies
```

## Testing
Testing is done using the `pytest` framework. These commands are run from inside the `pdp-inference` directory. 

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
The SDK currently provides classes that represent PDP entities (`Server`, `Credential`, `Processor`) as well as clients to interact with distinct endpoints. The API requests are made using the [httpx](https://www.python-httpx.org/) library, and serialization is done using the `json` built-in module. Method overloading is handled by using the [multimethod](https://pypi.org/project/multimethod/) library.

Currently, the SDK provides a `QueryFlowClient` class, that can be instanced with the base url of the QueryFlow instance and an API key.