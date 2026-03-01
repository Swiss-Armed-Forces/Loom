"""This file has to exist to make celery's automatic task discovery happy.

We have to include here all modules containing top-level tasks.
"""

from worker.ai import process_question_task
from worker.create_archive import create_archive_task
from worker.index_file import (
    add_tags_to_file_task,
    index_file_task,
    remove_tag_from_file_task,
    set_hidden_state_task,
    summarize_file_task,
    translate_file_task,
)
from worker.periodic import (
    flush_on_idle_task,
    hide_periodically_task,
    reindex_started_files_on_idle_task,
    shrink_periodically_task,
)
from worker.test import canvas_test_task, sigkill_pgroup_task

# DO NOT REMOVE THIS ARRAY!!!
# the (then considered unused) imports would be removed by autoflake
tasks = [
    create_archive_task,
    index_file_task,
    add_tags_to_file_task,
    remove_tag_from_file_task,
    set_hidden_state_task,
    summarize_file_task,
    translate_file_task,
    flush_on_idle_task,
    shrink_periodically_task,
    process_question_task,
    canvas_test_task,
    sigkill_pgroup_task,
    hide_periodically_task,
    reindex_started_files_on_idle_task,
]
