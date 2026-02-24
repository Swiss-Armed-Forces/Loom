from typing import Iterable

from common.dependencies import get_file_repository, get_imap_service, get_redis_client
from common.services.query_builder import QueryParameters
from common.utils.cache import get_cache_statistics
from fastapi import FastAPI
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics import MeterProvider


def count_files(_: CallbackOptions) -> Iterable[Observation]:
    file_repository = get_file_repository()
    query_id = file_repository.open_point_in_time()
    email_count = file_repository.count_by_query(
        query=QueryParameters(
            query_id=query_id,
            search_string="*",
        )
    )
    yield Observation(value=email_count)


def count_emails(_: CallbackOptions) -> Iterable[Observation]:
    file_repository = get_file_repository()
    query_id = file_repository.open_point_in_time()
    email_count = file_repository.count_by_query(
        query=QueryParameters(
            query_id=query_id,
            search_string='extension:".eml" OR file_type:"message/rfc822"',
        )
    )
    yield Observation(value=email_count)


def count_imap_emails(_: CallbackOptions) -> Iterable[Observation]:
    imap_service = get_imap_service()
    email_count = imap_service.count_messages(recurse=True)
    yield Observation(value=email_count)


def observe_cache_mem_size(_: CallbackOptions) -> Iterable[Observation]:
    redis_client = get_redis_client()
    stats = get_cache_statistics(redis_client)
    for namespace, entry in stats.root.items():
        yield Observation(value=entry.mem_size, attributes={"namespace": namespace})


def observe_cache_entries(_: CallbackOptions) -> Iterable[Observation]:
    redis_client = get_redis_client()
    stats = get_cache_statistics(redis_client)
    for namespace, entry in stats.root.items():
        yield Observation(
            value=entry.entries_count, attributes={"namespace": namespace}
        )


def observe_cache_hits(_: CallbackOptions) -> Iterable[Observation]:
    redis_client = get_redis_client()
    stats = get_cache_statistics(redis_client)
    for namespace, entry in stats.root.items():
        yield Observation(value=entry.hits_count, attributes={"namespace": namespace})


def observe_cache_misses(_: CallbackOptions) -> Iterable[Observation]:
    redis_client = get_redis_client()
    stats = get_cache_statistics(redis_client)
    for namespace, entry in stats.root.items():
        yield Observation(value=entry.miss_count, attributes={"namespace": namespace})


def init_metrics(api: FastAPI):
    # setup prometheus provider
    prometheus_reader = PrometheusMetricReader()
    provider = MeterProvider(metric_readers=[prometheus_reader])

    # instrument the fastapi app
    FastAPIInstrumentor.instrument_app(api, meter_provider=provider)

    # add custom metrics
    data_meter = provider.get_meter("data")
    data_meter.create_observable_up_down_counter(
        name="data.files",
        callbacks=[count_files],
        unit="files",
        description="Number of files",
    )
    data_meter.create_observable_up_down_counter(
        name="data.emails",
        callbacks=[count_emails],
        unit="email",
        description="Number of emails",
    )
    data_meter.create_observable_up_down_counter(
        name="data.imap.emails",
        callbacks=[count_imap_emails],
        unit="email",
        description="Number of emails in IMAP inbox",
    )

    # add cache metrics
    cache_meter = provider.get_meter("cache")
    cache_meter.create_observable_gauge(
        name="cache.mem_size",
        callbacks=[observe_cache_mem_size],
        unit="bytes",
        description="Memory usage of cache namespace",
    )
    cache_meter.create_observable_gauge(
        name="cache.entries_count",
        callbacks=[observe_cache_entries],
        unit="entries",
        description="Number of entries in cache namespace",
    )
    cache_meter.create_observable_gauge(
        name="cache.hits_count",
        callbacks=[observe_cache_hits],
        unit="hits",
        description="Number of cache hits",
    )
    cache_meter.create_observable_gauge(
        name="cache.miss_count",
        callbacks=[observe_cache_misses],
        unit="misses",
        description="Number of cache misses",
    )
