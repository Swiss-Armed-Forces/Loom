from textwrap import dedent

import pytest
from common.file.file_repository import Secret
from common.services.lazybytes_service import LazyBytesService

from worker.index_file.tasks.secret_scan import (
    parse_ripsecrets_output,
    parse_trufflehog_output,
    ripsecrets_scan_task,
    trufflehog_scan_task,
)


@pytest.mark.parametrize(
    "extension, file_content, result",
    [
        (
            ".env",
            dedent("""
                APP_ENV=production
                APP_SECRET_KEY=8f9d0f4e3c2a7b1d6e5f0c3a8d7e6f5a
                """),
            [
                Secret(
                    line_number=3,
                    secret="APP_SECRET_KEY=8f9d0f4e3c2a7b1d6e5f0c3a8d7e6f5a",
                )
            ],
        ),
        (
            ".env",
            dedent("""
                AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
                AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
                AWS_DEFAULT_REGION=us-east-1
                """),
            [
                Secret(line_number=2, secret="AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"),
                Secret(
                    line_number=3,
                    secret="AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                ),
            ],
        ),
        (
            "",
            dedent("""
                -----BEGIN OPENSSH PRIVATE KEY-----
                b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
                QyNTUxOQAAACDtUokKSwahTl1UV+VmOL6PV35qAwOD1qpRd73c9OMxDwAAAJBXujs8V7o7
                PAAAAAtzc2gtZWQyNTUxOQAAACDtUokKSwahTl1UV+VmOL6PV35qAwOD1qpRd73c9OMxDw
                AAAEBCUyMQCop/GYIMTF92mEKFkBu4z0c8apiQt5Yhqofq3u1SiQpLBqFOXVRX5WY4vo9X
                fmoDA4PWqlF3vdz04zEPAAAACXVzZXJAbG9vbQECAwQ=
                -----END OPENSSH PRIVATE KEY-----

                """),
            [
                Secret(line_number=2, secret="-----BEGIN OPENSSH PRIVATE KEY-----"),
            ],
        ),
        (
            ".txt",
            dedent("""
                This text has no secrets in it! X-Ray Yankee Zulu
                """),
            [],
        ),
    ],
)
def test_ripsecrets_scan_task(
    extension: str,
    file_content: bytes,
    result: list[Secret],
    lazybytes_service_inmemory: LazyBytesService,
):
    lazy_bytes_obj = lazybytes_service_inmemory.from_bytes(file_content)
    secrets: list[Secret] = ripsecrets_scan_task(lazy_bytes_obj, extension)
    assert secrets == result


@pytest.mark.parametrize(
    "extension, file_content, result",
    [
        (
            ".env",
            "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/"
            + "T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
            [
                Secret(
                    line_number=1,
                    secret=dedent(
                        "https://hooks.slack.com/services/T00000000/"
                        + "B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
                    ),
                )
            ],
        ),
        (
            "",
            dedent("""
                -----BEGIN OPENSSH PRIVATE KEY-----
                b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
                QyNTUxOQAAACDtUokKSwahTl1UV+VmOL6PV35qAwOD1qpRd73c9OMxDwAAAJBXujs8V7o7
                PAAAAAtzc2gtZWQyNTUxOQAAACDtUokKSwahTl1UV+VmOL6PV35qAwOD1qpRd73c9OMxDw
                AAAEBCUyMQCop/GYIMTF92mEKFkBu4z0c8apiQt5Yhqofq3u1SiQpLBqFOXVRX5WY4vo9X
                fmoDA4PWqlF3vdz04zEPAAAACXVzZXJAbG9vbQECAwQ=
                -----END OPENSSH PRIVATE KEY-----
                """),
            [
                Secret(
                    line_number=2,
                    secret="-----BEGIN OPENSSH PRIVATE KEY-----\n"
                    + "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW\n"
                    + "QyNTUxOQAAACDtUokKSwahTl1UV+VmOL6PV35qAwOD1qpRd73c9OMxDwAAAJBXujs8V7o7\n"
                    + "PAAAAAtzc2gtZWQyNTUxOQAAACDtUokKSwahTl1UV+VmOL6PV35qAwOD1qpRd73c9OMxDw\n"
                    + "AAAEBCUyMQCop/GYIMTF92mEKFkBu4z0c8apiQt5Yhqofq3u1SiQpLBqFOXVRX5WY4vo9X\n"
                    + "fmoDA4PWqlF3vdz04zEPAAAACXVzZXJAbG9vbQECAwQ=\n"
                    + "-----END OPENSSH PRIVATE KEY-----\n",
                ),
            ],
        ),
        (
            ".txt",
            dedent("""
                This text has no secrets in it! X-Ray Yankee Zulu
                """),
            [],
        ),
    ],
)
def test_trufflehog_scan_task(
    extension: str,
    file_content: bytes,
    result: list[Secret],
    lazybytes_service_inmemory: LazyBytesService,
):
    lazy_bytes_obj = lazybytes_service_inmemory.from_bytes(file_content)
    secrets = trufflehog_scan_task(lazy_bytes_obj, extension)
    assert secrets == result


@pytest.mark.parametrize(
    "output",
    [
        (
            "./test.env:10:APP_SECRET_KEY=8f9d0f4e3c2a7b1d6e5f0c3a8d7e6f5a\n"
            + "./test.env:19:AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
            + "./test.env:20:AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        ),
    ],
)
def test_parse_ripsecrets_output(output):
    expected_secret_list = [
        Secret(
            line_number=10, secret="APP_SECRET_KEY=8f9d0f4e3c2a7b1d6e5f0c3a8d7e6f5a"
        ),
        Secret(line_number=19, secret="AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"),
        Secret(
            line_number=20,
            secret="AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        ),
    ]
    assert expected_secret_list == parse_ripsecrets_output(output)


TRUFFLE_HOG_JSON_OUTPUT = (
    '{"level":"info-0","ts":"2025-08-26T10:26:28+02:00","logger":"trufflehog",'
    '"msg":"running source","source_manager_worker_id":"qhWCF",'
    '"with_units":true}\n'
    '{"SourceMetadata":{"Data":{"Filesystem":{"file":"test.env","line":24}}},'
    '"SourceID":1,"SourceType":15,"SourceName":"trufflehog - filesystem",'
    '"DetectorType":30,"DetectorName":"SlackWebhook","DetectorDescription":'
    '"Slack webhooks are used to send messages from external sources into '
    "Slack channels. If compromised, they can be used to send unauthorized "
    'messages.","DecoderName":"PLAIN","Verified":false,'
    '"VerificationFromCache":false,"Raw":"https://hooks.slack.com/services/'
    'T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX","RawV2":"","Redacted":"",'
    '"ExtraData":{"rotation_guide":"https://howtorotate.com/docs/tutorials/'
    'slack-webhook/"},"StructuredData":null}\n'
    '{"level":"info-0","ts":"2025-08-26T10:26:28+02:00","logger":"trufflehog",'
    '"msg":"finished scanning","chunks":1,"bytes":680,"verified_secrets":0,'
    '"unverified_secrets":1,"scan_duration":"508.149309ms",'
    '"trufflehog_version":"3.88.25","verification_caching":{"Hits":0,"Misses":2,'
    '"HitsWasted":0,"AttemptsSaved":0,"VerificationTimeSpentMS":790}}\n'
)


@pytest.mark.parametrize(
    "output",
    [
        (TRUFFLE_HOG_JSON_OUTPUT),
    ],
)
def test_parse_trufflehog_output(output):
    # The expected result from parsing the trufflehog JSON output
    expected_secret_list = [
        Secret(
            line_number=24,
            secret="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
        )
    ]
    assert expected_secret_list == parse_trufflehog_output(output)
