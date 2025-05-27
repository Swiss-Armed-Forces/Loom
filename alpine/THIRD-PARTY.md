<!-- markdownlint-disable -->

Loom utilizes the **Alpine Linux** operating-system distribution as a standalone Docker image.

**Software Licenses:**

* *Aggregated licensing model* – Alpine Linux is a collection of independently-licensed components; no single umbrella licence applies.
* **Linux kernel** – GNU General Public License v2.0 only (GPL-2.0-only) **WITH** Linux-syscall-note.
* **BusyBox** – GPL-2.0-only.
* **musl libc** – MIT License.
* **Other packages** – Assorted FSF/OSI-approved licences (e.g. GPL, LGPL, MIT, Apache-2.0, BSD).
  Everyone distributing a Loom image that embeds Alpine Linux must satisfy the terms of *each* licence applicable to the specific packages present, including (where required) making modified source code available.

**Component Website:**
[https://www.alpinelinux.org/](https://www.alpinelinux.org/)

**Trademark Information:**
“Alpine” and the Alpine Linux logo are trademarks of the Alpine Linux Development Team. This declaration does **not** grant any trademark rights. Use of the mark must follow applicable law and must not imply endorsement, sponsorship, or affiliation without express permission. Nominative fair-use references such as “Loom runs on Alpine Linux” are generally acceptable.

**Source Code:**

* Official Git repositories: [https://git.alpinelinux.org/](https://git.alpinelinux.org/)
* Package source archives and licence metadata (SPDX-tagged): [https://pkgs.alpinelinux.org/](https://pkgs.alpinelinux.org/)
* Alpine-based container images (including Dockerfiles) are published at *docker.io/library/alpine*; the corresponding source for GPL-licensed components can be obtained via the above repositories or the `apk` package manager’s source fetching facilities (`apk fetch --source`).

By incorporating Alpine Linux, the Loom project acknowledges that the software is provided **“AS IS,”** without warranty, and accepts the responsibility for ongoing compliance with all applicable open-source licences.
