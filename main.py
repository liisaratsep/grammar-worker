import logging.config
from os import environ
from argparse import ArgumentParser, FileType
import yaml
from yaml.loader import SafeLoader
from pika import ConnectionParameters, credentials

from gec_worker.mq_consumer import MQConsumer
from gec_worker.gec import GEC

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('--worker-config', type=FileType('r'), default='config/config.yaml',
                        help="The worker config YAML file to load.")
    parser.add_argument('--log-config', type=FileType('r'), default='config/logging.ini',
                        help="Path to log config file.")
    args = parser.parse_known_args()[0]
    logging.config.fileConfig(args.log_config.name)

    with open(args.worker_config.name, 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=SafeLoader)

    exchange_name = 'grammar'

    routing_key = f"{exchange_name}.{config['language']}"
    mq_parameters = ConnectionParameters(host=environ.get('MQ_HOST', 'localhost'),
                                         port=int(environ.get('MQ_PORT', '5672')),
                                         credentials=credentials.PlainCredentials(
                                             username=environ.get('MQ_USERNAME', 'guest'),
                                             password=environ.get('MQ_PASSWORD', 'guest')))

    gec = GEC(**config['parameters'])
    worker = MQConsumer(gec=gec,
                        connection_parameters=mq_parameters,
                        exchange_name=exchange_name,
                        routing_key=routing_key)

    worker.start()
