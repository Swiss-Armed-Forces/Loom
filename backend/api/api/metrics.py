import logging
import math
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Iterable

from common.dependencies import (
    get_file_repository,
    get_imap_service,
    get_redis_cache_client,
)
from common.file.file_repository import Stat
from common.services.query_builder import QueryParameters
from common.utils.cache import cache_get, cache_set, get_cache_statistics
from fastapi import FastAPI
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    MetricExporter,
    MetricExportResult,
    MetricsData,
    PeriodicExportingMetricReader,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

PERIODIC_METRICS_REFRESH__MS = 60 * 1000
ADAPTIVE_CACHE_TIMEOUT_SAFETY_FACTOR = 0.8
ADAPTIVE_CACHE_MAX_AGE_FACTOR = 10  # max_age = this × PERIODIC_METRICS_REFRESH__MS
ADAPTIVE_CACHE_TIMEOUT_CAP__MS = 60 * 60 * 1000  # 1 hour
ADAPTIVE_CACHE_REDIS_TTL_FACTOR = 3  # Redis TTL = this × max_age


class LoggingMetricExporter(MetricExporter):
    """Metric exporter that logs metric collection."""

    def export(
        self,
        metrics_data: MetricsData,
        timeout_millis: float = 10_000,
        **kwargs,
    ) -> MetricExportResult:
        """Log metric collection."""
        logger.debug("Periodic metric collection triggered: %s", metrics_data)
        return MetricExportResult.SUCCESS

    def shutdown(self, timeout_millis: float = 30_000, **kwargs) -> None:
        pass

    def force_flush(self, timeout_millis: float = 10_000) -> bool:
        return True


class MetricCache(BaseModel):
    # Store raw (value, attributes) tuples rather than Observation objects
    # so that the Pydantic model is safely picklable by the Redis cache layer.
    # Must be defined at module level (not inside a function) for pickle to work.
    observations_raw: list[tuple[Any, Any]]
    timestamp: datetime = Field(default_factory=datetime.now)
    collection_time: timedelta


def with_adaptive_cache(max_age: timedelta | None = None):
    """Decorator that caches metric Observations based on collection time.

    Cached results are returned when the previous collection took longer than the
    available timeout budget. A ``max_age`` TTL forces re-collection after the cache
    expires, preventing indefinitely stale metrics.
    """
    if max_age is None:
        max_age = timedelta(
            milliseconds=PERIODIC_METRICS_REFRESH__MS * ADAPTIVE_CACHE_MAX_AGE_FACTOR
        )

    def decorator(
        func: Callable[[CallbackOptions], Iterable[Observation]],
    ) -> Callable:
        # One Redis namespace per decorated function — shared across all workers.
        namespace = f"metrics:{func.__qualname__}"

        @wraps(func)
        def wrapper(options: CallbackOptions) -> Iterable[Observation]:
            # Cap timeout_millis before building a timedelta: the periodic reader
            # passes math.inf, which causes OverflowError inside timedelta().
            timeout_ms = min(options.timeout_millis, ADAPTIVE_CACHE_TIMEOUT_CAP__MS)
            timeout = timedelta(
                milliseconds=timeout_ms * ADAPTIVE_CACHE_TIMEOUT_SAFETY_FACTOR
            )

            # Load cache entry from Redis (shared across all Uvicorn workers).
            result = cache_get(namespace, None)
            cache: MetricCache | None = result.value if result.hit else None

            if cache:
                cache_age = datetime.now() - cache.timestamp
                enough_time_to_compute = cache.collection_time < timeout
                not_expired = cache_age < max_age

                if not enough_time_to_compute:
                    # Can't afford to recompute inline — return cached value even if stale.
                    # This prevents the Prometheus scrape from blocking and timing out when
                    # the cache has expired or the periodic reader hasn't populated it yet.
                    # The PeriodicExportingMetricReader (which always has a large timeout budget
                    # and therefore always recomputes) will refresh the cache in the background.
                    logger.info(
                        "Returning cached metric %s (collected in %s, age: %s, expired: %s)",
                        func.__name__,
                        cache.collection_time,
                        cache_age,
                        not not_expired,
                    )
                    for value, attrs in cache.observations_raw:
                        yield Observation(value=value, attributes=attrs)
                    return

            # Collect new metric and measure time
            start_time = datetime.now()
            observations = list(func(options))
            collection_time = datetime.now() - start_time

            # Persist to Redis so all workers share the same cached value.
            cache_set(
                namespace,
                None,
                MetricCache(
                    observations_raw=[(o.value, o.attributes) for o in observations],
                    collection_time=collection_time,
                ),
                ttl_seconds=int(
                    max_age.total_seconds() * ADAPTIVE_CACHE_REDIS_TTL_FACTOR
                ),
            )

            logger.info(
                "Collected metric %s in %s",
                func.__name__,
                collection_time,
            )

            yield from observations

        return wrapper

    return decorator


@with_adaptive_cache()
def count_files(_: CallbackOptions) -> Iterable[Observation]:
    file_repository = get_file_repository()
    query_id = file_repository.open_point_in_time()
    count = file_repository.count_by_query(
        query=QueryParameters(
            query_id=query_id,
            search_string="hidden:*",
        )
    )
    yield Observation(value=count)


@with_adaptive_cache()
def count_files_by_state(_: CallbackOptions) -> Iterable[Observation]:
    file_repository = get_file_repository()
    query_id = file_repository.open_point_in_time()
    state_stat = file_repository.get_stat_generic(
        query=QueryParameters(
            query_id=query_id,
            search_string="hidden:*",
        ),
        stat=Stat.STATES,
    )
    for state_data in state_stat.data:
        yield Observation(
            value=state_data.hits_count, attributes={"state": state_data.name}
        )


@with_adaptive_cache()
def count_files_by_source(_: CallbackOptions) -> Iterable[Observation]:
    file_repository = get_file_repository()
    query_id = file_repository.open_point_in_time()
    source_stat = file_repository.get_stat_generic(
        query=QueryParameters(
            query_id=query_id,
            search_string="hidden:*",
        ),
        stat=Stat.SOURCES,
    )
    for source_data in source_stat.data:
        yield Observation(
            value=source_data.hits_count, attributes={"source": source_data.name}
        )


@with_adaptive_cache()
def count_files_hidden(_: CallbackOptions) -> Iterable[Observation]:
    file_repository = get_file_repository()
    query_id = file_repository.open_point_in_time()
    count = file_repository.count_by_query(
        query=QueryParameters(
            query_id=query_id,
            search_string="hidden:true",
        )
    )
    yield Observation(value=count)


@with_adaptive_cache()
def count_emails(_: CallbackOptions) -> Iterable[Observation]:
    file_repository = get_file_repository()
    query_id = file_repository.open_point_in_time()
    count = file_repository.count_by_query(
        query=QueryParameters(
            query_id=query_id,
            search_string='(extension:".eml" OR file_type:"message/rfc822") AND hidden:*',
        )
    )
    yield Observation(value=count)


@with_adaptive_cache()
def count_imap_emails(_: CallbackOptions) -> Iterable[Observation]:
    imap_service = get_imap_service()
    email_count = imap_service.count_messages(recurse=True)
    yield Observation(value=email_count)


@with_adaptive_cache()
def observe_cache_mem_size(_: CallbackOptions) -> Iterable[Observation]:
    stats = get_cache_statistics(get_redis_cache_client())
    for namespace, entry in stats.root.items():
        yield Observation(value=entry.mem_size, attributes={"namespace": namespace})


@with_adaptive_cache()
def observe_cache_entries(_: CallbackOptions) -> Iterable[Observation]:
    stats = get_cache_statistics(get_redis_cache_client())
    for namespace, entry in stats.root.items():
        yield Observation(
            value=entry.entries_count, attributes={"namespace": namespace}
        )


@with_adaptive_cache()
def observe_cache_hits(_: CallbackOptions) -> Iterable[Observation]:
    stats = get_cache_statistics(get_redis_cache_client())
    for namespace, entry in stats.root.items():
        yield Observation(value=entry.hits_count, attributes={"namespace": namespace})


@with_adaptive_cache()
def observe_cache_misses(_: CallbackOptions) -> Iterable[Observation]:
    stats = get_cache_statistics(get_redis_cache_client())
    for namespace, entry in stats.root.items():
        yield Observation(value=entry.miss_count, attributes={"namespace": namespace})


def init_metrics(api: FastAPI):
    logger.info("Initializing Metrics")

    # setup prometheus provider
    prometheus_reader = PrometheusMetricReader()

    # Periodic reader to warm up metric caches in the background.
    # The PrometheusMetricReader doesn't have a configurable export_timeout,
    # so we use this periodic reader to trigger metric collection every N seconds,
    # which populates the @with_adaptive_cache decorators.
    # This ensures Prometheus scrapes always get fast cached results.
    periodic_reader = PeriodicExportingMetricReader(
        exporter=LoggingMetricExporter(),
        export_interval_millis=PERIODIC_METRICS_REFRESH__MS,
        export_timeout_millis=math.inf,
    )

    provider = MeterProvider(metric_readers=[prometheus_reader, periodic_reader])

    # instrument the fastapi app
    FastAPIInstrumentor.instrument_app(api, meter_provider=provider)

    # add custom metrics
    data_meter = provider.get_meter("data")
    data_meter.create_observable_up_down_counter(
        name="data.files",
        callbacks=[count_files],
        unit="file",
        description="Number of files",
    )
    data_meter.create_observable_up_down_counter(
        name="data.files_by_state",
        callbacks=[count_files_by_state],
        unit="file",
        description="Number of files by state",
    )
    data_meter.create_observable_up_down_counter(
        name="data.files_by_source",
        callbacks=[count_files_by_source],
        unit="file",
        description="Number of files by source",
    )
    data_meter.create_observable_up_down_counter(
        name="data.files_hidden",
        callbacks=[count_files_hidden],
        unit="file",
        description="Number of hidden files",
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
        unit="byte",
        description="Memory usage of cache namespace",
    )
    cache_meter.create_observable_gauge(
        name="cache.entries_count",
        callbacks=[observe_cache_entries],
        unit="entry",
        description="Number of entries in cache namespace",
    )
    cache_meter.create_observable_gauge(
        name="cache.hits_count",
        callbacks=[observe_cache_hits],
        unit="hit",
        description="Number of cache hits",
    )
    cache_meter.create_observable_gauge(
        name="cache.miss_count",
        callbacks=[observe_cache_misses],
        unit="miss",
        description="Number of cache misses",
    )
