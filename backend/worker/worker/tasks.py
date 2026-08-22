"""This file has to exist to make celery's automatic task discovery happy.

We have to include here all modules containing top-level tasks.
"""

from worker.ai.tasks.describe_image_tool import describe_image_tool_task
from worker.ai.tasks.execute_query_tool import execute_query_tool_task
from worker.ai.tasks.get_file_tool import (
    get_file_field_tool_task,
    get_file_field_work_task,
    get_file_tool_task,
)
from worker.ai.tasks.list_folder_contents_tool import list_folder_contents_tool_task
from worker.ai.tasks.persist_processing_done import persist_processing_done_task
from worker.ai.tasks.persist_question import persist_question_task
from worker.ai.tasks.rag_tool import rag_pipeline_task, rag_search_tool_task
from worker.ai.tasks.search_by_filename_tool import search_by_filename_tool_task
from worker.ai.tasks.suggest_queries_tool import suggest_queries_task
from worker.ai.tasks.summarize_file_tool import summarize_file_tool_task
from worker.ai.tasks.translate_file_tool import translate_file_tool_task
from worker.create_archive import (
    create_archive_task,
    delete_archive_task,
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
    flush_file_storage_service_task,
    flush_root_task_info_on_idle_task,
    hide_periodically_task,
    reindex_lost_files_on_idle_task,
    seaweedfs_maintenance_task,
    shrink_periodically_task,
    sync_imap_flags_periodically_task,
    throttle_and_flush_lazybytes_task,
    unsubscribe_old_imap_folders_periodically_task,
)
from worker.periodic.tasks import (
    beat_healthcheck_task,
)
from worker.test import autoretry_test_task, canvas_test_task, sigkill_pgroup_task

# DO NOT REMOVE THIS ARRAY!!!
# the (then considered unused) imports would be removed by autoflake
tasks = [
    create_archive_task,
    delete_archive_task,
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
    flush_root_task_info_on_idle_task,
    throttle_and_flush_lazybytes_task,
    shrink_periodically_task,
    rag_pipeline_task,
    execute_query_tool_task,
    get_file_tool_task,
    get_file_field_tool_task,
    get_file_field_work_task,
    suggest_queries_task,
    rag_search_tool_task,
    persist_question_task,
    persist_processing_done_task,
    summarize_file_tool_task,
    translate_file_tool_task,
    describe_image_tool_task,
    list_folder_contents_tool_task,
    search_by_filename_tool_task,
    autoretry_test_task,
    canvas_test_task,
    sigkill_pgroup_task,
    image_description_task,
    hide_periodically_task,
    sync_imap_flags_periodically_task,
    reindex_lost_files_on_idle_task,
    unsubscribe_old_imap_folders_periodically_task,
    seaweedfs_maintenance_task,
    flush_file_storage_service_task,
    beat_healthcheck_task,
]
