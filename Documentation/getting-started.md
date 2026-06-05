<!-- markdownlint-disable -->

# Getting Started Guide

[TOC]

## Using Loom

### Uploading Files

To upload files to Loom:

1. Open Loom and choose the "Upload" option.
2. Double-click to open a file explorer, or drag and drop files into the upload area.
3. Once uploaded, Loom will automatically process and index the files.

Files can also be uploaded directly via the S3-compatible API.

### Searching for a File

1. Use the query box to search by filename, e.g., `filename:my-document.pdf`
2. Alternatively, search by typing a keyword from the file content.
3. If there are multiple files with similar names, use the `*` wildcard to narrow results.

### Displaying RAW JSON for Indexed Files

1. Search for the file and select it from the results list.
2. Click on the "View content" button.
3. Select the "RAW" tab to view the raw JSON data, including file metadata and contents.

Tips:

- You can disable line wrapping in the RAW JSON viewer by clicking the options icon (top right corner of the modal).
- The RAW JSON viewer displays the actual file content, including hiddenness, tasks associated, and bytes.

### Tagging Files

Tagging is done by clicking the tag button in the details view or using the tagging functionality from the left-hand side menu.

1. Click on the tag icon near the file name when the file is found.
2. Create or choose a tag for the document.
3. Use the "Add tag" functionality in the left sidebar to add tags individually or in bulk.

Note: Tags are case-sensitive.

### AI-Powered Auto Tagging

Loom can automatically propagate tags to similar documents using AI. Once you apply a tag to one or more documents, Loom analyzes the content and finds other documents in the index that are semantically similar, tagging them automatically.

To use auto tagging:

1. Tag one or more documents manually as described above.
2. Loom will use AI to identify similar documents across the index and apply the same tag to them.

This is useful for quickly categorizing large document sets where manually reviewing every file is not practical.

### Hiding and Unhiding Files

1. Click on the eye icon to hide or unhide a file.
2. Alternatively, use the mass-hide/show files button in the left-hand side menu.
3. Hidden files will disappear from the details view but can be found using the query `hidden:true`.

### Querying Files by Type

To find files of a specific type, use the `extension:` syntax:

- `extension:.pdf` to find all PDF files
- `extension:.txt` to find all text files
- `filename:*.html` to find all HTML files

### Save a Query

- To save a query, click on the "Save current query" button at the bottom of the left sidebar.
- Saved queries will be stored in your browser's local cache and can be retrieved by clicking on them in the left sidebar.
- Note: Saved queries are browser-local and cannot be retrieved from another browser.

### Translation

**Translate a search query:**

- Click on the translation indicator in the search bar and select the target language.
- Enter your query and search. The translated text will appear in the search results.

**Translate a file back to English:**

- Click the translate icon on the file and select the source language.

**Translate arbitrary text:**

- Click on the menu button at the top right and select "Translate".
- Type in text to be translated and specify the language or let it auto-detect.
- You can also upload a file for translation.

### Working with Archives

**Upload an archive:**

- Click on the "Upload" button in the left sidebar.
- Drag and drop the archive into the upload space, or select it from your files.
- ZIP and tar.gz archives will be decompressed automatically and their contents indexed individually.

**Filter for the content of an archive:**

- Use the search bar with `full_path:<filename>.tar.gz` or `filename:*.zip` to filter for the contents of a specific archive.

**Create an archive from search results:**

- Click on the "Create archive" button in the left sidebar.
- This will compile all files from the current search results into a single archive.
- The archive name is based on the creation datetime and can be found in the archives panel at the top right.

**Download an end-to-end encrypted archive:**

- Navigate to the archive section using the button at the top of the screen to the right of the search button.
- Click on the "Download" button next to the archive file name to get an encrypted version.

### Working with Emails

- To upload an email file (.eml), click on the "Upload" button in the left sidebar.
- The uploaded email will be processed by Rspamd and its contents indexed.

### Download the Original File

- Click on the "Download" button and select the option to download the original content.
- The downloaded file will have the same hash as the original.

## Monitoring and Diagnostics

### Check for Failed Tasks

- Failed tasks can be found by checking the alert in the top right corner of Loom or on the statistics page.
- On the statistics page, you can sort tasks into "stats" and check for any failures.

### Find Pipeline Tasks in Flower

- Click on the menu button at the top right and select "Flower".
- Click on the "tasks" option in the top panel to view a list of tasks.
- You can sort and filter this list to view different types of tasks.

### Inspect the RabbitMQ Message Queue

- Access RabbitMQ using the burger menu.
- Switch to the "Queues and Streams" tab.
- Confirm that none of the active tasks have any messages queued.

### Check Email Classification in RspamD

- Access RspamD using the burger menu.
- Check the RspamD homepage for the classification of the email you uploaded.
