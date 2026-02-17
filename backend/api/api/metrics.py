from typing import Iterable

from common.dependencies import get_file_repository, get_imap_service
from common.services.query_builder import QueryParameters
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
