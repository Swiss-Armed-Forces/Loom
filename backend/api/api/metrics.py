import logging
import math
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Iterable

from common.dependencies import (
    get_file_repository,
    get_imap_service,
    get_redis_cache_client,
)
from common.file.file_repository import Stat
from common.services.query_builder import QueryParameters
from common.utils.cache import CacheStatistics, get_cache_statistics
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


def with_adaptive_cache():
    """Decorator that caches metric Observations based on collection time."""

    class MetricCache(BaseModel):
        # Allow Observation type which doesn't have Pydantic schema
        model_config = {"arbitrary_types_allowed": True}

        observations: list[Observation]
        timestamp: datetime = Field(default_factory=datetime.now)
        collection_time: timedelta

    def decorator(
        func: Callable[[CallbackOptions], Iterable[Observation]],
    ) -> Callable:
        cache: MetricCache | None = None

        @wraps(func)
        def wrapper(options: CallbackOptions) -> Iterable[Observation]:
            nonlocal cache

            # Return cached result if we won't be able to collect them in time
            timeout = timedelta(
                milliseconds=(
                    options.timeout_millis * ADAPTIVE_CACHE_TIMEOUT_SAFETY_FACTOR
                )
            )

            if cache:
                enough_time_to_compute = cache.collection_time < timeout
                if not enough_time_to_compute:
                    logger.info(
                        "Returning cached metric %s (collected in %s, at: %s)",
                        func.__name__,
                        cache.collection_time,
                        cache.timestamp,
                    )
                    yield from cache.observations
                    return

            # Collect new metric and measure time
            start_time = datetime.now()
            observations = list(func(options))
            collection_time = datetime.now() - start_time

            # Update cache
            cache = MetricCache(
                observations=observations,
                collection_time=collection_time,
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


def with_cached_cache_statistics(ttl: timedelta | None = None):
    """Decorator factory that provides cached cache statistics to the function."""
    if ttl is None:
        ttl = timedelta(seconds=10)

    class CacheState(BaseModel):
        stats: CacheStatistics
        timestamp: datetime = Field(default_factory=datetime.now)

    # Cache state stored in closure
    cache: CacheState | None = None

    def decorator(
        func: Callable[[CallbackOptions, CacheStatistics], Iterable[Observation]],
    ) -> Callable:
        @wraps(func)
        def wrapper(options: CallbackOptions) -> Iterable[Observation]:
            current_time = datetime.now()
            # Check if cache is expired or empty
            nonlocal cache
            if cache is None or (current_time - cache.timestamp) > ttl:
                redis_client = get_redis_cache_client()
                cache = CacheState(stats=get_cache_statistics(redis_client))

            # Call the original function with cached stats
            return func(options, cache.stats)

        return wrapper

    return decorator


@with_adaptive_cache()
@with_cached_cache_statistics()
def observe_cache_mem_size(
    _: CallbackOptions, stats: CacheStatistics
) -> Iterable[Observation]:
    for namespace, entry in stats.root.items():
        yield Observation(value=entry.mem_size, attributes={"namespace": namespace})


@with_adaptive_cache()
@with_cached_cache_statistics()
def observe_cache_entries(
    _: CallbackOptions, stats: CacheStatistics
) -> Iterable[Observation]:
    for namespace, entry in stats.root.items():
        yield Observation(
            value=entry.entries_count, attributes={"namespace": namespace}
        )


@with_adaptive_cache()
@with_cached_cache_statistics()
def observe_cache_hits(
    _: CallbackOptions, stats: CacheStatistics
) -> Iterable[Observation]:
    for namespace, entry in stats.root.items():
        yield Observation(value=entry.hits_count, attributes={"namespace": namespace})


@with_adaptive_cache()
@with_cached_cache_statistics()
def observe_cache_misses(
    _: CallbackOptions, stats: CacheStatistics
) -> Iterable[Observation]:
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
