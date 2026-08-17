# Architecture

Loom uses a microservices architecture running on Kubernetes (via minikube for single-node deployments).

## Services

Multiple services that are useful for production and development purposes are started:

| Service       | Url                                                          | Description                         | Remarks                                        |
|---------------|--------------------------------------------------------------|-------------------------------------|------------------------------------------------|
| Frontend      | [https://frontend.loom](https://frontend.loom)               | The Loom frontend                   |                                                |
| Open Webui    | [https://open-webui.loom](https://open-webui.loom)           | AI web interface                    |                                                |
| Roundcube     | [https://roundcube.loom](https://roundcube.loom)             | Email web interface                 |                                                |
| SeaweedFS     | [https://seaweedfs.loom](https://seaweedfs.loom)             | Admin UI for cluster management     |                                                |
| S3            | [https://s3.loom](https://s3.loom)                           | S3-compatible storage API           |                                                |
| API           | [https://api.loom](https://api.loom)                         | The Loom API                        | Swagger documentation: <https://api.loom/docs> |
| RabbitMQ      | [https://rabbit.loom](https://rabbit.loom)                   | Monitor rabbit messages             | user: `guest` password: `guest`                |
| Elasticvue    | [https://elasticvue.loom](https://elasticvue.loom)           | Elasticsearch management            | use "predefined clusters"                      |
| Elasticsearch | [https://elasticsearch.loom](https://elasticsearch.loom)     | Elasticsearch database              |                                                |
| Rspamd        | [https://rspamd.loom](https://rspamd.loom)                   | Rspamd spam detection engine        |                                                |
| RedisInsight  | [https://redisinsight.loom](https://redisinsight.loom)       | Manage the Redis DB                 |                                                |
| Prometheus    | [https://prometheus.loom](https://prometheus.loom)           | Manage Prometheus                   |                                                |
| Grafana       | [https://grafana.loom](https://grafana.loom)                 | Statistics, dashboards and alerting |                                                |
| Traefik       | [https://traefik.loom](https://traefik.loom)                 | Traefik reverse proxy               |                                                |
| Apache Tika   | [https://tika.loom](https://tika.loom)                       | Tika content extraction engine      |                                                |
| Dovecot       | [imaps://dovecot.loom:443](imaps://dovecot.loom:443)         | IMAP server                         | user: `user` password: `pass`                  |
| Ollama        | [https://ollama.loom](https://ollama.loom)                   | AI server                           |                                                |
| Gotenberg     | [https://gotenberg.loom](https://gotenberg.loom)             | Document rendering                  |                                                |

## Container Diagram

![Context Diagram](Documentation/ContainerDiagram.svg)

> External access to most services is intentional. Users may interact with the
> underlying services and their APIs directly.
