# Grammatical Error Correction Worker

A component that runs a grammatical error correction (GEC) engine to process incoming requests. This implementation uses
a Transformer-based model to normalize the input text and is based on the FairSeq modular NMT implementation.

## Setup

The Estonian GEC worker can be used by running the prebuilt [docker image](ghcr.io/tartunlp/grammar-worker).

The container is designed to run in a CPU environment. For a manual setup, please refer to the included Dockerfile and
the Conda environment specification described in `config/environment.yml`.

The worker depends on the following components:

- [RabbitMQ message broker](https://www.rabbitmq.com/)

The following environment variables should be specified when running the container:

- `MQ_USERNAME` - RabbitMQ username
- `MQ_PASSWORD` - RabbitMQ user password
- `MQ_HOST` - RabbitMQ host
- `MQ_PORT` (optional) - RabbitMQ port (`5672` by default)

### Performance and Hardware Requirements

TODO

### Request Format

The worker consumes GEC requests from a RabbitMQ message broker and responds with the replacement suggestions. The
following format is compatible with the [GEC API](ghcr.io/tartunlp/grammar-api).

Requests should be published with the following parameters:

- Exchange name: `grammar` (exchange type is `direct`)
- Routing key: `grammar.<language>` where `<language>` refers to 2-letter ISO language code of the input text. For
  example `grammar.et`.
- Message properties:
    - Correlation ID - a UID for each request that can be used to correlate requests and responses.
    - Reply To - name of the callback queue where the response should be posted.
    - Content Type - `application/json`
- JSON-formatted message content with the following keys:
    - `text` – input text, either a string or a list of strings which are allowed to contain multiple sentences or
      paragraphs.
    - `language` – 2-letter ISO language code

The worker will return a response with the following parameters:

- Exchange name: (empty string)
- Routing key: the Reply To property value from the request
- Message properties:
    - Correlation ID - the Correlation ID value of the request
    - Content Type - `application/json`
- JSON-formatted message content with the following keys:
    - `status` - a human-readable status message, `OK` by default
    - `status_code` – (integer) a HTTP status code, `200` by default
    - `corrections` - A list of corrections formatted as the POST request output defined in
      the [API](github.com/tartunlp/grammar-api). May be `null` in case `status_code!=200`

Known non-OK responses can occur in case the request format was incorrect. Example request and response:

```
{
    "text": 1,
    "language": "et"
}
```

```
{
    "status": "Error parsing input: {'text': ['Invalid value.']}",
    "status_code": 400,
    "corrections": null
}
```

The JSON-formatted part of the `status` field is the
[ValidationError](https://marshmallow.readthedocs.io/en/stable/_modules/marshmallow/exceptions.html) message from
Marshmallow Schema validation.