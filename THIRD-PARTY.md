# Third Party Licenses
<!-- markdownlint-disable -->
This document serves to provide a comprehensive overview of all third-party software
components utilized in the development and operation of the "Loom" product.
Our intent is to maintain transparency and adhere strictly to the licensing terms
associated with each incorporated software package.

Within this file, you will find a detailed list of the open-source and proprietary
software libraries, frameworks, and tools that are integrated into Loom, along with
their respective licenses.

We are committed to respecting the intellectual property rights of others and ensuring
full compliance with all applicable license obligations.

Should you identify any instance of potential license infringement or trademark violation
related to the third-party software listed herein, we encourage you to promptly notify
the owners of "Loom" by opening a new issue via the following link:

* [Loom Issue Tracker](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/issues/new)

Your diligence in bringing such matters to our attention is greatly appreciated and will
enable us to take appropriate and timely action to rectify any concerns.

## Components


### ElasticSearch

<!-- markdownlint-disable -->
Loom utilizes **Elasticsearch** as a standalone Docker image.

**Software Licenses:**

Elasticsearch is distributed under a **tri-licensing model**, which currently includes:
- **Server Side Public License (SSPL) v1.0**
- **Elastic License v2.0 (ELv2)**
- **Affero General Public License (AGPL) v3**

Starting with version 7.11, Elastic introduced this tri-licensing model to govern Elasticsearch. The **default distribution** is offered under the Elastic License v2.0, which places notable restrictions on providing Elasticsearch as a **hosted or managed service**. The SSPL may also apply if Elasticsearch’s core functionalities are made accessible as a service to external users, potentially affecting the licensing requirements for the entire Loom project. Additionally, if Elasticsearch (or a modified version thereof) is provided over a network, the AGPLv3’s **network copyleft** provision could require making source code available under the AGPLv3.

These licensing terms may have **significant implications** for the Loom project’s integration, redistribution, and any potential managed-service offerings. Users are strongly advised to review the official license texts and consult legal counsel to ensure compliance with all relevant terms.

**Component Website:**
The official websites for Elasticsearch are:
- [www.elastic.co/products/elasticsearch](https://www.elastic.co/products/elasticsearch)
- [www.elastic.co/elasticsearch/](https://www.elastic.co/elasticsearch/)

These sites provide comprehensive documentation, licensing details, and additional resources. The main corporate website for Elastic is [www.elastic.co](https://www.elastic.co), where the complete legal texts for the SSPL, Elastic License v2.0, and AGPLv3 are available.

**Trademark Information:**

**"Elasticsearch"** is a registered trademark owned by Elastic N.V. and its subsidiaries. Use of the term “Elasticsearch” within the Loom project (including documentation or public-facing materials) must comply with all applicable trademark laws and any specific guidelines issued by Elastic N.V. Improper or unauthorized use of registered trademarks can result in legal consequences. Loom hereby acknowledges the ownership and validity of the “Elasticsearch” trademark and disclaims any affiliation or endorsement by Elastic N.V. unless expressly stated.

**Source Code:**
The Elasticsearch source code, subject to the tri-licensing model described above, can be obtained from official Elastic repositories and platforms linked on the Elastic website. Individuals or organizations seeking to modify or redistribute Elasticsearch must ensure they adhere to the corresponding license terms:
- **Server Side Public License (SSPL) v1.0**
- **Elastic License v2.0**
- **Affero General Public License (AGPL) v3**

Any party incorporating Elasticsearch into their workflow is responsible for **reviewing, understanding, and complying** with all licensing requirements. This includes potential obligations to disclose source code when offering network-accessible modifications under the AGPLv3 and observing the prohibitions on providing Elasticsearch as a managed service under the Elastic License v2.0.


### Grafana

<!-- markdownlint-disable -->
Loom utilizes the Grafana component as a standalone Docker image.

**Software Licenses:**

Grafana is made available under the terms of the GNU Affero General Public License, version 3.0 (AGPLv3). This open-source license grants permission to use, inspect, share, and adapt Grafana. Notably, it imposes a requirement to release source code for any modifications, including situations where modified versions are deployed over a network.

The complete text of the AGPLv3 license is accessible within Grafana’s official repository:
[https://github.com/grafana/grafana/blob/main/LICENSE](https://github.com/grafana/grafana/blob/main/LICENSE)

**Component Website:**

Additional details, documentation, and resources for Grafana are available at the official Grafana website:
[https://grafana.com/](https://grafana.com/)

**Trademark Information:**

The name “Grafana” and associated logos are trademarks of Grafana Labs, governed by the [Grafana Labs Trademark Policy](https://grafana.com/legal/trademark-policy/). This policy specifies the appropriate use of Grafana’s marks, including requirements to:

- Refrain from altering Grafana’s logos or names;
- Obtain a separate trademark license for uses outside open-source discussions, development, or support; and
- Provide proper attribution when referencing Grafana’s trademarks.

For any inquiries or clarifications regarding permitted trademark uses, please contact Grafana Labs at hello@grafana.com.

**Source Code:**

The source code for Grafana is publicly available on GitHub:
[https://github.com/grafana/grafana](https://github.com/grafana/grafana)

This repository contains complete version histories, issue tracking, and guidance for contributions, reflecting Grafana’s open and transparent development practices.


### Prometheus

<!-- markdownlint-disable -->
Loom utilizes the Prometheus monitoring system as a standalone Docker image.

**Software Licenses:**
Prometheus is distributed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). This permissive open-source license allows commercial use, modification, distribution, and patent use, provided that certain obligations are met. In particular, Loom must include a copy of the Apache License 2.0 with any redistributed versions of Prometheus, retain all original copyright notices, and clearly indicate any modifications to the Prometheus codebase. If a `NOTICE` file is present in Prometheus, Loom will include those attribution notices as required by the license.

**Component Website:**
The official website for the Prometheus project is [https://prometheus.io/](https://prometheus.io/). This website provides authoritative information, documentation, and resources for the Prometheus software.

**Trademark Information:**
“Prometheus,” when referring to the open-source monitoring project, is a trademark owned by The Linux Foundation. Under the Apache License 2.0, Loom may use the Prometheus name solely to accurately identify the software’s origin. No implication of endorsement or affiliation with the Linux Foundation or the Prometheus project is intended or should be inferred beyond this necessary reference.

**Source Code:**
Prometheus source code is publicly available and can be accessed via the official repository on [GitHub](https://github.com/prometheus/prometheus). The Loom project includes Prometheus in its Docker images without introducing modifications to the core functionality unless explicitly stated. Loom includes or makes available the Apache License 2.0 and, if applicable, any required `NOTICE` file contents in accordance with the license terms.


### Rabbit

<!-- markdownlint-disable -->
Loom utilizes the RabbitMQ software component as a standalone Docker image.

**Software Licenses:**
RabbitMQ is distributed under a dual-licensing scheme, governed by the Mozilla Public License 2.0 (MPL-2.0) and the Apache License 2.0. You may choose either license based on your project needs.
- [MPL-2.0 License Text](https://github.com/rabbitmq/rabbitmq-server/blob/main/LICENSE-MPL-RabbitMQ)
- [Apache License 2.0 Text](https://www.apache.org/licenses/LICENSE-2.0)

**Component Website:**
The official RabbitMQ website, serving as the primary resource for documentation, downloads, community forums, and updates, is located at:
- [https://www.rabbitmq.com/](https://www.rabbitmq.com/)

**Trademark Information:**
RabbitMQ’s name and logo are protected by trademark guidelines. These guidelines, including permissible uses of the RabbitMQ marks, can be found via the official website. The copyright for the RabbitMQ website and documentation is held by Broadcom.

**Source Code:**
RabbitMQ’s source code is available on its [GitHub repository](https://github.com/rabbitmq). The repository includes license files, contributing guidelines, and instructions for building and deploying the software.


### Redis

<!-- markdownlint-disable -->
Loom utilizes the Redis software as a standalone Docker image.

**Software Licenses:**

Redis’s software license obligations depend on the specific version in use within the Loom project:

- **Older Versions (up to and including 7.2.4):** These versions are distributed under the 3-Clause BSD License.
- **Versions 7.4.x and Later (Community Edition):** Offered under a dual-licensing scheme: either the Redis Source Available License v2 (RSALv2) **or** the Server Side Public License v1 (SSPLv1).

For any chosen version, please refer to the relevant license terms to ensure compliance with the applicable obligations and permissions.

**Component Website:**

The official Redis website is located at [https://redis.io/](https://redis.io/). It serves as a central repository for documentation, community resources, and legal information, including the full text of applicable licenses.

**Trademark Information:**

The “Redis” name and associated logo are legally protected trademarks owned by Redis Ltd. Comprehensive guidelines governing the appropriate use of Redis trademarks can be found at [https://redis.com/legal/trademark-guidelines/](https://redis.com/legal/trademark-guidelines/).
In accordance with these guidelines, all references to “Redis” in Loom’s materials must:

- Use the trademark symbol (™) upon first mention.
- Include a clear legend, for example:
  > *Redis is a trademark of Redis Ltd. Any rights therein are reserved to Redis Ltd. Any use by Loom is for referential purposes only and does not indicate any sponsorship, endorsement or affiliation between Redis and Loom.*

Ensuring adherence to these guidelines is vital to avoid infringement and maintain a clear distinction between Loom and the official Redis project.

**Source Code:**

The Redis source code, including the full text of its licenses, is available on the official Redis GitHub repository at:
[https://github.com/redis/redis](https://github.com/redis/redis)
The license file can be found within that repository, specifically at:
[https://github.com/redis/redis/blob/unstable/LICENSE.txt](https://github.com/redis/redis/blob/unstable/LICENSE.txt)

Please review this file to confirm and fulfill all relevant licensing requirements when incorporating Redis within Loom.


### alpine

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


### dovecot

<!-- markdownlint-disable -->

Loom utilizes the Dovecot Community Edition as a standalone Docker image.

**Software Licenses:**

* **Majority of codebase:** GNU Lesser General Public License v2.1 (LGPLv2.1). For more details, please refer to the `COPYING` file in the Dovecot source code repository.
* **Specific directories (src/lib/, src/auth/, src/lib-sql/):** MIT License. The full text of this license can be found in the `COPYING.MIT` file in the Dovecot source code repository.
* **Specific files:**
  * `src/lib/md5.c`: Public Domain.
  * `src/lib/sha1.c`, `sha2.c`: WIDE Project license with a copyright notice from Olivier Gay. Refer to the beginning of these files in the Dovecot source code for the specific terms.
  * `src/lib/UnicodeData.txt`: Unicode License. Details available at [http://www.unicode.org/copyright.html](http://www.unicode.org/copyright.html).

**Component Website:** <https://www.dovecot.org>

**Trademark Information:**

* The Dovecot project asserts copyright over the name "Dovecot" as indicated on their website.
* An unrelated entity, Dovecot Studios, also identifies "Dovecot" as a proprietary mark in the art gallery sector.
* The trademark status of the "Dovecot" software project in specific jurisdictions like the US and EU requires further investigation through official trademark databases.

**Source Code:** <https://github.com/dovecot/core>


### elasticvue

<!-- markdownlint-disable -->
Loom utilizes the “Elasticvue” software as a standalone Docker image.

**Software Licenses:**
The “Elasticvue” component is distributed under the terms of the MIT License. This permissive license grants you broad rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, provided that the relevant copyright and permission notices are retained. The full text of the MIT License is available at:
[https://github.com/cars10/elasticvue/blob/master/LICENSE](https://github.com/cars10/elasticvue/blob/master/LICENSE)

**Component Website:**
The official website for “Elasticvue” is: [https://elasticvue.com/](https://elasticvue.com/). This website provides comprehensive information about the project’s features, documentation, and deployment methods.

**Trademark Information:**
“Elasticsearch” is a registered trademark of Elasticsearch BV in the United States and other countries. Although “Elasticvue” was developed to interface with Elasticsearch, it remains an independent project and is not affiliated with Elasticsearch BV. Any reference to “Elastic” within the “Elasticvue” name does not imply an endorsement or sponsorship by Elasticsearch BV. This license declaration does not grant any rights or licenses to use the “Elasticsearch” trademark.

**Source Code:**
The source code for “Elasticvue” can be found at: [https://github.com/cars10/elasticvue](https://github.com/cars10/elasticvue). This repository includes documentation, issue tracking (including trademark discussions and considerations), and the latest updates for the project.


### gotenberg

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


### kube-state-metrics

<!-- markdownlint-disable -->
Loom utilizes the kube-state-metrics as a standalone Docker image.

**Software Licenses:**
Apache License, Version 2.0 (Apache-2.0).
Copyright © 2016–Present The Kubernetes Authors.

The kube-state-metrics project is licensed under the Apache License 2.0, a permissive open-source license that grants the rights to use, reproduce, distribute, and prepare derivative works of the software in both Source and Object forms, subject to the conditions defined in the license.

The Loom project distributes kube-state-metrics in unmodified Object form as a standalone Docker image. In accordance with Section 4 of the Apache License 2.0, all applicable copyright, patent, attribution, and license notices are preserved. If a NOTICE file is included with the upstream project, its attribution notices are retained within the Loom third-party notices documentation.

The software is provided “AS IS”, without warranties or conditions of any kind, either express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, and non-infringement, as described in the Apache License 2.0.

**Component Website:**
https://github.com/kubernetes/kube-state-metrics

**Trademark Information:**
“Kubernetes®” is a registered trademark of The Linux Foundation in the United States and other countries.
“CNCF®” is a registered trademark of the Cloud Native Computing Foundation.
“Linux®” is a registered trademark of Linus Torvalds.

The Loom project references these trademarks solely for nominative and descriptive purposes to identify compatibility with the Kubernetes ecosystem. Such references do not imply endorsement, sponsorship, or affiliation with The Linux Foundation, the Cloud Native Computing Foundation, or the Kubernetes project.

**Source Code:**
https://github.com/kubernetes/kube-state-metrics


### ollama

<!-- markdownlint-disable -->
Loom utilizes the **Ollama** software as a standalone Docker image.

**Software Licenses:**
Ollama is distributed under the [MIT License](https://github.com/ollama/ollama/blob/main/LICENSE). This permissive open-source license grants broad rights to use, modify, and distribute the software, provided that the original copyright notice and permission notice remain intact.

**Component Website:**
Ollama’s official website is [https://ollama.com/](https://ollama.com/). It hosts detailed documentation, installation resources, and additional information regarding the Ollama project.

**Trademark Information:**
“Ollama” is likely a trademark of Ollama Inc. based on the notice “© 2025 Ollama Inc.” presented in various sources. Loom respects these trademark rights and does not imply endorsement or sponsorship by Ollama Inc. unless explicitly stated.

**Source Code:**
The Ollama source code is publicly available at the following GitHub repository: [https://github.com/ollama/ollama](https://github.com/ollama/ollama). Interested users may review the repository for updates, contributions, and further technical details.


### open-webui

<!-- markdownlint-disable -->
Loom utilizes the Open WebUI software as a standalone Docker image.

**Software Licenses:**
Open WebUI is presented under permissive open-source licenses. However, there is a noted discrepancy:
- The project's GitHub repository (https://github.com/open-webui/open-webui) references a BSD-3-Clause License.
- The project's PyPI page (https://pypi.org/project/open-webui/) states it is licensed under the MIT License.

Both the MIT License and the BSD-3-Clause License grant broad permissions to copy, modify, and distribute the software while disavowing warranties and liabilities.

**Component Website:**
The official website for Open WebUI is located at [https://openwebui.com/](https://openwebui.com/). This site provides additional information about the project’s features, documentation, and community resources.

**Trademark Information:**
Based on the available information, there are no confirmed or registered trademarks explicitly associated with "Open WebUI." In open-source contexts, trademark rights are separate from copyrights and patents. If you plan to use Open WebUI’s name or branding in a manner that might suggest endorsement or affiliation, conducting an independent trademark search is advisable to avoid potential infringement concerns.

**Source Code:**
Open WebUI’s primary development occurs on GitHub at [https://github.com/open-webui/open-webui](https://github.com/open-webui/open-webui). The GitHub repository includes the project’s core source code, licensing files, issue tracker, and additional technical documentation.


### roundcube

<!-- markdownlint-disable -->
Loom utilizes the Roundcube webmail software as a standalone Docker image.

**Software Licenses:**
Roundcube is distributed under the GNU General Public License Version 3 or later (GPLv3+). This license grants you the rights to run, study, share, and modify the software. Roundcube’s licensing structure also permits skins and plugins that merely make function calls to the Roundcube Webmail software and include it by reference without constituting a modification of the core software. When distributing any adaptations or modifications of Roundcube, you are responsible for preserving copyright notices, license notices, and providing access to the source code in compliance with GPLv3+.

**Component Website:**
The primary source of official information for Roundcube, including features, documentation, and news, is located at [https://roundcube.net/](https://roundcube.net/).

**Trademark Information:**
Available information does not confirm a registered trademark for the name “Roundcube.” Although discussions reference a “Roundcube Logo,” no definitive registration has been verified. If you plan to use the Roundcube name or associated logo, you should consider a diligent review of relevant trademark databases or consult legal counsel to ensure compliance with any applicable trademark rights.

**Source Code:**
The Roundcube source code is publicly available on GitHub at [https://github.com/roundcube/roundcubemail](https://github.com/roundcube/roundcubemail). This repository enables transparency, collaboration, and the opportunity to adapt Roundcube to specific needs within the Loom project.


### rspamd

<!-- markdownlint-disable -->
Loom utilizes **Rspamd** as a standalone Docker image.

**Software Licenses:**

- **Core Rspamd Software:**
  Rspamd is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). This license permits broad use, modification, and distribution, subject to requirements such as retaining copyright notices, including a copy of the license with redistributions, and clearly indicating any modifications.

- **Docker Image (Language Model):**
  The official Docker image for Rspamd includes a language identification model powered by fasttext, which is licensed under the [Creative Commons Attribution-Share-Alike 3.0 Unported License](https://creativecommons.org/licenses/by-sa/3.0/legalcode). Users must comply with the attribution and share-alike requirements specified therein.

Please be advised that Loom adheres to both licenses where applicable. The Apache License 2.0 includes a disclaimer of warranties and a limitation of liability, while the Creative Commons Attribution-Share-Alike 3.0 License imposes distinct obligations concerning attribution and licensing of derivative works.

**Component Website:**

The official website for Rspamd is [https://rspamd.com/](https://rspamd.com/). It provides documentation, downloads, and further details regarding Rspamd’s features.

**Trademark Information:**

Based on publicly available information at the time of review, no explicit registration or trademark notice for “Rspamd” was found on the official website. If you require definitive confirmation of trademark status, please consult the relevant trademark registries.

**Source Code:**

The Rspamd source code is available through its [GitHub repository](https://github.com/rspamd/rspamd). Interested parties are encouraged to review the repository for additional licensing details and updates.

This declaration reflects the information accessible at the time of writing. Users of the “Loom” project are responsible for verifying any updates to Rspamd’s licensing terms or trademark status to ensure continuous compliance with applicable legal requirements.


### seaweedfs

<!-- markdownlint-disable -->

Loom utilizes the SeaweedFS as a standalone Docker image.

**Software Licenses:**
SeaweedFS is subject to a dual-licensing model:

1. **Community Edition – Apache License, Version 2.0**
    - Copyright © 2016–2026 Chris Lu and contributors.
    - Licensed under the Apache License, Version 2.0.
    - This license grants a perpetual, worldwide, non-exclusive, no-charge, royalty-free, and irrevocable copyright and patent license.
    - Redistribution in Docker image form requires inclusion of the license text and preservation of all copyright, patent, and attribution notices.
    - The software is provided on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

2. **Enterprise Edition – Seaweed Data End User License Agreement (EULA)**
    - Applicable when deployment exceeds 25TB of managed storage or when enterprise features are used.
    - Publisher: Seaweed Data.
    - Free usage permitted below 25TB; above this threshold requires a commercial license.
    - Includes additional restrictions, including limitations on reverse engineering and certain hosting or resale scenarios.
    - May impose indemnification obligations on the user.

**Component Website:**
- https://seaweedfs.com

**Trademark Information:**
- “SeaweedFS” is a trademark of its respective owners.
- All references to the name are for descriptive purposes only and do not imply endorsement, affiliation, or sponsorship.
- Loom does not claim any rights to the SeaweedFS trademarks and uses them in accordance with the Apache License 2.0 trademark limitations.
- When applicable, Docker images or distributions (e.g., Bitnami builds) may include additional trademarks and copyrights owned by their respective providers (e.g., Broadcom Inc.).

**Source Code:**
- https://github.com/seaweedfs/seaweedfs


### tika-server

<!-- markdownlint-disable -->
Loom utilizes Apache Tika as a standalone Docker image.

**Software Licenses:**

Apache Tika is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). This permissive license allows extensive rights to use, modify, and distribute the software, including for both commercial and non-commercial purposes, subject to compliance with its requirements (such as attribution). Apache Tika may also include subcomponents governed by separate licenses, typically detailed in its `LICENSE.txt` file. Users of Loom should review all applicable licenses to ensure full compliance.

**Component Website:**

The official website for Apache Tika is [https://tika.apache.org/](https://tika.apache.org/). This site provides comprehensive documentation, release information, and community resources. It is the primary source for updates and clarifications regarding Apache Tika.

**Trademark Information:**

Apache Tika, Tika, Apache, the Apache feather logo, and the Apache Tika project logo are trademarks of The Apache Software Foundation. They are protected by the ASF’s trademark policy, available at [https://www.apache.org/foundation/marks/](https://www.apache.org/foundation/marks/). Loom acknowledges these trademarks and complies with the ASF’s guidelines. Any use of these marks by Loom or its documentation should avoid implying endorsement or sponsorship by the ASF, unless explicitly permitted.

**Source Code:**

The Apache Tika source code can be found on its official website and associated repositories. It is strongly recommended that Loom contributors and users periodically review the applicable license texts and trademark policies, as changes or updates may occur. This third-party license declaration is provided for informational purposes only and does not constitute legal advice.


### traefik

<!-- markdownlint-disable -->
Loom utilizes the Traefik component as a standalone Docker image.

**Software Licenses:**
Traefik is distributed under the MIT License, a permissive open-source license originating from the Massachusetts Institute of Technology. This license grants extensive permissions for use, modification, distribution, and sublicensing. The primary condition is the requirement to include the original copyright notice and permission notice in all copies or substantial portions of Traefik. Failure to do so may violate the terms of the license.

**Component Website:**
The official website for Traefik is [https://traefik.io/](https://traefik.io/). This site hosts comprehensive documentation, community support, legal notices, and commercial information. Additional documentation can also be found at [https://doc.traefik.io/traefik/](https://doc.traefik.io/traefik/).

**Trademark Information:**
The name “Traefik” is claimed as a trademark by Traefik Labs pursuant to their End User License Agreement, which reserves all rights to the software, including any related trademarks or patents. For definitive information about the trademark status, refer to the legal sections of [https://traefik.io/](https://traefik.io/) and consult relevant trademark databases.

**Source Code:**
The complete source code for Traefik is publicly available at [https://github.com/traefik/traefik](https://github.com/traefik/traefik), which also includes the full text of the MIT License. If distributing Traefik within your own software, ensure that you adhere to the license requirements by including all required notices and disclaimers.


## Python

| Name                                  | Version         | License                                                                          |
|---------------------------------------|-----------------|----------------------------------------------------------------------------------|
| multidict                             | 6.7.1           | Apache License 2.0                                                               |
| aiosignal                             | 1.4.0           | Apache Software License                                                          |
| distro                                | 1.9.0           | Apache Software License                                                          |
| elastic-transport                     | 9.4.0           | Apache Software License                                                          |
| kubernetes                            | 36.0.3          | Apache Software License                                                          |
| memray                                | 1.19.3          | Apache Software License                                                          |
| minio                                 | 7.2.20          | Apache Software License                                                          |
| openai                                | 1.72.0          | Apache Software License                                                          |
| propcache                             | 0.5.2           | Apache Software License                                                          |
| pytest_docker_tools                   | 3.1.9           | Apache Software License                                                          |
| requests                              | 2.32.5          | Apache Software License                                                          |
| requests-toolbelt                     | 1.0.0           | Apache Software License                                                          |
| requirements-parser                   | 0.13.0          | Apache Software License                                                          |
| tenacity                              | 9.1.4           | Apache Software License                                                          |
| tornado                               | 6.5.5           | Apache Software License                                                          |
| types-pyOpenSSL                       | 24.1.0.20240722 | Apache Software License                                                          |
| types-redis                           | 4.6.0.20241004  | Apache Software License                                                          |
| watchdog                              | 6.0.0           | Apache Software License                                                          |
| websocket-client                      | 1.9.0           | Apache Software License                                                          |
| python-dateutil                       | 2.9.0.post0     | Apache Software License; BSD License                                             |
| luqum                                 | 0.14.0          | Apache Software License; GNU Lesser General Public License v3 or later (LGPLv3+) |
| sniffio                               | 1.3.1           | Apache Software License; MIT License                                             |
| celery-types                          | 0.24.0          | Apache-2.0                                                                       |
| coverage                              | 7.14.0          | Apache-2.0                                                                       |
| docker                                | 7.1.0           | Apache-2.0                                                                       |
| elasticsearch                         | 9.2.1           | Apache-2.0                                                                       |
| freezegun                             | 1.5.5           | Apache-2.0                                                                       |
| frozenlist                            | 1.8.0           | Apache-2.0                                                                       |
| importlib_metadata                    | 8.7.1           | Apache-2.0                                                                       |
| opentelemetry-api                     | 1.39.1          | Apache-2.0                                                                       |
| opentelemetry-exporter-prometheus     | 0.60b1          | Apache-2.0                                                                       |
| opentelemetry-instrumentation         | 0.60b1          | Apache-2.0                                                                       |
| opentelemetry-instrumentation-asgi    | 0.60b1          | Apache-2.0                                                                       |
| opentelemetry-instrumentation-fastapi | 0.60b1          | Apache-2.0                                                                       |
| opentelemetry-sdk                     | 1.39.1          | Apache-2.0                                                                       |
| opentelemetry-semantic-conventions    | 0.60b1          | Apache-2.0                                                                       |
| opentelemetry-util-http               | 0.60b1          | Apache-2.0                                                                       |
| pytest-asyncio                        | 1.4.0           | Apache-2.0                                                                       |
| pytest-memray                         | 1.8.0           | Apache-2.0                                                                       |
| python-multipart                      | 0.0.32          | Apache-2.0                                                                       |
| types-cffi                            | 2.0.0.20260518  | Apache-2.0                                                                       |
| types-docker                          | 7.1.0.20260512  | Apache-2.0                                                                       |
| types-paramiko                        | 4.0.0.20260508  | Apache-2.0                                                                       |
| types-requests                        | 2.32.4.20260324 | Apache-2.0                                                                       |
| types-setuptools                      | 82.0.0.20260518 | Apache-2.0                                                                       |
| tzdata                                | 2026.2          | Apache-2.0                                                                       |
| yarl                                  | 1.24.2          | Apache-2.0                                                                       |
| prometheus_client                     | 0.24.1          | Apache-2.0 AND BSD-2-Clause                                                      |
| aiohttp                               | 3.14.1          | Apache-2.0 AND MIT                                                               |
| packaging                             | 26.2            | Apache-2.0 OR BSD-2-Clause                                                       |
| cryptography                          | 48.0.0          | Apache-2.0 OR BSD-3-Clause                                                       |
| ply                                   | 3.11            | BSD                                                                              |
| IMAPClient                            | 3.1.0           | BSD License                                                                      |
| Jinja2                                | 3.1.6           | BSD License                                                                      |
| amqp                                  | 5.3.1           | BSD License                                                                      |
| asgiref                               | 3.11.1          | BSD License                                                                      |
| billiard                              | 4.2.4           | BSD License                                                                      |
| click-plugins                         | 1.1.1.2         | BSD License                                                                      |
| dill                                  | 0.4.1           | BSD License                                                                      |
| flower                                | 2.0.1           | BSD License                                                                      |
| gitdb                                 | 4.0.12          | BSD License                                                                      |
| httpx                                 | 0.28.1          | BSD License                                                                      |
| jsonpatch                             | 1.33            | BSD License                                                                      |
| jsonpointer                           | 3.1.1           | BSD License                                                                      |
| pika                                  | 1.4.1           | BSD License                                                                      |
| prompt_toolkit                        | 3.0.52          | BSD License                                                                      |
| pytest-celery                         | 1.3.0           | BSD License                                                                      |
| requests-oauthlib                     | 2.0.0           | BSD License                                                                      |
| scipy                                 | 1.17.1          | BSD License                                                                      |
| smmap                                 | 5.0.3           | BSD License                                                                      |
| threadpoolctl                         | 3.6.0           | BSD License                                                                      |
| vine                                  | 5.1.0           | BSD License                                                                      |
| websockets                            | 13.1            | BSD License                                                                      |
| wrapt                                 | 1.17.3          | BSD License                                                                      |
| xxhash                                | 3.7.0           | BSD License                                                                      |
| pycryptodome                          | 3.23.0          | BSD License; Public Domain                                                       |
| Pygments                              | 2.20.0          | BSD-2-Clause                                                                     |
| GitPython                             | 3.1.50          | BSD-3-Clause                                                                     |
| MarkupSafe                            | 3.0.3           | BSD-3-Clause                                                                     |
| celery                                | 5.6.3           | BSD-3-Clause                                                                     |
| click                                 | 8.3.3           | BSD-3-Clause                                                                     |
| httpcore                              | 1.0.9           | BSD-3-Clause                                                                     |
| idna                                  | 3.15            | BSD-3-Clause                                                                     |
| joblib                                | 1.5.3           | BSD-3-Clause                                                                     |
| kombu                                 | 5.6.2           | BSD-3-Clause                                                                     |
| oauthlib                              | 3.3.1           | BSD-3-Clause                                                                     |
| psutil                                | 7.2.2           | BSD-3-Clause                                                                     |
| pycparser                             | 3.0             | BSD-3-Clause                                                                     |
| python-dotenv                         | 1.2.2           | BSD-3-Clause                                                                     |
| scikit-learn                          | 1.8.0           | BSD-3-Clause                                                                     |
| starlette                             | 0.52.1          | BSD-3-Clause                                                                     |
| uuid_utils                            | 0.15.0          | BSD-3-Clause                                                                     |
| uvicorn                               | 0.40.0          | BSD-3-Clause                                                                     |
| zstandard                             | 0.25.0          | BSD-3-Clause                                                                     |
| numpy                                 | 2.4.4           | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0                               |
| pytest-timeout                        | 2.4.0           | DFSG approved; MIT License                                                       |
| pylint-plugin-utils                   | 0.9.0           | GNU General Public License v2 or later (GPLv2+)                                  |
| python-gitlab                         | 8.4.0           | GNU Lesser General Public License v3 (LGPLv3)                                    |
| pylint                                | 4.0.6           | GPL-2.0-or-later                                                                 |
| pylint-pydantic                       | 0.4.1           | GPLv3                                                                            |
| astroid                               | 4.0.4           | LGPL-2.1-or-later                                                                |
| annotated-doc                         | 0.0.4           | MIT                                                                              |
| anyio                                 | 4.13.0          | MIT                                                                              |
| argon2-cffi                           | 25.1.0          | MIT                                                                              |
| argon2-cffi-bindings                  | 25.1.0          | MIT                                                                              |
| attrs                                 | 26.1.0          | MIT                                                                              |
| autoflake                             | 2.3.3           | MIT                                                                              |
| black                                 | 26.5.1          | MIT                                                                              |
| cffi                                  | 2.0.0           | MIT                                                                              |
| charset-normalizer                    | 3.4.7           | MIT                                                                              |
| click-repl                            | 0.3.0           | MIT                                                                              |
| deptry                                | 0.25.1          | MIT                                                                              |
| durationpy                            | 0.10            | MIT                                                                              |
| fastapi                               | 0.128.8         | MIT                                                                              |
| humanize                              | 4.15.0          | MIT                                                                              |
| identify                              | 2.6.19          | MIT                                                                              |
| iniconfig                             | 2.3.0           | MIT                                                                              |
| isort                                 | 8.0.1           | MIT                                                                              |
| jiter                                 | 0.14.0          | MIT                                                                              |
| langsmith                             | 0.8.3           | MIT                                                                              |
| librt                                 | 0.11.0          | MIT                                                                              |
| mypy                                  | 1.20.2          | MIT                                                                              |
| mypy_extensions                       | 1.1.0           | MIT                                                                              |
| platformdirs                          | 4.9.6           | MIT                                                                              |
| pycodestyle                           | 2.14.0          | MIT                                                                              |
| pydantic                              | 2.13.4          | MIT                                                                              |
| pydantic-settings                     | 2.14.2          | MIT                                                                              |
| pydantic_core                         | 2.46.4          | MIT                                                                              |
| pytest                                | 9.0.3           | MIT                                                                              |
| pytest-cov                            | 7.1.0           | MIT                                                                              |
| tomli                                 | 2.4.1           | MIT                                                                              |
| typing-inspection                     | 0.4.2           | MIT                                                                              |
| tzlocal                               | 5.4             | MIT                                                                              |
| urllib3                               | 2.7.0           | MIT                                                                              |
| zipp                                  | 3.23.1          | MIT                                                                              |
| PyYAML                                | 6.0.3           | MIT License                                                                      |
| Wand                                  | 0.6.13          | MIT License                                                                      |
| aitools                               | 0.1.0           | MIT License                                                                      |
| annotated-types                       | 0.7.0           | MIT License                                                                      |
| api                                   | 0.1.0           | MIT License                                                                      |
| click-didyoumean                      | 0.3.1           | MIT License                                                                      |
| common                                | 0.1.0           | MIT License                                                                      |
| crawler                               | 0.1.0           | MIT License                                                                      |
| debugpy                               | 1.8.20          | MIT License                                                                      |
| flake8                                | 7.3.0           | MIT License                                                                      |
| flake8-bugbear                        | 25.11.29        | MIT License                                                                      |
| h11                                   | 0.16.0          | MIT License                                                                      |
| h2                                    | 4.3.0           | MIT License                                                                      |
| hpack                                 | 4.1.0           | MIT License                                                                      |
| hyperframe                            | 6.1.0           | MIT License                                                                      |
| integrationtest                       | 0.1.0           | MIT License                                                                      |
| langchain-core                        | 1.4.0           | MIT License                                                                      |
| langchain-protocol                    | 0.0.15          | MIT License                                                                      |
| langchain-text-splitters              | 1.1.2           | MIT License                                                                      |
| linkify-it-py                         | 2.1.0           | MIT License                                                                      |
| markdown-it-py                        | 4.2.0           | MIT License                                                                      |
| mccabe                                | 0.7.0           | MIT License                                                                      |
| mdit-py-plugins                       | 0.6.1           | MIT License                                                                      |
| mdurl                                 | 0.1.2           | MIT License                                                                      |
| pluggy                                | 1.6.0           | MIT License                                                                      |
| pyflakes                              | 3.4.0           | MIT License                                                                      |
| pytest-mock                           | 3.15.1          | MIT License                                                                      |
| pytest-random-order                   | 1.2.0           | MIT License                                                                      |
| pytest-split                          | 0.11.0          | MIT License                                                                      |
| python-magic                          | 0.4.27          | MIT License                                                                      |
| pytokens                              | 0.4.1           | MIT License                                                                      |
| pytz                                  | 2026.2          | MIT License                                                                      |
| redis                                 | 5.2.1           | MIT License                                                                      |
| rich                                  | 15.0.0          | MIT License                                                                      |
| six                                   | 1.17.0          | MIT License                                                                      |
| textual                               | 8.2.6           | MIT License                                                                      |
| tomlkit                               | 0.15.0          | MIT License                                                                      |
| uc-micro-py                           | 2.0.0           | MIT License                                                                      |
| worker                                | 0.1.0           | MIT License                                                                      |
| docformatter                          | 1.7.8           | MIT License; Other/Proprietary License                                           |
| gotenberg-client                      | 0.13.1          | MPL-2.0                                                                          |
| pytest-rerunfailures                  | 15.1            | MPL-2.0                                                                          |
| orjson                                | 3.11.9          | MPL-2.0 AND (Apache-2.0 OR MIT)                                                  |
| tqdm                                  | 4.67.3          | MPL-2.0 AND MIT                                                                  |
| certifi                               | 2026.4.22       | Mozilla Public License 2.0 (MPL 2.0)                                             |
| pathspec                              | 1.1.1           | Mozilla Public License 2.0 (MPL 2.0)                                             |
| typing_extensions                     | 4.15.0          | PSF-2.0                                                                          |
| aiohappyeyeballs                      | 2.7.1           | Python Software Foundation License                                               |

## JavaScript

| Name                                | License type | Installed version |
| :---------------------------------- | :----------- | :---------------- |
| @emotion/styled                     | MIT          | 11.14.1           |
| @mui/icons-material                 | MIT          | 9.0.0             |
| @mui/material                       | MIT          | 9.0.0             |
| @mui/x-charts                       | MIT          | 9.1.0             |
| @mui/x-tree-view                    | MIT          | 9.1.0             |
| @reduxjs/toolkit                    | MIT          | 2.11.2            |
| ace-builds                          | BSD-3-Clause | 1.44.0            |
| ajv                                 | MIT          | 8.20.0            |
| date-fns                            | MIT          | 4.1.0             |
| eslint-plugin-import                | MIT          | 2.32.0            |
| i18next                             | MIT          | 26.1.0            |
| i18next-http-backend                | MIT          | 3.0.5             |
| react                               | MIT          | 19.2.5            |
| react-ace                           | MIT          | 14.0.1            |
| react-dom                           | MIT          | 19.2.5            |
| react-dropzone                      | MIT          | 15.0.0            |
| react-i18next                       | MIT          | 17.0.4            |
| react-intersection-observer         | MIT          | 10.0.3            |
| react-pdf                           | MIT          | 10.4.1            |
| react-redux                         | MIT          | 9.2.0             |
| react-router-dom                    | MIT          | 7.15.0            |
| react-toastify                      | MIT          | 11.1.0            |
| uuid                                | MIT          | 14.0.0            |
| @eslint/js                          | MIT          | 9.39.4            |
| @mui/types                          | MIT          | 9.0.0             |
| @openapitools/openapi-generator-cli | Apache-2.0   | 2.32.0            |
| @testing-library/jest-dom           | MIT          | 6.9.1             |
| @testing-library/react              | MIT          | 16.3.2            |
| @types/node                         | MIT          | 25.6.0            |
| @types/react                        | MIT          | 19.2.14           |
| @types/react-dom                    | MIT          | 19.2.3            |
| @typescript-eslint/eslint-plugin    | MIT          | 8.59.0            |
| @typescript-eslint/parser           | MIT          | 8.59.0            |
| @vitejs/plugin-react                | MIT          | 6.0.1             |
| eslint                              | MIT          | 9.39.4            |
| eslint-config-prettier              | MIT          | 10.1.8            |
| eslint-import-resolver-typescript   | ISC          | 4.4.4             |
| eslint-plugin-prettier              | MIT          | 5.5.5             |
| eslint-plugin-react                 | MIT          | 7.37.5            |
| eslint-plugin-react-hooks           | MIT          | 7.1.1             |
| eslint-plugin-react-refresh         | MIT          | 0.5.2             |
| eslint-plugin-unused-imports        | MIT          | 4.4.1             |
| globals                             | MIT          | 17.6.0            |
| jsdom                               | MIT          | 29.1.1            |
| license-report                      | MIT          | 6.8.2             |
| msw                                 | MIT          | 2.15.0            |
| prettier                            | MIT          | 3.8.3             |
| typescript                          | Apache-2.0   | 6.0.3             |
| typescript-eslint                   | MIT          | 8.59.0            |
| vite                                | MIT          | 8.0.9             |
| vite-plugin-static-copy             | MIT          | 4.1.0             |
| vite-plugin-svgr                    | MIT          | 5.2.0             |
| vitest                              | MIT          | 4.1.4             |


## Container


### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/traefik

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.6-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.23.4-r0 | MIT | apk-db-cataloger |
| apk-tools | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| busybox | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates | 20260413-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20260413-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| cloud.google.com/go/auth | v0.20.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.8 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.9.0 |  | go-module-binary-cataloger |
| github.com/AdamSLevy/jsonrpc2/v14 | v14.1.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go | v68.0.0+incompatible |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.21.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.13.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.12.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/dns/armdns | v1.2.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/privatedns/armprivatedns | v1.3.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/resourcegraph/armresourcegraph | v0.9.0 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest | v0.11.30 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/adal | v0.9.22 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/azure/auth | v0.5.13 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/azure/cli | v0.4.6 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/date | v0.3.0 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/to | v0.4.1 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/logger | v0.2.1 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/tracing | v0.6.0 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.6.0 |  | go-module-binary-cataloger |
| github.com/BurntSushi/toml | v1.6.0 |  | go-module-binary-cataloger |
| github.com/HdrHistogram/hdrhistogram-go | v1.2.0 |  | go-module-binary-cataloger |
| github.com/Masterminds/goutils | v1.1.1 |  | go-module-binary-cataloger |
| github.com/Masterminds/semver/v3 | v3.3.1 |  | go-module-binary-cataloger |
| github.com/Masterminds/sprig/v3 | v3.2.3 |  | go-module-binary-cataloger |
| github.com/VividCortex/gohistogram | v1.0.0 |  | go-module-binary-cataloger |
| github.com/akamai/AkamaiOPEN-edgegrid-golang/v13 | v13.1.0 |  | go-module-binary-cataloger |
| github.com/alibabacloud-go/alibabacloud-gateway-spi | v0.0.5 |  | go-module-binary-cataloger |
| github.com/alibabacloud-go/darabonba-openapi/v2 | v2.1.16 |  | go-module-binary-cataloger |
| github.com/alibabacloud-go/debug | v1.0.1 |  | go-module-binary-cataloger |
| github.com/alibabacloud-go/tea | v1.4.0 |  | go-module-binary-cataloger |
| github.com/alibabacloud-go/tea-utils/v2 | v2.0.9 |  | go-module-binary-cataloger |
| github.com/aliyun/credentials-go | v1.4.7 |  | go-module-binary-cataloger |
| github.com/andybalholm/brotli | v1.2.0 |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.41.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.16 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.15 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.22 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.22 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.22 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/v4a | v1.4.23 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ec2 | v1.203.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ecs | v1.53.15 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.8 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.22 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/lightsail | v1.53.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/route53 | v1.62.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.10 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssm | v1.56.13 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.16 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.35.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.42.0 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.25.0 |  | go-module-binary-cataloger |
| github.com/aziontech/azionapi-go-sdk | v0.144.0 |  | go-module-binary-cataloger |
| github.com/baidubce/bce-sdk-go | v0.9.265 |  | go-module-binary-cataloger |
| github.com/benbjohnson/clock | v1.3.5 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/bodgit/tsig | v1.2.2 |  | go-module-binary-cataloger |
| github.com/boombuler/barcode | v1.0.1 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/clbanning/mxj/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/containerd/errdefs | v1.0.0 |  | go-module-binary-cataloger |
| github.com/containerd/errdefs/pkg | v0.3.0 |  | go-module-binary-cataloger |
| github.com/containous/alice | v0.0.0-20181107144136-d83ebdd94cbd |  | go-module-binary-cataloger |
| github.com/containous/go-http-auth | v0.4.1-0.20200324110947-a37a7636d23e |  | go-module-binary-cataloger |
| github.com/containous/minheap | v0.0.0-20190809180810-6e71eb837595 |  | go-module-binary-cataloger |
| github.com/containous/mux | v0.0.0-20250523120546-41b6ec3aed59 |  | go-module-binary-cataloger |
| github.com/coreos/go-semver | v0.3.1 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.5.0 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/deepmap/oapi-codegen | v1.9.1 |  | go-module-binary-cataloger |
| github.com/desertbit/timer | v0.0.0-20180107155436-c41aec40b27f |  | go-module-binary-cataloger |
| github.com/dgryski/go-rendezvous | v0.0.0-20200823014737-9f7001d12a5f |  | go-module-binary-cataloger |
| github.com/dimchansky/utfbom | v1.1.1 |  | go-module-binary-cataloger |
| github.com/distribution/reference | v0.6.0 |  | go-module-binary-cataloger |
| github.com/dnsimple/dnsimple-go/v4 | v4.0.0 |  | go-module-binary-cataloger |
| github.com/docker/cli | v29.2.1+incompatible |  | go-module-binary-cataloger |
| github.com/docker/docker | v28.5.2+incompatible |  | go-module-binary-cataloger |
| github.com/docker/go-connections | v0.6.0 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.13.0 |  | go-module-binary-cataloger |
| github.com/evanphx/json-patch/v5 | v5.9.11 |  | go-module-binary-cataloger |
| github.com/exoscale/egoscale/v3 | v3.1.34 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/fatih/structs | v1.1.0 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.9.0 |  | go-module-binary-cataloger |
| github.com/gabriel-vasile/mimetype | v1.4.13 |  | go-module-binary-cataloger |
| github.com/ghodss/yaml | v1.0.0 |  | go-module-binary-cataloger |
| github.com/go-acme/alidns-20150109/v4 | v4.7.0 |  | go-module-binary-cataloger |
| github.com/go-acme/esa-20240910/v2 | v2.48.0 |  | go-module-binary-cataloger |
| github.com/go-acme/jdcloud-sdk-go | v1.64.0 |  | go-module-binary-cataloger |
| github.com/go-acme/lego/v4 | v4.35.2 |  | go-module-binary-cataloger |
| github.com/go-acme/tencentclouddnspod | v1.3.24 |  | go-module-binary-cataloger |
| github.com/go-acme/tencentedgdeone | v1.3.38 |  | go-module-binary-cataloger |
| github.com/go-errors/errors | v1.0.1 |  | go-module-binary-cataloger |
| github.com/go-jose/go-jose/v4 | v4.1.4 |  | go-module-binary-cataloger |
| github.com/go-kit/kit | v0.13.0 |  | go-module-binary-cataloger |
| github.com/go-kit/log | v0.2.1 |  | go-module-binary-cataloger |
| github.com/go-logfmt/logfmt | v0.5.1 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.21.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.23.1 |  | go-module-binary-cataloger |
| github.com/go-ozzo/ozzo-validation/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/go-playground/locales | v0.14.1 |  | go-module-binary-cataloger |
| github.com/go-playground/universal-translator | v0.18.1 |  | go-module-binary-cataloger |
| github.com/go-playground/validator/v10 | v10.23.0 |  | go-module-binary-cataloger |
| github.com/go-resty/resty/v2 | v2.17.2 |  | go-module-binary-cataloger |
| github.com/go-viper/mapstructure/v2 | v2.5.0 |  | go-module-binary-cataloger |
| github.com/go-zookeeper/zk | v1.0.3 |  | go-module-binary-cataloger |
| github.com/goccy/go-yaml | v1.19.2 |  | go-module-binary-cataloger |
| github.com/gofrs/flock | v0.13.0 |  | go-module-binary-cataloger |
| github.com/gofrs/uuid | v4.4.0+incompatible |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v4 | v4.5.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.3.1 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-github/v28 | v28.1.1 |  | go-module-binary-cataloger |
| github.com/google/go-querystring | v1.2.0 |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.9 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.14 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.21.0 |  | go-module-binary-cataloger |
| github.com/gophercloud/gophercloud | v1.14.1 |  | go-module-binary-cataloger |
| github.com/gophercloud/utils | v0.0.0-20231010081019-80377eca5d56 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.4-0.20250319132907-e064f32e3674 |  | go-module-binary-cataloger |
| github.com/gravitational/trace | v1.5.1 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.28.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/consul/api | v1.26.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/cronexpr | v1.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-immutable-radix | v1.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.8 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-uuid | v1.0.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-version | v1.9.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/hcl | v1.0.1-vault-5 |  | go-module-binary-cataloger |
| github.com/hashicorp/nomad/api | v0.0.0-20231213195942-64e3dca9274b |  | go-module-binary-cataloger |
| github.com/hashicorp/serf | v0.10.1 |  | go-module-binary-cataloger |
| github.com/http-wasm/http-wasm-host-go | v0.7.0 |  | go-module-binary-cataloger |
| github.com/huandu/xstrings | v1.5.0 |  | go-module-binary-cataloger |
| github.com/huaweicloud/huaweicloud-sdk-go-v3 | v0.1.192 |  | go-module-binary-cataloger |
| github.com/iij/doapi | v0.0.0-20190504054126-0bbf12d6d7df |  | go-module-binary-cataloger |
| github.com/imdario/mergo | v0.3.16 |  | go-module-binary-cataloger |
| github.com/influxdata/influxdb-client-go/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/influxdata/influxdb1-client | v0.0.0-20200827194710-b269163b24ab |  | go-module-binary-cataloger |
| github.com/influxdata/line-protocol | v0.0.0-20200327222509-2487e7298839 |  | go-module-binary-cataloger |
| github.com/infobloxopen/infoblox-go-client/v2 | v2.11.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/aescts/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/dnsutils/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/gofork | v1.7.6 |  | go-module-binary-cataloger |
| github.com/jcmturner/goidentity/v6 | v6.0.1 |  | go-module-binary-cataloger |
| github.com/jcmturner/gokrb5/v8 | v8.4.4 |  | go-module-binary-cataloger |
| github.com/jcmturner/rpc/v2 | v2.0.3 |  | go-module-binary-cataloger |
| github.com/jinzhu/copier | v0.4.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.13-0.20220915233716-71ac16282d12 |  | go-module-binary-cataloger |
| github.com/k0kubun/go-ansi | v0.0.0-20180517002512-3bf9e2903213 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.5 |  | go-module-binary-cataloger |
| github.com/kolo/xmlrpc | v0.0.0-20220921171641-a4b6fa1dd06b |  | go-module-binary-cataloger |
| github.com/kvtools/consul | v1.0.2 |  | go-module-binary-cataloger |
| github.com/kvtools/etcdv3 | v1.0.3 |  | go-module-binary-cataloger |
| github.com/kvtools/redis | v1.2.0 |  | go-module-binary-cataloger |
| github.com/kvtools/valkeyrie | v1.0.0 |  | go-module-binary-cataloger |
| github.com/kvtools/zookeeper | v1.0.2 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/labbsr0x/bindman-dns-webhook | v1.0.2 |  | go-module-binary-cataloger |
| github.com/labbsr0x/goh | v1.0.1 |  | go-module-binary-cataloger |
| github.com/leodido/go-urn | v1.4.0 |  | go-module-binary-cataloger |
| github.com/linode/linodego | v1.68.0 |  | go-module-binary-cataloger |
| github.com/liquidweb/liquidweb-cli | v0.7.0 |  | go-module-binary-cataloger |
| github.com/liquidweb/liquidweb-go | v1.6.4 |  | go-module-binary-cataloger |
| github.com/magiconair/properties | v1.8.10 |  | go-module-binary-cataloger |
| github.com/mailgun/multibuf | v0.2.0 |  | go-module-binary-cataloger |
| github.com/mailgun/timetools | v0.0.0-20141028012446-7e6055773c51 |  | go-module-binary-cataloger |
| github.com/mailgun/ttlmap | v0.0.0-20170619185759-c1c17f74874f |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.9.0 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.21 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.72 |  | go-module-binary-cataloger |
| github.com/mimuret/golang-iij-dpf | v0.9.1 |  | go-module-binary-cataloger |
| github.com/mitchellh/copystructure | v1.2.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-ps | v1.0.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/hashstructure | v1.0.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.1-0.20231216201459-8508981c8b6c |  | go-module-binary-cataloger |
| github.com/mitchellh/reflectwalk | v1.0.2 |  | go-module-binary-cataloger |
| github.com/moby/docker-image-spec | v1.3.1 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.3-0.20250322232337-35a7c28c31ee |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/namedotcom/go/v4 | v4.0.2 |  | go-module-binary-cataloger |
| github.com/nrdcg/auroradns | v1.2.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/bunny-go | v0.1.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/desec | v0.11.1 |  | go-module-binary-cataloger |
| github.com/nrdcg/dnspod-go | v0.4.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/freemyip | v0.3.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/goacmedns | v0.2.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/goinwx | v0.12.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/mailinabox | v0.3.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/namesilo | v0.5.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/nodion | v0.1.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/oci-go-sdk/common/v1065 | v1065.113.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/oci-go-sdk/dns/v1065 | v1065.113.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/porkbun | v0.4.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/vegadns | v0.3.0 |  | go-module-binary-cataloger |
| github.com/nzdjb/go-metaname | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/image-spec | v1.1.1 |  | go-module-binary-cataloger |
| github.com/ovh/go-ovh | v1.9.0 |  | go-module-binary-cataloger |
| github.com/patrickmn/go-cache | v2.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/pelletier/go-toml/v2 | v2.2.4 |  | go-module-binary-cataloger |
| github.com/peterhellberg/link | v1.2.0 |  | go-module-binary-cataloger |
| github.com/pires/go-proxyproto | v0.8.1 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/pquerna/otp | v1.5.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.65.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.17.0 |  | go-module-binary-cataloger |
| github.com/quic-go/qpack | v0.6.0 |  | go-module-binary-cataloger |
| github.com/quic-go/quic-go | v0.59.0 |  | go-module-binary-cataloger |
| github.com/redis/go-redis/v9 | v9.8.0 |  | go-module-binary-cataloger |
| github.com/regfish/regfish-dnsapi-go | v0.1.1 |  | go-module-binary-cataloger |
| github.com/rs/cors | v1.7.0 |  | go-module-binary-cataloger |
| github.com/rs/zerolog | v1.33.0 |  | go-module-binary-cataloger |
| github.com/sacloud/api-client-go | v0.3.5 |  | go-module-binary-cataloger |
| github.com/sacloud/go-http | v0.1.9 |  | go-module-binary-cataloger |
| github.com/sacloud/iaas-api-go | v1.23.1 |  | go-module-binary-cataloger |
| github.com/sacloud/packages-go | v0.0.12 |  | go-module-binary-cataloger |
| github.com/sagikazarmark/slog-shim | v0.1.0 |  | go-module-binary-cataloger |
| github.com/scaleway/scaleway-sdk-go | v1.0.0-beta.36 |  | go-module-binary-cataloger |
| github.com/selectel/domains-go | v1.1.0 |  | go-module-binary-cataloger |
| github.com/selectel/go-selvpcclient/v4 | v4.2.0 |  | go-module-binary-cataloger |
| github.com/shopspring/decimal | v1.4.0 |  | go-module-binary-cataloger |
| github.com/sirupsen/logrus | v1.9.3 |  | go-module-binary-cataloger |
| github.com/softlayer/softlayer-go | v1.2.1 |  | go-module-binary-cataloger |
| github.com/softlayer/xmlrpc | v0.0.0-20200409220501-5f089df7cb7e |  | go-module-binary-cataloger |
| github.com/sony/gobreaker | v1.0.0 |  | go-module-binary-cataloger |
| github.com/spf13/afero | v1.11.0 |  | go-module-binary-cataloger |
| github.com/spf13/cast | v1.7.0 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.7 |  | go-module-binary-cataloger |
| github.com/spf13/viper | v1.18.2 |  | go-module-binary-cataloger |
| github.com/spiffe/go-spiffe/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/stealthrocket/wasi-go | v0.8.0 |  | go-module-binary-cataloger |
| github.com/stealthrocket/wazergo | v0.19.1 |  | go-module-binary-cataloger |
| github.com/stretchr/objx | v0.5.3 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.11.1 |  | go-module-binary-cataloger |
| github.com/subosito/gotenv | v1.6.0 |  | go-module-binary-cataloger |
| github.com/tailscale/tscert | v0.0.0-20230806124524-28a91b69a046 |  | go-module-binary-cataloger |
| github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common | v1.3.83 |  | go-module-binary-cataloger |
| github.com/tetratelabs/wazero | v1.8.0 |  | go-module-binary-cataloger |
| github.com/tjfoc/gmsm | v1.4.1 |  | go-module-binary-cataloger |
| github.com/traefik/grpc-web | v0.16.0 |  | go-module-binary-cataloger |
| github.com/traefik/paerser | v0.2.2 |  | go-module-binary-cataloger |
| github.com/traefik/traefik/v3 | v3.6.15 |  | go-module-binary-cataloger |
| github.com/traefik/yaegi | v0.16.1 |  | go-module-binary-cataloger |
| github.com/transip/gotransip/v6 | v6.26.2 |  | go-module-binary-cataloger |
| github.com/ucloud/ucloud-sdk-go | v0.22.63 |  | go-module-binary-cataloger |
| github.com/ultradns/ultradns-go-sdk | v1.8.1-20250722213956-faef419 |  | go-module-binary-cataloger |
| github.com/unrolled/render | v1.0.2 |  | go-module-binary-cataloger |
| github.com/unrolled/secure | v1.0.9 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/valyala/fasthttp | v1.69.0 |  | go-module-binary-cataloger |
| github.com/vinyldns/go-vinyldns | v0.9.17 |  | go-module-binary-cataloger |
| github.com/volcengine/volc-sdk-golang | v1.0.242 |  | go-module-binary-cataloger |
| github.com/vulcand/oxy/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/vulcand/predicate | v1.3.0 |  | go-module-binary-cataloger |
| github.com/vultr/govultr/v3 | v3.31.0 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/yandex-cloud/go-genproto | v0.73.0 |  | go-module-binary-cataloger |
| github.com/yandex-cloud/go-sdk/services/dns | v0.0.54 |  | go-module-binary-cataloger |
| github.com/yandex-cloud/go-sdk/v2 | v2.92.0 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/api/v3 | v3.6.4 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.6.4 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.6.4 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.9 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/bridges/otellogrus | v0.13.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/autoprop | v0.63.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/aws | v1.38.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/b3 | v1.38.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/jaeger | v1.38.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/ot | v1.38.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc | v0.17.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp | v0.17.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc | v1.41.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp | v1.41.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.41.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.41.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp | v1.41.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/log | v0.17.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/log | v0.17.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/metric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.9.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/ratelimit | v0.3.1 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.27.0 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.2 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.50.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20260410095643-746e56fc9e2f |  | go-module-binary-cataloger |
| golang.org/x/mod | v0.35.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.53.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.43.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.42.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.15.0 |  | go-module-binary-cataloger |
| gomodules.xyz/jsonpatch/v2 | v2.4.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.276.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20260319201613-d00831a3d3e7 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20260401024825-9d38bb4040a9 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.80.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| gopkg.in/evanphx/json-patch.v4 | v4.13.0 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/ini.v1 | v1.67.1 |  | go-module-binary-cataloger |
| gopkg.in/natefinch/lumberjack.v2 | v2.2.1 |  | go-module-binary-cataloger |
| gopkg.in/ns1/ns1-go.v2 | v2.17.2 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| k8s.io/api | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/apiextensions-apiserver | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/klog/v2 | v2.130.1 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20250814151709-d7b6acb124c3 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20250820121507-0af2bda4dd1d |  | go-module-binary-cataloger |
| knative.dev/networking | v0.0.0-20241022012959-60e29ff520dc |  | go-module-binary-cataloger |
| knative.dev/pkg | v0.0.0-20241021183759-9b9d535af5ad |  | go-module-binary-cataloger |
| libapk | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| libcrypto3 | 3.5.6-r0 | Apache-2.0 | apk-db-cataloger |
| libssl3 | 3.5.6-r0 | Apache-2.0 | apk-db-cataloger |
| musl | 1.2.5-r23 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r23 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| mvdan.cc/xurls/v2 | v2.5.0 |  | go-module-binary-cataloger |
| nhooyr.io/websocket | v1.8.7 |  | go-module-binary-cataloger |
| scanelf | 1.3.8-r2 | GPL-2.0-only | apk-db-cataloger |
| sigs.k8s.io/gateway-api | v1.4.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20250730193827-2d320260d730 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v6 | v6.3.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.6.0 |  | go-module-binary-cataloger |
| ssl_client | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| stdlib | go1.25.9 | BSD-3-Clause | go-module-binary-cataloger |
| traefik | 3.6.15 |  | binary-classifier-cataloger |
| tzdata | 2026b-r0 |  | apk-db-cataloger |
| zlib | 1.3.2-r0 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/api

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| adduser | 3.134 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| amqp | 5.3.1 |  | python-installed-package-cataloger |
| annotated-doc | 0.0.4 | MIT | python-installed-package-cataloger |
| annotated-types | 0.7.0 |  | python-installed-package-cataloger |
| anyio | 4.13.0 | MIT | python-installed-package-cataloger |
| api | 0.1.0 | MIT | python-installed-package-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| argon2-cffi | 25.1.0 | MIT | python-installed-package-cataloger |
| argon2-cffi-bindings | 25.1.0 | MIT | python-installed-package-cataloger |
| asgiref | 3.11.1 | BSD-3-Clause | python-installed-package-cataloger |
| base-files | 12.4+deb12u15 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b13 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| billiard | 4.2.4 |  | python-installed-package-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20230311+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| celery | 5.6.3 | BSD-3-Clause | python-installed-package-cataloger |
| celery-types | 0.24.0 | Apache-2.0 | python-installed-package-cataloger |
| certifi | 2026.4.22 | MPL-2.0 | python-installed-package-cataloger |
| cffi | 2.0.0 | MIT | python-installed-package-cataloger |
| charset-normalizer | 3.4.7 | MIT | python-installed-package-cataloger |
| click | 8.3.3 | BSD-3-Clause | python-installed-package-cataloger |
| click-didyoumean | 0.3.1 | MIT | python-installed-package-cataloger |
| click-plugins | 1.1.1.2 |  | python-installed-package-cataloger |
| click-repl | 0.3.0 | MIT | python-installed-package-cataloger |
| common | 0.1.0 | MIT | python-installed-package-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cryptography | 48.0.0 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u2 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| distro | 1.9.0 |  | python-installed-package-cataloger |
| dpkg | 1.21.23 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| elastic-transport | 9.4.0 |  | python-installed-package-cataloger |
| elasticsearch | 9.2.1 | Apache-2.0 | python-installed-package-cataloger |
| fastapi | 0.128.8 | MIT | python-installed-package-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gpgv | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| h11 | 0.16.0 | MIT | python-installed-package-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| httpcore | 1.0.9 | BSD-3-Clause | python-installed-package-cataloger |
| httpx | 0.28.1 | BSD-3-Clause | python-installed-package-cataloger |
| idna | 3.15 | BSD-3-Clause | python-installed-package-cataloger |
| imapclient | 3.1.0 |  | python-installed-package-cataloger |
| imapclient | 3.1.0 |  | python-installed-package-cataloger |
| importlib-metadata | 8.7.1 | Apache-2.0 | python-installed-package-cataloger |
| init-system-helpers | 1.65.2+deb12u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| jiter | 0.14.0 | MIT | python-installed-package-cataloger |
| joblib | 1.5.3 | BSD-3-Clause | python-installed-package-cataloger |
| kombu | 5.6.2 | BSD-3-Clause | python-installed-package-cataloger |
| libacl1 | 2.3.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4+deb12u3+b1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdebconfclient0 | 0.270 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libext2fs2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi8 | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libgcc-s1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.1-3+deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u7 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libhogweed6 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libidn2-0 | 2.3.3-1+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libncursesw6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libreadline8 | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libseccomp2 | 2.5.4-1+deb12u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.4-1 |  | dpkg-db-cataloger |
| libsemanage2 | 3.4-1+b5 |  | dpkg-db-cataloger |
| libsepol2 | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsmartcols1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2+deb12u2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssl3 | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 252.39-1~deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2+deb12u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libudev1 | 252.39-1~deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libzstd1 | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+deb12u2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| luqum | 0.14.0 | LGPL-3.0-only | python-installed-package-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| minio | 7.2.20 | Apache-2.0 | python-installed-package-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| numpy | 2.5.0 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | python-installed-package-cataloger |
| openai | 1.72.0 | Apache-2.0 | python-installed-package-cataloger |
| openssl | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| opentelemetry-api | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-prometheus | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-asgi | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-fastapi | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-sdk | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-semantic-conventions | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-util-http | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause | python-installed-package-cataloger |
| passwd | 1:4.13+dfsg1-1+deb12u2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pip | 26.1.2 | MIT | python-installed-package-cataloger |
| pip | 26.1.2 | MIT | python-installed-package-cataloger |
| ply | 3.11 |  | python-installed-package-cataloger |
| prometheus-client | 0.24.1 | Apache-2.0 AND BSD-2-Clause | python-installed-package-cataloger |
| prompt-toolkit | 3.0.52 |  | python-installed-package-cataloger |
| pycparser | 3.0 | BSD-3-Clause | python-installed-package-cataloger |
| pycryptodome | 3.23.0 |  | python-installed-package-cataloger |
| pydantic | 2.13.4 | MIT | python-installed-package-cataloger |
| pydantic-core | 2.46.4 | MIT | python-installed-package-cataloger |
| pydantic-settings | 2.14.2 | MIT | python-installed-package-cataloger |
| python | 3.14.6 |  | binary-classifier-cataloger |
| python-dateutil | 2.9.0.post0 |  | python-installed-package-cataloger |
| python-dotenv | 1.2.2 | BSD-3-Clause | python-installed-package-cataloger |
| python-multipart | 0.0.32 | Apache-2.0 | python-installed-package-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| redis | 5.2.1 | MIT | python-installed-package-cataloger |
| requests | 2.32.5 | Apache-2.0 | python-installed-package-cataloger |
| scikit-learn | 1.8.0 | BSD-3-Clause | python-installed-package-cataloger |
| scipy | 1.17.1 | BSD-3-Clause | python-installed-package-cataloger |
| sed | 4.9-1+deb12u1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| sniffio | 1.3.1 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| starlette | 0.52.1 | BSD-3-Clause | python-installed-package-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| threadpoolctl | 3.6.0 | BSD-3-Clause | python-installed-package-cataloger |
| tqdm | 4.67.3 | MPL-2.0 AND MIT | python-installed-package-cataloger |
| types-cffi | 2.0.0.20260518 | Apache-2.0 | python-installed-package-cataloger |
| types-pyopenssl | 24.1.0.20240722 |  | python-installed-package-cataloger |
| types-redis | 4.6.0.20241004 | Apache-2.0 | python-installed-package-cataloger |
| types-requests | 2.32.4.20260324 | Apache-2.0 | python-installed-package-cataloger |
| types-setuptools | 82.0.0.20260518 | Apache-2.0 | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| typing-inspection | 0.4.2 | MIT | python-installed-package-cataloger |
| tzdata | 2026.2 | Apache-2.0 | python-installed-package-cataloger |
| tzdata | 2026b-0+deb12u1 |  | dpkg-db-cataloger |
| tzlocal | 5.4 | MIT | python-installed-package-cataloger |
| urllib3 | 2.7.0 | MIT | python-installed-package-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uvicorn | 0.40.0 | BSD-3-Clause | python-installed-package-cataloger |
| vine | 5.1.0 |  | python-installed-package-cataloger |
| wcwidth | 0.7.0 | MIT | python-installed-package-cataloger |
| websockets | 13.1 | BSD-3-Clause | python-installed-package-cataloger |
| wrapt | 1.17.3 |  | python-installed-package-cataloger |
| zipp | 3.23.1 | MIT | python-installed-package-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/worker

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| adduser | 3.134 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| amqp | 5.3.1 |  | python-installed-package-cataloger |
| annotated-doc | 0.0.4 | MIT | python-installed-package-cataloger |
| annotated-types | 0.7.0 |  | python-installed-package-cataloger |
| anyio | 4.13.0 | MIT | python-installed-package-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| argon2-cffi | 25.1.0 | MIT | python-installed-package-cataloger |
| argon2-cffi-bindings | 25.1.0 | MIT | python-installed-package-cataloger |
| atomicgo.dev/cursor | v0.2.0 |  | go-module-binary-cataloger |
| atomicgo.dev/keyboard | v0.2.9 |  | go-module-binary-cataloger |
| atomicgo.dev/schedule | v0.1.0 |  | go-module-binary-cataloger |
| autoconf | 2.71-3 | GFDL-1.3-only, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| automake | 1:1.16.5-1.3 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| autotools-dev | 20220109.1 | GPL-3.0-only | dpkg-db-cataloger |
| base-files | 12.4+deb12u15 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b13 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| billiard | 4.2.4 |  | python-installed-package-cataloger |
| binutils | 2.40-2 |  | dpkg-db-cataloger |
| binutils-common | 2.40-2 |  | dpkg-db-cataloger |
| binutils-x86-64-linux-gnu | 2.40-2 |  | dpkg-db-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| bzip2 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| ca-certificates | 20230311+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| cel.dev/expr | v0.25.1 |  | go-module-binary-cataloger |
| celery | 5.6.3 | BSD-3-Clause | python-installed-package-cataloger |
| celery-types | 0.24.0 | Apache-2.0 | python-installed-package-cataloger |
| certifi | 2026.4.22 | MPL-2.0 | python-installed-package-cataloger |
| cffi | 2.0.0 | MIT | python-installed-package-cataloger |
| charset-normalizer | 3.4.7 | MIT | python-installed-package-cataloger |
| click | 8.3.3 | BSD-3-Clause | python-installed-package-cataloger |
| click-didyoumean | 0.3.1 | MIT | python-installed-package-cataloger |
| click-plugins | 1.1.1.2 |  | python-installed-package-cataloger |
| click-repl | 0.3.0 | MIT | python-installed-package-cataloger |
| cloud.google.com/go | v0.123.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth | v0.17.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.8 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.9.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/iam | v1.5.3 |  | go-module-binary-cataloger |
| cloud.google.com/go/kms | v1.23.2 |  | go-module-binary-cataloger |
| cloud.google.com/go/longrunning | v0.7.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/monitoring | v1.24.3 |  | go-module-binary-cataloger |
| cloud.google.com/go/pubsub | v1.50.1 |  | go-module-binary-cataloger |
| cloud.google.com/go/pubsub/v2 | v2.3.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/storage | v1.59.2 |  | go-module-binary-cataloger |
| comerr-dev | 2.1-1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| common | 0.1.0 | MIT | python-installed-package-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cpp | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| cpp-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| cryptography | 48.0.0 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| curl | 7.88.1-10+deb12u15 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u2 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| default-libmysqlclient-dev | 1.1.0 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dirmngr | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| distro | 1.9.0 |  | python-installed-package-cataloger |
| dpkg | 1.21.23 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dpkg-dev | 1.21.23 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| elastic-transport | 9.4.0 |  | python-installed-package-cataloger |
| elasticsearch | 9.2.1 | Apache-2.0 | python-installed-package-cataloger |
| fastapi | 0.128.8 | MIT | python-installed-package-cataloger |
| file | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| filippo.io/edwards25519 | v1.1.1 |  | go-module-binary-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| flower | 2.0.1 |  | python-installed-package-cataloger |
| fontconfig | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| fontconfig-config | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-6 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-urw-base35 | 20200910-7 | AGPL-3.0-only, CC-BY-4.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| g++ | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| g++-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| gcc-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| ghostscript | 10.0.0~dfsg-11+deb12u8 | AGPL-3.0-only, AGPL-3.0-or-later, Apache-2.0, BSD-3-Clause, FTL, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, MIT-open-group, X11, Zlib | dpkg-db-cataloger |
| gir1.2-freedesktop | 1.74.0-3 | AFL-2.0, Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, CC0-1.0, FSFAP, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| gir1.2-gdkpixbuf-2.0 | 2.42.10+dfsg-1+deb12u4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| gir1.2-glib-2.0 | 1.74.0-3 | AFL-2.0, Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, CC0-1.0, FSFAP, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| gir1.2-rsvg-2.0 | 2.54.7+dfsg-1~deb12u1 | 0BSD, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, FSFAP, LGPL-2.0-only, LGPL-2.0-or-later, MPL-2.0, OFL-1.1, Unlicense, Zlib | dpkg-db-cataloger |
| git | 1:2.39.5-0+deb12u3 | Apache-2.0, BSD-3-Clause, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| git-man | 1:2.39.5-0+deb12u3 | Apache-2.0, BSD-3-Clause, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.21.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.13.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.11.2 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/storage/azblob | v1.6.4 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/to | v0.4.1 |  | go-module-binary-cataloger |
| github.com/Azure/go-ntlmssp | v0.1.0 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.6.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/detectors/gcp | v1.30.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/exporter/metric | v0.54.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/internal/resourcemapping | v0.54.0 |  | go-module-binary-cataloger |
| github.com/Jille/raft-grpc-transport | v1.6.1 |  | go-module-binary-cataloger |
| github.com/Shopify/sarama | v1.38.1 |  | go-module-binary-cataloger |
| github.com/ThreeDotsLabs/watermill | v1.5.1 |  | go-module-binary-cataloger |
| github.com/a-h/templ | v0.3.977 |  | go-module-binary-cataloger |
| github.com/andybalholm/brotli | v1.2.0 |  | go-module-binary-cataloger |
| github.com/antlr4-go/antlr/v4 | v4.13.1 |  | go-module-binary-cataloger |
| github.com/apache/arrow-go/v18 | v18.4.1 |  | go-module-binary-cataloger |
| github.com/apache/cassandra-gocql-driver/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/apache/iceberg-go | v0.4.0 |  | go-module-binary-cataloger |
| github.com/apache/thrift | v0.22.0 |  | go-module-binary-cataloger |
| github.com/arangodb/go-driver | v1.6.9 |  | go-module-binary-cataloger |
| github.com/arangodb/go-velocypack | v0.0.0-20200318135517-5af53c29c67e |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go | v1.55.8 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.41.3 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/aws/protocol/eventstream | v1.7.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/s3/manager | v1.20.12 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/ini | v1.8.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/v4a | v1.4.16 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/checksum | v1.9.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/s3shared | v1.19.16 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/s3 | v1.95.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.5 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.9 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.35.13 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.41.6 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.24.2 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/boltdb/bolt | v1.3.1 |  | go-module-binary-cataloger |
| github.com/bwmarrin/snowflake | v0.3.0 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/stringish | v0.1.1 |  | go-module-binary-cataloger |
| github.com/clipperhouse/uax29/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cncf/xds/go | v0.0.0-20251110193048-8bfbf64dc13e |  | go-module-binary-cataloger |
| github.com/cockroachdb/apd/v3 | v3.2.1 |  | go-module-binary-cataloger |
| github.com/cognusion/imaging | v1.0.2 |  | go-module-binary-cataloger |
| github.com/containerd/console | v1.0.5 |  | go-module-binary-cataloger |
| github.com/coreos/go-semver | v0.3.1 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.6.0 |  | go-module-binary-cataloger |
| github.com/creasty/defaults | v1.8.0 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/dgryski/go-rendezvous | v0.0.0-20200823014737-9f7001d12a5f |  | go-module-binary-cataloger |
| github.com/dustin/go-humanize | v1.0.1 |  | go-module-binary-cataloger |
| github.com/eapache/go-resiliency | v1.6.0 |  | go-module-binary-cataloger |
| github.com/eapache/go-xerial-snappy | v0.0.0-20230731223053-c322873962e3 |  | go-module-binary-cataloger |
| github.com/eapache/queue | v1.1.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/go-control-plane/envoy | v1.36.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/protoc-gen-validate | v1.2.1 |  | go-module-binary-cataloger |
| github.com/facebookgo/clock | v0.0.0-20150410010913-600d898af40a |  | go-module-binary-cataloger |
| github.com/facebookgo/stats | v0.0.0-20151006221625-1b76add642e4 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fluent/fluent-logger-golang | v1.10.1 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/getsentry/sentry-go | v0.43.0 |  | go-module-binary-cataloger |
| github.com/go-asn1-ber/asn1-ber | v1.5.8-0.20250403174932-29230038a667 |  | go-module-binary-cataloger |
| github.com/go-jose/go-jose/v4 | v4.1.3 |  | go-module-binary-cataloger |
| github.com/go-ldap/ldap/v3 | v3.4.12 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-redsync/redsync/v4 | v4.16.0 |  | go-module-binary-cataloger |
| github.com/go-sql-driver/mysql | v1.9.3 |  | go-module-binary-cataloger |
| github.com/go-viper/mapstructure/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/go-zookeeper/zk | v1.0.3 |  | go-module-binary-cataloger |
| github.com/goccy/go-json | v0.10.5 |  | go-module-binary-cataloger |
| github.com/goccy/go-yaml | v1.18.0 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.3.1 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v1.0.0 |  | go-module-binary-cataloger |
| github.com/google/btree | v1.1.3 |  | go-module-binary-cataloger |
| github.com/google/flatbuffers/go | v0.0.0-20230108230133-3b8644d32c50 |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.9 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/wire | v0.7.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.7 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.15.0 |  | go-module-binary-cataloger |
| github.com/gookit/color | v1.5.4 |  | go-module-binary-cataloger |
| github.com/gorilla/mux | v1.8.1 |  | go-module-binary-cataloger |
| github.com/gorilla/securecookie | v1.1.2 |  | go-module-binary-cataloger |
| github.com/gorilla/sessions | v1.4.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.27.3 |  | go-module-binary-cataloger |
| github.com/hamba/avro/v2 | v2.30.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-immutable-radix | v1.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-metrics | v0.5.4 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-msgpack/v2 | v2.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.8 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-secure-stdlib/parseutil | v0.2.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-secure-stdlib/strutil | v0.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-sockaddr | v1.0.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-uuid | v1.0.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v0.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/hcl | v1.0.1-vault-7 |  | go-module-binary-cataloger |
| github.com/hashicorp/raft | v1.7.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/raft-boltdb/v2 | v2.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/vault/api | v1.22.0 |  | go-module-binary-cataloger |
| github.com/jackc/pgpassfile | v1.0.0 |  | go-module-binary-cataloger |
| github.com/jackc/pgservicefile | v0.0.0-20240606120523-5a60cdf6a761 |  | go-module-binary-cataloger |
| github.com/jackc/pgx/v5 | v5.8.0 |  | go-module-binary-cataloger |
| github.com/jackc/puddle/v2 | v2.2.2 |  | go-module-binary-cataloger |
| github.com/jcmturner/aescts/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/dnsutils/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/gofork | v1.7.6 |  | go-module-binary-cataloger |
| github.com/jcmturner/gokrb5/v8 | v8.4.4 |  | go-module-binary-cataloger |
| github.com/jcmturner/rpc/v2 | v2.0.3 |  | go-module-binary-cataloger |
| github.com/jhump/protoreflect | v1.18.0 |  | go-module-binary-cataloger |
| github.com/jhump/protoreflect/v2 | v2.0.0-beta.1 |  | go-module-binary-cataloger |
| github.com/jmespath/go-jmespath | v0.4.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/karlseguin/ccache/v2 | v2.0.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.4 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/klauspost/reedsolomon | v1.13.0 |  | go-module-binary-cataloger |
| github.com/kr/fs | v0.1.0 |  | go-module-binary-cataloger |
| github.com/kurin/blazer | v0.5.3 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/linkedin/goavro/v2 | v2.15.0 |  | go-module-binary-cataloger |
| github.com/lithammer/fuzzysearch | v1.1.8 |  | go-module-binary-cataloger |
| github.com/lithammer/shortuuid/v3 | v3.0.7 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.19 |  | go-module-binary-cataloger |
| github.com/minio/crc64nvme | v1.1.1 |  | go-module-binary-cataloger |
| github.com/mitchellh/colorstring | v0.0.0-20190213212951-d06e56a500db |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.1-0.20220423185008-bf980b35cac4 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/oklog/ulid | v1.3.1 |  | go-module-binary-cataloger |
| github.com/orcaman/concurrent-map/v2 | v2.0.1 |  | go-module-binary-cataloger |
| github.com/parquet-go/bitpack | v1.0.0 |  | go-module-binary-cataloger |
| github.com/parquet-go/jsonlite | v1.0.0 |  | go-module-binary-cataloger |
| github.com/parquet-go/parquet-go | v0.28.0 |  | go-module-binary-cataloger |
| github.com/pelletier/go-toml/v2 | v2.2.4 |  | go-module-binary-cataloger |
| github.com/peterh/liner | v1.2.2 |  | go-module-binary-cataloger |
| github.com/philhofer/fwd | v1.2.0 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.25 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/sftp | v1.13.10 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/posener/complete | v1.2.3 |  | go-module-binary-cataloger |
| github.com/pquerna/cachecontrol | v0.2.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.2 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.20.1 |  | go-module-binary-cataloger |
| github.com/pterm/pterm | v0.12.81 |  | go-module-binary-cataloger |
| github.com/rcrowley/go-metrics | v0.0.0-20201227073835-cf1acfcdf475 |  | go-module-binary-cataloger |
| github.com/rdleal/intervalst | v1.5.0 |  | go-module-binary-cataloger |
| github.com/redis/go-redis/v9 | v9.18.0 |  | go-module-binary-cataloger |
| github.com/remyoudompheng/bigfft | v0.0.0-20230129092748-24d4a6f8daec |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.4.7 |  | go-module-binary-cataloger |
| github.com/ryanuber/go-glob | v1.0.0 |  | go-module-binary-cataloger |
| github.com/sagikazarmark/locafero | v0.11.0 |  | go-module-binary-cataloger |
| github.com/schollz/progressbar/v3 | v3.19.0 |  | go-module-binary-cataloger |
| github.com/seaweedfs/go-fuse/v2 | v2.9.1 |  | go-module-binary-cataloger |
| github.com/seaweedfs/goexif | v1.0.3 |  | go-module-binary-cataloger |
| github.com/seaweedfs/raft | v1.1.6 |  | go-module-binary-cataloger |
| github.com/seaweedfs/seaweedfs | v0.0.0-20260311092924-4a5243886a5c |  | go-module-binary-cataloger |
| github.com/shirou/gopsutil/v4 | v4.26.2 |  | go-module-binary-cataloger |
| github.com/sirupsen/logrus | v1.9.4-0.20230606125235-dd1b4c2e81af |  | go-module-binary-cataloger |
| github.com/sony/gobreaker | v1.0.0 |  | go-module-binary-cataloger |
| github.com/sourcegraph/conc | v0.3.1-0.20240121214520-5f936abd7ae8 |  | go-module-binary-cataloger |
| github.com/spf13/afero | v1.15.0 |  | go-module-binary-cataloger |
| github.com/spf13/cast | v1.10.0 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/spf13/viper | v1.21.0 |  | go-module-binary-cataloger |
| github.com/spiffe/go-spiffe/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/stretchr/objx | v0.5.2 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.11.1 |  | go-module-binary-cataloger |
| github.com/subosito/gotenv | v1.6.0 |  | go-module-binary-cataloger |
| github.com/substrait-io/substrait | v0.69.0 |  | go-module-binary-cataloger |
| github.com/substrait-io/substrait-go/v4 | v4.4.0 |  | go-module-binary-cataloger |
| github.com/substrait-io/substrait-protobuf/go | v0.71.0 |  | go-module-binary-cataloger |
| github.com/syndtr/goleveldb | v1.0.1-0.20190318030020-c3a204f8e965 |  | go-module-binary-cataloger |
| github.com/tidwall/gjson | v1.18.0 |  | go-module-binary-cataloger |
| github.com/tidwall/match | v1.2.0 |  | go-module-binary-cataloger |
| github.com/tidwall/pretty | v1.2.0 |  | go-module-binary-cataloger |
| github.com/tinylib/msgp | v1.5.0 |  | go-module-binary-cataloger |
| github.com/tklauser/go-sysconf | v0.3.16 |  | go-module-binary-cataloger |
| github.com/tklauser/numcpus | v0.11.0 |  | go-module-binary-cataloger |
| github.com/tsuna/gohbase | v0.0.0-20201125011725-348991136365 |  | go-module-binary-cataloger |
| github.com/twmb/murmur3 | v1.1.8 |  | go-module-binary-cataloger |
| github.com/twpayne/go-geom | v1.6.1 |  | go-module-binary-cataloger |
| github.com/tylertreat/BoomFilters | v0.0.0-20210315201527-1a82519a3e43 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/viant/ptrie | v1.0.1 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xeipuuv/gojsonpointer | v0.0.0-20190905194746-02993c407bfb |  | go-module-binary-cataloger |
| github.com/xeipuuv/gojsonreference | v0.0.0-20180127040603-bd5ef7bd5415 |  | go-module-binary-cataloger |
| github.com/xeipuuv/gojsonschema | v1.2.0 |  | go-module-binary-cataloger |
| github.com/xo/terminfo | v0.0.0-20220910002029-abceb7e1c41e |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/zeebo/xxh3 | v1.0.2 |  | go-module-binary-cataloger |
| gnupg | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-l10n | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-utils | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| go.etcd.io/bbolt | v1.4.3 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/api/v3 | v3.6.7 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.6.7 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.6.7 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.9 |  | go-module-binary-cataloger |
| go.opencensus.io | v0.24.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/detectors/gcp | v1.38.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc | v0.63.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.63.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/metric | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.40.0 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.27.1 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.3 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| gocloud.dev | v0.45.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.48.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20251023183803-a4bb9ffd2546 |  | go-module-binary-cataloger |
| golang.org/x/image | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.49.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.35.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.19.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.42.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.34.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20240903120638-7835f813f4da |  | go-module-binary-cataloger |
| google.golang.org/api | v0.258.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20251124214823-79d6a2a48846 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20251124214823-79d6a2a48846 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20251213004720-97cd9d5aeac2 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.78.0 |  | go-module-binary-cataloger |
| google.golang.org/grpc/security/advancedtls | v1.0.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gotenberg-client | 0.13.1 | MPL-2.0 | python-installed-package-cataloger |
| gpg | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-wks-client | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-wks-server | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgv | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| h11 | 0.16.0 | MIT | python-installed-package-cataloger |
| h2 | 4.3.0 | MIT | python-installed-package-cataloger |
| hicolor-icon-theme | 0.17-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| hpack | 4.1.0 | MIT | python-installed-package-cataloger |
| httpcore | 1.0.9 | BSD-3-Clause | python-installed-package-cataloger |
| httpx | 0.28.1 | BSD-3-Clause | python-installed-package-cataloger |
| humanize | 4.15.0 | MIT | python-installed-package-cataloger |
| hyperframe | 6.1.0 | MIT | python-installed-package-cataloger |
| icu-devtools | 72.1-3+deb12u1 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| idna | 3.15 | BSD-3-Clause | python-installed-package-cataloger |
| imagemagick | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| imagemagick-6-common | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| imagemagick-6.q16 | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| imapclient | 3.1.0 |  | python-installed-package-cataloger |
| imapclient | 3.1.0 |  | python-installed-package-cataloger |
| init-system-helpers | 1.65.2+deb12u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| jiter | 0.14.0 | MIT | python-installed-package-cataloger |
| joblib | 1.5.3 | BSD-3-Clause | python-installed-package-cataloger |
| jsonpatch | 1.33 |  | python-installed-package-cataloger |
| jsonpointer | 3.1.1 |  | python-installed-package-cataloger |
| kombu | 5.6.2 | BSD-3-Clause | python-installed-package-cataloger |
| krb5-multidev | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| langchain-core | 1.4.0 | MIT | python-installed-package-cataloger |
| langchain-protocol | 0.0.15 | MIT | python-installed-package-cataloger |
| langchain-text-splitters | 1.1.2 | MIT | python-installed-package-cataloger |
| langsmith | 0.8.3 | MIT | python-installed-package-cataloger |
| libabsl20220623 | 20220623.1-1+deb12u2 | Apache-2.0 | dpkg-db-cataloger |
| libacl1 | 2.3.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaom3 | 3.6.0-1+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, ISC | dpkg-db-cataloger |
| libapr1 | 1.7.2-3+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libaprutil1 | 1.6.3-1 | Apache-2.0 | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libasan8 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libassuan0 | 2.5.5-5 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libatomic1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavahi-client3 | 0.8-10+deb12u1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavahi-common-data | 0.8-10+deb12u1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavahi-common3 | 0.8-10+deb12u1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavif15 | 0.11.1-1+deb12u1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC0-1.0 | dpkg-db-cataloger |
| libbcg729-0 | 1.1.1-2 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libbinutils | 2.40-2 |  | dpkg-db-cataloger |
| libblkid-dev | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbluetooth-dev | 5.66-1+deb12u2 | Apache-2.0, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libbluetooth3 | 5.66-1+deb12u2 | Apache-2.0, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libbrotli-dev | 1.0.9-2+b6 | MIT | dpkg-db-cataloger |
| libbrotli1 | 1.0.9-2+b6 | MIT | dpkg-db-cataloger |
| libbsd0 | 0.11.7-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC, libutil-David-Nugent | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libbz2-dev | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-ares2 | 1.18.1-3 |  | dpkg-db-cataloger |
| libc-bin | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc-dev-bin | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6-dev | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcairo-gobject2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo-script-interpreter2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2-dev | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4+deb12u3+b1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcap2-bin | 1:2.66-4+deb12u3+b1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcbor0.8 | 0.8.0-2+b1 |  | dpkg-db-cataloger |
| libcc1-0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt-dev | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libctf-nobfd0 | 2.40-2 |  | dpkg-db-cataloger |
| libctf0 | 2.40-2 |  | dpkg-db-cataloger |
| libcups2 | 2.4.2-3+deb12u9 | Apache-2.0, BSD-2-Clause, FSFUL, Zlib | dpkg-db-cataloger |
| libcurl3-gnutls | 7.88.1-10+deb12u15 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4 | 7.88.1-10+deb12u15 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4-openssl-dev | 7.88.1-10+deb12u15 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libdatrie1 | 0.2.13-2+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libdav1d6 | 1.0.0-2+deb12u1 | BSD-2-Clause, ISC | dpkg-db-cataloger |
| libdb-dev | 5.3.2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdb5.3-dev | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdbus-1-3 | 1.14.10-1~deb12u1 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libde265-0 | 1.0.11-1+deb12u2 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libdebconfclient0 | 0.270 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdeflate-dev | 1.14-1 |  | dpkg-db-cataloger |
| libdeflate0 | 1.14-1 |  | dpkg-db-cataloger |
| libdjvulibre-dev | 3.5.28-2.2~deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| libdjvulibre-text | 3.5.28-2.2~deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| libdjvulibre21 | 3.5.28-2.2~deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| libdpkg-perl | 1.21.23 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libedit2 | 3.1-20221030-2 | BSD-3-Clause | dpkg-db-cataloger |
| libelf1 | 0.188-2.1 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| liberror-perl | 0.17029-2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libevent-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-core-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-dev | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-extra-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-openssl-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-pthreads-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libexif-dev | 0.6.24-1+deb12u1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libexif12 | 0.6.24-1+deb12u1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libexpat1 | 2.5.0-1+deb12u2 | MIT | dpkg-db-cataloger |
| libexpat1-dev | 2.5.0-1+deb12u2 | MIT | dpkg-db-cataloger |
| libext2fs2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi-dev | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libffi8 | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libfftw3-double3 | 3.3.10-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libfido2-1 | 1.12.0-2+b1 | BSD-2-Clause, ISC | dpkg-db-cataloger |
| libfontconfig-dev | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| libfontconfig1 | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| libfontenc1 | 1:1.1.4-1 | MIT | dpkg-db-cataloger |
| libfreetype-dev | 2.12.1+dfsg-5+deb12u4 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, Zlib | dpkg-db-cataloger |
| libfreetype6 | 2.12.1+dfsg-5+deb12u4 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, Zlib | dpkg-db-cataloger |
| libfreetype6-dev | 2.12.1+dfsg-5+deb12u4 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, Zlib | dpkg-db-cataloger |
| libfribidi0 | 1.0.8-2.1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgav1-1 | 0.18.0-1+b1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libgcc-12-dev | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcc-s1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.1-3+deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| libgd3 | 2.3.3-9 | BSD-3-Clause, GD, GPL-2.0-only, GPL-2.0-or-later, HPND, MIT, Xfig | dpkg-db-cataloger |
| libgdbm-compat4 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm-dev | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdk-pixbuf-2.0-0 | 2.42.10+dfsg-1+deb12u4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf-2.0-dev | 2.42.10+dfsg-1+deb12u4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf2.0-bin | 2.42.10+dfsg-1+deb12u4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf2.0-common | 2.42.10+dfsg-1+deb12u4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgif7 | 5.2.1-2.5+deb12u1 | ISC, MIT | dpkg-db-cataloger |
| libgirepository-1.0-1 | 1.74.0-3 | AFL-2.0, Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, CC0-1.0, FSFAP, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-0 | 2.74.6-2+deb12u9 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-bin | 2.74.6-2+deb12u9 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-data | 2.74.6-2+deb12u9 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-dev | 2.74.6-2+deb12u9 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-dev-bin | 2.74.6-2+deb12u9 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgmp-dev | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgmpxx4ldbl | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u7 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgprofng0 | 2.40-2 |  | dpkg-db-cataloger |
| libgraphite2-3 | 1.3.14-1+deb12u1 | GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libgs-common | 10.0.0~dfsg-11+deb12u8 | AGPL-3.0-only, AGPL-3.0-or-later, Apache-2.0, BSD-3-Clause, FTL, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, MIT-open-group, X11, Zlib | dpkg-db-cataloger |
| libgs10 | 10.0.0~dfsg-11+deb12u8 | AGPL-3.0-only, AGPL-3.0-or-later, Apache-2.0, BSD-3-Clause, FTL, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, MIT-open-group, X11, Zlib | dpkg-db-cataloger |
| libgs10-common | 10.0.0~dfsg-11+deb12u8 | AGPL-3.0-only, AGPL-3.0-or-later, Apache-2.0, BSD-3-Clause, FTL, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, MIT-open-group, X11, Zlib | dpkg-db-cataloger |
| libgsf-1-114 | 1.14.50-1+deb12u1 | FSFUL, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libgsf-1-common | 1.14.50-1+deb12u1 | FSFUL, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libgssrpc4 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libharfbuzz0b | 6.0.0+dfsg-3 | Apache-2.0, CC0-1.0, FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, MIT, OFL-1.1 | dpkg-db-cataloger |
| libheif1 | 1.15.1-1+deb12u1 | BSD-3-Clause, BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libhogweed6 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libice-dev | 2:1.0.10-1 |  | dpkg-db-cataloger |
| libice6 | 2:1.0.10-1 |  | dpkg-db-cataloger |
| libicu-dev | 72.1-3+deb12u1 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libicu72 | 72.1-3+deb12u1 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn12 | 1.41-1 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libidn2-0 | 2.3.3-1+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libijs-0.35 | 0.35-15 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libimath-3-1-29 | 3.1.6-1 |  | dpkg-db-cataloger |
| libimath-dev | 3.1.6-1 |  | dpkg-db-cataloger |
| libisl23 | 0.25-1.1 | BSD-2-Clause, LGPL-2.0-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libitm1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libjansson4 | 2.14-2 |  | dpkg-db-cataloger |
| libjbig-dev | 2.1-6.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libjbig0 | 2.1-6.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libjbig2dec0 | 0.19-3 | AGPL-3.0-or-later, BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libjpeg-dev | 1:2.1.5-2 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libjpeg62-turbo | 1:2.1.5-2 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libjpeg62-turbo-dev | 1:2.1.5-2 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libk5crypto3 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkadm5clnt-mit12 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkadm5srv-mit12 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkdb5-10 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5-dev | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libksba8 | 1.6.3-2 | FSFUL, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblcms2-2 | 2.14-2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| liblcms2-dev | 2.14-2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| libldap-2.5-0 | 2.5.13+dfsg-5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| liblept5 | 1.82.0-3+b3 | BSD-2-Clause | dpkg-db-cataloger |
| libleptonica-dev | 1.82.0-3+b3 | BSD-2-Clause | dpkg-db-cataloger |
| liblerc-dev | 4.0.0+ds-2 | Apache-2.0 | dpkg-db-cataloger |
| liblerc4 | 4.0.0+ds-2 | Apache-2.0 | dpkg-db-cataloger |
| liblqr-1-0 | 0.4.2-2.1 | GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| liblqr-1-0-dev | 0.4.2-2.1 | GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| liblsan0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libltdl-dev | 2.4.7-7~deb12u1 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libltdl7 | 2.4.7-7~deb12u1 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblua5.2-0 | 5.2.4-3 |  | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma-dev | 5.4.1-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblzo2-2 | 2.10-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmagic-mgc | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| libmagic1 | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| libmagickcore-6-arch-config | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-6-headers | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-6.q16-6 | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-6.q16-6-extra | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-6.q16-dev | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-dev | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-6-headers | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-6.q16-6 | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-6.q16-dev | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-dev | 8:6.9.11.60+dfsg-1.6+deb12u13 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmariadb-dev | 1:10.11.18-0+deb12u1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmariadb-dev-compat | 1:10.11.18-0+deb12u1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmariadb3 | 1:10.11.18-0+deb12u1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmaxminddb-dev | 1.7.1-1 | Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmaxminddb0 | 1.7.1-1 | Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount-dev | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmpc3 | 1.3.1-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libmpfr6 | 4.2.0-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libncurses-dev | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncurses5-dev | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncurses6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncursesw5-dev | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncursesw6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.52.0-1+deb12u3 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnl-3-200 | 3.7.0-0.2+b1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libnl-genl-3-200 | 3.7.0-0.2+b1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libnpth0 | 1.6-3 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnsl-dev | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnuma1 | 2.0.16-1 |  | dpkg-db-cataloger |
| libopenexr-3-1-30 | 3.1.5-5 | BSD-3-Clause | dpkg-db-cataloger |
| libopenexr-dev | 3.1.5-5 | BSD-3-Clause | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.0-2+deb12u3 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libopenjp2-7-dev | 2.5.0-2+deb12u3 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpango-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangocairo-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangoft2-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpaper1 | 1.1.29 | GPL-2.0-only | dpkg-db-cataloger |
| libpcap0.8 | 1.10.3-1 |  | dpkg-db-cataloger |
| libpcre2-16-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-32-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-dev | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-posix3 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libperl5.36 | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| libpixman-1-0 | 0.42.2-1 |  | dpkg-db-cataloger |
| libpixman-1-dev | 0.42.2-1 |  | dpkg-db-cataloger |
| libpkgconf3 | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| libpng-dev | 1.6.39-2+deb12u5 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpng16-16 | 1.6.39-2+deb12u5 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpq-dev | 15.18-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libpq5 | 15.18-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.2-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpsl5 | 0.21.2-1 | MIT | dpkg-db-cataloger |
| libpst4 | 0.6.76-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libpthread-stubs0-dev | 0.4-1 |  | dpkg-db-cataloger |
| libpython3-stdlib | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| libpython3.11-minimal | 3.11.2-6+deb12u8 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-stdlib | 3.11.2-6+deb12u8 | GPL-2.0-only | dpkg-db-cataloger |
| libquadmath0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| librav1e0 | 0.5.1-6 | BSD-2-Clause, BSD-2-Clause, ISC | dpkg-db-cataloger |
| libreadline-dev | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libreadline8 | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| librsvg2-2 | 2.54.7+dfsg-1~deb12u1 | 0BSD, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, FSFAP, LGPL-2.0-only, LGPL-2.0-or-later, MPL-2.0, OFL-1.1, Unlicense, Zlib | dpkg-db-cataloger |
| librsvg2-common | 2.54.7+dfsg-1~deb12u1 | 0BSD, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, FSFAP, LGPL-2.0-only, LGPL-2.0-or-later, MPL-2.0, OFL-1.1, Unlicense, Zlib | dpkg-db-cataloger |
| librsvg2-dev | 2.54.7+dfsg-1~deb12u1 | 0BSD, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, FSFAP, LGPL-2.0-only, LGPL-2.0-or-later, MPL-2.0, OFL-1.1, Unlicense, Zlib | dpkg-db-cataloger |
| librtmp1 | 2.4+20151223.gitfa8646d.1-2+b2 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsasl2-2 | 2.1.28+dfsg-10 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.28+dfsg-10 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libsbc1 | 2.0-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libseccomp2 | 2.5.4-1+deb12u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1-dev | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.4-1 |  | dpkg-db-cataloger |
| libsemanage2 | 3.4-1+b5 |  | dpkg-db-cataloger |
| libsepol-dev | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsepol2 | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libserf-1-1 | 1.3.9-11 | Apache-2.0, Zlib | dpkg-db-cataloger |
| libsm-dev | 2:1.2.3-1 |  | dpkg-db-cataloger |
| libsm6 | 2:1.2.3-1 |  | dpkg-db-cataloger |
| libsmartcols1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsmi2ldbl | 0.4.8+dfsg2-16 |  | dpkg-db-cataloger |
| libsnappy1v5 | 1.1.9-3 | BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, MIT | dpkg-db-cataloger |
| libspandsp2 | 0.0.6+dfsg-2+b1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libspeexdsp1 | 1.2.1-1 | BSD-3-Clause, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2+deb12u2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsqlite3-dev | 3.40.1-2+deb12u2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssh-gcrypt-4 | 0.10.6-0+deb12u2 | BSD-2-Clause, BSD-3-Clause, LGPL-2.1-only | dpkg-db-cataloger |
| libssh2-1 | 1.10.0-3+b1 |  | dpkg-db-cataloger |
| libssl-dev | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libssl3 | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++-12-dev | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsvn1 | 1.14.2-4+deb12u1 | AFL-3.0, Apache-2.0, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libsvtav1enc1 | 1.4.1+dfsg-1 | BSD-2-Clause, BSD-3-Clause-Clear, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsystemd0 | 252.39-1~deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2+deb12u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtcl8.6 | 8.6.13+dfsg-2 |  | dpkg-db-cataloger |
| libthai-data | 0.1.29-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libthai0 | 0.1.29-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtiff-dev | 4.5.0-6+deb12u4 |  | dpkg-db-cataloger |
| libtiff6 | 4.5.0-6+deb12u4 |  | dpkg-db-cataloger |
| libtiffxx6 | 4.5.0-6+deb12u4 |  | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc-dev | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtk8.6 | 8.6.13-2 |  | dpkg-db-cataloger |
| libtool | 2.4.7-7~deb12u1 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libtsan2 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libubsan1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libudev1 | 252.39-1~deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libutf8proc2 | 2.8.0-1 |  | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libwebp-dev | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebp7 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebpdemux2 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebpmux3 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwireshark-data | 4.0.17-0+deb12u3 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwireshark16 | 4.0.17-0+deb12u3 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwiretap13 | 4.0.17-0+deb12u3 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwmf-0.2-7 | 0.2.12-5.1 | AGPL-3.0-only, GD, ISC, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwmf-dev | 0.2.12-5.1 | AGPL-3.0-only, GD, ISC, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwmflite-0.2-7 | 0.2.12-5.1 | AGPL-3.0-only, GD, ISC, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwsutil14 | 4.0.17-0+deb12u3 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| libx11-6 | 2:1.8.4-2+deb12u2 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.8.4-2+deb12u2 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-dev | 2:1.8.4-2+deb12u2 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx265-199 | 3.5-2+b1 | GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libxau-dev | 1:1.0.9-1 |  | dpkg-db-cataloger |
| libxau6 | 1:1.0.9-1 |  | dpkg-db-cataloger |
| libxcb-render0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-render0-dev | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-shm0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-shm0-dev | 1.15-1 |  | dpkg-db-cataloger |
| libxcb1 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb1-dev | 1.15-1 |  | dpkg-db-cataloger |
| libxdmcp-dev | 1:1.1.2-3 |  | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.2-3 |  | dpkg-db-cataloger |
| libxext-dev | 2:1.3.4-1+b1 |  | dpkg-db-cataloger |
| libxext6 | 2:1.3.4-1+b1 |  | dpkg-db-cataloger |
| libxft-dev | 2.3.6-1 | HPND-sell-variant | dpkg-db-cataloger |
| libxft2 | 2.3.6-1 | HPND-sell-variant | dpkg-db-cataloger |
| libxml2 | 2.9.14+dfsg-1.3~deb12u6 | ISC | dpkg-db-cataloger |
| libxml2-dev | 2.9.14+dfsg-1.3~deb12u6 | ISC | dpkg-db-cataloger |
| libxpm4 | 1:3.5.12-1.1+deb12u1 | MIT | dpkg-db-cataloger |
| libxrender-dev | 1:0.9.10-1.1 | HPND-sell-variant | dpkg-db-cataloger |
| libxrender1 | 1:0.9.10-1.1 | HPND-sell-variant | dpkg-db-cataloger |
| libxslt1-dev | 1.1.35-1+deb12u4 |  | dpkg-db-cataloger |
| libxslt1.1 | 1.1.35-1+deb12u4 |  | dpkg-db-cataloger |
| libxss-dev | 1:1.2.3-1 | MIT | dpkg-db-cataloger |
| libxss1 | 1:1.2.3-1 | MIT | dpkg-db-cataloger |
| libxt-dev | 1:1.2.1-1.1 |  | dpkg-db-cataloger |
| libxt6 | 1:1.2.1-1.1 |  | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libyaml-0-2 | 0.2.5-1 |  | dpkg-db-cataloger |
| libyaml-dev | 0.2.5-1 |  | dpkg-db-cataloger |
| libyuv0 | 0.0~git20230123.b2528b0-1 | BSD-3-Clause | dpkg-db-cataloger |
| libzstd-dev | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| libzstd1 | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| linux-libc-dev | 6.1.176-1 | BSD-2-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+deb12u2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| luqum | 0.14.0 | LGPL-3.0-only | python-installed-package-cataloger |
| m4 | 1.4.19-3 |  | dpkg-db-cataloger |
| make | 4.3-4.1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| mariadb-common | 1:10.11.18-0+deb12u1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 10.0.0 |  | dpkg-db-cataloger |
| mercurial | 6.3.2 |  | python-installed-package-cataloger |
| mercurial | 6.3.2-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| mercurial-common | 6.3.2-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| minio | 7.2.20 | Apache-2.0 | python-installed-package-cataloger |
| modernc.org/b | v1.0.0 |  | go-module-binary-cataloger |
| modernc.org/mathutil | v1.7.1 |  | go-module-binary-cataloger |
| modernc.org/strutil | v1.2.1 |  | go-module-binary-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| mysql-common | 5.8+1.1.0 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| numpy | 2.4.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | python-installed-package-cataloger |
| openai | 1.72.0 | Apache-2.0 | python-installed-package-cataloger |
| openssh-client | 1:9.2p1-2+deb12u10 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| openssl | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| orjson | 3.11.9 | MPL-2.0 AND (Apache-2.0 OR MIT) | python-installed-package-cataloger |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause | python-installed-package-cataloger |
| passwd | 1:4.13+dfsg1-1+deb12u2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.7.6-7 |  | dpkg-db-cataloger |
| perl | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-modules-5.36 | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pinentry-curses | 1.2.1-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| pip | 26.1.2 | MIT | python-installed-package-cataloger |
| pip | 26.1.2 | MIT | python-installed-package-cataloger |
| pkg-config | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| pkgconf | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| pkgconf-bin | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| ply | 3.11 |  | python-installed-package-cataloger |
| poppler-data | 0.4.12-1 | AGPL-3.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| procps | 2:4.0.2-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| prometheus-client | 0.25.0 | Apache-2.0 AND BSD-2-Clause | python-installed-package-cataloger |
| prompt-toolkit | 3.0.52 |  | python-installed-package-cataloger |
| pst-utils | 0.6.76-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| pycparser | 3.0 | BSD-3-Clause | python-installed-package-cataloger |
| pycryptodome | 3.23.0 |  | python-installed-package-cataloger |
| pydantic | 2.13.4 | MIT | python-installed-package-cataloger |
| pydantic-core | 2.46.4 | MIT | python-installed-package-cataloger |
| pydantic-settings | 2.14.2 | MIT | python-installed-package-cataloger |
| python | 3.14.6 |  | binary-classifier-cataloger |
| python-dateutil | 2.9.0.post0 |  | python-installed-package-cataloger |
| python-dotenv | 1.2.2 | BSD-3-Clause | python-installed-package-cataloger |
| python-magic | 0.4.27 | MIT | python-installed-package-cataloger |
| python3 | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3-distutils | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-lib2to3 | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-minimal | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3.11 | 3.11.2-6+deb12u8 | GPL-2.0-only | dpkg-db-cataloger |
| python3.11-minimal | 3.11.2-6+deb12u8 | GPL-2.0-only | dpkg-db-cataloger |
| pytz | 2026.2 | MIT | python-installed-package-cataloger |
| pyyaml | 6.0.3 | MIT | python-installed-package-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| redis | 5.2.1 | MIT | python-installed-package-cataloger |
| requests | 2.32.5 | Apache-2.0 | python-installed-package-cataloger |
| requests-toolbelt | 1.0.0 |  | python-installed-package-cataloger |
| rpcsvc-proto | 1.4.3-1 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, MIT | dpkg-db-cataloger |
| scikit-learn | 1.8.0 | BSD-3-Clause | python-installed-package-cataloger |
| scipy | 1.17.1 | BSD-3-Clause | python-installed-package-cataloger |
| sed | 4.9-1+deb12u1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sensible-utils | 0.0.17+nmu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| shared-mime-info | 2.2-1 |  | dpkg-db-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| sniffio | 1.3.1 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| sq | 0.27.0-2+b1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| starlette | 0.52.1 | BSD-3-Clause | python-installed-package-cataloger |
| stdlib | go1.26.1 | BSD-3-Clause | go-module-binary-cataloger |
| subversion | 1.14.2-4+deb12u1 | AFL-3.0, Apache-2.0, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tcl | 8.6.13 |  | dpkg-db-cataloger |
| tcl-dev | 8.6.13 |  | dpkg-db-cataloger |
| tcl8.6 | 8.6.13+dfsg-2 |  | dpkg-db-cataloger |
| tcl8.6-dev | 8.6.13+dfsg-2 |  | dpkg-db-cataloger |
| tenacity | 9.1.4 |  | python-installed-package-cataloger |
| threadpoolctl | 3.6.0 | BSD-3-Clause | python-installed-package-cataloger |
| tk | 8.6.13 |  | dpkg-db-cataloger |
| tk-dev | 8.6.13 |  | dpkg-db-cataloger |
| tk8.6 | 8.6.13-2 |  | dpkg-db-cataloger |
| tk8.6-dev | 8.6.13-2 |  | dpkg-db-cataloger |
| tornado | 6.5.5 | Apache-2.0 | python-installed-package-cataloger |
| tqdm | 4.67.3 | MPL-2.0 AND MIT | python-installed-package-cataloger |
| tshark | 4.0.17-0+deb12u3 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| types-cffi | 2.0.0.20260518 | Apache-2.0 | python-installed-package-cataloger |
| types-pyopenssl | 24.1.0.20240722 |  | python-installed-package-cataloger |
| types-redis | 4.6.0.20241004 | Apache-2.0 | python-installed-package-cataloger |
| types-requests | 2.32.4.20260324 | Apache-2.0 | python-installed-package-cataloger |
| types-setuptools | 82.0.0.20260518 | Apache-2.0 | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| typing-inspection | 0.4.2 | MIT | python-installed-package-cataloger |
| tzdata | 2026.2 | Apache-2.0 | python-installed-package-cataloger |
| tzdata | 2026b-0+deb12u1 |  | dpkg-db-cataloger |
| tzlocal | 5.4 | MIT | python-installed-package-cataloger |
| ucf | 3.0043+nmu1+deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| unzip | 6.0-28 |  | dpkg-db-cataloger |
| urllib3 | 2.7.0 | MIT | python-installed-package-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uuid-dev | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uuid-utils | 0.15.0 | BSD-3-Clause | python-installed-package-cataloger |
| vine | 5.1.0 |  | python-installed-package-cataloger |
| wand | 0.6.13 |  | python-installed-package-cataloger |
| wcwidth | 0.7.0 | MIT | python-installed-package-cataloger |
| wget | 1.21.3-1+deb12u1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| wireshark-common | 4.0.17-0+deb12u3 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| worker | 0.1.0 | MIT | python-installed-package-cataloger |
| x11-common | 1:7.7+23 |  | dpkg-db-cataloger |
| x11proto-core-dev | 2022.1-1 | MIT | dpkg-db-cataloger |
| x11proto-dev | 2022.1-1 | MIT | dpkg-db-cataloger |
| xfonts-encodings | 1:1.0.4-2.2 |  | dpkg-db-cataloger |
| xfonts-utils | 1:7.7+6 |  | dpkg-db-cataloger |
| xorg-sgml-doctools | 1:1.11-1.1 | HPND-sell-variant, MIT | dpkg-db-cataloger |
| xtrans-dev | 1.4.0-1 | HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| xxhash | 3.7.0 |  | python-installed-package-cataloger |
| xz-utils | 5.4.1-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zlib1g-dev | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zstandard | 0.25.0 | BSD-3-Clause | python-installed-package-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/crawler

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| adduser | 3.134 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| amqp | 5.3.1 |  | python-installed-package-cataloger |
| annotated-doc | 0.0.4 | MIT | python-installed-package-cataloger |
| annotated-types | 0.7.0 |  | python-installed-package-cataloger |
| anyio | 4.13.0 | MIT | python-installed-package-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| argon2-cffi | 25.1.0 | MIT | python-installed-package-cataloger |
| argon2-cffi-bindings | 25.1.0 | MIT | python-installed-package-cataloger |
| base-files | 12.4+deb12u15 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b13 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| billiard | 4.2.4 |  | python-installed-package-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20230311+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| celery | 5.6.3 | BSD-3-Clause | python-installed-package-cataloger |
| celery-types | 0.24.0 | Apache-2.0 | python-installed-package-cataloger |
| certifi | 2026.4.22 | MPL-2.0 | python-installed-package-cataloger |
| cffi | 2.0.0 | MIT | python-installed-package-cataloger |
| charset-normalizer | 3.4.7 | MIT | python-installed-package-cataloger |
| click | 8.3.3 | BSD-3-Clause | python-installed-package-cataloger |
| click-didyoumean | 0.3.1 | MIT | python-installed-package-cataloger |
| click-plugins | 1.1.1.2 |  | python-installed-package-cataloger |
| click-repl | 0.3.0 | MIT | python-installed-package-cataloger |
| common | 0.1.0 | MIT | python-installed-package-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| crawler | 0.1.0 | MIT | python-installed-package-cataloger |
| cryptography | 48.0.0 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u2 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| distro | 1.9.0 |  | python-installed-package-cataloger |
| dpkg | 1.21.23 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| elastic-transport | 9.4.0 |  | python-installed-package-cataloger |
| elasticsearch | 9.2.1 | Apache-2.0 | python-installed-package-cataloger |
| fastapi | 0.128.8 | MIT | python-installed-package-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gpgv | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| h11 | 0.16.0 | MIT | python-installed-package-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| httpcore | 1.0.9 | BSD-3-Clause | python-installed-package-cataloger |
| httpx | 0.28.1 | BSD-3-Clause | python-installed-package-cataloger |
| idna | 3.15 | BSD-3-Clause | python-installed-package-cataloger |
| imapclient | 3.1.0 |  | python-installed-package-cataloger |
| imapclient | 3.1.0 |  | python-installed-package-cataloger |
| init-system-helpers | 1.65.2+deb12u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| jiter | 0.14.0 | MIT | python-installed-package-cataloger |
| kombu | 5.6.2 | BSD-3-Clause | python-installed-package-cataloger |
| libacl1 | 2.3.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4+deb12u3+b1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdebconfclient0 | 0.270 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libext2fs2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi8 | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libgcc-s1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.1-3+deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u7 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libhogweed6 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libidn2-0 | 2.3.3-1+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libncursesw6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libreadline8 | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libseccomp2 | 2.5.4-1+deb12u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.4-1 |  | dpkg-db-cataloger |
| libsemanage2 | 3.4-1+b5 |  | dpkg-db-cataloger |
| libsepol2 | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsmartcols1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2+deb12u2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssl3 | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 252.39-1~deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2+deb12u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libudev1 | 252.39-1~deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libzstd1 | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+deb12u2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| luqum | 0.14.0 | LGPL-3.0-only | python-installed-package-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| minio | 7.2.20 | Apache-2.0 | python-installed-package-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| openai | 1.72.0 | Apache-2.0 | python-installed-package-cataloger |
| openssl | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause | python-installed-package-cataloger |
| passwd | 1:4.13+dfsg1-1+deb12u2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pip | 26.1.2 | MIT | python-installed-package-cataloger |
| pip | 26.1.2 | MIT | python-installed-package-cataloger |
| ply | 3.11 |  | python-installed-package-cataloger |
| prompt-toolkit | 3.0.52 |  | python-installed-package-cataloger |
| pycparser | 3.0 | BSD-3-Clause | python-installed-package-cataloger |
| pycryptodome | 3.23.0 |  | python-installed-package-cataloger |
| pydantic | 2.13.4 | MIT | python-installed-package-cataloger |
| pydantic-core | 2.46.4 | MIT | python-installed-package-cataloger |
| pydantic-settings | 2.14.2 | MIT | python-installed-package-cataloger |
| python | 3.14.6 |  | binary-classifier-cataloger |
| python-dateutil | 2.9.0.post0 |  | python-installed-package-cataloger |
| python-dotenv | 1.2.2 | BSD-3-Clause | python-installed-package-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| redis | 5.2.1 | MIT | python-installed-package-cataloger |
| requests | 2.32.5 | Apache-2.0 | python-installed-package-cataloger |
| sed | 4.9-1+deb12u1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| sniffio | 1.3.1 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| starlette | 0.52.1 | BSD-3-Clause | python-installed-package-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tqdm | 4.67.3 | MPL-2.0 AND MIT | python-installed-package-cataloger |
| types-cffi | 2.0.0.20260518 | Apache-2.0 | python-installed-package-cataloger |
| types-pyopenssl | 24.1.0.20240722 |  | python-installed-package-cataloger |
| types-redis | 4.6.0.20241004 | Apache-2.0 | python-installed-package-cataloger |
| types-requests | 2.32.4.20260324 | Apache-2.0 | python-installed-package-cataloger |
| types-setuptools | 82.0.0.20260518 | Apache-2.0 | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| typing-inspection | 0.4.2 | MIT | python-installed-package-cataloger |
| tzdata | 2026.2 | Apache-2.0 | python-installed-package-cataloger |
| tzdata | 2026b-0+deb12u1 |  | dpkg-db-cataloger |
| tzlocal | 5.4 | MIT | python-installed-package-cataloger |
| urllib3 | 2.7.0 | MIT | python-installed-package-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| vine | 5.1.0 |  | python-installed-package-cataloger |
| watchdog | 6.0.0 | Apache-2.0 | python-installed-package-cataloger |
| wcwidth | 0.7.0 | MIT | python-installed-package-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/frontend

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.6-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.23.5-r0 | MIT | apk-db-cataloger |
| aom-libs | 3.14.1-r0 | BSD-2-Clause | apk-db-cataloger |
| apk-tools | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| brotli-libs | 1.2.0-r0 | MIT | apk-db-cataloger |
| busybox | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| c-ares | 1.34.6-r0 | MIT | apk-db-cataloger |
| ca-certificates | 20260611-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20260611-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| curl | 8.19.0-r0 | curl | apk-db-cataloger |
| fontconfig | 2.17.1-r0 | MIT | apk-db-cataloger |
| freetype | 2.14.1-r0 | FTL OR GPL-2.0-or-later | apk-db-cataloger |
| geoip | 1.6.12-r6 | LGPL-2.1-or-later | apk-db-cataloger |
| gettext-envsubst | 0.24.1-r1 | GPL-3.0-or-later AND LGPL-2.1-or-later AND MIT | apk-db-cataloger |
| libapk | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| libavif | 1.3.0-r0 | BSD-2-Clause | apk-db-cataloger |
| libbsd | 0.12.2-r0 | BSD-3-Clause | apk-db-cataloger |
| libbz2 | 1.0.8-r6 | bzip2-1.0.6 | apk-db-cataloger |
| libcrypto3 | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| libcurl | 8.19.0-r0 | curl | apk-db-cataloger |
| libdav1d | 1.5.2-r0 | BSD-2-Clause | apk-db-cataloger |
| libedit | 20251016.3.1-r0 | BSD-3-Clause | apk-db-cataloger |
| libexpat | 2.8.1-r0 | MIT | apk-db-cataloger |
| libgcc | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libgd | 2.3.3-r10 | GD | apk-db-cataloger |
| libice | 1.1.2-r0 | X11 | apk-db-cataloger |
| libidn2 | 2.3.8-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libintl | 0.24.1-r1 | LGPL-2.1-or-later | apk-db-cataloger |
| libjpeg-turbo | 3.1.2-r0 | BSD-3-Clause AND IJG AND Zlib | apk-db-cataloger |
| libmd | 1.1.0-r0 | BSD-2-Clause, BSD-3-Clause, Beerware, ISC | apk-db-cataloger |
| libncursesw | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| libpng | 1.6.58-r1 | Libpng | apk-db-cataloger |
| libpsl | 0.21.5-r3 | MIT | apk-db-cataloger |
| libsharpyuv | 1.6.0-r0 | BSD-3-Clause | apk-db-cataloger |
| libsm | 1.2.6-r0 | MIT | apk-db-cataloger |
| libssl3 | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| libstdc++ | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libunistring | 1.4.1-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libuuid | 2.41.4-r0 | BSD-3-Clause | apk-db-cataloger |
| libwebp | 1.6.0-r0 | BSD-3-Clause | apk-db-cataloger |
| libx11 | 1.8.12-r1 | X11 | apk-db-cataloger |
| libxau | 1.0.12-r0 | MIT | apk-db-cataloger |
| libxcb | 1.17.0-r1 | MIT | apk-db-cataloger |
| libxdmcp | 1.1.5-r1 | MIT | apk-db-cataloger |
| libxext | 1.3.6-r2 | MIT | apk-db-cataloger |
| libxml2 | 2.13.9-r1 | MIT | apk-db-cataloger |
| libxpm | 3.5.19-r0 | X11 | apk-db-cataloger |
| libxslt | 1.1.43-r3 | X11 | apk-db-cataloger |
| libxt | 1.3.1-r0 | MIT | apk-db-cataloger |
| libyuv | 0.0.1887.20251502-r1 | BSD-3-Clause | apk-db-cataloger |
| musl | 1.2.5-r23 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r23 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| nghttp2-libs | 1.69.0-r0 | MIT | apk-db-cataloger |
| nginx | 1.30.3-r1 |  | apk-db-cataloger |
| nginx-module-acme | 1.30.3.0.4.1-r1 |  | apk-db-cataloger |
| nginx-module-geoip | 1.30.3-r1 |  | apk-db-cataloger |
| nginx-module-image-filter | 1.30.3-r1 |  | apk-db-cataloger |
| nginx-module-njs | 1.30.3.0.9.9-r1 |  | apk-db-cataloger |
| nginx-module-xslt | 1.30.3-r1 |  | apk-db-cataloger |
| pcre2 | 10.47-r0 | BSD-3-Clause | apk-db-cataloger |
| scanelf | 1.3.8-r2 | GPL-2.0-only | apk-db-cataloger |
| ssl_client | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| tiff | 4.7.1-r0 | libtiff | apk-db-cataloger |
| tzdata | 2026b-r0 |  | apk-db-cataloger |
| xz-libs | 5.8.3-r0 | 0BSD, GPL-2.0-or-later, LGPL-2.1-or-later | apk-db-cataloger |
| zlib | 1.3.2-r0 | Zlib | apk-db-cataloger |
| zstd-libs | 1.5.7-r2 | BSD-3-Clause OR GPL-2.0-or-later | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/open-webui

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| accelerate | 1.13.0 |  | python-installed-package-cataloger |
| adduser | 3.134 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| adler2 | 2.0.1 |  | cargo-auditable-binary-cataloger |
| adler2 | 2.0.1 |  | cargo-auditable-binary-cataloger |
| aes | 0.8.4 |  | cargo-auditable-binary-cataloger |
| aes | 0.8.4 |  | cargo-auditable-binary-cataloger |
| aho-corasick | 1.1.4 |  | cargo-auditable-binary-cataloger |
| aho-corasick | 1.1.4 |  | cargo-auditable-binary-cataloger |
| aiocache | 0.12.3 | BSD-3-Clause | python-installed-package-cataloger |
| aiofiles | 25.1.0 | Apache-2.0 | python-installed-package-cataloger |
| aiohappyeyeballs | 2.6.2 | PSF-2.0 | python-installed-package-cataloger |
| aiohttp | 3.13.5 | Apache-2.0 AND MIT | python-installed-package-cataloger |
| aiosignal | 1.4.0 |  | python-installed-package-cataloger |
| aiosqlite | 0.22.1 |  | python-installed-package-cataloger |
| alembic | 1.18.4 | MIT | python-installed-package-cataloger |
| allocator-api2 | 0.2.21 |  | cargo-auditable-binary-cataloger |
| allocator-api2 | 0.2.21 |  | cargo-auditable-binary-cataloger |
| ambient-id | 0.0.11 |  | cargo-auditable-binary-cataloger |
| ambient-id | 0.0.11 |  | cargo-auditable-binary-cataloger |
| annotated-doc | 0.0.4 | MIT | python-installed-package-cataloger |
| annotated-types | 0.7.0 |  | python-installed-package-cataloger |
| anstream | 1.0.0 |  | cargo-auditable-binary-cataloger |
| anstream | 1.0.0 |  | cargo-auditable-binary-cataloger |
| anstyle | 1.0.14 |  | cargo-auditable-binary-cataloger |
| anstyle | 1.0.14 |  | cargo-auditable-binary-cataloger |
| anstyle-parse | 1.0.0 |  | cargo-auditable-binary-cataloger |
| anstyle-parse | 1.0.0 |  | cargo-auditable-binary-cataloger |
| anstyle-query | 1.1.5 |  | cargo-auditable-binary-cataloger |
| anstyle-query | 1.1.5 |  | cargo-auditable-binary-cataloger |
| anthropic | 0.86.0 | MIT | python-installed-package-cataloger |
| anyhow | 1.0.102 |  | cargo-auditable-binary-cataloger |
| anyhow | 1.0.102 |  | cargo-auditable-binary-cataloger |
| anyio | 4.14.1 | MIT | python-installed-package-cataloger |
| apscheduler | 3.11.2 | MIT | python-installed-package-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| arcstr | 1.2.0 |  | cargo-auditable-binary-cataloger |
| arcstr | 1.2.0 |  | cargo-auditable-binary-cataloger |
| argon2-cffi | 25.1.0 | MIT | python-installed-package-cataloger |
| argon2-cffi-bindings | 25.1.0 | MIT | python-installed-package-cataloger |
| asgiref | 3.11.1 | BSD-3-Clause | python-installed-package-cataloger |
| asn1-rs | 0.7.1 |  | cargo-auditable-binary-cataloger |
| asn1-rs | 0.7.1 |  | cargo-auditable-binary-cataloger |
| asn1-rs-impl | 0.2.0 |  | cargo-auditable-binary-cataloger |
| asn1-rs-impl | 0.2.0 |  | cargo-auditable-binary-cataloger |
| assert-json-diff | 2.0.2 |  | cargo-auditable-binary-cataloger |
| assert-json-diff | 2.0.2 |  | cargo-auditable-binary-cataloger |
| assert_cmd | 2.2.2 |  | cargo-auditable-binary-cataloger |
| assert_cmd | 2.2.2 |  | cargo-auditable-binary-cataloger |
| assert_fs | 1.1.4 |  | cargo-auditable-binary-cataloger |
| assert_fs | 1.1.4 |  | cargo-auditable-binary-cataloger |
| astral-pubgrub | 0.3.3 |  | cargo-auditable-binary-cataloger |
| astral-pubgrub | 0.3.3 |  | cargo-auditable-binary-cataloger |
| astral-reqwest-middleware | 0.5.1 |  | cargo-auditable-binary-cataloger |
| astral-reqwest-middleware | 0.5.1 |  | cargo-auditable-binary-cataloger |
| astral-reqwest-retry | 0.9.1 |  | cargo-auditable-binary-cataloger |
| astral-reqwest-retry | 0.9.1 |  | cargo-auditable-binary-cataloger |
| astral-tl | 0.7.11 |  | cargo-auditable-binary-cataloger |
| astral-tl | 0.7.11 |  | cargo-auditable-binary-cataloger |
| astral-tokio-tar | 0.6.3 |  | cargo-auditable-binary-cataloger |
| astral-tokio-tar | 0.6.3 |  | cargo-auditable-binary-cataloger |
| astral-version-ranges | 0.1.4 |  | cargo-auditable-binary-cataloger |
| astral-version-ranges | 0.1.4 |  | cargo-auditable-binary-cataloger |
| astral_async_http_range_reader | 0.11.0 |  | cargo-auditable-binary-cataloger |
| astral_async_http_range_reader | 0.11.0 |  | cargo-auditable-binary-cataloger |
| astral_async_zip | 0.0.18 |  | cargo-auditable-binary-cataloger |
| astral_async_zip | 0.0.18 |  | cargo-auditable-binary-cataloger |
| async-broadcast | 0.7.2 |  | cargo-auditable-binary-cataloger |
| async-broadcast | 0.7.2 |  | cargo-auditable-binary-cataloger |
| async-channel | 2.5.0 |  | cargo-auditable-binary-cataloger |
| async-channel | 2.5.0 |  | cargo-auditable-binary-cataloger |
| async-compression | 0.4.19 |  | cargo-auditable-binary-cataloger |
| async-compression | 0.4.19 |  | cargo-auditable-binary-cataloger |
| async-recursion | 1.1.1 |  | cargo-auditable-binary-cataloger |
| async-recursion | 1.1.1 |  | cargo-auditable-binary-cataloger |
| async-timeout | 5.0.1 |  | python-installed-package-cataloger |
| async-trait | 0.1.89 |  | cargo-auditable-binary-cataloger |
| async-trait | 0.1.89 |  | cargo-auditable-binary-cataloger |
| atomic-waker | 1.1.2 |  | cargo-auditable-binary-cataloger |
| atomic-waker | 1.1.2 |  | cargo-auditable-binary-cataloger |
| attrs | 26.1.0 | MIT | python-installed-package-cataloger |
| authlib | 1.7.2 | BSD-3-Clause | python-installed-package-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| av | 14.0.1 |  | python-installed-package-cataloger |
| aws-lc-rs | 1.16.2 |  | cargo-auditable-binary-cataloger |
| aws-lc-rs | 1.16.2 |  | cargo-auditable-binary-cataloger |
| aws-lc-sys | 0.39.0 |  | cargo-auditable-binary-cataloger |
| aws-lc-sys | 0.39.0 |  | cargo-auditable-binary-cataloger |
| axoasset | 2.0.1 |  | cargo-auditable-binary-cataloger |
| axoasset | 2.0.1 |  | cargo-auditable-binary-cataloger |
| axoprocess | 0.2.1 |  | cargo-auditable-binary-cataloger |
| axoprocess | 0.2.1 |  | cargo-auditable-binary-cataloger |
| axotag | 0.3.0 |  | cargo-auditable-binary-cataloger |
| axotag | 0.3.0 |  | cargo-auditable-binary-cataloger |
| axoupdater | 0.10.0 |  | cargo-auditable-binary-cataloger |
| axoupdater | 0.10.0 |  | cargo-auditable-binary-cataloger |
| azure-ai-documentintelligence | 1.0.2 |  | python-installed-package-cataloger |
| azure-core | 1.41.0 | MIT | python-installed-package-cataloger |
| azure-identity | 1.25.3 | MIT | python-installed-package-cataloger |
| azure-search-documents | 12.0.0 | MIT | python-installed-package-cataloger |
| azure-storage-blob | 12.29.0 |  | python-installed-package-cataloger |
| backports-tarfile | 1.2.0 | MIT | python-installed-package-cataloger |
| base-files | 12.4+deb12u14 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| base64 | 0.22.1 |  | cargo-auditable-binary-cataloger |
| base64 | 0.22.1 |  | cargo-auditable-binary-cataloger |
| base64ct | 1.8.3 |  | cargo-auditable-binary-cataloger |
| base64ct | 1.8.3 |  | cargo-auditable-binary-cataloger |
| bash | 5.2.15-2+b13 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| bcrypt | 5.0.0 | Apache-2.0 | python-installed-package-cataloger |
| beautifulsoup4 | 4.14.3 |  | python-installed-package-cataloger |
| bidict | 0.23.1 |  | python-installed-package-cataloger |
| binutils | 2.40-2 |  | dpkg-db-cataloger |
| binutils-common | 2.40-2 |  | dpkg-db-cataloger |
| binutils-x86-64-linux-gnu | 2.40-2 |  | dpkg-db-cataloger |
| bitarray | 3.8.2 | PSF-2.0 | python-installed-package-cataloger |
| bitflags | 2.13.0 |  | cargo-auditable-binary-cataloger |
| bitflags | 2.13.0 |  | cargo-auditable-binary-cataloger |
| black | 26.5.1 | MIT | python-installed-package-cataloger |
| blake2 | 0.10.6 |  | cargo-auditable-binary-cataloger |
| blake2 | 0.10.6 |  | cargo-auditable-binary-cataloger |
| blinker | 1.9.0 | MIT | python-installed-package-cataloger |
| blis | 1.3.3 |  | python-installed-package-cataloger |
| block-buffer | 0.10.4 |  | cargo-auditable-binary-cataloger |
| block-buffer | 0.10.4 |  | cargo-auditable-binary-cataloger |
| block-padding | 0.3.3 |  | cargo-auditable-binary-cataloger |
| block-padding | 0.3.3 |  | cargo-auditable-binary-cataloger |
| borrow-or-share | 0.2.4 |  | cargo-auditable-binary-cataloger |
| borrow-or-share | 0.2.4 |  | cargo-auditable-binary-cataloger |
| boto3 | 1.42.62 | Apache-2.0 | python-installed-package-cataloger |
| botocore | 1.42.97 | Apache-2.0 | python-installed-package-cataloger |
| boxcar | 0.2.14 |  | cargo-auditable-binary-cataloger |
| boxcar | 0.2.14 |  | cargo-auditable-binary-cataloger |
| brotli | 1.2.0 | MIT | python-installed-package-cataloger |
| brotlicffi | 1.2.0.1 | MIT | python-installed-package-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| bstr | 1.12.1 |  | cargo-auditable-binary-cataloger |
| bstr | 1.12.1 |  | cargo-auditable-binary-cataloger |
| build | 1.5.0 | MIT | python-installed-package-cataloger |
| build-essential | 12.9 |  | dpkg-db-cataloger |
| bytecheck | 0.8.2 |  | cargo-auditable-binary-cataloger |
| bytecheck | 0.8.2 |  | cargo-auditable-binary-cataloger |
| bytemuck | 1.25.0 |  | cargo-auditable-binary-cataloger |
| bytemuck | 1.25.0 |  | cargo-auditable-binary-cataloger |
| byteorder-lite | 0.1.0 |  | cargo-auditable-binary-cataloger |
| byteorder-lite | 0.1.0 |  | cargo-auditable-binary-cataloger |
| bytes | 1.11.1 |  | cargo-auditable-binary-cataloger |
| bytes | 1.11.1 |  | cargo-auditable-binary-cataloger |
| bzip2 | 0.5.2 |  | cargo-auditable-binary-cataloger |
| bzip2 | 0.5.2 |  | cargo-auditable-binary-cataloger |
| bzip2 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| bzip2-sys | 0.1.13+1.0.8 |  | cargo-auditable-binary-cataloger |
| bzip2-sys | 0.1.13+1.0.8 |  | cargo-auditable-binary-cataloger |
| ca-certificates | 20230311+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| cachetools | 7.1.4 | MIT | python-installed-package-cataloger |
| camino | 1.2.2 |  | cargo-auditable-binary-cataloger |
| camino | 1.2.2 |  | cargo-auditable-binary-cataloger |
| cargo-util | 0.2.28 |  | cargo-auditable-binary-cataloger |
| cargo-util | 0.2.28 |  | cargo-auditable-binary-cataloger |
| catalogue | 2.0.10 | MIT | python-installed-package-cataloger |
| cbc | 0.1.2 |  | cargo-auditable-binary-cataloger |
| cbc | 0.1.2 |  | cargo-auditable-binary-cataloger |
| certifi | 2026.6.17 | MPL-2.0 | python-installed-package-cataloger |
| cffi | 2.0.0 | MIT | python-installed-package-cataloger |
| cfg-if | 1.0.4 |  | cargo-auditable-binary-cataloger |
| cfg-if | 1.0.4 |  | cargo-auditable-binary-cataloger |
| chardet | 7.4.3 | 0BSD | python-installed-package-cataloger |
| charset | 0.1.5 |  | cargo-auditable-binary-cataloger |
| charset | 0.1.5 |  | cargo-auditable-binary-cataloger |
| charset-normalizer | 3.4.7 | MIT | python-installed-package-cataloger |
| chromadb | 1.5.9 |  | python-installed-package-cataloger |
| cipher | 0.4.4 |  | cargo-auditable-binary-cataloger |
| cipher | 0.4.4 |  | cargo-auditable-binary-cataloger |
| clap | 4.6.1 |  | cargo-auditable-binary-cataloger |
| clap | 4.6.1 |  | cargo-auditable-binary-cataloger |
| clap_builder | 4.6.0 |  | cargo-auditable-binary-cataloger |
| clap_builder | 4.6.0 |  | cargo-auditable-binary-cataloger |
| clap_complete | 4.6.0 |  | cargo-auditable-binary-cataloger |
| clap_complete | 4.6.0 |  | cargo-auditable-binary-cataloger |
| clap_complete_command | 0.6.1 |  | cargo-auditable-binary-cataloger |
| clap_complete_command | 0.6.1 |  | cargo-auditable-binary-cataloger |
| clap_complete_nushell | 4.6.0 |  | cargo-auditable-binary-cataloger |
| clap_complete_nushell | 4.6.0 |  | cargo-auditable-binary-cataloger |
| clap_lex | 1.1.0 |  | cargo-auditable-binary-cataloger |
| clap_lex | 1.1.0 |  | cargo-auditable-binary-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| click | 8.4.2 | BSD-3-Clause | python-installed-package-cataloger |
| cloudpathlib | 0.24.0 |  | python-installed-package-cataloger |
| colbert-ai | 0.2.22 |  | python-installed-package-cataloger |
| colorchoice | 1.0.5 |  | cargo-auditable-binary-cataloger |
| colorchoice | 1.0.5 |  | cargo-auditable-binary-cataloger |
| concurrent-queue | 2.5.0 |  | cargo-auditable-binary-cataloger |
| concurrent-queue | 2.5.0 |  | cargo-auditable-binary-cataloger |
| confection | 1.3.3 | MIT | python-installed-package-cataloger |
| configparser | 3.2.0 |  | cargo-auditable-binary-cataloger |
| configparser | 3.2.0 |  | cargo-auditable-binary-cataloger |
| console | 0.16.3 |  | cargo-auditable-binary-cataloger |
| console | 0.16.3 |  | cargo-auditable-binary-cataloger |
| const-oid | 0.9.6 |  | cargo-auditable-binary-cataloger |
| const-oid | 0.9.6 |  | cargo-auditable-binary-cataloger |
| const-random | 0.1.18 |  | cargo-auditable-binary-cataloger |
| const-random | 0.1.18 |  | cargo-auditable-binary-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cpp | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| cpp-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| cpufeatures | 0.2.17 |  | cargo-auditable-binary-cataloger |
| cpufeatures | 0.2.17 |  | cargo-auditable-binary-cataloger |
| crc32fast | 1.5.0 |  | cargo-auditable-binary-cataloger |
| crc32fast | 1.5.0 |  | cargo-auditable-binary-cataloger |
| crossbeam-channel | 0.5.15 |  | cargo-auditable-binary-cataloger |
| crossbeam-channel | 0.5.15 |  | cargo-auditable-binary-cataloger |
| crossbeam-deque | 0.8.6 |  | cargo-auditable-binary-cataloger |
| crossbeam-deque | 0.8.6 |  | cargo-auditable-binary-cataloger |
| crossbeam-epoch | 0.9.18 |  | cargo-auditable-binary-cataloger |
| crossbeam-epoch | 0.9.18 |  | cargo-auditable-binary-cataloger |
| crossbeam-utils | 0.8.21 |  | cargo-auditable-binary-cataloger |
| crossbeam-utils | 0.8.21 |  | cargo-auditable-binary-cataloger |
| crypto-common | 0.1.7 |  | cargo-auditable-binary-cataloger |
| crypto-common | 0.1.7 |  | cargo-auditable-binary-cataloger |
| cryptography | 48.0.0 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| csv | 1.4.0 |  | cargo-auditable-binary-cataloger |
| csv | 1.4.0 |  | cargo-auditable-binary-cataloger |
| csv-core | 0.1.13 |  | cargo-auditable-binary-cataloger |
| csv-core | 0.1.13 |  | cargo-auditable-binary-cataloger |
| ctranslate2 | 4.8.0 | MIT | python-installed-package-cataloger |
| ctrlc | 3.5.2 |  | cargo-auditable-binary-cataloger |
| ctrlc | 3.5.2 |  | cargo-auditable-binary-cataloger |
| curl | 7.88.1-10+deb12u14 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| cyclonedx-bom | 0.8.1 |  | cargo-auditable-binary-cataloger |
| cyclonedx-bom | 0.8.1 |  | cargo-auditable-binary-cataloger |
| cyclonedx-bom-macros | 0.1.0 |  | cargo-auditable-binary-cataloger |
| cyclonedx-bom-macros | 0.1.0 |  | cargo-auditable-binary-cataloger |
| cymem | 2.0.13 | MIT | python-installed-package-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| data-encoding | 2.11.0 |  | cargo-auditable-binary-cataloger |
| data-encoding | 2.11.0 |  | cargo-auditable-binary-cataloger |
| datasets | 4.0.0 |  | python-installed-package-cataloger |
| ddgs | 9.14.4 | MIT | python-installed-package-cataloger |
| deadpool | 0.12.3 |  | cargo-auditable-binary-cataloger |
| deadpool | 0.12.3 |  | cargo-auditable-binary-cataloger |
| deadpool-runtime | 0.1.4 |  | cargo-auditable-binary-cataloger |
| deadpool-runtime | 0.1.4 |  | cargo-auditable-binary-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u2 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| defusedxml | 0.7.1 |  | python-installed-package-cataloger |
| deprecation | 2.1.0 |  | python-installed-package-cataloger |
| der | 0.7.10 |  | cargo-auditable-binary-cataloger |
| der | 0.7.10 |  | cargo-auditable-binary-cataloger |
| der-parser | 10.0.0 |  | cargo-auditable-binary-cataloger |
| der-parser | 10.0.0 |  | cargo-auditable-binary-cataloger |
| deranged | 0.5.8 |  | cargo-auditable-binary-cataloger |
| deranged | 0.5.8 |  | cargo-auditable-binary-cataloger |
| difflib | 0.4.0 |  | cargo-auditable-binary-cataloger |
| difflib | 0.4.0 |  | cargo-auditable-binary-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| digest | 0.10.7 |  | cargo-auditable-binary-cataloger |
| digest | 0.10.7 |  | cargo-auditable-binary-cataloger |
| dill | 0.3.8 | BSD-3-Clause | python-installed-package-cataloger |
| dirs | 6.0.0 |  | cargo-auditable-binary-cataloger |
| dirs | 6.0.0 |  | cargo-auditable-binary-cataloger |
| dirs-sys | 0.5.0 |  | cargo-auditable-binary-cataloger |
| dirs-sys | 0.5.0 |  | cargo-auditable-binary-cataloger |
| diskus | 0.9.0 |  | cargo-auditable-binary-cataloger |
| diskus | 0.9.0 |  | cargo-auditable-binary-cataloger |
| displaydoc | 0.2.5 |  | cargo-auditable-binary-cataloger |
| displaydoc | 0.2.5 |  | cargo-auditable-binary-cataloger |
| distro | 1.9.0 |  | python-installed-package-cataloger |
| dlv-list | 0.5.2 |  | cargo-auditable-binary-cataloger |
| dlv-list | 0.5.2 |  | cargo-auditable-binary-cataloger |
| dnspython | 2.8.0 | ISC | python-installed-package-cataloger |
| docker | 7.1.0 | Apache-2.0 | python-installed-package-cataloger |
| docstring-parser | 0.18.0 | MIT | python-installed-package-cataloger |
| docx2txt | 0.9 |  | python-installed-package-cataloger |
| dotenvy | 0.15.7 |  | cargo-auditable-binary-cataloger |
| dotenvy | 0.15.7 |  | cargo-auditable-binary-cataloger |
| dpkg | 1.21.23 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dpkg-dev | 1.21.23 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dunce | 1.0.5 |  | cargo-auditable-binary-cataloger |
| dunce | 1.0.5 |  | cargo-auditable-binary-cataloger |
| durationpy | 0.10 | MIT | python-installed-package-cataloger |
| dyn-clone | 1.0.20 |  | cargo-auditable-binary-cataloger |
| dyn-clone | 1.0.20 |  | cargo-auditable-binary-cataloger |
| e2fsprogs | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| ecdsa | 0.19.2 | MIT | python-installed-package-cataloger |
| einops | 0.8.2 | MIT | python-installed-package-cataloger |
| either | 1.16.0 |  | cargo-auditable-binary-cataloger |
| either | 1.16.0 |  | cargo-auditable-binary-cataloger |
| elastic-transport | 9.4.2 |  | python-installed-package-cataloger |
| elasticsearch | 9.4.1 | Apache-2.0 | python-installed-package-cataloger |
| emoji | 2.15.0 |  | python-installed-package-cataloger |
| encoding_rs | 0.8.35 |  | cargo-auditable-binary-cataloger |
| encoding_rs | 0.8.35 |  | cargo-auditable-binary-cataloger |
| encoding_rs_io | 0.1.7 |  | cargo-auditable-binary-cataloger |
| encoding_rs_io | 0.1.7 |  | cargo-auditable-binary-cataloger |
| endi | 1.1.1 |  | cargo-auditable-binary-cataloger |
| endi | 1.1.1 |  | cargo-auditable-binary-cataloger |
| enumflags2 | 0.7.12 |  | cargo-auditable-binary-cataloger |
| enumflags2 | 0.7.12 |  | cargo-auditable-binary-cataloger |
| equivalent | 1.0.2 |  | cargo-auditable-binary-cataloger |
| equivalent | 1.0.2 |  | cargo-auditable-binary-cataloger |
| erased-serde | 0.4.10 |  | cargo-auditable-binary-cataloger |
| erased-serde | 0.4.10 |  | cargo-auditable-binary-cataloger |
| errno | 0.3.14 |  | cargo-auditable-binary-cataloger |
| errno | 0.3.14 |  | cargo-auditable-binary-cataloger |
| et-xmlfile | 2.0.0 | MIT | python-installed-package-cataloger |
| etcetera | 0.11.0 |  | cargo-auditable-binary-cataloger |
| etcetera | 0.11.0 |  | cargo-auditable-binary-cataloger |
| event-listener | 5.4.1 |  | cargo-auditable-binary-cataloger |
| event-listener | 5.4.1 |  | cargo-auditable-binary-cataloger |
| event-listener-strategy | 0.5.4 |  | cargo-auditable-binary-cataloger |
| event-listener-strategy | 0.5.4 |  | cargo-auditable-binary-cataloger |
| events | 0.5 |  | python-installed-package-cataloger |
| fake-useragent | 2.2.0 | Apache-2.0 | python-installed-package-cataloger |
| fastapi | 0.136.3 | MIT | python-installed-package-cataloger |
| faster-whisper | 1.2.1 | MIT | python-installed-package-cataloger |
| fastrand | 2.4.1 |  | cargo-auditable-binary-cataloger |
| fastrand | 2.4.1 |  | cargo-auditable-binary-cataloger |
| ffmpeg | 7.1 |  | binary-classifier-cataloger |
| ffmpeg | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| ffmpeg | 8.0.1 |  | binary-classifier-cataloger |
| filelock | 3.29.0 | MIT | python-installed-package-cataloger |
| filetime | 0.2.29 |  | cargo-auditable-binary-cataloger |
| filetime | 0.2.29 |  | cargo-auditable-binary-cataloger |
| filetype | 1.2.0 | MIT | python-installed-package-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| fixedbitset | 0.5.7 |  | cargo-auditable-binary-cataloger |
| fixedbitset | 0.5.7 |  | cargo-auditable-binary-cataloger |
| flask | 3.1.3 | BSD-3-Clause | python-installed-package-cataloger |
| flatbuffers | 25.12.19 |  | python-installed-package-cataloger |
| flate2 | 1.1.9 |  | cargo-auditable-binary-cataloger |
| flate2 | 1.1.9 |  | cargo-auditable-binary-cataloger |
| float-cmp | 0.10.0 |  | cargo-auditable-binary-cataloger |
| float-cmp | 0.10.0 |  | cargo-auditable-binary-cataloger |
| fluent-uri | 0.4.1 |  | cargo-auditable-binary-cataloger |
| fluent-uri | 0.4.1 |  | cargo-auditable-binary-cataloger |
| fnv | 1.0.7 |  | cargo-auditable-binary-cataloger |
| fnv | 1.0.7 |  | cargo-auditable-binary-cataloger |
| foldhash | 0.1.5 |  | cargo-auditable-binary-cataloger |
| foldhash | 0.1.5 |  | cargo-auditable-binary-cataloger |
| foldhash | 0.2.0 |  | cargo-auditable-binary-cataloger |
| foldhash | 0.2.0 |  | cargo-auditable-binary-cataloger |
| fontconfig | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| fontconfig-config | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-6 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonttools | 4.63.0 | MIT | python-installed-package-cataloger |
| form_urlencoded | 1.2.2 |  | cargo-auditable-binary-cataloger |
| form_urlencoded | 1.2.2 |  | cargo-auditable-binary-cataloger |
| fpdf2 | 2.8.7 | LGPL-3.0-only | python-installed-package-cataloger |
| frozenlist | 1.8.0 | Apache-2.0 | python-installed-package-cataloger |
| fs-err | 3.3.0 |  | cargo-auditable-binary-cataloger |
| fs-err | 3.3.0 |  | cargo-auditable-binary-cataloger |
| fsspec | 2025.3.0 | BSD-3-Clause | python-installed-package-cataloger |
| ftfy | 6.3.1 | Apache-2.0 | python-installed-package-cataloger |
| futures | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-channel | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-channel | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-core | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-core | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-executor | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-executor | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-io | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-io | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-lite | 2.6.1 |  | cargo-auditable-binary-cataloger |
| futures-lite | 2.6.1 |  | cargo-auditable-binary-cataloger |
| futures-sink | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-sink | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-task | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-task | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-util | 0.3.32 |  | cargo-auditable-binary-cataloger |
| futures-util | 0.3.32 |  | cargo-auditable-binary-cataloger |
| g++ | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| g++-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| gcc-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| generic-array | 0.14.7 |  | cargo-auditable-binary-cataloger |
| generic-array | 0.14.7 |  | cargo-auditable-binary-cataloger |
| getrandom | 0.2.16 |  | cargo-auditable-binary-cataloger |
| getrandom | 0.2.16 |  | cargo-auditable-binary-cataloger |
| getrandom | 0.3.3 |  | cargo-auditable-binary-cataloger |
| getrandom | 0.3.3 |  | cargo-auditable-binary-cataloger |
| getrandom | 0.4.1 |  | cargo-auditable-binary-cataloger |
| getrandom | 0.4.1 |  | cargo-auditable-binary-cataloger |
| git | 1:2.39.5-0+deb12u3 | Apache-2.0, BSD-3-Clause, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| git-man | 1:2.39.5-0+deb12u3 | Apache-2.0, BSD-3-Clause, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| gitdb | 4.0.12 |  | python-installed-package-cataloger |
| gitpython | 3.1.50 | BSD-3-Clause | python-installed-package-cataloger |
| glob | 0.3.3 |  | cargo-auditable-binary-cataloger |
| glob | 0.3.3 |  | cargo-auditable-binary-cataloger |
| globset | 0.4.18 |  | cargo-auditable-binary-cataloger |
| globset | 0.4.18 |  | cargo-auditable-binary-cataloger |
| globwalk | 0.9.1 |  | cargo-auditable-binary-cataloger |
| globwalk | 0.9.1 |  | cargo-auditable-binary-cataloger |
| goblin | 0.10.7 |  | cargo-auditable-binary-cataloger |
| goblin | 0.10.7 |  | cargo-auditable-binary-cataloger |
| google-api-core | 2.31.0 |  | python-installed-package-cataloger |
| google-api-python-client | 2.197.0 |  | python-installed-package-cataloger |
| google-auth | 2.55.1 |  | python-installed-package-cataloger |
| google-auth-httplib2 | 0.4.0 |  | python-installed-package-cataloger |
| google-auth-oauthlib | 1.4.0 |  | python-installed-package-cataloger |
| google-cloud-core | 2.6.0 |  | python-installed-package-cataloger |
| google-cloud-storage | 3.9.0 |  | python-installed-package-cataloger |
| google-crc32c | 1.8.0 |  | python-installed-package-cataloger |
| google-genai | 1.66.0 | Apache-2.0 | python-installed-package-cataloger |
| google-resumable-media | 2.10.0 |  | python-installed-package-cataloger |
| googleapis-common-protos | 1.75.0 |  | python-installed-package-cataloger |
| gpgv | 2.2.40-1.1+deb12u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| greenlet | 3.5.3 | MIT AND PSF-2.0 | python-installed-package-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| grpcio | 1.78.0 | Apache-2.0 | python-installed-package-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| h11 | 0.16.0 | MIT | python-installed-package-cataloger |
| h2 | 0.4.14 |  | cargo-auditable-binary-cataloger |
| h2 | 0.4.14 |  | cargo-auditable-binary-cataloger |
| h2 | 4.3.0 | MIT | python-installed-package-cataloger |
| hashbrown | 0.14.5 |  | cargo-auditable-binary-cataloger |
| hashbrown | 0.14.5 |  | cargo-auditable-binary-cataloger |
| hashbrown | 0.15.5 |  | cargo-auditable-binary-cataloger |
| hashbrown | 0.15.5 |  | cargo-auditable-binary-cataloger |
| hashbrown | 0.17.1 |  | cargo-auditable-binary-cataloger |
| hashbrown | 0.17.1 |  | cargo-auditable-binary-cataloger |
| hex | 0.4.3 |  | cargo-auditable-binary-cataloger |
| hex | 0.4.3 |  | cargo-auditable-binary-cataloger |
| hf-xet | 1.5.1 | Apache-2.0 | python-installed-package-cataloger |
| hkdf | 0.12.4 |  | cargo-auditable-binary-cataloger |
| hkdf | 0.12.4 |  | cargo-auditable-binary-cataloger |
| hmac | 0.12.1 |  | cargo-auditable-binary-cataloger |
| hmac | 0.12.1 |  | cargo-auditable-binary-cataloger |
| homedir | 0.3.6 |  | cargo-auditable-binary-cataloger |
| homedir | 0.3.6 |  | cargo-auditable-binary-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| hpack | 4.2.0 | MIT | python-installed-package-cataloger |
| html-escape | 0.2.13 |  | cargo-auditable-binary-cataloger |
| html-escape | 0.2.13 |  | cargo-auditable-binary-cataloger |
| html5lib | 1.1 |  | python-installed-package-cataloger |
| http | 1.4.1 |  | cargo-auditable-binary-cataloger |
| http | 1.4.1 |  | cargo-auditable-binary-cataloger |
| http-body | 1.0.1 |  | cargo-auditable-binary-cataloger |
| http-body | 1.0.1 |  | cargo-auditable-binary-cataloger |
| http-body-util | 0.1.3 |  | cargo-auditable-binary-cataloger |
| http-body-util | 0.1.3 |  | cargo-auditable-binary-cataloger |
| http-content-range | 0.2.4 |  | cargo-auditable-binary-cataloger |
| http-content-range | 0.2.4 |  | cargo-auditable-binary-cataloger |
| httparse | 1.10.1 |  | cargo-auditable-binary-cataloger |
| httparse | 1.10.1 |  | cargo-auditable-binary-cataloger |
| httpcore | 1.0.9 | BSD-3-Clause | python-installed-package-cataloger |
| httpdate | 1.0.3 |  | cargo-auditable-binary-cataloger |
| httpdate | 1.0.3 |  | cargo-auditable-binary-cataloger |
| httplib2 | 0.32.0 | MIT | python-installed-package-cataloger |
| httptools | 0.8.0 | MIT | python-installed-package-cataloger |
| httpx | 0.28.1 | BSD-3-Clause | python-installed-package-cataloger |
| httpx-sse | 0.4.3 | MIT | python-installed-package-cataloger |
| huggingface-hub | 1.21.0 | Apache-2.0 | python-installed-package-cataloger |
| hyper | 1.10.1 |  | cargo-auditable-binary-cataloger |
| hyper | 1.10.1 |  | cargo-auditable-binary-cataloger |
| hyper-rustls | 0.27.7 |  | cargo-auditable-binary-cataloger |
| hyper-rustls | 0.27.7 |  | cargo-auditable-binary-cataloger |
| hyper-util | 0.1.20 |  | cargo-auditable-binary-cataloger |
| hyper-util | 0.1.20 |  | cargo-auditable-binary-cataloger |
| hyperframe | 6.1.0 | MIT | python-installed-package-cataloger |
| icu_collections | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_collections | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_locale_core | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_locale_core | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_normalizer | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_normalizer | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_normalizer_data | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_normalizer_data | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_properties | 2.1.2 |  | cargo-auditable-binary-cataloger |
| icu_properties | 2.1.2 |  | cargo-auditable-binary-cataloger |
| icu_properties_data | 2.1.2 |  | cargo-auditable-binary-cataloger |
| icu_properties_data | 2.1.2 |  | cargo-auditable-binary-cataloger |
| icu_provider | 2.1.1 |  | cargo-auditable-binary-cataloger |
| icu_provider | 2.1.1 |  | cargo-auditable-binary-cataloger |
| idna | 1.1.0 |  | cargo-auditable-binary-cataloger |
| idna | 1.1.0 |  | cargo-auditable-binary-cataloger |
| idna | 3.18 | BSD-3-Clause | python-installed-package-cataloger |
| idna_adapter | 1.2.1 |  | cargo-auditable-binary-cataloger |
| idna_adapter | 1.2.1 |  | cargo-auditable-binary-cataloger |
| ignore | 0.4.26 |  | cargo-auditable-binary-cataloger |
| ignore | 0.4.26 |  | cargo-auditable-binary-cataloger |
| image | 0.25.10 |  | cargo-auditable-binary-cataloger |
| image | 0.25.10 |  | cargo-auditable-binary-cataloger |
| importlib-metadata | 8.0.0 | Apache-2.0 | python-installed-package-cataloger |
| importlib-resources | 7.1.0 | Apache-2.0 | python-installed-package-cataloger |
| indexmap | 2.14.0 |  | cargo-auditable-binary-cataloger |
| indexmap | 2.14.0 |  | cargo-auditable-binary-cataloger |
| indicatif | 0.18.4 |  | cargo-auditable-binary-cataloger |
| indicatif | 0.18.4 |  | cargo-auditable-binary-cataloger |
| indoc | 2.0.7 |  | cargo-auditable-binary-cataloger |
| indoc | 2.0.7 |  | cargo-auditable-binary-cataloger |
| inflect | 7.3.1 | MIT | python-installed-package-cataloger |
| iniconfig | 2.3.0 | MIT | python-installed-package-cataloger |
| init-system-helpers | 1.65.2+deb12u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| inout | 0.1.4 |  | cargo-auditable-binary-cataloger |
| inout | 0.1.4 |  | cargo-auditable-binary-cataloger |
| insta | 1.48.0 |  | cargo-auditable-binary-cataloger |
| insta | 1.48.0 |  | cargo-auditable-binary-cataloger |
| installer | 0.7.0 | MIT | python-installed-package-cataloger |
| ipnet | 2.12.0 |  | cargo-auditable-binary-cataloger |
| ipnet | 2.12.0 |  | cargo-auditable-binary-cataloger |
| iri-string | 0.7.10 |  | cargo-auditable-binary-cataloger |
| iri-string | 0.7.10 |  | cargo-auditable-binary-cataloger |
| is-docker | 0.2.0 |  | cargo-auditable-binary-cataloger |
| is-docker | 0.2.0 |  | cargo-auditable-binary-cataloger |
| is-wsl | 0.4.0 |  | cargo-auditable-binary-cataloger |
| is-wsl | 0.4.0 |  | cargo-auditable-binary-cataloger |
| is_ci | 1.2.0 |  | cargo-auditable-binary-cataloger |
| is_ci | 1.2.0 |  | cargo-auditable-binary-cataloger |
| is_terminal_polyfill | 1.70.2 |  | cargo-auditable-binary-cataloger |
| is_terminal_polyfill | 1.70.2 |  | cargo-auditable-binary-cataloger |
| isodate | 0.7.2 | BSD-3-Clause | python-installed-package-cataloger |
| itertools | 0.14.0 |  | cargo-auditable-binary-cataloger |
| itertools | 0.14.0 |  | cargo-auditable-binary-cataloger |
| itoa | 1.0.17 |  | cargo-auditable-binary-cataloger |
| itoa | 1.0.17 |  | cargo-auditable-binary-cataloger |
| itsdangerous | 2.2.0 | BSD-3-Clause | python-installed-package-cataloger |
| jaraco-collections | 5.1.0 | MIT | python-installed-package-cataloger |
| jaraco-context | 5.3.0 | MIT | python-installed-package-cataloger |
| jaraco-functools | 4.0.1 | MIT | python-installed-package-cataloger |
| jaraco-text | 3.12.1 | MIT | python-installed-package-cataloger |
| jiff | 0.2.28 |  | cargo-auditable-binary-cataloger |
| jiff | 0.2.28 |  | cargo-auditable-binary-cataloger |
| jinja2 | 3.1.6 |  | python-installed-package-cataloger |
| jiter | 0.16.0 | MIT | python-installed-package-cataloger |
| jmespath | 1.1.0 | MIT | python-installed-package-cataloger |
| joblib | 1.5.3 | BSD-3-Clause | python-installed-package-cataloger |
| jobserver | 0.1.34 |  | cargo-auditable-binary-cataloger |
| jobserver | 0.1.34 |  | cargo-auditable-binary-cataloger |
| joserfc | 1.7.2 | BSD-3-Clause | python-installed-package-cataloger |
| jq | 1.6-2.1+deb12u1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| jsonpatch | 1.33 |  | python-installed-package-cataloger |
| jsonpointer | 3.1.1 |  | python-installed-package-cataloger |
| jsonschema | 4.26.0 | MIT | python-installed-package-cataloger |
| jsonschema-specifications | 2025.9.1 | MIT | python-installed-package-cataloger |
| jsonwebtoken | 10.3.0 |  | cargo-auditable-binary-cataloger |
| jsonwebtoken | 10.3.0 |  | cargo-auditable-binary-cataloger |
| kubernetes | 36.0.2 |  | python-installed-package-cataloger |
| langchain | 1.2.10 | MIT | python-installed-package-cataloger |
| langchain-classic | 1.0.7 | MIT | python-installed-package-cataloger |
| langchain-community | 0.4.2 | MIT | python-installed-package-cataloger |
| langchain-core | 1.4.8 | MIT | python-installed-package-cataloger |
| langchain-protocol | 0.0.18 | MIT | python-installed-package-cataloger |
| langchain-text-splitters | 1.1.2 | MIT | python-installed-package-cataloger |
| langdetect | 1.0.9 | MIT | python-installed-package-cataloger |
| langgraph | 1.0.10 | MIT | python-installed-package-cataloger |
| langgraph-checkpoint | 4.1.1 | MIT | python-installed-package-cataloger |
| langgraph-prebuilt | 1.0.13 | MIT | python-installed-package-cataloger |
| langgraph-sdk | 0.3.15 | MIT | python-installed-package-cataloger |
| langsmith | 0.9.3 | MIT | python-installed-package-cataloger |
| lazy_static | 1.5.0 |  | cargo-auditable-binary-cataloger |
| lazy_static | 1.5.0 |  | cargo-auditable-binary-cataloger |
| ldap3 | 2.9.1 |  | python-installed-package-cataloger |
| libacl1 | 2.3.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaom3 | 3.6.0-1+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, ISC | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libasan8 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libasound2 | 1.2.8-1+b1 | LGPL-2.1-only | dpkg-db-cataloger |
| libasound2-data | 1.2.8-1 | LGPL-2.1-only | dpkg-db-cataloger |
| libass9 | 1:0.17.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC | dpkg-db-cataloger |
| libasyncns0 | 0.8-6+b3 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libatomic1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavc1394-0 | 0.5.4-5 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libavcodec59 | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libavdevice59 | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libavfilter8 | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libavformat59 | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libavutil57 | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libbinutils | 2.40-2 |  | dpkg-db-cataloger |
| libblas3 | 3.11.0-2 | BSD-3-Clause | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbluray2 | 1:1.3.4-1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.0 | dpkg-db-cataloger |
| libbrotli1 | 1.0.9-2+b6 | MIT | dpkg-db-cataloger |
| libbs2b0 | 3.1.0+dfsg-7 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libbsd0 | 0.11.7-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC, libutil-David-Nugent | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc | 0.2.186 |  | cargo-auditable-binary-cataloger |
| libc | 0.2.186 |  | cargo-auditable-binary-cataloger |
| libc-bin | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc-dev-bin | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6-dev | 2.36-9+deb12u14 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcaca0 | 0.99.beta20-3 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libcairo-gobject2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4+deb12u3+b1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcc1-0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libcdio-cdda2 | 10.2+2.0.1-1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libcdio-paranoia2 | 10.2+2.0.1-1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libcdio19 | 2.1.0-4 | GFDL-1.2-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only | dpkg-db-cataloger |
| libchromaprint1 | 1.5.1-2+b1 | BSD-3-Clause, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcjson1 | 1.7.15-1+deb12u4 | Apache-2.0, MIT | dpkg-db-cataloger |
| libcodec2-1.0 | 1.0.5-1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt-dev | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libctf-nobfd0 | 2.40-2 |  | dpkg-db-cataloger |
| libctf0 | 2.40-2 |  | dpkg-db-cataloger |
| libcurl3-gnutls | 7.88.1-10+deb12u14 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4 | 7.88.1-10+deb12u14 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libdatrie1 | 0.2.13-2+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libdav1d6 | 1.0.0-2+deb12u1 | BSD-2-Clause, ISC | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdbus-1-3 | 1.14.10-1~deb12u1 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libdc1394-25 | 2.2.6-4 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libdebconfclient0 | 0.270 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdecor-0-0 | 0.1.1-2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libdeflate0 | 1.14-1 |  | dpkg-db-cataloger |
| libdpkg-perl | 1.21.23 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdrm-amdgpu1 | 2.4.114-1+b1 |  | dpkg-db-cataloger |
| libdrm-common | 2.4.114-1 |  | dpkg-db-cataloger |
| libdrm-intel1 | 2.4.114-1+b1 |  | dpkg-db-cataloger |
| libdrm-nouveau2 | 2.4.114-1+b1 |  | dpkg-db-cataloger |
| libdrm-radeon1 | 2.4.114-1+b1 |  | dpkg-db-cataloger |
| libdrm2 | 2.4.114-1+b1 |  | dpkg-db-cataloger |
| libedit2 | 3.1-20221030-2 | BSD-3-Clause | dpkg-db-cataloger |
| libelf1 | 0.188-2.1 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libepoxy0 | 1.5.10-1 |  | dpkg-db-cataloger |
| liberror-perl | 0.17029-2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libexpat1 | 2.5.0-1+deb12u2 | MIT | dpkg-db-cataloger |
| libexpat1-dev | 2.5.0-1+deb12u2 | MIT | dpkg-db-cataloger |
| libext2fs2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi8 | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libflac12 | 1.4.2+ds-2 | BSD-3-Clause, GFDL-1.1-or-later, GFDL-1.2-only, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libflite1 | 2.2-5 | GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libfontconfig1 | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| libfreetype6 | 2.12.1+dfsg-5+deb12u4 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, Zlib | dpkg-db-cataloger |
| libfribidi0 | 1.0.8-2.1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgbm1 | 22.3.6-1+deb12u1 | Apache-2.0, BSD-2-Clause, MIT | dpkg-db-cataloger |
| libgcc-12-dev | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcc-s1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.1-3+deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm-compat4 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdk-pixbuf-2.0-0 | 2.42.10+dfsg-1+deb12u4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf2.0-common | 2.42.10+dfsg-1+deb12u4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgfortran5 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgl1 | 1.6.0-1 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libgl1-mesa-dri | 22.3.6-1+deb12u1 | Apache-2.0, BSD-2-Clause, MIT | dpkg-db-cataloger |
| libglapi-mesa | 22.3.6-1+deb12u1 | Apache-2.0, BSD-2-Clause, MIT | dpkg-db-cataloger |
| libglib2.0-0 | 2.74.6-2+deb12u9 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglvnd0 | 1.6.0-1 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libglx-mesa0 | 22.3.6-1+deb12u1 | Apache-2.0, BSD-2-Clause, MIT | dpkg-db-cataloger |
| libglx0 | 1.6.0-1 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libgme0 | 0.6.3-6 | LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u7 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgprofng0 | 2.40-2 |  | dpkg-db-cataloger |
| libgraphite2-3 | 1.3.14-1 | GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libgsm1 | 1.0.22-1 | TU-Berlin-2.0 | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libharfbuzz0b | 6.0.0+dfsg-3 | Apache-2.0, CC0-1.0, FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, MIT, OFL-1.1 | dpkg-db-cataloger |
| libhogweed6 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libhwy1 | 1.0.3-3+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libice6 | 2:1.0.10-1 |  | dpkg-db-cataloger |
| libicu72 | 72.1-3+deb12u1 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn2-0 | 2.3.3-1+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libiec61883-0 | 1.2.0-6+b1 | LGPL-2.1-only | dpkg-db-cataloger |
| libisl23 | 0.25-1.1 | BSD-2-Clause, LGPL-2.0-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libitm1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libjack-jackd2-0 | 1.9.21~dfsg-3 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libjansson4 | 2.14-2 |  | dpkg-db-cataloger |
| libjbig0 | 2.1-6.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libjpeg62-turbo | 1:2.1.5-2 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libjq1 | 1.6-2.1+deb12u1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| libjs-jquery | 3.6.1+dfsg+~3.5.14-1 |  | dpkg-db-cataloger |
| libjs-sphinxdoc | 5.3.0-4 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| libjs-underscore | 1.13.4~dfsg+~1.11.4-3 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libjxl0.7 | 0.7.0-10+deb12u1 |  | dpkg-db-cataloger |
| libk5crypto3 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.20.1-2+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| liblapack3 | 3.11.0-2 | BSD-3-Clause | dpkg-db-cataloger |
| liblcms2-2 | 2.14-2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| libldap-2.5-0 | 2.5.13+dfsg-5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| liblerc4 | 4.0.0+ds-2 | Apache-2.0 | dpkg-db-cataloger |
| liblilv-0-0 | 0.24.14-1 | BSD-3-Clause, ISC | dpkg-db-cataloger |
| libllvm15 | 1:15.0.6-4+b1 | Apache-2.0, BSD-3-Clause, BSD-3-Clause, MIT | dpkg-db-cataloger |
| liblsan0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| liblua5.3-0 | 5.3.6-2 |  | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libm | 0.2.16 |  | cargo-auditable-binary-cataloger |
| libm | 0.2.16 |  | cargo-auditable-binary-cataloger |
| libmariadb-dev | 1:10.11.14-0+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmariadb3 | 1:10.11.14-0+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmbedcrypto7 | 2.28.3-1 | Apache-2.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmfx1 | 22.5.4-1 | Apache-2.0, BSD-3-Clause, MIT, NTP | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmp3lame0 | 3.100-6 | BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmpc3 | 1.3.1-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libmpfr6 | 4.2.0-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libmpg123-0 | 1.31.2-1+deb12u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libmysofa1 | 1.3.1~dfsg0-1 | BSD-3-Clause, CC-BY-4.0, CC-BY-SA-3.0 | dpkg-db-cataloger |
| libncursesw6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.52.0-1+deb12u3 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnorm1 | 1.5.9+dfsg-2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause-UC | dpkg-db-cataloger |
| libnsl-dev | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnuma1 | 2.0.16-1 |  | dpkg-db-cataloger |
| libogg0 | 1.3.5-3 | BSD-3-Clause | dpkg-db-cataloger |
| libonig5 | 6.9.8-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libopenal-data | 1:1.19.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libopenal1 | 1:1.19.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.0-2+deb12u3 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libopenmpt0 | 0.6.9-1 | BSD-3-Clause, BSL-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, X11 | dpkg-db-cataloger |
| libopus0 | 1.3.1-3 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u2 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpango-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangocairo-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangoft2-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpciaccess0 | 0.17-2 |  | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libperl5.36 | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| libpgm-5.3-0 | 5.3.128~dfsg-2 | BSD-3-Clause, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libpixman-1-0 | 0.42.2-1 |  | dpkg-db-cataloger |
| libplacebo208 | 4.208.0-3 | LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libpng16-16 | 1.6.39-2+deb12u5 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpocketsphinx3 | 0.8+5prealpha+1-15 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libpostproc56 | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libpsl5 | 0.21.2-1 | MIT | dpkg-db-cataloger |
| libpulse0 | 16.1+dfsg1-2+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpython3-dev | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| libpython3-stdlib | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| libpython3.11 | 3.11.2-6+deb12u7 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-dev | 3.11.2-6+deb12u7 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-minimal | 3.11.2-6+deb12u7 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-stdlib | 3.11.2-6+deb12u7 | GPL-2.0-only | dpkg-db-cataloger |
| libquadmath0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| librabbitmq4 | 0.11.0-1+deb12u1 |  | dpkg-db-cataloger |
| librav1e0 | 0.5.1-6 | BSD-2-Clause, BSD-2-Clause, ISC | dpkg-db-cataloger |
| libraw1394-11 | 2.1.2-2 |  | dpkg-db-cataloger |
| libreadline8 | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| librist4 | 0.2.7+dfsg-1 | BSD-2-Clause, ISC | dpkg-db-cataloger |
| librsvg2-2 | 2.54.7+dfsg-1~deb12u1 | 0BSD, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, FSFAP, LGPL-2.0-only, LGPL-2.0-or-later, MPL-2.0, OFL-1.1, Unlicense, Zlib | dpkg-db-cataloger |
| librtmp1 | 2.4+20151223.gitfa8646d.1-2+b2 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| librubberband2 | 3.1.2+dfsg0-1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Zlib | dpkg-db-cataloger |
| libsamplerate0 | 0.2.2-3 | BSD-2-Clause, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libsasl2-2 | 2.1.28+dfsg-10 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.28+dfsg-10 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libsdl2-2.0-0 | 2.26.5+dfsg-1 | Apache-2.0, BSD-3-Clause, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT-open-group, SunPro | dpkg-db-cataloger |
| libseccomp2 | 2.5.4-1+deb12u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.4-1 |  | dpkg-db-cataloger |
| libsemanage2 | 3.4-1+b5 |  | dpkg-db-cataloger |
| libsensors-config | 1:3.6.0-7.1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsensors5 | 1:3.6.0-7.1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsepol2 | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libserd-0-0 | 0.30.16-1 | ISC | dpkg-db-cataloger |
| libshine3 | 3.1.1-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only | dpkg-db-cataloger |
| libslang2 | 2.3.3-3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsm6 | 2:1.2.3-1 |  | dpkg-db-cataloger |
| libsmartcols1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsnappy1v5 | 1.1.9-3 | BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, MIT | dpkg-db-cataloger |
| libsndfile1 | 1.2.0-1+deb12u1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, NTP | dpkg-db-cataloger |
| libsndio7.0 | 1.9.0-0.3+b2 | ISC | dpkg-db-cataloger |
| libsodium23 | 1.0.18-1+deb12u1 | BSD-2-Clause, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libsord-0-0 | 0.16.14+git221008-1 | ISC | dpkg-db-cataloger |
| libsoxr0 | 0.1.3-4 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libspeex1 | 1.2.1-2 | BSD-3-Clause, GFDL-1.1-or-later, GFDL-1.2-only, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libsphinxbase3 | 0.8+5prealpha+1-16 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2+deb12u2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsratom-0-0 | 0.6.14-1 | ISC | dpkg-db-cataloger |
| libsrt1.5-gnutls | 1.5.1-1+deb12u1 | BSD-3-Clause, LGPL-2.1-only, LGPL-2.1-or-later, MPL-2.0, Zlib, Unlicense | dpkg-db-cataloger |
| libss2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssh-gcrypt-4 | 0.10.6-0+deb12u2 | BSD-2-Clause, BSD-3-Clause, LGPL-2.1-only | dpkg-db-cataloger |
| libssh2-1 | 1.10.0-3+b1 |  | dpkg-db-cataloger |
| libssl-dev | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libssl3 | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++-12-dev | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsvtav1enc1 | 1.4.1+dfsg-1 | BSD-2-Clause, BSD-3-Clause-Clear, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libswresample4 | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libswscale6 | 7:5.1.9-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsystemd0 | 252.39-1~deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2+deb12u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libthai-data | 0.1.29-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libthai0 | 0.1.29-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtheora0 | 1.1.1+dfsg.1-16.1+deb12u1 | BSD-3-Clause | dpkg-db-cataloger |
| libtiff6 | 4.5.0-6+deb12u4 |  | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc-dev | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtsan2 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libtwolame0 | 0.4.0-2 | LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libubsan1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libudev1 | 252.39-1~deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libudfread0 | 1.1.2-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libusb-1.0-0 | 2:1.0.26-1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libva-drm2 | 2.17.0-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libva-x11-2 | 2.17.0-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libva2 | 2.17.0-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libvdpau1 | 1.5-2 |  | dpkg-db-cataloger |
| libvidstab1.1 | 1.1.0-2+b1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libvorbis0a | 1.3.7-1 | BSD-3-Clause | dpkg-db-cataloger |
| libvorbisenc2 | 1.3.7-1 | BSD-3-Clause | dpkg-db-cataloger |
| libvorbisfile3 | 1.3.7-1 | BSD-3-Clause | dpkg-db-cataloger |
| libvpx7 | 1.12.0-1+deb12u5 | BSD-3-Clause, ISC | dpkg-db-cataloger |
| libvulkan1 | 1.3.239.0-1 | Apache-2.0, MIT | dpkg-db-cataloger |
| libwayland-client0 | 1.21.0-1 | X11 | dpkg-db-cataloger |
| libwayland-cursor0 | 1.21.0-1 | X11 | dpkg-db-cataloger |
| libwayland-egl1 | 1.21.0-1 | X11 | dpkg-db-cataloger |
| libwayland-server0 | 1.21.0-1 | X11 | dpkg-db-cataloger |
| libwebp7 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebpmux3 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libx11-6 | 2:1.8.4-2+deb12u2 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.8.4-2+deb12u2 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-xcb1 | 2:1.8.4-2+deb12u2 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx264-164 | 2:0.164.3095+gitbaee400-3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.1-or-later | dpkg-db-cataloger |
| libx265-199 | 3.5-2+b1 | GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libxau6 | 1:1.0.9-1 |  | dpkg-db-cataloger |
| libxcb-dri2-0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-dri3-0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-glx0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-present0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-randr0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-render0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-shape0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-shm0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-sync1 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb-xfixes0 | 1.15-1 |  | dpkg-db-cataloger |
| libxcb1 | 1.15-1 |  | dpkg-db-cataloger |
| libxcursor1 | 1:1.2.1-1 | HPND-sell-variant | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.2-3 |  | dpkg-db-cataloger |
| libxext6 | 2:1.3.4-1+b1 |  | dpkg-db-cataloger |
| libxfixes3 | 1:6.0.0-2 | HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxi6 | 2:1.8-1+b1 |  | dpkg-db-cataloger |
| libxkbcommon0 | 1.5.0-1 |  | dpkg-db-cataloger |
| libxml2 | 2.9.14+dfsg-1.3~deb12u5 | ISC | dpkg-db-cataloger |
| libxrandr2 | 2:1.5.2-2+b1 | HPND-sell-variant | dpkg-db-cataloger |
| libxrender1 | 1:0.9.10-1.1 | HPND-sell-variant | dpkg-db-cataloger |
| libxshmfence1 | 1.3-1 | HPND-sell-variant | dpkg-db-cataloger |
| libxss1 | 1:1.2.3-1 | MIT | dpkg-db-cataloger |
| libxv1 | 2:1.0.11-1.1 | HPND, HPND-sell-variant | dpkg-db-cataloger |
| libxvidcore4 | 2:1.3.7-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libxxf86vm1 | 1:1.1.4-1+b2 | MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libyaml-0-2 | 0.2.5-1 |  | dpkg-db-cataloger |
| libz3-4 | 4.8.12-3.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libzimg2 | 3.0.4+ds1-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libzmq5 | 4.3.4-6 | LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libzstd1 | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| libzvbi-common | 0.2.41-1+deb12u1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libzvbi0 | 0.2.41-1+deb12u1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| linux-libc-dev | 6.1.174-1 | BSD-2-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| linux-raw-sys | 0.12.1 |  | cargo-auditable-binary-cataloger |
| linux-raw-sys | 0.12.1 |  | cargo-auditable-binary-cataloger |
| linux-raw-sys | 0.4.15 |  | cargo-auditable-binary-cataloger |
| linux-raw-sys | 0.4.15 |  | cargo-auditable-binary-cataloger |
| litemap | 0.8.1 |  | cargo-auditable-binary-cataloger |
| litemap | 0.8.1 |  | cargo-auditable-binary-cataloger |
| llvmlite | 0.47.0 | BSD-2-Clause AND Apache-2.0 WITH LLVM-exception | python-installed-package-cataloger |
| lock_api | 0.4.14 |  | cargo-auditable-binary-cataloger |
| lock_api | 0.4.14 |  | cargo-auditable-binary-cataloger |
| log | 0.4.29 |  | cargo-auditable-binary-cataloger |
| log | 0.4.29 |  | cargo-auditable-binary-cataloger |
| login | 1:4.13+dfsg1-1+deb12u2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| loguru | 0.7.3 |  | python-installed-package-cataloger |
| lru-slab | 0.1.2 |  | cargo-auditable-binary-cataloger |
| lru-slab | 0.1.2 |  | cargo-auditable-binary-cataloger |
| lxml | 6.1.1 | BSD-3-Clause | python-installed-package-cataloger |
| lzma-sys | 0.1.20 |  | cargo-auditable-binary-cataloger |
| lzma-sys | 0.1.20 |  | cargo-auditable-binary-cataloger |
| mailparse | 0.16.1 |  | cargo-auditable-binary-cataloger |
| mailparse | 0.16.1 |  | cargo-auditable-binary-cataloger |
| make | 4.3-4.1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| mako | 1.3.12 | MIT | python-installed-package-cataloger |
| mariadb-common | 1:10.11.14-0+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| markdown | 3.10.2 | BSD-3-Clause | python-installed-package-cataloger |
| markdown-it-py | 4.2.0 |  | python-installed-package-cataloger |
| markupsafe | 3.0.3 | BSD-3-Clause | python-installed-package-cataloger |
| matchers | 0.2.0 |  | cargo-auditable-binary-cataloger |
| matchers | 0.2.0 |  | cargo-auditable-binary-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| mcp | 1.27.2 | MIT | python-installed-package-cataloger |
| md-5 | 0.10.6 |  | cargo-auditable-binary-cataloger |
| md-5 | 0.10.6 |  | cargo-auditable-binary-cataloger |
| mdurl | 0.1.2 | MIT | python-installed-package-cataloger |
| media-types | 10.0.0 |  | dpkg-db-cataloger |
| memchr | 2.8.2 |  | cargo-auditable-binary-cataloger |
| memchr | 2.8.2 |  | cargo-auditable-binary-cataloger |
| memmap2 | 0.9.10 |  | cargo-auditable-binary-cataloger |
| memmap2 | 0.9.10 |  | cargo-auditable-binary-cataloger |
| miette | 7.6.0 |  | cargo-auditable-binary-cataloger |
| miette | 7.6.0 |  | cargo-auditable-binary-cataloger |
| mime | 0.3.17 |  | cargo-auditable-binary-cataloger |
| mime | 0.3.17 |  | cargo-auditable-binary-cataloger |
| mime_guess | 2.0.5 |  | cargo-auditable-binary-cataloger |
| mime_guess | 2.0.5 |  | cargo-auditable-binary-cataloger |
| minimal-lexical | 0.2.1 |  | cargo-auditable-binary-cataloger |
| minimal-lexical | 0.2.1 |  | cargo-auditable-binary-cataloger |
| miniz_oxide | 0.8.9 |  | cargo-auditable-binary-cataloger |
| miniz_oxide | 0.8.9 |  | cargo-auditable-binary-cataloger |
| mio | 1.2.0 |  | cargo-auditable-binary-cataloger |
| mio | 1.2.0 |  | cargo-auditable-binary-cataloger |
| mmh3 | 5.2.1 | MIT | python-installed-package-cataloger |
| more-itertools | 10.3.0 | MIT | python-installed-package-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| moxcms | 0.8.1 |  | cargo-auditable-binary-cataloger |
| moxcms | 0.8.1 |  | cargo-auditable-binary-cataloger |
| mpmath | 1.3.0 |  | python-installed-package-cataloger |
| msal | 1.37.0 | MIT | python-installed-package-cataloger |
| msal-extensions | 1.3.1 |  | python-installed-package-cataloger |
| msoffcrypto-tool | 6.0.0 | MIT | python-installed-package-cataloger |
| multidict | 6.7.1 |  | python-installed-package-cataloger |
| multiprocess | 0.70.16 | BSD-3-Clause | python-installed-package-cataloger |
| munge | 0.4.7 |  | cargo-auditable-binary-cataloger |
| munge | 0.4.7 |  | cargo-auditable-binary-cataloger |
| murmurhash | 1.0.15 | MIT | python-installed-package-cataloger |
| mypy-extensions | 1.1.0 | MIT | python-installed-package-cataloger |
| mysql-common | 5.8+1.1.0 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| narwhals | 2.22.1 | MIT | python-installed-package-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| netcat-openbsd | 1.219-1 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| networkx | 3.6.1 | BSD-3-Clause | python-installed-package-cataloger |
| ninja | 1.13.0 |  | python-installed-package-cataloger |
| nix | 0.30.1 |  | cargo-auditable-binary-cataloger |
| nix | 0.30.1 |  | cargo-auditable-binary-cataloger |
| nix | 0.31.3 |  | cargo-auditable-binary-cataloger |
| nix | 0.31.3 |  | cargo-auditable-binary-cataloger |
| nltk | 3.9.4 |  | python-installed-package-cataloger |
| node | 24.15.0 |  | binary-classifier-cataloger |
| nom | 7.1.3 |  | cargo-auditable-binary-cataloger |
| nom | 7.1.3 |  | cargo-auditable-binary-cataloger |
| normalize-line-endings | 0.3.0 |  | cargo-auditable-binary-cataloger |
| normalize-line-endings | 0.3.0 |  | cargo-auditable-binary-cataloger |
| nu-ansi-term | 0.50.3 |  | cargo-auditable-binary-cataloger |
| nu-ansi-term | 0.50.3 |  | cargo-auditable-binary-cataloger |
| num | 0.4.3 |  | cargo-auditable-binary-cataloger |
| num | 0.4.3 |  | cargo-auditable-binary-cataloger |
| num-bigint | 0.4.6 |  | cargo-auditable-binary-cataloger |
| num-bigint | 0.4.6 |  | cargo-auditable-binary-cataloger |
| num-bigint-dig | 0.8.6 |  | cargo-auditable-binary-cataloger |
| num-bigint-dig | 0.8.6 |  | cargo-auditable-binary-cataloger |
| num-complex | 0.4.6 |  | cargo-auditable-binary-cataloger |
| num-complex | 0.4.6 |  | cargo-auditable-binary-cataloger |
| num-conv | 0.2.0 |  | cargo-auditable-binary-cataloger |
| num-conv | 0.2.0 |  | cargo-auditable-binary-cataloger |
| num-integer | 0.1.46 |  | cargo-auditable-binary-cataloger |
| num-integer | 0.1.46 |  | cargo-auditable-binary-cataloger |
| num-iter | 0.1.45 |  | cargo-auditable-binary-cataloger |
| num-iter | 0.1.45 |  | cargo-auditable-binary-cataloger |
| num-rational | 0.4.2 |  | cargo-auditable-binary-cataloger |
| num-rational | 0.4.2 |  | cargo-auditable-binary-cataloger |
| num-traits | 0.2.19 |  | cargo-auditable-binary-cataloger |
| num-traits | 0.2.19 |  | cargo-auditable-binary-cataloger |
| num_cpus | 1.17.0 |  | cargo-auditable-binary-cataloger |
| num_cpus | 1.17.0 |  | cargo-auditable-binary-cataloger |
| numba | 0.65.1 |  | python-installed-package-cataloger |
| numpy | 2.4.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | python-installed-package-cataloger |
| oauthlib | 3.3.1 | BSD-3-Clause | python-installed-package-cataloger |
| ocl-icd-libopencl1 | 2.3.1-1 | BSD-2-Clause | dpkg-db-cataloger |
| oid-registry | 0.8.1 |  | cargo-auditable-binary-cataloger |
| oid-registry | 0.8.1 |  | cargo-auditable-binary-cataloger |
| olefile | 0.47 |  | python-installed-package-cataloger |
| once_cell | 1.21.4 |  | cargo-auditable-binary-cataloger |
| once_cell | 1.21.4 |  | cargo-auditable-binary-cataloger |
| onnxruntime | 1.26.0 |  | python-installed-package-cataloger |
| open | 5.3.5 |  | cargo-auditable-binary-cataloger |
| open | 5.3.5 |  | cargo-auditable-binary-cataloger |
| open-webui | 0.10.2 |  | javascript-package-cataloger |
| openai | 2.29.0 | Apache-2.0 | python-installed-package-cataloger |
| opencv-python | 4.13.0.92 |  | python-installed-package-cataloger |
| opencv-python-headless | 4.13.0.92 |  | python-installed-package-cataloger |
| openpyxl | 3.1.5 | MIT | python-installed-package-cataloger |
| opensearch-protobufs | 1.2.0 | Apache-2.0 | python-installed-package-cataloger |
| opensearch-py | 3.2.0 | Apache-2.0 | python-installed-package-cataloger |
| openssl | 3.0.20-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| openssl-probe | 0.2.1 |  | cargo-auditable-binary-cataloger |
| openssl-probe | 0.2.1 |  | cargo-auditable-binary-cataloger |
| opentelemetry-api | 1.42.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-otlp | 1.42.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-otlp-proto-common | 1.42.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-otlp-proto-grpc | 1.42.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-otlp-proto-http | 1.42.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-aiohttp-client | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-asgi | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-fastapi | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-httpx | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-logging | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-redis | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-requests | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-sqlalchemy | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-system-metrics | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-proto | 1.42.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-sdk | 1.42.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-semantic-conventions | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-util-http | 0.63b1 | Apache-2.0 | python-installed-package-cataloger |
| option-ext | 0.2.0 |  | cargo-auditable-binary-cataloger |
| option-ext | 0.2.0 |  | cargo-auditable-binary-cataloger |
| oracledb | 3.4.2 | UPL-1.0 OR Apache-2.0 | python-installed-package-cataloger |
| ordered-float | 5.3.0 |  | cargo-auditable-binary-cataloger |
| ordered-float | 5.3.0 |  | cargo-auditable-binary-cataloger |
| ordered-multimap | 0.7.3 |  | cargo-auditable-binary-cataloger |
| ordered-multimap | 0.7.3 |  | cargo-auditable-binary-cataloger |
| ordered-stream | 0.2.0 |  | cargo-auditable-binary-cataloger |
| ordered-stream | 0.2.0 |  | cargo-auditable-binary-cataloger |
| orjson | 3.11.9 | MPL-2.0 AND (Apache-2.0 OR MIT) | python-installed-package-cataloger |
| ormsgpack | 1.12.2 | Apache-2.0 OR MIT | python-installed-package-cataloger |
| os_str_bytes | 6.6.1 |  | cargo-auditable-binary-cataloger |
| os_str_bytes | 6.6.1 |  | cargo-auditable-binary-cataloger |
| overrides | 7.7.0 |  | python-installed-package-cataloger |
| owo-colors | 4.3.0 |  | cargo-auditable-binary-cataloger |
| owo-colors | 4.3.0 |  | cargo-auditable-binary-cataloger |
| packaging | 24.2 | Apache-2.0, BSD-2-Clause | python-installed-package-cataloger |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause | python-installed-package-cataloger |
| pandas | 3.0.3 |  | python-installed-package-cataloger |
| pandoc | 2.17.1.1-2~deb12u1 | CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MS-RL | dpkg-db-cataloger |
| pandoc-data | 2.17.1.1-2~deb12u1 | CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MS-RL | dpkg-db-cataloger |
| papaya | 0.2.4 |  | cargo-auditable-binary-cataloger |
| papaya | 0.2.4 |  | cargo-auditable-binary-cataloger |
| parking | 2.2.1 |  | cargo-auditable-binary-cataloger |
| parking | 2.2.1 |  | cargo-auditable-binary-cataloger |
| parking_lot | 0.12.5 |  | cargo-auditable-binary-cataloger |
| parking_lot | 0.12.5 |  | cargo-auditable-binary-cataloger |
| parking_lot_core | 0.9.12 |  | cargo-auditable-binary-cataloger |
| parking_lot_core | 0.9.12 |  | cargo-auditable-binary-cataloger |
| passwd | 1:4.13+dfsg1-1+deb12u2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.7.6-7 |  | dpkg-db-cataloger |
| path-slash | 0.2.1 |  | cargo-auditable-binary-cataloger |
| path-slash | 0.2.1 |  | cargo-auditable-binary-cataloger |
| pathdiff | 0.2.3 |  | cargo-auditable-binary-cataloger |
| pathdiff | 0.2.3 |  | cargo-auditable-binary-cataloger |
| pathspec | 1.1.1 |  | python-installed-package-cataloger |
| pbkdf2 | 0.12.2 |  | cargo-auditable-binary-cataloger |
| pbkdf2 | 0.12.2 |  | cargo-auditable-binary-cataloger |
| pem | 3.0.6 |  | cargo-auditable-binary-cataloger |
| pem | 3.0.6 |  | cargo-auditable-binary-cataloger |
| pem-rfc7468 | 0.7.0 |  | cargo-auditable-binary-cataloger |
| pem-rfc7468 | 0.7.0 |  | cargo-auditable-binary-cataloger |
| percent-encoding | 2.3.2 |  | cargo-auditable-binary-cataloger |
| percent-encoding | 2.3.2 |  | cargo-auditable-binary-cataloger |
| perl | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-modules-5.36 | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pest | 2.8.6 |  | cargo-auditable-binary-cataloger |
| pest | 2.8.6 |  | cargo-auditable-binary-cataloger |
| pest_derive | 2.8.6 |  | cargo-auditable-binary-cataloger |
| pest_derive | 2.8.6 |  | cargo-auditable-binary-cataloger |
| pest_generator | 2.8.6 |  | cargo-auditable-binary-cataloger |
| pest_generator | 2.8.6 |  | cargo-auditable-binary-cataloger |
| pest_meta | 2.8.6 |  | cargo-auditable-binary-cataloger |
| pest_meta | 2.8.6 |  | cargo-auditable-binary-cataloger |
| petgraph | 0.8.3 |  | cargo-auditable-binary-cataloger |
| petgraph | 0.8.3 |  | cargo-auditable-binary-cataloger |
| pgvector | 0.4.2 | MIT | python-installed-package-cataloger |
| pillow | 12.2.0 | MIT-CMU | python-installed-package-cataloger |
| pin-project | 1.1.11 |  | cargo-auditable-binary-cataloger |
| pin-project | 1.1.11 |  | cargo-auditable-binary-cataloger |
| pin-project-lite | 0.2.17 |  | cargo-auditable-binary-cataloger |
| pin-project-lite | 0.2.17 |  | cargo-auditable-binary-cataloger |
| pinecone | 6.0.2 | Apache-2.0 | python-installed-package-cataloger |
| pinecone-plugin-interface | 0.0.7 | Apache-2.0 | python-installed-package-cataloger |
| pip | 24.0 | MIT | python-installed-package-cataloger |
| pkcs1 | 0.7.5 |  | cargo-auditable-binary-cataloger |
| pkcs1 | 0.7.5 |  | cargo-auditable-binary-cataloger |
| pkcs5 | 0.7.1 |  | cargo-auditable-binary-cataloger |
| pkcs5 | 0.7.1 |  | cargo-auditable-binary-cataloger |
| pkcs8 | 0.10.2 |  | cargo-auditable-binary-cataloger |
| pkcs8 | 0.10.2 |  | cargo-auditable-binary-cataloger |
| plain | 0.2.3 |  | cargo-auditable-binary-cataloger |
| plain | 0.2.3 |  | cargo-auditable-binary-cataloger |
| platformdirs | 4.10.0 | MIT | python-installed-package-cataloger |
| platformdirs | 4.2.2 | MIT | python-installed-package-cataloger |
| playwright | 1.60.0 | Apache-2.0 | python-installed-package-cataloger |
| playwright-core | 1.60.0 | Apache-2.0 | javascript-package-cataloger |
| pluggy | 1.6.0 | MIT | python-installed-package-cataloger |
| portable-atomic | 1.13.1 |  | cargo-auditable-binary-cataloger |
| portable-atomic | 1.13.1 |  | cargo-auditable-binary-cataloger |
| portalocker | 3.2.0 | BSD-3-Clause | python-installed-package-cataloger |
| potential_utf | 0.1.4 |  | cargo-auditable-binary-cataloger |
| potential_utf | 0.1.4 |  | cargo-auditable-binary-cataloger |
| powerfmt | 0.2.0 |  | cargo-auditable-binary-cataloger |
| powerfmt | 0.2.0 |  | cargo-auditable-binary-cataloger |
| ppv-lite86 | 0.2.21 |  | cargo-auditable-binary-cataloger |
| ppv-lite86 | 0.2.21 |  | cargo-auditable-binary-cataloger |
| predicates | 3.1.4 |  | cargo-auditable-binary-cataloger |
| predicates | 3.1.4 |  | cargo-auditable-binary-cataloger |
| predicates-core | 1.0.10 |  | cargo-auditable-binary-cataloger |
| predicates-core | 1.0.10 |  | cargo-auditable-binary-cataloger |
| predicates-tree | 1.0.13 |  | cargo-auditable-binary-cataloger |
| predicates-tree | 1.0.13 |  | cargo-auditable-binary-cataloger |
| preshed | 3.0.13 | MIT | python-installed-package-cataloger |
| primp | 1.3.1 |  | python-installed-package-cataloger |
| priority-queue | 2.7.0 |  | cargo-auditable-binary-cataloger |
| priority-queue | 2.7.0 |  | cargo-auditable-binary-cataloger |
| proc-macro-crate | 3.5.0 |  | cargo-auditable-binary-cataloger |
| proc-macro-crate | 3.5.0 |  | cargo-auditable-binary-cataloger |
| proc-macro2 | 1.0.106 |  | cargo-auditable-binary-cataloger |
| proc-macro2 | 1.0.106 |  | cargo-auditable-binary-cataloger |
| procfs | 0.18.0 |  | cargo-auditable-binary-cataloger |
| procfs | 0.18.0 |  | cargo-auditable-binary-cataloger |
| procfs-core | 0.18.0 |  | cargo-auditable-binary-cataloger |
| procfs-core | 0.18.0 |  | cargo-auditable-binary-cataloger |
| propcache | 0.5.2 | Apache-2.0 | python-installed-package-cataloger |
| proto-plus | 1.28.0 |  | python-installed-package-cataloger |
| protobuf | 6.33.6 |  | python-installed-package-cataloger |
| psutil | 7.2.2 | BSD-3-Clause | python-installed-package-cataloger |
| psycopg | 3.3.4 | LGPL-3.0-only | python-installed-package-cataloger |
| psycopg-binary | 3.3.4 | LGPL-3.0-only | python-installed-package-cataloger |
| psycopg2-binary | 2.9.12 |  | python-installed-package-cataloger |
| ptr_meta | 0.3.1 |  | cargo-auditable-binary-cataloger |
| ptr_meta | 0.3.1 |  | cargo-auditable-binary-cataloger |
| purl | 0.1.6 |  | cargo-auditable-binary-cataloger |
| purl | 0.1.6 |  | cargo-auditable-binary-cataloger |
| pxfm | 0.1.28 |  | cargo-auditable-binary-cataloger |
| pxfm | 0.1.28 |  | cargo-auditable-binary-cataloger |
| pyarrow | 20.0.0 |  | python-installed-package-cataloger |
| pyasn1 | 0.6.3 | BSD-2-Clause | python-installed-package-cataloger |
| pyasn1-modules | 0.4.2 |  | python-installed-package-cataloger |
| pybase64 | 1.4.3 | BSD-2-Clause | python-installed-package-cataloger |
| pyclipper | 1.4.0 | MIT | python-installed-package-cataloger |
| pycparser | 3.0 | BSD-3-Clause | python-installed-package-cataloger |
| pycrdt | 0.13.1 |  | python-installed-package-cataloger |
| pydantic | 2.13.4 | MIT | python-installed-package-cataloger |
| pydantic-core | 2.46.4 | MIT | python-installed-package-cataloger |
| pydantic-settings | 2.14.2 | MIT | python-installed-package-cataloger |
| pydub | 0.25.1 | MIT | python-installed-package-cataloger |
| pyee | 13.0.1 | MIT | python-installed-package-cataloger |
| pygments | 2.20.0 | BSD-2-Clause | python-installed-package-cataloger |
| pyjwt | 2.13.0 | MIT | python-installed-package-cataloger |
| pymdown-extensions | 10.21.3 | MIT | python-installed-package-cataloger |
| pymilvus | 2.6.14 |  | python-installed-package-cataloger |
| pymongo | 4.17.0 | Apache-2.0 | python-installed-package-cataloger |
| pymysql | 1.2.0 | MIT | python-installed-package-cataloger |
| pyodide | 0.28.3 | MPL-2.0 | javascript-package-cataloger |
| pypandoc | 1.17 | MIT | python-installed-package-cataloger |
| pyparsing | 3.3.2 | MIT | python-installed-package-cataloger |
| pypdf | 6.7.5 | BSD-3-Clause | python-installed-package-cataloger |
| pypdfium2 | 5.11.0 |  | python-installed-package-cataloger |
| pypika | 0.51.1 |  | python-installed-package-cataloger |
| pyproject-hooks | 1.2.0 | MIT | python-installed-package-cataloger |
| pytest | 8.4.2 | MIT | python-installed-package-cataloger |
| pytest-docker | 3.2.5 | MIT | python-installed-package-cataloger |
| python | 3.11.15 |  | binary-classifier-cataloger |
| python-dateutil | 2.9.0.post0 |  | python-installed-package-cataloger |
| python-dotenv | 1.2.2 | BSD-3-Clause | python-installed-package-cataloger |
| python-engineio | 4.13.3 | MIT | python-installed-package-cataloger |
| python-iso639 | 2026.4.20 | Apache-2.0 | python-installed-package-cataloger |
| python-jose | 3.5.0 | MIT | python-installed-package-cataloger |
| python-magic | 0.4.27 | MIT | python-installed-package-cataloger |
| python-mimeparse | 2.0.0 | MIT | python-installed-package-cataloger |
| python-multipart | 0.0.27 | Apache-2.0 | python-installed-package-cataloger |
| python-oxmsg | 0.0.2 | MIT | python-installed-package-cataloger |
| python-pptx | 1.0.2 | MIT | python-installed-package-cataloger |
| python-socketio | 5.16.2 | MIT | python-installed-package-cataloger |
| python3 | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3-dev | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3-distutils | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-lib2to3 | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-minimal | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3.11 | 3.11.2-6+deb12u7 | GPL-2.0-only | dpkg-db-cataloger |
| python3.11-dev | 3.11.2-6+deb12u7 | GPL-2.0-only | dpkg-db-cataloger |
| python3.11-minimal | 3.11.2-6+deb12u7 | GPL-2.0-only | dpkg-db-cataloger |
| pytokens | 0.4.1 | MIT | python-installed-package-cataloger |
| pytube | 15.0.0 |  | python-installed-package-cataloger |
| pytz | 2026.2 | MIT | python-installed-package-cataloger |
| pyxlsb | 1.0.10 |  | python-installed-package-cataloger |
| pyyaml | 6.0.3 | MIT | python-installed-package-cataloger |
| qdrant-client | 1.18.0 | Apache-2.0 | python-installed-package-cataloger |
| quick-xml | 0.39.2 |  | cargo-auditable-binary-cataloger |
| quick-xml | 0.39.2 |  | cargo-auditable-binary-cataloger |
| quinn | 0.11.9 |  | cargo-auditable-binary-cataloger |
| quinn | 0.11.9 |  | cargo-auditable-binary-cataloger |
| quinn-proto | 0.11.14 |  | cargo-auditable-binary-cataloger |
| quinn-proto | 0.11.14 |  | cargo-auditable-binary-cataloger |
| quinn-udp | 0.5.14 |  | cargo-auditable-binary-cataloger |
| quinn-udp | 0.5.14 |  | cargo-auditable-binary-cataloger |
| quote | 1.0.45 |  | cargo-auditable-binary-cataloger |
| quote | 1.0.45 |  | cargo-auditable-binary-cataloger |
| quoted_printable | 0.5.1 |  | cargo-auditable-binary-cataloger |
| quoted_printable | 0.5.1 |  | cargo-auditable-binary-cataloger |
| rancor | 0.1.1 |  | cargo-auditable-binary-cataloger |
| rancor | 0.1.1 |  | cargo-auditable-binary-cataloger |
| rand | 0.8.6 |  | cargo-auditable-binary-cataloger |
| rand | 0.8.6 |  | cargo-auditable-binary-cataloger |
| rand | 0.9.4 |  | cargo-auditable-binary-cataloger |
| rand | 0.9.4 |  | cargo-auditable-binary-cataloger |
| rand_chacha | 0.3.1 |  | cargo-auditable-binary-cataloger |
| rand_chacha | 0.3.1 |  | cargo-auditable-binary-cataloger |
| rand_chacha | 0.9.0 |  | cargo-auditable-binary-cataloger |
| rand_chacha | 0.9.0 |  | cargo-auditable-binary-cataloger |
| rand_core | 0.6.4 |  | cargo-auditable-binary-cataloger |
| rand_core | 0.6.4 |  | cargo-auditable-binary-cataloger |
| rand_core | 0.9.5 |  | cargo-auditable-binary-cataloger |
| rand_core | 0.9.5 |  | cargo-auditable-binary-cataloger |
| rank-bm25 | 0.2.2 | Apache-2.0 | python-installed-package-cataloger |
| rapidfuzz | 3.14.5 | MIT | python-installed-package-cataloger |
| rapidocr-onnxruntime | 1.4.4 | Apache-2.0 | python-installed-package-cataloger |
| rayon | 1.12.0 |  | cargo-auditable-binary-cataloger |
| rayon | 1.12.0 |  | cargo-auditable-binary-cataloger |
| rayon-core | 1.13.0 |  | cargo-auditable-binary-cataloger |
| rayon-core | 1.13.0 |  | cargo-auditable-binary-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| redis | 8.0.0 | MIT | python-installed-package-cataloger |
| ref-cast | 1.0.25 |  | cargo-auditable-binary-cataloger |
| ref-cast | 1.0.25 |  | cargo-auditable-binary-cataloger |
| referencing | 0.37.0 | MIT | python-installed-package-cataloger |
| reflink-copy | 0.1.29 |  | cargo-auditable-binary-cataloger |
| reflink-copy | 0.1.29 |  | cargo-auditable-binary-cataloger |
| regex | 1.12.4 |  | cargo-auditable-binary-cataloger |
| regex | 1.12.4 |  | cargo-auditable-binary-cataloger |
| regex | 2026.6.28 | Apache-2.0 AND CNRI-Python | python-installed-package-cataloger |
| regex-automata | 0.4.14 |  | cargo-auditable-binary-cataloger |
| regex-automata | 0.4.14 |  | cargo-auditable-binary-cataloger |
| regex-syntax | 0.8.11 |  | cargo-auditable-binary-cataloger |
| regex-syntax | 0.8.11 |  | cargo-auditable-binary-cataloger |
| rend | 0.5.3 |  | cargo-auditable-binary-cataloger |
| rend | 0.5.3 |  | cargo-auditable-binary-cataloger |
| reqsign | 0.20.0 |  | cargo-auditable-binary-cataloger |
| reqsign | 0.20.0 |  | cargo-auditable-binary-cataloger |
| reqsign-aws-v4 | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-aws-v4 | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-azure-storage | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-azure-storage | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-command-execute-tokio | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-command-execute-tokio | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-core | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-core | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-file-read-tokio | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-file-read-tokio | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-google | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-google | 3.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-http-send-reqwest | 4.0.0 |  | cargo-auditable-binary-cataloger |
| reqsign-http-send-reqwest | 4.0.0 |  | cargo-auditable-binary-cataloger |
| requests | 2.34.2 | Apache-2.0 | python-installed-package-cataloger |
| requests-oauthlib | 2.0.0 | ISC | python-installed-package-cataloger |
| requests-toolbelt | 1.0.0 |  | python-installed-package-cataloger |
| reqwest | 0.13.4 |  | cargo-auditable-binary-cataloger |
| reqwest | 0.13.4 |  | cargo-auditable-binary-cataloger |
| restrictedpython | 8.2 | ZPL-2.1 | python-installed-package-cataloger |
| retry-policies | 0.5.1 |  | cargo-auditable-binary-cataloger |
| retry-policies | 0.5.1 |  | cargo-auditable-binary-cataloger |
| rich | 13.9.4 | MIT | python-installed-package-cataloger |
| ring | 0.17.14 |  | cargo-auditable-binary-cataloger |
| ring | 0.17.14 |  | cargo-auditable-binary-cataloger |
| rkyv | 0.8.16 |  | cargo-auditable-binary-cataloger |
| rkyv | 0.8.16 |  | cargo-auditable-binary-cataloger |
| rmp | 0.8.15 |  | cargo-auditable-binary-cataloger |
| rmp | 0.8.15 |  | cargo-auditable-binary-cataloger |
| rmp-serde | 1.3.1 |  | cargo-auditable-binary-cataloger |
| rmp-serde | 1.3.1 |  | cargo-auditable-binary-cataloger |
| rpcsvc-proto | 1.4.3-1 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, MIT | dpkg-db-cataloger |
| rpds-py | 2026.5.1 | MIT | python-installed-package-cataloger |
| rsa | 0.9.10 |  | cargo-auditable-binary-cataloger |
| rsa | 0.9.10 |  | cargo-auditable-binary-cataloger |
| rsa | 4.9.1 | Apache-2.0 | python-installed-package-cataloger |
| rust-ini | 0.21.3 |  | cargo-auditable-binary-cataloger |
| rust-ini | 0.21.3 |  | cargo-auditable-binary-cataloger |
| rustc-hash | 2.1.2 |  | cargo-auditable-binary-cataloger |
| rustc-hash | 2.1.2 |  | cargo-auditable-binary-cataloger |
| rusticata-macros | 4.1.0 |  | cargo-auditable-binary-cataloger |
| rusticata-macros | 4.1.0 |  | cargo-auditable-binary-cataloger |
| rustix | 0.38.44 |  | cargo-auditable-binary-cataloger |
| rustix | 0.38.44 |  | cargo-auditable-binary-cataloger |
| rustix | 1.1.4 |  | cargo-auditable-binary-cataloger |
| rustix | 1.1.4 |  | cargo-auditable-binary-cataloger |
| rustls | 0.23.40 |  | cargo-auditable-binary-cataloger |
| rustls | 0.23.40 |  | cargo-auditable-binary-cataloger |
| rustls-native-certs | 0.8.4 |  | cargo-auditable-binary-cataloger |
| rustls-native-certs | 0.8.4 |  | cargo-auditable-binary-cataloger |
| rustls-pki-types | 1.14.1 |  | cargo-auditable-binary-cataloger |
| rustls-pki-types | 1.14.1 |  | cargo-auditable-binary-cataloger |
| rustls-platform-verifier | 0.7.0 |  | cargo-auditable-binary-cataloger |
| rustls-platform-verifier | 0.7.0 |  | cargo-auditable-binary-cataloger |
| rustls-webpki | 0.103.13 |  | cargo-auditable-binary-cataloger |
| rustls-webpki | 0.103.13 |  | cargo-auditable-binary-cataloger |
| ryu | 1.0.23 |  | cargo-auditable-binary-cataloger |
| ryu | 1.0.23 |  | cargo-auditable-binary-cataloger |
| s3transfer | 0.16.1 |  | python-installed-package-cataloger |
| safetensors | 0.8.0 |  | python-installed-package-cataloger |
| salsa20 | 0.10.2 |  | cargo-auditable-binary-cataloger |
| salsa20 | 0.10.2 |  | cargo-auditable-binary-cataloger |
| same-file | 1.0.6 |  | cargo-auditable-binary-cataloger |
| same-file | 1.0.6 |  | cargo-auditable-binary-cataloger |
| schemars | 1.2.1 |  | cargo-auditable-binary-cataloger |
| schemars | 1.2.1 |  | cargo-auditable-binary-cataloger |
| scikit-learn | 1.9.0 | BSD-3-Clause | python-installed-package-cataloger |
| scipy | 1.17.1 | BSD-3-Clause | python-installed-package-cataloger |
| scopeguard | 1.2.0 |  | cargo-auditable-binary-cataloger |
| scopeguard | 1.2.0 |  | cargo-auditable-binary-cataloger |
| scroll | 0.13.0 |  | cargo-auditable-binary-cataloger |
| scroll | 0.13.0 |  | cargo-auditable-binary-cataloger |
| scrypt | 0.11.0 |  | cargo-auditable-binary-cataloger |
| scrypt | 0.11.0 |  | cargo-auditable-binary-cataloger |
| seahash | 4.1.0 |  | cargo-auditable-binary-cataloger |
| seahash | 4.1.0 |  | cargo-auditable-binary-cataloger |
| secrecy | 0.10.3 |  | cargo-auditable-binary-cataloger |
| secrecy | 0.10.3 |  | cargo-auditable-binary-cataloger |
| secret-service | 5.1.0 |  | cargo-auditable-binary-cataloger |
| secret-service | 5.1.0 |  | cargo-auditable-binary-cataloger |
| sed | 4.9-1+deb12u1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| seize | 0.5.1 |  | cargo-auditable-binary-cataloger |
| seize | 0.5.1 |  | cargo-auditable-binary-cataloger |
| semver | 1.0.27 |  | cargo-auditable-binary-cataloger |
| semver | 1.0.27 |  | cargo-auditable-binary-cataloger |
| sentence-transformers | 5.5.1 |  | python-installed-package-cataloger |
| sentencepiece | 0.2.1 |  | python-installed-package-cataloger |
| serde | 1.0.228 |  | cargo-auditable-binary-cataloger |
| serde | 1.0.228 |  | cargo-auditable-binary-cataloger |
| serde-untagged | 0.1.9 |  | cargo-auditable-binary-cataloger |
| serde-untagged | 0.1.9 |  | cargo-auditable-binary-cataloger |
| serde_core | 1.0.228 |  | cargo-auditable-binary-cataloger |
| serde_core | 1.0.228 |  | cargo-auditable-binary-cataloger |
| serde_json | 1.0.150 |  | cargo-auditable-binary-cataloger |
| serde_json | 1.0.150 |  | cargo-auditable-binary-cataloger |
| serde_repr | 0.1.20 |  | cargo-auditable-binary-cataloger |
| serde_repr | 0.1.20 |  | cargo-auditable-binary-cataloger |
| serde_spanned | 1.1.1 |  | cargo-auditable-binary-cataloger |
| serde_spanned | 1.1.1 |  | cargo-auditable-binary-cataloger |
| serde_urlencoded | 0.7.1 |  | cargo-auditable-binary-cataloger |
| serde_urlencoded | 0.7.1 |  | cargo-auditable-binary-cataloger |
| setuptools | 79.0.1 |  | python-installed-package-cataloger |
| sha1 | 0.10.6 |  | cargo-auditable-binary-cataloger |
| sha1 | 0.10.6 |  | cargo-auditable-binary-cataloger |
| sha2 | 0.10.9 |  | cargo-auditable-binary-cataloger |
| sha2 | 0.10.9 |  | cargo-auditable-binary-cataloger |
| shapely | 2.1.2 |  | python-installed-package-cataloger |
| sharded-slab | 0.1.7 |  | cargo-auditable-binary-cataloger |
| sharded-slab | 0.1.7 |  | cargo-auditable-binary-cataloger |
| shared-mime-info | 2.2-1 |  | dpkg-db-cataloger |
| shell-escape | 0.1.5 |  | cargo-auditable-binary-cataloger |
| shell-escape | 0.1.5 |  | cargo-auditable-binary-cataloger |
| shellexpand | 3.1.2 |  | cargo-auditable-binary-cataloger |
| shellexpand | 3.1.2 |  | cargo-auditable-binary-cataloger |
| shellingham | 1.5.4 |  | python-installed-package-cataloger |
| signal-hook-registry | 1.4.8 |  | cargo-auditable-binary-cataloger |
| signal-hook-registry | 1.4.8 |  | cargo-auditable-binary-cataloger |
| signature | 2.2.0 |  | cargo-auditable-binary-cataloger |
| signature | 2.2.0 |  | cargo-auditable-binary-cataloger |
| simd-adler32 | 0.3.8 |  | cargo-auditable-binary-cataloger |
| simd-adler32 | 0.3.8 |  | cargo-auditable-binary-cataloger |
| simdutf8 | 0.1.5 |  | cargo-auditable-binary-cataloger |
| simdutf8 | 0.1.5 |  | cargo-auditable-binary-cataloger |
| similar | 2.7.0 |  | cargo-auditable-binary-cataloger |
| similar | 2.7.0 |  | cargo-auditable-binary-cataloger |
| similar | 3.1.1 |  | cargo-auditable-binary-cataloger |
| similar | 3.1.1 |  | cargo-auditable-binary-cataloger |
| simple-websocket | 1.1.0 | MIT | python-installed-package-cataloger |
| simple_asn1 | 0.6.4 |  | cargo-auditable-binary-cataloger |
| simple_asn1 | 0.6.4 |  | cargo-auditable-binary-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| slab | 0.4.12 |  | cargo-auditable-binary-cataloger |
| slab | 0.4.12 |  | cargo-auditable-binary-cataloger |
| smallvec | 1.15.2 |  | cargo-auditable-binary-cataloger |
| smallvec | 1.15.2 |  | cargo-auditable-binary-cataloger |
| smart-open | 8.0.0 |  | python-installed-package-cataloger |
| smawk | 0.3.2 |  | cargo-auditable-binary-cataloger |
| smawk | 0.3.2 |  | cargo-auditable-binary-cataloger |
| smmap | 5.0.3 | BSD-3-Clause | python-installed-package-cataloger |
| sniffio | 1.3.1 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| socket2 | 0.6.3 |  | cargo-auditable-binary-cataloger |
| socket2 | 0.6.3 |  | cargo-auditable-binary-cataloger |
| socksio | 1.0.0 |  | python-installed-package-cataloger |
| soundfile | 0.13.1 |  | python-installed-package-cataloger |
| soupsieve | 2.8.4 | MIT | python-installed-package-cataloger |
| spacy | 3.8.14 | MIT | python-installed-package-cataloger |
| spacy-legacy | 3.0.12 | MIT | python-installed-package-cataloger |
| spacy-loggers | 1.0.5 | MIT | python-installed-package-cataloger |
| spdx | 0.13.4 |  | cargo-auditable-binary-cataloger |
| spdx | 0.13.4 |  | cargo-auditable-binary-cataloger |
| spin | 0.9.8 |  | cargo-auditable-binary-cataloger |
| spin | 0.9.8 |  | cargo-auditable-binary-cataloger |
| spki | 0.7.3 |  | cargo-auditable-binary-cataloger |
| spki | 0.7.3 |  | cargo-auditable-binary-cataloger |
| sqlalchemy | 2.0.50 | MIT | python-installed-package-cataloger |
| srsly | 2.5.3 | MIT | python-installed-package-cataloger |
| sse-starlette | 3.4.5 | BSD-3-Clause | python-installed-package-cataloger |
| stable_deref_trait | 1.2.1 |  | cargo-auditable-binary-cataloger |
| stable_deref_trait | 1.2.1 |  | cargo-auditable-binary-cataloger |
| starlette | 1.3.1 | BSD-3-Clause | python-installed-package-cataloger |
| starlette-compress | 1.7.1 | 0BSD | python-installed-package-cataloger |
| starsessions | 2.2.1 | MIT | python-installed-package-cataloger |
| strip-ansi-escapes | 0.2.1 |  | cargo-auditable-binary-cataloger |
| strip-ansi-escapes | 0.2.1 |  | cargo-auditable-binary-cataloger |
| strsim | 0.11.1 |  | cargo-auditable-binary-cataloger |
| strsim | 0.11.1 |  | cargo-auditable-binary-cataloger |
| strum | 0.28.0 |  | cargo-auditable-binary-cataloger |
| strum | 0.28.0 |  | cargo-auditable-binary-cataloger |
| subtle | 2.6.1 |  | cargo-auditable-binary-cataloger |
| subtle | 2.6.1 |  | cargo-auditable-binary-cataloger |
| supports-color | 3.0.2 |  | cargo-auditable-binary-cataloger |
| supports-color | 3.0.2 |  | cargo-auditable-binary-cataloger |
| supports-hyperlinks | 3.2.0 |  | cargo-auditable-binary-cataloger |
| supports-hyperlinks | 3.2.0 |  | cargo-auditable-binary-cataloger |
| supports-unicode | 3.0.0 |  | cargo-auditable-binary-cataloger |
| supports-unicode | 3.0.0 |  | cargo-auditable-binary-cataloger |
| sympy | 1.14.0 |  | python-installed-package-cataloger |
| syn | 2.0.117 |  | cargo-auditable-binary-cataloger |
| syn | 2.0.117 |  | cargo-auditable-binary-cataloger |
| sync_wrapper | 1.0.2 |  | cargo-auditable-binary-cataloger |
| sync_wrapper | 1.0.2 |  | cargo-auditable-binary-cataloger |
| synstructure | 0.13.2 |  | cargo-auditable-binary-cataloger |
| synstructure | 0.13.2 |  | cargo-auditable-binary-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| t32 | UNKNOWN |  | pe-binary-package-cataloger |
| t64 | UNKNOWN |  | pe-binary-package-cataloger |
| t64-arm | UNKNOWN |  | pe-binary-package-cataloger |
| t_arm | UNKNOWN |  | pe-binary-package-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| target-lexicon | 0.13.5 |  | cargo-auditable-binary-cataloger |
| target-lexicon | 0.13.5 |  | cargo-auditable-binary-cataloger |
| temp-env | 0.3.6 |  | cargo-auditable-binary-cataloger |
| temp-env | 0.3.6 |  | cargo-auditable-binary-cataloger |
| tempfile | 3.27.0 |  | cargo-auditable-binary-cataloger |
| tempfile | 3.27.0 |  | cargo-auditable-binary-cataloger |
| tenacity | 9.1.4 |  | python-installed-package-cataloger |
| terminal_size | 0.4.4 |  | cargo-auditable-binary-cataloger |
| terminal_size | 0.4.4 |  | cargo-auditable-binary-cataloger |
| termtree | 0.5.1 |  | cargo-auditable-binary-cataloger |
| termtree | 0.5.1 |  | cargo-auditable-binary-cataloger |
| textwrap | 0.16.2 |  | cargo-auditable-binary-cataloger |
| textwrap | 0.16.2 |  | cargo-auditable-binary-cataloger |
| thinc | 8.3.13 | MIT | python-installed-package-cataloger |
| thiserror | 2.0.18 |  | cargo-auditable-binary-cataloger |
| thiserror | 2.0.18 |  | cargo-auditable-binary-cataloger |
| thread_local | 1.1.9 |  | cargo-auditable-binary-cataloger |
| thread_local | 1.1.9 |  | cargo-auditable-binary-cataloger |
| threadpoolctl | 3.6.0 | BSD-3-Clause | python-installed-package-cataloger |
| tiktoken | 0.13.0 | MIT | python-installed-package-cataloger |
| tikv-jemalloc-sys | 0.6.1+5.3.0-1-ge13ca993e8ccb9ba9847cc330696e02839f328f7 |  | cargo-auditable-binary-cataloger |
| tikv-jemalloc-sys | 0.6.1+5.3.0-1-ge13ca993e8ccb9ba9847cc330696e02839f328f7 |  | cargo-auditable-binary-cataloger |
| tikv-jemallocator | 0.6.1 |  | cargo-auditable-binary-cataloger |
| tikv-jemallocator | 0.6.1 |  | cargo-auditable-binary-cataloger |
| time | 0.3.47 |  | cargo-auditable-binary-cataloger |
| time | 0.3.47 |  | cargo-auditable-binary-cataloger |
| time-core | 0.1.8 |  | cargo-auditable-binary-cataloger |
| time-core | 0.1.8 |  | cargo-auditable-binary-cataloger |
| tinystr | 0.8.2 |  | cargo-auditable-binary-cataloger |
| tinystr | 0.8.2 |  | cargo-auditable-binary-cataloger |
| tinyvec | 1.11.0 |  | cargo-auditable-binary-cataloger |
| tinyvec | 1.11.0 |  | cargo-auditable-binary-cataloger |
| tinyvec_macros | 0.1.1 |  | cargo-auditable-binary-cataloger |
| tinyvec_macros | 0.1.1 |  | cargo-auditable-binary-cataloger |
| tokenizers | 0.22.2 |  | python-installed-package-cataloger |
| tokio | 1.52.3 |  | cargo-auditable-binary-cataloger |
| tokio | 1.52.3 |  | cargo-auditable-binary-cataloger |
| tokio-rustls | 0.26.4 |  | cargo-auditable-binary-cataloger |
| tokio-rustls | 0.26.4 |  | cargo-auditable-binary-cataloger |
| tokio-stream | 0.1.18 |  | cargo-auditable-binary-cataloger |
| tokio-stream | 0.1.18 |  | cargo-auditable-binary-cataloger |
| tokio-util | 0.7.18 |  | cargo-auditable-binary-cataloger |
| tokio-util | 0.7.18 |  | cargo-auditable-binary-cataloger |
| toml | 1.1.2+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml | 1.1.2+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml_datetime | 1.1.1+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml_datetime | 1.1.1+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml_edit | 0.25.12+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml_edit | 0.25.12+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml_parser | 1.1.2+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml_parser | 1.1.2+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml_writer | 1.1.1+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| toml_writer | 1.1.1+spec-1.1.0 |  | cargo-auditable-binary-cataloger |
| tomli | 2.0.1 | MIT | python-installed-package-cataloger |
| torch | 2.9.1+cpu | BSD-3-Clause | python-installed-package-cataloger |
| torchaudio | 2.11.0+cpu |  | python-installed-package-cataloger |
| torchvision | 0.24.1+cpu |  | python-installed-package-cataloger |
| tower | 0.5.3 |  | cargo-auditable-binary-cataloger |
| tower | 0.5.3 |  | cargo-auditable-binary-cataloger |
| tower-http | 0.6.8 |  | cargo-auditable-binary-cataloger |
| tower-http | 0.6.8 |  | cargo-auditable-binary-cataloger |
| tower-layer | 0.3.3 |  | cargo-auditable-binary-cataloger |
| tower-layer | 0.3.3 |  | cargo-auditable-binary-cataloger |
| tower-service | 0.3.3 |  | cargo-auditable-binary-cataloger |
| tower-service | 0.3.3 |  | cargo-auditable-binary-cataloger |
| tqdm | 4.68.3 | MPL-2.0 AND MIT | python-installed-package-cataloger |
| tracing | 0.1.44 |  | cargo-auditable-binary-cataloger |
| tracing | 0.1.44 |  | cargo-auditable-binary-cataloger |
| tracing-attributes | 0.1.31 |  | cargo-auditable-binary-cataloger |
| tracing-attributes | 0.1.31 |  | cargo-auditable-binary-cataloger |
| tracing-core | 0.1.36 |  | cargo-auditable-binary-cataloger |
| tracing-core | 0.1.36 |  | cargo-auditable-binary-cataloger |
| tracing-log | 0.2.0 |  | cargo-auditable-binary-cataloger |
| tracing-log | 0.2.0 |  | cargo-auditable-binary-cataloger |
| tracing-subscriber | 0.3.23 |  | cargo-auditable-binary-cataloger |
| tracing-subscriber | 0.3.23 |  | cargo-auditable-binary-cataloger |
| tracing-tree | 0.4.1 |  | cargo-auditable-binary-cataloger |
| tracing-tree | 0.4.1 |  | cargo-auditable-binary-cataloger |
| transformers | 5.5.4 |  | python-installed-package-cataloger |
| try-lock | 0.2.5 |  | cargo-auditable-binary-cataloger |
| try-lock | 0.2.5 |  | cargo-auditable-binary-cataloger |
| typeguard | 4.3.0 | MIT | python-installed-package-cataloger |
| typeid | 1.0.3 |  | cargo-auditable-binary-cataloger |
| typeid | 1.0.3 |  | cargo-auditable-binary-cataloger |
| typenum | 1.19.0 |  | cargo-auditable-binary-cataloger |
| typenum | 1.19.0 |  | cargo-auditable-binary-cataloger |
| typer | 0.25.1 | MIT | python-installed-package-cataloger |
| typing-extensions | 4.12.2 |  | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| typing-inspection | 0.4.2 | MIT | python-installed-package-cataloger |
| tzdata | 2026b-0+deb12u1 |  | dpkg-db-cataloger |
| tzlocal | 5.4.4 | MIT | python-installed-package-cataloger |
| ucd-trie | 0.1.7 |  | cargo-auditable-binary-cataloger |
| ucd-trie | 0.1.7 |  | cargo-auditable-binary-cataloger |
| ujson | 5.13.0 | BSD-3-Clause AND TCL | python-installed-package-cataloger |
| unicase | 2.9.0 |  | cargo-auditable-binary-cataloger |
| unicase | 2.9.0 |  | cargo-auditable-binary-cataloger |
| unicode-ident | 1.0.24 |  | cargo-auditable-binary-cataloger |
| unicode-ident | 1.0.24 |  | cargo-auditable-binary-cataloger |
| unicode-linebreak | 0.1.5 |  | cargo-auditable-binary-cataloger |
| unicode-linebreak | 0.1.5 |  | cargo-auditable-binary-cataloger |
| unicode-width | 0.1.14 |  | cargo-auditable-binary-cataloger |
| unicode-width | 0.1.14 |  | cargo-auditable-binary-cataloger |
| unicode-width | 0.2.2 |  | cargo-auditable-binary-cataloger |
| unicode-width | 0.2.2 |  | cargo-auditable-binary-cataloger |
| unit-prefix | 0.5.2 |  | cargo-auditable-binary-cataloger |
| unit-prefix | 0.5.2 |  | cargo-auditable-binary-cataloger |
| unscanny | 0.1.0 |  | cargo-auditable-binary-cataloger |
| unscanny | 0.1.0 |  | cargo-auditable-binary-cataloger |
| unstructured | 0.22.31 | Apache-2.0 | python-installed-package-cataloger |
| unstructured-client | 0.42.12 | MIT | python-installed-package-cataloger |
| untrusted | 0.7.1 |  | cargo-auditable-binary-cataloger |
| untrusted | 0.7.1 |  | cargo-auditable-binary-cataloger |
| untrusted | 0.9.0 |  | cargo-auditable-binary-cataloger |
| untrusted | 0.9.0 |  | cargo-auditable-binary-cataloger |
| uritemplate | 4.2.0 |  | python-installed-package-cataloger |
| url | 2.5.8 |  | cargo-auditable-binary-cataloger |
| url | 2.5.8 |  | cargo-auditable-binary-cataloger |
| urllib3 | 2.7.0 | MIT | python-installed-package-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| utf8-width | 0.1.8 |  | cargo-auditable-binary-cataloger |
| utf8-width | 0.1.8 |  | cargo-auditable-binary-cataloger |
| utf8_iter | 1.0.4 |  | cargo-auditable-binary-cataloger |
| utf8_iter | 1.0.4 |  | cargo-auditable-binary-cataloger |
| utf8parse | 0.2.2 |  | cargo-auditable-binary-cataloger |
| utf8parse | 0.2.2 |  | cargo-auditable-binary-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uuid | 1.23.3 |  | cargo-auditable-binary-cataloger |
| uuid | 1.23.3 |  | cargo-auditable-binary-cataloger |
| uuid-utils | 0.16.2 | BSD-3-Clause | python-installed-package-cataloger |
| uv | 0.11.25 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| uv | 0.11.25 |  | cargo-auditable-binary-cataloger |
| uv | 0.11.25 |  | cargo-auditable-binary-cataloger |
| uv-audit | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-audit | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-auth | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-auth | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-bin-install | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-bin-install | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-build-backend | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-build-backend | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-build-frontend | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-build-frontend | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-cache | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-cache | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-cache-info | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-cache-info | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-cache-key | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-cache-key | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-cli | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-cli | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-client | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-client | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-configuration | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-configuration | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-console | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-console | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-dirs | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-dirs | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-dispatch | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-dispatch | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-distribution | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-distribution | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-distribution-filename | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-distribution-filename | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-distribution-types | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-distribution-types | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-errors | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-errors | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-extract | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-extract | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-fastid | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-fastid | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-flags | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-flags | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-fs | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-fs | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-git | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-git | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-git-types | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-git-types | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-globfilter | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-globfilter | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-install-wheel | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-install-wheel | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-installer | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-installer | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-keyring | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-keyring | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-logging | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-logging | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-metadata | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-metadata | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-netrc | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-netrc | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-normalize | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-normalize | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-once-map | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-once-map | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-options-metadata | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-options-metadata | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-pep440 | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-pep440 | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-pep508 | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-pep508 | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-performance-memory-allocator | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-performance-memory-allocator | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-platform | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-platform | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-platform-tags | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-platform-tags | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-preview | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-preview | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-publish | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-publish | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-pypi-types | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-pypi-types | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-python | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-python | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-redacted | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-redacted | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-requirements | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-requirements | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-requirements-txt | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-requirements-txt | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-resolver | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-resolver | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-scripts | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-scripts | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-settings | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-settings | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-shell | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-shell | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-small-str | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-small-str | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-state | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-state | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-static | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-static | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-test | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-test | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-toml | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-toml | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-tool | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-tool | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-torch | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-torch | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-trampoline-builder | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-trampoline-builder | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-types | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-types | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-unix | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-unix | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-version | 0.11.25 |  | cargo-auditable-binary-cataloger |
| uv-version | 0.11.25 |  | cargo-auditable-binary-cataloger |
| uv-virtualenv | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-virtualenv | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-warnings | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-warnings | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-workspace | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uv-workspace | 0.0.58 |  | cargo-auditable-binary-cataloger |
| uvicorn | 0.41.0 | BSD-3-Clause | python-installed-package-cataloger |
| uvloop | 0.22.1 |  | python-installed-package-cataloger |
| validators | 0.35.0 | MIT | python-installed-package-cataloger |
| vte | 0.14.1 |  | cargo-auditable-binary-cataloger |
| vte | 0.14.1 |  | cargo-auditable-binary-cataloger |
| w32 | UNKNOWN |  | pe-binary-package-cataloger |
| w64 | UNKNOWN |  | pe-binary-package-cataloger |
| w64-arm | UNKNOWN |  | pe-binary-package-cataloger |
| w_arm | UNKNOWN |  | pe-binary-package-cataloger |
| wait-timeout | 0.2.1 |  | cargo-auditable-binary-cataloger |
| wait-timeout | 0.2.1 |  | cargo-auditable-binary-cataloger |
| walkdir | 2.5.0 |  | cargo-auditable-binary-cataloger |
| walkdir | 2.5.0 |  | cargo-auditable-binary-cataloger |
| want | 0.3.1 |  | cargo-auditable-binary-cataloger |
| want | 0.3.1 |  | cargo-auditable-binary-cataloger |
| wasabi | 1.1.3 | MIT | python-installed-package-cataloger |
| watchfiles | 1.2.0 | MIT | python-installed-package-cataloger |
| wcwidth | 0.8.2 | MIT | python-installed-package-cataloger |
| weasel | 1.0.0 | MIT | python-installed-package-cataloger |
| weaviate-client | 4.20.3 |  | python-installed-package-cataloger |
| webencodings | 0.5.1 |  | python-installed-package-cataloger |
| webpki-root-certs | 1.0.7 |  | cargo-auditable-binary-cataloger |
| webpki-root-certs | 1.0.7 |  | cargo-auditable-binary-cataloger |
| websocket-client | 1.9.0 | Apache-2.0 | python-installed-package-cataloger |
| websockets | 16.0 | BSD-3-Clause | python-installed-package-cataloger |
| werkzeug | 3.1.8 | BSD-3-Clause | python-installed-package-cataloger |
| wheel | 0.45.1 | MIT | python-installed-package-cataloger |
| wheel | 0.45.1 | MIT | python-installed-package-cataloger |
| which | 8.0.3 |  | cargo-auditable-binary-cataloger |
| which | 8.0.3 |  | cargo-auditable-binary-cataloger |
| winnow | 1.0.3 |  | cargo-auditable-binary-cataloger |
| winnow | 1.0.3 |  | cargo-auditable-binary-cataloger |
| wiremock | 0.6.5 |  | cargo-auditable-binary-cataloger |
| wiremock | 0.6.5 |  | cargo-auditable-binary-cataloger |
| wrapt | 2.2.2 | BSD-2-Clause | python-installed-package-cataloger |
| writeable | 0.6.2 |  | cargo-auditable-binary-cataloger |
| writeable | 0.6.2 |  | cargo-auditable-binary-cataloger |
| wsproto | 1.3.2 | MIT | python-installed-package-cataloger |
| x11-common | 1:7.7+23 |  | dpkg-db-cataloger |
| x509-parser | 0.18.1 |  | cargo-auditable-binary-cataloger |
| x509-parser | 0.18.1 |  | cargo-auditable-binary-cataloger |
| xattr | 1.6.1 |  | cargo-auditable-binary-cataloger |
| xattr | 1.6.1 |  | cargo-auditable-binary-cataloger |
| xkb-data | 2.35.1-1 |  | dpkg-db-cataloger |
| xlrd | 2.0.2 |  | python-installed-package-cataloger |
| xlsxwriter | 3.2.9 | BSD-2-Clause | python-installed-package-cataloger |
| xml-rs | 0.8.28 |  | cargo-auditable-binary-cataloger |
| xml-rs | 0.8.28 |  | cargo-auditable-binary-cataloger |
| xxhash | 3.8.0 | BSD-2-Clause | python-installed-package-cataloger |
| xz-utils | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| xz2 | 0.1.7 |  | cargo-auditable-binary-cataloger |
| xz2 | 0.1.7 |  | cargo-auditable-binary-cataloger |
| yarl | 1.24.2 | Apache-2.0 | python-installed-package-cataloger |
| yoke | 0.8.1 |  | cargo-auditable-binary-cataloger |
| yoke | 0.8.1 |  | cargo-auditable-binary-cataloger |
| yoke-derive | 0.8.1 |  | cargo-auditable-binary-cataloger |
| yoke-derive | 0.8.1 |  | cargo-auditable-binary-cataloger |
| youtube-transcript-api | 1.2.4 | MIT | python-installed-package-cataloger |
| zbus | 5.15.0 |  | cargo-auditable-binary-cataloger |
| zbus | 5.15.0 |  | cargo-auditable-binary-cataloger |
| zbus_macros | 5.15.0 |  | cargo-auditable-binary-cataloger |
| zbus_macros | 5.15.0 |  | cargo-auditable-binary-cataloger |
| zbus_names | 4.3.2 |  | cargo-auditable-binary-cataloger |
| zbus_names | 4.3.2 |  | cargo-auditable-binary-cataloger |
| zerocopy | 0.8.42 |  | cargo-auditable-binary-cataloger |
| zerocopy | 0.8.42 |  | cargo-auditable-binary-cataloger |
| zerocopy-derive | 0.8.42 |  | cargo-auditable-binary-cataloger |
| zerocopy-derive | 0.8.42 |  | cargo-auditable-binary-cataloger |
| zerofrom | 0.1.6 |  | cargo-auditable-binary-cataloger |
| zerofrom | 0.1.6 |  | cargo-auditable-binary-cataloger |
| zerofrom-derive | 0.1.6 |  | cargo-auditable-binary-cataloger |
| zerofrom-derive | 0.1.6 |  | cargo-auditable-binary-cataloger |
| zeroize | 1.9.0 |  | cargo-auditable-binary-cataloger |
| zeroize | 1.9.0 |  | cargo-auditable-binary-cataloger |
| zerotrie | 0.2.3 |  | cargo-auditable-binary-cataloger |
| zerotrie | 0.2.3 |  | cargo-auditable-binary-cataloger |
| zerovec | 0.11.5 |  | cargo-auditable-binary-cataloger |
| zerovec | 0.11.5 |  | cargo-auditable-binary-cataloger |
| zerovec-derive | 0.11.2 |  | cargo-auditable-binary-cataloger |
| zerovec-derive | 0.11.2 |  | cargo-auditable-binary-cataloger |
| zipp | 3.19.2 | MIT | python-installed-package-cataloger |
| zlib-rs | 0.6.3 |  | cargo-auditable-binary-cataloger |
| zlib-rs | 0.6.3 |  | cargo-auditable-binary-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zlib1g-dev | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zmij | 1.0.21 |  | cargo-auditable-binary-cataloger |
| zmij | 1.0.21 |  | cargo-auditable-binary-cataloger |
| zstandard | 0.25.0 | BSD-3-Clause | python-installed-package-cataloger |
| zstd | 0.13.3 |  | cargo-auditable-binary-cataloger |
| zstd | 0.13.3 |  | cargo-auditable-binary-cataloger |
| zstd | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| zstd-safe | 7.2.4 |  | cargo-auditable-binary-cataloger |
| zstd-safe | 7.2.4 |  | cargo-auditable-binary-cataloger |
| zstd-sys | 2.0.16+zstd.1.5.7 |  | cargo-auditable-binary-cataloger |
| zstd-sys | 2.0.16+zstd.1.5.7 |  | cargo-auditable-binary-cataloger |
| zvariant | 5.11.0 |  | cargo-auditable-binary-cataloger |
| zvariant | 5.11.0 |  | cargo-auditable-binary-cataloger |
| zvariant_derive | 5.11.0 |  | cargo-auditable-binary-cataloger |
| zvariant_derive | 5.11.0 |  | cargo-auditable-binary-cataloger |
| zvariant_utils | 3.3.1 |  | cargo-auditable-binary-cataloger |
| zvariant_utils | 3.3.1 |  | cargo-auditable-binary-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/elasticsearch

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| HdrHistogram | 2.1.9 |  | java-archive-cataloger |
| SparseBitSet | 1.3 |  | java-archive-cataloger |
| accessors-smart | 2.5.2 | Apache-2.0 | java-archive-cataloger |
| accessors-smart | 2.5.2 | Apache-2.0 | java-archive-cataloger |
| aggregations | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| aggregations | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| alternatives | 1.24-2.el9 | GPL-2.0-only | rpm-db-cataloger |
| analysis-common | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| analysis-icu | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| analysis-smartcn | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| analysis-stempel | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| analysis-ukrainian | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| annotations | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| annotations | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| apache-client | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| apache-client | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| apache-mime4j-core | 0.8.13 | Apache-2.0 | java-archive-cataloger |
| apache-mime4j-dom | 0.8.13 | Apache-2.0 | java-archive-cataloger |
| api-common | 2.46.1 |  | java-archive-cataloger |
| apm | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| apm-agent-cached-lookup-key | 1.55.6 |  | java-archive-cataloger |
| apm-agent-common | 1.55.6 |  | java-archive-cataloger |
| apm-agent-common | 1.55.6 |  | java-archive-cataloger |
| apm-agent-core | 1.55.6 |  | java-archive-cataloger |
| apm-agent-java8 | 1.55.6 |  | java-archive-cataloger |
| apm-agent-plugin-sdk | 1.55.6 |  | java-archive-cataloger |
| apm-agent-tracer | 1.55.6 |  | java-archive-cataloger |
| apm-apache-httpclient-common | 1.55.6 |  | java-archive-cataloger |
| apm-apache-httpclient3-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-apache-httpclient4-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-apache-httpclient5-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-api-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-asynchttpclient-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-aws-sdk-1-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-aws-sdk-2-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-aws-sdk-common | 1.55.6 |  | java-archive-cataloger |
| apm-awslambda-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-cassandra-core-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-cassandra3-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-cassandra4-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-dubbo-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-ecs-logging-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-es-restclient-plugin-5_6 | 1.55.6 |  | java-archive-cataloger |
| apm-es-restclient-plugin-6_4 | 1.55.6 |  | java-archive-cataloger |
| apm-es-restclient-plugin-7_x | 1.55.6 |  | java-archive-cataloger |
| apm-es-restclient-plugin-8_x | 1.55.6 |  | java-archive-cataloger |
| apm-es-restclient-plugin-common | 1.55.6 |  | java-archive-cataloger |
| apm-finagle-httpclient-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-grails-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-grpc-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-hibernate-search-plugin-5_x | 1.55.6 |  | java-archive-cataloger |
| apm-hibernate-search-plugin-6_x | 1.55.6 |  | java-archive-cataloger |
| apm-hibernate-search-plugin-common | 1.55.6 |  | java-archive-cataloger |
| apm-httpclient-core | 1.55.6 |  | java-archive-cataloger |
| apm-httpserver-core | 1.55.6 |  | java-archive-cataloger |
| apm-jakarta-websocket-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-java-concurrent-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-java-ldap-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-javalin-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jaxrs-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jaxws-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jboss-logging-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jdbc-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jdk-httpclient-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jdk-httpserver-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jedis-4-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jedis-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jms-jakarta | 1.55.6 |  | java-archive-cataloger |
| apm-jms-javax | 1.55.6 |  | java-archive-cataloger |
| apm-jms-plugin-base | 1.55.6 |  | java-archive-cataloger |
| apm-jmx-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jsf-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-jul-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-kafka-base-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-kafka-headers-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-kafka-spring-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-lettuce-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-log4j1-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-log4j2-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-logback-plugin-impl | 1.55.6 |  | java-archive-cataloger |
| apm-logging-plugin-common | 1.55.6 |  | java-archive-cataloger |
| apm-micrometer-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-mongodb-common | 1.55.6 |  | java-archive-cataloger |
| apm-mongodb3-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-mongodb4-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-okhttp-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-opentelemetry-embedded-metrics-sdk | 1.55.6 |  | java-archive-cataloger |
| apm-opentelemetry-metrics-bridge-common | 1.55.6 |  | java-archive-cataloger |
| apm-opentelemetry-metrics-bridge-latest | 1.55.6 |  | java-archive-cataloger |
| apm-opentelemetry-metrics-bridge-v1_14 | 1.55.6 |  | java-archive-cataloger |
| apm-opentelemetry-metricsdk-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-opentelemetry-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-opentracing-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-process-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-profiling-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-quartz-common | 1.55.6 |  | java-archive-cataloger |
| apm-quartz-plugin-1 | 1.55.6 |  | java-archive-cataloger |
| apm-quartz-plugin-2 | 1.55.6 |  | java-archive-cataloger |
| apm-rabbitmq-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-rabbitmq-spring5 | 1.55.6 |  | java-archive-cataloger |
| apm-reactor-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-redis-common | 1.55.6 |  | java-archive-cataloger |
| apm-redisson-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-scala-concurrent-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-scheduled-annotation-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-servlet-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-slf4j-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-sparkjava-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-spring-resttemplate-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-spring-webclient-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-spring-webflux-common | 1.55.6 |  | java-archive-cataloger |
| apm-spring-webflux-common-spring5 | 1.55.6 |  | java-archive-cataloger |
| apm-spring-webflux-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-spring-webflux-spring5 | 1.55.6 |  | java-archive-cataloger |
| apm-spring-webmvc-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-spring-webmvc-spring5 | 1.55.6 |  | java-archive-cataloger |
| apm-struts-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-tomcat-logging-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-urlconnection-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-vertx-common | 1.55.6 |  | java-archive-cataloger |
| apm-vertx3-plugin | 1.55.6 |  | java-archive-cataloger |
| apm-vertx4-plugin | 1.55.6 |  | java-archive-cataloger |
| arns | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| arrow | 9.3.6 |  | java-archive-cataloger |
| arrow-format | 18.3.0 | Apache-2.0 | java-archive-cataloger |
| arrow-memory-core | 18.3.0 | Apache-2.0 | java-archive-cataloger |
| arrow-vector | 18.3.0 | Apache-2.0 | java-archive-cataloger |
| asm | 9.9 |  | java-archive-cataloger |
| asm | 9.9 |  | java-archive-cataloger |
| asm | 9.9 |  | java-archive-cataloger |
| asm | 9.9 |  | java-archive-cataloger |
| asm | 9.9 |  | java-archive-cataloger |
| asm-analysis | 9.9 |  | java-archive-cataloger |
| asm-analysis | 9.9 |  | java-archive-cataloger |
| asm-commons | 9.9 |  | java-archive-cataloger |
| asm-commons | 9.9 |  | java-archive-cataloger |
| asm-jdk-bridge | 0.0.13 |  | java-archive-cataloger |
| asm-tree | 9.9 |  | java-archive-cataloger |
| asm-tree | 9.9 |  | java-archive-cataloger |
| asm-tree | 9.9 |  | java-archive-cataloger |
| asm-util | 9.9 |  | java-archive-cataloger |
| audit-libs | 3.1.5-8.el9 |  | rpm-db-cataloger |
| auth | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| auth | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| aws-core | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| aws-core | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| aws-json-protocol | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| aws-query-protocol | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| aws-xml-protocol | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| azure-core | 1.51.0 |  | java-archive-cataloger |
| azure-core-http-netty | 1.15.3 |  | java-archive-cataloger |
| azure-identity | 1.13.2 |  | java-archive-cataloger |
| azure-json | 1.2.0 |  | java-archive-cataloger |
| azure-storage-blob | 12.27.1 |  | java-archive-cataloger |
| azure-storage-blob-batch | 12.23.1 |  | java-archive-cataloger |
| azure-storage-common | 12.26.1 |  | java-archive-cataloger |
| azure-storage-internal-avro | 12.12.1 |  | java-archive-cataloger |
| azure-xml | 1.1.0 |  | java-archive-cataloger |
| basesystem | 11-13.el9 |  | rpm-db-cataloger |
| bash | 5.1.8-9.el9 |  | rpm-db-cataloger |
| bc-fips | 1.0.2.6 |  | java-archive-cataloger |
| bcpg-fips | 1.0.7.1 |  | java-archive-cataloger |
| bcpkix-jdk18on | 1.84 |  | java-archive-cataloger |
| bcprov-jdk18on | 1.84 |  | java-archive-cataloger |
| bcutil-jdk18on | 1.84 |  | java-archive-cataloger |
| bedrockruntime | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| blob-cache | 9.3.6 |  | java-archive-cataloger |
| byte-buddy-dep | 1.18.7-jdk5 |  | java-archive-cataloger |
| bzip2-libs | 1.0.8-11.el9 |  | rpm-db-cataloger |
| ca-certificates | 2025.2.80_v9.0.305-91.el9 | MIT AND GPL-2.0-or-later | rpm-db-cataloger |
| checker-qual | 3.42.0 | MIT | java-archive-cataloger |
| checker-qual | 3.49.0 | MIT | java-archive-cataloger |
| checksums | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| checksums | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| checksums-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| checksums-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| cli-launcher | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| collate | 77.1 |  | java-archive-cataloger |
| collate | 77.1 |  | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.19.0 | Apache-2.0 | java-archive-cataloger |
| commons-collections4 | 4.5.0 | Apache-2.0 | java-archive-cataloger |
| commons-compress | 1.28.0 | Apache-2.0 | java-archive-cataloger |
| commons-io | 2.20.0 | Apache-2.0 | java-archive-cataloger |
| commons-lang3 | 3.18.0 | Apache-2.0 | java-archive-cataloger |
| commons-lang3 | 3.20.0 | Apache-2.0 | java-archive-cataloger |
| commons-lang3 | 3.9 | Apache-2.0 | java-archive-cataloger |
| commons-logging | 1.2 | Apache-2.0 | java-archive-cataloger |
| commons-logging | 1.2 | Apache-2.0 | java-archive-cataloger |
| commons-logging | 1.2 | Apache-2.0 | java-archive-cataloger |
| commons-logging | 1.2 | Apache-2.0 | java-archive-cataloger |
| commons-math3 | 3.6.1 | Apache-2.0 | java-archive-cataloger |
| commons-math3 | 3.6.1 | Apache-2.0 | java-archive-cataloger |
| commons-math3 | 3.6.1 | Apache-2.0 | java-archive-cataloger |
| commons-math3 | 3.6.1 | Apache-2.0 | java-archive-cataloger |
| commons-text | 1.4 | Apache-2.0 | java-archive-cataloger |
| compiler | 0.9.14 |  | java-archive-cataloger |
| compiler | 0.9.14 |  | java-archive-cataloger |
| compiler | 0.9.14 |  | java-archive-cataloger |
| concurrentlinkedhashmap-lru | 1.4.2 |  | java-archive-cataloger |
| content-type | 2.3 | Apache-2.0 | java-archive-cataloger |
| content-type | 2.3 | Apache-2.0 | java-archive-cataloger |
| core | 77.1 |  | java-archive-cataloger |
| core | 77.1 |  | java-archive-cataloger |
| coreutils-single | 8.32-41.el9_8 |  | rpm-db-cataloger |
| cryptacular | 1.2.5 |  | java-archive-cataloger |
| cryptacular | 1.2.5 |  | java-archive-cataloger |
| crypto-policies | 20260224-1.gitea0f072.el9_8 | LGPL-2.1-or-later | rpm-db-cataloger |
| curl-minimal | 7.76.1-40.el9 | MIT | rpm-db-cataloger |
| currdata | 77.1 |  | java-archive-cataloger |
| currdata | 77.1 |  | java-archive-cataloger |
| cuvs-java | 25.12.0 |  | java-archive-cataloger |
| cyrus-sasl-lib | 2.1.27-22.el9 |  | rpm-db-cataloger |
| data-streams | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| dejavu-sans-fonts | 2.37-18.el9 |  | rpm-db-cataloger |
| dnf-data | 4.14.0-34.el9_8 |  | rpm-db-cataloger |
| dot-prefix-validation | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| dsl-json | 1.9.3 |  | java-archive-cataloger |
| ecs-logging-core | 1.7.0 | Apache-2.0 | java-archive-cataloger |
| ecs-logging-core | 1.7.0 |  | java-archive-cataloger |
| elastic-apm-agent-java8 | 1.55.6 | Apache-2.0 | java-archive-cataloger |
| elastic-apm-agent-premain | 1.55.6 |  | java-archive-cataloger |
| elasticsearch | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-ansi-console | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-cli | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-core | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-core | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-dissect | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-dissect | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-dissect | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-entitlement | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-entitlement | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-entitlement-agent | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-entitlement-bridge | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-exponential-histogram | 9.3.6 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-geo | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-geoip-cli | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-gpu-codec | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-grok | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-h3 | 9.3.6 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-h3 | 9.3.6 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-log4j | 9.3.6 |  | java-archive-cataloger |
| elasticsearch-logging | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-lz4 | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-native | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-analysis-api | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-api | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-api | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-cli | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-scanner | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-rest-client | 9.3.6 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-rest-client | 9.3.6 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-rest-client | 9.3.6 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-rest-client-sniffer | 9.3.6 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-scripting-painless-spi | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-security-cli | 9.3.6 |  | java-archive-cataloger |
| elasticsearch-simdvec | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-sql-cli | 9.3.6 | Apache-2.0, LGPL-2.1-only | java-archive-cataloger |
| elasticsearch-ssl-config | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-ssl-config | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-ssl-config | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-ssl-config | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-tdigest | 9.3.6 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-x-content | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-x-content | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| endpoints-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| endpoints-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| eventstream | 1.0.1 |  | java-archive-cataloger |
| failureaccess | 1.0.1 | Apache-2.0 | java-archive-cataloger |
| failureaccess | 1.0.1 | Apache-2.0 | java-archive-cataloger |
| failureaccess | 1.0.1 | Apache-2.0 | java-archive-cataloger |
| failureaccess | 1.0.2 | Apache-2.0 | java-archive-cataloger |
| file-libs | 5.39-17.el9 |  | rpm-db-cataloger |
| filesystem | 3.16-5.el9 |  | rpm-db-cataloger |
| findutils | 1:4.8.0-7.el9 |  | rpm-db-cataloger |
| flatbuffers-java | 23.5.26 |  | java-archive-cataloger |
| fontbox | 3.0.5 | Apache-2.0 | java-archive-cataloger |
| fonts-filesystem | 1:2.0.5-7.el9.1 | MIT | rpm-db-cataloger |
| gawk | 5.1.0-6.el9 |  | rpm-db-cataloger |
| gax | 2.63.1 |  | java-archive-cataloger |
| gax-httpjson | 0.105.1 |  | java-archive-cataloger |
| gax-httpjson | 2.63.1 |  | java-archive-cataloger |
| gdbm-libs | 1:1.23-1.el9 |  | rpm-db-cataloger |
| geoip2 | 4.2.1 |  | java-archive-cataloger |
| glib2 | 2.68.4-19.el9_8.1 |  | rpm-db-cataloger |
| glibc | 2.34-270.el9_8 | LGPL-2.1-or-later AND SunPro AND LGPL-2.1-or-later WITH GCC-exception-2.0 AND BSD-3-Clause AND GPL-2.0-or-later AND LGPL-2.1-or-later WITH GNU-compiler-exception AND GPL-2.0-only AND ISC AND LicenseRef-Fedora-Public-Domain AND HPND AND CMU-Mach AND LGPL-2.0-or-later AND Unicode-3.0 AND GFDL-1.1-or-later AND GPL-1.0-or-later AND FSFUL AND MIT AND Inner-Net-2.0 AND X11 AND GPL-2.0-or-later WITH GCC-exception-2.0 AND GFDL-1.3-only AND GFDL-1.1-only AND GPL-3.0-or-later AND GPL-3.0-or-later WITH Autoconf-exception-generic-3.0 AND GPL-3.0-or-later WITH Texinfo-exception | rpm-db-cataloger |
| glibc-common | 2.34-270.el9_8 | LGPL-2.1-or-later AND SunPro AND LGPL-2.1-or-later WITH GCC-exception-2.0 AND BSD-3-Clause AND GPL-2.0-or-later AND LGPL-2.1-or-later WITH GNU-compiler-exception AND GPL-2.0-only AND ISC AND LicenseRef-Fedora-Public-Domain AND HPND AND CMU-Mach AND LGPL-2.0-or-later AND Unicode-3.0 AND GFDL-1.1-or-later AND GPL-1.0-or-later AND FSFUL AND MIT AND Inner-Net-2.0 AND X11 AND GPL-2.0-or-later WITH GCC-exception-2.0 AND GFDL-1.3-only AND GFDL-1.1-only AND GPL-3.0-or-later AND GPL-3.0-or-later WITH Autoconf-exception-generic-3.0 AND GPL-3.0-or-later WITH Texinfo-exception | rpm-db-cataloger |
| glibc-minimal-langpack | 2.34-270.el9_8 | LGPL-2.1-or-later AND SunPro AND LGPL-2.1-or-later WITH GCC-exception-2.0 AND BSD-3-Clause AND GPL-2.0-or-later AND LGPL-2.1-or-later WITH GNU-compiler-exception AND GPL-2.0-only AND ISC AND LicenseRef-Fedora-Public-Domain AND HPND AND CMU-Mach AND LGPL-2.0-or-later AND Unicode-3.0 AND GFDL-1.1-or-later AND GPL-1.0-or-later AND FSFUL AND MIT AND Inner-Net-2.0 AND X11 AND GPL-2.0-or-later WITH GCC-exception-2.0 AND GFDL-1.3-only AND GFDL-1.1-only AND GPL-3.0-or-later AND GPL-3.0-or-later WITH Autoconf-exception-generic-3.0 AND GPL-3.0-or-later WITH Texinfo-exception | rpm-db-cataloger |
| gmp | 1:6.2.0-13.el9 |  | rpm-db-cataloger |
| gnupg2 | 2.3.3-5.el9_7 |  | rpm-db-cataloger |
| gnutls | 3.8.10-4.el9_8 |  | rpm-db-cataloger |
| gobject-introspection | 1.68.0-11.el9 |  | rpm-db-cataloger |
| google-api-client | 2.1.1 | Apache-2.0 | java-archive-cataloger |
| google-api-client | 2.7.2 | Apache-2.0 | java-archive-cataloger |
| google-api-services-storage | v1-rev20250224-2.0.0 |  | java-archive-cataloger |
| google-api-services-storage-v1-rev20250224 | 2.0.0 |  | java-archive-cataloger |
| google-auth-library-credentials | 1.11.0 |  | java-archive-cataloger |
| google-auth-library-credentials | 1.33.1 |  | java-archive-cataloger |
| google-auth-library-oauth2-http | 1.11.0 |  | java-archive-cataloger |
| google-auth-library-oauth2-http | 1.33.1 |  | java-archive-cataloger |
| google-cloud-core | 2.53.1 |  | java-archive-cataloger |
| google-cloud-core-http | 2.53.1 |  | java-archive-cataloger |
| google-cloud-storage | 2.50.0 | Apache-2.0 | java-archive-cataloger |
| google-http-client | 1.42.3 | Apache-2.0 | java-archive-cataloger |
| google-http-client | 1.46.3 | Apache-2.0 | java-archive-cataloger |
| google-http-client-appengine | 1.42.3 |  | java-archive-cataloger |
| google-http-client-appengine | 1.46.3 |  | java-archive-cataloger |
| google-http-client-gson | 1.42.3 |  | java-archive-cataloger |
| google-http-client-gson | 1.46.3 |  | java-archive-cataloger |
| google-http-client-jackson2 | 1.42.3 |  | java-archive-cataloger |
| google-http-client-jackson2 | 1.46.3 |  | java-archive-cataloger |
| google-oauth-client | 1.34.1 | Apache-2.0 | java-archive-cataloger |
| google-oauth-client | 1.34.1 | Apache-2.0 | java-archive-cataloger |
| gpg-pubkey | 5a6340b3-6229229e |  | rpm-db-cataloger |
| gpg-pubkey | fd431d51-4ae0493b |  | rpm-db-cataloger |
| gpgme | 1.15.1-6.el9 |  | rpm-db-cataloger |
| grep | 3.6-5.el9 |  | rpm-db-cataloger |
| grpc-api | 1.70.0 |  | java-archive-cataloger |
| grpc-context | 1.49.2 |  | java-archive-cataloger |
| gson | 2.10 |  | java-archive-cataloger |
| gson | 2.11.0 |  | java-archive-cataloger |
| gson | 2.12.1 | Apache-2.0 | java-archive-cataloger |
| gson | 2.12.1 |  | java-archive-cataloger |
| gson | 2.12.1 | Apache-2.0 | java-archive-cataloger |
| guava | 32.0.1-jre | Apache-2.0 | java-archive-cataloger |
| guava | 32.0.1-jre | Apache-2.0 | java-archive-cataloger |
| guava | 32.0.1-jre | Apache-2.0 | java-archive-cataloger |
| guava | 32.0.1-jre | Apache-2.0 | java-archive-cataloger |
| guava | 33.4.0-jre | Apache-2.0 | java-archive-cataloger |
| health-shards-availability | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| hppc | 0.8.1 | Apache-2.0 | java-archive-cataloger |
| http-auth | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| http-auth | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| http-auth-aws | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| http-auth-aws | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| http-auth-aws-eventstream | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| http-auth-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| http-auth-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| http-client-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| http-client-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| httpasyncclient | 4.1.5 | Apache-2.0 | java-archive-cataloger |
| httpasyncclient | 4.1.5 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient-cache | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient-cache | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient5 | 5.5 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore-nio | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore-nio | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore5 | 5.3.5 | Apache-2.0 | java-archive-cataloger |
| httpcore5-h2 | 5.3.5 | Apache-2.0 | java-archive-cataloger |
| icu4j | 77.1 | Unicode-3.0 | java-archive-cataloger |
| icu4j | 77.1 | Unicode-3.0 | java-archive-cataloger |
| identity-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| identity-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| ingest-attachment | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| ingest-common | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| ingest-geoip | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| ingest-otel | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| ingest-user-agent | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| isorelax | 20090621 |  | java-archive-cataloger |
| jackson-annotations | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-annotations | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-annotations | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-annotations | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 |  | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.17.2 |  | java-archive-cataloger |
| jackson-core | 2.17.2 |  | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-dataformat-cbor | 2.15.0 |  | java-archive-cataloger |
| jackson-dataformat-cbor | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-dataformat-cbor | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-cbor | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-smile | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-smile | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-xml | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-dataformat-yaml | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-yaml | 2.17.2 |  | java-archive-cataloger |
| jackson-datatype-jsr310 | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-module-jaxb-annotations | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jakarta.activation | 1.2.1 | BSD-3-Clause | java-archive-cataloger |
| jakarta.activation-api | 1.2.1 | BSD-3-Clause | java-archive-cataloger |
| jakarta.mail | 1.6.8 |  | java-archive-cataloger |
| jakarta.mail | 1.6.8 |  | java-archive-cataloger |
| jakarta.xml.bind-api | 2.3.3 | BSD-3-Clause | java-archive-cataloger |
| jansi | 2.4.0 | Apache-2.0 | java-archive-cataloger |
| java-support | 8.4.0 |  | java-archive-cataloger |
| java-support | 8.4.0 |  | java-archive-cataloger |
| java-version-checker | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| jcip-annotations | 1.0 |  | java-archive-cataloger |
| jcip-annotations | 1.0-1 |  | java-archive-cataloger |
| jcip-annotations | 1.0-1 |  | java-archive-cataloger |
| jcip-annotations | 1.0-1 |  | java-archive-cataloger |
| jcl-over-slf4j | 2.0.17 | Apache-2.0 | java-archive-cataloger |
| jcodings | 1.0.63 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jctools-core | 4.0.6 |  | java-archive-cataloger |
| jdk | 26.0.1+8-34 |  | java-jvm-cataloger |
| jempbox | 1.8.17 | Apache-2.0 | java-archive-cataloger |
| jline-reader | 3.21.0 |  | java-archive-cataloger |
| jline-style | 3.21.0 |  | java-archive-cataloger |
| jline-terminal | 3.21.0 |  | java-archive-cataloger |
| jline-terminal-jna | 3.21.0 |  | java-archive-cataloger |
| jna | 5.12.1 | Apache-2.0, LGPL-2.1-only | java-archive-cataloger |
| jna-platform | 5.12.1 | Apache-2.0, LGPL-2.1-only | java-archive-cataloger |
| joda-time | 2.10.10 |  | java-archive-cataloger |
| joda-time | 2.10.14 |  | java-archive-cataloger |
| joni | 2.2.6 |  | java-archive-cataloger |
| jopt-simple | 5.0.2 |  | java-archive-cataloger |
| jopt-simple | 5.0.2 |  | java-archive-cataloger |
| jrt-fs | 26.0.1 |  | java-archive-cataloger |
| json-c | 0.14-11.el9 | MIT | rpm-db-cataloger |
| json-glib | 1.6.6-1.el9 |  | rpm-db-cataloger |
| json-schema-validator | 1.0.48 |  | java-archive-cataloger |
| json-smart | 2.5.2 | Apache-2.0 | java-archive-cataloger |
| json-smart | 2.5.2 | Apache-2.0 | java-archive-cataloger |
| json-utils | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| json-utils | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| jsoup | 1.21.2 |  | java-archive-cataloger |
| jsr305 | 3.0.2 | Apache-2.0 | java-archive-cataloger |
| jsr305 | 3.0.2 | Apache-2.0 | java-archive-cataloger |
| jts-core | 1.20.0 |  | java-archive-cataloger |
| jul-ecs-formatter | 1.7.0 |  | java-archive-cataloger |
| juniversalchardet | 1.0.3 |  | java-archive-cataloger |
| keystore-cli | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| keyutils-libs | 1.6.3-1.el9 |  | rpm-db-cataloger |
| kibana | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| krb5-libs | 1.21.1-10.el9_8 | MIT | rpm-db-cataloger |
| lang-expression | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-mustache | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-mustache | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-mustache | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-painless | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-tag | 1.7 | Apache-2.0 | java-archive-cataloger |
| lang-tag | 1.7 | Apache-2.0 | java-archive-cataloger |
| langdata | 77.1 |  | java-archive-cataloger |
| langdata | 77.1 |  | java-archive-cataloger |
| langpacks-core-en | 3.0-16.el9 |  | rpm-db-cataloger |
| langpacks-core-font-en | 3.0-16.el9 |  | rpm-db-cataloger |
| langpacks-en | 3.0-16.el9 |  | rpm-db-cataloger |
| legacy-geo | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| libacl | 2.3.1-4.el9 |  | rpm-db-cataloger |
| libarchive | 3.5.3-9.el9_7 |  | rpm-db-cataloger |
| libassuan | 2.5.5-3.el9 |  | rpm-db-cataloger |
| libattr | 2.5.1-3.el9 |  | rpm-db-cataloger |
| libblkid | 2.37.4-25.el9 |  | rpm-db-cataloger |
| libcap | 2.48-10.el9_8.1 |  | rpm-db-cataloger |
| libcap-ng | 0.8.2-7.el9 |  | rpm-db-cataloger |
| libcom_err | 1.46.5-8.el9 | MIT | rpm-db-cataloger |
| libcurl-minimal | 7.76.1-40.el9 | MIT | rpm-db-cataloger |
| libdnf | 0.69.0-18.el9 |  | rpm-db-cataloger |
| libevent | 2.1.12-8.el9_4 |  | rpm-db-cataloger |
| libffi | 3.4.2-8.el9 | MIT | rpm-db-cataloger |
| libgcc | 11.5.0-14.el9 |  | rpm-db-cataloger |
| libgcrypt | 1.10.0-11.el9 |  | rpm-db-cataloger |
| libgpg-error | 1.42-5.el9 |  | rpm-db-cataloger |
| libibverbs | 61.0-2.el9 |  | rpm-db-cataloger |
| libidn2 | 2.3.0-7.el9 |  | rpm-db-cataloger |
| libksba | 1.5.1-7.el9 |  | rpm-db-cataloger |
| libmodulemd | 2.13.0-2.el9 | MIT | rpm-db-cataloger |
| libmount | 2.37.4-25.el9 |  | rpm-db-cataloger |
| libnghttp2 | 1.43.0-6.el9_8.1 | MIT | rpm-db-cataloger |
| libnl3 | 3.11.0-1.el9 | LGPL-2.1-only | rpm-db-cataloger |
| libpcap | 14:1.10.0-4.el9 |  | rpm-db-cataloger |
| libpeas | 1.30.0-4.el9 |  | rpm-db-cataloger |
| librepo | 1.19.0-1.el9 | LGPL-2.1-or-later | rpm-db-cataloger |
| libreport-filesystem | 2.15.2-6.el9 |  | rpm-db-cataloger |
| librhsm | 0.0.3-9.el9 |  | rpm-db-cataloger |
| libselinux | 3.6-3.el9 |  | rpm-db-cataloger |
| libsemanage | 3.6-5.el9_6 |  | rpm-db-cataloger |
| libsepol | 3.6-3.el9 |  | rpm-db-cataloger |
| libsigsegv | 2.13-4.el9 |  | rpm-db-cataloger |
| libsmartcols | 2.37.4-25.el9 |  | rpm-db-cataloger |
| libsolv | 0.7.24-5.el9_8 |  | rpm-db-cataloger |
| libstdc++ | 11.5.0-14.el9 |  | rpm-db-cataloger |
| libtasn1 | 4.16.0-10.el9_8 |  | rpm-db-cataloger |
| libtool-ltdl | 2.4.6-46.el9 |  | rpm-db-cataloger |
| libunistring | 0.9.10-15.el9 |  | rpm-db-cataloger |
| libusbx | 1.0.30-1.el9_8 |  | rpm-db-cataloger |
| libuuid | 2.37.4-25.el9 |  | rpm-db-cataloger |
| libverto | 0.3.2-3.el9 | MIT | rpm-db-cataloger |
| libxcrypt | 4.4.18-3.el9 |  | rpm-db-cataloger |
| libxml2 | 2.9.13-14.el9_8.1 | MIT | rpm-db-cataloger |
| libyaml | 0.2.5-7.el9 | MIT | rpm-db-cataloger |
| libzstd | 1.5.5-1.el9 |  | rpm-db-cataloger |
| log4j-1.2-api | 2.26.0 |  | java-archive-cataloger |
| log4j-1.2-api | 2.26.0 |  | java-archive-cataloger |
| log4j-1.2-api | 2.26.0 |  | java-archive-cataloger |
| log4j-api | 2.25.4 | Apache-2.0 | java-archive-cataloger |
| log4j-api | 2.26.0 |  | java-archive-cataloger |
| log4j-core | 2.25.4 | Apache-2.0 | java-archive-cataloger |
| log4j-core | 2.26.0 | Apache-2.0 | java-archive-cataloger |
| log4j-ecs-layout | 1.7.0 |  | java-archive-cataloger |
| log4j-slf4j-impl | 2.25.4 | Apache-2.0 | java-archive-cataloger |
| log4j-slf4j2-impl | 2.26.0 |  | java-archive-cataloger |
| log4j-slf4j2-impl | 2.26.0 |  | java-archive-cataloger |
| log4j2-ecs-layout | 1.7.0 | Apache-2.0 | java-archive-cataloger |
| log4j2-ecs-layout | 1.7.0 |  | java-archive-cataloger |
| logback-ecs-encoder | 1.7.0 |  | java-archive-cataloger |
| lua-libs | 5.4.4-4.el9 | MIT | rpm-db-cataloger |
| lucene-analysis-common | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-icu | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-icu | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-kuromoji | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-morfologik | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-smartcn | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-stempel | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-backward-codecs | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-codecs | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-core | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-expressions | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-facet | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-grouping | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-highlighter | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-join | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-memory | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-misc | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-queries | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-queryparser | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-sandbox | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-spatial-extras | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-spatial3d | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-spatial3d | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-suggest | 10.3.2 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lz4-java | 1.10.1 |  | java-archive-cataloger |
| lz4-libs | 1.9.3-5.el9 |  | rpm-db-cataloger |
| mapbox-vector-tile | 3.1.0 |  | java-archive-cataloger |
| mapper-extras | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| mapper-extras | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| maxmind-db | 3.1.1 |  | java-archive-cataloger |
| metrics-core | 4.1.4 | Apache-2.0 | java-archive-cataloger |
| metrics-core | 4.1.4 | Apache-2.0 | java-archive-cataloger |
| metrics-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| metrics-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| microdnf | 3.9.1-3.el9 |  | rpm-db-cataloger |
| ml-package-loader | 9.3.6 |  | java-archive-cataloger |
| morfologik-fsa | 2.1.1 |  | java-archive-cataloger |
| morfologik-stemming | 2.1.1 |  | java-archive-cataloger |
| morfologik-ukrainian-search | 3.7.5 |  | java-archive-cataloger |
| mpfr | 4.1.0-10.el9 |  | rpm-db-cataloger |
| msal4j | 1.16.2 |  | java-archive-cataloger |
| msal4j-persistence-extension | 1.3.0 |  | java-archive-cataloger |
| ncurses-base | 6.2-12.20210508.el9 | MIT | rpm-db-cataloger |
| ncurses-libs | 6.2-12.20210508.el9 | MIT | rpm-db-cataloger |
| nettle | 3.10.1-1.el9 |  | rpm-db-cataloger |
| netty-buffer | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-buffer | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-buffer | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-buffer | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-dns | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-dns | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http2 | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http2 | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-socks | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-common | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-common | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-common | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-common | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler-proxy | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-nio-client | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| netty-resolver | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver-dns | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver-dns | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-classes-epoll | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-native-unix-common | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-native-unix-common | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-native-unix-common | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-native-unix-common | 4.1.135.Final | Apache-2.0 | java-archive-cataloger |
| nimbus-jose-jwt | 10.0.2 | Apache-2.0 | java-archive-cataloger |
| nimbus-jose-jwt | 10.0.2 | Apache-2.0 | java-archive-cataloger |
| nmap-ncat | 3:7.92-5.el9 |  | rpm-db-cataloger |
| npth | 1.6-8.el9 |  | rpm-db-cataloger |
| oauth2-oidc-sdk | 11.22.2 |  | java-archive-cataloger |
| oauth2-oidc-sdk | 11.22.2 |  | java-archive-cataloger |
| ojalgo | 51.2.0 | MIT | java-archive-cataloger |
| opencensus-api | 0.31.1 |  | java-archive-cataloger |
| opencensus-api | 0.31.1 |  | java-archive-cataloger |
| opencensus-contrib-http-util | 0.31.1 |  | java-archive-cataloger |
| opencensus-contrib-http-util | 0.31.1 |  | java-archive-cataloger |
| openldap | 2.6.8-4.el9 | OLDAP-2.8 | rpm-db-cataloger |
| opensaml-core | 4.3.0 |  | java-archive-cataloger |
| opensaml-core | 4.3.0 |  | java-archive-cataloger |
| opensaml-messaging-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-messaging-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-messaging-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-messaging-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-profile-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-profile-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-profile-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-profile-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-saml-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-saml-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-saml-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-saml-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-security-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-security-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-security-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-security-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-soap-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-soap-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-soap-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-soap-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-storage-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-storage-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-storage-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-storage-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-xmlsec-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-xmlsec-api | 4.3.0 |  | java-archive-cataloger |
| opensaml-xmlsec-impl | 4.3.0 |  | java-archive-cataloger |
| opensaml-xmlsec-impl | 4.3.0 |  | java-archive-cataloger |
| openssl-fips-provider | 3.0.7-11.el9_8 |  | rpm-db-cataloger |
| openssl-fips-provider-so | 3.0.7-11.el9_8 |  | rpm-db-cataloger |
| openssl-libs | 1:3.5.5-4.el9_8 | Apache-2.0 | rpm-db-cataloger |
| opentelemetry-api | 1.47.0 |  | java-archive-cataloger |
| opentelemetry-api | 1.62.0 |  | java-archive-cataloger |
| opentelemetry-common | 1.62.0 |  | java-archive-cataloger |
| opentelemetry-context | 1.47.0 |  | java-archive-cataloger |
| opentelemetry-context | 1.62.0 |  | java-archive-cataloger |
| opentelemetry-semconv | 1.21.0-alpha |  | java-archive-cataloger |
| owasp-java-html-sanitizer | 20211018.2 | Apache-2.0 | java-archive-cataloger |
| p11-kit | 0.26.2-1.el9 | BSD-3-Clause | rpm-db-cataloger |
| p11-kit-trust | 0.26.2-1.el9 | BSD-3-Clause | rpm-db-cataloger |
| parent-join | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| pcre | 8.44-4.el9 |  | rpm-db-cataloger |
| pcre2 | 10.40-6.el9 |  | rpm-db-cataloger |
| pcre2-syntax | 10.40-6.el9 |  | rpm-db-cataloger |
| pdfbox | 3.0.5 | Apache-2.0 | java-archive-cataloger |
| pdfbox-io | 3.0.5 | Apache-2.0 | java-archive-cataloger |
| percolator | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| poi | 5.4.1 | Apache-2.0, MIT | java-archive-cataloger |
| poi-ooxml | 5.4.1 | Apache-2.0, MIT | java-archive-cataloger |
| poi-ooxml-lite | 5.4.1 | Apache-2.0, MIT | java-archive-cataloger |
| poi-scratchpad | 5.4.1 | Apache-2.0, MIT | java-archive-cataloger |
| popt | 1.18-8.el9 | MIT | rpm-db-cataloger |
| procps-ng | 3.3.17-14.el9 |  | rpm-db-cataloger |
| profiles | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| profiles | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| proto-google-cloud-storage-v2 | 2.50.0 |  | java-archive-cataloger |
| proto-google-common-protos | 2.54.1 | Apache-2.0 | java-archive-cataloger |
| proto-google-iam-v1 | 1.49.1 | Apache-2.0 | java-archive-cataloger |
| proto-google-iam-v1 | 1.6.2 | Apache-2.0 | java-archive-cataloger |
| protobuf-java | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java | 4.32.0 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java-util | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java-util | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protocol-core | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| protocol-core | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| rank-eval | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| rank-rrf | 9.3.6 |  | java-archive-cataloger |
| rank-vectors | 9.3.6 |  | java-archive-cataloger |
| reactive-streams | 1.0.4 |  | java-archive-cataloger |
| reactive-streams | 1.0.4 |  | java-archive-cataloger |
| reactive-streams | 1.0.4 |  | java-archive-cataloger |
| reactive-streams-tck | 1.0.4 |  | java-archive-cataloger |
| reactor-core | 3.4.38 |  | java-archive-cataloger |
| reactor-netty-core | 1.0.45 |  | java-archive-cataloger |
| reactor-netty-http | 1.0.45 |  | java-archive-cataloger |
| readline | 8.1-4.el9 |  | rpm-db-cataloger |
| redhat-release | 9.8-1.0.el9 |  | rpm-db-cataloger |
| regiondata | 77.1 |  | java-archive-cataloger |
| regiondata | 77.1 |  | java-archive-cataloger |
| regions | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| regions | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| reindex | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| reindex | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| reindex-management | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| repository-azure | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| repository-gcs | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| repository-s3 | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| repository-url | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| rest-root | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| retries | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| retries | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| retries-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| retries-spi | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| rootfiles | 8.1-35.el9 |  | rpm-db-cataloger |
| rpm | 4.16.1.3-40.el9 |  | rpm-db-cataloger |
| rpm-libs | 4.16.1.3-40.el9 |  | rpm-db-cataloger |
| runtime-fields-common | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| s2-geometry-library-java | 1.0.1 |  | java-archive-cataloger |
| s3 | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| sagemakerruntime | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| sdk-core | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| sdk-core | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| sed | 4.8-10.el9 |  | rpm-db-cataloger |
| server-cli | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| setup | 2.13.7-10.el9 |  | rpm-db-cataloger |
| shadow-utils | 2:4.9-16.el9 |  | rpm-db-cataloger |
| siv-mode | 1.5.2 |  | java-archive-cataloger |
| slf4j-api | 1.7.36 |  | java-archive-cataloger |
| slf4j-api | 2.0.17 |  | java-archive-cataloger |
| slf4j-api | 2.0.17 |  | java-archive-cataloger |
| slf4j-api | 2.0.17 |  | java-archive-cataloger |
| slf4j-api | 2.0.17 |  | java-archive-cataloger |
| slf4j-api | 2.0.17 |  | java-archive-cataloger |
| slf4j-nop | 2.0.17 |  | java-archive-cataloger |
| slf4j-nop | 2.0.17 |  | java-archive-cataloger |
| slf4j-nop | 2.0.17 |  | java-archive-cataloger |
| slf4j-nop | 2.0.17 |  | java-archive-cataloger |
| snakeyaml | 2.0 |  | java-archive-cataloger |
| snakeyaml | 2.0 |  | java-archive-cataloger |
| spatial | 9.3.6 |  | java-archive-cataloger |
| spatial4j | 0.7 | Apache-2.0 | java-archive-cataloger |
| sql-action | 9.3.6 |  | java-archive-cataloger |
| sql-proto | 9.3.6 |  | java-archive-cataloger |
| sqlite-libs | 3.34.1-10.el9_8 |  | rpm-db-cataloger |
| stax2-api | 4.2.2 |  | java-archive-cataloger |
| streams | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| sts | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| super-csv | 2.4.0 | Apache-2.0 | java-archive-cataloger |
| systemd-libs | 252-67.el9_8.4 |  | rpm-db-cataloger |
| third-party-jackson-core | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| third-party-jackson-core | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| threetenbp | 1.7.0 |  | java-archive-cataloger |
| tika-core | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-langdetect-tika | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-apple-module | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-html-module | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-microsoft-module | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-miscoffice-module | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-pdf-module | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-text-module | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-xml-module | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-xmp-commons | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-zip-commons | 3.2.3 | Apache-2.0 | java-archive-cataloger |
| transform | 9.3.6 |  | java-archive-cataloger |
| translit | 77.1 |  | java-archive-cataloger |
| translit | 77.1 |  | java-archive-cataloger |
| transport-netty4 | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| transport-netty4 | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| transport-netty4 | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| tzdata | 2026b-1.el9 |  | rpm-db-cataloger |
| unboundid-ldapsdk | 7.0.3 | GPL-2.0-only, LGPL-2.1-only | java-archive-cataloger |
| unzip | 6.0-60.el9 |  | rpm-db-cataloger |
| utils | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| utils | 2.31.78 | Apache-2.0 | java-archive-cataloger |
| vector-tile | 9.3.6 |  | java-archive-cataloger |
| weak-lock-free | 0.18 |  | java-archive-cataloger |
| windows-service-cli | 9.3.6 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| woodstox-core | 6.7.0 | Apache-2.0 | java-archive-cataloger |
| x-pack-aggregate-metric | 9.3.6 |  | java-archive-cataloger |
| x-pack-analytics | 9.3.6 |  | java-archive-cataloger |
| x-pack-analytics | 9.3.6 |  | java-archive-cataloger |
| x-pack-apm-data | 9.3.6 |  | java-archive-cataloger |
| x-pack-async | 9.3.6 |  | java-archive-cataloger |
| x-pack-async-search | 9.3.6 |  | java-archive-cataloger |
| x-pack-autoscaling | 9.3.6 |  | java-archive-cataloger |
| x-pack-ccr | 9.3.6 |  | java-archive-cataloger |
| x-pack-constant-keyword | 9.3.6 |  | java-archive-cataloger |
| x-pack-core | 9.3.6 |  | java-archive-cataloger |
| x-pack-counted-keyword | 9.3.6 |  | java-archive-cataloger |
| x-pack-deprecation | 9.3.6 |  | java-archive-cataloger |
| x-pack-diskbbq | 9.3.6 |  | java-archive-cataloger |
| x-pack-downsample | 9.3.6 |  | java-archive-cataloger |
| x-pack-enrich | 9.3.6 |  | java-archive-cataloger |
| x-pack-ent-search | 9.3.6 |  | java-archive-cataloger |
| x-pack-eql | 9.3.6 |  | java-archive-cataloger |
| x-pack-esql | 9.3.6 |  | java-archive-cataloger |
| x-pack-esql-compute | 9.3.6 |  | java-archive-cataloger |
| x-pack-esql-compute-ann | 9.3.6 |  | java-archive-cataloger |
| x-pack-esql-core | 9.3.6 |  | java-archive-cataloger |
| x-pack-exponential-histogram | 9.3.6 |  | java-archive-cataloger |
| x-pack-fleet | 9.3.6 |  | java-archive-cataloger |
| x-pack-frozen-indices | 9.3.6 |  | java-archive-cataloger |
| x-pack-geoip-enterprise-downloader | 9.3.6 |  | java-archive-cataloger |
| x-pack-gpu | 9.3.6 |  | java-archive-cataloger |
| x-pack-graph | 9.3.6 |  | java-archive-cataloger |
| x-pack-identity-provider | 9.3.6 |  | java-archive-cataloger |
| x-pack-ilm | 9.3.6 |  | java-archive-cataloger |
| x-pack-inference | 9.3.6 |  | java-archive-cataloger |
| x-pack-kql | 9.3.6 |  | java-archive-cataloger |
| x-pack-kql | 9.3.6 |  | java-archive-cataloger |
| x-pack-logsdb | 9.3.6 |  | java-archive-cataloger |
| x-pack-logstash | 9.3.6 |  | java-archive-cataloger |
| x-pack-mapper-version | 9.3.6 |  | java-archive-cataloger |
| x-pack-mapper-version | 9.3.6 |  | java-archive-cataloger |
| x-pack-mapper-version | 9.3.6 |  | java-archive-cataloger |
| x-pack-migrate | 9.3.6 |  | java-archive-cataloger |
| x-pack-ml | 9.3.6 |  | java-archive-cataloger |
| x-pack-monitoring | 9.3.6 |  | java-archive-cataloger |
| x-pack-old-lucene-versions | 9.3.6 |  | java-archive-cataloger |
| x-pack-otel-data | 9.3.6 |  | java-archive-cataloger |
| x-pack-profiling | 9.3.6 |  | java-archive-cataloger |
| x-pack-ql | 9.3.6 |  | java-archive-cataloger |
| x-pack-redact | 9.3.6 |  | java-archive-cataloger |
| x-pack-repositories-metering-api | 9.3.6 |  | java-archive-cataloger |
| x-pack-rollup | 9.3.6 |  | java-archive-cataloger |
| x-pack-searchable-snapshots | 9.3.6 |  | java-archive-cataloger |
| x-pack-searchbusinessrules | 9.3.6 |  | java-archive-cataloger |
| x-pack-security | 9.3.6 |  | java-archive-cataloger |
| x-pack-shutdown | 9.3.6 |  | java-archive-cataloger |
| x-pack-slm | 9.3.6 |  | java-archive-cataloger |
| x-pack-snapshot-based-recoveries | 9.3.6 |  | java-archive-cataloger |
| x-pack-snapshot-repo-test-kit | 9.3.6 |  | java-archive-cataloger |
| x-pack-sql | 9.3.6 |  | java-archive-cataloger |
| x-pack-stack | 9.3.6 |  | java-archive-cataloger |
| x-pack-template-resources | 9.3.6 |  | java-archive-cataloger |
| x-pack-text-structure | 9.3.6 |  | java-archive-cataloger |
| x-pack-unsigned-long | 9.3.6 |  | java-archive-cataloger |
| x-pack-voting-only-node | 9.3.6 |  | java-archive-cataloger |
| x-pack-watcher | 9.3.6 |  | java-archive-cataloger |
| x-pack-wildcard | 9.3.6 |  | java-archive-cataloger |
| x-pack-write-load-forecaster | 9.3.6 |  | java-archive-cataloger |
| xmlbeans | 5.3.0 | Apache-2.0, W3C-19980720 | java-archive-cataloger |
| xmlsec | 2.3.4 | Apache-2.0 | java-archive-cataloger |
| xmlsec | 2.3.4 | Apache-2.0 | java-archive-cataloger |
| xsdlib | 2022.7 |  | java-archive-cataloger |
| xz | 1.10 | 0BSD | java-archive-cataloger |
| xz-libs | 5.2.5-8.el9_0 |  | rpm-db-cataloger |
| zip | 3.0-35.el9 |  | rpm-db-cataloger |
| zlib | 1.2.11-40.el9 |  | rpm-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/elasticsearch-exporter

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| busybox | 1.37.0 |  | binary-classifier-cataloger |
| github.com/alecthomas/kingpin/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/alecthomas/units | v0.0.0-20240927000941-0f3dac36c52b |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.40.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.2 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.2 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.14 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.14 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.14 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/ini | v1.8.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.3 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.14 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.2 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.5 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.35.10 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.41.2 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.23.2 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/blang/semver/v4 | v4.0.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.6.0 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.3.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/imdario/mergo | v0.3.13 |  | go-module-binary-cataloger |
| github.com/jpillora/backoff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/mdlayher/socket | v0.4.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/vsock | v1.2.1 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/mwitkow/go-conntrack | v0.0.0-20190716064945-2f068394615f |  | go-module-binary-cataloger |
| github.com/prometheus-community/elasticsearch_exporter | v1.10.0+dirty |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.4 |  | go-module-binary-cataloger |
| github.com/prometheus/exporter-toolkit | v0.15.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.16.1 |  | go-module-binary-cataloger |
| github.com/xhit/go-str2duration/v2 | v2.1.0 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.3 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.45.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.47.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.18.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.31.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.13.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.10 |  | go-module-binary-cataloger |
| stdlib | go1.25.5 | BSD-3-Clause | go-module-binary-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/rabbit

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| .otp-run-deps | 20260622.200759 |  | apk-db-cataloger |
| alpine-baselayout | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.6-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.23.5-r0 | MIT | apk-db-cataloger |
| apk-tools | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| bash | 5.3.3-r1 | GPL-3.0-or-later | apk-db-cataloger |
| busybox | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates-bundle | 20260611-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| erlang | 27.3.4.13 |  | binary-classifier-cataloger |
| libapk | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| libcrypto3 | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| libgcc | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libintl | 0.24.1-r1 | LGPL-2.1-or-later | apk-db-cataloger |
| libncursesw | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| libproc2 | 4.0.5-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libssl3 | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| libstdc++ | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| musl | 1.2.5-r23 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r23 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| openssl | 3.5.7 |  | binary-classifier-cataloger |
| procps-ng | 4.0.5-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| readline | 8.3.1-r0 | GPL-3.0-or-later | apk-db-cataloger |
| scanelf | 1.3.8-r2 | GPL-2.0-only | apk-db-cataloger |
| skalibs-libs | 2.14.4.0-r0 | ISC | apk-db-cataloger |
| ssl_client | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| su-exec | 0.3-r0 | MIT | apk-db-cataloger |
| tzdata | 2026b-r0 |  | apk-db-cataloger |
| utmps-libs | 0.1.3.1-r0 | ISC | apk-db-cataloger |
| zlib | 1.3.2-r0 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/redis

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| .redis-rundeps | 20260507.173448 |  | apk-db-cataloger |
| alpine-baselayout | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.5-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.21.7-r0 | MIT | apk-db-cataloger |
| apk-tools | 2.14.6-r3 | GPL-2.0-only | apk-db-cataloger |
| busybox | 1.37.0-r14 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r14 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates-bundle | 20260413-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| libcap-ng | 0.8.5-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libcrypto3 | 3.3.7-r0 | Apache-2.0 | apk-db-cataloger |
| libssl3 | 3.3.7-r0 | Apache-2.0 | apk-db-cataloger |
| musl | 1.2.5-r11 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r11 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| redis | 7.4.9 |  | binary-classifier-cataloger |
| scanelf | 1.3.8-r1 | GPL-2.0-only | apk-db-cataloger |
| setpriv | 2.40.4-r1 | GPL-2.0-or-later | apk-db-cataloger |
| ssl_client | 1.37.0-r14 | GPL-2.0-only | apk-db-cataloger |
| tzdata | 2026b-r0 |  | apk-db-cataloger |
| zlib | 1.3.2-r0 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/redis-exporter

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/gomodule/redigo | v1.9.3 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.0 |  | go-module-binary-cataloger |
| github.com/mna/redisc | v1.4.0 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/oliver006/redis_exporter | v1.82.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.66.1 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.16.1 |  | go-module-binary-cataloger |
| github.com/sirupsen/logrus | v1.9.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.2 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.48.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.41.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.8 |  | go-module-binary-cataloger |
| stdlib | go1.26.1 | BSD-3-Clause | go-module-binary-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/tika

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| SparseBitSet | 1.3 |  | java-archive-cataloger |
| adduser | 3.153ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| angus-activation | 2.0.3 |  | java-archive-cataloger |
| apache-mime4j-core | 0.8.14 |  | java-archive-cataloger |
| apache-mime4j-dom | 0.8.14 |  | java-archive-cataloger |
| apt | 3.2.0 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, curl | dpkg-db-cataloger |
| attrs | 25.4.0 | MIT | python-installed-package-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| backports-tarfile | 1.2.0 |  | python-installed-package-cataloger |
| base-files | 14ubuntu6 | GPL-2.0-or-later | dpkg-db-cataloger |
| base-passwd | 3.6.8 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.3-2ubuntu1 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| bcrypt | 5.0.0 | Apache-2.0 | python-installed-package-cataloger |
| blinker | 1.9.0 |  | python-installed-package-cataloger |
| brotli | 1.2.0 | MIT | python-installed-package-cataloger |
| bsdutils | 1:2.41.3-3ubuntu2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| ca-certificates | 20260223 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| ca-certificates-java | 20260311 |  | dpkg-db-cataloger |
| ca-certificates-java | UNKNOWN |  | java-archive-cataloger |
| cabextract | 1.11-2build1 |  | dpkg-db-cataloger |
| commons-cli | 1.11.0 |  | java-archive-cataloger |
| commons-codec | 1.22.0 |  | java-archive-cataloger |
| commons-collections4 | 4.5.0 |  | java-archive-cataloger |
| commons-compress | 1.28.0 |  | java-archive-cataloger |
| commons-csv | 1.14.1 |  | java-archive-cataloger |
| commons-exec | 1.6.0 |  | java-archive-cataloger |
| commons-io | 2.22.0 |  | java-archive-cataloger |
| commons-lang3 | 3.20.0 |  | java-archive-cataloger |
| commons-math3 | 3.6.1 |  | java-archive-cataloger |
| contourpy | 1.3.3 | BSD-3-Clause | python-installed-package-cataloger |
| coreutils | 9.5-1ubuntu2+0.0.0~ubuntu25 | GPL-3.0-only | dpkg-db-cataloger |
| coreutils-from-uutils | 0.0.0~ubuntu25 | GPL-3.0-only | dpkg-db-cataloger |
| cryptography | 46.0.5 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| curl | 8.18.0-1ubuntu2.3 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| curvesapi | 1.08 |  | java-archive-cataloger |
| cxf-core | 4.0.11 |  | java-archive-cataloger |
| cxf-rt-frontend-jaxrs | 4.0.11 |  | java-archive-cataloger |
| cxf-rt-rs-client | 4.0.11 |  | java-archive-cataloger |
| cxf-rt-rs-security-cors | 4.0.11 |  | java-archive-cataloger |
| cxf-rt-security | 4.0.11 |  | java-archive-cataloger |
| cxf-rt-transports-http | 4.0.11 |  | java-archive-cataloger |
| cxf-rt-transports-http-jetty | 4.0.11 |  | java-archive-cataloger |
| cycler | 0.12.1 | BSD-3-Clause | python-installed-package-cataloger |
| dash | 0.5.12-12ubuntu3 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dbus | 1.16.2-2ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-bin | 1.16.2-2ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-daemon | 1.16.2-2ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-python | 1.4.0 |  | python-installed-package-cataloger |
| dbus-session-bus-common | 1.16.2-2ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-system-bus-common | 1.16.2-2ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dd-plist | 1.29 |  | java-archive-cataloger |
| debconf | 1.5.92 | BSD-2-Clause | dpkg-db-cataloger |
| debianutils | 5.23.2build1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| dec | 0.1.2 |  | java-archive-cataloger |
| decorator | 5.2.1 | BSD-2-Clause | python-installed-package-cataloger |
| diffutils | 1:3.12-1 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dirmngr | 2.4.8-4ubuntu3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| distro | 1.9.0 |  | python-installed-package-cataloger |
| distro-info | 1.15 | ISC | dpkg-db-cataloger |
| distro-info | 1.15 |  | python-installed-package-cataloger |
| distro-info-data | 0.68ubuntu0.1 | ISC | dpkg-db-cataloger |
| dpkg | 1.23.7ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.2-3ubuntu4 | 0BSD, Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| error_prone_annotations | 2.49.0 |  | java-archive-cataloger |
| failureaccess | 1.0.3 |  | java-archive-cataloger |
| findutils | 4.10.0-3build2 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| fontbox | 3.0.7 |  | java-archive-cataloger |
| fontconfig | 2.17.1-3ubuntu1 | HPND-sell-variant | dpkg-db-cataloger |
| fontconfig-config | 2.17.1-3ubuntu1 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-8build1 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-dejavu-mono | 2.37-8build1 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-freefont-ttf | 20211204+svn4273-4build1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-liberation | 1:2.1.5-3build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-lyx | 2.5.0-1 | BSD-3-Clause, BSL-1.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| fonttools | 4.61.1 | MIT | python-installed-package-cataloger |
| gcc-16-base | 16-20260322-1ubuntu1 | Apache-2.0, GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| gdal | 3.12.2 | MIT | python-installed-package-cataloger |
| gdal-bin | 3.12.2+dfsg-1build2 | Apache-2.0, BSD-3-Clause, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| gdal-data | 3.12.2+dfsg-1build2 | Apache-2.0, BSD-3-Clause, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| gdal-plugins | 3.12.2+dfsg-1build2 | Apache-2.0, BSD-3-Clause, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| gir1.2-girepository-3.0 | 2.88.0-1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| gir1.2-glib-2.0 | 2.88.0-1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| gir1.2-packagekitglib-1.0 | 1.3.4-3ubuntu1 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| github.com/GehirnInc/crypt | v0.0.0-20230320061759-8cc1b52080c5 |  | go-module-binary-cataloger |
| github.com/canonical/go-flags | v0.0.0-20230403090104-105d09a091b8 |  | go-module-binary-cataloger |
| github.com/canonical/pebble | v1.30.2-0.20260416224941-1b3384178e3f |  | go-module-binary-cataloger |
| github.com/canonical/x-go | v0.0.0-20230522092633-7947a7587f5b |  | go-module-binary-cataloger |
| github.com/gorilla/mux | v1.8.1 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.1 |  | go-module-binary-cataloger |
| github.com/pkg/term | v1.1.0 |  | go-module-binary-cataloger |
| gnu-coreutils | 9.7-3ubuntu2 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| gnupg | 2.4.8-4ubuntu3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg2 | 2.4.8-4ubuntu3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| gopkg.in/tomb.v2 | v2.0.0-20161208151619-d5d1b5820637 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gpg | 2.4.8-4ubuntu3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.4.8-4ubuntu3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.4.8-4ubuntu3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.4.8-4ubuntu3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgv | 2.4.8-4ubuntu3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.12-1 | BSD-3-Clause, FSFAP, FSFUL, FSFULLR, GFDL-1.3-only, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| grizzly-framework | 4.0.2 |  | java-archive-cataloger |
| grizzly-http | 4.0.2 |  | java-archive-cataloger |
| grizzly-http-server | 4.0.2 |  | java-archive-cataloger |
| guava | 33.6.0-jre |  | java-archive-cataloger |
| gzip | 1.14-1~exp2ubuntu1 | GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hicolor-icon-theme | 0.18-2build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| hostname | 3.25build1 | GPL-2.0-only | dpkg-db-cataloger |
| httplib2 | 0.22.0 | MIT | python-installed-package-cataloger |
| imageio | 2.37.2 | BSD-2-Clause | python-installed-package-cataloger |
| imagemagick | 8:7.1.2.18+dfsg1-1 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| imagemagick-7-common | 8:7.1.2.18+dfsg1-1 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| imagemagick-7.q16 | 8:7.1.2.18+dfsg1-1 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| importlib-metadata | 8.0.0 |  | python-installed-package-cataloger |
| inflect | 7.3.1 |  | python-installed-package-cataloger |
| inflect | 7.5.0 |  | python-installed-package-cataloger |
| init-system-helpers | 1.69 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| iso-codes | 4.20.1-1 | FSFAP, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| isorelax | 20090621 |  | java-archive-cataloger |
| istack-commons-runtime | 4.1.2 |  | java-archive-cataloger |
| j2objc-annotations | 3.1 |  | java-archive-cataloger |
| jackcess | 4.0.10 |  | java-archive-cataloger |
| jackcess-encrypt | 4.0.3 |  | java-archive-cataloger |
| jackson-annotations | 2.21 |  | java-archive-cataloger |
| jackson-core | 2.21.3 |  | java-archive-cataloger |
| jackson-databind | 2.21.3 |  | java-archive-cataloger |
| jackson-jakarta-rs-base | 2.21.3 |  | java-archive-cataloger |
| jackson-jakarta-rs-json-provider | 2.21.3 |  | java-archive-cataloger |
| jackson-module-jakarta-xmlbind-annotations | 2.21.3 |  | java-archive-cataloger |
| jai-imageio-core | 1.4.0 |  | java-archive-cataloger |
| jakarta.activation-api | 2.1.4 |  | java-archive-cataloger |
| jakarta.annotation-api | 3.0.0 |  | java-archive-cataloger |
| jakarta.websocket-api | 2.2.0 |  | java-archive-cataloger |
| jakarta.websocket-client-api | 2.2.0 |  | java-archive-cataloger |
| jakarta.ws.rs-api | 3.1.0 | EPL-2.0, GPL-2.0-with-classpath-exception | java-archive-cataloger |
| jakarta.xml.bind-api | 4.0.5 |  | java-archive-cataloger |
| jaraco-collections | 5.1.0 |  | python-installed-package-cataloger |
| jaraco-context | 5.3.0 |  | python-installed-package-cataloger |
| jaraco-context | 6.0.1 |  | python-installed-package-cataloger |
| jaraco-functools | 4.0.1 |  | python-installed-package-cataloger |
| jaraco-functools | 4.1.0 |  | python-installed-package-cataloger |
| jaraco-text | 3.12.1 |  | python-installed-package-cataloger |
| jaraco-text | 4.0.0 |  | python-installed-package-cataloger |
| java-common | 0.77 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| java-libpst | 0.9.3 |  | java-archive-cataloger |
| jaxb-core | 4.0.8 |  | java-archive-cataloger |
| jaxb-runtime | 4.0.8 |  | java-archive-cataloger |
| jbig2-imageio | 3.0.5 |  | java-archive-cataloger |
| jcl-over-slf4j | 2.0.18 | Apache-2.0 | java-archive-cataloger |
| jempbox | 1.8.17 |  | java-archive-cataloger |
| jetty-http | 11.0.26 |  | java-archive-cataloger |
| jetty-io | 11.0.26 |  | java-archive-cataloger |
| jetty-security | 11.0.26 |  | java-archive-cataloger |
| jetty-server | 11.0.26 |  | java-archive-cataloger |
| jetty-util | 11.0.26 |  | java-archive-cataloger |
| jhighlight | 1.1.1 |  | java-archive-cataloger |
| jmatio | 1.5 |  | java-archive-cataloger |
| jrt-fs | 21.0.11-ea |  | java-archive-cataloger |
| json-simple | 1.1.1 |  | java-archive-cataloger |
| jsoup | 1.22.2 |  | java-archive-cataloger |
| juniversalchardet | 2.5.0 |  | java-archive-cataloger |
| jwarc | 0.36.0 |  | java-archive-cataloger |
| kiwisolver | 1.4.10rc0 |  | python-installed-package-cataloger |
| language-detector | 0.6 |  | java-archive-cataloger |
| launchpadlib | 2.1.0 |  | python-installed-package-cataloger |
| lazr-restfulclient | 0.14.6 |  | python-installed-package-cataloger |
| lazr-uri | 1.0.6 |  | python-installed-package-cataloger |
| lazy-loader | 0.4 | BSD-3-Clause | python-installed-package-cataloger |
| libabsl20260107 | 20260107.0-4 | Apache-2.0 | dpkg-db-cataloger |
| libacl1 | 2.3.2-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaec0 | 1.1.5-1 | BSD-2-Clause | dpkg-db-cataloger |
| libaom3 | 3.13.1-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, ISC | dpkg-db-cataloger |
| libapparmor1 | 5.0.0~beta1-0ubuntu7 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libappstream5 | 1.1.2-1 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libapt-pkg7.0 | 3.2.0 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, curl | dpkg-db-cataloger |
| libarchive13t64 | 3.8.5-1ubuntu2.1 | Apache-2.0, BSD-2-Clause, CC0-1.0 | dpkg-db-cataloger |
| libarmadillo15 | 1:15.2.1+dfsg-2 | Apache-2.0, GPL-2.0-only | dpkg-db-cataloger |
| libarpack2t64 | 3.9.1-6build1 | BSD-3-Clause | dpkg-db-cataloger |
| libassuan9 | 3.0.2-2build1 | FSFULLR, FSFULLRWD, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| libatomic1 | 16-20260322-1ubuntu1 | Apache-2.0, GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libattr1 | 1:2.5.2-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:4.1.2-1build1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:4.1.2-1build1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavif16 | 1.3.0-1ubuntu4 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC0-1.0, MIT | dpkg-db-cataloger |
| libblas3 | 3.12.1-7ubuntu1 | BSD-3-Clause | dpkg-db-cataloger |
| libblkid1 | 2.41.3-3ubuntu2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libblosc1 | 1.21.5+ds-2 | BSD-3-Clause, Zlib | dpkg-db-cataloger |
| libbrotli1 | 1.2.0-3build1 | MIT | dpkg-db-cataloger |
| libbsd0 | 0.12.2-2build2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-6build2 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.43-2ubuntu2 | BSD-2-Clause, BSL-1.0, FSFAP, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libc-gconv-modules-extra | 2.43-2ubuntu2 | BSD-2-Clause, BSL-1.0, FSFAP, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libc6 | 2.43-2ubuntu2 | BSD-2-Clause, BSL-1.0, FSFAP, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libcairo2 | 1.18.4-3 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.5-4build5 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.75-10ubuntu2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcap2-bin | 1:2.75-10ubuntu2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcfitsio10t64 | 4.6.3-1 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, X11 | dpkg-db-cataloger |
| libcom-err2 | 1.47.2-3ubuntu4 | 0BSD, Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.5.1-1 |  | dpkg-db-cataloger |
| libcurl3t64-gnutls | 8.18.0-1ubuntu2.3 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4t64 | 8.18.0-1ubuntu2.3 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libdatrie1 | 0.2.14-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libdav1d7 | 1.5.3-1 | BSD-2-Clause, ISC | dpkg-db-cataloger |
| libdb5.3t64 | 5.3.28+dfsg2-10ubuntu1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdbus-1-3 | 1.16.2-2ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libdebconfclient0 | 0.280ubuntu1 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdeflate0 | 1.23-2ubuntu1 |  | dpkg-db-cataloger |
| libduktape207 | 2.7.0+tests-0ubuntu4 | CC0-1.0 | dpkg-db-cataloger |
| libelf1t64 | 0.194-4 | GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libexpat1 | 2.7.4-1 | MIT | dpkg-db-cataloger |
| libext2fs2t64 | 1.47.2-3ubuntu4 | 0BSD, Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi8 | 3.5.2-4 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libfftw3-double3 | 3.3.10-2fakesync1build3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libfontconfig1 | 2.17.1-3ubuntu1 | HPND-sell-variant | dpkg-db-cataloger |
| libfontenc1 | 1:1.1.8-1build2 | MIT | dpkg-db-cataloger |
| libfreetype6 | 2.14.2+dfsg-1 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT-Modern-Variant, Zlib | dpkg-db-cataloger |
| libfreexl1 | 2.0.0-1build3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libfribidi0 | 1.0.16-5 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libfyaml0 | 0.9.4-1 | BSD-2-Clause, FSFAP, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libfyba0t64 | 4.1.1-11build2 | GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| libgav1-2 | 0.20.0-2build1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libgcc-s1 | 16-20260322-1ubuntu1 | Apache-2.0, GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.12.0-2 | GPL-2.0-only | dpkg-db-cataloger |
| libgdal38 | 3.12.2+dfsg-1build2 | Apache-2.0, BSD-3-Clause, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| libgeos-c1t64 | 3.14.1-2 | Apache-2.0, BSL-1.0, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libgeos3.14.1 | 3.14.1-2 | Apache-2.0, BSL-1.0, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libgeotiff5 | 1.7.4-1build1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| libgfortran5 | 16-20260322-1ubuntu1 | Apache-2.0, GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgif7 | 5.2.2-1ubuntu3 | ISC, MIT | dpkg-db-cataloger |
| libgirepository-2.0-0 | 2.88.0-1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-0t64 | 2.88.0-1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-bin | 2.88.0-1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-data | 2.88.0-1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgmp10 | 2:6.3.0+dfsg-5ubuntu2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30t64 | 3.8.12-2ubuntu1.1 | Apache-2.0, BSD-3-Clause, FSFAP, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only, MIT | dpkg-db-cataloger |
| libgomp1 | 16-20260322-1ubuntu1 | Apache-2.0, GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.58-2 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgpgme45 | 2.0.1-2build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgpgmepp7 | 2.0.0-2 | BSD-2-Clause, BSD-3-Clause, FSFULLRWD, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgraphite2-3 | 1.3.14-11ubuntu1 | GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.22.1-2ubuntu4 | GPL-2.0-only | dpkg-db-cataloger |
| libgstreamer1.0-0 | 1.28.2-1 | CC-BY-SA-4.0, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-2.0 | dpkg-db-cataloger |
| libharfbuzz0b | 12.3.2-2 | Apache-2.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MIT, OFL-1.1 | dpkg-db-cataloger |
| libhdf4-0 | 4.3.1-2 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, NetCDF | dpkg-db-cataloger |
| libhdf5-310 | 1.14.6+repack-2 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libhdf5-hl-310 | 1.14.6+repack-2 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libheif-plugin-aomdec | 1.21.2-3 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause-UC, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libheif1 | 1.21.2-3 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause-UC, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libhogweed6t64 | 3.10.2-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libhwy1t64 | 1.3.0-2 | Apache-2.0 | dpkg-db-cataloger |
| libicu78 | 78.2-2ubuntu1 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn2-0 | 2.3.8-4build1 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libimagequant0 | 4.4.1-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libjansson4 | 2.14-2build4 |  | dpkg-db-cataloger |
| libjbig0 | 2.1-6.1ubuntu3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libjpeg-turbo8 | 2.1.5-4ubuntu4 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libjpeg8 | 8c-2ubuntu12 | LGPL-2.1-only | dpkg-db-cataloger |
| libjson-c5 | 0.18+ds-3 |  | dpkg-db-cataloger |
| libjxl0.11 | 0.11.1-6ubuntu4 |  | dpkg-db-cataloger |
| libk5crypto3 | 1.22.1-2ubuntu4 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-6ubuntu3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkmlbase1t64 | 1.3.0-13 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, Zlib | dpkg-db-cataloger |
| libkmldom1t64 | 1.3.0-13 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, Zlib | dpkg-db-cataloger |
| libkmlengine1t64 | 1.3.0-13 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, Zlib | dpkg-db-cataloger |
| libkrb5-3 | 1.22.1-2ubuntu4 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.22.1-2ubuntu4 | GPL-2.0-only | dpkg-db-cataloger |
| libksba8 | 1.6.7-2build1 | FSFUL, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblapack3 | 3.12.1-7ubuntu1 | BSD-3-Clause | dpkg-db-cataloger |
| liblcms2-2 | 2.17-1ubuntu0.2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| libldap-common | 2.6.10+dfsg-1ubuntu5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libldap2 | 2.6.10+dfsg-1ubuntu5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libleptonica6 | 1.86.0-1 | BSD-2-Clause | dpkg-db-cataloger |
| liblerc4 | 4.0.0+ds-5ubuntu2 | Apache-2.0 | dpkg-db-cataloger |
| liblqr-1-0 | 0.4.2-2.2 | GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libltdl7 | 2.5.4-9 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblz4-1 | 1.10.0-8 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.8.3-1 | 0BSD, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmagickcore-7.q16-10 | 8:7.1.2.18+dfsg1-1 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-7.q16-10 | 8:7.1.2.18+dfsg1-1 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmd0 | 1.1.0-2build4 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libminizip1t64 | 1:1.3.dfsg+really1.3.1-1ubuntu3 | Zlib | dpkg-db-cataloger |
| libmount1 | 2.41.3-3ubuntu2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmspack0t64 | 0.11-1.1build2 | LGPL-2.1-only | dpkg-db-cataloger |
| libmuparser2v5 | 2.3.4-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmysqlclient24 | 8.4.8-0ubuntu1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only | dpkg-db-cataloger |
| libncursesw6 | 6.6+20251231-1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnetcdf22 | 1:4.9.3-1build2 | BSD-3-Clause, BSL-1.0, CC-BY-4.0, GPL-3.0-only, GPL-3.0-or-later, HDF5, NetCDF, Zlib, curl | dpkg-db-cataloger |
| libnettle8t64 | 3.10.2-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.68.0-2ubuntu0.1 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnpth0t64 | 1.8-3build1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnspr4 | 2:4.38.2-1ubuntu1 | MPL-2.0 | dpkg-db-cataloger |
| libnss3 | 2:3.120-1ubuntu2 | MPL-2.0, Zlib | dpkg-db-cataloger |
| libodbc2 | 2.3.14-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libodbcinst2 | 2.3.14-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.4-1ubuntu0.1 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libp11-kit0 | 0.26.2-2 | Apache-2.0, BSD-3-Clause, FSFAP, FSFULLR, GPL-2.0-or-later, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, X11 | dpkg-db-cataloger |
| libpackagekit-glib2-18 | 1.3.4-3ubuntu1 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.7.0-5ubuntu3 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.7.0-5ubuntu3 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.7.0-5ubuntu3 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-systemd | 259.5-0ubuntu3 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam0g | 1.7.0-5ubuntu3 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpango-1.0-0 | 1.57.0-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangocairo-1.0-0 | 1.57.0-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangoft2-1.0-0 | 1.57.0-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpcre2-8-0 | 10.46-1build1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcsclite1 | 2.4.1-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libpixman-1-0 | 0.46.4-1 |  | dpkg-db-cataloger |
| libpng16-16t64 | 1.6.57-1 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpolkit-agent-1-0 | 127-2ubuntu1 | LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpolkit-gobject-1-0 | 127-2ubuntu1 | LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpoppler156 | 26.01.0-2build2 | Apache-2.0, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libpq5 | 18.4-0ubuntu0.26.04.1 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.4-9ubuntu1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libproj25 | 9.7.1-1 | Apache-2.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libpsl5t64 | 0.21.2-1.1build2 | MIT | dpkg-db-cataloger |
| libpython3-stdlib | 3.14.3-0ubuntu2 |  | dpkg-db-cataloger |
| libpython3.14-minimal | 3.14.4-1ubuntu0.1 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.14-stdlib | 3.14.4-1ubuntu0.1 | GPL-2.0-only | dpkg-db-cataloger |
| libqhull-r8.0 | 2020.2-8 | GPL-3.0-only, GPL-3.0-or-later, Qhull | dpkg-db-cataloger |
| libraqm0 | 0.10.4-1 | MIT | dpkg-db-cataloger |
| libraw23t64 | 0.21.5b-1ubuntu1 | CC-BY-SA-3.0, CDDL-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libreadline8t64 | 8.3-4 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| librtmp1 | 2.4+20151223.gitfa8646d.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| librttopo1 | 1.1.0-4build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsasl2-2 | 2.1.28+dfsg1-9ubuntu3 | BSD-2-Clause, BSD-3-Clause-Attribution, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.28+dfsg1-9ubuntu3 | BSD-2-Clause, BSD-3-Clause-Attribution, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, RSA-MD | dpkg-db-cataloger |
| libseccomp2 | 2.6.0-2ubuntu5 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.9-4build1 | GPL-2.0-only | dpkg-db-cataloger |
| libsemanage-common | 3.9-1build1 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsemanage2 | 3.9-1build1 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsepol2 | 3.9-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsharpyuv0 | 1.5.0-0.1build1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libsmartcols1 | 2.41.3-3ubuntu2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libsnappy1v5 | 1.2.2-2 | BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, MIT | dpkg-db-cataloger |
| libspatialite8t64 | 5.1.0-3ubuntu2 | BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libsqlite3-0 | 3.46.1-9 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.2-3ubuntu4 | 0BSD, Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssh2-1t64 | 1.11.1-1ubuntu0.26.04.1 | ISC | dpkg-db-cataloger |
| libssl3t64 | 3.5.5-1ubuntu3 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 16-20260322-1ubuntu1 | Apache-2.0, GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libstemmer0d | 3.0.1-1 |  | dpkg-db-cataloger |
| libsuperlu7 | 7.0.1+dfsg1-2build1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsystemd-shared | 259.5-0ubuntu3 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsystemd0 | 259.5-0ubuntu3 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsz2 | 1.1.5-1 | BSD-2-Clause | dpkg-db-cataloger |
| libtasn1-6 | 4.21.0-2 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtcl8.6 | 8.6.17+dfsg-1build1 |  | dpkg-db-cataloger |
| libtesseract5 | 5.5.0-1build1 | Apache-2.0, MIT | dpkg-db-cataloger |
| libthai-data | 0.1.30-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libthai0 | 0.1.30-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtiff6 | 4.7.0-3ubuntu4 |  | dpkg-db-cataloger |
| libtinfo6 | 6.6+20251231-1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtk8.6 | 8.6.17-1build1 |  | dpkg-db-cataloger |
| libudev1 | 259.5-0ubuntu3 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring5 | 1.3-2build1 | BSD-3-Clause, GFDL-1.2-or-later, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, X11, BSD-3-Clause, GFDL-1.2-or-later, GFDL-1.3-or-later, ISC, Unicode-DFS-2016 | dpkg-db-cataloger |
| liburiparser1 | 0.9.8+dfsg-2build1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libuuid1 | 2.41.3-3ubuntu2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libwebp7 | 1.5.0-0.1build1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libwebpdemux2 | 1.5.0-0.1build1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libwebpmux3 | 1.5.0-0.1build1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libx11-6 | 2:1.8.13-1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.8.13-1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxau6 | 1:1.0.11-1build2 |  | dpkg-db-cataloger |
| libxcb-render0 | 1.17.0-2ubuntu1 |  | dpkg-db-cataloger |
| libxcb-shm0 | 1.17.0-2ubuntu1 |  | dpkg-db-cataloger |
| libxcb1 | 1.17.0-2ubuntu1 |  | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.5-2 |  | dpkg-db-cataloger |
| libxerces-c3.2t64 | 3.2.4+debian-1.3build2 | Apache-2.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libxext6 | 2:1.3.4-1build3 |  | dpkg-db-cataloger |
| libxft2 | 2.3.6-1build2 | HPND-sell-variant | dpkg-db-cataloger |
| libxml2-16 | 2.15.2+dfsg-0.1 | ISC | dpkg-db-cataloger |
| libxmlb2 | 0.3.24-2 | CC0-1.0, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libxrender1 | 1:0.9.12-1build1 | HPND-sell-variant | dpkg-db-cataloger |
| libxslt1.1 | 1.1.45-0.1 |  | dpkg-db-cataloger |
| libxss1 | 1:1.2.3-1build4 | MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.3-2build1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libyaml-0-2 | 0.2.5-2build3 |  | dpkg-db-cataloger |
| libyuv0 | 0.0.1922.20260106-1 | BSD-3-Clause | dpkg-db-cataloger |
| libzopfli1 | 1.0.3-3build1 | Apache-2.0, GPL-3.0-only, GPL-3.0-or-later, Zlib | dpkg-db-cataloger |
| libzstd1 | 1.5.7+dfsg-3 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| listenablefuture | 9999.0-empty-to-avoid-conflict-with-guava |  | java-archive-cataloger |
| log4j-api | 2.26.0 | Apache-2.0 | java-archive-cataloger |
| log4j-core | 2.26.0 | Apache-2.0 | java-archive-cataloger |
| log4j-slf4j2-impl | 2.26.0 | Apache-2.0 | java-archive-cataloger |
| login | 1:4.16.0-2+really2.41.3-3ubuntu2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| login.defs | 1:4.17.4-2ubuntu3 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.2-3ubuntu4 | 0BSD, Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| lsb-release | 12.1-2build1 | 0BSD, ISC | dpkg-db-cataloger |
| lxml | 6.0.2 | BSD-3-Clause | python-installed-package-cataloger |
| lz4 | 4.4.5+dfsg |  | python-installed-package-cataloger |
| matplotlib | 3.10.7+dfsg1 |  | python-installed-package-cataloger |
| mawk | 1.3.4.20260129-1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 14.0.0build1 |  | dpkg-db-cataloger |
| metadata-extractor | 2.20.0 |  | java-archive-cataloger |
| microsoft-translator-java-api | 0.6.2 |  | java-archive-cataloger |
| more-itertools | 10.3.0 |  | python-installed-package-cataloger |
| more-itertools | 10.8.0 | MIT | python-installed-package-cataloger |
| mount | 2.41.3-3ubuntu2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| mpmath | 1.3.0 |  | python-installed-package-cataloger |
| my-test-package | 1.0 |  | python-installed-package-cataloger |
| mysql-common | 5.8+1.1.1ubuntu2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| ncurses-base | 6.6+20251231-1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.6+20251231-1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.5build1 | GPL-2.0-only | dpkg-db-cataloger |
| networkx | 3.2.1 |  | python-installed-package-cataloger |
| numpy | 2.3.5 | BSD-3-Clause | python-installed-package-cataloger |
| oauthlib | 3.3.1 | BSD-3-Clause | python-installed-package-cataloger |
| openjdk-21-jre-headless | 21.0.11~8ea-1 | GPL-2.0-only, MIT | dpkg-db-cataloger |
| openssl | 3.5.5-1ubuntu3 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| openssl-provider-legacy | 3.5.5-1ubuntu3 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| packagekit | 1.3.4-3ubuntu1 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| packaging | 24.2 |  | python-installed-package-cataloger |
| packaging | 26.0 | Apache-2.0 OR BSD-2-Clause | python-installed-package-cataloger |
| passwd | 1:4.17.4-2ubuntu3 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.8-2build1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| pdfbox | 3.0.7 |  | java-archive-cataloger |
| pdfbox-io | 3.0.7 |  | java-archive-cataloger |
| pdfbox-tools | 3.0.7 |  | java-archive-cataloger |
| perl-base | 5.40.1-7build1 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pillow | 12.1.1 | MIT-CMU | python-installed-package-cataloger |
| pinentry-curses | 1.3.2-3ubuntu1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| platformdirs | 4.2.2 | MIT | python-installed-package-cataloger |
| polkitd | 127-2ubuntu1 | LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| procps | 2:4.0.4-9ubuntu1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| proj-data | 9.7.1-1 | Apache-2.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| pygobject | 3.56.2 | LGPL-2.1-or-later | python-installed-package-cataloger |
| pyjwt | 2.10.1 | MIT | python-installed-package-cataloger |
| pyparsing | 3.3.2 | MIT | python-installed-package-cataloger |
| python-apt | 3.1.0+ubuntu1 |  | python-installed-package-cataloger |
| python-apt-common | 3.1.0ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python-dateutil | 2.9.0 |  | python-installed-package-cataloger |
| python-debian | 1.0.1+ubuntu2 | GPL-2.0-or-later | python-installed-package-cataloger |
| python-matplotlib-data | 3.10.7+dfsg1-2build1 | BSD-3-Clause, CC-BY-4.0 | dpkg-db-cataloger |
| python3 | 3.14.3-0ubuntu2 |  | dpkg-db-cataloger |
| python3-apt | 3.1.0ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-attr | 25.4.0-1build1 |  | dpkg-db-cataloger |
| python3-autocommand | 2.2.2-4 | LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| python3-bcrypt | 5.0.0-3build1 | Apache-2.0, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| python3-blinker | 1.9.0-2build1 |  | dpkg-db-cataloger |
| python3-brotli | 1.2.0-3build1 | MIT | dpkg-db-cataloger |
| python3-cffi-backend | 2.0.0-3build1 |  | dpkg-db-cataloger |
| python3-contourpy | 1.3.3-1build1 | BSD-3-Clause | dpkg-db-cataloger |
| python3-cryptography | 46.0.5-1ubuntu2 | Apache-2.0 | dpkg-db-cataloger |
| python3-cycler | 0.12.1-2 |  | dpkg-db-cataloger |
| python3-dateutil | 2.9.0-4build1 | BSD-3-Clause | dpkg-db-cataloger |
| python3-dbus | 1.4.0-1build2 | AFL-2.1, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-debconf | 1.5.92 | BSD-2-Clause | dpkg-db-cataloger |
| python3-debian | 1.0.1ubuntu2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| python3-decorator | 5.2.1-2 | BSD-2-Clause | dpkg-db-cataloger |
| python3-distro | 1.9.0-1build1 | Apache-2.0 | dpkg-db-cataloger |
| python3-distro-info | 1.15 | ISC | dpkg-db-cataloger |
| python3-distupgrade | 1:26.04.18 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-fonttools | 4.61.1-3build1 | Apache-2.0, GPL-2.0-only | dpkg-db-cataloger |
| python3-gdal | 3.12.2+dfsg-1build2 | Apache-2.0, BSD-3-Clause, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| python3-gi | 3.56.2-1 | LGPL-2.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| python3-httplib2 | 0.22.0-1build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| python3-imageio | 2.37.2-1 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| python3-inflect | 7.5.0-1build1 |  | dpkg-db-cataloger |
| python3-jaraco.context | 6.0.1-2 |  | dpkg-db-cataloger |
| python3-jaraco.functools | 4.1.0-1build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-jaraco.text | 4.0.0-1build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-jwt | 2.10.1-4ubuntu1 |  | dpkg-db-cataloger |
| python3-kiwisolver | 1.4.10~rc0-1build1 | BSD-3-Clause | dpkg-db-cataloger |
| python3-launchpadlib | 2.1.0-1build1 | LGPL-3.0-only, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| python3-lazr.restfulclient | 0.14.6-3build1 | LGPL-3.0-only, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| python3-lazr.uri | 1.0.6-7build1 | LGPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| python3-lazy-loader | 0.4-1build1 | BSD-3-Clause | dpkg-db-cataloger |
| python3-lxml | 6.0.2-1build1 | GPL-2.0-only | dpkg-db-cataloger |
| python3-lz4 | 4.4.5+dfsg-1build1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-matplotlib | 3.10.7+dfsg1-2build1 | BSD-3-Clause, CC-BY-4.0 | dpkg-db-cataloger |
| python3-minimal | 3.14.3-0ubuntu2 |  | dpkg-db-cataloger |
| python3-more-itertools | 10.8.0-1build1 |  | dpkg-db-cataloger |
| python3-mpmath | 1.3.0-2 | BSD-3-Clause | dpkg-db-cataloger |
| python3-networkx | 3.2.1-4ubuntu2 | BSD-3-Clause, GPL-3.0-only | dpkg-db-cataloger |
| python3-numpy | 1:2.3.5+ds-3ubuntu1 | Apache-2.0, Apache-2.0, BSD-3-Clause, BSD-3-Clause, CC0-1.0, FSFAP, Zlib, Zlib | dpkg-db-cataloger |
| python3-numpy-dev | 1:2.3.5+ds-3ubuntu1 | Apache-2.0, Apache-2.0, BSD-3-Clause, BSD-3-Clause, CC0-1.0, FSFAP, Zlib, Zlib | dpkg-db-cataloger |
| python3-oauthlib | 3.3.1-1build1 | BSD-3-Clause | dpkg-db-cataloger |
| python3-packaging | 26.0-1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| python3-pil | 12.1.1-2ubuntu1.2 | Apache-2.0, GPL-3.0-only, HPND | dpkg-db-cataloger |
| python3-pil.imagetk | 12.1.1-2ubuntu1.2 | Apache-2.0, GPL-3.0-only, HPND | dpkg-db-cataloger |
| python3-pkg-resources | 78.1.1-0.1build1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| python3-pyparsing | 3.3.2-2 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| python3-scipy | 1.16.3-4build1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, MIT, PSF-2.0 | dpkg-db-cataloger |
| python3-setuptools | 78.1.1-0.1build1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| python3-skimage | 0.26.0-3build1 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| python3-skimage-lib | 0.26.0-3build1 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| python3-software-properties | 0.120 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| python3-sympy | 1.14.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-tifffile | 20260216-1 | BSD-3-Clause | dpkg-db-cataloger |
| python3-tk | 3.14.3-0ubuntu2 |  | dpkg-db-cataloger |
| python3-typeguard | 4.4.4-2 |  | dpkg-db-cataloger |
| python3-typing-extensions | 4.15.0-2 |  | dpkg-db-cataloger |
| python3-ufolib2 | 0.18.1+dfsg1-1 | Apache-2.0 | dpkg-db-cataloger |
| python3-unicodedata2 | 16.0.0+ds-1build2 | Apache-2.0, PSF-2.0 | dpkg-db-cataloger |
| python3-update-manager | 1:26.04.5 |  | dpkg-db-cataloger |
| python3-wadllib | 2.0.0-3 | LGPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| python3-yaml | 6.0.3-1build1 |  | dpkg-db-cataloger |
| python3-zipp | 3.23.0-1build1 |  | dpkg-db-cataloger |
| python3-zopfli | 0.4.1-1 | Apache-2.0, CC0-1.0 | dpkg-db-cataloger |
| python3.14 | 3.14.4-1ubuntu0.1 | GPL-2.0-only | dpkg-db-cataloger |
| python3.14-minimal | 3.14.4-1ubuntu0.1 | GPL-2.0-only | dpkg-db-cataloger |
| python3.14-tk | 3.14.4-1ubuntu0.1 | GPL-2.0-only | dpkg-db-cataloger |
| pyyaml | 6.0.3 | MIT | python-installed-package-cataloger |
| readline-common | 8.3-4 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| rome | 2.1.0 |  | java-archive-cataloger |
| rome-utils | 2.1.0 |  | java-archive-cataloger |
| rome-utils | 2.1.0 |  | java-archive-cataloger |
| rust-coreutils | 0.8.0-0ubuntu3 | Apache-2.0, MIT | dpkg-db-cataloger |
| scikit-image | 0.26.0 |  | python-installed-package-cataloger |
| scipy | 1.16.3 | BSD-3-Clause | python-installed-package-cataloger |
| screen | 4.9.1-3ubuntu2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| sed | 4.9-2build3 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sensible-utils | 0.0.26build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| setuptools | 78.1.1 |  | python-installed-package-cataloger |
| sgml-base | 1.31+nmu1build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| slf4j-api | 2.0.18 |  | java-archive-cataloger |
| software-properties-common | 0.120 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| stax2-api | 4.2.2 |  | java-archive-cataloger |
| stdlib | go1.26.2 | BSD-3-Clause | go-module-binary-cataloger |
| sympy | 1.14.0 |  | python-installed-package-cataloger |
| systemd | 259.5-0ubuntu3 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| systemd-sysv | 259.5-0ubuntu3 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| sysvinit-utils | 3.15-5ubuntu1 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| tar | 1.35+dfsg-4 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tesseract-ocr | 5.5.0-1build1 | Apache-2.0, MIT | dpkg-db-cataloger |
| tesseract-ocr-afr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-all | 5.5.0-1build1 | Apache-2.0, MIT | dpkg-db-cataloger |
| tesseract-ocr-amh | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ara | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-asm | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-aze | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-aze-cyrl | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bel | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ben | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bod | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bos | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bre | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bul | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-cat | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ceb | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ces | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chi-sim | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chi-sim-vert | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chi-tra | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chi-tra-vert | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-cos | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-cym | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-dan | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-deu | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-div | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-dzo | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ell | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-eng | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-enm | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-epo | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-est | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-eus | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fao | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fas | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fil | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fin | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fra | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-frk | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-frm | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fry | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-gla | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-gle | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-glg | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-grc | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-guj | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hat | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-heb | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hin | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hrv | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hun | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hye | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-iku | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ind | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-isl | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ita | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ita-old | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-jav | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-jpn | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-jpn-vert | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kan | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kat | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kat-old | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kaz | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-khm | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kir | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kmr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kor | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kor-vert | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-lao | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-lat | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-lav | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-lit | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ltz | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mal | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mar | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mkd | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mlt | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mon | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mri | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-msa | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mya | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-nep | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-nld | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-nor | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-oci | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ori | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-osd | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-pan | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-pol | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-por | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-pus | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-que | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ron | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-rus | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-san | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-arab | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-armn | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-beng | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-cans | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-cher | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-cyrl | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-deva | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-ethi | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-frak | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-geor | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-grek | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-gujr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-guru | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hang | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hang-vert | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hans | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hans-vert | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hant | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hant-vert | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hebr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-jpan | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-jpan-vert | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-khmr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-knda | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-laoo | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-latn | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-mlym | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-mymr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-orya | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-sinh | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-syrc | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-taml | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-telu | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-thaa | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-thai | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-tibt | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-viet | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-sin | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-slk | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-slv | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-snd | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-spa | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-spa-old | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-sqi | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-srp | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-srp-latn | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-sun | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-swa | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-swe | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-syr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tam | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tat | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tel | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tgk | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tha | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tir | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ton | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tur | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-uig | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ukr | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-urd | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-uzb | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-uzb-cyrl | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-vie | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-yid | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-yor | 1:4.1.0-2build1 | Apache-2.0 | dpkg-db-cataloger |
| tifffile | 2026.2.16 | BSD-3-Clause | python-installed-package-cataloger |
| tika-core | 3.3.1 |  | java-archive-cataloger |
| tika-emitter-fs | 3.3.1 |  | java-archive-cataloger |
| tika-handler-boilerpipe | 3.3.1 |  | java-archive-cataloger |
| tika-langdetect-optimaize | 3.3.1 |  | java-archive-cataloger |
| tika-parser-apple-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-audiovideo-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-cad-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-code-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-crypto-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-digest-commons | 3.3.1 |  | java-archive-cataloger |
| tika-parser-font-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-html-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-image-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-mail-commons | 3.3.1 |  | java-archive-cataloger |
| tika-parser-mail-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-microsoft-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-miscoffice-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-news-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-ocr-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-pdf-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-pkg-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-text-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-webarchive-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-xml-module | 3.3.1 |  | java-archive-cataloger |
| tika-parser-xmp-commons | 3.3.1 |  | java-archive-cataloger |
| tika-parser-zip-commons | 3.3.1 |  | java-archive-cataloger |
| tika-serialization | 3.3.1 |  | java-archive-cataloger |
| tika-server-core | 3.3.1 |  | java-archive-cataloger |
| tika-server-standard | 3.3.1 | Apache-2.0, EPL-2.0, GPL-2.0-only | java-archive-cataloger |
| tika-translate | 3.3.1 |  | java-archive-cataloger |
| tika-xmp | 3.3.1 |  | java-archive-cataloger |
| tini | 0.19.0-6 |  | dpkg-db-cataloger |
| tomli | 2.0.1 |  | python-installed-package-cataloger |
| ttf-mscorefonts-installer | 3.8.1ubuntu2 |  | dpkg-db-cataloger |
| txw2 | 4.0.8 |  | java-archive-cataloger |
| typeguard | 4.3.0 | MIT | python-installed-package-cataloger |
| typeguard | 4.4.4 | MIT | python-installed-package-cataloger |
| typing-extensions | 4.12.2 |  | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| tyrus-client | 2.2.2 |  | java-archive-cataloger |
| tyrus-container-grizzly-client | 2.2.2 |  | java-archive-cataloger |
| tyrus-core | 2.2.2 |  | java-archive-cataloger |
| tyrus-spi | 2.2.2 |  | java-archive-cataloger |
| tyrus-standalone-client | 2.2.2 |  | java-archive-cataloger |
| tzdata | 2026a-3ubuntu1 | ICU | dpkg-db-cataloger |
| ubuntu-keyring | 2023.11.28.1build1 |  | dpkg-db-cataloger |
| ubuntu-pro-client | 37.2ubuntu | GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| ubuntu-pro-client | 8001 |  | python-installed-package-cataloger |
| ubuntu-release-upgrader-core | 1:26.04.18 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| ufolib2 | 0.18.1 |  | python-installed-package-cataloger |
| unicode-data | 16.0.0-1build1 |  | dpkg-db-cataloger |
| unicodedata2 | 16.0.0 |  | python-installed-package-cataloger |
| unixodbc-common | 2.3.14-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| update-manager-core | 1:26.04.5 |  | dpkg-db-cataloger |
| update-notifier-common | 3.207 | LGPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.41.3-3ubuntu2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| vorbis-java-core | 0.8 |  | java-archive-cataloger |
| vorbis-java-tika | 0.8 |  | java-archive-cataloger |
| wadllib | 2.0.0 |  | python-installed-package-cataloger |
| wget | 1.25.0-2ubuntu4 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| wheel | 0.45.1 |  | python-installed-package-cataloger |
| woodstox-core | 7.1.1 |  | java-archive-cataloger |
| x11-common | 1:7.7+26ubuntu1 |  | dpkg-db-cataloger |
| xfonts-encodings | 1:1.0.5-0ubuntu3 |  | dpkg-db-cataloger |
| xfonts-utils | 1:7.7+7build1 |  | dpkg-db-cataloger |
| xml-core | 0.19build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| xmlschema-core | 2.3.2 |  | java-archive-cataloger |
| xmpbox | 3.0.7 |  | java-archive-cataloger |
| xsdlib | 2022.7 |  | java-archive-cataloger |
| zipp | 3.19.2 |  | python-installed-package-cataloger |
| zipp | 3.23.0 | MIT | python-installed-package-cataloger |
| zlib1g | 1:1.3.dfsg+really1.3.1-1ubuntu3 | Zlib | dpkg-db-cataloger |
| zopfli | 0.4.1 | Apache-2.0 | python-installed-package-cataloger |
| zstd-jni | 1.5.7-7 |  | java-archive-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/rspamd

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| adduser | 3.134 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| base-files | 12.4+deb12u5 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b2 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| binutils-common | 2.40-2 |  | dpkg-db-cataloger |
| bsdutils | 1:2.38.1-5+b1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20230311 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u1 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dpkg | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gpgv | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| init-system-helpers | 1.65.2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libacl1 | 2.3.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libbinutils | 2.40-2 |  | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+b1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.36-9+deb12u4 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u4 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdebconfclient0 | 0.270 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libext2fs2 | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libfasttext0 | 0.9.2+ds-1+b1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libffi8 | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libgcc-s1 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.1-3 | GPL-2.0-only | dpkg-db-cataloger |
| libglib2.0-0 | 2.74.6-2 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-data | 2.74.6-2 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u2 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libhogweed6 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libhyperscan5 | 5.4.0-2 | BSD-2-Clause, BSL-1.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libicu72 | 72.1-3 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn2-0 | 2.3.3-1+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-0.2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+b1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libseccomp2 | 2.5.4-1+b3 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.4-1 |  | dpkg-db-cataloger |
| libsemanage2 | 3.4-1+b5 |  | dpkg-db-cataloger |
| libsepol2 | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsmartcols1 | 2.38.1-5+b1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsodium23 | 1.0.18-1 | BSD-2-Clause, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssl3 | 3.0.11-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 252.22-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libudev1 | 252.22-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+b1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libxml2 | 2.9.14+dfsg-1.3~deb12u1 | ISC | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libzstd1 | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+b1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| lsb-base | 11.6 | BSD-3-Clause, GPL-2.0-only | dpkg-db-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| mount | 2.38.1-5+b1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| openssl | 3.0.11-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| passwd | 1:4.13+dfsg1-1+b1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u1 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| rspamd | 3.8.4 | Apache-2.0, BSD-1-Clause, BSD-2-Clause, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-2.0 | dpkg-db-cataloger |
| rspamd-dbg | 3.8.4 | Apache-2.0, BSD-1-Clause, BSD-2-Clause, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-2.0 | dpkg-db-cataloger |
| sed | 4.9-1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| shared-mime-info | 2.2-1 |  | dpkg-db-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tzdata | 2024a-0+deb12u1 |  | dpkg-db-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+b1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+b1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| xdg-user-dirs | 0.18-1 | GPL-2.0-only | dpkg-db-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/prometheus

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| busybox | 1.37.0 |  | binary-classifier-cataloger |
| cloud.google.com/go/auth | v0.18.2 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth | v0.18.2 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.8 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.8 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.9.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.9.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.21.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.21.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.13.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.13.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.11.2 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.11.2 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/compute/armcompute/v5 | v5.7.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/compute/armcompute/v5 | v5.7.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/network/armnetwork/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/network/armnetwork/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.6.0 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.6.0 |  | go-module-binary-cataloger |
| github.com/Code-Hex/go-generics-cache | v1.5.1 |  | go-module-binary-cataloger |
| github.com/Code-Hex/go-generics-cache | v1.5.1 |  | go-module-binary-cataloger |
| github.com/KimMachineGun/automemlimit | v0.7.5 |  | go-module-binary-cataloger |
| github.com/alecthomas/kingpin/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/alecthomas/kingpin/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/alecthomas/units | v0.0.0-20240927000941-0f3dac36c52b |  | go-module-binary-cataloger |
| github.com/alecthomas/units | v0.0.0-20240927000941-0f3dac36c52b |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.41.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.41.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.12 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.12 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.12 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.12 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/ini | v1.8.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/ini | v1.8.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ec2 | v1.296.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ec2 | v1.296.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ecs | v1.74.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ecs | v1.74.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/elasticache | v1.51.12 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/elasticache | v1.51.12 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.20 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/kafka | v1.49.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/kafka | v1.49.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/lightsail | v1.51.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/lightsail | v1.51.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/rds | v1.117.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/rds | v1.117.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.8 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.8 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.13 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.13 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.35.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.35.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.41.9 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.41.9 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.24.2 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.24.2 |  | go-module-binary-cataloger |
| github.com/bahlo/generic-list-go | v0.2.0 |  | go-module-binary-cataloger |
| github.com/basgys/goxml2json | v1.1.1-0.20231018121955-e66ee54ceaad |  | go-module-binary-cataloger |
| github.com/bboreham/go-loser | v0.0.0-20230920113527-fcc2c21820a3 |  | go-module-binary-cataloger |
| github.com/bboreham/go-loser | v0.0.0-20230920113527-fcc2c21820a3 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/buger/jsonparser | v1.1.1 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cncf/xds/go | v0.0.0-20251210132809-ee656c7534f5 |  | go-module-binary-cataloger |
| github.com/cncf/xds/go | v0.0.0-20251210132809-ee656c7534f5 |  | go-module-binary-cataloger |
| github.com/containerd/errdefs | v1.0.0 |  | go-module-binary-cataloger |
| github.com/containerd/errdefs | v1.0.0 |  | go-module-binary-cataloger |
| github.com/containerd/errdefs/pkg | v0.3.0 |  | go-module-binary-cataloger |
| github.com/containerd/errdefs/pkg | v0.3.0 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.6.0 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.6.0 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/dennwc/varint | v1.0.0 |  | go-module-binary-cataloger |
| github.com/dennwc/varint | v1.0.0 |  | go-module-binary-cataloger |
| github.com/digitalocean/godo | v1.178.0 |  | go-module-binary-cataloger |
| github.com/digitalocean/godo | v1.178.0 |  | go-module-binary-cataloger |
| github.com/distribution/reference | v0.6.0 |  | go-module-binary-cataloger |
| github.com/distribution/reference | v0.6.0 |  | go-module-binary-cataloger |
| github.com/docker/docker | v28.5.2+incompatible |  | go-module-binary-cataloger |
| github.com/docker/docker | v28.5.2+incompatible |  | go-module-binary-cataloger |
| github.com/docker/go-connections | v0.6.0 |  | go-module-binary-cataloger |
| github.com/docker/go-connections | v0.6.0 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/edsrzf/mmap-go | v1.2.0 |  | go-module-binary-cataloger |
| github.com/edsrzf/mmap-go | v1.2.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.12.2 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.12.2 |  | go-module-binary-cataloger |
| github.com/envoyproxy/go-control-plane/envoy | v1.37.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/go-control-plane/envoy | v1.37.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/protoc-gen-validate | v1.3.3 |  | go-module-binary-cataloger |
| github.com/envoyproxy/protoc-gen-validate | v1.3.3 |  | go-module-binary-cataloger |
| github.com/facette/natsort | v0.0.0-20181210072756-2cd4dd1e2dcb |  | go-module-binary-cataloger |
| github.com/facette/natsort | v0.0.0-20181210072756-2cd4dd1e2dcb |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/felixge/fgprof | v0.9.5 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.9.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.9.0 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/analysis | v0.24.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/analysis | v0.24.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/errors | v0.22.7 |  | go-module-binary-cataloger |
| github.com/go-openapi/errors | v0.22.7 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.22.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.22.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.21.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.21.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/loads | v0.23.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/loads | v0.23.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/spec | v0.22.3 |  | go-module-binary-cataloger |
| github.com/go-openapi/spec | v0.22.3 |  | go-module-binary-cataloger |
| github.com/go-openapi/strfmt | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/strfmt | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/cmdutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/cmdutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/conv | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/conv | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/fileutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/fileutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/jsonname | v0.25.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/jsonname | v0.25.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/jsonutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/jsonutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/loading | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/loading | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/mangling | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/mangling | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/netutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/netutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/stringutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/stringutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/typeutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/typeutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/yamlutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/yamlutils | v0.25.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/validate | v0.25.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/validate | v0.25.1 |  | go-module-binary-cataloger |
| github.com/go-resty/resty/v2 | v2.17.2 |  | go-module-binary-cataloger |
| github.com/go-resty/resty/v2 | v2.17.2 |  | go-module-binary-cataloger |
| github.com/go-viper/mapstructure/v2 | v2.5.0 |  | go-module-binary-cataloger |
| github.com/go-viper/mapstructure/v2 | v2.5.0 |  | go-module-binary-cataloger |
| github.com/go-zookeeper/zk | v1.0.4 |  | go-module-binary-cataloger |
| github.com/go-zookeeper/zk | v1.0.4 |  | go-module-binary-cataloger |
| github.com/gobwas/glob | v0.2.3 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.3.1 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.3.1 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v1.0.0 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v1.0.0 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-querystring | v1.2.0 |  | go-module-binary-cataloger |
| github.com/google/go-querystring | v1.2.0 |  | go-module-binary-cataloger |
| github.com/google/pprof | v0.0.0-20260302011040-a15ffb7f9dcc |  | go-module-binary-cataloger |
| github.com/google/pprof | v0.0.0-20260302011040-a15ffb7f9dcc |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.9 |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.9 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.14 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.14 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.18.0 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.18.0 |  | go-module-binary-cataloger |
| github.com/gophercloud/gophercloud/v2 | v2.11.1 |  | go-module-binary-cataloger |
| github.com/gophercloud/gophercloud/v2 | v2.11.1 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.4-0.20250319132907-e064f32e3674 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.4-0.20250319132907-e064f32e3674 |  | go-module-binary-cataloger |
| github.com/grafana/regexp | v0.0.0-20250905093917-f7b3be9d1853 |  | go-module-binary-cataloger |
| github.com/grafana/regexp | v0.0.0-20250905093917-f7b3be9d1853 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.28.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/consul/api | v1.32.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/consul/api | v1.32.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/cronexpr | v1.1.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/cronexpr | v1.1.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-immutable-radix | v1.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-immutable-radix | v1.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.8 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.8 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-version | v1.8.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v0.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v0.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/nomad/api | v0.0.0-20260324203407-b27b0c2e019a |  | go-module-binary-cataloger |
| github.com/hashicorp/nomad/api | v0.0.0-20260324203407-b27b0c2e019a |  | go-module-binary-cataloger |
| github.com/hashicorp/serf | v0.10.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/serf | v0.10.1 |  | go-module-binary-cataloger |
| github.com/hetznercloud/hcloud-go/v2 | v2.36.0 |  | go-module-binary-cataloger |
| github.com/hetznercloud/hcloud-go/v2 | v2.36.0 |  | go-module-binary-cataloger |
| github.com/ionos-cloud/sdk-go/v6 | v6.3.6 |  | go-module-binary-cataloger |
| github.com/ionos-cloud/sdk-go/v6 | v6.3.6 |  | go-module-binary-cataloger |
| github.com/jpillora/backoff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/jpillora/backoff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/julienschmidt/httprouter | v1.3.0 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.5 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.5 |  | go-module-binary-cataloger |
| github.com/knadh/koanf/maps | v0.1.2 |  | go-module-binary-cataloger |
| github.com/knadh/koanf/providers/confmap | v1.0.0 |  | go-module-binary-cataloger |
| github.com/knadh/koanf/v2 | v2.3.3 |  | go-module-binary-cataloger |
| github.com/kolo/xmlrpc | v0.0.0-20220921171641-a4b6fa1dd06b |  | go-module-binary-cataloger |
| github.com/kolo/xmlrpc | v0.0.0-20220921171641-a4b6fa1dd06b |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/linode/linodego | v1.66.0 |  | go-module-binary-cataloger |
| github.com/linode/linodego | v1.66.0 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mdlayher/socket | v0.4.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/socket | v0.4.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/vsock | v1.2.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/vsock | v1.2.1 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.72 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.72 |  | go-module-binary-cataloger |
| github.com/mitchellh/copystructure | v1.2.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/reflectwalk | v1.0.2 |  | go-module-binary-cataloger |
| github.com/moby/docker-image-spec | v1.3.1 |  | go-module-binary-cataloger |
| github.com/moby/docker-image-spec | v1.3.1 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.3-0.20250322232337-35a7c28c31ee |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.3-0.20250322232337-35a7c28c31ee |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/mwitkow/go-conntrack | v0.0.0-20190716064945-2f068394615f |  | go-module-binary-cataloger |
| github.com/mwitkow/go-conntrack | v0.0.0-20190716064945-2f068394615f |  | go-module-binary-cataloger |
| github.com/nsf/jsondiff | v0.0.0-20260207060731-8e8d90c4c0ac |  | go-module-binary-cataloger |
| github.com/oklog/run | v1.2.0 |  | go-module-binary-cataloger |
| github.com/oklog/ulid/v2 | v2.1.1 |  | go-module-binary-cataloger |
| github.com/oklog/ulid/v2 | v2.1.1 |  | go-module-binary-cataloger |
| github.com/open-telemetry/opentelemetry-collector-contrib/internal/exp/metrics | v0.148.0 |  | go-module-binary-cataloger |
| github.com/open-telemetry/opentelemetry-collector-contrib/pkg/pdatautil | v0.148.0 |  | go-module-binary-cataloger |
| github.com/open-telemetry/opentelemetry-collector-contrib/processor/deltatocumulativeprocessor | v0.148.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/image-spec | v1.1.1 |  | go-module-binary-cataloger |
| github.com/opencontainers/image-spec | v1.1.1 |  | go-module-binary-cataloger |
| github.com/ovh/go-ovh | v1.9.0 |  | go-module-binary-cataloger |
| github.com/ovh/go-ovh | v1.9.0 |  | go-module-binary-cataloger |
| github.com/pb33f/jsonpath | v0.8.1 |  | go-module-binary-cataloger |
| github.com/pb33f/libopenapi | v0.34.3 |  | go-module-binary-cataloger |
| github.com/pb33f/libopenapi-validator | v0.13.3 |  | go-module-binary-cataloger |
| github.com/pb33f/ordered-map/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/pbnjay/memory | v0.0.0-20210728143218-7b4eea64cf58 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/prometheus/alertmanager | v0.31.1 |  | go-module-binary-cataloger |
| github.com/prometheus/alertmanager | v0.31.1 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang/exp | v0.0.0-20260325093428-d8591d0db856 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang/exp | v0.0.0-20260325093428-d8591d0db856 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.5 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.5 |  | go-module-binary-cataloger |
| github.com/prometheus/common/assets | v0.2.0 |  | go-module-binary-cataloger |
| github.com/prometheus/exporter-toolkit | v0.15.1 |  | go-module-binary-cataloger |
| github.com/prometheus/exporter-toolkit | v0.15.1 |  | go-module-binary-cataloger |
| github.com/prometheus/otlptranslator | v1.0.0 |  | go-module-binary-cataloger |
| github.com/prometheus/otlptranslator | v1.0.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.16.1 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.16.1 |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.0.0-20260427144041-eb173f5256d4+dirty |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.0.0-20260427144041-eb173f5256d4+dirty |  | go-module-binary-cataloger |
| github.com/prometheus/sigv4 | v0.4.1 |  | go-module-binary-cataloger |
| github.com/prometheus/sigv4 | v0.4.1 |  | go-module-binary-cataloger |
| github.com/puzpuzpuz/xsync/v4 | v4.4.0 |  | go-module-binary-cataloger |
| github.com/santhosh-tekuri/jsonschema/v6 | v6.0.2 |  | go-module-binary-cataloger |
| github.com/scaleway/scaleway-sdk-go | v1.0.0-beta.36 |  | go-module-binary-cataloger |
| github.com/scaleway/scaleway-sdk-go | v1.0.0-beta.36 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/stackitcloud/stackit-sdk-go/core | v0.23.0 |  | go-module-binary-cataloger |
| github.com/stackitcloud/stackit-sdk-go/core | v0.23.0 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.11.1 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.11.1 |  | go-module-binary-cataloger |
| github.com/vultr/govultr/v3 | v3.28.1 |  | go-module-binary-cataloger |
| github.com/vultr/govultr/v3 | v3.28.1 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/xhit/go-str2duration/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/xhit/go-str2duration/v2 | v2.1.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/component | v1.54.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/confmap | v1.54.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/confmap/xconfmap | v0.148.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/consumer | v1.54.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/featuregate | v1.54.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/internal/componentalias | v0.148.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/pdata | v1.54.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/pipeline | v1.54.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/processor | v1.54.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.9.0 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/automaxprocs | v1.6.0 |  | go-module-binary-cataloger |
| go.uber.org/goleak | v1.3.0 |  | go-module-binary-cataloger |
| go.uber.org/goleak | v1.3.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.27.1 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v4 | v4.0.0-rc.4 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.49.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.49.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20260218203240-3dfff04db8fa |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20260218203240-3dfff04db8fa |  | go-module-binary-cataloger |
| golang.org/x/net | v0.52.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.52.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.42.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.42.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.41.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.41.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.35.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.35.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.15.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.15.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.272.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.272.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20260319201613-d00831a3d3e7 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20260319201613-d00831a3d3e7 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20260311181403-84a4fc48630c |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20260311181403-84a4fc48630c |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.79.3 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.79.3 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| gopkg.in/evanphx/json-patch.v4 | v4.13.0 |  | go-module-binary-cataloger |
| gopkg.in/evanphx/json-patch.v4 | v4.13.0 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/ini.v1 | v1.67.1 |  | go-module-binary-cataloger |
| gopkg.in/ini.v1 | v1.67.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| k8s.io/api | v0.35.3 |  | go-module-binary-cataloger |
| k8s.io/api | v0.35.3 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.35.3 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.35.3 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.35.3 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.35.3 |  | go-module-binary-cataloger |
| k8s.io/klog | v1.0.0 |  | go-module-binary-cataloger |
| k8s.io/klog/v2 | v2.140.0 |  | go-module-binary-cataloger |
| k8s.io/klog/v2 | v2.140.0 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20250910181357-589584f1c912 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20250910181357-589584f1c912 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20251002143259-bc988d571ff4 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20251002143259-bc988d571ff4 |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20250730193827-2d320260d730 |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20250730193827-2d320260d730 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v6 | v6.3.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v6 | v6.3.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.6.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.6.0 |  | go-module-binary-cataloger |
| stdlib | go1.26.2 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.26.2 | BSD-3-Clause | go-module-binary-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/grafana

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| @grafana-plugins/grafana-azure-monitor-datasource | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/grafana-postgresql-datasource | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/grafana-pyroscope-datasource | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/grafana-testdata-datasource | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/graphite | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/influxdb | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/jaeger | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/loki | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/mssql | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/mysql | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/opentsdb | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/parca | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/stackdriver | 13.1.0 |  | javascript-package-cataloger |
| @grafana-plugins/tempo | 13.1.0 |  | javascript-package-cataloger |
| alpine-baselayout | 3.7.2-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.2-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.6-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.24.1-r0 | MIT | apk-db-cataloger |
| apk-tools | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| bash | 5.3.9-r1 | GPL-3.0-or-later | apk-db-cataloger |
| brotli-libs | 1.2.0-r1 | MIT | apk-db-cataloger |
| bubblewrap | 0.11.2-r0 | LGPL-2.0-or-later | apk-db-cataloger |
| buf.build/gen/go/parca-dev/parca/connectrpc/go | v1.18.1-20250703125925-3f0fcf4bff96.1 |  | go-module-binary-cataloger |
| buf.build/gen/go/parca-dev/parca/protocolbuffers/go | v1.36.2-20250703125925-3f0fcf4bff96.1 |  | go-module-binary-cataloger |
| busybox | 1.37.0-r31 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r31 | GPL-2.0-only | apk-db-cataloger |
| c-ares | 1.34.6-r0 | MIT | apk-db-cataloger |
| ca-certificates | 20260611-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20260611-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| cel.dev/expr | v0.25.1 |  | go-module-binary-cataloger |
| cloud.google.com/go | v0.123.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/aiplatform | v1.125.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth | v0.20.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.8 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.9.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/iam | v1.7.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/longrunning | v0.9.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/monitoring | v1.24.3 |  | go-module-binary-cataloger |
| cloud.google.com/go/storage | v1.62.3 |  | go-module-binary-cataloger |
| connectrpc.com/connect | v1.19.2 |  | go-module-binary-cataloger |
| curl | 8.20.0-r1 | curl | apk-db-cataloger |
| dario.cat/mergo | v1.0.2 |  | go-module-binary-cataloger |
| filippo.io/age | v1.3.1 |  | go-module-binary-cataloger |
| filippo.io/edwards25519 | v1.2.0 |  | go-module-binary-cataloger |
| filippo.io/hpke | v0.4.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.22.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.13.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.12.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/storage/azblob | v1.6.4 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/to | v0.4.1 |  | go-module-binary-cataloger |
| github.com/Azure/go-ntlmssp | v0.1.1 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.6.0 |  | go-module-binary-cataloger |
| github.com/BurntSushi/toml | v1.6.0 |  | go-module-binary-cataloger |
| github.com/FZambia/eagle | v0.2.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/detectors/gcp | v1.31.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/exporter/metric | v0.55.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/internal/resourcemapping | v0.55.0 |  | go-module-binary-cataloger |
| github.com/IBM/pgxpoolprometheus | v1.1.2 |  | go-module-binary-cataloger |
| github.com/Machiel/slugify | v1.0.1 |  | go-module-binary-cataloger |
| github.com/Masterminds/goutils | v1.1.1 |  | go-module-binary-cataloger |
| github.com/Masterminds/semver | v1.5.0 |  | go-module-binary-cataloger |
| github.com/Masterminds/semver/v3 | v3.5.0 |  | go-module-binary-cataloger |
| github.com/Masterminds/sprig/v3 | v3.3.0 |  | go-module-binary-cataloger |
| github.com/Masterminds/squirrel | v1.5.4 |  | go-module-binary-cataloger |
| github.com/NYTimes/gziphandler | v1.1.1 |  | go-module-binary-cataloger |
| github.com/PaesslerAG/gval | v1.0.0 |  | go-module-binary-cataloger |
| github.com/PaesslerAG/jsonpath | v0.1.1 |  | go-module-binary-cataloger |
| github.com/ProtonMail/go-crypto | v1.4.1 |  | go-module-binary-cataloger |
| github.com/RoaringBitmap/roaring/v2 | v2.14.5 |  | go-module-binary-cataloger |
| github.com/VividCortex/mysqlerr | v1.0.0 |  | go-module-binary-cataloger |
| github.com/Yiling-J/theine-go | v0.6.2 |  | go-module-binary-cataloger |
| github.com/agext/levenshtein | v1.2.3 |  | go-module-binary-cataloger |
| github.com/alecthomas/units | v0.0.0-20240927000941-0f3dac36c52b |  | go-module-binary-cataloger |
| github.com/andybalholm/brotli | v1.2.1 |  | go-module-binary-cataloger |
| github.com/antlr4-go/antlr/v4 | v4.13.1 |  | go-module-binary-cataloger |
| github.com/apache/arrow-go/v18 | v18.5.1 |  | go-module-binary-cataloger |
| github.com/apache/arrow-go/v18 | v18.5.2 |  | go-module-binary-cataloger |
| github.com/apache/arrow-go/v18 | v18.5.2 |  | go-module-binary-cataloger |
| github.com/apache/arrow-go/v18 | v18.6.0 |  | go-module-binary-cataloger |
| github.com/apache/thrift | v0.23.1-0.20260429145742-d2acd3c49e58 |  | go-module-binary-cataloger |
| github.com/apapsch/go-jsonmerge/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/apparentlymart/go-textseg/v15 | v15.0.0 |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/armon/go-radix | v1.0.0 |  | go-module-binary-cataloger |
| github.com/at-wat/mqtt-go | v0.19.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go | v1.55.8 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.41.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.41.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.41.9 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/aws/protocol/eventstream | v1.7.10 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.18 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.23 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/s3/manager | v1.20.12 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.25 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.25 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/ini | v1.8.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/ini | v1.8.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/v4a | v1.4.24 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/bedrockruntime | v1.50.5 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/cloudwatch | v1.45.3 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/cloudwatchlogs | v1.73.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ec2 | v1.304.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.4 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.9 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/checksum | v1.9.15 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.23 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/s3shared | v1.19.23 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/oam | v1.18.3 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/resourcegroupstaggingapi | v1.26.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/s3 | v1.101.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.11 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.5 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.5 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.9 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.9 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.35.13 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.35.13 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.36.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.41.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.41.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.42.1 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.24.0 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.24.0 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.26.0 |  | go-module-binary-cataloger |
| github.com/bahlo/generic-list-go | v0.2.0 |  | go-module-binary-cataloger |
| github.com/barkimedes/go-deepcopy | v0.0.0-20220514131651-17c30cfc62df |  | go-module-binary-cataloger |
| github.com/benbjohnson/clock | v1.3.5 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/bits-and-blooms/bitset | v1.24.4 |  | go-module-binary-cataloger |
| github.com/blang/semver | v3.5.1+incompatible |  | go-module-binary-cataloger |
| github.com/blang/semver/v4 | v4.0.0 |  | go-module-binary-cataloger |
| github.com/blevesearch/bleve/v2 | v2.5.7 |  | go-module-binary-cataloger |
| github.com/blevesearch/bleve_index_api | v1.3.11 |  | go-module-binary-cataloger |
| github.com/blevesearch/geo | v0.2.5 |  | go-module-binary-cataloger |
| github.com/blevesearch/go-porterstemmer | v1.0.3 |  | go-module-binary-cataloger |
| github.com/blevesearch/gtreap | v0.1.1 |  | go-module-binary-cataloger |
| github.com/blevesearch/mmap-go | v1.2.0 |  | go-module-binary-cataloger |
| github.com/blevesearch/scorch_segment_api/v2 | v2.4.7 |  | go-module-binary-cataloger |
| github.com/blevesearch/segment | v0.9.1 |  | go-module-binary-cataloger |
| github.com/blevesearch/snowballstem | v0.9.0 |  | go-module-binary-cataloger |
| github.com/blevesearch/upsidedown_store_api | v1.0.2 |  | go-module-binary-cataloger |
| github.com/blevesearch/vellum | v1.2.0 |  | go-module-binary-cataloger |
| github.com/blevesearch/zapx/v11 | v11.4.3 |  | go-module-binary-cataloger |
| github.com/blevesearch/zapx/v12 | v12.4.3 |  | go-module-binary-cataloger |
| github.com/blevesearch/zapx/v13 | v13.4.3 |  | go-module-binary-cataloger |
| github.com/blevesearch/zapx/v14 | v14.4.3 |  | go-module-binary-cataloger |
| github.com/blevesearch/zapx/v15 | v15.4.3 |  | go-module-binary-cataloger |
| github.com/blevesearch/zapx/v16 | v16.3.4 |  | go-module-binary-cataloger |
| github.com/bradfitz/gomemcache | v0.0.0-20250403215159-8d39553ac7cf |  | go-module-binary-cataloger |
| github.com/bufbuild/protocompile | v0.14.1 |  | go-module-binary-cataloger |
| github.com/buger/jsonparser | v1.1.2 |  | go-module-binary-cataloger |
| github.com/bwmarrin/snowflake | v0.3.0 |  | go-module-binary-cataloger |
| github.com/c2h5oh/datasize | v0.0.0-20231215233829-aa82cc1e6500 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/centrifugal/centrifuge | v0.38.0 |  | go-module-binary-cataloger |
| github.com/centrifugal/protocol | v0.17.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cheekybits/genny | v1.0.0 |  | go-module-binary-cataloger |
| github.com/cheekybits/genny | v1.0.0 |  | go-module-binary-cataloger |
| github.com/cheekybits/genny | v1.0.0 |  | go-module-binary-cataloger |
| github.com/cheekybits/genny | v1.0.0 |  | go-module-binary-cataloger |
| github.com/chromedp/cdproto | v0.0.0-20250803210736-d308e07a266d |  | go-module-binary-cataloger |
| github.com/clipperhouse/displaywidth | v0.10.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/displaywidth | v0.10.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/displaywidth | v0.11.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/displaywidth | v0.6.2 |  | go-module-binary-cataloger |
| github.com/clipperhouse/stringish | v0.1.1 |  | go-module-binary-cataloger |
| github.com/clipperhouse/uax29/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/uax29/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/uax29/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/uax29/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/cloudflare/circl | v1.6.3 |  | go-module-binary-cataloger |
| github.com/cncf/xds/go | v0.0.0-20260202195803-dba9d589def2 |  | go-module-binary-cataloger |
| github.com/cockroachdb/apd/v2 | v2.0.2 |  | go-module-binary-cataloger |
| github.com/containerd/errdefs | v1.0.0 |  | go-module-binary-cataloger |
| github.com/containerd/errdefs/pkg | v0.3.0 |  | go-module-binary-cataloger |
| github.com/coreos/go-semver | v0.3.1 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.7.0 |  | go-module-binary-cataloger |
| github.com/cpuguy83/go-md2man/v2 | v2.0.7 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/dennwc/varint | v1.0.0 |  | go-module-binary-cataloger |
| github.com/dgraph-io/badger/v4 | v4.9.1 |  | go-module-binary-cataloger |
| github.com/dgraph-io/ristretto/v2 | v2.2.0 |  | go-module-binary-cataloger |
| github.com/diegoholiveira/jsonlogic/v3 | v3.7.4 |  | go-module-binary-cataloger |
| github.com/distribution/reference | v0.6.0 |  | go-module-binary-cataloger |
| github.com/dlmiddlecote/sqlstats | v1.0.2 |  | go-module-binary-cataloger |
| github.com/docker/go-connections | v0.7.0 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/dolthub/flatbuffers/v23 | v23.3.3-dh.2 |  | go-module-binary-cataloger |
| github.com/dolthub/jsonpath | v0.0.2-0.20240227200619-19675ab05c71 |  | go-module-binary-cataloger |
| github.com/dolthub/maphash | v0.1.0 |  | go-module-binary-cataloger |
| github.com/dustin/go-humanize | v1.0.1 |  | go-module-binary-cataloger |
| github.com/edsrzf/mmap-go | v1.2.1-0.20241212181136-fad1cd13edbd |  | go-module-binary-cataloger |
| github.com/elazarl/goproxy | v1.8.3 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.11.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.11.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.13.0 |  | go-module-binary-cataloger |
| github.com/emirpasic/gods | v1.18.1 |  | go-module-binary-cataloger |
| github.com/envoyproxy/go-control-plane/envoy | v1.37.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/protoc-gen-validate | v1.3.3 |  | go-module-binary-cataloger |
| github.com/facette/natsort | v0.0.0-20181210072756-2cd4dd1e2dcb |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.19.0 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.10.1 |  | go-module-binary-cataloger |
| github.com/fullstorydev/grpchan | v1.1.2 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.9.0 |  | go-module-binary-cataloger |
| github.com/gammazero/deque | v0.2.1 |  | go-module-binary-cataloger |
| github.com/gchaincl/sqlhooks | v1.3.0 |  | go-module-binary-cataloger |
| github.com/getkin/kin-openapi | v0.140.0 |  | go-module-binary-cataloger |
| github.com/go-asn1-ber/asn1-ber | v1.5.4 |  | go-module-binary-cataloger |
| github.com/go-jose/go-jose/v4 | v4.1.4 |  | go-module-binary-cataloger |
| github.com/go-json-experiment/json | v0.0.0-20260214004413-d219187c3433 |  | go-module-binary-cataloger |
| github.com/go-kit/log | v0.2.1 |  | go-module-binary-cataloger |
| github.com/go-ldap/ldap/v3 | v3.4.4 |  | go-module-binary-cataloger |
| github.com/go-logfmt/logfmt | v0.6.1 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/analysis | v0.25.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/errors | v0.22.8 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.22.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.22.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.23.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.21.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.21.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.21.6 |  | go-module-binary-cataloger |
| github.com/go-openapi/loads | v0.24.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/runtime | v0.29.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/spec | v0.22.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/strfmt | v0.26.3 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.26.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/cmdutils | v0.26.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/conv | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/fileutils | v0.26.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/jsonname | v0.25.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/jsonname | v0.25.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/jsonname | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/jsonutils | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/loading | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/mangling | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/netutils | v0.26.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/stringutils | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/typeutils | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag/yamlutils | v0.26.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/validate | v0.25.2 |  | go-module-binary-cataloger |
| github.com/go-sourcemap/sourcemap | v2.1.4+incompatible |  | go-module-binary-cataloger |
| github.com/go-sql-driver/mysql | v1.10.0 |  | go-module-binary-cataloger |
| github.com/go-stack/stack | v1.8.1 |  | go-module-binary-cataloger |
| github.com/go-viper/mapstructure/v2 | v2.5.0 |  | go-module-binary-cataloger |
| github.com/gobwas/glob | v0.2.3 |  | go-module-binary-cataloger |
| github.com/goccy/go-json | v0.10.6 |  | go-module-binary-cataloger |
| github.com/gofrs/uuid | v4.4.0+incompatible |  | go-module-binary-cataloger |
| github.com/gogo/googleapis | v1.4.1 |  | go-module-binary-cataloger |
| github.com/gogo/googleapis | v1.4.1 |  | go-module-binary-cataloger |
| github.com/gogo/googleapis | v1.4.1 |  | go-module-binary-cataloger |
| github.com/gogo/googleapis | v1.4.1 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/gogo/status | v1.1.1 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v4 | v4.5.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.3.1 |  | go-module-binary-cataloger |
| github.com/golang-sql/civil | v0.0.0-20220223132316-b832511892a9 |  | go-module-binary-cataloger |
| github.com/golang-sql/sqlexp | v0.1.0 |  | go-module-binary-cataloger |
| github.com/golang/mock | v1.7.0-rc.1 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v1.0.0 |  | go-module-binary-cataloger |
| github.com/google/btree | v1.1.3 |  | go-module-binary-cataloger |
| github.com/google/cel-go | v0.28.0 |  | go-module-binary-cataloger |
| github.com/google/flatbuffers | v25.12.19+incompatible |  | go-module-binary-cataloger |
| github.com/google/flatbuffers | v25.12.19+incompatible |  | go-module-binary-cataloger |
| github.com/google/flatbuffers | v25.12.19+incompatible |  | go-module-binary-cataloger |
| github.com/google/flatbuffers | v25.12.19+incompatible |  | go-module-binary-cataloger |
| github.com/google/gnostic | v0.7.1 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.7.1 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-github/v82 | v82.0.0 |  | go-module-binary-cataloger |
| github.com/google/go-querystring | v1.2.0 |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.9 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/wire | v0.7.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.16 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.22.0 |  | go-module-binary-cataloger |
| github.com/gorilla/mux | v1.8.1 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.4-0.20250319132907-e064f32e3674 |  | go-module-binary-cataloger |
| github.com/grafana/alerting | v0.0.0-20260616104851-587c401ed754 |  | go-module-binary-cataloger |
| github.com/grafana/authlib | v0.0.0-20260603144019-18cfcbc9496a |  | go-module-binary-cataloger |
| github.com/grafana/authlib/types | v0.0.0-20260603144019-18cfcbc9496a |  | go-module-binary-cataloger |
| github.com/grafana/cue | v0.0.0-20230926092038-971951014e3f |  | go-module-binary-cataloger |
| github.com/grafana/dataplane/sdata | v0.0.9 |  | go-module-binary-cataloger |
| github.com/grafana/dataplane/sdata | v0.0.9 |  | go-module-binary-cataloger |
| github.com/grafana/dataplane/sdata | v0.0.9 |  | go-module-binary-cataloger |
| github.com/grafana/dskit | v0.0.0-20260427162712-0457a92dacc3 |  | go-module-binary-cataloger |
| github.com/grafana/go-mysql-server | v0.20.2-grafana-4 |  | go-module-binary-cataloger |
| github.com/grafana/gomemcache | v0.0.0-20251127154401-74f93547077b |  | go-module-binary-cataloger |
| github.com/grafana/grafana | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana-app-sdk | v0.56.2 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-app-sdk/logging | v0.56.2 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-aws-sdk | v1.4.3 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-aws-sdk | v1.4.3 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-aws-sdk | v1.4.4 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-azure-sdk-go/v2 | v2.4.1 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-cloud-migration-snapshot | v1.11.0 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-elasticsearch-datasource | v0.0.0-20260612100722-e6ffa8b41781 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-elasticsearch-datasource | v0.0.0-20260612100722-e6ffa8b41781 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-google-sdk-go | v0.4.2 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-plugin-sdk-go | v0.290.0 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-plugin-sdk-go | v0.291.1 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-plugin-sdk-go | v0.291.1 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-plugin-sdk-go | v0.292.1 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-prometheus-datasource/pkg/promlib | v0.0.11 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-zipkin-datasource | v0.0.0-20260504104403-712ed9bdeee0 |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/advisor | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/alerting/historian | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/alerting/notifications | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/alerting/rules | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/annotation | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/collections | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/correlations | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/dashboard | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/dashvalidator | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/example | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/folder | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/iam | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/live | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/logsdrilldown | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/playlist | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/plugins | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/preferences | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/provisioning | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/quotas | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/scope | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/secret | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/apps/shorturl | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/pkg/aggregator | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/pkg/apimachinery | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/pkg/apiserver | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/pkg/infra/features | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/pkg/plugins | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/pkg/storage/unified/resource/kv | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/pkg/storage/unified/resourcepb | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana/pkg/util/sqlite | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/jsonparser | v0.0.0-20241004153430-023329977675 |  | go-module-binary-cataloger |
| github.com/grafana/loki/pkg/push | v0.0.0-20250823105456-332df2b20000 |  | go-module-binary-cataloger |
| github.com/grafana/loki/v3 | v3.7.2 |  | go-module-binary-cataloger |
| github.com/grafana/memberlist | v0.3.1-0.20251126142931-6f9f62ab6f86 |  | go-module-binary-cataloger |
| github.com/grafana/nanogit | v0.18.1 |  | go-module-binary-cataloger |
| github.com/grafana/otel-profiling-go | v0.5.1 |  | go-module-binary-cataloger |
| github.com/grafana/otel-profiling-go | v0.5.1 |  | go-module-binary-cataloger |
| github.com/grafana/otel-profiling-go | v0.5.1 |  | go-module-binary-cataloger |
| github.com/grafana/otel-profiling-go | v0.5.1 |  | go-module-binary-cataloger |
| github.com/grafana/prometheus-alertmanager | v0.25.1-0.20260225120258-18275ca76b0c |  | go-module-binary-cataloger |
| github.com/grafana/pyroscope-go/godeltaprof | v0.1.9 |  | go-module-binary-cataloger |
| github.com/grafana/pyroscope-go/godeltaprof | v0.1.9 |  | go-module-binary-cataloger |
| github.com/grafana/pyroscope-go/godeltaprof | v0.1.9 |  | go-module-binary-cataloger |
| github.com/grafana/pyroscope-go/godeltaprof | v0.1.9 |  | go-module-binary-cataloger |
| github.com/grafana/pyroscope/api | v1.3.0 |  | go-module-binary-cataloger |
| github.com/grafana/regexp | v0.0.0-20250905093917-f7b3be9d1853 |  | go-module-binary-cataloger |
| github.com/grafana/schemads | v0.0.8 |  | go-module-binary-cataloger |
| github.com/grafana/schemads | v0.0.8 |  | go-module-binary-cataloger |
| github.com/grafana/schemads | v0.2.2 |  | go-module-binary-cataloger |
| github.com/grafana/sqlds/v5 | v5.0.4 |  | go-module-binary-cataloger |
| github.com/grafana/sqlds/v5 | v5.0.4 |  | go-module-binary-cataloger |
| github.com/grafana/sqlds/v5 | v5.1.1 |  | go-module-binary-cataloger |
| github.com/grafana/tempo | v1.5.1-0.20260427112133-525d1bab07e0 |  | go-module-binary-cataloger |
| github.com/grafana/vitess | v0.0.0-grafana-2 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware | v1.4.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware/providers/prometheus | v1.1.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware/providers/prometheus | v1.1.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware/providers/prometheus | v1.1.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware/providers/prometheus | v1.1.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware/v2 | v2.3.3 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware/v2 | v2.3.3 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware/v2 | v2.3.3 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware/v2 | v2.3.3 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.27.7 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.28.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.28.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.29.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/consul/api | v1.33.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-immutable-radix | v1.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-metrics | v0.5.4 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-msgpack/v2 | v2.1.5 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-plugin | v1.7.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-plugin | v1.7.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-plugin | v1.7.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-plugin | v1.7.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-secure-stdlib/plugincontainer | v0.5.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-sockaddr | v1.0.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-uuid | v1.0.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-version | v1.9.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru/v2 | v2.0.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/hcl/v2 | v2.24.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/serf | v0.10.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/yamux | v0.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/yamux | v0.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/yamux | v0.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/yamux | v0.1.2 |  | go-module-binary-cataloger |
| github.com/huandu/go-clone | v1.7.3 |  | go-module-binary-cataloger |
| github.com/huandu/go-clone | v1.7.3 |  | go-module-binary-cataloger |
| github.com/huandu/go-clone | v1.7.3 |  | go-module-binary-cataloger |
| github.com/huandu/go-sqlbuilder | v1.39.1 |  | go-module-binary-cataloger |
| github.com/huandu/go-sqlbuilder | v1.39.1 |  | go-module-binary-cataloger |
| github.com/huandu/go-sqlbuilder | v1.40.2 |  | go-module-binary-cataloger |
| github.com/huandu/xstrings | v1.4.0 |  | go-module-binary-cataloger |
| github.com/huandu/xstrings | v1.4.0 |  | go-module-binary-cataloger |
| github.com/huandu/xstrings | v1.5.0 |  | go-module-binary-cataloger |
| github.com/influxdata/influxdb-client-go/v2 | v2.14.0 |  | go-module-binary-cataloger |
| github.com/influxdata/influxql | v1.4.1 |  | go-module-binary-cataloger |
| github.com/influxdata/line-protocol | v0.0.0-20210922203350-b1ad95c89adf |  | go-module-binary-cataloger |
| github.com/invopop/jsonschema | v0.14.0 |  | go-module-binary-cataloger |
| github.com/jackc/pgpassfile | v1.0.0 |  | go-module-binary-cataloger |
| github.com/jackc/pgservicefile | v0.0.0-20240606120523-5a60cdf6a761 |  | go-module-binary-cataloger |
| github.com/jackc/pgx/v5 | v5.9.2 |  | go-module-binary-cataloger |
| github.com/jackc/puddle/v2 | v2.2.2 |  | go-module-binary-cataloger |
| github.com/jaegertracing/jaeger-idl | v0.6.0 |  | go-module-binary-cataloger |
| github.com/jaegertracing/jaeger-idl | v0.6.0 |  | go-module-binary-cataloger |
| github.com/jaegertracing/jaeger-idl | v0.6.0 |  | go-module-binary-cataloger |
| github.com/jaegertracing/jaeger-idl | v0.6.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/aescts/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/dnsutils/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/gofork | v1.7.6 |  | go-module-binary-cataloger |
| github.com/jcmturner/goidentity/v6 | v6.0.1 |  | go-module-binary-cataloger |
| github.com/jcmturner/gokrb5/v8 | v8.4.4 |  | go-module-binary-cataloger |
| github.com/jcmturner/rpc/v2 | v2.0.3 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.6.1 |  | go-module-binary-cataloger |
| github.com/jhump/protoreflect | v1.17.0 |  | go-module-binary-cataloger |
| github.com/jmespath-community/go-jmespath | v1.1.1 |  | go-module-binary-cataloger |
| github.com/jmespath/go-jmespath | v0.4.0 |  | go-module-binary-cataloger |
| github.com/jmoiron/sqlx | v1.4.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/joshlf/go-acl | v0.0.0-20200411065538-eae00ae38531 |  | go-module-binary-cataloger |
| github.com/jpillora/backoff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/jszwedko/go-datemath | v0.1.1-0.20230526204004-640a500621d6 |  | go-module-binary-cataloger |
| github.com/jszwedko/go-datemath | v0.1.1-0.20230526204004-640a500621d6 |  | go-module-binary-cataloger |
| github.com/jszwedko/go-datemath | v0.1.1-0.20230526204004-640a500621d6 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.2 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.4 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.4 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.6 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/klauspost/pgzip | v1.2.6 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/lann/builder | v0.0.0-20180802200727-47ae307949d0 |  | go-module-binary-cataloger |
| github.com/lann/ps | v0.0.0-20150810152359-62de8c46ede0 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/strftime | v1.0.4 |  | go-module-binary-cataloger |
| github.com/lib/pq | v1.12.3 |  | go-module-binary-cataloger |
| github.com/m3db/prometheus_remote_client_golang | v0.4.4 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.9.1 |  | go-module-binary-cataloger |
| github.com/mattbaird/jsonpatch | v0.0.0-20240118010651-0ba75a80ca38 |  | go-module-binary-cataloger |
| github.com/mattetti/filebuffer | v1.0.1 |  | go-module-binary-cataloger |
| github.com/mattetti/filebuffer | v1.0.1 |  | go-module-binary-cataloger |
| github.com/mattetti/filebuffer | v1.0.1 |  | go-module-binary-cataloger |
| github.com/mattetti/filebuffer | v1.0.1 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.22 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.19 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.19 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.19 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.20 |  | go-module-binary-cataloger |
| github.com/matttproud/golang_protobuf_extensions | v1.0.4 |  | go-module-binary-cataloger |
| github.com/maypok86/otter | v1.2.4 |  | go-module-binary-cataloger |
| github.com/mdlayher/socket | v0.5.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/vsock | v1.2.1 |  | go-module-binary-cataloger |
| github.com/mfridman/interpolate | v0.0.2 |  | go-module-binary-cataloger |
| github.com/microsoft/go-mssqldb | v1.10.0 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.72 |  | go-module-binary-cataloger |
| github.com/mitchellh/copystructure | v1.2.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-wordwrap | v1.0.1 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.1-0.20231216201459-8508981c8b6c |  | go-module-binary-cataloger |
| github.com/mitchellh/reflectwalk | v1.0.2 |  | go-module-binary-cataloger |
| github.com/mithrandie/csvq | v1.18.1 |  | go-module-binary-cataloger |
| github.com/mithrandie/csvq | v1.18.1 |  | go-module-binary-cataloger |
| github.com/mithrandie/csvq | v1.18.1 |  | go-module-binary-cataloger |
| github.com/mithrandie/csvq-driver | v1.7.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/csvq-driver | v1.7.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/csvq-driver | v1.7.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/go-file/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/go-file/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/go-file/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/go-text | v1.6.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/go-text | v1.6.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/go-text | v1.6.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/ternary | v1.1.1 |  | go-module-binary-cataloger |
| github.com/mithrandie/ternary | v1.1.1 |  | go-module-binary-cataloger |
| github.com/mithrandie/ternary | v1.1.1 |  | go-module-binary-cataloger |
| github.com/moby/docker-image-spec | v1.3.1 |  | go-module-binary-cataloger |
| github.com/moby/moby/api | v1.54.2 |  | go-module-binary-cataloger |
| github.com/moby/moby/client | v0.4.1 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.3-0.20250322232337-35a7c28c31ee |  | go-module-binary-cataloger |
| github.com/mpvl/unique | v0.0.0-20150818121801-cbe035fff7de |  | go-module-binary-cataloger |
| github.com/mschoch/smat | v0.2.0 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/mwitkow/go-conntrack | v0.0.0-20190716064945-2f068394615f |  | go-module-binary-cataloger |
| github.com/natefinch/wrap | v0.2.0 |  | go-module-binary-cataloger |
| github.com/nikunjy/rules | v1.5.0 |  | go-module-binary-cataloger |
| github.com/oapi-codegen/runtime | v1.0.0 |  | go-module-binary-cataloger |
| github.com/oasdiff/yaml | v0.1.0 |  | go-module-binary-cataloger |
| github.com/oasdiff/yaml3 | v0.0.13 |  | go-module-binary-cataloger |
| github.com/oklog/run | v1.1.0 |  | go-module-binary-cataloger |
| github.com/oklog/run | v1.1.0 |  | go-module-binary-cataloger |
| github.com/oklog/run | v1.1.0 |  | go-module-binary-cataloger |
| github.com/oklog/run | v1.2.0 |  | go-module-binary-cataloger |
| github.com/oklog/ulid | v1.3.1 |  | go-module-binary-cataloger |
| github.com/oklog/ulid/v2 | v2.1.1 |  | go-module-binary-cataloger |
| github.com/olekukonko/cat | v0.0.0-20250911104152-50322a0618f6 |  | go-module-binary-cataloger |
| github.com/olekukonko/cat | v0.0.0-20250911104152-50322a0618f6 |  | go-module-binary-cataloger |
| github.com/olekukonko/cat | v0.0.0-20250911104152-50322a0618f6 |  | go-module-binary-cataloger |
| github.com/olekukonko/cat | v0.0.0-20250911104152-50322a0618f6 |  | go-module-binary-cataloger |
| github.com/olekukonko/errors | v1.1.0 |  | go-module-binary-cataloger |
| github.com/olekukonko/errors | v1.2.0 |  | go-module-binary-cataloger |
| github.com/olekukonko/errors | v1.2.0 |  | go-module-binary-cataloger |
| github.com/olekukonko/errors | v1.2.0 |  | go-module-binary-cataloger |
| github.com/olekukonko/ll | v0.1.4-0.20260115111900-9e59c2286df0 |  | go-module-binary-cataloger |
| github.com/olekukonko/ll | v0.1.6 |  | go-module-binary-cataloger |
| github.com/olekukonko/ll | v0.1.6 |  | go-module-binary-cataloger |
| github.com/olekukonko/ll | v0.1.6 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v1.1.3 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v1.1.4 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v1.1.4 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v1.1.4 |  | go-module-binary-cataloger |
| github.com/open-feature/go-sdk | v1.17.2 |  | go-module-binary-cataloger |
| github.com/open-feature/go-sdk-contrib/providers/ofrep | v0.1.7 |  | go-module-binary-cataloger |
| github.com/openai/openai-go/v3 | v3.16.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/image-spec | v1.1.1 |  | go-module-binary-cataloger |
| github.com/openfga/api/proto | v0.0.0-20260319214821-f153694bfc20 |  | go-module-binary-cataloger |
| github.com/openfga/language/pkg/go | v0.2.1 |  | go-module-binary-cataloger |
| github.com/openfga/openfga | v1.14.2 |  | go-module-binary-cataloger |
| github.com/opentracing-contrib/go-grpc | v0.1.2 |  | go-module-binary-cataloger |
| github.com/opentracing-contrib/go-stdlib | v1.1.1 |  | go-module-binary-cataloger |
| github.com/opentracing/opentracing-go | v1.2.1-0.20220228012449-10b1cf09e00b |  | go-module-binary-cataloger |
| github.com/openzipkin/zipkin-go | v0.4.3 |  | go-module-binary-cataloger |
| github.com/patrickmn/go-cache | v2.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/patrickmn/go-cache | v2.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/patrickmn/go-cache | v2.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/patrickmn/go-cache | v2.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/pb33f/ordered-map/v2 | v2.3.1 |  | go-module-binary-cataloger |
| github.com/pelletier/go-toml/v2 | v2.2.4 |  | go-module-binary-cataloger |
| github.com/pgvector/pgvector-go | v0.3.0 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.23 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.25 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.25 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.26 |  | go-module-binary-cataloger |
| github.com/pires/go-proxyproto | v0.11.0 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/planetscale/vtprotobuf | v0.6.1-0.20250313105119-ba97887b0a25 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/pressly/goose/v3 | v3.27.1 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang/exp | v0.0.0-20260518105423-c9d5bc4c50a9 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.5 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.5 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.5 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.68.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common/sigv4 | v0.1.0 |  | go-module-binary-cataloger |
| github.com/prometheus/exporter-toolkit | v0.16.0 |  | go-module-binary-cataloger |
| github.com/prometheus/otlptranslator | v1.0.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.16.1 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.16.1 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.16.1 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.20.1 |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.312.0 |  | go-module-binary-cataloger |
| github.com/prometheus/sigv4 | v0.4.1 |  | go-module-binary-cataloger |
| github.com/puzpuzpuz/xsync/v2 | v2.5.1 |  | go-module-binary-cataloger |
| github.com/puzpuzpuz/xsync/v4 | v4.5.0 |  | go-module-binary-cataloger |
| github.com/quagmt/udecimal | v1.9.0 |  | go-module-binary-cataloger |
| github.com/redis/go-redis/v9 | v9.19.0 |  | go-module-binary-cataloger |
| github.com/redis/rueidis | v1.0.72 |  | go-module-binary-cataloger |
| github.com/remyoudompheng/bigfft | v0.0.0-20230129092748-24d4a6f8daec |  | go-module-binary-cataloger |
| github.com/rs/cors | v1.11.1 |  | go-module-binary-cataloger |
| github.com/russross/blackfriday/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/sagikazarmark/locafero | v0.11.0 |  | go-module-binary-cataloger |
| github.com/santhosh-tekuri/jsonschema/v6 | v6.0.2 |  | go-module-binary-cataloger |
| github.com/sean-/seed | v0.0.0-20170313163322-e2103e2c3529 |  | go-module-binary-cataloger |
| github.com/segmentio/asm | v1.2.1 |  | go-module-binary-cataloger |
| github.com/segmentio/encoding | v0.5.3 |  | go-module-binary-cataloger |
| github.com/sercand/kuberesolver/v6 | v6.0.1 |  | go-module-binary-cataloger |
| github.com/sethvargo/go-retry | v0.3.0 |  | go-module-binary-cataloger |
| github.com/shadowspore/fossil-delta | v0.0.0-20241213113458-1d797d70cbe3 |  | go-module-binary-cataloger |
| github.com/shopspring/decimal | v1.4.0 |  | go-module-binary-cataloger |
| github.com/shurcooL/httpfs | v0.0.0-20230704072500-f1e31cf0ba5c |  | go-module-binary-cataloger |
| github.com/shurcooL/vfsgen | v0.0.0-20230704071429-0000e147ea92 |  | go-module-binary-cataloger |
| github.com/sirupsen/logrus | v1.9.4 |  | go-module-binary-cataloger |
| github.com/smallstep/pkcs7 | v0.2.1 |  | go-module-binary-cataloger |
| github.com/sony/gobreaker/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/sourcegraph/conc | v0.3.1-0.20240121214520-5f936abd7ae8 |  | go-module-binary-cataloger |
| github.com/spf13/afero | v1.15.0 |  | go-module-binary-cataloger |
| github.com/spf13/cast | v1.10.0 |  | go-module-binary-cataloger |
| github.com/spf13/cobra | v1.10.2 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/spf13/viper | v1.21.0 |  | go-module-binary-cataloger |
| github.com/spiffe/go-spiffe/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/stretchr/objx | v0.5.2 |  | go-module-binary-cataloger |
| github.com/stretchr/objx | v0.5.2 |  | go-module-binary-cataloger |
| github.com/stretchr/objx | v0.5.3 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.11.1 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.11.1 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.11.1 |  | go-module-binary-cataloger |
| github.com/subosito/gotenv | v1.6.0 |  | go-module-binary-cataloger |
| github.com/thomaspoignant/go-feature-flag | v1.42.0 |  | go-module-binary-cataloger |
| github.com/tidwall/gjson | v1.18.0 |  | go-module-binary-cataloger |
| github.com/tidwall/match | v1.1.1 |  | go-module-binary-cataloger |
| github.com/tidwall/pretty | v1.2.1 |  | go-module-binary-cataloger |
| github.com/tidwall/sjson | v1.2.5 |  | go-module-binary-cataloger |
| github.com/tjhop/slog-gokit | v0.2.0 |  | go-module-binary-cataloger |
| github.com/ua-parser/uap-go | v0.0.0-20251207011819-db9adb27a0b8 |  | go-module-binary-cataloger |
| github.com/uber/jaeger-client-go | v2.30.0+incompatible |  | go-module-binary-cataloger |
| github.com/uber/jaeger-lib | v2.4.1+incompatible |  | go-module-binary-cataloger |
| github.com/urfave/cli/v2 | v2.27.7 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/wk8/go-ordered-map | v1.0.0 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/xlab/treeprint | v1.2.0 |  | go-module-binary-cataloger |
| github.com/xrash/smetrics | v0.0.0-20240521201337-686a1a2994c1 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/zclconf/go-cty | v1.16.3 |  | go-module-binary-cataloger |
| github.com/zeebo/xxh3 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/zeebo/xxh3 | v1.1.0 |  | go-module-binary-cataloger |
| github.com/zeebo/xxh3 | v1.1.0 |  | go-module-binary-cataloger |
| github.com/zeebo/xxh3 | v1.1.0 |  | go-module-binary-cataloger |
| go.etcd.io/bbolt | v1.4.3 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/api/v3 | v3.6.9 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.6.9 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.6.9 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/featuregate | v1.59.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/pdata | v1.59.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/bridges/prometheus | v0.68.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/detectors/gcp | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/exporters/autoexport | v0.68.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc | v0.65.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc | v0.68.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace | v0.65.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace | v0.67.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace | v0.69.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.69.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/jaeger | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/jaeger | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/jaeger | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/jaeger | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/samplers/jaegerremote | v0.34.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/samplers/jaegerremote | v0.36.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/samplers/jaegerremote | v0.36.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/samplers/jaegerremote | v0.37.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.44.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/jaeger | v1.17.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.44.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.42.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.44.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp | v1.44.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/prometheus | v0.65.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/stdout/stdoutlog | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/stdout/stdoutmetric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/stdout/stdouttrace | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/log | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.44.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.44.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/log | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/metric | v1.44.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.40.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.44.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.10.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.9.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.9.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.9.0 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/mock | v0.6.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.28.0 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.3 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.3 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.3 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v4 | v4.0.0-rc.4 |  | go-module-binary-cataloger |
| go4.org/netipx | v0.0.0-20230125063823-8449b0a6169f |  | go-module-binary-cataloger |
| gocloud.dev | v0.45.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.52.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.52.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.52.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20251002181428-27f1f14c8bb9 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20260112195511-716be5621a96 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20260112195511-716be5621a96 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20260410095643-746e56fc9e2f |  | go-module-binary-cataloger |
| golang.org/x/net | v0.49.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.55.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.55.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.55.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.21.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.45.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.45.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.45.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.43.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.43.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.43.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.37.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.37.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.37.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.15.0 |  | go-module-binary-cataloger |
| golang.org/x/tools | v0.45.0 |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20240903120638-7835f813f4da |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20240903120638-7835f813f4da |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20240903120638-7835f813f4da |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20240903120638-7835f813f4da |  | go-module-binary-cataloger |
| gomodules.xyz/jsonpatch/v2 | v2.5.0 |  | go-module-binary-cataloger |
| gonum.org/v1/gonum | v0.17.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.283.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20210630183607-d20f26d13c79 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20210630183607-d20f26d13c79 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20210630183607-d20f26d13c79 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20260319201613-d00831a3d3e7 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20260526163538-3dc84a4a5aaa |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20260526163538-3dc84a4a5aaa |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.79.3 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.79.3 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.79.3 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.81.1 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.12-0.20260120151049-f2248ac996af |  | go-module-binary-cataloger |
| gopkg.in/evanphx/json-patch.v4 | v4.13.0 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/ini.v1 | v1.67.2 |  | go-module-binary-cataloger |
| gopkg.in/mail.v2 | v2.3.1 |  | go-module-binary-cataloger |
| gopkg.in/natefinch/lumberjack.v2 | v2.2.1 |  | go-module-binary-cataloger |
| gopkg.in/src-d/go-errors.v1 | v1.0.0 |  | go-module-binary-cataloger |
| gopkg.in/telebot.v3 | v3.3.8 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| grafana | 13.1.0 |  | binary-classifier-cataloger |
| k8s.io/api | v0.36.1 |  | go-module-binary-cataloger |
| k8s.io/apiextensions-apiserver | v0.36.0 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.36.1 |  | go-module-binary-cataloger |
| k8s.io/apiserver | v0.36.0 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.36.1 |  | go-module-binary-cataloger |
| k8s.io/component-base | v0.36.0 |  | go-module-binary-cataloger |
| k8s.io/klog/v2 | v2.140.0 |  | go-module-binary-cataloger |
| k8s.io/kms | v0.36.0 |  | go-module-binary-cataloger |
| k8s.io/kube-aggregator | v0.36.0 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20260127142750-a19766b6e2d4 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20260127142750-a19766b6e2d4 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20260317180543-43fb72c5454a |  | go-module-binary-cataloger |
| k8s.io/streaming | v0.36.1 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20260210185600-b8788abfbbc2 |  | go-module-binary-cataloger |
| libapk | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| libcap2 | 2.78-r0 | BSD-3-Clause OR GPL-2.0-only | apk-db-cataloger |
| libcrypto3 | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| libcurl | 8.20.0-r1 | curl | apk-db-cataloger |
| libidn2 | 2.3.8-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libncursesw | 6.6_p20260516-r0 | X11 | apk-db-cataloger |
| libpsl | 0.21.5-r3 | MIT | apk-db-cataloger |
| libssl3 | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| libunistring | 1.4.2-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| modernc.org/libc | v1.72.3 |  | go-module-binary-cataloger |
| modernc.org/mathutil | v1.7.1 |  | go-module-binary-cataloger |
| modernc.org/memory | v1.11.0 |  | go-module-binary-cataloger |
| modernc.org/sqlite | v1.52.0 |  | go-module-binary-cataloger |
| musl | 1.2.6-r2 | MIT | apk-db-cataloger |
| musl-utils | 1.2.6-r2 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.6_p20260516-r0 | X11 | apk-db-cataloger |
| nghttp2-libs | 1.69.0-r0 | MIT | apk-db-cataloger |
| readline | 8.3.3-r1 | GPL-3.0-or-later | apk-db-cataloger |
| scanelf | 1.3.9-r1 | GPL-2.0-only | apk-db-cataloger |
| sigs.k8s.io/apiserver-network-proxy/konnectivity-client | v0.34.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20250730193827-2d320260d730 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v6 | v6.4.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.6.0 |  | go-module-binary-cataloger |
| software.sslmate.com/src/go-pkcs12 | v0.7.0 |  | go-module-binary-cataloger |
| ssl_client | 1.37.0-r31 | GPL-2.0-only | apk-db-cataloger |
| stdlib | go1.25.7 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.26.3 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.26.3 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.26.4 | BSD-3-Clause | go-module-binary-cataloger |
| tzdata | 2026b-r0 |  | apk-db-cataloger |
| xorm.io/builder | v0.3.13 |  | go-module-binary-cataloger |
| zlib | 1.3.2-r0 | Zlib | apk-db-cataloger |
| zstd-libs | 1.5.7-r2 | BSD-3-Clause OR GPL-2.0-or-later | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/ollama

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| apt | 2.8.3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| base-files | 13ubuntu10.4 |  | dpkg-db-cataloger |
| base-passwd | 3.6.3build1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.21-2ubuntu4 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| bsdutils | 1:2.39.3-9ubuntu6.5 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20240203 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| coreutils | 9.4-3ubuntu6.2 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| dash | 0.5.12-6ubuntu5 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.86ubuntu1 | BSD-2-Clause | dpkg-db-cataloger |
| debianutils | 5.17build1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| diffutils | 1:3.10-1build1 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dpkg | 1.22.6ubuntu6.5 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| findutils | 4.9.0-5build1 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| gcc-14-base | 14.2.0-4ubuntu2~24.04.1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| github.com/agnivade/levenshtein | v1.1.1 |  | go-module-binary-cataloger |
| github.com/apache/arrow/go/arrow | v0.0.0-20211112161151-bc219186db40 |  | go-module-binary-cataloger |
| github.com/aymanbagabas/go-osc52/v2 | v2.0.1 |  | go-module-binary-cataloger |
| github.com/bahlo/generic-list-go | v0.2.0 |  | go-module-binary-cataloger |
| github.com/buger/jsonparser | v1.1.1 |  | go-module-binary-cataloger |
| github.com/charmbracelet/bubbletea | v1.3.10 |  | go-module-binary-cataloger |
| github.com/charmbracelet/colorprofile | v0.2.3-0.20250311203215-f60798e515dc |  | go-module-binary-cataloger |
| github.com/charmbracelet/lipgloss | v1.1.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/ansi | v0.10.1 |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/cellbuf | v0.0.13-0.20250311204145-2c3ea96c31dd |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/term | v0.2.1 |  | go-module-binary-cataloger |
| github.com/chewxy/hm | v1.0.0 |  | go-module-binary-cataloger |
| github.com/chewxy/math32 | v1.11.0 |  | go-module-binary-cataloger |
| github.com/containerd/console | v1.0.3 |  | go-module-binary-cataloger |
| github.com/d4l3k/go-bfloat16 | v0.0.0-20211005043715-690c3bdd05f1 |  | go-module-binary-cataloger |
| github.com/dlclark/regexp2 | v1.11.4 |  | go-module-binary-cataloger |
| github.com/emirpasic/gods/v2 | v2.0.0-alpha |  | go-module-binary-cataloger |
| github.com/gabriel-vasile/mimetype | v1.4.3 |  | go-module-binary-cataloger |
| github.com/gin-contrib/cors | v1.7.2 |  | go-module-binary-cataloger |
| github.com/gin-contrib/sse | v0.1.0 |  | go-module-binary-cataloger |
| github.com/gin-gonic/gin | v1.10.0 |  | go-module-binary-cataloger |
| github.com/go-playground/locales | v0.14.1 |  | go-module-binary-cataloger |
| github.com/go-playground/universal-translator | v0.18.1 |  | go-module-binary-cataloger |
| github.com/go-playground/validator/v10 | v10.20.0 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/google/flatbuffers | v24.3.25+incompatible |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.3 |  | go-module-binary-cataloger |
| github.com/leodido/go-urn | v1.4.0 |  | go-module-binary-cataloger |
| github.com/lucasb-eyer/go-colorful | v1.2.0 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.16 |  | go-module-binary-cataloger |
| github.com/mattn/go-sqlite3 | v1.14.24 |  | go-module-binary-cataloger |
| github.com/muesli/ansi | v0.0.0-20230316100256-276c6243b2f6 |  | go-module-binary-cataloger |
| github.com/muesli/cancelreader | v0.2.2 |  | go-module-binary-cataloger |
| github.com/muesli/termenv | v0.16.0 |  | go-module-binary-cataloger |
| github.com/nlpodyssey/gopickle | v0.3.0 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v0.0.5 |  | go-module-binary-cataloger |
| github.com/ollama/ollama | UNKNOWN |  | go-module-binary-cataloger |
| github.com/pdevine/tensor | v0.0.0-20240510204454-f88f4562727c |  | go-module-binary-cataloger |
| github.com/pelletier/go-toml/v2 | v2.2.2 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.4.7 |  | go-module-binary-cataloger |
| github.com/spf13/cobra | v1.7.0 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.5 |  | go-module-binary-cataloger |
| github.com/ugorji/go/codec | v1.2.12 |  | go-module-binary-cataloger |
| github.com/wk8/go-ordered-map/v2 | v2.1.8 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/xo/terminfo | v0.0.0-20220910002029-abceb7e1c41e |  | go-module-binary-cataloger |
| github.com/xtgo/set | v1.0.0 |  | go-module-binary-cataloger |
| go4.org/unsafe/assume-no-moving-gc | v0.0.0-20231121144256-b99613f794b6 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.43.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250218142911-aa4b98e5adaa |  | go-module-binary-cataloger |
| golang.org/x/image | v0.22.0 |  | go-module-binary-cataloger |
| golang.org/x/mod | v0.30.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.46.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.17.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.37.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.30.0 |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20200804184101-5ec99f83aff1 |  | go-module-binary-cataloger |
| gonum.org/v1/gonum | v0.15.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.34.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gorgonia.org/vecf32 | v0.9.0 |  | go-module-binary-cataloger |
| gorgonia.org/vecf64 | v0.9.0 |  | go-module-binary-cataloger |
| gpgv | 2.4.4-2ubuntu17.4 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.11-4build1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gzip | 1.12-1ubuntu3.1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hostname | 3.23+nmu2ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| init-system-helpers | 1.66ubuntu1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libacl1 | 2.3.2-1build1.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0t64 | 2.8.3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libassuan0 | 2.5.6-1build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libattr1 | 1:2.5.2-1build1.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.1.2-2.1build1.1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.1.2-2.1build1.1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblkid1 | 2.39.3-9ubuntu6.5 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbsd0 | 0.12.1-1build1.1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5.1build0.1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.39-0ubuntu8.7 | GFDL-1.3-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.39-0ubuntu8.7 | GFDL-1.3-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.4-2build2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-5ubuntu2.2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.36-4build1 |  | dpkg-db-cataloger |
| libdb5.3t64 | 5.3.28+dfsg2-7 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdebconfclient0 | 0.271ubuntu3 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdrm-amdgpu1 | 2.4.125-1ubuntu0.1~24.04.1 |  | dpkg-db-cataloger |
| libdrm-common | 2.4.125-1ubuntu0.1~24.04.1 |  | dpkg-db-cataloger |
| libdrm2 | 2.4.125-1ubuntu0.1~24.04.1 |  | dpkg-db-cataloger |
| libedit2 | 3.1-20230828-1build1 | BSD-3-Clause | dpkg-db-cataloger |
| libelf1t64 | 0.190-1.1ubuntu0.1 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libexpat1 | 2.6.1-2ubuntu0.4 | MIT | dpkg-db-cataloger |
| libext2fs2t64 | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi8 | 3.4.6-1build1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libgcc-s1 | 14.2.0-4ubuntu2~24.04.1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.3-2build1 | GPL-2.0-only | dpkg-db-cataloger |
| libgfortran5 | 14.2.0-4ubuntu2~24.04.1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgmp10 | 2:6.3.0+dfsg-2ubuntu6.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30t64 | 3.8.3-1.1ubuntu3.5 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.47-3build2.1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libhogweed6t64 | 3.9.1-2.2build1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libicu74 | 74.2-1ubuntu3.1 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn2-0 | 2.3.7-2build1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libllvm20 | 1:20.1.2-0ubuntu1~24.04.2 | Apache-2.0, BSD-3-Clause, BSD-3-Clause, MIT | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1build1.1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.6.1+really5.4.5-1ubuntu0.2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmd0 | 1.1.0-2build1.1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount1 | 2.39.3-9ubuntu6.5 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libncursesw6 | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8t64 | 3.9.1-2.2build1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnpth0t64 | 1.6-3.1build1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libopenblas0 | 0.3.26+ds-1ubuntu0.1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| libopenblas0-pthread | 0.3.26+ds-1ubuntu0.1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| libp11-kit0 | 0.25.3-4ubuntu2.1 | Apache-2.0, BSD-3-Clause, FSFAP, FSFULLR, GPL-2.0-or-later, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, X11 | dpkg-db-cataloger |
| libpam-modules | 1.5.3-5ubuntu5.5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.3-5ubuntu5.5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.3-5ubuntu5.5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.3-5ubuntu5.5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-4ubuntu2.1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.4-4ubuntu3.2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpython3-stdlib | 3.12.3-0ubuntu2.1 |  | dpkg-db-cataloger |
| libpython3.12-minimal | 3.12.3-1ubuntu0.13 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.12-stdlib | 3.12.3-1ubuntu0.13 | GPL-2.0-only | dpkg-db-cataloger |
| libreadline8t64 | 8.2-4build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libseccomp2 | 2.5.5-1ubuntu3.1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.5-2ubuntu2.1 | GPL-2.0-only | dpkg-db-cataloger |
| libsemanage-common | 3.5-1build5 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsemanage2 | 3.5-1build5 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsepol2 | 3.5-2build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsmartcols1 | 2.39.3-9ubuntu6.5 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.45.1-1ubuntu2.6 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssl3t64 | 3.0.13-0ubuntu3.9 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 14.2.0-4ubuntu2~24.04.1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 255.4-1ubuntu8.15 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-3ubuntu0.24.04.2 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libudev1 | 255.4-1ubuntu8.15 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring5 | 1.1-2build1.1 | GFDL-1.2-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| libuuid1 | 2.39.3-9ubuntu6.5 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libvulkan1 | 1.3.275.0-1build1 | Apache-2.0, MIT | dpkg-db-cataloger |
| libwayland-client0 | 1.22.0-2.1build1 | X11 | dpkg-db-cataloger |
| libx11-6 | 2:1.8.7-1build1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.8.7-1build1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-xcb1 | 2:1.8.7-1build1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxau6 | 1:1.0.9-1build6 |  | dpkg-db-cataloger |
| libxcb-dri3-0 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxcb-present0 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxcb-randr0 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxcb-shm0 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxcb-sync1 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxcb-xfixes0 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxcb1 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.3-0ubuntu6 |  | dpkg-db-cataloger |
| libxml2 | 2.9.14+dfsg-1.3ubuntu3.7 | ISC | dpkg-db-cataloger |
| libxshmfence1 | 1.3-1build5 | HPND-sell-variant | dpkg-db-cataloger |
| libxxhash0 | 0.8.2-2build1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libzstd1 | 1.5.5+dfsg2-2build1.1 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-4ubuntu3.2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| mawk | 1.3.4.20240123-1build1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 10.1.0 |  | dpkg-db-cataloger |
| mesa-vulkan-drivers | 25.2.8-0ubuntu0.24.04.1 | Apache-2.0, BSD-2-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, MIT, Unicode-DFS-2016 | dpkg-db-cataloger |
| mount | 2.39.3-9ubuntu6.5 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ncurses-base | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| openssl | 3.0.13-0ubuntu3.9 |  | dpkg-db-cataloger |
| passwd | 1:4.13+dfsg1-4ubuntu3.2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| perl-base | 5.38.2-3.2ubuntu0.2 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| procps | 2:4.0.4-4ubuntu3.2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| python3 | 3.12.3-0ubuntu2.1 |  | dpkg-db-cataloger |
| python3-minimal | 3.12.3-0ubuntu2.1 |  | dpkg-db-cataloger |
| python3.12 | 3.12.3-1ubuntu0.13 | GPL-2.0-only | dpkg-db-cataloger |
| python3.12-minimal | 3.12.3-1ubuntu0.13 | GPL-2.0-only | dpkg-db-cataloger |
| readline-common | 8.2-4build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| sed | 4.9-2build1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sensible-utils | 0.0.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| stdlib | go1.26.0 | BSD-3-Clause | go-module-binary-cataloger |
| sysvinit-utils | 3.08-6ubuntu3 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| tar | 1.35+dfsg-3build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tzdata | 2026a-0ubuntu0.24.04.1 | ICU | dpkg-db-cataloger |
| ubuntu-keyring | 2023.11.28.1 |  | dpkg-db-cataloger |
| unminimize | 0.2.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.39.3-9ubuntu6.5 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| zlib1g | 1:1.3.dfsg-3.1ubuntu2.1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/dovecot

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| adduser | 3.118+deb11u1 | GPL-2.0-only | dpkg-db-cataloger |
| apt | 2.2.4 | GPL-2.0-only | dpkg-db-cataloger |
| base-files | 11.1+deb11u10 |  | dpkg-db-cataloger |
| base-passwd | 3.5.51 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.1-2+deb11u1 | GPL-3.0-only | dpkg-db-cataloger |
| bsdutils | 1:2.36.1-8+deb11u2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20210119 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| coreutils | 8.32-4+b1 | GPL-3.0-only | dpkg-db-cataloger |
| dash | 0.5.11+git20200708+dd9ef66-5 | BSD-3-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.77 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2021.1.1+deb11u1 |  | dpkg-db-cataloger |
| debianutils | 4.11.2 | GPL-2.0-only | dpkg-db-cataloger |
| diffutils | 1:3.7-5 |  | dpkg-db-cataloger |
| dovecot-core | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-gssapi | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-imapd | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-ldap | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-lmtpd | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-lua | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-managesieved | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-mysql | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-pgsql | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-pop3d | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-sieve | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-solr | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-sqlite | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dovecot-submissiond | 2:2.3.21.1-2+debian11 |  | dpkg-db-cataloger |
| dpkg | 1.20.13 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.46.2-2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| findutils | 4.8.0-1 | GFDL-1.3-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-10-base | 10.2.1-6 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-9-base | 9.3.0-22 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| gpgv | 2.2.27-2+deb11u2 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.6-1+deb11u1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gzip | 1.10-4+deb11u1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hostname | 3.23 | GPL-2.0-only | dpkg-db-cataloger |
| init-system-helpers | 1.60 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libacl1 | 2.2.53-10 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.2.4 | GPL-2.0-only | dpkg-db-cataloger |
| libattr1 | 1:2.4.48-6 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0-2 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0-2 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblkid1 | 2.36.1-8+deb11u2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-4 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.31-13+deb11u10 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.31-13+deb11u10 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.7.9-2.2+b1 | GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcom-err2 | 1.46.2-2 |  | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.18-4 |  | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg1-0.8 |  | dpkg-db-cataloger |
| libdebconfclient0 | 0.260 | BSD-2-Clause | dpkg-db-cataloger |
| libexpat1 | 2.2.10-2+deb11u5 | MIT | dpkg-db-cataloger |
| libext2fs2 | 1.46.2-2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| libexttextcat-2.0-0 | 3.4.5-1 | BSD-3-Clause | dpkg-db-cataloger |
| libexttextcat-data | 3.4.5-1 | BSD-3-Clause | dpkg-db-cataloger |
| libffi7 | 3.3-6 |  | dpkg-db-cataloger |
| libgcc-s1 | 10.2.1-6 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.8.7-6 | GPL-2.0-only | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg-1+deb11u1 | GPL-2.0-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgnutls30 | 3.7.1-5+deb11u5 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.38-2 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.18.3-6+deb11u5 | GPL-2.0-only | dpkg-db-cataloger |
| libhogweed6 | 3.7.3-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libidn2-0 | 2.3.0-5 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libk5crypto3 | 1.18.3-6+deb11u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.1-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.18.3-6+deb11u5 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.18.3-6+deb11u5 | GPL-2.0-only | dpkg-db-cataloger |
| libldap-2.4-2 | 2.4.57+dfsg-3+deb11u1 |  | dpkg-db-cataloger |
| libldap-common | 2.4.57+dfsg-3+deb11u1 |  | dpkg-db-cataloger |
| liblua5.3-0 | 5.3.3-1.1+deb11u1 |  | dpkg-db-cataloger |
| liblz4-1 | 1.9.3-2 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.2.5-2.1~deb11u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmariadb3 | 1:10.5.23-0+deb11u1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmount1 | 2.36.1-8+deb11u2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnettle8 | 3.7.3-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libp11-kit0 | 0.23.22-1 | BSD-3-Clause, ISC | dpkg-db-cataloger |
| libpam-modules | 1.4.0-9+deb11u1 |  | dpkg-db-cataloger |
| libpam-modules-bin | 1.4.0-9+deb11u1 |  | dpkg-db-cataloger |
| libpam-runtime | 1.4.0-9+deb11u1 |  | dpkg-db-cataloger |
| libpam0g | 1.4.0-9+deb11u1 |  | dpkg-db-cataloger |
| libpcre2-8-0 | 10.36-2+deb11u1 |  | dpkg-db-cataloger |
| libpcre3 | 2:8.39-13 |  | dpkg-db-cataloger |
| libpq5 | 13.16-0+deb11u1 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libsasl2-2 | 2.1.27+dfsg-2.1+deb11u1 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libsasl2-modules | 2.1.27+dfsg-2.1+deb11u1 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.27+dfsg-2.1+deb11u1 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libseccomp2 | 2.5.1-1+deb11u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.1-3 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.1-1 |  | dpkg-db-cataloger |
| libsemanage1 | 3.1-1+b2 |  | dpkg-db-cataloger |
| libsepol1 | 3.1-1 |  | dpkg-db-cataloger |
| libsmartcols1 | 2.36.1-8+deb11u2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsodium23 | 1.0.18-1 | BSD-2-Clause, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.34.1-3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.46.2-2 |  | dpkg-db-cataloger |
| libssl1.1 | 1.1.1w-0+deb11u1 | OpenSSL | dpkg-db-cataloger |
| libstdc++6 | 10.2.1-6 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libstemmer0d | 2.1.0-1 |  | dpkg-db-cataloger |
| libsystemd0 | 247.3-7+deb11u5 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.16.0-2+deb11u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.2+20201114-2+deb11u2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.1-1+deb11u1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.1-1+deb11u1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libudev1 | 247.3-7+deb11u5 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 0.9.10-4 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.36.1-8+deb11u2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libwrap0 | 7.6.q-31 |  | dpkg-db-cataloger |
| libxxhash0 | 0.8.0-2 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libzstd1 | 1.4.8+dfsg-2.1 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.8.1-1 | GPL-2.0-only | dpkg-db-cataloger |
| logsave | 1.46.2-2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| lsb-base | 11.1.0 | BSD-3-Clause, GPL-2.0-only | dpkg-db-cataloger |
| mariadb-common | 1:10.5.23-0+deb11u1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| mawk | 1.3.4.20200120-2 | GPL-2.0-only | dpkg-db-cataloger |
| mount | 2.36.1-8+deb11u2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| mysql-common | 5.8+1.0.7 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| ncurses-base | 6.2+20201114-2+deb11u2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.2+20201114-2+deb11u2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| openssl | 1.1.1w-0+deb11u1 | OpenSSL | dpkg-db-cataloger |
| passwd | 1:4.8.1-1 | GPL-2.0-only | dpkg-db-cataloger |
| perl-base | 5.32.1-4+deb11u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| sed | 4.7-1 | GPL-3.0-only | dpkg-db-cataloger |
| sensible-utils | 0.0.14 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| ssl-cert | 1.1.0+nmu1 | BSD-3-Clause | dpkg-db-cataloger |
| sysvinit-utils | 2.96-7+deb11u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| tar | 1.34+dfsg-1+deb11u1 | GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tini | 0.19.0-1 |  | dpkg-db-cataloger |
| tzdata | 2024a-0+deb11u1 |  | dpkg-db-cataloger |
| ucf | 3.0043 | GPL-2.0-only | dpkg-db-cataloger |
| util-linux | 2.36.1-8+deb11u2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| zlib1g | 1:1.2.11.dfsg-2+deb11u2 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/roundcube

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| Archive_Tar | 1.6.0 |  | php-pear-serialized-cataloger |
| Console_Getopt | 1.4.3 | BSD-2-Clause | php-pear-serialized-cataloger |
| PEAR | 1.10.18 |  | php-pear-serialized-cataloger |
| Structures_Graph | 1.2.0 |  | php-pear-serialized-cataloger |
| XML_Util | 1.4.5 |  | php-pear-serialized-cataloger |
| adduser | 3.152 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| apache2 | 2.4.67-1~deb13u3 | Apache-2.0, BSD-2-Clause-Darwin, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| apache2-bin | 2.4.67-1~deb13u3 | Apache-2.0, BSD-2-Clause-Darwin, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| apache2-data | 2.4.67-1~deb13u3 | Apache-2.0, BSD-2-Clause-Darwin, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| apache2-utils | 2.4.67-1~deb13u3 | Apache-2.0, BSD-2-Clause-Darwin, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| apt | 3.0.3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, curl | dpkg-db-cataloger |
| aspell | 0.60.8.1-4 | GFDL-1.2-only, GFDL-1.2-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| aspell-en | 2020.12.07-0-1 |  | dpkg-db-cataloger |
| autoconf | 2.72-3.1 | GFDL-1.3-only, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| bacon/bacon-qr-code | 2.0.8 | BSD-2-Clause | php-composer-installed-cataloger |
| bacon/bacon-qr-code | 2.0.8 | BSD-2-Clause | php-composer-installed-cataloger |
| base-files | 13.8+deb13u5 | GPL-2.0-or-later | dpkg-db-cataloger |
| base-passwd | 3.6.7 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.37-2+b9 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| binutils | 2.44-3 |  | dpkg-db-cataloger |
| binutils-common | 2.44-3 |  | dpkg-db-cataloger |
| binutils-x86-64-linux-gnu | 2.44-3 |  | dpkg-db-cataloger |
| bsdutils | 1:2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| bzip2 | 1.0.8-6 | GPL-2.0-only | dpkg-db-cataloger |
| ca-certificates | 20250419 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| composer | 2.10.1 |  | binary-classifier-cataloger |
| coreutils | 9.7-3 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cpp | 4:14.2.0-1 | GPL-2.0-only | dpkg-db-cataloger |
| cpp-14 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| cpp-14-x86-64-linux-gnu | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| cpp-x86-64-linux-gnu | 4:14.2.0-1 | GPL-2.0-only | dpkg-db-cataloger |
| curl | 8.14.1-2+deb13u3 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| dash | 0.5.12-12 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dasprid/enum | 1.0.7 | BSD-2-Clause | php-composer-installed-cataloger |
| dasprid/enum | 1.0.7 | BSD-2-Clause | php-composer-installed-cataloger |
| debconf | 1.5.91 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2025.1 |  | dpkg-db-cataloger |
| debianutils | 5.23.2 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| dictionaries-common | 1.30.10 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| diffutils | 1:3.10-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dirmngr | 2.4.7-21+deb13u1+b3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| dpkg | 1.22.22 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dpkg-dev | 1.22.22 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| emacsen-common | 3.0.8 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| exif | 8.4.22 |  | php-interpreter-cataloger |
| file | 1:5.46-5 | BSD-2-Clause | dpkg-db-cataloger |
| findutils | 4.10.0-3 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| fontconfig-config | 2.15.0-2.3 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-8 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-dejavu-mono | 2.37-8 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| g++ | 4:14.2.0-1 | GPL-2.0-only | dpkg-db-cataloger |
| g++-14 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| g++-14-x86-64-linux-gnu | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| g++-x86-64-linux-gnu | 4:14.2.0-1 | GPL-2.0-only | dpkg-db-cataloger |
| gcc | 4:14.2.0-1 | GPL-2.0-only | dpkg-db-cataloger |
| gcc-14 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-14-base | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-14-x86-64-linux-gnu | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-x86-64-linux-gnu | 4:14.2.0-1 | GPL-2.0-only | dpkg-db-cataloger |
| gd | 8.4.22 |  | php-interpreter-cataloger |
| germancoding/tls_icon | 2.0.0 | MIT | php-composer-installed-cataloger |
| girepository-tools | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| gnupg | 2.4.7-21+deb13u1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-l10n | 2.4.7-21+deb13u1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg | 2.4.7-21+deb13u1+b3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.4.7-21+deb13u1+b3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.4.7-21+deb13u1+b3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.4.7-21+deb13u1+b3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.11-4 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| guzzlehttp/guzzle | 7.10.4 | MIT | php-composer-installed-cataloger |
| guzzlehttp/guzzle | 7.10.4 | MIT | php-composer-installed-cataloger |
| guzzlehttp/promises | 2.4.1 | MIT | php-composer-installed-cataloger |
| guzzlehttp/promises | 2.4.1 | MIT | php-composer-installed-cataloger |
| guzzlehttp/psr7 | 2.10.1 | MIT | php-composer-installed-cataloger |
| guzzlehttp/psr7 | 2.10.1 | MIT | php-composer-installed-cataloger |
| gzip | 1.13-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hostname | 3.25 | GPL-2.0-only | dpkg-db-cataloger |
| imagemagick-7-common | 8:7.1.1.43+dfsg1-1+deb13u10 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| init-system-helpers | 1.69~deb13u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| intl | 8.4.22 |  | php-interpreter-cataloger |
| johndoh/contextmenu | 3.3.1 | GPL-3.0-or-later | php-composer-installed-cataloger |
| kolab/net_ldap3 | v1.1.5 | GPL-3.0-or-later | php-composer-installed-cataloger |
| kolab/net_ldap3 | v1.1.5 | GPL-3.0-or-later | php-composer-installed-cataloger |
| ldap | 8.4.22 |  | php-interpreter-cataloger |
| libacl1 | 2.3.2-2+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapr1t64 | 1.7.5-1 | Apache-2.0 | dpkg-db-cataloger |
| libaprutil1-dbd-sqlite3 | 1.6.3-3+b1 | Apache-2.0 | dpkg-db-cataloger |
| libaprutil1-ldap | 1.6.3-3+b1 | Apache-2.0 | dpkg-db-cataloger |
| libaprutil1t64 | 1.6.3-3+b1 | Apache-2.0 | dpkg-db-cataloger |
| libapt-pkg7.0 | 3.0.3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, curl | dpkg-db-cataloger |
| libargon2-1 | 0~20190702+dfsg-4+b2 | Apache-2.0 | dpkg-db-cataloger |
| libasan8 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libaspell15 | 0.60.8.1-4 | GFDL-1.2-only, GFDL-1.2-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libassuan9 | 3.0.2-2 | FSFULLR, FSFULLRWD, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| libatomic1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libattr1 | 1:2.5.2-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:4.0.2-2 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:4.0.2-2+b2 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libbinutils | 2.44-3 |  | dpkg-db-cataloger |
| libblkid-dev | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libblkid1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libbrotli1 | 1.1.0-2+b7 | MIT | dpkg-db-cataloger |
| libbsd0 | 0.12.2-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-6 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.41-12+deb13u3 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libc-dev-bin | 2.41-12+deb13u3 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libc-l10n | 2.41-12+deb13u3 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libc6 | 2.41-12+deb13u3 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libc6-dev | 2.41-12+deb13u3 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libcap-ng0 | 0.8.5-4+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.75-10+deb13u1+b1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcc1-0 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libcom-err2 | 1.47.2-3+b11 | 0BSD, Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt-dev | 1:4.4.38-1 |  | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.38-1 |  | dpkg-db-cataloger |
| libctf-nobfd0 | 2.44-3 |  | dpkg-db-cataloger |
| libctf0 | 2.44-3 |  | dpkg-db-cataloger |
| libcurl4t64 | 8.14.1-2+deb13u3 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libdav1d7 | 1.5.1-1 | BSD-2-Clause, ISC | dpkg-db-cataloger |
| libdb5.3t64 | 5.3.28+dfsg2-9 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libde265-0 | 1.0.15-1+b3 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libdebconfclient0 | 0.280 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdeflate0 | 1.23-2 |  | dpkg-db-cataloger |
| libdpkg-perl | 1.22.22 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libelf1t64 | 0.192-4 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libexpat1 | 2.7.1-2 | MIT | dpkg-db-cataloger |
| libffi-dev | 3.4.8-2 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libffi8 | 3.4.8-2 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libfftw3-double3 | 3.3.10-2+b1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libfontconfig1 | 2.15.0-2.3 | HPND-sell-variant | dpkg-db-cataloger |
| libfreetype6 | 2.13.3+dfsg-1+deb13u1 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT-Modern-Variant, Zlib | dpkg-db-cataloger |
| libgcc-14-dev | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcc-s1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.11.0-7+deb13u1 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm-compat4t64 | 1.24-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6t64 | 1.24-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgio-2.0-dev | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgio-2.0-dev-bin | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgirepository-2.0-0 | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-0t64 | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-bin | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-data | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-dev | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-dev-bin | 2.84.4-3~deb13u3 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgmp10 | 2:6.3.0+dfsg-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30t64 | 3.8.9-3+deb13u4 | Apache-2.0, BSD-3-Clause, FSFAP, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.51-4 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgprofng0 | 2.44-3 |  | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.21.3-5+deb13u1 | GPL-2.0-only | dpkg-db-cataloger |
| libheif-plugin-dav1d | 1.19.8-1 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause-UC, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libheif-plugin-libde265 | 1.19.8-1 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause-UC, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libheif1 | 1.19.8-1 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause-UC, BSL-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libhogweed6t64 | 3.10.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libhwasan0 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libicu76 | 76.1-4 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn2-0 | 2.3.8-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libisl23 | 0.27-1 | BSD-2-Clause, LGPL-2.0-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libitm1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libjansson4 | 2.14-2+b3 |  | dpkg-db-cataloger |
| libjbig0 | 2.1-6.1+b2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libjpeg62-turbo | 1:2.1.5-4 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libk5crypto3 | 1.21.3-5+deb13u1 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-6 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.21.3-5+deb13u1 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.21.3-5+deb13u1 | GPL-2.0-only | dpkg-db-cataloger |
| libksba8 | 1.6.7-2+b1 | FSFUL, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblastlog2-2 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| liblcms2-2 | 2.16-2+deb13u2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| libldap2 | 2.6.10+dfsg-1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| liblerc4 | 4.0.0+ds-5 | Apache-2.0 | dpkg-db-cataloger |
| liblqr-1-0 | 0.4.2-2.1+b2 | GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| liblsan0 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libltdl7 | 2.5.4-4 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblua5.4-0 | 5.4.7-1+b2 |  | dpkg-db-cataloger |
| liblz4-1 | 1.10.0-4 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.8.1-1 | 0BSD, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmagic-mgc | 1:5.46-5 | BSD-2-Clause | dpkg-db-cataloger |
| libmagic1t64 | 1:5.46-5 | BSD-2-Clause | dpkg-db-cataloger |
| libmagickcore-7.q16-10 | 8:7.1.1.43+dfsg1-1+deb13u10 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-7.q16-10 | 8:7.1.1.43+dfsg1-1+deb13u10 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmd0 | 1.1.0-2+b1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount-dev | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmount1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmpc3 | 1.3.1-1+b3 | LGPL-3.0-only | dpkg-db-cataloger |
| libmpfr6 | 4.2.2-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libncursesw6 | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8t64 | 3.10.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.64.0-1.1+deb13u1 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnghttp3-9 | 1.8.0-1 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnpth0t64 | 1.8-3 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libonig5 | 6.9.9-1+b1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.3-2.1~deb13u2 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libp11-kit0 | 0.25.5-3 | Apache-2.0, BSD-3-Clause, FSFAP, FSFULLR, GPL-2.0-or-later, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, X11 | dpkg-db-cataloger |
| libpam-modules | 1.7.0-5 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.7.0-5 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.7.0-5 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.7.0-5 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-16-0 | 10.46-1~deb13u1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-32-0 | 10.46-1~deb13u1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-8-0 | 10.46-1~deb13u1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-dev | 10.46-1~deb13u1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-posix3 | 10.46-1~deb13u1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libperl5.40 | 5.40.1-6 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| libphp | 8.4.22 |  | php-interpreter-cataloger |
| libpkgconf3 | 1.8.1-4 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| libpng16-16t64 | 1.6.48-1+deb13u5 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpopt0 | 1.19+dfsg-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libpq5 | 17.10-0+deb13u1 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.4-9 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpsl5t64 | 0.21.2-1.1+b1 | MIT | dpkg-db-cataloger |
| libpython3-stdlib | 3.13.5-1 |  | dpkg-db-cataloger |
| libpython3.13-minimal | 3.13.5-2+deb13u2 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.13-stdlib | 3.13.5-2+deb13u2 | GPL-2.0-only | dpkg-db-cataloger |
| libquadmath0 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libraw23t64 | 0.21.4-2 | CC-BY-SA-3.0, CDDL-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libreadline8t64 | 8.2-6 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| librtmp1 | 2.4+20151223.gitfa8646d.1-2+b5 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsasl2-2 | 2.1.28+dfsg1-9 | BSD-2-Clause, BSD-3-Clause-Attribution, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.28+dfsg1-9 | BSD-2-Clause, BSD-3-Clause-Attribution, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, RSA-MD | dpkg-db-cataloger |
| libseccomp2 | 2.6.0-2 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.8.1-1 | GPL-2.0-only | dpkg-db-cataloger |
| libselinux1-dev | 3.8.1-1 | GPL-2.0-only | dpkg-db-cataloger |
| libsemanage-common | 3.8.1-1 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsemanage2 | 3.8.1-1 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsepol-dev | 3.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsepol2 | 3.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsframe1 | 2.44-3 |  | dpkg-db-cataloger |
| libsharpyuv0 | 1.5.0-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libsmartcols1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libsodium23 | 1.0.18-1+deb13u1 | BSD-2-Clause, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.46.1-7+deb13u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libssh2-1t64 | 1.11.1-1+deb13u1 | ISC | dpkg-db-cataloger |
| libssl3t64 | 3.5.6-1~deb13u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++-14-dev | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libstdc++6 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libsysprof-capture-4-dev | 48.0-2 | BSD-2-Clause-Patent, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libsystemd0 | 257.13-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.20.0-2 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtext-iconv-perl | 1.7-8+b4 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libtiff6 | 4.7.0-3+deb13u2 |  | dpkg-db-cataloger |
| libtinfo6 | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtsan2 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libubsan1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libudev1 | 257.13-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring5 | 1.3-2 | BSD-3-Clause, GFDL-1.2-or-later, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, X11, BSD-3-Clause, GFDL-1.2-or-later, GFDL-1.3-or-later, ISC, Unicode-DFS-2016 | dpkg-db-cataloger |
| libuuid1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libwebp7 | 1.5.0-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libwebpdemux2 | 1.5.0-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libwebpmux3 | 1.5.0-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libx11-6 | 2:1.8.12-1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.8.12-1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxau6 | 1:1.0.11-1 |  | dpkg-db-cataloger |
| libxcb1 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.5-1 |  | dpkg-db-cataloger |
| libxext6 | 2:1.3.4-1+b3 |  | dpkg-db-cataloger |
| libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u2 | ISC | dpkg-db-cataloger |
| libxxhash0 | 0.8.3-2 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libzip5 | 1.11.3-2 | Apache-2.0, BSD-3-Clause, GPL-3.0-only | dpkg-db-cataloger |
| libzstd1 | 1.5.7+dfsg-1 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| linux-libc-dev | 6.12.94-1 | BSD-2-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| locales | 2.41-12+deb13u3 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| login | 1:4.16.0-2+really2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| login.defs | 1:4.17.4-2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| m4 | 1.4.19-8 |  | dpkg-db-cataloger |
| make | 4.4.1-2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| masterminds/html5 | 2.7.6 | MIT | php-composer-installed-cataloger |
| masterminds/html5 | 2.7.6 | MIT | php-composer-installed-cataloger |
| mawk | 1.3.4.20250131-1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 13.0.0 |  | dpkg-db-cataloger |
| mlocati/ip-lib | 1.22.0 | MIT | php-composer-installed-cataloger |
| mlocati/ip-lib | 1.22.0 | MIT | php-composer-installed-cataloger |
| mount | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| native-architecture | 0.2.6 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| ncurses-base | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.5 | GPL-2.0-only | dpkg-db-cataloger |
| opcache | 8.4.22 |  | php-interpreter-cataloger |
| openssl | 3.5.6-1~deb13u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| openssl-provider-legacy | 3.5.6-1~deb13u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| packaging | 25.0 |  | python-installed-package-cataloger |
| passwd | 1:4.17.4-2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.8-2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| pdo_mysql | 8.4.22 |  | php-interpreter-cataloger |
| pdo_pgsql | 8.4.22 |  | php-interpreter-cataloger |
| pdo_sqlite | 8.4.22 |  | php-interpreter-cataloger |
| pear/auth_sasl | v1.1.0 |  | php-composer-installed-cataloger |
| pear/auth_sasl | v1.1.0 |  | php-composer-installed-cataloger |
| pear/console_commandline | v1.2.6 | MIT | php-composer-installed-cataloger |
| pear/console_commandline | v1.2.6 | MIT | php-composer-installed-cataloger |
| pear/console_getopt | v1.4.3 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/console_getopt | v1.4.3 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/crypt_gpg | v1.6.11 | LGPL-2.1-only | php-composer-installed-cataloger |
| pear/crypt_gpg | v1.6.11 | LGPL-2.1-only | php-composer-installed-cataloger |
| pear/mail_mime | 1.10.12 | BSD-3-Clause | php-composer-installed-cataloger |
| pear/mail_mime | 1.10.12 | BSD-3-Clause | php-composer-installed-cataloger |
| pear/net_ldap2 | v2.3.0 | LGPL-3.0-only | php-composer-installed-cataloger |
| pear/net_ldap2 | v2.3.0 | LGPL-3.0-only | php-composer-installed-cataloger |
| pear/net_sieve | 1.4.8 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/net_sieve | 1.4.8 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/net_smtp | 1.10.1 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/net_smtp | 1.10.1 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/net_socket | v1.2.2 |  | php-composer-installed-cataloger |
| pear/net_socket | v1.2.2 |  | php-composer-installed-cataloger |
| pear/pear-core-minimal | v1.10.18 | BSD-3-Clause | php-composer-installed-cataloger |
| pear/pear-core-minimal | v1.10.18 | BSD-3-Clause | php-composer-installed-cataloger |
| pear/pear_exception | v1.0.2 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/pear_exception | v1.0.2 | BSD-2-Clause | php-composer-installed-cataloger |
| perl | 5.40.1-6 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-base | 5.40.1-6 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-modules-5.40 | 5.40.1-6 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| php-cli | 8.4.22 |  | php-interpreter-cataloger |
| pinentry-curses | 1.3.1-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| pkg-config | 1.8.1-4 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| pkgconf | 1.8.1-4 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| pkgconf-bin | 1.8.1-4 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| procps | 2:4.0.4-9 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| psr/http-client | 1.0.3 | MIT | php-composer-installed-cataloger |
| psr/http-client | 1.0.3 | MIT | php-composer-installed-cataloger |
| psr/http-factory | 1.1.0 | MIT | php-composer-installed-cataloger |
| psr/http-factory | 1.1.0 | MIT | php-composer-installed-cataloger |
| psr/http-message | 2.0 | MIT | php-composer-installed-cataloger |
| psr/http-message | 2.0 | MIT | php-composer-installed-cataloger |
| python3 | 3.13.5-1 |  | dpkg-db-cataloger |
| python3-minimal | 3.13.5-1 |  | dpkg-db-cataloger |
| python3-packaging | 25.0-1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| python3.13 | 3.13.5-2+deb13u2 | GPL-2.0-only | dpkg-db-cataloger |
| python3.13-minimal | 3.13.5-2+deb13u2 | GPL-2.0-only | dpkg-db-cataloger |
| ralouphie/getallheaders | 3.0.3 | MIT | php-composer-installed-cataloger |
| ralouphie/getallheaders | 3.0.3 | MIT | php-composer-installed-cataloger |
| re2c | 4.1-1 | Apache-2.0, Apache-2.0, PHP-3.01 | dpkg-db-cataloger |
| readline-common | 8.2-6 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| roundcube/plugin-installer | 0.3.11 | GPL-3.0-or-later | php-composer-installed-cataloger |
| roundcube/plugin-installer | 0.3.11 | GPL-3.0-or-later | php-composer-installed-cataloger |
| roundcube/rtf-html-php | v2.2 | GPL-2.0-only | php-composer-installed-cataloger |
| roundcube/rtf-html-php | v2.2 | GPL-2.0-only | php-composer-installed-cataloger |
| rpcsvc-proto | 1.4.3-1 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, MIT | dpkg-db-cataloger |
| rsync | 3.4.1+ds1-5+deb13u3 | FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, PostgreSQL, snprintf | dpkg-db-cataloger |
| sed | 4.9-2+deb13u1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sodium | 8.4.22 |  | php-interpreter-cataloger |
| sqv | 1.3.0-3+b2 | LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| symfony/deprecation-contracts | v2.5.4 | MIT | php-composer-installed-cataloger |
| symfony/deprecation-contracts | v2.5.4 | MIT | php-composer-installed-cataloger |
| sysvinit-utils | 3.14-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| tar | 1.35+dfsg-3.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tzdata | 2026b-0+deb13u1 |  | dpkg-db-cataloger |
| unzip | 6.0-29 |  | dpkg-db-cataloger |
| util-linux | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| uuid-dev | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| xz-utils | 5.8.1-1 | 0BSD, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| zip | 1.22.8 |  | php-interpreter-cataloger |
| zlib1g | 1:1.3.dfsg+really1.3.1-1+b1 | Zlib | dpkg-db-cataloger |
| zlib1g-dev | 1:1.3.dfsg+really1.3.1-1+b1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/seaweedfs

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.6-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.23.4-r0 | MIT | apk-db-cataloger |
| apk-tools | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| atomicgo.dev/cursor | v0.2.0 |  | go-module-binary-cataloger |
| atomicgo.dev/keyboard | v0.2.9 |  | go-module-binary-cataloger |
| atomicgo.dev/schedule | v0.1.0 |  | go-module-binary-cataloger |
| brotli-libs | 1.2.0-r0 | MIT | apk-db-cataloger |
| busybox | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| c-ares | 1.34.6-r0 | MIT | apk-db-cataloger |
| ca-certificates-bundle | 20260413-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| cel.dev/expr | v0.25.1 |  | go-module-binary-cataloger |
| cloud.google.com/go | v0.123.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth | v0.18.2 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.8 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.9.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/iam | v1.5.3 |  | go-module-binary-cataloger |
| cloud.google.com/go/kms | v1.26.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/longrunning | v0.8.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/monitoring | v1.24.3 |  | go-module-binary-cataloger |
| cloud.google.com/go/pubsub | v1.50.2 |  | go-module-binary-cataloger |
| cloud.google.com/go/pubsub/v2 | v2.4.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/storage | v1.60.0 |  | go-module-binary-cataloger |
| curl | 8.17.0-r1 | curl | apk-db-cataloger |
| filippo.io/edwards25519 | v1.1.1 |  | go-module-binary-cataloger |
| fuse | 2.9.9-r7 | GPL-2.0-only AND LGPL-2.1-only | apk-db-cataloger |
| fuse-common | 3.17.3-r1 | GPL-2.0-only AND LGPL-2.1-only | apk-db-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.21.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.13.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.11.2 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/storage/azblob | v1.6.4 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/storage/azfile | v1.5.3 |  | go-module-binary-cataloger |
| github.com/Azure/go-ntlmssp | v0.1.1 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.6.0 |  | go-module-binary-cataloger |
| github.com/FilenCloudDienste/filen-sdk-go | v0.0.38 |  | go-module-binary-cataloger |
| github.com/Files-com/files-sdk-go/v3 | v3.2.264 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/detectors/gcp | v1.30.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/exporter/metric | v0.55.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/internal/resourcemapping | v0.55.0 |  | go-module-binary-cataloger |
| github.com/IBM/go-sdk-core/v5 | v5.21.0 |  | go-module-binary-cataloger |
| github.com/Jille/raft-grpc-transport | v1.6.1 |  | go-module-binary-cataloger |
| github.com/Max-Sum/base32768 | v0.0.0-20230304063302-18e6ce5945fd |  | go-module-binary-cataloger |
| github.com/ProtonMail/bcrypt | v0.0.0-20211005172633-e235017c1baf |  | go-module-binary-cataloger |
| github.com/ProtonMail/gluon | v0.17.1-0.20230724134000-308be39be96e |  | go-module-binary-cataloger |
| github.com/ProtonMail/go-crypto | v1.3.0 |  | go-module-binary-cataloger |
| github.com/ProtonMail/go-mime | v0.0.0-20230322103455-7d82a3887f2f |  | go-module-binary-cataloger |
| github.com/ProtonMail/go-srp | v0.0.7 |  | go-module-binary-cataloger |
| github.com/ProtonMail/gopenpgp/v2 | v2.9.0 |  | go-module-binary-cataloger |
| github.com/PuerkitoBio/goquery | v1.10.3 |  | go-module-binary-cataloger |
| github.com/Shopify/sarama | v1.38.1 |  | go-module-binary-cataloger |
| github.com/ThreeDotsLabs/watermill | v1.5.1 |  | go-module-binary-cataloger |
| github.com/a-h/templ | v0.3.977 |  | go-module-binary-cataloger |
| github.com/a1ex3/zstd-seekable-format-go/pkg | v0.10.0 |  | go-module-binary-cataloger |
| github.com/abbot/go-http-auth | v0.4.0 |  | go-module-binary-cataloger |
| github.com/anchore/go-lzo | v0.1.0 |  | go-module-binary-cataloger |
| github.com/andybalholm/brotli | v1.2.0 |  | go-module-binary-cataloger |
| github.com/andybalholm/cascadia | v1.3.3 |  | go-module-binary-cataloger |
| github.com/antlr4-go/antlr/v4 | v4.13.1 |  | go-module-binary-cataloger |
| github.com/apache/arrow-go/v18 | v18.5.2-0.20260220015023-a886a5722b87 |  | go-module-binary-cataloger |
| github.com/apache/cassandra-gocql-driver/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/apache/iceberg-go | v0.5.0 |  | go-module-binary-cataloger |
| github.com/apache/thrift | v0.22.0 |  | go-module-binary-cataloger |
| github.com/appscode/go-querystring | v0.0.0-20170504095604-0126cfb3f1dc |  | go-module-binary-cataloger |
| github.com/arangodb/go-driver | v1.6.9 |  | go-module-binary-cataloger |
| github.com/arangodb/go-velocypack | v0.0.0-20200318135517-5af53c29c67e |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go | v1.55.8 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.41.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/aws/protocol/eventstream | v1.7.8 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.32.14 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.19.14 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.18.21 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/s3/manager | v1.22.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.4.21 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.7.21 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/ini | v1.8.6 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/v4a | v1.4.22 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.13.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/checksum | v1.9.13 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.13.21 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/s3shared | v1.19.21 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/s3 | v1.99.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/signin | v1.0.9 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sns | v1.39.7 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sqs | v1.42.17 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.30.15 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.35.19 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.41.10 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.25.0 |  | go-module-binary-cataloger |
| github.com/bahlo/generic-list-go | v0.2.0 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/boltdb/bolt | v1.3.1 |  | go-module-binary-cataloger |
| github.com/boombuler/barcode | v1.1.0 |  | go-module-binary-cataloger |
| github.com/bradenaw/juniper | v0.15.3 |  | go-module-binary-cataloger |
| github.com/bradfitz/iter | v0.0.0-20191230175014-e8f45d346db8 |  | go-module-binary-cataloger |
| github.com/buengese/sgzip | v0.1.1 |  | go-module-binary-cataloger |
| github.com/buger/jsonparser | v1.1.2 |  | go-module-binary-cataloger |
| github.com/bwmarrin/snowflake | v0.3.0 |  | go-module-binary-cataloger |
| github.com/calebcase/tmpfile | v1.0.3 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/chilts/sid | v0.0.0-20190607042430-660e94789ec9 |  | go-module-binary-cataloger |
| github.com/clipperhouse/stringish | v0.1.1 |  | go-module-binary-cataloger |
| github.com/clipperhouse/uax29/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cloudflare/circl | v1.6.3 |  | go-module-binary-cataloger |
| github.com/cloudinary/cloudinary-go/v2 | v2.13.0 |  | go-module-binary-cataloger |
| github.com/cloudsoda/go-smb2 | v0.0.0-20250228001242-d4c70e6251cc |  | go-module-binary-cataloger |
| github.com/cloudsoda/sddl | v0.0.0-20250224235906-926454e91efc |  | go-module-binary-cataloger |
| github.com/cncf/xds/go | v0.0.0-20251210132809-ee656c7534f5 |  | go-module-binary-cataloger |
| github.com/cockroachdb/apd/v3 | v3.2.1 |  | go-module-binary-cataloger |
| github.com/cognusion/imaging | v1.0.2 |  | go-module-binary-cataloger |
| github.com/colinmarc/hdfs/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/containerd/console | v1.0.5 |  | go-module-binary-cataloger |
| github.com/coreos/go-semver | v0.3.1 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.6.0 |  | go-module-binary-cataloger |
| github.com/creasty/defaults | v1.8.0 |  | go-module-binary-cataloger |
| github.com/cronokirby/saferith | v0.33.0 |  | go-module-binary-cataloger |
| github.com/cznic/mathutil | v0.0.0-20181122101859-297441e03548 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/dgryski/go-farm | v0.0.0-20200201041132-a6ae2369ad13 |  | go-module-binary-cataloger |
| github.com/dgryski/go-rendezvous | v0.0.0-20200823014737-9f7001d12a5f |  | go-module-binary-cataloger |
| github.com/diskfs/go-diskfs | v1.7.0 |  | go-module-binary-cataloger |
| github.com/dromara/dongle | v1.0.1 |  | go-module-binary-cataloger |
| github.com/dropbox/dropbox-sdk-go-unofficial/v6 | v6.0.5 |  | go-module-binary-cataloger |
| github.com/dustin/go-humanize | v1.0.1 |  | go-module-binary-cataloger |
| github.com/eapache/go-resiliency | v1.6.0 |  | go-module-binary-cataloger |
| github.com/eapache/go-xerial-snappy | v0.0.0-20230731223053-c322873962e3 |  | go-module-binary-cataloger |
| github.com/eapache/queue | v1.1.0 |  | go-module-binary-cataloger |
| github.com/elastic/gosigar | v0.14.3 |  | go-module-binary-cataloger |
| github.com/emersion/go-message | v0.18.2 |  | go-module-binary-cataloger |
| github.com/emersion/go-vcard | v0.0.0-20241024213814-c9703dde27ff |  | go-module-binary-cataloger |
| github.com/envoyproxy/go-control-plane/envoy | v1.36.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/protoc-gen-validate | v1.3.0 |  | go-module-binary-cataloger |
| github.com/facebookgo/clock | v0.0.0-20150410010913-600d898af40a |  | go-module-binary-cataloger |
| github.com/facebookgo/stats | v0.0.0-20151006221625-1b76add642e4 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fluent/fluent-logger-golang | v1.10.1 |  | go-module-binary-cataloger |
| github.com/flynn/noise | v1.1.0 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/gabriel-vasile/mimetype | v1.4.11 |  | go-module-binary-cataloger |
| github.com/geoffgarside/ber | v1.2.0 |  | go-module-binary-cataloger |
| github.com/getsentry/sentry-go | v0.44.1 |  | go-module-binary-cataloger |
| github.com/go-asn1-ber/asn1-ber | v1.5.8-0.20250403174932-29230038a667 |  | go-module-binary-cataloger |
| github.com/go-chi/chi/v5 | v5.2.5 |  | go-module-binary-cataloger |
| github.com/go-git/go-billy/v5 | v5.8.0 |  | go-module-binary-cataloger |
| github.com/go-jose/go-jose/v4 | v4.1.4 |  | go-module-binary-cataloger |
| github.com/go-ldap/ldap/v3 | v3.4.13 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/errors | v0.22.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/strfmt | v0.25.0 |  | go-module-binary-cataloger |
| github.com/go-playground/locales | v0.14.1 |  | go-module-binary-cataloger |
| github.com/go-playground/universal-translator | v0.18.1 |  | go-module-binary-cataloger |
| github.com/go-playground/validator/v10 | v10.28.0 |  | go-module-binary-cataloger |
| github.com/go-redsync/redsync/v4 | v4.16.0 |  | go-module-binary-cataloger |
| github.com/go-resty/resty/v2 | v2.16.5 |  | go-module-binary-cataloger |
| github.com/go-sql-driver/mysql | v1.9.3 |  | go-module-binary-cataloger |
| github.com/go-viper/mapstructure/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/go-zookeeper/zk | v1.0.4 |  | go-module-binary-cataloger |
| github.com/goccy/go-json | v0.10.5 |  | go-module-binary-cataloger |
| github.com/goccy/go-yaml | v1.18.0 |  | go-module-binary-cataloger |
| github.com/gofrs/flock | v0.13.0 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v4 | v4.5.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.3.1 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v1.0.0 |  | go-module-binary-cataloger |
| github.com/google/btree | v1.1.3 |  | go-module-binary-cataloger |
| github.com/google/flatbuffers/go | v0.0.0-20230108230133-3b8644d32c50 |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.9 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/wire | v0.7.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.14 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.19.0 |  | go-module-binary-cataloger |
| github.com/gookit/color | v1.5.4 |  | go-module-binary-cataloger |
| github.com/gorilla/mux | v1.8.1 |  | go-module-binary-cataloger |
| github.com/gorilla/schema | v1.4.1 |  | go-module-binary-cataloger |
| github.com/gorilla/securecookie | v1.1.2 |  | go-module-binary-cataloger |
| github.com/gorilla/sessions | v1.4.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware | v1.4.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.27.3 |  | go-module-binary-cataloger |
| github.com/hamba/avro/v2 | v2.31.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-immutable-radix | v1.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-metrics | v0.5.4 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-msgpack/v2 | v2.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.8 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-secure-stdlib/parseutil | v0.2.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-secure-stdlib/strutil | v0.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-sockaddr | v1.0.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-uuid | v1.0.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v0.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/hcl | v1.0.1-vault-7 |  | go-module-binary-cataloger |
| github.com/hashicorp/raft | v1.7.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/raft-boltdb/v2 | v2.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/vault/api | v1.23.0 |  | go-module-binary-cataloger |
| github.com/internxt/rclone-adapter | v0.0.0-20260220172730-613f4cc8b8fd |  | go-module-binary-cataloger |
| github.com/jackc/pgpassfile | v1.0.0 |  | go-module-binary-cataloger |
| github.com/jackc/pgservicefile | v0.0.0-20240606120523-5a60cdf6a761 |  | go-module-binary-cataloger |
| github.com/jackc/pgx/v5 | v5.9.2 |  | go-module-binary-cataloger |
| github.com/jackc/puddle/v2 | v2.2.2 |  | go-module-binary-cataloger |
| github.com/jcmturner/aescts/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/dnsutils/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/gofork | v1.7.6 |  | go-module-binary-cataloger |
| github.com/jcmturner/goidentity/v6 | v6.0.1 |  | go-module-binary-cataloger |
| github.com/jcmturner/gokrb5/v8 | v8.4.4 |  | go-module-binary-cataloger |
| github.com/jcmturner/rpc/v2 | v2.0.3 |  | go-module-binary-cataloger |
| github.com/jhump/protoreflect | v1.18.0 |  | go-module-binary-cataloger |
| github.com/jhump/protoreflect/v2 | v2.0.0-beta.1 |  | go-module-binary-cataloger |
| github.com/jlaffaye/ftp | v0.2.1-0.20240918233326-1b970516f5d3 |  | go-module-binary-cataloger |
| github.com/jmespath/go-jmespath | v0.4.0 |  | go-module-binary-cataloger |
| github.com/jonboulle/clockwork | v0.5.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/jtolio/noiseconn | v0.0.0-20231127013910-f6d9ecbf1de7 |  | go-module-binary-cataloger |
| github.com/jzelinskie/whirlpool | v0.0.0-20201016144138-0675e54bb004 |  | go-module-binary-cataloger |
| github.com/karlseguin/ccache/v2 | v2.0.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.5 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/klauspost/reedsolomon | v1.13.3 |  | go-module-binary-cataloger |
| github.com/koofr/go-httpclient | v0.0.0-20240520111329-e20f8f203988 |  | go-module-binary-cataloger |
| github.com/koofr/go-koofrclient | v0.0.0-20221207135200-cbd7fc9ad6a6 |  | go-module-binary-cataloger |
| github.com/kr/fs | v0.1.0 |  | go-module-binary-cataloger |
| github.com/kurin/blazer | v0.5.3 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/lanrat/extsort | v1.4.2 |  | go-module-binary-cataloger |
| github.com/leodido/go-urn | v1.4.0 |  | go-module-binary-cataloger |
| github.com/linkedin/goavro/v2 | v2.15.0 |  | go-module-binary-cataloger |
| github.com/lithammer/fuzzysearch | v1.1.8 |  | go-module-binary-cataloger |
| github.com/lithammer/shortuuid/v3 | v3.0.7 |  | go-module-binary-cataloger |
| github.com/lpar/date | v1.0.0 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.9.1 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.19 |  | go-module-binary-cataloger |
| github.com/minio/crc64nvme | v1.1.1 |  | go-module-binary-cataloger |
| github.com/mitchellh/colorstring | v0.0.0-20190213212951-d06e56a500db |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.1-0.20220423185008-bf980b35cac4 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/nats-io/nats.go | v1.48.0 |  | go-module-binary-cataloger |
| github.com/nats-io/nkeys | v0.4.12 |  | go-module-binary-cataloger |
| github.com/nats-io/nuid | v1.0.1 |  | go-module-binary-cataloger |
| github.com/ncw/swift/v2 | v2.0.5 |  | go-module-binary-cataloger |
| github.com/oklog/ulid | v1.3.1 |  | go-module-binary-cataloger |
| github.com/olivere/elastic/v7 | v7.0.32 |  | go-module-binary-cataloger |
| github.com/opentracing/opentracing-go | v1.2.0 |  | go-module-binary-cataloger |
| github.com/oracle/oci-go-sdk/v65 | v65.104.0 |  | go-module-binary-cataloger |
| github.com/orcaman/concurrent-map/v2 | v2.0.1 |  | go-module-binary-cataloger |
| github.com/panjf2000/ants/v2 | v2.11.3 |  | go-module-binary-cataloger |
| github.com/parquet-go/bitpack | v1.0.0 |  | go-module-binary-cataloger |
| github.com/parquet-go/jsonlite | v1.0.0 |  | go-module-binary-cataloger |
| github.com/parquet-go/parquet-go | v0.28.0 |  | go-module-binary-cataloger |
| github.com/patrickmn/go-cache | v2.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/pelletier/go-toml/v2 | v2.2.4 |  | go-module-binary-cataloger |
| github.com/pengsrc/go-shared | v0.2.1-0.20190131101655-1999055a4a14 |  | go-module-binary-cataloger |
| github.com/peterh/liner | v1.2.2 |  | go-module-binary-cataloger |
| github.com/philhofer/fwd | v1.2.0 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.26 |  | go-module-binary-cataloger |
| github.com/pingcap/errors | v0.11.5-0.20211224045212-9687c2b0f87c |  | go-module-binary-cataloger |
| github.com/pingcap/failpoint | v0.0.0-20220801062533-2eaa32854a6c |  | go-module-binary-cataloger |
| github.com/pingcap/kvproto | v0.0.0-20230403051650-e166ae588106 |  | go-module-binary-cataloger |
| github.com/pingcap/log | v1.1.1-0.20221110025148-ca232912c9f3 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/sftp | v1.13.10 |  | go-module-binary-cataloger |
| github.com/pkg/xattr | v0.4.12 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/posener/complete | v1.2.3 |  | go-module-binary-cataloger |
| github.com/pquerna/cachecontrol | v0.2.0 |  | go-module-binary-cataloger |
| github.com/pquerna/otp | v1.5.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.2 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.20.1 |  | go-module-binary-cataloger |
| github.com/pterm/pterm | v0.12.82 |  | go-module-binary-cataloger |
| github.com/putdotio/go-putio/putio | v0.0.0-20200123120452-16d982cac2b8 |  | go-module-binary-cataloger |
| github.com/rabbitmq/amqp091-go | v1.10.0 |  | go-module-binary-cataloger |
| github.com/rasky/go-xdr | v0.0.0-20170124162913-1a41d1a06c93 |  | go-module-binary-cataloger |
| github.com/rclone/Proton-API-Bridge | v1.0.1-0.20260127174007-77f974840d11 |  | go-module-binary-cataloger |
| github.com/rclone/go-proton-api | v1.0.1-0.20260127173028-eb465cac3b18 |  | go-module-binary-cataloger |
| github.com/rclone/rclone | v1.73.5 |  | go-module-binary-cataloger |
| github.com/rcrowley/go-metrics | v0.0.0-20201227073835-cf1acfcdf475 |  | go-module-binary-cataloger |
| github.com/rdleal/intervalst | v1.5.0 |  | go-module-binary-cataloger |
| github.com/redis/go-redis/v9 | v9.18.0 |  | go-module-binary-cataloger |
| github.com/relvacode/iso8601 | v1.7.0 |  | go-module-binary-cataloger |
| github.com/remyoudompheng/bigfft | v0.0.0-20230129092748-24d4a6f8daec |  | go-module-binary-cataloger |
| github.com/rfjakob/eme | v1.1.2 |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.4.7 |  | go-module-binary-cataloger |
| github.com/ryanuber/go-glob | v1.0.0 |  | go-module-binary-cataloger |
| github.com/sabhiram/go-gitignore | v0.0.0-20210923224102-525f6e181f06 |  | go-module-binary-cataloger |
| github.com/sagikazarmark/locafero | v0.11.0 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.52.0 |  | go-module-binary-cataloger |
| github.com/schollz/progressbar/v3 | v3.19.0 |  | go-module-binary-cataloger |
| github.com/seaweedfs/go-fuse/v2 | v2.9.3 |  | go-module-binary-cataloger |
| github.com/seaweedfs/goexif | v1.0.3 |  | go-module-binary-cataloger |
| github.com/seaweedfs/raft | v1.1.8 |  | go-module-binary-cataloger |
| github.com/seaweedfs/seaweedfs | v0.0.0-20260504061534-73fc9e3833cf |  | go-module-binary-cataloger |
| github.com/shirou/gopsutil/v4 | v4.26.2 |  | go-module-binary-cataloger |
| github.com/sirupsen/logrus | v1.9.4-0.20230606125235-dd1b4c2e81af |  | go-module-binary-cataloger |
| github.com/skratchdot/open-golang | v0.0.0-20200116055534-eef842397966 |  | go-module-binary-cataloger |
| github.com/sony/gobreaker | v1.0.0 |  | go-module-binary-cataloger |
| github.com/sourcegraph/conc | v0.3.1-0.20240121214520-5f936abd7ae8 |  | go-module-binary-cataloger |
| github.com/spacemonkeygo/monkit/v3 | v3.0.25-0.20251022131615-eb24eb109368 |  | go-module-binary-cataloger |
| github.com/spf13/afero | v1.15.0 |  | go-module-binary-cataloger |
| github.com/spf13/cast | v1.10.0 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/spf13/viper | v1.21.0 |  | go-module-binary-cataloger |
| github.com/spiffe/go-spiffe/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/stretchr/objx | v0.5.2 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.11.1 |  | go-module-binary-cataloger |
| github.com/subosito/gotenv | v1.6.0 |  | go-module-binary-cataloger |
| github.com/substrait-io/substrait | v0.81.0 |  | go-module-binary-cataloger |
| github.com/substrait-io/substrait-go/v7 | v7.4.0 |  | go-module-binary-cataloger |
| github.com/substrait-io/substrait-protobuf/go | v0.81.0 |  | go-module-binary-cataloger |
| github.com/syndtr/goleveldb | v1.0.1-0.20190318030020-c3a204f8e965 |  | go-module-binary-cataloger |
| github.com/t3rm1n4l/go-mega | v0.0.0-20251031123324-a804aaa87491 |  | go-module-binary-cataloger |
| github.com/tarantool/go-iproto | v1.1.0 |  | go-module-binary-cataloger |
| github.com/tarantool/go-tarantool/v2 | v2.4.2 |  | go-module-binary-cataloger |
| github.com/tiancaiamao/gp | v0.0.0-20221230034425-4025bc8a4d4a |  | go-module-binary-cataloger |
| github.com/tidwall/gjson | v1.18.0 |  | go-module-binary-cataloger |
| github.com/tidwall/match | v1.2.0 |  | go-module-binary-cataloger |
| github.com/tidwall/pretty | v1.2.0 |  | go-module-binary-cataloger |
| github.com/tikv/client-go/v2 | v2.0.7 |  | go-module-binary-cataloger |
| github.com/tikv/pd/client | v0.0.0-20230329114254-1948c247c2b1 |  | go-module-binary-cataloger |
| github.com/tinylib/msgp | v1.5.0 |  | go-module-binary-cataloger |
| github.com/tklauser/go-sysconf | v0.3.16 |  | go-module-binary-cataloger |
| github.com/tklauser/numcpus | v0.11.0 |  | go-module-binary-cataloger |
| github.com/tsuna/gohbase | v0.0.0-20201125011725-348991136365 |  | go-module-binary-cataloger |
| github.com/twmb/murmur3 | v1.1.8 |  | go-module-binary-cataloger |
| github.com/twpayne/go-geom | v1.6.1 |  | go-module-binary-cataloger |
| github.com/tyler-smith/go-bip39 | v1.1.0 |  | go-module-binary-cataloger |
| github.com/tylertreat/BoomFilters | v0.0.0-20210315201527-1a82519a3e43 |  | go-module-binary-cataloger |
| github.com/ulikunitz/xz | v0.5.15 |  | go-module-binary-cataloger |
| github.com/unknwon/goconfig | v1.0.0 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/viant/ptrie | v1.0.1 |  | go-module-binary-cataloger |
| github.com/vmihailenco/msgpack/v5 | v5.4.1 |  | go-module-binary-cataloger |
| github.com/vmihailenco/tagparser/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/willscott/go-nfs | v0.0.3 |  | go-module-binary-cataloger |
| github.com/willscott/go-nfs-client | v0.0.0-20251022144359-801f10d98886 |  | go-module-binary-cataloger |
| github.com/wk8/go-ordered-map/v2 | v2.1.8 |  | go-module-binary-cataloger |
| github.com/xanzy/ssh-agent | v0.3.3 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.2.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xeipuuv/gojsonpointer | v0.0.0-20190905194746-02993c407bfb |  | go-module-binary-cataloger |
| github.com/xeipuuv/gojsonreference | v0.0.0-20180127040603-bd5ef7bd5415 |  | go-module-binary-cataloger |
| github.com/xeipuuv/gojsonschema | v1.2.0 |  | go-module-binary-cataloger |
| github.com/xo/terminfo | v0.0.0-20220910002029-abceb7e1c41e |  | go-module-binary-cataloger |
| github.com/yandex-cloud/go-genproto | v0.0.0-20211115083454-9ca41db5ed9e |  | go-module-binary-cataloger |
| github.com/ydb-platform/ydb-go-genproto | v0.0.0-20260311095541-ebbf792c1180 |  | go-module-binary-cataloger |
| github.com/ydb-platform/ydb-go-sdk-auth-environ | v0.5.1 |  | go-module-binary-cataloger |
| github.com/ydb-platform/ydb-go-sdk/v3 | v3.134.2 |  | go-module-binary-cataloger |
| github.com/ydb-platform/ydb-go-yc | v0.12.1 |  | go-module-binary-cataloger |
| github.com/ydb-platform/ydb-go-yc-metadata | v0.6.1 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/yunify/qingstor-sdk-go/v3 | v3.2.0 |  | go-module-binary-cataloger |
| github.com/zeebo/blake3 | v0.2.4 |  | go-module-binary-cataloger |
| github.com/zeebo/errs | v1.4.0 |  | go-module-binary-cataloger |
| github.com/zeebo/xxh3 | v1.1.0 |  | go-module-binary-cataloger |
| go.etcd.io/bbolt | v1.4.3 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/api/v3 | v3.6.10 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.6.10 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.6.10 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.9 |  | go-module-binary-cataloger |
| go.opencensus.io | v0.24.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/detectors/gcp | v1.39.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc | v0.63.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.63.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/metric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.43.0 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.27.1 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.3 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| gocloud.dev | v0.45.0 |  | go-module-binary-cataloger |
| gocloud.dev/pubsub/natspubsub | v0.45.0 |  | go-module-binary-cataloger |
| gocloud.dev/pubsub/rabbitpubsub | v0.45.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.50.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20260218203240-3dfff04db8fa |  | go-module-binary-cataloger |
| golang.org/x/image | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.53.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.43.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.42.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.15.0 |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20240903120638-7835f813f4da |  | go-module-binary-cataloger |
| google.golang.org/api | v0.274.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20260316180232-0b37fe3546d5 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20260316180232-0b37fe3546d5 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20260319201613-d00831a3d3e7 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.79.3 |  | go-module-binary-cataloger |
| google.golang.org/grpc/security/advancedtls | v1.0.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/natefinch/lumberjack.v2 | v2.2.1 |  | go-module-binary-cataloger |
| gopkg.in/validator.v2 | v2.0.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| libapk | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| libcrypto3 | 3.5.6-r0 | Apache-2.0 | apk-db-cataloger |
| libcurl | 8.17.0-r1 | curl | apk-db-cataloger |
| libgcc | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libidn2 | 2.3.8-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libncursesw | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| libpsl | 0.21.5-r3 | MIT | apk-db-cataloger |
| libssl3 | 3.5.6-r0 | Apache-2.0 | apk-db-cataloger |
| libunistring | 1.4.1-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| modernc.org/b | v1.0.0 |  | go-module-binary-cataloger |
| modernc.org/libc | v1.72.0 |  | go-module-binary-cataloger |
| modernc.org/mathutil | v1.7.1 |  | go-module-binary-cataloger |
| modernc.org/memory | v1.11.0 |  | go-module-binary-cataloger |
| modernc.org/sqlite | v1.49.1 |  | go-module-binary-cataloger |
| moul.io/http2curl/v2 | v2.3.0 |  | go-module-binary-cataloger |
| musl | 1.2.5-r23 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r23 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| nghttp2-libs | 1.69.0-r0 | MIT | apk-db-cataloger |
| nghttp3 | 1.13.1-r0 | MIT | apk-db-cataloger |
| readline | 8.3.1-r0 | GPL-3.0-or-later | apk-db-cataloger |
| scanelf | 1.3.8-r2 | GPL-2.0-only | apk-db-cataloger |
| sigs.k8s.io/yaml | v1.6.0 |  | go-module-binary-cataloger |
| sqlite | 3.51.2-r0 | blessing | apk-db-cataloger |
| ssl_client | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| stdlib | go1.25.9 | BSD-3-Clause | go-module-binary-cataloger |
| storj.io/common | v0.0.0-20251107171817-6221ae45072c |  | go-module-binary-cataloger |
| storj.io/drpc | v0.0.35-0.20250513201419-f7819ea69b55 |  | go-module-binary-cataloger |
| storj.io/eventkit | v0.0.0-20250410172343-61f26d3de156 |  | go-module-binary-cataloger |
| storj.io/infectious | v0.0.2 |  | go-module-binary-cataloger |
| storj.io/picobuf | v0.0.4 |  | go-module-binary-cataloger |
| storj.io/uplink | v1.13.1 |  | go-module-binary-cataloger |
| su-exec | 0.3-r0 | MIT | apk-db-cataloger |
| zlib | 1.3.2-r0 | Zlib | apk-db-cataloger |
| zstd-libs | 1.5.7-r2 | BSD-3-Clause OR GPL-2.0-or-later | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/alpine

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.2-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.6-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.23.5-r0 | MIT | apk-db-cataloger |
| apk-tools | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| bash | 5.3.3-r1 | GPL-3.0-or-later | apk-db-cataloger |
| busybox | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates | 20260611-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20260611-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| github.com/MakeNowJust/heredoc | v1.0.0 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/blang/semver/v4 | v4.0.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/chai2010/gettext-go | v1.0.2 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.1 |  | go-module-binary-cataloger |
| github.com/distribution/reference | v0.6.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.12.2 |  | go-module-binary-cataloger |
| github.com/exponent-io/jsonpath | v0.0.0-20210407135951-1de76d718b3f |  | go-module-binary-cataloger |
| github.com/fatih/camelcase | v1.0.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.9.0 |  | go-module-binary-cataloger |
| github.com/go-errors/errors | v1.4.2 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.20.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.23.0 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/google/btree | v1.1.3 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.4-0.20250319132907-e064f32e3674 |  | go-module-binary-cataloger |
| github.com/gregjones/httpcache | v0.0.0-20190611155906-901d90724c79 |  | go-module-binary-cataloger |
| github.com/jonboulle/clockwork | v0.5.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/liggitt/tabwriter | v0.0.0-20181228230101-89fcab3d43de |  | go-module-binary-cataloger |
| github.com/lithammer/dedent | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-wordwrap | v1.0.1 |  | go-module-binary-cataloger |
| github.com/moby/spdystream | v0.5.0 |  | go-module-binary-cataloger |
| github.com/moby/term | v0.5.0 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.3-0.20250322232337-35a7c28c31ee |  | go-module-binary-cataloger |
| github.com/monochromegane/go-gitignore | v0.0.0-20200626010858-205db1a8cc00 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/mxk/go-flowrate | v0.0.0-20140419014527-cca7078d478f |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/peterbourgon/diskv | v2.0.1+incompatible |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.22.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.62.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.15.1 |  | go-module-binary-cataloger |
| github.com/russross/blackfriday/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/spf13/cobra | v1.9.1 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.6 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/xlab/treeprint | v1.2.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.35.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.35.0 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.2 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.27.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.12.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.31.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.30.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.9.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.5 |  | go-module-binary-cataloger |
| gopkg.in/evanphx/json-patch.v4 | v4.12.0 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| k8s.io/api | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/apimachinery | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/cli-runtime | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/client-go | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/component-base | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/component-helpers | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/klog/v2 | v2.130.1 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20250710124328-f3f2b991d03b |  | go-module-binary-cataloger |
| k8s.io/kubectl | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/kubernetes | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/metrics | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20250604170112-4c0f3b243397 |  | go-module-binary-cataloger |
| kubectl | 1.34.2-r6 | Apache-2.0 | apk-db-cataloger |
| libapk | 3.0.6-r0 | GPL-2.0-only | apk-db-cataloger |
| libcrypto3 | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| libncursesw | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| libssl3 | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| musl | 1.2.5-r23 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r23 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| openssl | 3.5.7-r0 | Apache-2.0 | apk-db-cataloger |
| readline | 8.3.1-r0 | GPL-3.0-or-later | apk-db-cataloger |
| scanelf | 1.3.8-r2 | GPL-2.0-only | apk-db-cataloger |
| sigs.k8s.io/json | v0.0.0-20241014173422-cfa47c3a1cc8 |  | go-module-binary-cataloger |
| sigs.k8s.io/kustomize/api | v0.20.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/kustomize/kustomize/v5 | v5.7.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/kustomize/kyaml | v0.20.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v6 | v6.3.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.6.0 |  | go-module-binary-cataloger |
| ssl_client | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| stdlib | go1.25.10 | BSD-3-Clause | go-module-binary-cataloger |
| zlib | 1.3.2-r0 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/elasticvue

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.7.1-r8 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.1-r8 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.6-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.23.3-r0 | MIT | apk-db-cataloger |
| aom-libs | 3.13.1-r1 | BSD-2-Clause | apk-db-cataloger |
| apk-tools | 3.0.3-r1 | GPL-2.0-only | apk-db-cataloger |
| brotli-libs | 1.2.0-r0 | MIT | apk-db-cataloger |
| busybox | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| c-ares | 1.34.6-r0 | MIT | apk-db-cataloger |
| ca-certificates | 20251003-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20251003-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| curl | 8.17.0-r1 | curl | apk-db-cataloger |
| fontconfig | 2.17.1-r0 | MIT | apk-db-cataloger |
| freetype | 2.14.1-r0 | FTL OR GPL-2.0-or-later | apk-db-cataloger |
| geoip | 1.6.12-r6 | LGPL-2.1-or-later | apk-db-cataloger |
| gettext-envsubst | 0.24.1-r1 | GPL-3.0-or-later AND LGPL-2.1-or-later AND MIT | apk-db-cataloger |
| libapk | 3.0.3-r1 | GPL-2.0-only | apk-db-cataloger |
| libavif | 1.3.0-r0 | BSD-2-Clause | apk-db-cataloger |
| libbsd | 0.12.2-r0 | BSD-3-Clause | apk-db-cataloger |
| libbz2 | 1.0.8-r6 | bzip2-1.0.6 | apk-db-cataloger |
| libcrypto3 | 3.5.5-r0 | Apache-2.0 | apk-db-cataloger |
| libcurl | 8.17.0-r1 | curl | apk-db-cataloger |
| libdav1d | 1.5.2-r0 | BSD-2-Clause | apk-db-cataloger |
| libedit | 20251016.3.1-r0 | BSD-3-Clause | apk-db-cataloger |
| libexpat | 2.7.4-r0 | MIT | apk-db-cataloger |
| libgcc | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libgd | 2.3.3-r10 | GD | apk-db-cataloger |
| libice | 1.1.2-r0 | X11 | apk-db-cataloger |
| libidn2 | 2.3.8-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libintl | 0.24.1-r1 | LGPL-2.1-or-later | apk-db-cataloger |
| libjpeg-turbo | 3.1.2-r0 | BSD-3-Clause AND IJG AND Zlib | apk-db-cataloger |
| libmd | 1.1.0-r0 | BSD-2-Clause, BSD-3-Clause, Beerware, ISC | apk-db-cataloger |
| libncursesw | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| libpng | 1.6.55-r0 | Libpng | apk-db-cataloger |
| libpsl | 0.21.5-r3 | MIT | apk-db-cataloger |
| libsharpyuv | 1.6.0-r0 | BSD-3-Clause | apk-db-cataloger |
| libsm | 1.2.6-r0 | MIT | apk-db-cataloger |
| libssl3 | 3.5.5-r0 | Apache-2.0 | apk-db-cataloger |
| libstdc++ | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libunistring | 1.4.1-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libuuid | 2.41.2-r0 | BSD-3-Clause | apk-db-cataloger |
| libwebp | 1.6.0-r0 | BSD-3-Clause | apk-db-cataloger |
| libx11 | 1.8.12-r1 | X11 | apk-db-cataloger |
| libxau | 1.0.12-r0 | MIT | apk-db-cataloger |
| libxcb | 1.17.0-r1 | MIT | apk-db-cataloger |
| libxdmcp | 1.1.5-r1 | MIT | apk-db-cataloger |
| libxext | 1.3.6-r2 | MIT | apk-db-cataloger |
| libxml2 | 2.13.9-r0 | MIT | apk-db-cataloger |
| libxpm | 3.5.17-r0 | X11 | apk-db-cataloger |
| libxslt | 1.1.43-r3 | X11 | apk-db-cataloger |
| libxt | 1.3.1-r0 | MIT | apk-db-cataloger |
| libyuv | 0.0.1887.20251502-r1 | BSD-3-Clause | apk-db-cataloger |
| musl | 1.2.5-r21 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r21 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20251123-r0 | X11 | apk-db-cataloger |
| nghttp2-libs | 1.68.0-r0 | MIT | apk-db-cataloger |
| nghttp3 | 1.13.1-r0 | MIT | apk-db-cataloger |
| nginx | 1.29.5-r1 |  | apk-db-cataloger |
| nginx-module-geoip | 1.29.5-r1 |  | apk-db-cataloger |
| nginx-module-image-filter | 1.29.5-r1 |  | apk-db-cataloger |
| nginx-module-njs | 1.29.5.0.9.5-r1 |  | apk-db-cataloger |
| nginx-module-xslt | 1.29.5-r1 |  | apk-db-cataloger |
| pcre2 | 10.47-r0 | BSD-3-Clause | apk-db-cataloger |
| scanelf | 1.3.8-r2 | GPL-2.0-only | apk-db-cataloger |
| ssl_client | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| tiff | 4.7.1-r0 | libtiff | apk-db-cataloger |
| tzdata | 2026a-r0 |  | apk-db-cataloger |
| xz-libs | 5.8.2-r0 | 0BSD, GPL-2.0-or-later, LGPL-2.1-or-later | apk-db-cataloger |
| zlib | 1.3.1-r2 | Zlib | apk-db-cataloger |
| zstd-libs | 1.5.7-r2 | BSD-3-Clause OR GPL-2.0-or-later | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/redisinsight

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| 1to2 | 1.0.0 | MIT | javascript-package-cataloger |
| @azure/msal-common | 16.0.2 | MIT | javascript-package-cataloger |
| @azure/msal-node | 5.0.2 | MIT | javascript-package-cataloger |
| @babel/runtime | 7.27.0 | MIT | javascript-package-cataloger |
| @colors/colors | 1.5.0 | MIT | javascript-package-cataloger |
| @cspotcode/source-map-support | 0.8.1 | MIT | javascript-package-cataloger |
| @dabh/diagnostics | 2.0.3 | MIT | javascript-package-cataloger |
| @glideapps/ts-necessities | 2.1.3 | MIT | javascript-package-cataloger |
| @ioredis/commands | 1.2.0 | MIT | javascript-package-cataloger |
| @isaacs/cliui | 8.0.2 | ISC | javascript-package-cataloger |
| @isaacs/cliui | 8.0.2 | ISC | javascript-package-cataloger |
| @isaacs/fs-minipass | 4.0.1 | ISC | javascript-package-cataloger |
| @isaacs/string-locale-compare | 1.1.0 | ISC | javascript-package-cataloger |
| @jridgewell/resolve-uri | 3.1.2 | MIT | javascript-package-cataloger |
| @jridgewell/sourcemap-codec | 1.5.5 | MIT | javascript-package-cataloger |
| @jridgewell/trace-mapping | 0.3.9 | MIT | javascript-package-cataloger |
| @lukeed/csprng | 1.1.0 | MIT | javascript-package-cataloger |
| @lukeed/uuid | 2.0.1 | MIT | javascript-package-cataloger |
| @microsoft/tsdoc | 0.15.1 | MIT | javascript-package-cataloger |
| @nestjs/common | 11.0.20 | MIT | javascript-package-cataloger |
| @nestjs/core | 11.1.18 | MIT | javascript-package-cataloger |
| @nestjs/event-emitter | 3.0.1 | MIT | javascript-package-cataloger |
| @nestjs/mapped-types | 2.1.0 | MIT | javascript-package-cataloger |
| @nestjs/platform-express | 11.1.3 | MIT | javascript-package-cataloger |
| @nestjs/platform-socket.io | 11.0.20 | MIT | javascript-package-cataloger |
| @nestjs/serve-static | 5.0.3 | MIT | javascript-package-cataloger |
| @nestjs/swagger | 11.1.3 | MIT | javascript-package-cataloger |
| @nestjs/typeorm | 11.0.0 | MIT | javascript-package-cataloger |
| @nestjs/websockets | 11.0.20 | MIT | javascript-package-cataloger |
| @npmcli/agent | 3.0.0 | ISC | javascript-package-cataloger |
| @npmcli/arborist | 8.0.1 | ISC | javascript-package-cataloger |
| @npmcli/config | 9.0.0 | ISC | javascript-package-cataloger |
| @npmcli/fs | 4.0.0 | ISC | javascript-package-cataloger |
| @npmcli/git | 6.0.3 | ISC | javascript-package-cataloger |
| @npmcli/installed-package-contents | 3.0.0 | ISC | javascript-package-cataloger |
| @npmcli/map-workspaces | 4.0.2 | ISC | javascript-package-cataloger |
| @npmcli/metavuln-calculator | 8.0.1 | ISC | javascript-package-cataloger |
| @npmcli/name-from-folder | 3.0.0 | ISC | javascript-package-cataloger |
| @npmcli/node-gyp | 4.0.0 | ISC | javascript-package-cataloger |
| @npmcli/package-json | 6.2.0 | ISC | javascript-package-cataloger |
| @npmcli/promise-spawn | 8.0.2 | ISC | javascript-package-cataloger |
| @npmcli/query | 4.0.1 | ISC | javascript-package-cataloger |
| @npmcli/redact | 3.2.2 | ISC | javascript-package-cataloger |
| @npmcli/run-script | 9.1.0 | ISC | javascript-package-cataloger |
| @nuxt/opencollective | 0.4.1 | MIT | javascript-package-cataloger |
| @okta/okta-auth-js | 7.12.1 |  | javascript-package-cataloger |
| @okta/okta-auth-js | 7.12.1 |  | javascript-package-cataloger |
| @okta/okta-auth-js | 7.12.1 | Apache-2.0 | javascript-package-cataloger |
| @peculiar/asn1-schema | 2.3.6 | MIT | javascript-package-cataloger |
| @peculiar/json-schema | 1.1.12 | MIT | javascript-package-cataloger |
| @peculiar/webcrypto | 1.4.3 | MIT | javascript-package-cataloger |
| @pkgjs/parseargs | 0.11.0 | MIT | javascript-package-cataloger |
| @pkgjs/parseargs | 0.11.0 | MIT | javascript-package-cataloger |
| @redis/bloom | 1.2.0 | MIT | javascript-package-cataloger |
| @redis/client | 1.5.11 | MIT | javascript-package-cataloger |
| @redis/graph | 1.1.0 | MIT | javascript-package-cataloger |
| @redis/json | 1.0.6 | MIT | javascript-package-cataloger |
| @redis/search | 1.1.5 | MIT | javascript-package-cataloger |
| @redis/time-series | 1.0.5 | MIT | javascript-package-cataloger |
| @scarf/scarf | 1.4.0 | Apache-2.0 | javascript-package-cataloger |
| @segment/analytics-core | 1.8.0 | MIT | javascript-package-cataloger |
| @segment/analytics-generic-utils | 1.2.0 | MIT | javascript-package-cataloger |
| @segment/analytics-node | 2.2.0 | MIT | javascript-package-cataloger |
| @sigstore/bundle | 3.1.0 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/core | 2.0.0 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/protobuf-specs | 0.4.3 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/sign | 3.1.0 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/tuf | 3.1.1 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/verify | 2.1.1 | Apache-2.0 | javascript-package-cataloger |
| @socket.io/component-emitter | 3.1.2 | MIT | javascript-package-cataloger |
| @socket.io/component-emitter | UNKNOWN |  | javascript-package-cataloger |
| @socket.io/component-emitter | UNKNOWN |  | javascript-package-cataloger |
| @sqltools/formatter | 1.2.5 | MIT | javascript-package-cataloger |
| @supercharge/promise-pool | 3.2.0 | MIT | javascript-package-cataloger |
| @tokenizer/inflate | 0.2.7 | MIT | javascript-package-cataloger |
| @tokenizer/token | 0.3.0 | MIT | javascript-package-cataloger |
| @tsconfig/node10 | 1.0.11 | MIT | javascript-package-cataloger |
| @tsconfig/node12 | 1.0.11 | MIT | javascript-package-cataloger |
| @tsconfig/node14 | 1.0.3 | MIT | javascript-package-cataloger |
| @tsconfig/node16 | 1.0.4 | MIT | javascript-package-cataloger |
| @tufjs/canonical-json | 2.0.0 | MIT | javascript-package-cataloger |
| @tufjs/models | 3.0.1 | MIT | javascript-package-cataloger |
| @types/cookie | 0.4.1 | MIT | javascript-package-cataloger |
| @types/cors | 2.8.17 | MIT | javascript-package-cataloger |
| @types/json-bigint | 1.0.4 | MIT | javascript-package-cataloger |
| @types/node | 18.19.76 | MIT | javascript-package-cataloger |
| @types/node | 22.7.5 | MIT | javascript-package-cataloger |
| @types/node | 24.10.1 | MIT | javascript-package-cataloger |
| @types/triple-beam | 1.3.2 | MIT | javascript-package-cataloger |
| @types/urijs | 1.19.25 | MIT | javascript-package-cataloger |
| @types/validator | 13.12.2 | MIT | javascript-package-cataloger |
| Base64 | 1.1.0 | (Apache-2.0 OR WTFPL) | javascript-package-cataloger |
| abbrev | 3.0.1 | ISC | javascript-package-cataloger |
| abort-controller | 3.0.0 | MIT | javascript-package-cataloger |
| accepts | 1.3.8 | MIT | javascript-package-cataloger |
| accepts | 2.0.0 | MIT | javascript-package-cataloger |
| accepts | 2.0.0 | MIT | javascript-package-cataloger |
| acorn | 8.13.0 | MIT | javascript-package-cataloger |
| acorn | 8.13.0 | MIT | javascript-package-cataloger |
| acorn-walk | 8.3.4 | MIT | javascript-package-cataloger |
| address | 1.2.2 | MIT | javascript-package-cataloger |
| adm-zip | 0.5.10 | MIT | javascript-package-cataloger |
| agent-base | 7.1.3 | MIT | javascript-package-cataloger |
| alpine-baselayout | 3.7.1-r8 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.1-r8 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.6-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.23.3-r0 | MIT | apk-db-cataloger |
| ansi-regex | 5.0.1 | MIT | javascript-package-cataloger |
| ansi-regex | 5.0.1 | MIT | javascript-package-cataloger |
| ansi-regex | 6.1.0 | MIT | javascript-package-cataloger |
| ansi-regex | 6.1.0 | MIT | javascript-package-cataloger |
| ansi-regex | 6.2.2 | MIT | javascript-package-cataloger |
| ansi-styles | 4.3.0 | MIT | javascript-package-cataloger |
| ansi-styles | 4.3.0 | MIT | javascript-package-cataloger |
| ansi-styles | 6.2.1 | MIT | javascript-package-cataloger |
| ansi-styles | 6.2.3 | MIT | javascript-package-cataloger |
| ansis | 3.17.0 | ISC | javascript-package-cataloger |
| apk-tools | 3.0.3-r1 | GPL-2.0-only | apk-db-cataloger |
| app-root-path | 3.1.0 | MIT | javascript-package-cataloger |
| append-field | 1.0.0 | MIT | javascript-package-cataloger |
| aproba | 2.0.0 | ISC | javascript-package-cataloger |
| archy | 1.0.0 | MIT | javascript-package-cataloger |
| arg | 4.1.3 | MIT | javascript-package-cataloger |
| argparse | 2.0.1 | Python-2.0 | javascript-package-cataloger |
| asn1 | 0.2.6 | MIT | javascript-package-cataloger |
| asn1js | 3.0.5 | BSD-3-Clause | javascript-package-cataloger |
| async | 3.2.4 | MIT | javascript-package-cataloger |
| asynckit | 0.4.0 | MIT | javascript-package-cataloger |
| atob | 2.1.2 | (MIT OR Apache-2.0) | javascript-package-cataloger |
| available-typed-arrays | 1.0.7 | MIT | javascript-package-cataloger |
| axios | 1.15.0 | MIT | javascript-package-cataloger |
| balanced-match | 1.0.2 | MIT | javascript-package-cataloger |
| balanced-match | 1.0.2 | MIT | javascript-package-cataloger |
| base64-js | 1.5.1 | MIT | javascript-package-cataloger |
| base64id | 2.0.0 | MIT | javascript-package-cataloger |
| bcrypt-pbkdf | 1.0.2 | BSD-3-Clause | javascript-package-cataloger |
| beep-boop | 1.2.3 |  | javascript-package-cataloger |
| better-sqlite3 | 12.8.0 | MIT | javascript-package-cataloger |
| bignumber.js | 9.1.2 | MIT | javascript-package-cataloger |
| bin-links | 5.0.0 | ISC | javascript-package-cataloger |
| binary-extensions | 2.3.0 | MIT | javascript-package-cataloger |
| bindings | 1.5.0 | MIT | javascript-package-cataloger |
| bl | 4.1.0 | MIT | javascript-package-cataloger |
| body-parser | 1.20.3 | MIT | javascript-package-cataloger |
| body-parser | 2.2.1 | MIT | javascript-package-cataloger |
| body-parser | 2.2.1 | MIT | javascript-package-cataloger |
| brace-expansion | 2.0.2 | MIT | javascript-package-cataloger |
| brace-expansion | 2.0.2 | MIT | javascript-package-cataloger |
| broadcast-channel | 7.1.0 | MIT | javascript-package-cataloger |
| browser-or-node | 2.1.1 | MIT | javascript-package-cataloger |
| btoa | 1.2.1 | (MIT OR Apache-2.0) | javascript-package-cataloger |
| buffer | 5.7.1 | MIT | javascript-package-cataloger |
| buffer | 6.0.3 | MIT | javascript-package-cataloger |
| buffer-equal-constant-time | 1.0.1 | BSD-3-Clause | javascript-package-cataloger |
| buffer-from | 1.1.2 | MIT | javascript-package-cataloger |
| busboy | 1.6.0 | MIT | javascript-package-cataloger |
| busybox | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| bytes | 3.1.2 | MIT | javascript-package-cataloger |
| ca-certificates-bundle | 20251003-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| cacache | 19.0.1 | ISC | javascript-package-cataloger |
| call-bind | 1.0.7 | MIT | javascript-package-cataloger |
| call-bind | 1.0.8 | MIT | javascript-package-cataloger |
| call-bind-apply-helpers | 1.0.2 | MIT | javascript-package-cataloger |
| call-bound | 1.0.3 | MIT | javascript-package-cataloger |
| call-bound | 1.0.4 | MIT | javascript-package-cataloger |
| call-bound | 1.0.4 | MIT | javascript-package-cataloger |
| chalk | 5.4.1 | MIT | javascript-package-cataloger |
| chownr | 1.1.4 | ISC | javascript-package-cataloger |
| chownr | 2.0.0 | ISC | javascript-package-cataloger |
| chownr | 3.0.0 | BlueOak-1.0.0 | javascript-package-cataloger |
| chownr | 3.0.0 | BlueOak-1.0.0 | javascript-package-cataloger |
| ci-info | 4.2.0 | MIT | javascript-package-cataloger |
| cidr-regex | 4.1.3 | BSD-2-Clause | javascript-package-cataloger |
| class-transformer | 0.5.1 | MIT | javascript-package-cataloger |
| class-validator | 0.14.1 | MIT | javascript-package-cataloger |
| cli-columns | 4.0.0 | MIT | javascript-package-cataloger |
| client-list | 0.0.3 |  | javascript-package-cataloger |
| cliui | 8.0.1 | ISC | javascript-package-cataloger |
| clone | 2.1.2 | MIT | javascript-package-cataloger |
| cluster-key-slot | 1.1.2 | Apache-2.0 | javascript-package-cataloger |
| cmd-shim | 7.0.0 | ISC | javascript-package-cataloger |
| collection-utils | 1.0.1 | Apache-2.0 | javascript-package-cataloger |
| color | 3.2.1 | MIT | javascript-package-cataloger |
| color-convert | 1.9.3 | MIT | javascript-package-cataloger |
| color-convert | 2.0.1 | MIT | javascript-package-cataloger |
| color-convert | 2.0.1 | MIT | javascript-package-cataloger |
| color-name | 1.1.3 | MIT | javascript-package-cataloger |
| color-name | 1.1.4 | MIT | javascript-package-cataloger |
| color-name | 1.1.4 | MIT | javascript-package-cataloger |
| color-string | 1.9.1 | MIT | javascript-package-cataloger |
| colorspace | 1.1.4 | MIT | javascript-package-cataloger |
| combined-stream | 1.0.8 | MIT | javascript-package-cataloger |
| common | 0.0.1 |  | javascript-package-cataloger |
| common-ancestor-path | 1.0.1 | ISC | javascript-package-cataloger |
| concat-stream | 2.0.0 | MIT | javascript-package-cataloger |
| connect-timeout | 1.9.1 | MIT | javascript-package-cataloger |
| consola | 3.4.0 | MIT | javascript-package-cataloger |
| content-disposition | 1.0.0 | MIT | javascript-package-cataloger |
| content-type | 1.0.5 | MIT | javascript-package-cataloger |
| cookie | 0.7.2 | MIT | javascript-package-cataloger |
| cookie-signature | 1.2.2 | MIT | javascript-package-cataloger |
| core-js | 3.41.0 | MIT | javascript-package-cataloger |
| corepack | 0.34.0 | MIT | javascript-package-cataloger |
| cors | 2.8.5 | MIT | javascript-package-cataloger |
| cpu-features | 1.0.0 |  | javascript-package-cataloger |
| create-require | 1.1.1 | MIT | javascript-package-cataloger |
| cross-fetch | 3.1.7 | MIT | javascript-package-cataloger |
| cross-fetch | 4.0.0 | MIT | javascript-package-cataloger |
| cross-fetch-polyfill | 0.0.0 | MIT | javascript-package-cataloger |
| cross-fetch-polyfill | 0.0.0 | MIT | javascript-package-cataloger |
| cross-spawn | 7.0.6 | MIT | javascript-package-cataloger |
| cross-spawn | 7.0.6 | MIT | javascript-package-cataloger |
| cssesc | 3.0.0 | MIT | javascript-package-cataloger |
| date-fns | 2.29.3 | MIT | javascript-package-cataloger |
| dayjs | 1.11.13 | MIT | javascript-package-cataloger |
| debug | 2.6.9 | MIT | javascript-package-cataloger |
| debug | 4.3.7 | MIT | javascript-package-cataloger |
| debug | 4.3.7 | MIT | javascript-package-cataloger |
| debug | 4.3.7 | MIT | javascript-package-cataloger |
| debug | 4.3.7 | MIT | javascript-package-cataloger |
| debug | 4.3.7 | MIT | javascript-package-cataloger |
| debug | 4.4.1 | MIT | javascript-package-cataloger |
| debug | 4.4.3 | MIT | javascript-package-cataloger |
| decompress-response | 6.0.0 | MIT | javascript-package-cataloger |
| dedent | 1.6.0 | MIT | javascript-package-cataloger |
| deep-extend | 0.6.0 | MIT | javascript-package-cataloger |
| define-data-property | 1.1.4 | MIT | javascript-package-cataloger |
| delayed-stream | 1.0.0 | MIT | javascript-package-cataloger |
| denque | 2.1.0 | Apache-2.0 | javascript-package-cataloger |
| depd | 1.1.2 | MIT | javascript-package-cataloger |
| depd | 2.0.0 | MIT | javascript-package-cataloger |
| destroy | 1.2.0 | MIT | javascript-package-cataloger |
| detect-libc | 2.0.1 | Apache-2.0 | javascript-package-cataloger |
| detect-port | 1.5.1 | MIT | javascript-package-cataloger |
| diff | 4.0.2 | BSD-3-Clause | javascript-package-cataloger |
| diff | 5.2.0 | BSD-3-Clause | javascript-package-cataloger |
| dotenv | 16.6.1 | BSD-2-Clause | javascript-package-cataloger |
| dset | 3.1.4 | MIT | javascript-package-cataloger |
| dunder-proto | 1.0.1 | MIT | javascript-package-cataloger |
| eastasianwidth | 0.2.0 | MIT | javascript-package-cataloger |
| eastasianwidth | 0.2.0 | MIT | javascript-package-cataloger |
| ecdsa-sig-formatter | 1.0.11 | Apache-2.0 | javascript-package-cataloger |
| ee-first | 1.1.1 | MIT | javascript-package-cataloger |
| emoji-regex | 8.0.0 | MIT | javascript-package-cataloger |
| emoji-regex | 8.0.0 | MIT | javascript-package-cataloger |
| emoji-regex | 9.2.2 | MIT | javascript-package-cataloger |
| emoji-regex | 9.2.2 | MIT | javascript-package-cataloger |
| emoji-regex | 9.2.2 | MIT | javascript-package-cataloger |
| enabled | 2.0.0 | MIT | javascript-package-cataloger |
| encodeurl | 2.0.0 | MIT | javascript-package-cataloger |
| encoding | 0.1.13 | MIT | javascript-package-cataloger |
| end-of-stream | 1.4.4 | MIT | javascript-package-cataloger |
| engine.io | 6.6.2 | MIT | javascript-package-cataloger |
| engine.io-client | 6.6.1 | MIT | javascript-package-cataloger |
| engine.io-client | UNKNOWN |  | javascript-package-cataloger |
| engine.io-client | UNKNOWN |  | javascript-package-cataloger |
| engine.io-client | UNKNOWN |  | javascript-package-cataloger |
| engine.io-parser | 5.2.3 | MIT | javascript-package-cataloger |
| engine.io-parser | UNKNOWN |  | javascript-package-cataloger |
| engine.io-parser | UNKNOWN |  | javascript-package-cataloger |
| env-paths | 2.2.1 | MIT | javascript-package-cataloger |
| err-code | 2.0.3 | MIT | javascript-package-cataloger |
| es-define-property | 1.0.0 | MIT | javascript-package-cataloger |
| es-define-property | 1.0.1 | MIT | javascript-package-cataloger |
| es-define-property | 1.0.1 | MIT | javascript-package-cataloger |
| es-define-property | 1.0.1 | MIT | javascript-package-cataloger |
| es-define-property | 1.0.1 | MIT | javascript-package-cataloger |
| es-define-property | 1.0.1 | MIT | javascript-package-cataloger |
| es-define-property | 1.0.1 | MIT | javascript-package-cataloger |
| es-errors | 1.3.0 | MIT | javascript-package-cataloger |
| es-object-atoms | 1.1.1 | MIT | javascript-package-cataloger |
| es-set-tostringtag | 2.1.0 | MIT | javascript-package-cataloger |
| escalade | 3.2.0 | MIT | javascript-package-cataloger |
| escape-html | 1.0.3 | MIT | javascript-package-cataloger |
| etag | 1.8.1 | MIT | javascript-package-cataloger |
| event-target-shim | 5.0.1 | MIT | javascript-package-cataloger |
| eventemitter2 | 6.4.9 | MIT | javascript-package-cataloger |
| eventemitter3 | 4.0.7 | MIT | javascript-package-cataloger |
| events | 3.3.0 | MIT | javascript-package-cataloger |
| expand-template | 2.0.3 | (MIT OR WTFPL) | javascript-package-cataloger |
| explain-plugin | 0.0.2 |  | javascript-package-cataloger |
| exponential-backoff | 3.1.2 | Apache-2.0 | javascript-package-cataloger |
| express | 5.1.0 | MIT | javascript-package-cataloger |
| express | 5.2.0 | MIT | javascript-package-cataloger |
| fast-safe-stringify | 2.1.1 | MIT | javascript-package-cataloger |
| fast-text-encoding | 1.0.6 | Apache-2.0 | javascript-package-cataloger |
| fastest-levenshtein | 1.0.16 | MIT | javascript-package-cataloger |
| fdir | 6.4.6 | MIT | javascript-package-cataloger |
| fecha | 4.2.3 | MIT | javascript-package-cataloger |
| fflate | 0.8.2 | MIT | javascript-package-cataloger |
| file-stream-rotator | 1.0.0 | MIT | javascript-package-cataloger |
| file-type | 16.5.4 | MIT | javascript-package-cataloger |
| file-type | 20.4.1 | MIT | javascript-package-cataloger |
| file-uri-to-path | 1.0.0 | MIT | javascript-package-cataloger |
| finalhandler | 2.1.0 | MIT | javascript-package-cataloger |
| fn.name | 1.1.0 | MIT | javascript-package-cataloger |
| follow-redirects | 1.15.11 | MIT | javascript-package-cataloger |
| for-each | 0.3.5 | MIT | javascript-package-cataloger |
| foreground-child | 3.3.1 | ISC | javascript-package-cataloger |
| foreground-child | 3.3.1 | ISC | javascript-package-cataloger |
| form-data | 4.0.5 | MIT | javascript-package-cataloger |
| forwarded | 0.2.0 | MIT | javascript-package-cataloger |
| fresh | 2.0.0 | MIT | javascript-package-cataloger |
| fs-constants | 1.0.0 | MIT | javascript-package-cataloger |
| fs-extra | 10.1.0 | MIT | javascript-package-cataloger |
| fs-minipass | 2.1.0 | ISC | javascript-package-cataloger |
| fs-minipass | 3.0.3 | ISC | javascript-package-cataloger |
| function-bind | 1.1.2 | MIT | javascript-package-cataloger |
| generic-pool | 3.9.0 | MIT | javascript-package-cataloger |
| get-caller-file | 2.0.5 | ISC | javascript-package-cataloger |
| get-intrinsic | 1.2.4 | MIT | javascript-package-cataloger |
| get-intrinsic | 1.3.0 | MIT | javascript-package-cataloger |
| get-intrinsic | 1.3.0 | MIT | javascript-package-cataloger |
| get-intrinsic | 1.3.0 | MIT | javascript-package-cataloger |
| get-intrinsic | 1.3.0 | MIT | javascript-package-cataloger |
| get-intrinsic | 1.3.0 | MIT | javascript-package-cataloger |
| get-intrinsic | 1.3.0 | MIT | javascript-package-cataloger |
| get-proto | 1.0.1 | MIT | javascript-package-cataloger |
| github-from-package | 0.0.0 | MIT | javascript-package-cataloger |
| glob | 10.4.5 | ISC | javascript-package-cataloger |
| glob | 10.5.0 | ISC | javascript-package-cataloger |
| gopd | 1.0.1 | MIT | javascript-package-cataloger |
| gopd | 1.0.1 | MIT | javascript-package-cataloger |
| gopd | 1.2.0 | MIT | javascript-package-cataloger |
| graceful-fs | 4.2.11 | ISC | javascript-package-cataloger |
| graceful-fs | 4.2.11 | ISC | javascript-package-cataloger |
| graph-plugin | 0.0.2 |  | javascript-package-cataloger |
| has-property-descriptors | 1.0.2 | MIT | javascript-package-cataloger |
| has-proto | 1.0.3 | MIT | javascript-package-cataloger |
| has-symbols | 1.1.0 | MIT | javascript-package-cataloger |
| has-tostringtag | 1.0.2 | MIT | javascript-package-cataloger |
| hasown | 2.0.2 | MIT | javascript-package-cataloger |
| hosted-git-info | 8.1.0 | ISC | javascript-package-cataloger |
| http-cache-semantics | 4.2.0 | BSD-2-Clause | javascript-package-cataloger |
| http-errors | 1.6.3 | MIT | javascript-package-cataloger |
| http-errors | 2.0.0 | MIT | javascript-package-cataloger |
| http-errors | 2.0.0 | MIT | javascript-package-cataloger |
| http-errors | 2.0.1 | MIT | javascript-package-cataloger |
| http-proxy-agent | 7.0.2 | MIT | javascript-package-cataloger |
| https-proxy-agent | 7.0.6 | MIT | javascript-package-cataloger |
| iconv-lite | 0.4.24 | MIT | javascript-package-cataloger |
| iconv-lite | 0.4.24 | MIT | javascript-package-cataloger |
| iconv-lite | 0.6.3 | MIT | javascript-package-cataloger |
| iconv-lite | 0.7.0 | MIT | javascript-package-cataloger |
| ieee754 | 1.2.1 | BSD-3-Clause | javascript-package-cataloger |
| ignore-walk | 7.0.0 | ISC | javascript-package-cataloger |
| imurmurhash | 0.1.4 | MIT | javascript-package-cataloger |
| inherits | 2.0.3 | ISC | javascript-package-cataloger |
| inherits | 2.0.4 | ISC | javascript-package-cataloger |
| ini | 1.3.8 | ISC | javascript-package-cataloger |
| ini | 5.0.0 | ISC | javascript-package-cataloger |
| init-package-json | 7.0.2 | ISC | javascript-package-cataloger |
| ioredis | 5.3.2 | MIT | javascript-package-cataloger |
| ip-address | 9.0.5 | MIT | javascript-package-cataloger |
| ip-regex | 5.0.0 | MIT | javascript-package-cataloger |
| ipaddr.js | 1.9.1 | MIT | javascript-package-cataloger |
| is-arrayish | 0.3.2 | MIT | javascript-package-cataloger |
| is-callable | 1.2.7 | MIT | javascript-package-cataloger |
| is-cidr | 5.1.1 | BSD-2-Clause | javascript-package-cataloger |
| is-extglob | 2.1.1 | MIT | javascript-package-cataloger |
| is-fullwidth-code-point | 3.0.0 | MIT | javascript-package-cataloger |
| is-fullwidth-code-point | 3.0.0 | MIT | javascript-package-cataloger |
| is-glob | 4.0.3 | MIT | javascript-package-cataloger |
| is-promise | 4.0.0 | MIT | javascript-package-cataloger |
| is-stream | 2.0.1 | MIT | javascript-package-cataloger |
| is-typed-array | 1.1.15 | MIT | javascript-package-cataloger |
| is-url | 1.2.4 | MIT | javascript-package-cataloger |
| isarray | 2.0.5 | MIT | javascript-package-cataloger |
| isexe | 2.0.0 | ISC | javascript-package-cataloger |
| isexe | 2.0.0 | ISC | javascript-package-cataloger |
| isexe | 3.1.1 | ISC | javascript-package-cataloger |
| iterare | 1.2.1 | ISC | javascript-package-cataloger |
| jackspeak | 3.4.3 | BlueOak-1.0.0 | javascript-package-cataloger |
| jackspeak | 3.4.3 | BlueOak-1.0.0 | javascript-package-cataloger |
| jose | 5.4.0 | MIT | javascript-package-cataloger |
| js-base64 | 3.7.7 | BSD-3-Clause | javascript-package-cataloger |
| js-cookie | 3.0.5 | MIT | javascript-package-cataloger |
| js-yaml | 4.1.1 | MIT | javascript-package-cataloger |
| jsbn | 1.1.0 | MIT | javascript-package-cataloger |
| json-bigint | 1.0.0 | MIT | javascript-package-cataloger |
| json-parse-even-better-errors | 4.0.0 | MIT | javascript-package-cataloger |
| json-stringify-nice | 1.1.4 | ISC | javascript-package-cataloger |
| jsonfile | 6.1.0 | MIT | javascript-package-cataloger |
| jsonparse | 1.3.1 | MIT | javascript-package-cataloger |
| jsonwebtoken | 9.0.2 | MIT | javascript-package-cataloger |
| jsonwebtoken | 9.0.3 | MIT | javascript-package-cataloger |
| just-diff | 6.0.2 | MIT | javascript-package-cataloger |
| just-diff-apply | 5.5.0 | MIT | javascript-package-cataloger |
| jwa | 1.4.2 | MIT | javascript-package-cataloger |
| jwa | 2.0.1 | MIT | javascript-package-cataloger |
| jws | 3.2.3 | MIT | javascript-package-cataloger |
| jws | 4.0.1 | MIT | javascript-package-cataloger |
| keytar | 7.9.0 | MIT | javascript-package-cataloger |
| kuler | 2.0.0 | MIT | javascript-package-cataloger |
| libapk | 3.0.3-r1 | GPL-2.0-only | apk-db-cataloger |
| libcrypto3 | 3.5.6-r0 | Apache-2.0 | apk-db-cataloger |
| libgcc | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libnpmaccess | 9.0.0 | ISC | javascript-package-cataloger |
| libnpmdiff | 7.0.1 | ISC | javascript-package-cataloger |
| libnpmexec | 9.0.1 | ISC | javascript-package-cataloger |
| libnpmfund | 6.0.1 | ISC | javascript-package-cataloger |
| libnpmhook | 11.0.0 | ISC | javascript-package-cataloger |
| libnpmorg | 7.0.0 | ISC | javascript-package-cataloger |
| libnpmpack | 8.0.1 | ISC | javascript-package-cataloger |
| libnpmpublish | 10.0.1 | ISC | javascript-package-cataloger |
| libnpmsearch | 8.0.0 | ISC | javascript-package-cataloger |
| libnpmteam | 7.0.0 | ISC | javascript-package-cataloger |
| libnpmversion | 7.0.0 | ISC | javascript-package-cataloger |
| libphonenumber-js | 1.11.11 | MIT | javascript-package-cataloger |
| libphonenumber-js/build | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/core | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/max | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/max/metadata | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/min | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/min/metadata | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/mobile | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/mobile/examples | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/mobile/metadata | UNKNOWN |  | javascript-package-cataloger |
| libssl3 | 3.5.6-r0 | Apache-2.0 | apk-db-cataloger |
| libstdc++ | 15.2.0-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| load-esm | 1.0.2 | MIT | javascript-package-cataloger |
| lodash | 4.17.21 | MIT | javascript-package-cataloger |
| lodash | 4.18.1 | MIT | javascript-package-cataloger |
| lodash.defaults | 4.2.0 | MIT | javascript-package-cataloger |
| lodash.includes | 4.3.0 | MIT | javascript-package-cataloger |
| lodash.isarguments | 3.1.0 | MIT | javascript-package-cataloger |
| lodash.isboolean | 3.0.3 | MIT | javascript-package-cataloger |
| lodash.isinteger | 4.0.4 | MIT | javascript-package-cataloger |
| lodash.isnumber | 3.0.3 | MIT | javascript-package-cataloger |
| lodash.isplainobject | 4.0.6 | MIT | javascript-package-cataloger |
| lodash.isstring | 4.0.1 | MIT | javascript-package-cataloger |
| lodash.once | 4.1.1 | MIT | javascript-package-cataloger |
| logform | 2.5.1 | MIT | javascript-package-cataloger |
| lru-cache | 10.4.3 | ISC | javascript-package-cataloger |
| lru-cache | 10.4.3 | ISC | javascript-package-cataloger |
| lru-cache | 6.0.0 | ISC | javascript-package-cataloger |
| make-error | 1.3.6 | ISC | javascript-package-cataloger |
| make-fetch-happen | 14.0.3 | ISC | javascript-package-cataloger |
| math-intrinsics | 1.1.0 | MIT | javascript-package-cataloger |
| media-typer | 0.3.0 | MIT | javascript-package-cataloger |
| media-typer | 1.1.0 | MIT | javascript-package-cataloger |
| media-typer | 1.1.0 | MIT | javascript-package-cataloger |
| merge-descriptors | 2.0.0 | MIT | javascript-package-cataloger |
| mime-db | 1.52.0 | MIT | javascript-package-cataloger |
| mime-db | 1.52.0 | MIT | javascript-package-cataloger |
| mime-db | 1.52.0 | MIT | javascript-package-cataloger |
| mime-db | 1.54.0 | MIT | javascript-package-cataloger |
| mime-types | 2.1.35 | MIT | javascript-package-cataloger |
| mime-types | 2.1.35 | MIT | javascript-package-cataloger |
| mime-types | 2.1.35 | MIT | javascript-package-cataloger |
| mime-types | 3.0.1 | MIT | javascript-package-cataloger |
| mimic-response | 3.1.0 | MIT | javascript-package-cataloger |
| minimatch | 9.0.5 | ISC | javascript-package-cataloger |
| minimatch | 9.0.5 | ISC | javascript-package-cataloger |
| minimist | 1.2.8 | MIT | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 5.0.0 | ISC | javascript-package-cataloger |
| minipass | 7.1.2 | ISC | javascript-package-cataloger |
| minipass | 7.1.2 | ISC | javascript-package-cataloger |
| minipass-collect | 2.0.1 | ISC | javascript-package-cataloger |
| minipass-fetch | 4.0.1 | MIT | javascript-package-cataloger |
| minipass-flush | 1.0.5 | ISC | javascript-package-cataloger |
| minipass-pipeline | 1.2.4 | ISC | javascript-package-cataloger |
| minipass-sized | 1.0.3 | ISC | javascript-package-cataloger |
| minizlib | 2.1.2 | MIT | javascript-package-cataloger |
| minizlib | 3.0.2 | MIT | javascript-package-cataloger |
| mkdirp | 0.5.6 | MIT | javascript-package-cataloger |
| mkdirp | 1.0.4 | MIT | javascript-package-cataloger |
| mkdirp | 1.0.4 | MIT | javascript-package-cataloger |
| mkdirp | 3.0.1 | MIT | javascript-package-cataloger |
| mkdirp | 3.0.1 | MIT | javascript-package-cataloger |
| mkdirp | 3.0.1 | MIT | javascript-package-cataloger |
| mkdirp | 3.0.1 | MIT | javascript-package-cataloger |
| mkdirp-classic | 0.5.3 | MIT | javascript-package-cataloger |
| ms | 2.0.0 | MIT | javascript-package-cataloger |
| ms | 2.0.0 | MIT | javascript-package-cataloger |
| ms | 2.1.3 | MIT | javascript-package-cataloger |
| ms | 2.1.3 | MIT | javascript-package-cataloger |
| multer | 2.0.2 | MIT | javascript-package-cataloger |
| musl | 1.2.5-r23 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r21 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| mute-stream | 2.0.0 | ISC | javascript-package-cataloger |
| nan | 2.18.0 | MIT | javascript-package-cataloger |
| napi-build-utils | 1.0.2 | MIT | javascript-package-cataloger |
| negotiator | 0.6.3 | MIT | javascript-package-cataloger |
| negotiator | 1.0.0 | MIT | javascript-package-cataloger |
| negotiator | 1.0.0 | MIT | javascript-package-cataloger |
| negotiator | 1.0.0 | MIT | javascript-package-cataloger |
| nest-winston | 1.10.2 | MIT | javascript-package-cataloger |
| nestjs-form-data | 1.9.93 | MIT | javascript-package-cataloger |
| node | 22.22.0 |  | binary-classifier-cataloger |
| node-abi | 3.40.0 | MIT | javascript-package-cataloger |
| node-addon-api | 4.3.0 | MIT | javascript-package-cataloger |
| node-cache | 5.1.2 | MIT | javascript-package-cataloger |
| node-fetch | 2.6.12 | MIT | javascript-package-cataloger |
| node-fetch | 2.7.0 | MIT | javascript-package-cataloger |
| node-gyp | 11.2.0 | MIT | javascript-package-cataloger |
| node-version-compare | 1.0.3 | MIT | javascript-package-cataloger |
| nopt | 8.1.0 | ISC | javascript-package-cataloger |
| normalize-package-data | 7.0.0 | BSD-2-Clause | javascript-package-cataloger |
| npm | 10.9.4 | Artistic-2.0 | javascript-package-cataloger |
| npm-audit-report | 6.0.0 | ISC | javascript-package-cataloger |
| npm-bundled | 4.0.0 | ISC | javascript-package-cataloger |
| npm-install-checks | 7.1.1 | BSD-2-Clause | javascript-package-cataloger |
| npm-normalize-package-bin | 4.0.0 | ISC | javascript-package-cataloger |
| npm-package-arg | 12.0.2 | ISC | javascript-package-cataloger |
| npm-packlist | 9.0.0 | ISC | javascript-package-cataloger |
| npm-pick-manifest | 10.0.0 | ISC | javascript-package-cataloger |
| npm-profile | 11.0.1 | ISC | javascript-package-cataloger |
| npm-registry-fetch | 18.0.2 | ISC | javascript-package-cataloger |
| npm-user-validate | 3.0.0 | BSD-2-Clause | javascript-package-cataloger |
| object-assign | 4.1.1 | MIT | javascript-package-cataloger |
| object-hash | 2.2.0 | MIT | javascript-package-cataloger |
| object-hash | 3.0.0 | MIT | javascript-package-cataloger |
| object-inspect | 1.13.2 | MIT | javascript-package-cataloger |
| object-inspect | 1.13.4 | MIT | javascript-package-cataloger |
| oblivious-set | 1.4.0 | MIT | javascript-package-cataloger |
| on-finished | 2.3.0 | MIT | javascript-package-cataloger |
| on-finished | 2.4.1 | MIT | javascript-package-cataloger |
| on-headers | 1.1.0 | MIT | javascript-package-cataloger |
| once | 1.4.0 | ISC | javascript-package-cataloger |
| one-time | 1.0.0 | MIT | javascript-package-cataloger |
| p-cancelable | 2.1.1 | MIT | javascript-package-cataloger |
| p-finally | 1.0.0 | MIT | javascript-package-cataloger |
| p-map | 7.0.3 | MIT | javascript-package-cataloger |
| p-queue | 6.6.2 | MIT | javascript-package-cataloger |
| p-timeout | 3.2.0 | MIT | javascript-package-cataloger |
| package-json-from-dist | 1.0.1 | BlueOak-1.0.0 | javascript-package-cataloger |
| package-json-from-dist | 1.0.1 | BlueOak-1.0.0 | javascript-package-cataloger |
| pacote | 19.0.1 | ISC | javascript-package-cataloger |
| pacote | 20.0.0 | ISC | javascript-package-cataloger |
| pagent | UNKNOWN |  | pe-binary-package-cataloger |
| pako | 0.2.9 | MIT | javascript-package-cataloger |
| pako | 1.0.11 | (MIT AND Zlib) | javascript-package-cataloger |
| parse-conflict-json | 4.0.0 | ISC | javascript-package-cataloger |
| parseurl | 1.3.3 | MIT | javascript-package-cataloger |
| path-key | 3.1.1 | MIT | javascript-package-cataloger |
| path-key | 3.1.1 | MIT | javascript-package-cataloger |
| path-scurry | 1.11.1 | BlueOak-1.0.0 | javascript-package-cataloger |
| path-scurry | 1.11.1 | BlueOak-1.0.0 | javascript-package-cataloger |
| path-to-regexp | 8.2.0 | MIT | javascript-package-cataloger |
| path-to-regexp | 8.4.2 | MIT | javascript-package-cataloger |
| path-to-regexp | 8.4.2 | MIT | javascript-package-cataloger |
| peek-readable | 4.1.0 | MIT | javascript-package-cataloger |
| peek-readable | 7.0.0 | MIT | javascript-package-cataloger |
| picomatch | 4.0.2 | MIT | javascript-package-cataloger |
| pluralize | 8.0.0 | MIT | javascript-package-cataloger |
| possible-typed-array-names | 1.1.0 | MIT | javascript-package-cataloger |
| postcss-selector-parser | 7.1.0 | MIT | javascript-package-cataloger |
| prebuild-install | 7.1.1 | MIT | javascript-package-cataloger |
| prebuild-install | 7.1.2 | MIT | javascript-package-cataloger |
| proc-log | 5.0.0 | ISC | javascript-package-cataloger |
| process | 0.11.10 | MIT | javascript-package-cataloger |
| proggy | 3.0.0 | ISC | javascript-package-cataloger |
| promise-all-reject-late | 1.0.1 | ISC | javascript-package-cataloger |
| promise-call-limit | 3.0.2 | ISC | javascript-package-cataloger |
| promise-retry | 2.0.1 | MIT | javascript-package-cataloger |
| promzard | 2.0.0 | ISC | javascript-package-cataloger |
| proxy-addr | 2.0.7 | MIT | javascript-package-cataloger |
| proxy-from-env | 2.1.0 | MIT | javascript-package-cataloger |
| pump | 3.0.0 | MIT | javascript-package-cataloger |
| pvtsutils | 1.3.2 | MIT | javascript-package-cataloger |
| pvutils | 1.1.3 | MIT | javascript-package-cataloger |
| qrcode-terminal | 0.12.0 |  | javascript-package-cataloger |
| qs | 6.13.0 | BSD-3-Clause | javascript-package-cataloger |
| qs | 6.14.0 | BSD-3-Clause | javascript-package-cataloger |
| quicktype-core | 23.0.116 | Apache-2.0 | javascript-package-cataloger |
| range-parser | 1.2.1 | MIT | javascript-package-cataloger |
| raw-body | 2.5.2 | MIT | javascript-package-cataloger |
| raw-body | 3.0.2 | MIT | javascript-package-cataloger |
| raw-body | 3.0.2 | MIT | javascript-package-cataloger |
| rc | 1.2.8 | (BSD-2-Clause OR MIT OR Apache-2.0) | javascript-package-cataloger |
| read | 4.1.0 | ISC | javascript-package-cataloger |
| read-cmd-shim | 5.0.0 | ISC | javascript-package-cataloger |
| read-package-json-fast | 4.0.0 | ISC | javascript-package-cataloger |
| readable-stream | 3.6.2 | MIT | javascript-package-cataloger |
| readable-stream | 4.5.2 | MIT | javascript-package-cataloger |
| readable-web-to-node-stream | 3.0.2 | MIT | javascript-package-cataloger |
| redis | 4.6.10 | MIT | javascript-package-cataloger |
| redis-errors | 1.2.0 | MIT | javascript-package-cataloger |
| redis-parser | 3.0.0 | MIT | javascript-package-cataloger |
| redisearch | 0.0.2 |  | javascript-package-cataloger |
| redisinsight-api | 3.4.2 |  | javascript-package-cataloger |
| redistimeseries | 0.0.2 |  | javascript-package-cataloger |
| reflect-metadata | 0.1.13 | Apache-2.0 | javascript-package-cataloger |
| regenerator-runtime | 0.14.1 | MIT | javascript-package-cataloger |
| require-directory | 2.1.1 | MIT | javascript-package-cataloger |
| retry | 0.12.0 | MIT | javascript-package-cataloger |
| router | 2.2.0 | MIT | javascript-package-cataloger |
| rxjs | 7.8.1 | Apache-2.0 | javascript-package-cataloger |
| rxjs/ajax | UNKNOWN |  | javascript-package-cataloger |
| rxjs/fetch | UNKNOWN |  | javascript-package-cataloger |
| rxjs/operators | UNKNOWN |  | javascript-package-cataloger |
| rxjs/testing | UNKNOWN |  | javascript-package-cataloger |
| rxjs/webSocket | UNKNOWN |  | javascript-package-cataloger |
| safe-buffer | 5.2.1 | MIT | javascript-package-cataloger |
| safe-stable-stringify | 2.4.3 | MIT | javascript-package-cataloger |
| safer-buffer | 2.1.2 | MIT | javascript-package-cataloger |
| safer-buffer | 2.1.2 | MIT | javascript-package-cataloger |
| scanelf | 1.3.8-r2 | GPL-2.0-only | apk-db-cataloger |
| semver | 7.5.4 | ISC | javascript-package-cataloger |
| semver | 7.7.2 | ISC | javascript-package-cataloger |
| send | 1.2.0 | MIT | javascript-package-cataloger |
| serve-static | 2.2.0 | MIT | javascript-package-cataloger |
| set-function-length | 1.2.2 | MIT | javascript-package-cataloger |
| setprototypeof | 1.1.0 | ISC | javascript-package-cataloger |
| setprototypeof | 1.2.0 | ISC | javascript-package-cataloger |
| sha.js | 2.4.12 | (MIT AND BSD-3-Clause) | javascript-package-cataloger |
| shebang-command | 2.0.0 | MIT | javascript-package-cataloger |
| shebang-command | 2.0.0 | MIT | javascript-package-cataloger |
| shebang-regex | 3.0.0 | MIT | javascript-package-cataloger |
| shebang-regex | 3.0.0 | MIT | javascript-package-cataloger |
| side-channel | 1.0.6 | MIT | javascript-package-cataloger |
| side-channel | 1.1.0 | MIT | javascript-package-cataloger |
| side-channel-list | 1.0.0 | MIT | javascript-package-cataloger |
| side-channel-map | 1.0.1 | MIT | javascript-package-cataloger |
| side-channel-weakmap | 1.0.2 | MIT | javascript-package-cataloger |
| signal-exit | 4.1.0 | ISC | javascript-package-cataloger |
| signal-exit | 4.1.0 | ISC | javascript-package-cataloger |
| sigstore | 3.1.0 | Apache-2.0 | javascript-package-cataloger |
| simple-concat | 1.0.1 | MIT | javascript-package-cataloger |
| simple-get | 4.0.1 | MIT | javascript-package-cataloger |
| simple-swizzle | 0.2.2 | MIT | javascript-package-cataloger |
| smart-buffer | 4.2.0 | MIT | javascript-package-cataloger |
| socket.io | 4.8.1 | MIT | javascript-package-cataloger |
| socket.io-adapter | 2.5.5 | MIT | javascript-package-cataloger |
| socket.io-client | 4.7.5 |  | javascript-package-cataloger |
| socket.io-client | 4.7.5 |  | javascript-package-cataloger |
| socket.io-client | 4.8.1 | MIT | javascript-package-cataloger |
| socket.io-parser | 4.2.6 | MIT | javascript-package-cataloger |
| socks | 2.8.5 | MIT | javascript-package-cataloger |
| socks-proxy-agent | 8.0.5 | MIT | javascript-package-cataloger |
| source-map | 0.6.1 | BSD-3-Clause | javascript-package-cataloger |
| source-map-support | 0.5.21 | MIT | javascript-package-cataloger |
| spdx-correct | 3.2.0 | Apache-2.0 | javascript-package-cataloger |
| spdx-exceptions | 2.5.0 | CC-BY-3.0 | javascript-package-cataloger |
| spdx-expression-parse | 3.0.1 | MIT | javascript-package-cataloger |
| spdx-expression-parse | 3.0.1 | MIT | javascript-package-cataloger |
| spdx-expression-parse | 4.0.0 | MIT | javascript-package-cataloger |
| spdx-license-ids | 3.0.21 | CC0-1.0 | javascript-package-cataloger |
| sprintf-js | 1.1.3 | BSD-3-Clause | javascript-package-cataloger |
| sql-highlight | 6.1.0 | MIT | javascript-package-cataloger |
| ssh2 | 1.15.0 | MIT | javascript-package-cataloger |
| ssl_client | 1.37.0-r30 | GPL-2.0-only | apk-db-cataloger |
| ssri | 12.0.0 | ISC | javascript-package-cataloger |
| stack-trace | 0.0.10 | MIT | javascript-package-cataloger |
| standard-as-callback | 2.1.0 | MIT | javascript-package-cataloger |
| statuses | 1.5.0 | MIT | javascript-package-cataloger |
| statuses | 2.0.1 | MIT | javascript-package-cataloger |
| statuses | 2.0.1 | MIT | javascript-package-cataloger |
| statuses | 2.0.2 | MIT | javascript-package-cataloger |
| streamsearch | 1.1.0 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 5.1.2 | MIT | javascript-package-cataloger |
| string-width | 5.1.2 | MIT | javascript-package-cataloger |
| string-width | 5.1.2 | MIT | javascript-package-cataloger |
| string_decoder | 1.3.0 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 7.1.0 | MIT | javascript-package-cataloger |
| strip-ansi | 7.1.0 | MIT | javascript-package-cataloger |
| strip-ansi | 7.1.2 | MIT | javascript-package-cataloger |
| strip-json-comments | 2.0.1 | MIT | javascript-package-cataloger |
| strtok3 | 10.2.2 | MIT | javascript-package-cataloger |
| strtok3 | 6.3.0 | MIT | javascript-package-cataloger |
| supports-color | 9.4.0 | MIT | javascript-package-cataloger |
| swagger-ui-dist | 4.18.3 | Apache-2.0 | javascript-package-cataloger |
| swagger-ui-dist | 5.21.0 | Apache-2.0 | javascript-package-cataloger |
| swagger-ui-express | 4.6.2 | MIT | javascript-package-cataloger |
| tar | 6.2.1 | ISC | javascript-package-cataloger |
| tar | 7.4.3 | ISC | javascript-package-cataloger |
| tar | 7.4.3 | ISC | javascript-package-cataloger |
| tar-fs | 2.1.4 | MIT | javascript-package-cataloger |
| tar-stream | 2.2.0 | MIT | javascript-package-cataloger |
| text-hex | 1.0.0 | MIT | javascript-package-cataloger |
| text-table | 0.2.0 | MIT | javascript-package-cataloger |
| tiny-emitter | 1.1.0 | MIT | javascript-package-cataloger |
| tiny-inflate | 1.0.3 | MIT | javascript-package-cataloger |
| tiny-relative-date | 1.3.0 | MIT | javascript-package-cataloger |
| tinyglobby | 0.2.14 | MIT | javascript-package-cataloger |
| to-buffer | 1.2.1 | MIT | javascript-package-cataloger |
| toidentifier | 1.0.1 | MIT | javascript-package-cataloger |
| token-types | 4.2.1 | MIT | javascript-package-cataloger |
| token-types | 6.0.0 | MIT | javascript-package-cataloger |
| tr46 | 0.0.3 | MIT | javascript-package-cataloger |
| treeverse | 3.0.0 | ISC | javascript-package-cataloger |
| triple-beam | 1.3.0 | MIT | javascript-package-cataloger |
| ts-node | 10.9.2 | MIT | javascript-package-cataloger |
| tslib | 2.8.1 | 0BSD | javascript-package-cataloger |
| tuf-js | 3.0.1 | MIT | javascript-package-cataloger |
| tunnel-agent | 0.6.0 | Apache-2.0 | javascript-package-cataloger |
| tunnel-ssh | 5.1.2 | MIT | javascript-package-cataloger |
| tweetnacl | 0.14.5 | Unlicense | javascript-package-cataloger |
| type-is | 1.6.18 | MIT | javascript-package-cataloger |
| type-is | 2.0.1 | MIT | javascript-package-cataloger |
| type-is | 2.0.1 | MIT | javascript-package-cataloger |
| typed-array-buffer | 1.0.3 | MIT | javascript-package-cataloger |
| typedarray | 0.0.6 | MIT | javascript-package-cataloger |
| typeorm | 0.3.26 | MIT | javascript-package-cataloger |
| typescript | 4.9.5 | Apache-2.0 | javascript-package-cataloger |
| uid | 2.0.2 | MIT | javascript-package-cataloger |
| uint8array-extras | 1.4.0 | MIT | javascript-package-cataloger |
| undici-types | 5.26.5 | MIT | javascript-package-cataloger |
| undici-types | 6.19.8 | MIT | javascript-package-cataloger |
| undici-types | 7.16.0 | MIT | javascript-package-cataloger |
| unicode-properties | 1.4.1 | MIT | javascript-package-cataloger |
| unicode-trie | 2.0.0 | MIT | javascript-package-cataloger |
| unique-filename | 4.0.0 | ISC | javascript-package-cataloger |
| unique-slug | 5.0.0 | ISC | javascript-package-cataloger |
| universalify | 2.0.0 | MIT | javascript-package-cataloger |
| unload | 2.4.1 | Apache-2.0 | javascript-package-cataloger |
| unpipe | 1.0.0 | MIT | javascript-package-cataloger |
| urijs | 1.19.11 | MIT | javascript-package-cataloger |
| util-deprecate | 1.0.2 | MIT | javascript-package-cataloger |
| util-deprecate | 1.0.2 | MIT | javascript-package-cataloger |
| uuid | 11.1.0 | MIT | javascript-package-cataloger |
| uuid | 8.3.2 | MIT | javascript-package-cataloger |
| v8-compile-cache-lib | 3.0.1 | MIT | javascript-package-cataloger |
| validate-npm-package-license | 3.0.4 | Apache-2.0 | javascript-package-cataloger |
| validate-npm-package-name | 6.0.1 | ISC | javascript-package-cataloger |
| validator | 13.15.23 | MIT | javascript-package-cataloger |
| vary | 1.1.2 | MIT | javascript-package-cataloger |
| walk-up-path | 3.0.1 | ISC | javascript-package-cataloger |
| webcrypto-core | 1.7.7 | MIT | javascript-package-cataloger |
| webcrypto-shim | 0.1.7 | MIT | javascript-package-cataloger |
| webidl-conversions | 3.0.1 | BSD-2-Clause | javascript-package-cataloger |
| whatwg-url | 5.0.0 | MIT | javascript-package-cataloger |
| which | 2.0.2 | ISC | javascript-package-cataloger |
| which | 2.0.2 | ISC | javascript-package-cataloger |
| which | 5.0.0 | ISC | javascript-package-cataloger |
| which-typed-array | 1.1.19 | MIT | javascript-package-cataloger |
| winston | 3.8.2 | MIT | javascript-package-cataloger |
| winston-daily-rotate-file | 4.7.1 | MIT | javascript-package-cataloger |
| winston-transport | 4.5.0 | MIT | javascript-package-cataloger |
| wordwrap | 1.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 7.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 7.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 7.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 8.1.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 8.1.0 | MIT | javascript-package-cataloger |
| wrappy | 1.0.2 | ISC | javascript-package-cataloger |
| write-file-atomic | 6.0.0 | ISC | javascript-package-cataloger |
| ws | 8.17.1 | MIT | javascript-package-cataloger |
| xhr2 | 0.1.3 | MIT | javascript-package-cataloger |
| xmlhttprequest-ssl | 2.1.1 | MIT | javascript-package-cataloger |
| xtend | 4.0.2 | MIT | javascript-package-cataloger |
| y18n | 5.0.8 | ISC | javascript-package-cataloger |
| yallist | 4.0.0 | ISC | javascript-package-cataloger |
| yallist | 4.0.0 | ISC | javascript-package-cataloger |
| yallist | 5.0.0 | BlueOak-1.0.0 | javascript-package-cataloger |
| yallist | 5.0.0 | BlueOak-1.0.0 | javascript-package-cataloger |
| yaml | 2.8.3 | ISC | javascript-package-cataloger |
| yargs | 17.7.2 | MIT | javascript-package-cataloger |
| yargs-parser | 21.1.1 | ISC | javascript-package-cataloger |
| yarn | 1.22.22 | BSD-2-Clause | javascript-package-cataloger |
| yn | 3.1.1 | MIT | javascript-package-cataloger |
| zlib | 1.3.1-r2 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/gotenberg

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| adduser | 3.152 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| adwaita-icon-theme | 48.1-1 | CC-BY-3.0-US, CC-BY-SA-3.0, CC-BY-SA-4.0, GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only | dpkg-db-cataloger |
| apt | 3.0.3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, curl | dpkg-db-cataloger |
| at-spi2-common | 2.56.2-1+deb13u1 | AFL-2.1, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| autoconf | 2.72-3.1 | GFDL-1.3-only, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| automake | 1:1.17-4 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| autotools-dev | 20240727.1 | GPL-3.0-only | dpkg-db-cataloger |
| backports-tarfile | 1.2.0 |  | python-installed-package-cataloger |
| base-files | 13.8+deb13u4 | GPL-2.0-or-later | dpkg-db-cataloger |
| base-passwd | 3.6.7 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.37-2+b8 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| bsdutils | 1:2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| ca-certificates | 20250419 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| chromium | 147.0.7727.116-1~deb13u1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, BSL-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, ICU, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT, MPL-1.1, MPL-2.0, MS-PL, Zlib | dpkg-db-cataloger |
| chromium-common | 147.0.7727.116-1~deb13u1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, BSL-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, ICU, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT, MPL-1.1, MPL-2.0, MS-PL, Zlib | dpkg-db-cataloger |
| coinor-libcbc3.1 | 2.10.12+ds-1 | EPL-1.0, EPL-2.0, FSFUL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only | dpkg-db-cataloger |
| coinor-libcgl1 | 0.60.9+ds-1 | EPL-1.0, EPL-2.0, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, X11 | dpkg-db-cataloger |
| coinor-libclp1 | 1.17.10+ds-1 | EPL-1.0, EPL-2.0, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, X11 | dpkg-db-cataloger |
| coinor-libcoinmp0 | 1.8.4+dfsg-2 | CPL-1.0, EPL-1.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| coinor-libcoinutils3v5 | 2.11.11+ds-5 | EPL-1.0, GPL-3.0-only | dpkg-db-cataloger |
| coinor-libosi1v5 | 0.108.10+ds-2 | EPL-1.0, EPL-2.0, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, X11 | dpkg-db-cataloger |
| commons-lang3 | 3.12.0 |  | java-archive-cataloger |
| coreutils | 9.7-3 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| curl | 8.19.0-1~bpo13+1 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| dash | 0.5.12-12 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dbus | 1.16.2-2 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-bin | 1.16.2-2 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-daemon | 1.16.2-2 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-session-bus-common | 1.16.2-2 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-system-bus-common | 1.16.2-2 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-user-session | 1.16.2-2 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dconf-gsettings-backend | 0.40.0-5 | GPL-3.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| dconf-service | 0.40.0-5 | GPL-3.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.91 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2025.1 |  | dpkg-db-cataloger |
| debianutils | 5.23.2 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| dictionaries-common | 1.30.10 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| diffutils | 1:3.10-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dirmngr | 2.4.7-21+deb13u1+b2 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| dpkg | 1.22.22 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| emacsen-common | 3.0.8 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| file | 1:5.46-5 | BSD-2-Clause | dpkg-db-cataloger |
| findutils | 4.10.0-3 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| fontconfig | 2.15.0-2.3 | HPND-sell-variant | dpkg-db-cataloger |
| fontconfig-config | 2.15.0-2.3 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-arphic-uming | 0.2.20080216.2-11 | GPL-2.0-only | dpkg-db-cataloger |
| fonts-beng | 2:1.3 | ISC | dpkg-db-cataloger |
| fonts-beng-extra | 3.6.0-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only | dpkg-db-cataloger |
| fonts-cantarell | 0.303.1-4 | CC0-1.0, OFL-1.1 | dpkg-db-cataloger |
| fonts-comic-neue | 2.51-4 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-courier-prime | 0+git20190115-4 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-crosextra-caladea | 20200211-2 | Apache-2.0, OFL-1.1 | dpkg-db-cataloger |
| fonts-crosextra-carlito | 20230309-2 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-dejavu | 2.37-8 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-8 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-dejavu-extra | 2.37-8 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-dejavu-mono | 2.37-8 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-deva | 2:1.4 | ISC | dpkg-db-cataloger |
| fonts-deva-extra | 3.0-6 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-dzongkha | 0.3-9 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.0 | dpkg-db-cataloger |
| fonts-firacode | 6.2-2 | OFL-1.1 | dpkg-db-cataloger |
| fonts-freefont-otf | 20211204+svn4273-2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-gargi | 2.0-6 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-gubbi | 1.3-7 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-gujr | 2:1.5 | ISC | dpkg-db-cataloger |
| fonts-gujr-extra | 1.0.1-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-guru | 2:1.3 | ISC | dpkg-db-cataloger |
| fonts-guru-extra | 2.0-5 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-indic | 2:1.4 | ISC | dpkg-db-cataloger |
| fonts-kalapi | 1.0-5 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-knda | 2:1.3.1 | ISC | dpkg-db-cataloger |
| fonts-league-spartan | 2.210-2 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-liberation | 1:2.1.5-3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-liberation2 | 1:2.1.5-3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-lohit-beng-assamese | 2.91.5-2 | CC0-1.0, ISC, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-beng-bengali | 2.91.5-3 | CC0-1.0, ISC, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-deva | 2.95.4-5 | CC0-1.0, ISC, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-gujr | 2.92.4-4 | CC0-1.0, ISC, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-guru | 2.91.2-3 | CC0-1.0, ISC, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-knda | 2.5.4-3 | CC0-1.0, ISC, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-mlym | 2.92.2-2 | CC0-1.0, ISC, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-orya | 2.91.2-2 | CC0-1.0, ISC, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-taml | 2.91.3-2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-taml-classical | 2.5.4-2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-lohit-telu | 2.5.5-2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-mlym | 2:1.3 | ISC | dpkg-db-cataloger |
| fonts-nakula | 1.0-4 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-navilu | 1.2-4 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-noto-cjk | 1:20240730+repack1-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-noto-cjk-extra | 1:20240730+repack1-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-noto-color-emoji | 2.051-0+deb13u1 | Apache-2.0 | dpkg-db-cataloger |
| fonts-noto-core | 20201225-2 | GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-noto-mono | 20201225-2 | GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-opensymbol | 4:102.12+LibO26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| fonts-orya | 2:1.3 | ISC | dpkg-db-cataloger |
| fonts-orya-extra | 2.0-6 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-pagul | 1.0-9 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-recommended | 2 |  | dpkg-db-cataloger |
| fonts-sahadeva | 1.0-5 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-samyak-deva | 1.2.2-6 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-samyak-gujr | 1.2.2-6 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-samyak-mlym | 1.2.2-6 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-samyak-taml | 1.2.2-6 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-sil-annapurna | 2.000-2 | OFL-1.1 | dpkg-db-cataloger |
| fonts-smc | 1:7.5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-smc-anjalioldlipi | 7.1.2-2 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-chilanka | 1.540-2 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-dyuthi | 3.0.2-2 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-gayathri | 1.200-1 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-karumbi | 1.1.2-2 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-keraleeyam | 3.0.2-2 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-manjari | 2.200-1 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-meera | 7.0.3-1 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-rachana | 7.0.2-1 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-smc-raghumalayalamsans | 2.2.1-1 | CC0-1.0, GPL-2.0-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-smc-suruma | 3.2.3-1 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-smc-uroob | 2.0.2-1 | CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-symbola | 2.60-2 |  | dpkg-db-cataloger |
| fonts-taml | 2:1.4 | ISC | dpkg-db-cataloger |
| fonts-telu | 2:1.3 | ISC | dpkg-db-cataloger |
| fonts-telu-extra | 2.0-6 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-teluguvijayam | 2.1-1 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-unfonts-core | 1:1.0.2-080608-19 | CC0-1.0, GPL-2.0-only | dpkg-db-cataloger |
| fonts-urw-base35 | 20200910-8 | AGPL-3.0-only, CC-BY-4.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-wqy-zenhei | 0.9.45-8 | GPL-2.0-only | dpkg-db-cataloger |
| fonts-yrsa-rasa | 2.005-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| gcc-14-base | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| gettext | 0.23.1-2 | GFDL-1.2-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| gettext | UNKNOWN |  | java-archive-cataloger |
| gettext-base | 0.23.1-2 | GFDL-1.2-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| github.com/STARRY-S/zip | v0.2.3 |  | go-module-binary-cataloger |
| github.com/alexliesenfeld/health | v0.8.1 |  | go-module-binary-cataloger |
| github.com/andybalholm/brotli | v1.2.1 |  | go-module-binary-cataloger |
| github.com/aymerick/douceur | v0.2.0 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/bodgit/plumbing | v1.3.0 |  | go-module-binary-cataloger |
| github.com/bodgit/sevenzip | v1.6.1 |  | go-module-binary-cataloger |
| github.com/bodgit/windows | v1.0.1 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.3 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/chromedp/cdproto | v0.0.0-20250803210736-d308e07a266d |  | go-module-binary-cataloger |
| github.com/chromedp/chromedp | v0.14.2 |  | go-module-binary-cataloger |
| github.com/chromedp/sysutil | v1.1.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/uax29/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/dlclark/regexp2 | v1.12.0 |  | go-module-binary-cataloger |
| github.com/dsnet/compress | v0.0.2-0.20230904184137-39efe44ab707 |  | go-module-binary-cataloger |
| github.com/go-json-experiment/json | v0.0.0-20260214004413-d219187c3433 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/gobwas/httphead | v0.1.0 |  | go-module-binary-cataloger |
| github.com/gobwas/pool | v0.2.1 |  | go-module-binary-cataloger |
| github.com/gobwas/ws | v1.4.0 |  | go-module-binary-cataloger |
| github.com/gomarkdown/markdown | v0.0.0-20260412113850-134a5b2cce7f |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/gorilla/css | v1.0.1 |  | go-module-binary-cataloger |
| github.com/gotenberg/gotenberg/v8 | v8.32.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.28.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.8 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru/v2 | v2.0.7 |  | go-module-binary-cataloger |
| github.com/hhrutter/lzw | v1.0.0 |  | go-module-binary-cataloger |
| github.com/hhrutter/pkcs7 | v0.2.2 |  | go-module-binary-cataloger |
| github.com/hhrutter/tiff | v1.0.3 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.5 |  | go-module-binary-cataloger |
| github.com/klauspost/pgzip | v1.2.6 |  | go-module-binary-cataloger |
| github.com/labstack/echo/v4 | v4.15.1 |  | go-module-binary-cataloger |
| github.com/labstack/gommon | v0.5.0 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.21 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.23 |  | go-module-binary-cataloger |
| github.com/mholt/archives | v0.1.5 |  | go-module-binary-cataloger |
| github.com/microcosm-cc/bluemonday | v1.0.27 |  | go-module-binary-cataloger |
| github.com/mikelolasagasti/xz | v1.0.1 |  | go-module-binary-cataloger |
| github.com/minio/minlz | v1.1.0 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/nwaples/rardecode/v2 | v2.2.2 |  | go-module-binary-cataloger |
| github.com/pdfcpu/pdfcpu | v0.12.0 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.26 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.5 |  | go-module-binary-cataloger |
| github.com/prometheus/otlptranslator | v1.0.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.20.1 |  | go-module-binary-cataloger |
| github.com/shirou/gopsutil/v4 | v4.26.3 |  | go-module-binary-cataloger |
| github.com/sorairolake/lzip-go | v0.3.8 |  | go-module-binary-cataloger |
| github.com/spf13/afero | v1.15.0 |  | go-module-binary-cataloger |
| github.com/spf13/cobra | v1.10.2 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/tklauser/go-sysconf | v0.3.16 |  | go-module-binary-cataloger |
| github.com/tklauser/numcpus | v0.11.0 |  | go-module-binary-cataloger |
| github.com/ulikunitz/xz | v0.5.15 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/valyala/fasttemplate | v1.2.2 |  | go-module-binary-cataloger |
| gnupg | 2.4.7-21+deb13u1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-l10n | 2.4.7-21+deb13u1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| go.opentelemetry.io/auto/sdk | v1.2.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/bridges/otelslog | v0.18.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/bridges/prometheus | v0.68.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/exporters/autoexport | v0.68.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/prometheus | v0.65.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/stdout/stdoutlog | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/stdout/stdoutmetric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/stdout/stdouttrace | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/log | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/log | v0.19.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/metric | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.43.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.10.0 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.4 |  | go-module-binary-cataloger |
| go4.org | v0.0.0-20260112195520-a5071408f32f |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.50.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.50.0 |  | go-module-binary-cataloger |
| golang.org/x/image | v0.39.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.53.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.43.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.42.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.15.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20260406210006-6f92a3bedf2d |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20260406210006-6f92a3bedf2d |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.80.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gpg | 2.4.7-21+deb13u1+b2 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.4.7-21+deb13u1+b2 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.4.7-21+deb13u1+b2 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.4.7-21+deb13u1+b2 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.11-4 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gtk-update-icon-cache | 4.18.6+ds-2 | Apache-2.0, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Unicode-DFS-2016, ZPL-2.1 | dpkg-db-cataloger |
| gzip | 1.13-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hicolor-icon-theme | 0.18-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| hostname | 3.25 | GPL-2.0-only | dpkg-db-cataloger |
| hyphen-af | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-as | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-be | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-bg | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-bn | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-ca | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-cs | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-da | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-de | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-el | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-en-gb | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-en-us | 2.8.8-7 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1+ | dpkg-db-cataloger |
| hyphen-eo | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-es | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-fr | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-gl | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-gu | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-hi | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-hr | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-hu | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-id | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-is | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-it | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-kn | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-lt | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-lv | 1.4.0-5 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| hyphen-ml | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-mn | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-mr | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-nl | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-no | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-or | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-pa | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-pl | 1:3.0a-4.4 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| hyphen-pt-br | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-pt-pt | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-ro | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-ru | 20030310-1.2 | LPPL-1.2 | dpkg-db-cataloger |
| hyphen-sk | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-sl | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-sr | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-sv | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-ta | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-te | 0.9.0-2 |  | dpkg-db-cataloger |
| hyphen-th | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-uk | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| hyphen-zu | 1:25.2.3-1 | AGPL-3.0-or-later, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-SA-1.0, CC0-1.0, GFDL-1.1-or-later, GFDL-1.2-only, GFDL-1.2-or-later, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, MPL-1.1+, MPL-2.0, MPL-2.0+, SISSL | dpkg-db-cataloger |
| importlib-metadata | 8.0.0 |  | python-installed-package-cataloger |
| inflect | 7.3.1 |  | python-installed-package-cataloger |
| inflect | 7.3.1 |  | python-installed-package-cataloger |
| init-system-helpers | 1.69~deb13u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| intltool | 0.51.0-7 | GPL-2.0-only | dpkg-db-cataloger |
| iso-codes | 4.18.0-1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| jaraco-collections | 5.1.0 |  | python-installed-package-cataloger |
| jaraco-context | 5.3.0 |  | python-installed-package-cataloger |
| jaraco-context | 6.0.1 |  | python-installed-package-cataloger |
| jaraco-functools | 4.0.1 |  | python-installed-package-cataloger |
| jaraco-functools | 4.1.0 |  | python-installed-package-cataloger |
| jaraco-text | 3.12.1 |  | python-installed-package-cataloger |
| jaraco-text | 4.0.0 |  | python-installed-package-cataloger |
| jrt-fs | 21.0.11 |  | java-archive-cataloger |
| libabsl20240722 | 20240722.0-4 | Apache-2.0 | dpkg-db-cataloger |
| libabw-0.1-1 | 0.1.3-1+b2 | GPL-3.0-only, LGPL-3.0-only, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libacl1 | 2.3.2-2+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapparmor1 | 4.1.0-1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libapt-pkg7.0 | 3.0.3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, curl | dpkg-db-cataloger |
| libargon2-1 | 0~20190702+dfsg-4+b2 | Apache-2.0 | dpkg-db-cataloger |
| libasound2-data | 1.2.14-1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libasound2t64 | 1.2.14-1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libassuan9 | 3.0.2-2 | FSFULLR, FSFULLRWD, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| libasyncns0 | 0.8-6+b5 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libatk-bridge2.0-0t64 | 2.56.2-1+deb13u1 | AFL-2.1, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libatk1.0-0t64 | 2.56.2-1+deb13u1 | AFL-2.1, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libatomic1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libatspi2.0-0t64 | 2.56.2-1+deb13u1 | AFL-2.1, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libattr1 | 1:2.5.2-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:4.0.2-2 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:4.0.2-2+b2 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavahi-client3 | 0.8-16 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavahi-common-data | 0.8-16 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libavahi-common3 | 0.8-16 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblas3 | 3.12.1-6 | BSD-3-Clause | dpkg-db-cataloger |
| libblkid1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libboost-iostreams1.83.0 | 1.83.0-4.2 | Apache-2.0, BSL-1.0, Jam, MIT, Zlib | dpkg-db-cataloger |
| libboost-locale1.83.0 | 1.83.0-4.2 | Apache-2.0, BSL-1.0, Jam, MIT, Zlib | dpkg-db-cataloger |
| libboost-thread1.83.0 | 1.83.0-4.2 | Apache-2.0, BSL-1.0, Jam, MIT, Zlib | dpkg-db-cataloger |
| libbox2d2 | 2.4.1-3+b3 | Apache-2.0, Zlib | dpkg-db-cataloger |
| libbrotli1 | 1.1.0-2+b7 | MIT | dpkg-db-cataloger |
| libbsd0 | 0.12.2-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-6 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.41-12+deb13u2 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libc6 | 2.41-12+deb13u2 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libcairo-gobject2 | 1.18.4-1+b1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2 | 1.18.4-1+b1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.5-4+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.75-10+b8 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcap2-bin | 1:2.75-10+b8 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcdr-0.1-1 | 0.1.7-1+b3 | MPL-2.0 | dpkg-db-cataloger |
| libclone-perl | 0.47-1+b1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libcloudproviders0 | 0.3.6-2 | LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libclucene-contribs1t64 | 2.3.3.4+dfsg-1.2+b1 | Apache-2.0, LGPL-2.1-only | dpkg-db-cataloger |
| libclucene-core1t64 | 2.3.3.4+dfsg-1.2+b1 | Apache-2.0, LGPL-2.1-only | dpkg-db-cataloger |
| libcmis-0.6-6t64 | 0.6.2-2.1+b1 |  | dpkg-db-cataloger |
| libcolamd3 | 1:7.10.1+dfsg-1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, LPPL-1.0+, LPPL-1.3c+ | dpkg-db-cataloger |
| libcolord2 | 1.4.7-3 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.2-3+b10 | 0BSD, Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.38-1 |  | dpkg-db-cataloger |
| libcups2t64 | 2.4.10-3+deb13u2 | Apache-2.0, BSD-2-Clause, FSFUL, Zlib | dpkg-db-cataloger |
| libcurl3t64-gnutls | 8.19.0-1~bpo13+1 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4t64 | 8.19.0-1~bpo13+1 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libdatrie1 | 0.2.13-3+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libdav1d7 | 1.5.1-1 | BSD-2-Clause, ISC | dpkg-db-cataloger |
| libdb5.3t64 | 5.3.28+dfsg2-9 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdbus-1-3 | 1.16.2-2 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libdconf1 | 0.40.0-5 | GPL-3.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libdebconfclient0 | 0.280 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdeflate0 | 1.23-2 |  | dpkg-db-cataloger |
| libdouble-conversion3 | 3.3.1-1 | BSD-3-Clause | dpkg-db-cataloger |
| libdrm-amdgpu1 | 2.4.124-2 |  | dpkg-db-cataloger |
| libdrm-common | 2.4.124-2 |  | dpkg-db-cataloger |
| libdrm-intel1 | 2.4.124-2 |  | dpkg-db-cataloger |
| libdrm2 | 2.4.124-2 |  | dpkg-db-cataloger |
| libe-book-0.1-1 | 0.1.3-2+b4 | MPL-2.0 | dpkg-db-cataloger |
| libedit2 | 3.1-20250104-1 | BSD-3-Clause | dpkg-db-cataloger |
| libelf1t64 | 0.192-4 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libencode-locale-perl | 1.05-3 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libeot0 | 0.01-5+b2 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| libepoxy0 | 1.5.10-2 |  | dpkg-db-cataloger |
| libepubgen-0.1-1 | 0.1.1-1+b2 | MPL-2.0 | dpkg-db-cataloger |
| libetonyek-0.1-1 | 0.1.12-1 |  | dpkg-db-cataloger |
| libexpat1 | 2.7.1-2 | MIT | dpkg-db-cataloger |
| libexttextcat-2.0-0 | 3.4.7-1+b1 | BSD-3-Clause | dpkg-db-cataloger |
| libexttextcat-data | 3.4.7-1 | BSD-3-Clause | dpkg-db-cataloger |
| libffi8 | 3.4.8-2 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libfile-listing-perl | 6.16-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libflac14 | 1.5.0+ds-2 | BSD-3-Clause, GFDL-1.1-or-later, GFDL-1.2-only, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libfontconfig1 | 2.15.0-2.3 | HPND-sell-variant | dpkg-db-cataloger |
| libfontenc1 | 1:1.1.8-1+b2 | MIT | dpkg-db-cataloger |
| libfreehand-0.1-1 | 0.1.2-3 | GPL-3.0-only, LGPL-3.0-only, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libfreetype6 | 2.13.3+dfsg-1+deb13u1 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT-Modern-Variant, Zlib | dpkg-db-cataloger |
| libfribidi0 | 1.0.16-1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgbm1 | 25.0.7-2 | Apache-2.0, BSD-2-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| libgcc-s1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.11.0-7 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm-compat4t64 | 1.24-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6t64 | 1.24-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdk-pixbuf-2.0-0 | 2.42.12+dfsg-4+deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf2.0-common | 2.42.12+dfsg-4+deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgfortran5 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgl1 | 1.7.0-1+b2 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libgl1-mesa-dri | 25.0.7-2 | Apache-2.0, BSD-2-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| libglib2.0-0t64 | 2.84.4-3~deb13u2 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglvnd0 | 1.7.0-1+b2 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libglx-mesa0 | 25.0.7-2 | Apache-2.0, BSD-2-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| libglx0 | 1.7.0-1+b2 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libgmp10 | 2:6.3.0+dfsg-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30t64 | 3.8.9-3+deb13u2 | Apache-2.0, BSD-3-Clause, FSFAP, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.51-4 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgpgme11t64 | 1.24.2-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgpgmepp6t64 | 1.24.2-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgraphite2-3 | 1.3.14-2+b1 | GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.21.3-5 | GPL-2.0-only | dpkg-db-cataloger |
| libgstreamer-plugins-base1.0-0 | 1.26.2-1+deb13u1 | BSD-3-Clause, CC-BY-SA-4.0, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgstreamer1.0-0 | 1.26.2-2 | CC-BY-SA-4.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-2.0 | dpkg-db-cataloger |
| libgtk-3-0t64 | 3.24.49-3 | Apache-2.0, CC-BY-SA-4.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, SWL, ZPL-2.1 | dpkg-db-cataloger |
| libgtk-3-common | 3.24.49-3 | Apache-2.0, CC-BY-SA-4.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, SWL, ZPL-2.1 | dpkg-db-cataloger |
| libharfbuzz-icu0 | 10.2.0-1+b1 | Apache-2.0, CC0-1.0, FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, MIT, OFL-1.1 | dpkg-db-cataloger |
| libharfbuzz-subset0 | 10.2.0-1+b1 | Apache-2.0, CC0-1.0, FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, MIT, OFL-1.1 | dpkg-db-cataloger |
| libharfbuzz0b | 10.2.0-1+b1 | Apache-2.0, CC0-1.0, FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, MIT, OFL-1.1 | dpkg-db-cataloger |
| libhogweed6t64 | 3.10.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libhtml-parser-perl | 3.83-1+b2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libhtml-tagset-perl | 3.24-1 | Artistic-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libhtml-tree-perl | 5.07-3 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libhttp-cookies-perl | 6.11-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libhttp-date-perl | 6.06-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libhttp-message-perl | 7.00-2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libhttp-negotiate-perl | 6.01-2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libhunspell-1.7-0 | 1.7.2+really1.7.2-10+b4 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libhyphen0 | 2.8.8-7+b2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1+ | dpkg-db-cataloger |
| libice6 | 2:1.1.1-1 |  | dpkg-db-cataloger |
| libicu76 | 76.1-4 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn2-0 | 2.3.8-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libimage-exiftool-perl | 13.25+dfsg-1 | CC-BY-4.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libintl | 0.23.1 |  | java-archive-cataloger |
| libio-html-perl | 1.004-3 | GPL-1.0-only, GPL-1.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libio-socket-ssl-perl | 2.089-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libjbig0 | 2.1-6.1+b2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libjpeg62-turbo | 1:2.1.5-4 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libk5crypto3 | 1.21.3-5 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-6 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.21.3-5 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.21.3-5 | GPL-2.0-only | dpkg-db-cataloger |
| libksba8 | 1.6.7-2+b1 | FSFUL, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblangtag-common | 0.6.7-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblangtag1 | 0.6.7-1+b2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblapack3 | 3.12.1-6 | BSD-3-Clause | dpkg-db-cataloger |
| liblastlog2-2 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| liblcms2-2 | 2.16-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| libldap2 | 2.6.10+dfsg-1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| liblerc4 | 4.0.0+ds-5 | Apache-2.0 | dpkg-db-cataloger |
| libllvm19 | 1:19.1.7-3+b1 | Apache-2.0, BSD-3-Clause, BSD-3-Clause, MIT | dpkg-db-cataloger |
| libltdl7 | 2.5.4-4 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblwp-mediatypes-perl | 6.04-2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| liblwp-protocol-https-perl | 6.14-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| liblz4-1 | 1.10.0-4 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.8.1-1 | 0BSD, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmagic-mgc | 1:5.46-5 | BSD-2-Clause | dpkg-db-cataloger |
| libmagic1t64 | 1:5.46-5 | BSD-2-Clause | dpkg-db-cataloger |
| libmd0 | 1.1.0-2+b1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmd4c0 | 0.5.2-2+b1 | BSD-2-Clause, CC-BY-SA-4.0 | dpkg-db-cataloger |
| libmhash2 | 0.9.9.9-10 | LGPL-2.0-only | dpkg-db-cataloger |
| libminizip1t64 | 1:1.3.dfsg+really1.3.1-1+b1 | Zlib | dpkg-db-cataloger |
| libmount1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmp3lame0 | 3.100-6+b3 | BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmpg123-0t64 | 1.32.10-1+deb13u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libmspub-0.1-1 | 0.1.4-3+b5 | MPL-2.0 | dpkg-db-cataloger |
| libmwaw-0.3-3 | 0.3.22-1+b2 | MPL-2.0 | dpkg-db-cataloger |
| libmythes-1.2-0 | 2:1.2.5-1+b2 |  | dpkg-db-cataloger |
| libncursesw6 | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnet-http-perl | 6.23-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libnet-ssleay-perl | 1.94-3 | Artistic-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libnettle8t64 | 3.10.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.64.0-1.1 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnghttp3-9 | 1.12.0-1~bpo13+1 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libngtcp2-16 | 1.22.1-1~bpo13+1 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libngtcp2-crypto-gnutls8 | 1.22.1-1~bpo13+1 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libngtcp2-crypto-ossl0 | 1.22.1-1~bpo13+1 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libnpth0t64 | 1.8-3 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnspr4 | 2:4.36-1 | MPL-2.0 | dpkg-db-cataloger |
| libnss3 | 2:3.110-1+deb13u1 | MPL-2.0, Zlib | dpkg-db-cataloger |
| libnumbertext-1.0-0 | 1.0.11-4+b2 | BSD-3-Clause, CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnumbertext-data | 1.0.11-4 | BSD-3-Clause, CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libodfgen-0.1-1 | 0.1.8-2+b2 | MPL-2.0 | dpkg-db-cataloger |
| libogg0 | 1.3.5-3+b2 | BSD-3-Clause | dpkg-db-cataloger |
| libopenh264-8 | 2.6.0+dfsg-2 | Apache-2.0, BSD-2-Clause, MPL-2.0 | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.3-2.1~deb13u1 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libopus0 | 1.5.2-2 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| liborc-0.4-0t64 | 1:0.4.41-1 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| liborcus-0.21-0 | 0.21.0-4~bpo13+1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, MPL-2.0 | dpkg-db-cataloger |
| liborcus-parser-0.21-0 | 0.21.0-4~bpo13+1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, MPL-2.0 | dpkg-db-cataloger |
| libp11-kit0 | 0.25.5-3 | Apache-2.0, BSD-3-Clause, FSFAP, FSFULLR, GPL-2.0-or-later, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, X11 | dpkg-db-cataloger |
| libpagemaker-0.0-0 | 0.0.4-1+b2 | MPL-2.0 | dpkg-db-cataloger |
| libpam-modules | 1.7.0-5 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.7.0-5 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.7.0-5 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-systemd | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam0g | 1.7.0-5 | BSD-3-Clause, Beerware, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpango-1.0-0 | 1.56.3-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangocairo-1.0-0 | 1.56.3-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangoft2-1.0-0 | 1.56.3-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpciaccess0 | 0.17-3+b3 |  | dpkg-db-cataloger |
| libpcre2-8-0 | 10.46-1~deb13u1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libperl5.40 | 5.40.1-6 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| libpixman-1-0 | 0.44.0-3 |  | dpkg-db-cataloger |
| libpng16-16t64 | 1.6.48-1+deb13u4 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpoppler147 | 25.03.0-5+deb13u2 | Apache-2.0, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.4-9 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpsl5t64 | 0.21.2-1.1+b1 | MIT | dpkg-db-cataloger |
| libpulse0 | 17.0+dfsg1-2+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpython3-stdlib | 3.13.5-1 |  | dpkg-db-cataloger |
| libpython3.13 | 3.13.5-2 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.13-minimal | 3.13.5-2 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.13-stdlib | 3.13.5-2 | GPL-2.0-only | dpkg-db-cataloger |
| libqpdf30 | 12.2.0-1 | Apache-2.0 | dpkg-db-cataloger |
| libqxp-0.0-0 | 0.0.2-1+b4 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| libraptor2-0 | 2.0.16-6 | Apache-2.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| librasqal3t64 | 0.9.33-2.1+b2 | Apache-2.0, Apache-2.0+, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| librdf0t64 | 1.0.17-4+b1 | Apache-2.0, LGPL-2.1-only | dpkg-db-cataloger |
| libreadline8t64 | 8.2-6 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libreoffice-base-core | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-calc | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-common | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-core | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-draw | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-impress | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-style-colibre | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-calc | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-common | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-draw | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-impress | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-writer | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-writer | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| librevenge-0.0-0 | 0.0.5-3+b2 | LGPL-2.1-only, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| librtmp1 | 2.4+20151223.gitfa8646d.1-2+b5 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsasl2-2 | 2.1.28+dfsg1-9 | BSD-2-Clause, BSD-3-Clause-Attribution, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.28+dfsg1-9 | BSD-2-Clause, BSD-3-Clause-Attribution, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, RSA-MD | dpkg-db-cataloger |
| libseccomp2 | 2.6.0-2 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.8.1-1 | GPL-2.0-only | dpkg-db-cataloger |
| libsemanage-common | 3.8.1-1 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsemanage2 | 3.8.1-1 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsensors-config | 1:3.6.2-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Linux-man-pages-copyleft | dpkg-db-cataloger |
| libsensors5 | 1:3.6.2-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Linux-man-pages-copyleft | dpkg-db-cataloger |
| libsepol2 | 3.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsharpyuv0 | 1.5.0-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libsm6 | 2:1.2.6-1 |  | dpkg-db-cataloger |
| libsmartcols1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libsndfile1 | 1.2.2-2+deb13u1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, NTP | dpkg-db-cataloger |
| libsqlite3-0 | 3.46.1-7+deb13u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libssh2-1t64 | 1.11.1-1 | ISC | dpkg-db-cataloger |
| libssl3t64 | 3.5.5-1~deb13u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstaroffice-0.0-0 | 0.0.7-1+b2 | MPL-2.0 | dpkg-db-cataloger |
| libstdc++6 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libsuitesparseconfig7 | 1:7.10.1+dfsg-1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, LPPL-1.0+, LPPL-1.3c+ | dpkg-db-cataloger |
| libsystemd-shared | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsystemd0 | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.20.0-2 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtext-charwidth-perl | 0.04-11+b4 | GPL-1.0-or-later | dpkg-db-cataloger |
| libtext-iconv-perl | 1.7-8+b4 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libtext-wrapi18n-perl | 0.06-10 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libthai-data | 0.1.29-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libthai0 | 0.1.29-2+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtiff6 | 4.7.0-3+deb13u2 |  | dpkg-db-cataloger |
| libtimedate-perl | 2.3300-2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libtinfo6 | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtry-tiny-perl | 0.32-1 |  | dpkg-db-cataloger |
| libudev1 | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring5 | 1.3-2 | BSD-3-Clause, GFDL-1.2-or-later, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, X11, BSD-3-Clause, GFDL-1.2-or-later, GFDL-1.3-or-later, ISC, Unicode-DFS-2016 | dpkg-db-cataloger |
| libuno-cppu3t64 | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libuno-cppuhelpergcc3-3t64 | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libuno-purpenvhelpergcc3-3t64 | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libuno-sal3t64 | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libuno-salhelpergcc3-3t64 | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| liburi-perl | 5.30-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libuuid1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libvisio-0.1-1 | 0.1.7-1+b5 | MIT, MPL-2.0 | dpkg-db-cataloger |
| libvorbis0a | 1.3.7-3 | BSD-3-Clause | dpkg-db-cataloger |
| libvorbisenc2 | 1.3.7-3 | BSD-3-Clause | dpkg-db-cataloger |
| libvulkan1 | 1.4.309.0-1 | Apache-2.0, MIT | dpkg-db-cataloger |
| libwayland-client0 | 1.23.1-3 | X11 | dpkg-db-cataloger |
| libwayland-cursor0 | 1.23.1-3 | X11 | dpkg-db-cataloger |
| libwayland-egl1 | 1.23.1-3 | X11 | dpkg-db-cataloger |
| libwayland-server0 | 1.23.1-3 | X11 | dpkg-db-cataloger |
| libwebp7 | 1.5.0-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libwpd-0.10-10 | 0.10.3-2+b2 | MPL-2.0 | dpkg-db-cataloger |
| libwpg-0.3-3 | 0.3.4-3+b2 |  | dpkg-db-cataloger |
| libwps-0.4-4 | 0.4.14-2+b2 | LGPL-2.1-only, LGPL-2.1-or-later, MPL-2.0 | dpkg-db-cataloger |
| libwww-perl | 6.78-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libwww-robotrules-perl | 6.02-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libx11-6 | 2:1.8.12-1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.8.12-1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-xcb1 | 2:1.8.12-1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxau6 | 1:1.0.11-1 |  | dpkg-db-cataloger |
| libxaw7 | 2:1.0.16-1 | HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxcb-dri3-0 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb-glx0 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb-present0 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb-randr0 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb-render0 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb-shape0 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb-shm0 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb-sync1 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb-xfixes0 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcb1 | 1.17.0-2+b1 |  | dpkg-db-cataloger |
| libxcomposite1 | 1:0.4.6-1 | HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxcursor1 | 1:1.2.3-1 | HPND-sell-variant | dpkg-db-cataloger |
| libxdamage1 | 1:1.1.6-1+b2 | HPND-sell-variant | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.5-1 |  | dpkg-db-cataloger |
| libxext6 | 2:1.3.4-1+b3 |  | dpkg-db-cataloger |
| libxfixes3 | 1:6.0.0-2+b4 | HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxft2 | 2.3.6-1+b4 | HPND-sell-variant | dpkg-db-cataloger |
| libxi6 | 2:1.8.2-1 |  | dpkg-db-cataloger |
| libxinerama1 | 2:1.1.4-3+b4 |  | dpkg-db-cataloger |
| libxkbcommon0 | 1.7.0-2 |  | dpkg-db-cataloger |
| libxkbfile1 | 1:1.1.0-1+b4 |  | dpkg-db-cataloger |
| libxml-parser-perl | 2.47-2~deb13u1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libxml2 | 2.12.7+dfsg+really2.9.14-2.1+deb13u2 | ISC | dpkg-db-cataloger |
| libxmlsec1t64 | 1.2.41-1+b1 |  | dpkg-db-cataloger |
| libxmlsec1t64-nss | 1.2.41-1+b1 |  | dpkg-db-cataloger |
| libxmu6 | 2:1.1.3-3+b4 |  | dpkg-db-cataloger |
| libxmuu1 | 2:1.1.3-3+b4 |  | dpkg-db-cataloger |
| libxnvctrl0 | 535.171.04-1+b2 | GPL-2.0-only | dpkg-db-cataloger |
| libxpm4 | 1:3.5.17-1+b3 | MIT | dpkg-db-cataloger |
| libxrandr2 | 2:1.5.4-1+b3 | HPND-sell-variant | dpkg-db-cataloger |
| libxrender1 | 1:0.9.12-1 | HPND-sell-variant | dpkg-db-cataloger |
| libxshmfence1 | 1.3.3-1 | HPND-sell-variant | dpkg-db-cataloger |
| libxslt1.1 | 1.1.35-1.2+deb13u2 |  | dpkg-db-cataloger |
| libxt6t64 | 1:1.2.1-1.2+b2 |  | dpkg-db-cataloger |
| libxtst6 | 2:1.2.5-1 |  | dpkg-db-cataloger |
| libxv1 | 2:1.0.11-1.1+b3 | HPND, HPND-sell-variant | dpkg-db-cataloger |
| libxxf86dga1 | 2:1.1.5-1+b3 | MIT | dpkg-db-cataloger |
| libxxf86vm1 | 1:1.1.4-1+b4 | MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.3-2 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libyajl2 | 2.1.0-5+b2 | ISC | dpkg-db-cataloger |
| libz3-4 | 4.13.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libzmf-0.0-0 | 0.0.2-1+b9 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| libzstd1 | 1.5.7+dfsg-1 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| libzxcvbn0 | 2.5+dfsg-2+b2 | BSD-3-Clause, CC-BY-SA-3.0 | dpkg-db-cataloger |
| libzxing3 | 2.3.0-4 | Apache-2.0, BSD-3-Clause, CC0-1.0 | dpkg-db-cataloger |
| login | 1:4.16.0-2+really2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| login.defs | 1:4.17.4-2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| m4 | 1.4.19-8 |  | dpkg-db-cataloger |
| mawk | 1.3.4.20250131-1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 13.0.0 |  | dpkg-db-cataloger |
| mesa-libgallium | 25.0.7-2 | Apache-2.0, BSD-2-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| more-itertools | 10.3.0 |  | python-installed-package-cataloger |
| more-itertools | 10.7.0 |  | python-installed-package-cataloger |
| mount | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| my-test-package | 1.0 |  | python-installed-package-cataloger |
| ncurses-base | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.5 | GPL-2.0-only | dpkg-db-cataloger |
| openjdk | 21.0.11 |  | java-jvm-cataloger |
| openssl | 3.5.5-1~deb13u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| openssl-provider-legacy | 3.5.5-1~deb13u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| packaging | 24.2 |  | python-installed-package-cataloger |
| passwd | 1:4.17.4-2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.8-2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| pdftk-all | UNKNOWN | Apache-2.0 | java-archive-cataloger |
| perl | 5.40.1-6 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-base | 5.40.1-6 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-modules-5.40 | 5.40.1-6 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-openssl-defaults | 7+b2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| pinentry-curses | 1.3.1-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| platformdirs | 4.2.2 | MIT | python-installed-package-cataloger |
| procps | 2:4.0.4-9 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| python-distutils-extra | 3.1 |  | python-installed-package-cataloger |
| python3 | 3.13.5-1 |  | dpkg-db-cataloger |
| python3-autocommand | 2.2.2-3 | LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| python3-distutils-extra | 3.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-inflect | 7.3.1-2 |  | dpkg-db-cataloger |
| python3-jaraco.context | 6.0.1-1+deb13u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-jaraco.functools | 4.1.0-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-jaraco.text | 4.0.0-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-minimal | 3.13.5-1 |  | dpkg-db-cataloger |
| python3-more-itertools | 10.7.0-1 |  | dpkg-db-cataloger |
| python3-pkg-resources | 78.1.1-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| python3-setuptools | 78.1.1-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| python3-typeguard | 4.4.2-1 |  | dpkg-db-cataloger |
| python3-typing-extensions | 4.13.2-1 |  | dpkg-db-cataloger |
| python3-uno | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| python3-zipp | 3.21.0-1 |  | dpkg-db-cataloger |
| python3.13 | 3.13.5-2 | GPL-2.0-only | dpkg-db-cataloger |
| python3.13-minimal | 3.13.5-2 | GPL-2.0-only | dpkg-db-cataloger |
| qpdf | 12.2.0-1 | Apache-2.0 | dpkg-db-cataloger |
| readline-common | 8.2-6 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| sed | 4.9-2 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sensible-utils | 0.0.25 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| setuptools | 78.1.1 |  | python-installed-package-cataloger |
| shared-mime-info | 2.4-5+b2 |  | dpkg-db-cataloger |
| sqv | 1.3.0-3+b2 | LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| stdlib | go1.26.2 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.26.2 | BSD-3-Clause | go-module-binary-cataloger |
| systemd | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| systemd-sysv | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| sysvinit-utils | 3.14-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| tar | 1.35+dfsg-3.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tini | 0.19.0-3+b6 |  | dpkg-db-cataloger |
| tomli | 2.0.1 |  | python-installed-package-cataloger |
| typeguard | 4.3.0 | MIT | python-installed-package-cataloger |
| typeguard | 4.4.2 | MIT | python-installed-package-cataloger |
| typing-extensions | 4.12.2 |  | python-installed-package-cataloger |
| typing-extensions | 4.13.2 | PSF-2.0 | python-installed-package-cataloger |
| tzdata | 2026a-0+deb13u1 |  | dpkg-db-cataloger |
| ucf | 3.0052 | GPL-2.0-only | dpkg-db-cataloger |
| uno-libs-private | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| ure | 4:26.2.2.2-3~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| util-linux | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| wheel | 0.45.1 |  | python-installed-package-cataloger |
| x11-common | 1:7.7+24+deb13u1 |  | dpkg-db-cataloger |
| x11-utils | 7.7+7 |  | dpkg-db-cataloger |
| xdg-utils | 1.2.1-2 |  | dpkg-db-cataloger |
| xfonts-encodings | 1:1.0.4-2.2 |  | dpkg-db-cataloger |
| xfonts-utils | 1:7.7+7 |  | dpkg-db-cataloger |
| xkb-data | 2.42-1 |  | dpkg-db-cataloger |
| zipp | 3.19.2 |  | python-installed-package-cataloger |
| zipp | 3.21.0 |  | python-installed-package-cataloger |
| zlib1g | 1:1.3.dfsg+really1.3.1-1+b1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/kube-state-metrics

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| base-files | 12.4+deb12u13 |  | dpkg-db-cataloger |
| cel.dev/expr | v0.24.0 |  | go-module-binary-cataloger |
| github.com/KimMachineGun/automemlimit | v0.7.5 |  | go-module-binary-cataloger |
| github.com/antlr4-go/antlr/v4 | v4.13.0 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/blang/semver/v4 | v4.0.0 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v5 | v5.0.2 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.6.0 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/dgryski/go-jump | v0.0.0-20211018200510-ba001c3ffce0 |  | go-module-binary-cataloger |
| github.com/dlclark/regexp2 | v1.11.5 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.12.2 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.9.0 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.3 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.20.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-viper/mapstructure/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/gobuffalo/flect | v1.0.3 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.3.0 |  | go-module-binary-cataloger |
| github.com/google/cel-go | v0.26.0 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.26.3 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/jpillora/backoff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mdlayher/socket | v0.4.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/vsock | v1.2.1 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.3-0.20250322232337-35a7c28c31ee |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/mwitkow/go-conntrack | v0.0.0-20190716064945-2f068394615f |  | go-module-binary-cataloger |
| github.com/oklog/run | v1.2.0 |  | go-module-binary-cataloger |
| github.com/pbnjay/memory | v0.0.0-20210728143218-7b4eea64cf58 |  | go-module-binary-cataloger |
| github.com/pelletier/go-toml/v2 | v2.2.4 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.3-0.20251103151724-a5ae20370e5e |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.5 |  | go-module-binary-cataloger |
| github.com/prometheus/exporter-toolkit | v0.15.1 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.19.2 |  | go-module-binary-cataloger |
| github.com/robfig/cron/v3 | v3.0.1 |  | go-module-binary-cataloger |
| github.com/sagikazarmark/locafero | v0.11.0 |  | go-module-binary-cataloger |
| github.com/sourcegraph/conc | v0.3.1-0.20240121214520-5f936abd7ae8 |  | go-module-binary-cataloger |
| github.com/spf13/afero | v1.15.0 |  | go-module-binary-cataloger |
| github.com/spf13/cast | v1.10.0 |  | go-module-binary-cataloger |
| github.com/spf13/cobra | v1.10.2 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/spf13/viper | v1.21.0 |  | go-module-binary-cataloger |
| github.com/stoewer/go-strcase | v1.3.0 |  | go-module-binary-cataloger |
| github.com/subosito/gotenv | v1.6.0 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.1.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.60.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.37.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.36.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.36.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.37.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.37.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.37.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.6.0 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.3 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v3 | v3.0.4 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.46.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250819193227-8b4c13bb791b |  | go-module-binary-cataloger |
| golang.org/x/net | v0.48.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.34.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.19.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.39.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.14.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20250707201910-8d1bb00bc6a7 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20250707201910-8d1bb00bc6a7 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.75.1 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| gopkg.in/evanphx/json-patch.v4 | v4.12.0 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| k8s.io/api | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/apiserver | v0.34.1 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/component-base | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/klog/v2 | v2.130.1 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20250710124328-f3f2b991d03b |  | go-module-binary-cataloger |
| k8s.io/kube-state-metrics/v2 | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/sample-controller | v0.34.3 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20250820121507-0af2bda4dd1d |  | go-module-binary-cataloger |
| media-types | 10.0.0 |  | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| sigs.k8s.io/apiserver-network-proxy/konnectivity-client | v0.33.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/controller-runtime | v0.22.4 |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20241014173422-cfa47c3a1cc8 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v6 | v6.3.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.6.0 |  | go-module-binary-cataloger |
| stdlib | go1.25.5 | BSD-3-Clause | go-module-binary-cataloger |
| tzdata | 2025b-0+deb12u2 |  | dpkg-db-cataloger |
