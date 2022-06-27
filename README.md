# Grammatical Error Correction Worker

A component that runs a grammatical error correction (GEC) engine to process incoming requests. This implementation uses
a Transformer-based model to normalize the input text and is based on the
custom [modular NMT implementation of FairSeq](https://github.com/TartuNLP/fairseq).

## Setup

The Estonian GEC worker can be used by running the prebuilt images published alongside this repository.

There are two seprate images:

- [`grammar-worker`](https://ghcr.io/tartunlp/grammar-worker) (documented below)
- [`grammar-model`](https://ghcr.io/tartunlp/grammar-model)
  (documented in [`models/README.md`](https://github.com/TartuNLP/grammar-worker/tree/main/models))

The worker can be set up using the [`grammar-worker`](https://ghcr.io/tartunlp/grammar-worker)
image. This image contains only the environment setup and code to run the models, and is designed to be used in a CPU
environment. The container should be configured using the following parameters:

- Volumes:
    - `/app/models/` - the image does not contain the model files and these must be attached as described in
      [`models/README.md`](https://github.com/TartuNLP/grammar-worker/tree/main/models).

- Environment variables:
    - Variables that configure the connection to a [RabbitMQ message broker](https://www.rabbitmq.com/):
        - `MQ_USERNAME` - RabbitMQ username
        - `MQ_PASSWORD` - RabbitMQ user password
        - `MQ_HOST` - RabbitMQ host
        - `MQ_PORT` (optional) - RabbitMQ port (`5672` by default)
        - `MQ_EXCHANGE` (optional) - RabbitMQ exchange name (`grammar` by default)
        - `MQ_CONNECTION_NAME` (optional) - friendly connection name (`GEC worker` by default)
        - `MQ_HEARTBEAT` (optional) - heartbeat interval (`60` seconds by default)
    - PyTorch-related variables:
        - `MKL_NUM_THREADS` (optional) - number of threads used for intra-op parallelism by PyTorch. This defaults to
          the number of CPU cores which may cause computational overhead when deployed on larger nodes. Alternatively,
          the `docker run` flag `--cpuset-cpus` can be used to control this. For more details, refer to
          the [performance and hardware requirements](#performance-and-hardware-requirements) section below.
    - Worker-related variables:
        - `WORKER_MAX_INPUT_LENGTH` (optional) - the number of characters allowed per request (`10000` by default).
          Longer requests will return validation errors.

- Optional runtime flags (the `COMMAND` option):
    - `--model-config` - path to the model config file (`models/config.yaml` by default). The default file is included
      in images that already include models. Compatible sample files are included in the `models/` directory and the
      format is described in [`models/README.md`](https://github.com/TartuNLP/grammar-worker/tree/main/models)).
    - `--log-config` - path to logging config files (`logging/logging.ini` by default), `logging/debug.ini` can be used
      for debug-level logging
    - `--port` - port of the healthcheck probes (`8000` by default):

- Endpoints for healthcheck probes:
    - `/health/startup`
    - `/health/readiness`
    - `/health/liveness`

### Building new images

When building the image, the model can be built with different targets. BuildKit should be enabled to skip any unused
stages of the build.

- `worker-base` - the worker code without any models.
- `worker-model` - a worker with an included model. Requires **one** of the following build-time arguments:
    - `MODEL_IMAGE` - the image name where the model is copied from. For example any of
      the [`translation-model`](https://ghcr.io/TartuNLP/grammar-model) images.
    - `MODEL_CONFIG_FILE` - path to the model configuration file, for example `models/general.yaml`. The file must
      contain the otherwise optional key `huggingface` to download the model or the build will fail.

- `env` - an intermediate build stage with all packages installed, but no code.
- `model-cp` - images that only contain model files and configuration. The separate stage is used to cache this step and
  speed up builds because model files can be very large. Published
  at [`translation-model`](https://ghcr.io/TartuNLP/grammar-model). Alternatively, these can be used
  as init containers to copy models over during startup, but this is quite slow and not recommended.
- `model` - an alias for the model image, the value of `MODEL_IMAGE` or `model-cp` by default.

## Manual / development setup

For a manual setup, please refer to the included Dockerfile and the environment specification described in
`requirements/requirements.txt`.
Additionally, [`models/README.md`](https://github.com/TartuNLP/grammar-worker/tree/main/models) describes how models
should be set up correctly.

To initialize the sentence splitting functionality, the following command should be run before starting the application:

```python -c "import nltk; nltk.download(\"punkt\")"```

RabbitMQ and PyTorch parameters should be configured with environment variables as described above. The worker can be
started with:

```python main.py [--model-logging models/logging.yaml] [--log-logging logging/logging.ini]```

### Performance and Hardware Requirements

The exact RAM usage depends on the model and should always be tested, but a conservative estimate is to have **8 GB of
memory** available.

The performance depends on the available CPU resources, however, this should be finetuned for the deployment
infrastructure. By default, PyTorch will try to utilize all CPU cores to 100% and run as many threads as there are
cores. This can cause major computational overhead if the worker is deployed on large nodes. The **number of threads
used should be limited** using the `MKL_NUM_THREADS` environment variable or the `docker run` flag `--cpuset-cpus`.

Limiting CPU usage by docker configuration which only limits CPU shares is not sufficient (e.g. `docker run` flag
`--cpus` or the CPU limit in K8s, unless the non-default
[static CPU Manager policy](https://kubernetes.io/docs/tasks/administer-cluster/cpu-management-policies/) is used). For
example, on a node with 128 cores, setting the CPU limit at `16.0` results in 128 parallel threads running with each one
utilizing only 1/8 of each core's computational potential. This amplifies the effect of multithreading overhead and can
result in inference speeds up to 20x slower than expected.

Although the optimal number of threads depends on the exact model and infrastructure used, a good starting point is
around `16`. With optimal configuration and modern hardware, the worker should be able to process ~7 sentences per
second. For more information, please refer to
[PyTorch documentation](https://pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference.html).

### Request Format

The worker consumes GEC requests from a RabbitMQ message broker and responds with the replacement suggestions. The
following format is compatible with the [GEC API](https://ghcr.io/tartunlp/grammar-api).

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
      the [API](https://github.com/tartunlp/grammar-api). May be `null` in case `status_code!=200`
