"""Unit tests for how a headless agentic run is invoked and read back."""

import io

from aitools.aitools import build_agent_command, consume_stream

RESULT_ERROR = (
    '{"type":"result","subtype":"error_during_execution","is_error":true,'
    '"num_turns":7,"result":"failed"}'
)
RESULT_OK = '{"type":"result","subtype":"success","is_error":false,"num_turns":3}'


class TestBuildAgentCommand:
    def test_stream_json_carries_verbose(self):
        """Claude refuses --print with stream-json unless --verbose is given too."""
        command = build_agent_command("claude", "none", "do the thing")

        assert "--output-format" in command.argv
        assert command.argv[command.argv.index("--output-format") + 1] == "stream-json"
        assert "--verbose" in command.argv
        # The prompt travels on stdin, so its size is not bounded by ARG_MAX.
        assert command.stdin_text == "do the thing"
        assert "do the thing" not in command.argv


class TestConsumeStream:
    def test_result_event_reports_the_backends_failure(self):
        transcript = io.StringIO()

        outcome = consume_stream([RESULT_ERROR], transcript)

        assert outcome.reported_error is True
        assert outcome.turns == 7
        assert RESULT_ERROR in transcript.getvalue()

    def test_a_malformed_line_does_not_end_the_run(self):
        """An undecodable line is kept and skipped: the schema is the backend's."""
        transcript = io.StringIO()

        outcome = consume_stream(["not json at all", RESULT_OK], transcript)

        assert outcome.reported_error is False
        assert outcome.turns == 3
        assert "not json at all" in transcript.getvalue()
