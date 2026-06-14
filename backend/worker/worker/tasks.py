"""This file has to exist to make celery's automatic task discovery happy.

We have to include here all modules containing top-level tasks.
"""

from worker.ai import process_question_task
from worker.create_archive import (
    create_archive_task,
)
from worker.create_archive import dispatch_tasks as create_archive_dispatch_tasks
from worker.create_archive import (
    index_archive,
    update_archive_task,
)
from worker.create_archive.tasks import (
    detect_loom_archive as detect_loom_archive_module,
)
from worker.create_archive.tasks import (
    load_loom_archive_encrypted as load_loom_archive_encrypted_module,
)
from worker.create_archive.tasks import unzip_loom_archive as unzip_loom_archive_module
from worker.index_file import (
    add_tags_to_file_task,
    dispatch_tasks,
    image_description_task,
    index_file_task,
    remove_tag_from_file_task,
    summarize_file_task,
    translate_file_task,
    update_file_task,
)
from worker.periodic import (
    compute_complete_estimate_task,
    flush_on_idle_task,
    hide_periodically_task,
    reindex_lost_files_on_idle_task,
    seaweedfs_maintenance_task,
    shrink_periodically_task,
    sync_flagged_emails_periodically_task,
    unsubscribe_old_imap_folders_periodically_task,
)
from worker.test import autoretry_test_task, canvas_test_task, sigkill_pgroup_task

# DO NOT REMOVE THIS ARRAY!!!
# the (then considered unused) imports would be removed by autoflake
tasks = [
    create_archive_task,
    create_archive_dispatch_tasks,
    index_archive,
    update_archive_task,
    detect_loom_archive_module,
    load_loom_archive_encrypted_module,
    unzip_loom_archive_module,
    dispatch_tasks,
    index_file_task,
    add_tags_to_file_task,
    remove_tag_from_file_task,
    update_file_task,
    summarize_file_task,
    translate_file_task,
    compute_complete_estimate_task,
    flush_on_idle_task,
    shrink_periodically_task,
    process_question_task,
    autoretry_test_task,
    canvas_test_task,
    sigkill_pgroup_task,
    image_description_task,
    hide_periodically_task,
    sync_flagged_emails_periodically_task,
    reindex_lost_files_on_idle_task,
    unsubscribe_old_imap_folders_periodically_task,
    seaweedfs_maintenance_task,
]
