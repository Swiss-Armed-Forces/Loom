<!-- markdownlint-disable -->
Loom utilizes the Gotenberg document conversion API as a standalone Docker image.

**Software Licenses:**

The primary Gotenberg orchestration layer and API source code are licensed under the **MIT License**.

In addition, the official Gotenberg Docker image bundles and executes several independent third-party components, each governed by its own license. These components are executed as separate programs and are distributed as an aggregate within the container image:

- **Chromium** – BSD-3-Clause (and compatible permissive licenses for subcomponents)
- **LibreOffice** – Mozilla Public License v2.0 (MPL-2.0)
- **pdfcpu** – Apache License 2.0
- **qpdf** – Apache License 2.0
- **ExifTool** – Artistic License 1.0 (Perl) or GNU GPL v1.0 or later
- **PDFtk (pdftk-java)** – GNU General Public License v2.0 or later
- **Debian GNU/Linux base system** – Various free and open-source licenses, including GPL and LGPL

The MIT License grants broad rights to use, modify, and redistribute the Gotenberg source code, subject to the preservation of copyright and license notices.
The bundled components remain subject to their respective licenses. Strong or weak copyleft obligations (including those under the GPL and MPL) apply only to the respective components and do not extend to the Loom project, as the software is distributed and executed as an aggregate of separate programs.

**Component Website:**

https://gotenberg.dev/

**Trademark Information:**

“Gotenberg” is the name of an open-source software project maintained by Julien Neuhart. No registered trademark is claimed by the Loom project.
The name “Gotenberg” is used solely for nominative and descriptive purposes to identify the third-party software component.

All other trademarks referenced or included in the Gotenberg Docker image—including but not limited to Docker, Chromium, LibreOffice, Debian, and Microsoft Office—are the property of their respective owners. Their use does not imply endorsement, sponsorship, or affiliation with the Loom project.

**Source Code:**

Primary Gotenberg source repository:
https://github.com/gotenberg/gotenberg

Source code for bundled third-party components is available from their respective upstream projects and, where required by applicable licenses (including GPL-2.0-or-later), may be obtained from the corresponding public repositories or upon request, consistent with the terms of those licenses.
