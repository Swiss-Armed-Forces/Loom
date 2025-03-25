#!/usr/bin/env python

import json
from collections import defaultdict

import pika

aggregate = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


def callback(
    current_channel, method, properties, body
):  # pylint: disable=unused-argument
    # print(f"[x] Received {properties}")
    aggregate[properties.headers["task"]][properties.priority]["count"] += 1
    aggregate[properties.headers["task"]][properties.priority]["len"] += len(body)
    aggregate[properties.headers["task"]][properties.priority]["max_len"] = max(
        aggregate[properties.headers["task"]][properties.priority]["max_len"], len(body)
    )
    print(json.dumps(aggregate, indent=4))
    # current_channel.basic_ack(delivery_tag=method.delivery_tag)


connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbit"))
channel = connection.channel()
channel.basic_consume("celery", callback)

try:
    print("[*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()
connection.close()
