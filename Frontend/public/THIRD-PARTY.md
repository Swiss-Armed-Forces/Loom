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

### MongoDB

<!-- markdownlint-disable -->
Loom utilizes the MongoDB component as a standalone Docker image.

**Software Licenses:**

MongoDB Community Edition is commonly licensed under the Server Side Public License (SSPL) for versions released on or after October 16, 2018. Prior to that date, it was licensed under the GNU Affero General Public License (AGPL) v3.0. MongoDB also provides officially supported drivers under the Apache License v2.0. When incorporating MongoDB in the Loom project, please review the version of MongoDB in use to confirm the applicable license. Consult the MongoDB website’s “Legal” section for the most up-to-date information, as MongoDB also offers commercial licenses for MongoDB Enterprise Advanced under separate terms.

**Component Website:**

[https://www.mongodb.com/](https://www.mongodb.com/)

This official MongoDB website provides documentation, community resources, downloads, and detailed legal notices.

**Trademark Information:**

MongoDB’s trademarks, including its logos and service marks, are subject to strict usage guidelines. For comprehensive trademark information and proper usage standards, refer to the “Legal” section or “Trademark Standards of Use” on the MongoDB website. Adhering to these guidelines ensures respectful and non-confusing use of MongoDB’s intellectual property.

**Source Code:**

Details and links for accessing MongoDB source code, including the Community Edition, may be found on the official MongoDB website and their publicly available repositories (for instance, on GitHub under the MongoDB organization). For specific drivers or other related components, consult each repository’s documentation regarding any additional license terms.


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

### fluentd

<!-- markdownlint-disable -->
Loom utilizes the "fluentd" software as a standalone Docker image.

**Software Licenses:**
The “fluentd” software is distributed under the Apache License, Version 2.0. This permissive, open-source license grants broad rights to use, modify, and distribute the software. Additional information regarding the Apache License, Version 2.0 can be found within the “fluentd” GitHub repository and on the official “fluentd” website. By integrating the “fluentd” component into the Loom project, users acknowledge and agree to adhere to the terms of the Apache License, Version 2.0.

**Component Website:**
For detailed information about features, documentation, community forums, and development updates, please visit the officially recognized “fluentd” website at [https://www.fluentd.org/](https://www.fluentd.org/). This website serves as the central resource for understanding the capabilities of the “fluentd” project and its role within the open-source ecosystem.

**Trademark Information:**
While no explicit trademark statement has been identified for “fluentd,” it is important to note that “fluentd” is a graduated project under the Cloud Native Computing Foundation (CNCF). As part of this affiliation, the CNCF may hold or manage certain trademark and governance rights to protect the “fluentd” identity. Any references to “fluentd” within the Loom project are solely for identifying the open-source software used, and no ownership of the “fluentd” name is claimed by Loom.

**Source Code:**
The source code for “fluentd” is available through its GitHub repository, which can be accessed via links provided on the official project website. Interested parties may review the complete source code to gain clarity on its functionality, contribute to its ongoing development, or verify compliance with applicable license terms.

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


### libretranslate

<!-- markdownlint-disable -->

Loom utilizes the LibreTranslate as a standalone Docker image.

**Software License:** GNU Affero General Public License version 3.0 (AGPL-3.0)

**Component Website:** <https://libretranslate.com/>

**Trademark Information:**

The name "LibreTranslate" is a registered trademark. The LibreTranslate Trademark Guidelines (available at <https://github.com/LibreTranslate/LibreTranslate/blob/main/TRADEMARK.md>) specify that the LibreTranslate trademarks should not be used in the name of any business, product, service, app, or domain name in a way that implies endorsement or affiliation.

"LibretTranslate" recognize swiss-armed-forces's "Loom"'s use of LibreTranslate to be usage of an "unmodified" version of LibreTranslate and as such, can proceed in using the LibreTranslate trademark following "LibretTranslate"'s guidelines.

**Source Code:** The authoritative source code for LibreTranslate, including all license files, is available at: <https://github.com/LibreTranslate/LibreTranslate>

### minio

<!-- markdownlint-disable -->
Loom utilizes the MinIO software as a standalone Docker image.

**Software Licenses:**
MinIO is distributed under a dual-licensing model, which includes the GNU Affero General Public License Version 3 (AGPLv3) as its primary open-source license. The full text of the AGPLv3 is available at [https://www.gnu.org/licenses/agpl-3.0.txt](https://www.gnu.org/licenses/agpl-3.0.txt). Because AGPLv3 places specific requirements on network distribution and derivative works, organizations whose use cases are not compatible with AGPLv3 obligations may opt for a commercial license from MinIO, Inc. For questions about compliance or determining the most suitable license for your specific deployment model, consulting legal counsel is recommended.

**Component Website:**
Further information about MinIO, including detailed documentation, support resources, and commercial licensing options, is available at [https://min.io/](https://min.io/).

**Trademark Information:**
"MinIO" is a registered trademark of MinIO, Inc. in the United States and other countries. Usage of the MinIO name, logos, or related trademarks must adhere to the official [MinIO Trademark Policy](https://min.io/compliance). This policy details permissible references and ensures clarity regarding the origin and endorsement of the software.

**Source Code:**
The source code for MinIO can be found in its official repository at [https://github.com/minio/minio](https://github.com/minio/minio).

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
| celery-types                          | 0.24.0          | Apache Software License                                                          |
| coverage                              | 7.5.4           | Apache Software License                                                          |
| docker                                | 7.1.0           | Apache Software License                                                          |
| elastic-transport                     | 8.17.1          | Apache Software License                                                          |
| elasticsearch                         | 9.0.2           | Apache Software License                                                          |
| memray                                | 1.17.2          | Apache Software License                                                          |
| minio                                 | 7.2.15          | Apache Software License                                                          |
| opentelemetry-instrumentation         | 0.60b1          | Apache Software License                                                          |
| opentelemetry-instrumentation-asgi    | 0.60b1          | Apache Software License                                                          |
| opentelemetry-instrumentation-fastapi | 0.60b1          | Apache Software License                                                          |
| opentelemetry-util-http               | 0.60b1          | Apache Software License                                                          |
| pymongo                               | 4.7.3           | Apache Software License                                                          |
| pytest-memray                         | 1.7.0           | Apache Software License                                                          |
| pytest_docker_tools                   | 3.1.9           | Apache Software License                                                          |
| python-multipart                      | 0.0.22          | Apache Software License                                                          |
| requests                              | 2.32.3          | Apache Software License                                                          |
| requests-toolbelt                     | 1.0.0           | Apache Software License                                                          |
| requirements-parser                   | 0.13.0          | Apache Software License                                                          |
| tenacity                              | 9.1.2           | Apache Software License                                                          |
| tornado                               | 6.5.1           | Apache Software License                                                          |
| types-cffi                            | 1.16.0.20240331 | Apache Software License                                                          |
| types-docker                          | 7.1.0.20240626  | Apache Software License                                                          |
| types-pyOpenSSL                       | 24.1.0.20240425 | Apache Software License                                                          |
| types-redis                           | 4.6.0.20240425  | Apache Software License                                                          |
| types-requests                        | 2.32.0.20240622 | Apache Software License                                                          |
| types-setuptools                      | 70.1.0.20240625 | Apache Software License                                                          |
| tzdata                                | 2025.2          | Apache Software License                                                          |
| watchdog                              | 6.0.0           | Apache Software License                                                          |
| cryptography                          | 42.0.8          | Apache Software License; BSD License                                             |
| packaging                             | 24.2            | Apache Software License; BSD License                                             |
| python-dateutil                       | 2.9.0.post0     | Apache Software License; BSD License                                             |
| pycryptodome                          | 3.20.0          | Apache Software License; BSD License; Public Domain                              |
| pycryptodome                          | 3.20.0          | Apache Software License; BSD License; Public Domain                              |
| pycryptodomex                         | 3.20.0          | Apache Software License; BSD License; Public Domain                              |
| luqum                                 | 0.14.0          | Apache Software License; GNU Lesser General Public License v3 or later (LGPLv3+) |
| orjson                                | 3.10.5          | Apache Software License; MIT License                                             |
| sniffio                               | 1.3.1           | Apache Software License; MIT License                                             |
| freezegun                             | 1.5.5           | Apache-2.0                                                                       |
| ply                                   | 3.11            | BSD                                                                              |
| IMAPClient                            | 3.0.1           | BSD License                                                                      |
| Jinja2                                | 3.1.6           | BSD License                                                                      |
| MarkupSafe                            | 3.0.2           | BSD License                                                                      |
| Pygments                              | 2.19.1          | BSD License                                                                      |
| amqp                                  | 5.2.0           | BSD License                                                                      |
| asgiref                               | 3.11.1          | BSD License                                                                      |
| billiard                              | 4.2.2           | BSD License                                                                      |
| celery                                | 5.5.3           | BSD License                                                                      |
| click                                 | 8.1.7           | BSD License                                                                      |
| click-plugins                         | 1.1.1           | BSD License                                                                      |
| dill                                  | 0.3.8           | BSD License                                                                      |
| flower                                | 2.0.1           | BSD License                                                                      |
| gitdb                                 | 4.0.12          | BSD License                                                                      |
| httpcore                              | 1.0.5           | BSD License                                                                      |
| httpx                                 | 0.28.1          | BSD License                                                                      |
| idna                                  | 3.7             | BSD License                                                                      |
| joblib                                | 1.4.2           | BSD License                                                                      |
| jsonpatch                             | 1.33            | BSD License                                                                      |
| jsonpointer                           | 3.0.0           | BSD License                                                                      |
| kombu                                 | 5.5.4           | BSD License                                                                      |
| lxml                                  | 4.9.4           | BSD License                                                                      |
| numpy                                 | 1.26.4          | BSD License                                                                      |
| pika                                  | 1.3.2           | BSD License                                                                      |
| prompt_toolkit                        | 3.0.47          | BSD License                                                                      |
| pycparser                             | 2.22            | BSD License                                                                      |
| pytest-celery                         | 1.2.1           | BSD License                                                                      |
| python-dotenv                         | 1.0.1           | BSD License                                                                      |
| scikit-learn                          | 1.7.0           | BSD License                                                                      |
| scipy                                 | 1.15.3          | BSD License                                                                      |
| smmap                                 | 5.0.2           | BSD License                                                                      |
| starlette                             | 0.46.1          | BSD License                                                                      |
| threadpoolctl                         | 3.5.0           | BSD License                                                                      |
| vine                                  | 5.1.0           | BSD License                                                                      |
| websockets                            | 13.1            | BSD License                                                                      |
| wrapt                                 | 1.17.3          | BSD License                                                                      |
| GitPython                             | 3.1.46          | BSD-3-Clause                                                                     |
| psutil                                | 7.2.1           | BSD-3-Clause                                                                     |
| pytest-timeout                        | 2.4.0           | DFSG approved; MIT License                                                       |
| pylint-plugin-utils                   | 0.8.2           | GNU General Public License v2 or later (GPLv2+)                                  |
| python-gitlab                         | 6.0.0           | GNU Lesser General Public License v3 (LGPLv3)                                    |
| pylint-pydantic                       | 0.4.1           | GPLv3                                                                            |
| dnspython                             | 2.6.1           | ISC License (ISCL)                                                               |
| click-repl                            | 0.3.0           | MIT                                                                              |
| identify                              | 2.6.16          | MIT                                                                              |
| pycodestyle                           | 2.14.0          | MIT                                                                              |
| pytest-cov                            | 6.3.0           | MIT                                                                              |
| PyYAML                                | 6.0.1           | MIT License                                                                      |
| Wand                                  | 0.6.13          | MIT License                                                                      |
| annotated-types                       | 0.7.0           | MIT License                                                                      |
| anyio                                 | 4.9.0           | MIT License                                                                      |
| api                                   | 0.1.0           | MIT License                                                                      |
| argon2-cffi                           | 23.1.0          | MIT License                                                                      |
| argon2-cffi-bindings                  | 21.2.0          | MIT License                                                                      |
| attrs                                 | 23.2.0          | MIT License                                                                      |
| autoflake                             | 2.3.1           | MIT License                                                                      |
| cffi                                  | 1.17.1          | MIT License                                                                      |
| charset-normalizer                    | 3.3.2           | MIT License                                                                      |
| click-didyoumean                      | 0.3.1           | MIT License                                                                      |
| common                                | 0.1.0           | MIT License                                                                      |
| crawler                               | 0.1.0           | MIT License                                                                      |
| debugpy                               | 1.8.19          | MIT License                                                                      |
| deptry                                | 0.24.0          | MIT License                                                                      |
| flake8                                | 7.3.0           | MIT License                                                                      |
| flake8-bugbear                        | 25.11.29        | MIT License                                                                      |
| h11                                   | 0.14.0          | MIT License                                                                      |
| h2                                    | 4.3.0           | MIT License                                                                      |
| hpack                                 | 4.1.0           | MIT License                                                                      |
| hyperframe                            | 6.1.0           | MIT License                                                                      |
| iniconfig                             | 2.0.0           | MIT License                                                                      |
| integrationtest                       | 0.1.0           | MIT License                                                                      |
| isort                                 | 7.0.0           | MIT License                                                                      |
| langchain-core                        | 0.3.22          | MIT License                                                                      |
| langchain-text-splitters              | 0.3.2           | MIT License                                                                      |
| langsmith                             | 0.1.147         | MIT License                                                                      |
| libretranslatepy                      | 2.1.4           | MIT License                                                                      |
| linkify-it-py                         | 2.0.3           | MIT License                                                                      |
| markdown-it-py                        | 3.0.0           | MIT License                                                                      |
| mccabe                                | 0.7.0           | MIT License                                                                      |
| mdit-py-plugins                       | 0.4.2           | MIT License                                                                      |
| mdurl                                 | 0.1.2           | MIT License                                                                      |
| mypy                                  | 1.10.1          | MIT License                                                                      |
| mypy-extensions                       | 1.0.0           | MIT License                                                                      |
| platformdirs                          | 4.2.2           | MIT License                                                                      |
| pluggy                                | 1.5.0           | MIT License                                                                      |
| pydantic                              | 2.10.3          | MIT License                                                                      |
| pydantic-mongo                        | 2.3.0           | MIT License                                                                      |
| pydantic-settings                     | 2.3.4           | MIT License                                                                      |
| pydantic_core                         | 2.27.1          | MIT License                                                                      |
| pyflakes                              | 3.4.0           | MIT License                                                                      |
| pytest-mock                           | 3.15.1          | MIT License                                                                      |
| pytest-random-order                   | 1.1.1           | MIT License                                                                      |
| pytest-split                          | 0.11.0          | MIT License                                                                      |
| python-magic                          | 0.4.27          | MIT License                                                                      |
| pytokens                              | 0.3.0           | MIT License                                                                      |
| pytz                                  | 2025.2          | MIT License                                                                      |
| redis                                 | 5.0.7           | MIT License                                                                      |
| rich                                  | 14.0.0          | MIT License                                                                      |
| six                                   | 1.16.0          | MIT License                                                                      |
| stream-zip                            | 0.0.84          | MIT License                                                                      |
| textual                               | 3.3.0           | MIT License                                                                      |
| tomlkit                               | 0.12.5          | MIT License                                                                      |
| uc-micro-py                           | 1.0.3           | MIT License                                                                      |
| untokenize                            | 0.1.1           | MIT License                                                                      |
| urllib3                               | 2.2.2           | MIT License                                                                      |
| worker                                | 0.1.0           | MIT License                                                                      |
| docformatter                          | 1.7.7           | MIT License; Other/Proprietary License                                           |
| pytest-rerunfailures                  | 15.1            | MPL-2.0                                                                          |
| certifi                               | 2024.6.2        | Mozilla Public License 2.0 (MPL 2.0)                                             |
| gotenberg-client                      | 0.13.1          | Mozilla Public License 2.0 (MPL 2.0)                                             |
| pathspec                              | 1.0.4           | Mozilla Public License 2.0 (MPL 2.0)                                             |
| blobfile                              | 2.1.1           | Public Domain                                                                    |
| filelock                              | 3.15.4          | The Unlicense (Unlicense)                                                        |
| annotated-doc                         | 0.0.4           | UNKNOWN                                                                          |
| astroid                               | 4.0.4           | UNKNOWN                                                                          |
| binwalk                               | 2.4.3           | UNKNOWN                                                                          |
| black                                 | 26.1.0          | UNKNOWN                                                                          |
| fastapi                               | 0.128.0         | UNKNOWN                                                                          |
| humanize                              | 4.12.3          | UNKNOWN                                                                          |
| importlib_metadata                    | 8.7.1           | UNKNOWN                                                                          |
| ollama                                | 0.6.1           | UNKNOWN                                                                          |
| opentelemetry-api                     | 1.39.1          | UNKNOWN                                                                          |
| opentelemetry-exporter-prometheus     | 0.60b1          | UNKNOWN                                                                          |
| opentelemetry-sdk                     | 1.39.1          | UNKNOWN                                                                          |
| opentelemetry-semantic-conventions    | 0.60b1          | UNKNOWN                                                                          |
| prometheus_client                     | 0.24.1          | UNKNOWN                                                                          |
| pycrypto                              | 3.20.0          | UNKNOWN                                                                          |
| pylint                                | 4.0.4           | UNKNOWN                                                                          |
| pytest                                | 9.0.2           | UNKNOWN                                                                          |
| pytest-asyncio                        | 1.3.0           | UNKNOWN                                                                          |
| typing_extensions                     | 4.15.0          | UNKNOWN                                                                          |
| uvicorn                               | 0.40.0          | UNKNOWN                                                                          |
| zipp                                  | 3.23.0          | UNKNOWN                                                                          |
| zstandard                             | 0.25.0          | UNKNOWN                                                                          |

## JavaScript

| Name                                | License type | Installed version |
| :---------------------------------- | :----------- | :---------------- |
| @emotion/styled                     | MIT          | 11.14.1           |
| @mui/icons-material                 | MIT          | 7.3.8             |
| @mui/material                       | MIT          | 7.3.8             |
| @mui/x-charts                       | MIT          | 8.27.0            |
| @mui/x-tree-view                    | MIT          | 8.27.1            |
| @reduxjs/toolkit                    | MIT          | 2.11.2            |
| ace-builds                          | BSD-3-Clause | 1.43.6            |
| ajv                                 | MIT          | 8.18.0            |
| date-fns                            | MIT          | 4.1.0             |
| i18next                             | MIT          | 25.8.11           |
| i18next-http-backend                | MIT          | 3.0.2             |
| react                               | MIT          | 19.2.4            |
| react-ace                           | MIT          | 14.0.1            |
| react-dom                           | MIT          | 19.2.4            |
| react-dropzone                      | MIT          | 14.4.1            |
| react-i18next                       | MIT          | 15.7.4            |
| react-intersection-observer         | MIT          | 9.16.0            |
| react-pdf                           | MIT          | 10.3.0            |
| react-redux                         | MIT          | 9.2.0             |
| react-router-dom                    | MIT          | 7.13.0            |
| react-toastify                      | MIT          | 11.0.5            |
| uuid                                | MIT          | 12.0.0            |
| @eslint/js                          | MIT          | 9.39.2            |
| @mui/types                          | MIT          | 7.4.11            |
| @openapitools/openapi-generator-cli | Apache-2.0   | 2.29.0            |
| @testing-library/jest-dom           | MIT          | 6.9.1             |
| @testing-library/react              | MIT          | 16.3.2            |
| @types/node                         | MIT          | 24.10.13          |
| @types/react                        | MIT          | 19.2.14           |
| @types/react-dom                    | MIT          | 19.2.3            |
| @typescript-eslint/eslint-plugin    | MIT          | 8.56.0            |
| @typescript-eslint/parser           | MIT          | 8.56.0            |
| @vitejs/plugin-react                | MIT          | 5.1.4             |
| eslint                              | MIT          | 9.39.2            |
| eslint-config-prettier              | MIT          | 10.1.8            |
| eslint-plugin-prettier              | MIT          | 5.5.5             |
| eslint-plugin-react                 | MIT          | 7.37.5            |
| eslint-plugin-react-hooks           | MIT          | 7.0.1             |
| eslint-plugin-react-refresh         | MIT          | 0.4.26            |
| eslint-plugin-unused-imports        | MIT          | 4.4.1             |
| globals                             | MIT          | 16.5.0            |
| jsdom                               | MIT          | 26.1.0            |
| license-report                      | MIT          | 6.8.1             |
| prettier                            | MIT          | 3.8.1             |
| typescript                          | Apache-2.0   | 5.9.3             |
| typescript-eslint                   | MIT          | 8.56.0            |
| vite                                | MIT          | 6.4.1             |
| vite-plugin-static-copy             | MIT          | 3.2.0             |
| vite-plugin-svgr                    | MIT          | 4.5.0             |
| vitest                              | MIT          | 3.2.4             |


## Container


### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/traefik

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.5-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.21.3-r0 | MIT | apk-db-cataloger |
| apk-tools | 2.14.6-r3 | GPL-2.0-only | apk-db-cataloger |
| busybox | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates | 20241121-r1 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20241121-r1 | MPL-2.0 AND MIT | apk-db-cataloger |
| cloud.google.com/go/auth | v0.15.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.7 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.6.0 |  | go-module-binary-cataloger |
| github.com/AdamSLevy/jsonrpc2/v14 | v14.1.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go | v68.0.0+incompatible |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.2 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
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
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.3 |  | go-module-binary-cataloger |
| github.com/BurntSushi/toml | v1.5.0 |  | go-module-binary-cataloger |
| github.com/HdrHistogram/hdrhistogram-go | v1.1.2 |  | go-module-binary-cataloger |
| github.com/Masterminds/goutils | v1.1.1 |  | go-module-binary-cataloger |
| github.com/Masterminds/semver/v3 | v3.2.1 |  | go-module-binary-cataloger |
| github.com/Masterminds/sprig/v3 | v3.2.3 |  | go-module-binary-cataloger |
| github.com/OpenDNS/vegadns2client | v0.0.0-20180418235048-a3fa4a771d87 |  | go-module-binary-cataloger |
| github.com/VividCortex/gohistogram | v1.0.0 |  | go-module-binary-cataloger |
| github.com/akamai/AkamaiOPEN-edgegrid-golang | v1.2.2 |  | go-module-binary-cataloger |
| github.com/aliyun/alibaba-cloud-sdk-go | v1.63.100 |  | go-module-binary-cataloger |
| github.com/andybalholm/brotli | v1.1.1 |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2 | v1.36.3 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/config | v1.29.9 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/credentials | v1.17.62 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/feature/ec2/imds | v1.16.30 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/configsources | v1.3.34 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/endpoints/v2 | v2.6.34 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/internal/ini | v1.8.3 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ec2 | v1.203.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ecs | v1.53.15 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/accept-encoding | v1.12.3 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/internal/presigned-url | v1.12.15 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/lightsail | v1.43.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/route53 | v1.50.0 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssm | v1.56.13 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sso | v1.25.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/ssooidc | v1.29.1 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go-v2/service/sts | v1.33.17 |  | go-module-binary-cataloger |
| github.com/aws/smithy-go | v1.22.2 |  | go-module-binary-cataloger |
| github.com/baidubce/bce-sdk-go | v0.9.223 |  | go-module-binary-cataloger |
| github.com/benbjohnson/clock | v1.3.0 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/boombuler/barcode | v1.0.1-0.20190219062509-6c824513bacc |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/civo/civogo | v0.3.11 |  | go-module-binary-cataloger |
| github.com/cloudflare/cloudflare-go | v0.115.0 |  | go-module-binary-cataloger |
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
| github.com/dnsimple/dnsimple-go | v1.7.0 |  | go-module-binary-cataloger |
| github.com/docker/cli | v27.1.1+incompatible |  | go-module-binary-cataloger |
| github.com/docker/docker | v27.1.1+incompatible |  | go-module-binary-cataloger |
| github.com/docker/go-connections | v0.5.0 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.12.0 |  | go-module-binary-cataloger |
| github.com/exoscale/egoscale/v3 | v3.1.13 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.17.0 |  | go-module-binary-cataloger |
| github.com/fatih/structs | v1.1.0 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.8.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/gabriel-vasile/mimetype | v1.4.2 |  | go-module-binary-cataloger |
| github.com/ghodss/yaml | v1.0.0 |  | go-module-binary-cataloger |
| github.com/go-acme/lego/v4 | v4.23.1 |  | go-module-binary-cataloger |
| github.com/go-errors/errors | v1.0.1 |  | go-module-binary-cataloger |
| github.com/go-jose/go-jose/v4 | v4.0.5 |  | go-module-binary-cataloger |
| github.com/go-kit/kit | v0.13.0 |  | go-module-binary-cataloger |
| github.com/go-kit/log | v0.2.1 |  | go-module-binary-cataloger |
| github.com/go-logfmt/logfmt | v0.5.1 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.2 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-playground/locales | v0.14.1 |  | go-module-binary-cataloger |
| github.com/go-playground/universal-translator | v0.18.1 |  | go-module-binary-cataloger |
| github.com/go-playground/validator/v10 | v10.16.0 |  | go-module-binary-cataloger |
| github.com/go-resty/resty/v2 | v2.16.5 |  | go-module-binary-cataloger |
| github.com/go-viper/mapstructure/v2 | v2.2.1 |  | go-module-binary-cataloger |
| github.com/go-zookeeper/zk | v1.0.3 |  | go-module-binary-cataloger |
| github.com/goccy/go-json | v0.10.5 |  | go-module-binary-cataloger |
| github.com/gofrs/flock | v0.12.1 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v4 | v4.5.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.6.8 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/go-github/v28 | v28.1.1 |  | go-module-binary-cataloger |
| github.com/google/go-querystring | v1.1.0 |  | go-module-binary-cataloger |
| github.com/google/gofuzz | v1.2.0 |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.9 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.6 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.14.1 |  | go-module-binary-cataloger |
| github.com/gophercloud/gophercloud | v1.14.1 |  | go-module-binary-cataloger |
| github.com/gophercloud/utils | v0.0.0-20231010081019-80377eca5d56 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.3 |  | go-module-binary-cataloger |
| github.com/gravitational/trace | v1.1.16-0.20220114165159-14a9a7dd6aaf |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.23.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/consul/api | v1.26.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/cronexpr | v1.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v1.6.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-immutable-radix | v1.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-uuid | v1.0.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-version | v1.7.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/hcl | v1.0.1-vault-5 |  | go-module-binary-cataloger |
| github.com/hashicorp/nomad/api | v0.0.0-20231213195942-64e3dca9274b |  | go-module-binary-cataloger |
| github.com/hashicorp/serf | v0.10.1 |  | go-module-binary-cataloger |
| github.com/http-wasm/http-wasm-host-go | v0.7.0 |  | go-module-binary-cataloger |
| github.com/huandu/xstrings | v1.5.0 |  | go-module-binary-cataloger |
| github.com/huaweicloud/huaweicloud-sdk-go-v3 | v0.1.141 |  | go-module-binary-cataloger |
| github.com/iij/doapi | v0.0.0-20190504054126-0bbf12d6d7df |  | go-module-binary-cataloger |
| github.com/imdario/mergo | v0.3.16 |  | go-module-binary-cataloger |
| github.com/influxdata/influxdb-client-go/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/influxdata/influxdb1-client | v0.0.0-20200827194710-b269163b24ab |  | go-module-binary-cataloger |
| github.com/influxdata/line-protocol | v0.0.0-20200327222509-2487e7298839 |  | go-module-binary-cataloger |
| github.com/infobloxopen/infoblox-go-client/v2 | v2.9.0 |  | go-module-binary-cataloger |
| github.com/jmespath/go-jmespath | v0.4.0 |  | go-module-binary-cataloger |
| github.com/jonboulle/clockwork | v0.4.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/k0kubun/go-ansi | v0.0.0-20180517002512-3bf9e2903213 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.11 |  | go-module-binary-cataloger |
| github.com/kolo/xmlrpc | v0.0.0-20220921171641-a4b6fa1dd06b |  | go-module-binary-cataloger |
| github.com/kvtools/consul | v1.0.2 |  | go-module-binary-cataloger |
| github.com/kvtools/etcdv3 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/kvtools/redis | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kvtools/valkeyrie | v1.0.0 |  | go-module-binary-cataloger |
| github.com/kvtools/zookeeper | v1.0.2 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/labbsr0x/bindman-dns-webhook | v1.0.2 |  | go-module-binary-cataloger |
| github.com/labbsr0x/goh | v1.0.1 |  | go-module-binary-cataloger |
| github.com/leodido/go-urn | v1.2.4 |  | go-module-binary-cataloger |
| github.com/linode/linodego | v1.48.1 |  | go-module-binary-cataloger |
| github.com/liquidweb/liquidweb-cli | v0.6.9 |  | go-module-binary-cataloger |
| github.com/liquidweb/liquidweb-go | v1.6.4 |  | go-module-binary-cataloger |
| github.com/magiconair/properties | v1.8.7 |  | go-module-binary-cataloger |
| github.com/mailgun/multibuf | v0.1.2 |  | go-module-binary-cataloger |
| github.com/mailgun/timetools | v0.0.0-20141028012446-7e6055773c51 |  | go-module-binary-cataloger |
| github.com/mailgun/ttlmap | v0.0.0-20170619185759-c1c17f74874f |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.13 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.64 |  | go-module-binary-cataloger |
| github.com/mimuret/golang-iij-dpf | v0.9.1 |  | go-module-binary-cataloger |
| github.com/mitchellh/copystructure | v1.2.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-ps | v1.0.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/hashstructure | v1.0.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/reflectwalk | v1.0.2 |  | go-module-binary-cataloger |
| github.com/moby/docker-image-spec | v1.3.1 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/namedotcom/go | v0.0.0-20180403034216-08470befbe04 |  | go-module-binary-cataloger |
| github.com/nrdcg/auroradns | v1.1.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/bunny-go | v0.0.0-20240207213615-dde5bf4577a3 |  | go-module-binary-cataloger |
| github.com/nrdcg/desec | v0.10.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/dnspod-go | v0.4.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/freemyip | v0.3.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/goacmedns | v0.2.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/goinwx | v0.10.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/mailinabox | v0.2.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/namesilo | v0.2.1 |  | go-module-binary-cataloger |
| github.com/nrdcg/nodion | v0.1.0 |  | go-module-binary-cataloger |
| github.com/nrdcg/porkbun | v0.4.0 |  | go-module-binary-cataloger |
| github.com/nzdjb/go-metaname | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/image-spec | v1.1.0 |  | go-module-binary-cataloger |
| github.com/opentracing/opentracing-go | v1.2.1-0.20220228012449-10b1cf09e00b |  | go-module-binary-cataloger |
| github.com/oracle/oci-go-sdk/v65 | v65.87.0 |  | go-module-binary-cataloger |
| github.com/ovh/go-ovh | v1.7.0 |  | go-module-binary-cataloger |
| github.com/patrickmn/go-cache | v2.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/pelletier/go-toml/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/peterhellberg/link | v1.2.0 |  | go-module-binary-cataloger |
| github.com/pires/go-proxyproto | v0.6.1 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/pquerna/otp | v1.4.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.19.1 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.55.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.15.1 |  | go-module-binary-cataloger |
| github.com/quic-go/qpack | v0.5.1 |  | go-module-binary-cataloger |
| github.com/quic-go/quic-go | v0.48.2 |  | go-module-binary-cataloger |
| github.com/redis/go-redis/v9 | v9.7.3 |  | go-module-binary-cataloger |
| github.com/regfish/regfish-dnsapi-go | v0.1.1 |  | go-module-binary-cataloger |
| github.com/rs/cors | v1.7.0 |  | go-module-binary-cataloger |
| github.com/rs/zerolog | v1.33.0 |  | go-module-binary-cataloger |
| github.com/sacloud/api-client-go | v0.2.10 |  | go-module-binary-cataloger |
| github.com/sacloud/go-http | v0.1.8 |  | go-module-binary-cataloger |
| github.com/sacloud/iaas-api-go | v1.14.0 |  | go-module-binary-cataloger |
| github.com/sacloud/packages-go | v0.0.10 |  | go-module-binary-cataloger |
| github.com/sagikazarmark/slog-shim | v0.1.0 |  | go-module-binary-cataloger |
| github.com/scaleway/scaleway-sdk-go | v1.0.0-beta.32 |  | go-module-binary-cataloger |
| github.com/selectel/domains-go | v1.1.0 |  | go-module-binary-cataloger |
| github.com/selectel/go-selvpcclient/v3 | v3.2.1 |  | go-module-binary-cataloger |
| github.com/shopspring/decimal | v1.4.0 |  | go-module-binary-cataloger |
| github.com/sirupsen/logrus | v1.9.3 |  | go-module-binary-cataloger |
| github.com/smartystreets/go-aws-auth | v0.0.0-20180515143844-0c1422d1fdb9 |  | go-module-binary-cataloger |
| github.com/softlayer/softlayer-go | v1.1.7 |  | go-module-binary-cataloger |
| github.com/softlayer/xmlrpc | v0.0.0-20200409220501-5f089df7cb7e |  | go-module-binary-cataloger |
| github.com/sony/gobreaker | v0.5.0 |  | go-module-binary-cataloger |
| github.com/spf13/afero | v1.11.0 |  | go-module-binary-cataloger |
| github.com/spf13/cast | v1.7.0 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.5 |  | go-module-binary-cataloger |
| github.com/spf13/viper | v1.18.2 |  | go-module-binary-cataloger |
| github.com/spiffe/go-spiffe/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/stealthrocket/wasi-go | v0.8.0 |  | go-module-binary-cataloger |
| github.com/stealthrocket/wazergo | v0.19.1 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.10.0 |  | go-module-binary-cataloger |
| github.com/subosito/gotenv | v1.6.0 |  | go-module-binary-cataloger |
| github.com/tailscale/tscert | v0.0.0-20230806124524-28a91b69a046 |  | go-module-binary-cataloger |
| github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common | v1.0.1128 |  | go-module-binary-cataloger |
| github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/dnspod | v1.0.1128 |  | go-module-binary-cataloger |
| github.com/tetratelabs/wazero | v1.8.0 |  | go-module-binary-cataloger |
| github.com/tjfoc/gmsm | v1.4.1 |  | go-module-binary-cataloger |
| github.com/traefik/grpc-web | v0.16.0 |  | go-module-binary-cataloger |
| github.com/traefik/paerser | v0.2.2 |  | go-module-binary-cataloger |
| github.com/traefik/traefik/v3 | v0.0.0-20250527123204-8b495b45a547 |  | go-module-binary-cataloger |
| github.com/traefik/yaegi | v0.16.1 |  | go-module-binary-cataloger |
| github.com/transip/gotransip/v6 | v6.26.0 |  | go-module-binary-cataloger |
| github.com/ultradns/ultradns-go-sdk | v1.8.0-20241010134910-243eeec |  | go-module-binary-cataloger |
| github.com/unrolled/render | v1.0.2 |  | go-module-binary-cataloger |
| github.com/unrolled/secure | v1.0.9 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/valyala/fasthttp | v1.58.0 |  | go-module-binary-cataloger |
| github.com/vinyldns/go-vinyldns | v0.9.16 |  | go-module-binary-cataloger |
| github.com/volcengine/volc-sdk-golang | v1.0.199 |  | go-module-binary-cataloger |
| github.com/vulcand/oxy/v2 | v2.0.3 |  | go-module-binary-cataloger |
| github.com/vulcand/predicate | v1.2.0 |  | go-module-binary-cataloger |
| github.com/vultr/govultr/v3 | v3.17.0 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/yandex-cloud/go-genproto | v0.0.0-20250319153614-fb9d3e5eb01a |  | go-module-binary-cataloger |
| github.com/yandex-cloud/go-sdk | v0.0.0-20250320143332-9cbcfc5de4ae |  | go-module-binary-cataloger |
| github.com/zeebo/errs | v1.3.0 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/api/v3 | v3.5.14 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.5.14 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.5.14 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.13.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.1.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/bridges/otellogrus | v0.7.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.59.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/autoprop | v0.53.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/aws | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/b3 | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/jaeger | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/ot | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.34.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc | v0.8.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp | v0.8.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp | v1.28.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/log | v0.8.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.34.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.34.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/log | v0.8.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/metric | v1.34.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.34.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.3.1 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/ratelimit | v0.3.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.26.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20241210194714-1829a127f884 |  | go-module-binary-cataloger |
| golang.org/x/mod | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.28.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.12.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.31.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.30.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.11.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.227.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20241021214115-324edc3d5d38 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20250106144421-5f5ef82da422 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20250313205543-e70fdf4c4cb4 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.71.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.5 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/ini.v1 | v1.67.0 |  | go-module-binary-cataloger |
| gopkg.in/natefinch/lumberjack.v2 | v2.2.1 |  | go-module-binary-cataloger |
| gopkg.in/ns1/ns1-go.v2 | v2.13.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| k8s.io/api | v0.31.1 |  | go-module-binary-cataloger |
| k8s.io/apiextensions-apiserver | v0.31.1 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.31.1 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.31.1 |  | go-module-binary-cataloger |
| k8s.io/klog/v2 | v2.130.1 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20240423202451-8948a665c108 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20240711033017-18e509b52bc8 |  | go-module-binary-cataloger |
| libcrypto3 | 3.3.3-r0 | Apache-2.0 | apk-db-cataloger |
| libssl3 | 3.3.3-r0 | Apache-2.0 | apk-db-cataloger |
| musl | 1.2.5-r9 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r9 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| mvdan.cc/xurls/v2 | v2.5.0 |  | go-module-binary-cataloger |
| nhooyr.io/websocket | v1.8.7 |  | go-module-binary-cataloger |
| scanelf | 1.3.8-r1 | GPL-2.0-only | apk-db-cataloger |
| sigs.k8s.io/gateway-api | v1.2.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20221116044647-bc3834ca7abd |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v4 | v4.4.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.4.0 |  | go-module-binary-cataloger |
| ssl_client | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| stdlib | go1.23.9 | BSD-3-Clause | go-module-binary-cataloger |
| traefik | 3.4.1 |  | binary-classifier-cataloger |
| tzdata | 2025b-r0 |  | apk-db-cataloger |
| zlib | 1.3.1-r2 | Zlib | apk-db-cataloger |

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
| anyio | 4.8.0 | MIT | python-installed-package-cataloger |
| api | 0.1.0 | MIT | python-installed-package-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| asgiref | 3.11.1 | BSD-3-Clause | python-installed-package-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| backports-tarfile | 1.2.0 | MIT | python-installed-package-cataloger |
| base-files | 12.4+deb12u12 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b9 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| billiard | 4.2.1 |  | python-installed-package-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20230311+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| celery | 5.5.3 | BSD-3-Clause | python-installed-package-cataloger |
| celery-types | 0.24.0 | Apache-2.0 | python-installed-package-cataloger |
| certifi | 2025.1.31 | MPL-2.0 | python-installed-package-cataloger |
| cffi | 1.17.1 | MIT | python-installed-package-cataloger |
| charset-normalizer | 3.4.1 | MIT | python-installed-package-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| click | 8.1.8 | BSD-3-Clause | python-installed-package-cataloger |
| click-didyoumean | 0.3.1 | MIT | python-installed-package-cataloger |
| click-plugins | 1.1.1 |  | python-installed-package-cataloger |
| click-repl | 0.3.0 | MIT | python-installed-package-cataloger |
| common | 0.1.0 | MIT | python-installed-package-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cryptography | 44.0.2 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u2 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dnspython | 2.7.0 | ISC | python-installed-package-cataloger |
| dpkg | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| elastic-transport | 8.17.0 | Apache-2.0 | python-installed-package-cataloger |
| elasticsearch | 9.0.2 | Apache-2.0 | python-installed-package-cataloger |
| fastapi | 0.128.8 | MIT | python-installed-package-cataloger |
| filelock | 3.17.0 | Unlicense | python-installed-package-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gpgv | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| h11 | 0.14.0 | MIT | python-installed-package-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| httpcore | 1.0.8 | BSD-3-Clause | python-installed-package-cataloger |
| httpx | 0.28.1 | BSD-3-Clause | python-installed-package-cataloger |
| idna | 3.10 | BSD-3-Clause | python-installed-package-cataloger |
| imapclient | 3.1.0 |  | python-installed-package-cataloger |
| importlib-metadata | 8.0.0 | Apache-2.0 | python-installed-package-cataloger |
| importlib-metadata | 8.7.1 | Apache-2.0 | python-installed-package-cataloger |
| inflect | 7.3.1 | MIT | python-installed-package-cataloger |
| init-system-helpers | 1.65.2+deb12u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| jaraco-collections | 5.1.0 | MIT | python-installed-package-cataloger |
| jaraco-context | 5.3.0 | MIT | python-installed-package-cataloger |
| jaraco-functools | 4.0.1 | MIT | python-installed-package-cataloger |
| jaraco-text | 3.12.1 | MIT | python-installed-package-cataloger |
| joblib | 1.4.2 |  | python-installed-package-cataloger |
| kombu | 5.5.4 | BSD-3-Clause | python-installed-package-cataloger |
| libacl1 | 2.3.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4+deb12u2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdebconfclient0 | 0.270 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libext2fs2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi8 | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libgcc-s1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.1-3 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u5 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libhogweed6 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libidn2-0 | 2.3.3-1+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libk5crypto3 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libncursesw6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libreadline8 | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libretranslatepy | 2.1.4 |  | python-installed-package-cataloger |
| libseccomp2 | 2.5.4-1+deb12u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.4-1 |  | dpkg-db-cataloger |
| libsemanage2 | 3.4-1+b5 |  | dpkg-db-cataloger |
| libsepol2 | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsmartcols1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2+deb12u2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssl3 | 3.0.17-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 252.39-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2+deb12u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libudev1 | 252.39-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libzstd1 | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+deb12u1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| luqum | 0.14.0 | LGPL-3.0-only | python-installed-package-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| more-itertools | 10.3.0 | MIT | python-installed-package-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| my-test-package | 1.0 |  | python-installed-package-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| numpy | 1.26.4 | BSD-3-Clause | python-installed-package-cataloger |
| ollama | 0.6.1 | MIT | python-installed-package-cataloger |
| openssl | 3.0.17-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| opentelemetry-api | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-prometheus | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-asgi | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-fastapi | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-sdk | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-semantic-conventions | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-util-http | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| packaging | 24.2 | Apache-2.0, BSD-2-Clause | python-installed-package-cataloger |
| packaging | 25.0 |  | python-installed-package-cataloger |
| passwd | 1:4.13+dfsg1-1+deb12u1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pip | 24.0 | MIT | python-installed-package-cataloger |
| pip | 26.0.1 | MIT | python-installed-package-cataloger |
| platformdirs | 4.2.2 | MIT | python-installed-package-cataloger |
| ply | 3.11 |  | python-installed-package-cataloger |
| prometheus-client | 0.24.1 | Apache-2.0 AND BSD-2-Clause | python-installed-package-cataloger |
| prompt-toolkit | 3.0.50 |  | python-installed-package-cataloger |
| pycparser | 2.22 | BSD-3-Clause | python-installed-package-cataloger |
| pycryptodome | 3.21.0 |  | python-installed-package-cataloger |
| pydantic | 2.10.6 | MIT | python-installed-package-cataloger |
| pydantic-core | 2.27.2 | MIT | python-installed-package-cataloger |
| pydantic-mongo | 2.3.0 | MIT | python-installed-package-cataloger |
| pydantic-settings | 2.8.1 | MIT | python-installed-package-cataloger |
| pymongo | 4.11.2 | Apache-2.0 | python-installed-package-cataloger |
| python | 3.11.13 |  | binary-classifier-cataloger |
| python-dateutil | 2.9.0.post0 |  | python-installed-package-cataloger |
| python-dotenv | 1.0.1 | BSD-3-Clause | python-installed-package-cataloger |
| python-multipart | 0.0.22 | Apache-2.0 | python-installed-package-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| redis | 5.2.1 | MIT | python-installed-package-cataloger |
| requests | 2.32.3 | Apache-2.0 | python-installed-package-cataloger |
| scikit-learn | 1.8.0 | BSD-3-Clause | python-installed-package-cataloger |
| scipy | 1.15.2 | BSD-3-Clause | python-installed-package-cataloger |
| sed | 4.9-1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| setuptools | 65.5.1 | MIT | python-installed-package-cataloger |
| setuptools | 76.0.0 | MIT | python-installed-package-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| sniffio | 1.3.1 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| starlette | 0.46.1 | BSD-3-Clause | python-installed-package-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| threadpoolctl | 3.5.0 | BSD-3-Clause | python-installed-package-cataloger |
| tomli | 2.0.1 | MIT | python-installed-package-cataloger |
| typeguard | 4.3.0 | MIT | python-installed-package-cataloger |
| types-cffi | 1.16.0.20250307 | Apache-2.0 | python-installed-package-cataloger |
| types-pyopenssl | 24.1.0.20240722 |  | python-installed-package-cataloger |
| types-redis | 4.6.0.20241004 | Apache-2.0 | python-installed-package-cataloger |
| types-requests | 2.32.0.20250306 | Apache-2.0 | python-installed-package-cataloger |
| types-setuptools | 75.8.2.20250305 | Apache-2.0 | python-installed-package-cataloger |
| typing-extensions | 4.12.2 |  | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| typing-inspection | 0.4.2 | MIT | python-installed-package-cataloger |
| tzdata | 2025.2 | Apache-2.0 | python-installed-package-cataloger |
| tzdata | 2025b-0+deb12u2 |  | dpkg-db-cataloger |
| urllib3 | 2.3.0 |  | python-installed-package-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uvicorn | 0.40.0 | BSD-3-Clause | python-installed-package-cataloger |
| vine | 5.1.0 |  | python-installed-package-cataloger |
| wcwidth | 0.2.13 | MIT | python-installed-package-cataloger |
| websockets | 13.1 | BSD-3-Clause | python-installed-package-cataloger |
| wheel | 0.43.0 | MIT | python-installed-package-cataloger |
| wheel | 0.45.1 | MIT | python-installed-package-cataloger |
| wrapt | 1.17.3 |  | python-installed-package-cataloger |
| zipp | 3.19.2 | MIT | python-installed-package-cataloger |
| zipp | 3.23.0 | MIT | python-installed-package-cataloger |
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
| anyio | 4.9.0 | MIT | python-installed-package-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| autoconf | 2.71-3 | GFDL-1.3-only, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| automake | 1:1.16.5-1.3 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| autotools-dev | 20220109.1 | GPL-3.0-only | dpkg-db-cataloger |
| backports-tarfile | 1.2.0 | MIT | python-installed-package-cataloger |
| base-files | 12.4+deb12u12 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b9 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| billiard | 4.2.1 |  | python-installed-package-cataloger |
| binutils | 2.40-2 |  | dpkg-db-cataloger |
| binutils-common | 2.40-2 |  | dpkg-db-cataloger |
| binutils-x86-64-linux-gnu | 2.40-2 |  | dpkg-db-cataloger |
| binwalk | 2.3.3 |  | python-installed-package-cataloger |
| binwalk | 2.3.4+dfsg1-1 |  | dpkg-db-cataloger |
| blobfile | 2.1.1 |  | python-installed-package-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| bzip2 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| ca-certificates | 20230311+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| cabextract | 1.9-3 |  | dpkg-db-cataloger |
| celery | 5.5.3 | BSD-3-Clause | python-installed-package-cataloger |
| celery-types | 0.24.0 | Apache-2.0 | python-installed-package-cataloger |
| certifi | 2025.4.26 | MPL-2.0 | python-installed-package-cataloger |
| cffi | 1.17.1 | MIT | python-installed-package-cataloger |
| charset-normalizer | 3.4.2 | MIT | python-installed-package-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| click | 8.2.1 | BSD-3-Clause | python-installed-package-cataloger |
| click-didyoumean | 0.3.1 | MIT | python-installed-package-cataloger |
| click-plugins | 1.1.1 |  | python-installed-package-cataloger |
| click-repl | 0.3.0 | MIT | python-installed-package-cataloger |
| comerr-dev | 2.1-1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| common | 0.1.0 | MIT | python-installed-package-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cpp | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| cpp-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| cryptography | 45.0.4 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| curl | 7.88.1-10+deb12u14 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u2 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| default-libmysqlclient-dev | 1.1.0 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dirmngr | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| dnspython | 2.7.0 | ISC | python-installed-package-cataloger |
| dpkg | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dpkg-dev | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| elastic-transport | 8.17.1 |  | python-installed-package-cataloger |
| elasticsearch | 9.0.2 | Apache-2.0 | python-installed-package-cataloger |
| fastapi | 0.128.0 | MIT | python-installed-package-cataloger |
| file | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| filelock | 3.18.0 | Unlicense | python-installed-package-cataloger |
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
| gir1.2-gdkpixbuf-2.0 | 2.42.10+dfsg-1+deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| gir1.2-glib-2.0 | 1.74.0-3 | AFL-2.0, Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, CC0-1.0, FSFAP, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| gir1.2-rsvg-2.0 | 2.54.7+dfsg-1~deb12u1 | 0BSD, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-3.0, FSFAP, LGPL-2.0-only, LGPL-2.0-or-later, MPL-2.0, OFL-1.1, Unlicense, Zlib | dpkg-db-cataloger |
| git | 1:2.39.5-0+deb12u2 | Apache-2.0, BSD-3-Clause, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| git-man | 1:2.39.5-0+deb12u2 | Apache-2.0, BSD-3-Clause, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| gnupg | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-l10n | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-utils | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gotenberg-client | 0.13.1 | MPL-2.0 | python-installed-package-cataloger |
| gpg | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-wks-client | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-wks-server | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgv | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| h11 | 0.16.0 | MIT | python-installed-package-cataloger |
| h2 | 4.3.0 | MIT | python-installed-package-cataloger |
| hicolor-icon-theme | 0.17-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| hpack | 4.1.0 | MIT | python-installed-package-cataloger |
| httpcore | 1.0.9 | BSD-3-Clause | python-installed-package-cataloger |
| httpx | 0.28.1 | BSD-3-Clause | python-installed-package-cataloger |
| humanize | 4.12.3 | MIT | python-installed-package-cataloger |
| hyperframe | 6.1.0 | MIT | python-installed-package-cataloger |
| icu-devtools | 72.1-3+deb12u1 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| idna | 3.10 | BSD-3-Clause | python-installed-package-cataloger |
| imagemagick | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| imagemagick-6-common | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| imagemagick-6.q16 | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| imapclient | 3.0.1 |  | python-installed-package-cataloger |
| importlib-metadata | 8.7.1 | Apache-2.0 | python-installed-package-cataloger |
| init-system-helpers | 1.65.2+deb12u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| jaraco-context | 6.1.0 | MIT | python-installed-package-cataloger |
| jaraco-functools | 4.4.0 | MIT | python-installed-package-cataloger |
| jaraco-text | 4.0.0 | MIT | python-installed-package-cataloger |
| joblib | 1.5.1 |  | python-installed-package-cataloger |
| jsonpatch | 1.33 |  | python-installed-package-cataloger |
| jsonpointer | 3.0.0 |  | python-installed-package-cataloger |
| kombu | 5.5.4 | BSD-3-Clause | python-installed-package-cataloger |
| krb5-multidev | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| langchain-core | 1.2.7 | MIT | python-installed-package-cataloger |
| langchain-text-splitters | 0.3.11 | MIT | python-installed-package-cataloger |
| langsmith | 0.3.45 | MIT | python-installed-package-cataloger |
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
| libc-bin | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc-dev-bin | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6-dev | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcairo-gobject2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo-script-interpreter2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2-dev | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4+deb12u2+b2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcap2-bin | 1:2.66-4+deb12u2+b2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcbor0.8 | 0.8.0-2+b1 |  | dpkg-db-cataloger |
| libcc1-0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt-dev | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libctf-nobfd0 | 2.40-2 |  | dpkg-db-cataloger |
| libctf0 | 2.40-2 |  | dpkg-db-cataloger |
| libcups2 | 2.4.2-3+deb12u9 | Apache-2.0, BSD-2-Clause, FSFUL, Zlib | dpkg-db-cataloger |
| libcurl3-gnutls | 7.88.1-10+deb12u14 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4 | 7.88.1-10+deb12u14 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4-openssl-dev | 7.88.1-10+deb12u14 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
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
| libdpkg-perl | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libedit2 | 3.1-20221030-2 | BSD-3-Clause | dpkg-db-cataloger |
| libelf1 | 0.188-2.1 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| liberror-perl | 0.17029-2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libevent-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-core-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-dev | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-extra-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-openssl-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libevent-pthreads-2.1-7 | 2.1.12-stable-8 | BSD-2-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, curl | dpkg-db-cataloger |
| libexif-dev | 0.6.24-1+b1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libexif12 | 0.6.24-1+b1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
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
| libgcrypt20 | 1.10.1-3 | GPL-2.0-only | dpkg-db-cataloger |
| libgd3 | 2.3.3-9 | BSD-3-Clause, GD, GPL-2.0-only, GPL-2.0-or-later, HPND, MIT, Xfig | dpkg-db-cataloger |
| libgdbm-compat4 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm-dev | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdk-pixbuf-2.0-0 | 2.42.10+dfsg-1+deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf-2.0-dev | 2.42.10+dfsg-1+deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf2.0-bin | 2.42.10+dfsg-1+deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf2.0-common | 2.42.10+dfsg-1+deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgif7 | 5.2.1-2.5 | ISC, MIT | dpkg-db-cataloger |
| libgirepository-1.0-1 | 1.74.0-3 | AFL-2.0, Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, CC0-1.0, FSFAP, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-0 | 2.74.6-2+deb12u7 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-bin | 2.74.6-2+deb12u7 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-data | 2.74.6-2+deb12u7 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-dev | 2.74.6-2+deb12u7 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-dev-bin | 2.74.6-2+deb12u7 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgmp-dev | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgmpxx4ldbl | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u5 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgprofng0 | 2.40-2 |  | dpkg-db-cataloger |
| libgraphite2-3 | 1.3.14-1 | GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libgs-common | 10.0.0~dfsg-11+deb12u8 | AGPL-3.0-only, AGPL-3.0-or-later, Apache-2.0, BSD-3-Clause, FTL, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, MIT-open-group, X11, Zlib | dpkg-db-cataloger |
| libgs10 | 10.0.0~dfsg-11+deb12u8 | AGPL-3.0-only, AGPL-3.0-or-later, Apache-2.0, BSD-3-Clause, FTL, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, MIT-open-group, X11, Zlib | dpkg-db-cataloger |
| libgs10-common | 10.0.0~dfsg-11+deb12u8 | AGPL-3.0-only, AGPL-3.0-or-later, Apache-2.0, BSD-3-Clause, FTL, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, MIT-open-group, X11, Zlib | dpkg-db-cataloger |
| libgsf-1-114 | 1.14.50-1+deb12u1 | FSFUL, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libgsf-1-common | 1.14.50-1+deb12u1 | FSFUL, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libgssrpc4 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
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
| libk5crypto3 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkadm5clnt-mit12 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkadm5srv-mit12 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkdb5-10 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5-dev | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libksba8 | 1.6.3-2 | FSFUL, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblcms2-2 | 2.14-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| liblcms2-dev | 2.14-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
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
| liblzma-dev | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblzo2-2 | 2.10-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmagic-mgc | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| libmagic1 | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| libmagickcore-6-arch-config | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-6-headers | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-6.q16-6 | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-6.q16-6-extra | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-6.q16-dev | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickcore-dev | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-6-headers | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-6.q16-6 | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-6.q16-dev | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-dev | 8:6.9.11.60+dfsg-1.6+deb12u6 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmariadb-dev | 1:10.11.14-0+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmariadb-dev-compat | 1:10.11.14-0+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmariadb3 | 1:10.11.14-0+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmaxminddb-dev | 1.7.1-1 | Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmaxminddb0 | 1.7.1-1 | Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount-dev | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmpc3 | 1.3.1-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libmpfr6 | 4.2.0-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libmspack0 | 0.11-1 | LGPL-2.1-only | dpkg-db-cataloger |
| libncurses-dev | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncurses5-dev | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncurses6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncursesw5-dev | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncursesw6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.52.0-1+deb12u2 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnl-3-200 | 3.7.0-0.2+b1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libnl-genl-3-200 | 3.7.0-0.2+b1 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libnpth0 | 1.6-3 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnsl-dev | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnuma1 | 2.0.16-1 |  | dpkg-db-cataloger |
| libopenexr-3-1-30 | 3.1.5-5 | BSD-3-Clause | dpkg-db-cataloger |
| libopenexr-dev | 3.1.5-5 | BSD-3-Clause | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.0-2+deb12u2 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libopenjp2-7-dev | 2.5.0-2+deb12u2 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
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
| libpng-dev | 1.6.39-2 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpng16-16 | 1.6.39-2 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpq-dev | 15.14-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libpq5 | 15.14-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.2-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpsl5 | 0.21.2-1 | MIT | dpkg-db-cataloger |
| libpst4 | 0.6.76-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libpthread-stubs0-dev | 0.4-1 |  | dpkg-db-cataloger |
| libpython3-stdlib | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| libpython3.11-minimal | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-stdlib | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| libquadmath0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| librav1e0 | 0.5.1-6 | BSD-2-Clause, BSD-2-Clause, ISC | dpkg-db-cataloger |
| libreadline-dev | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libreadline8 | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libretranslatepy | 2.1.4 |  | python-installed-package-cataloger |
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
| libssl-dev | 3.0.17-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libssl3 | 3.0.17-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++-12-dev | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsvn1 | 1.14.2-4+deb12u1 | AFL-3.0, Apache-2.0, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libsvtav1enc1 | 1.4.1+dfsg-1 | BSD-2-Clause, BSD-3-Clause-Clear, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsystemd0 | 252.39-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2+deb12u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtcl8.6 | 8.6.13+dfsg-2 |  | dpkg-db-cataloger |
| libthai-data | 0.1.29-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libthai0 | 0.1.29-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtiff-dev | 4.5.0-6+deb12u2 |  | dpkg-db-cataloger |
| libtiff6 | 4.5.0-6+deb12u2 |  | dpkg-db-cataloger |
| libtiffxx6 | 4.5.0-6+deb12u2 |  | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc-dev | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtk8.6 | 8.6.13-2 |  | dpkg-db-cataloger |
| libtool | 2.4.7-7~deb12u1 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libtsan2 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libubsan1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libudev1 | 252.39-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libutf8proc2 | 2.8.0-1 |  | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libwebp-dev | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebp7 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebpdemux2 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebpmux3 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwireshark-data | 4.0.17-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwireshark16 | 4.0.17-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwiretap13 | 4.0.17-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwmf-0.2-7 | 0.2.12-5.1 | AGPL-3.0-only, GD, ISC, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwmf-dev | 0.2.12-5.1 | AGPL-3.0-only, GD, ISC, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwmflite-0.2-7 | 0.2.12-5.1 | AGPL-3.0-only, GD, ISC, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libwsutil14 | 4.0.17-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
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
| libxml2 | 2.9.14+dfsg-1.3~deb12u4 | ISC | dpkg-db-cataloger |
| libxml2-dev | 2.9.14+dfsg-1.3~deb12u4 | ISC | dpkg-db-cataloger |
| libxpm4 | 1:3.5.12-1.1+deb12u1 | MIT | dpkg-db-cataloger |
| libxrender-dev | 1:0.9.10-1.1 | HPND-sell-variant | dpkg-db-cataloger |
| libxrender1 | 1:0.9.10-1.1 | HPND-sell-variant | dpkg-db-cataloger |
| libxslt1-dev | 1.1.35-1+deb12u3 |  | dpkg-db-cataloger |
| libxslt1.1 | 1.1.35-1+deb12u3 |  | dpkg-db-cataloger |
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
| linux-libc-dev | 6.1.153-1 | BSD-2-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+deb12u1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| luqum | 0.14.0 | LGPL-3.0-only | python-installed-package-cataloger |
| lxml | 4.9.4 | BSD-3-Clause | python-installed-package-cataloger |
| m4 | 1.4.19-3 |  | dpkg-db-cataloger |
| make | 4.3-4.1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| mariadb-common | 1:10.11.14-0+deb12u2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 10.0.0 |  | dpkg-db-cataloger |
| mercurial | 6.3.2 |  | python-installed-package-cataloger |
| mercurial | 6.3.2-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| mercurial-common | 6.3.2-1+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| more-itertools | 10.8.0 | MIT | python-installed-package-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| mysql-common | 5.8+1.1.0 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| numpy | 2.3.0 | BSD-3-Clause | python-installed-package-cataloger |
| ollama | 0.6.1 | MIT | python-installed-package-cataloger |
| openssh-client | 1:9.2p1-2+deb12u7 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| openssl | 3.0.17-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| orjson | 3.10.18 | Apache-2.0 OR MIT | python-installed-package-cataloger |
| packaging | 24.2 | Apache-2.0, BSD-2-Clause | python-installed-package-cataloger |
| packaging | 26.0 | Apache-2.0 OR BSD-2-Clause | python-installed-package-cataloger |
| passwd | 1:4.13+dfsg1-1+deb12u1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.7.6-7 |  | dpkg-db-cataloger |
| perl | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-modules-5.36 | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pinentry-curses | 1.2.1-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| pip | 24.0 | MIT | python-installed-package-cataloger |
| pip | 26.0.1 | MIT | python-installed-package-cataloger |
| pkg-config | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| pkgconf | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| pkgconf-bin | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| platformdirs | 4.4.0 | MIT | python-installed-package-cataloger |
| ply | 3.11 |  | python-installed-package-cataloger |
| poppler-data | 0.4.12-1 | AGPL-3.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| procps | 2:4.0.2-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| prometheus-client | 0.22.1 | Apache-2.0 AND BSD-2-Clause | python-installed-package-cataloger |
| prompt-toolkit | 3.0.51 |  | python-installed-package-cataloger |
| pst-utils | 0.6.76-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| pycparser | 2.22 | BSD-3-Clause | python-installed-package-cataloger |
| pycryptodome | 3.23.0 |  | python-installed-package-cataloger |
| pycryptodomex | 3.23.0 |  | python-installed-package-cataloger |
| pydantic | 2.11.5 | MIT | python-installed-package-cataloger |
| pydantic-core | 2.33.2 | MIT | python-installed-package-cataloger |
| pydantic-mongo | 2.4.0 | MIT | python-installed-package-cataloger |
| pydantic-settings | 2.9.1 | MIT | python-installed-package-cataloger |
| pymongo | 4.13.1 | Apache-2.0 | python-installed-package-cataloger |
| python | 3.11.13 |  | binary-classifier-cataloger |
| python-dateutil | 2.9.0.post0 |  | python-installed-package-cataloger |
| python-dotenv | 1.1.0 | BSD-3-Clause | python-installed-package-cataloger |
| python-magic | 0.4.27 | MIT | python-installed-package-cataloger |
| python3 | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3-binwalk | 2.3.4+dfsg1-1 |  | dpkg-db-cataloger |
| python3-distutils | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-lib2to3 | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-minimal | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3.11 | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| python3.11-minimal | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| pytz | 2025.2 | MIT | python-installed-package-cataloger |
| pyyaml | 6.0.2 | MIT | python-installed-package-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| redis | 5.2.1 | MIT | python-installed-package-cataloger |
| requests | 2.32.5 | Apache-2.0 | python-installed-package-cataloger |
| requests-toolbelt | 1.0.0 |  | python-installed-package-cataloger |
| rpcsvc-proto | 1.4.3-1 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, MIT | dpkg-db-cataloger |
| scikit-learn | 1.8.0 | BSD-3-Clause | python-installed-package-cataloger |
| scipy | 1.17.0 | BSD-3-Clause | python-installed-package-cataloger |
| sed | 4.9-1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sensible-utils | 0.0.17+nmu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| setuptools | 65.5.1 | MIT | python-installed-package-cataloger |
| setuptools | 82.0.0 | MIT | python-installed-package-cataloger |
| shared-mime-info | 2.2-1 |  | dpkg-db-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| sniffio | 1.3.1 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| sq | 0.27.0-2+b1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| starlette | 0.46.2 | BSD-3-Clause | python-installed-package-cataloger |
| stream-zip | 0.0.84 |  | python-installed-package-cataloger |
| subversion | 1.14.2-4+deb12u1 | AFL-3.0, Apache-2.0, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tcl | 8.6.13 |  | dpkg-db-cataloger |
| tcl-dev | 8.6.13 |  | dpkg-db-cataloger |
| tcl8.6 | 8.6.13+dfsg-2 |  | dpkg-db-cataloger |
| tcl8.6-dev | 8.6.13+dfsg-2 |  | dpkg-db-cataloger |
| tenacity | 9.1.2 |  | python-installed-package-cataloger |
| threadpoolctl | 3.6.0 | BSD-3-Clause | python-installed-package-cataloger |
| tk | 8.6.13 |  | dpkg-db-cataloger |
| tk-dev | 8.6.13 |  | dpkg-db-cataloger |
| tk8.6 | 8.6.13-2 |  | dpkg-db-cataloger |
| tk8.6-dev | 8.6.13-2 |  | dpkg-db-cataloger |
| tomli | 2.4.0 | MIT | python-installed-package-cataloger |
| tornado | 6.5.1 | Apache-2.0 | python-installed-package-cataloger |
| tshark | 4.0.17-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| types-cffi | 1.17.0.20250523 | Apache-2.0 | python-installed-package-cataloger |
| types-pyopenssl | 24.1.0.20240722 |  | python-installed-package-cataloger |
| types-redis | 4.6.0.20241004 | Apache-2.0 | python-installed-package-cataloger |
| types-requests | 2.32.4.20250611 | Apache-2.0 | python-installed-package-cataloger |
| types-setuptools | 80.9.0.20250529 | Apache-2.0 | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| typing-inspection | 0.4.1 | MIT | python-installed-package-cataloger |
| tzdata | 2025.2 | Apache-2.0 | python-installed-package-cataloger |
| tzdata | 2025b-0+deb12u2 |  | dpkg-db-cataloger |
| ucf | 3.0043+nmu1+deb12u1 | GPL-2.0-only | dpkg-db-cataloger |
| unzip | 6.0-28 |  | dpkg-db-cataloger |
| urllib3 | 2.4.0 | MIT | python-installed-package-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uuid-dev | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uuid-utils | 0.13.0 |  | python-installed-package-cataloger |
| vine | 5.1.0 |  | python-installed-package-cataloger |
| wand | 0.6.13 |  | python-installed-package-cataloger |
| wcwidth | 0.2.13 | MIT | python-installed-package-cataloger |
| wget | 1.21.3-1+deb12u1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| wheel | 0.45.1 | MIT | python-installed-package-cataloger |
| wheel | 0.46.3 | MIT | python-installed-package-cataloger |
| wireshark-common | 4.0.17-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later | dpkg-db-cataloger |
| worker | 0.1.0 | MIT | python-installed-package-cataloger |
| x11-common | 1:7.7+23 |  | dpkg-db-cataloger |
| x11proto-core-dev | 2022.1-1 | MIT | dpkg-db-cataloger |
| x11proto-dev | 2022.1-1 | MIT | dpkg-db-cataloger |
| xfonts-encodings | 1:1.0.4-2.2 |  | dpkg-db-cataloger |
| xfonts-utils | 1:7.7+6 |  | dpkg-db-cataloger |
| xorg-sgml-doctools | 1:1.11-1.1 | HPND-sell-variant, MIT | dpkg-db-cataloger |
| xtrans-dev | 1.4.0-1 | HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| xz-utils | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| zipp | 3.23.0 | MIT | python-installed-package-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zlib1g-dev | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zstandard | 0.23.0 |  | python-installed-package-cataloger |

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
| anyio | 4.7.0 | MIT | python-installed-package-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| argon2-cffi | 23.1.0 | MIT | python-installed-package-cataloger |
| argon2-cffi-bindings | 21.2.0 | MIT | python-installed-package-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| backports-tarfile | 1.2.0 | MIT | python-installed-package-cataloger |
| base-files | 12.4+deb12u12 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b9 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| billiard | 4.2.1 |  | python-installed-package-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20230311+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| celery | 5.5.3 | BSD-3-Clause | python-installed-package-cataloger |
| celery-types | 0.24.0 | Apache-2.0 | python-installed-package-cataloger |
| certifi | 2024.8.30 | MPL-2.0 | python-installed-package-cataloger |
| cffi | 1.17.1 | MIT | python-installed-package-cataloger |
| charset-normalizer | 3.4.0 | MIT | python-installed-package-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| click | 8.1.7 | BSD-3-Clause | python-installed-package-cataloger |
| click-didyoumean | 0.3.1 | MIT | python-installed-package-cataloger |
| click-plugins | 1.1.1 |  | python-installed-package-cataloger |
| click-repl | 0.3.0 | MIT | python-installed-package-cataloger |
| common | 0.1.0 | MIT | python-installed-package-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| crawler | 0.1.0 | MIT | python-installed-package-cataloger |
| cryptography | 44.0.0 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u2 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dnspython | 2.7.0 | ISC | python-installed-package-cataloger |
| dpkg | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| elastic-transport | 8.15.1 | Apache-2.0 | python-installed-package-cataloger |
| elasticsearch | 9.0.2 | Apache-2.0 | python-installed-package-cataloger |
| fastapi | 0.128.0 | MIT | python-installed-package-cataloger |
| filelock | 3.16.1 | Unlicense | python-installed-package-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gpgv | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| h11 | 0.16.0 | MIT | python-installed-package-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| httpcore | 1.0.9 | BSD-3-Clause | python-installed-package-cataloger |
| httpx | 0.28.1 | BSD-3-Clause | python-installed-package-cataloger |
| idna | 3.10 | BSD-3-Clause | python-installed-package-cataloger |
| imapclient | 3.1.0 |  | python-installed-package-cataloger |
| importlib-metadata | 8.7.1 | Apache-2.0 | python-installed-package-cataloger |
| init-system-helpers | 1.65.2+deb12u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| jaraco-context | 6.1.0 | MIT | python-installed-package-cataloger |
| jaraco-functools | 4.4.0 | MIT | python-installed-package-cataloger |
| jaraco-text | 4.0.0 | MIT | python-installed-package-cataloger |
| kombu | 5.5.4 | BSD-3-Clause | python-installed-package-cataloger |
| libacl1 | 2.3.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4+deb12u2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdebconfclient0 | 0.270 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libext2fs2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi8 | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libgcc-s1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.1-3 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u5 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libhogweed6 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libidn2-0 | 2.3.3-1+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libk5crypto3 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libncursesw6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libreadline8 | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libretranslatepy | 2.1.4 |  | python-installed-package-cataloger |
| libseccomp2 | 2.5.4-1+deb12u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.4-1 |  | dpkg-db-cataloger |
| libsemanage2 | 3.4-1+b5 |  | dpkg-db-cataloger |
| libsepol2 | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsmartcols1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2+deb12u2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssl3 | 3.0.17-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 252.39-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2+deb12u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libudev1 | 252.39-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libzstd1 | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+deb12u1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| luqum | 0.14.0 | LGPL-3.0-only | python-installed-package-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| minio | 7.2.20 | Apache-2.0 | python-installed-package-cataloger |
| more-itertools | 10.8.0 | MIT | python-installed-package-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| ollama | 0.6.1 | MIT | python-installed-package-cataloger |
| openssl | 3.0.17-1~deb12u2 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| packaging | 25.0 |  | python-installed-package-cataloger |
| packaging | 26.0 | Apache-2.0 OR BSD-2-Clause | python-installed-package-cataloger |
| passwd | 1:4.13+dfsg1-1+deb12u1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pip | 24.0 | MIT | python-installed-package-cataloger |
| pip | 26.0.1 | MIT | python-installed-package-cataloger |
| platformdirs | 4.4.0 | MIT | python-installed-package-cataloger |
| ply | 3.11 |  | python-installed-package-cataloger |
| prompt-toolkit | 3.0.48 |  | python-installed-package-cataloger |
| pycparser | 2.22 | BSD-3-Clause | python-installed-package-cataloger |
| pycryptodome | 3.21.0 |  | python-installed-package-cataloger |
| pydantic | 2.10.3 | MIT | python-installed-package-cataloger |
| pydantic-core | 2.27.1 | MIT | python-installed-package-cataloger |
| pydantic-mongo | 2.3.0 | MIT | python-installed-package-cataloger |
| pydantic-settings | 2.6.1 | MIT | python-installed-package-cataloger |
| pymongo | 4.10.1 | Apache-2.0 | python-installed-package-cataloger |
| python | 3.11.13 |  | binary-classifier-cataloger |
| python-dateutil | 2.9.0.post0 |  | python-installed-package-cataloger |
| python-dotenv | 1.0.1 | BSD-3-Clause | python-installed-package-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| redis | 5.2.1 | MIT | python-installed-package-cataloger |
| requests | 2.32.3 | Apache-2.0 | python-installed-package-cataloger |
| sed | 4.9-1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| setuptools | 65.5.1 | MIT | python-installed-package-cataloger |
| setuptools | 82.0.0 | MIT | python-installed-package-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| sniffio | 1.3.1 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| starlette | 0.46.1 | BSD-3-Clause | python-installed-package-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tomli | 2.4.0 | MIT | python-installed-package-cataloger |
| types-cffi | 1.16.0.20240331 |  | python-installed-package-cataloger |
| types-pyopenssl | 24.1.0.20240722 |  | python-installed-package-cataloger |
| types-redis | 4.6.0.20241004 | Apache-2.0 | python-installed-package-cataloger |
| types-requests | 2.32.0.20241016 | Apache-2.0 | python-installed-package-cataloger |
| types-setuptools | 75.6.0.20241126 | Apache-2.0 | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| tzdata | 2025.2 | Apache-2.0 | python-installed-package-cataloger |
| tzdata | 2025b-0+deb12u2 |  | dpkg-db-cataloger |
| urllib3 | 2.2.3 |  | python-installed-package-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| vine | 5.1.0 |  | python-installed-package-cataloger |
| watchdog | 6.0.0 | Apache-2.0 | python-installed-package-cataloger |
| wcwidth | 0.2.13 | MIT | python-installed-package-cataloger |
| wheel | 0.45.1 | MIT | python-installed-package-cataloger |
| wheel | 0.46.3 | MIT | python-installed-package-cataloger |
| zipp | 3.23.0 | MIT | python-installed-package-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/frontend

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.5-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.21.3-r0 | MIT | apk-db-cataloger |
| aom-libs | 3.11.0-r0 | BSD-2-Clause | apk-db-cataloger |
| apk-tools | 2.14.6-r3 | GPL-2.0-only | apk-db-cataloger |
| brotli-libs | 1.1.0-r2 | MIT | apk-db-cataloger |
| busybox | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| c-ares | 1.34.5-r0 | MIT | apk-db-cataloger |
| ca-certificates | 20241121-r1 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20241121-r1 | MPL-2.0 AND MIT | apk-db-cataloger |
| curl | 8.12.1-r1 | curl | apk-db-cataloger |
| fontconfig | 2.15.0-r1 | MIT | apk-db-cataloger |
| freetype | 2.13.3-r0 | FTL OR GPL-2.0-or-later | apk-db-cataloger |
| geoip | 1.6.12-r5 | LGPL-2.1-or-later | apk-db-cataloger |
| gettext-envsubst | 0.22.5-r0 | GPL-3.0-or-later AND LGPL-2.1-or-later AND MIT | apk-db-cataloger |
| libavif | 1.0.4-r0 | BSD-2-Clause | apk-db-cataloger |
| libbsd | 0.12.2-r0 | BSD-3-Clause | apk-db-cataloger |
| libbz2 | 1.0.8-r6 | bzip2-1.0.6 | apk-db-cataloger |
| libcrypto3 | 3.3.3-r0 | Apache-2.0 | apk-db-cataloger |
| libcurl | 8.12.1-r1 | curl | apk-db-cataloger |
| libdav1d | 1.5.0-r0 | BSD-2-Clause | apk-db-cataloger |
| libedit | 20240808.3.1-r0 | BSD-3-Clause | apk-db-cataloger |
| libexpat | 2.7.0-r0 | MIT | apk-db-cataloger |
| libgcrypt | 1.10.3-r1 | LGPL-2.1-or-later AND GPL-2.0-or-later | apk-db-cataloger |
| libgd | 2.3.3-r9 | GD | apk-db-cataloger |
| libgpg-error | 1.51-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libice | 1.1.1-r6 | X11 | apk-db-cataloger |
| libidn2 | 2.3.7-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libintl | 0.22.5-r0 | LGPL-2.1-or-later | apk-db-cataloger |
| libjpeg-turbo | 3.0.4-r0 | BSD-3-Clause AND IJG AND Zlib | apk-db-cataloger |
| libmd | 1.1.0-r0 | BSD-2-Clause, BSD-3-Clause, Beerware, ISC | apk-db-cataloger |
| libncursesw | 6.5_p20241006-r3 | X11 | apk-db-cataloger |
| libpng | 1.6.47-r0 | Libpng | apk-db-cataloger |
| libpsl | 0.21.5-r3 | MIT | apk-db-cataloger |
| libsharpyuv | 1.4.0-r0 | BSD-3-Clause | apk-db-cataloger |
| libsm | 1.2.4-r4 | MIT | apk-db-cataloger |
| libssl3 | 3.3.3-r0 | Apache-2.0 | apk-db-cataloger |
| libunistring | 1.2-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libuuid | 2.40.4-r1 | BSD-3-Clause | apk-db-cataloger |
| libwebp | 1.4.0-r0 | BSD-3-Clause | apk-db-cataloger |
| libx11 | 1.8.10-r0 | X11 | apk-db-cataloger |
| libxau | 1.0.11-r4 | MIT | apk-db-cataloger |
| libxcb | 1.16.1-r0 | MIT | apk-db-cataloger |
| libxdmcp | 1.1.5-r1 | MIT | apk-db-cataloger |
| libxext | 1.3.6-r2 | MIT | apk-db-cataloger |
| libxml2 | 2.13.4-r5 | MIT | apk-db-cataloger |
| libxpm | 3.5.17-r0 | X11 | apk-db-cataloger |
| libxslt | 1.1.42-r2 | X11 | apk-db-cataloger |
| libxt | 1.3.1-r0 | MIT | apk-db-cataloger |
| musl | 1.2.5-r9 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r9 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20241006-r3 | X11 | apk-db-cataloger |
| nghttp2-libs | 1.64.0-r0 | MIT | apk-db-cataloger |
| nginx | 1.27.5-r1 |  | apk-db-cataloger |
| nginx-module-geoip | 1.27.5-r1 |  | apk-db-cataloger |
| nginx-module-image-filter | 1.27.5-r1 |  | apk-db-cataloger |
| nginx-module-njs | 1.27.5.0.8.10-r1 |  | apk-db-cataloger |
| nginx-module-xslt | 1.27.5-r1 |  | apk-db-cataloger |
| pcre2 | 10.43-r0 | BSD-3-Clause | apk-db-cataloger |
| scanelf | 1.3.8-r1 | GPL-2.0-only | apk-db-cataloger |
| ssl_client | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| tiff | 4.7.0-r0 | libtiff | apk-db-cataloger |
| tzdata | 2025b-r0 |  | apk-db-cataloger |
| xz-libs | 5.6.3-r1 | 0BSD, GPL-2.0-or-later, LGPL-2.1-or-later | apk-db-cataloger |
| zlib | 1.3.1-r2 | Zlib | apk-db-cataloger |
| zstd-libs | 1.5.6-r2 | BSD-3-Clause OR GPL-2.0-or-later | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/mongodb

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| adduser | 3.118ubuntu5 | GPL-2.0-only | dpkg-db-cataloger |
| apt | 2.4.14 | GPL-2.0-only | dpkg-db-cataloger |
| base-files | 12ubuntu4.7 |  | dpkg-db-cataloger |
| base-passwd | 3.5.52build1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.1-6ubuntu1.1 | GPL-3.0-only | dpkg-db-cataloger |
| bsdutils | 1:2.37.2-4ubuntu3.4 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20240203~22.04.1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| coreutils | 8.32-4.1ubuntu1.2 | GPL-3.0-only | dpkg-db-cataloger |
| dash | 0.5.11+git20210903+057cd650a4ed-3build1 | BSD-3-Clause, BSD-3-Clause, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.79ubuntu1 | BSD-2-Clause | dpkg-db-cataloger |
| debianutils | 5.5-1ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| diffutils | 1:3.8-0ubuntu2 |  | dpkg-db-cataloger |
| dpkg | 1.21.1ubuntu2.6 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.46.5-2ubuntu1.2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| findutils | 4.8.0-1ubuntu3 | GFDL-1.3-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-12-base | 12.3.0-1ubuntu1~22.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.17.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.2 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.2 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.2 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.2 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.2 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.2 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.2 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.2 |  | go-module-binary-cataloger |
| github.com/deckarep/golang-set/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/deckarep/golang-set/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/deckarep/golang-set/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/deckarep/golang-set/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/deckarep/golang-set/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/deckarep/golang-set/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/deckarep/golang-set/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/deckarep/golang-set/v2 | v2.6.0 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.2 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.8 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.8 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.15 |  | go-module-binary-cataloger |
| github.com/moby/sys/user | v0.1.0 |  | go-module-binary-cataloger |
| github.com/mongodb/mongo-tools | UNKNOWN |  | go-module-binary-cataloger |
| github.com/mongodb/mongo-tools | UNKNOWN |  | go-module-binary-cataloger |
| github.com/mongodb/mongo-tools | UNKNOWN |  | go-module-binary-cataloger |
| github.com/mongodb/mongo-tools | UNKNOWN |  | go-module-binary-cataloger |
| github.com/mongodb/mongo-tools | UNKNOWN |  | go-module-binary-cataloger |
| github.com/mongodb/mongo-tools | UNKNOWN |  | go-module-binary-cataloger |
| github.com/mongodb/mongo-tools | UNKNOWN |  | go-module-binary-cataloger |
| github.com/mongodb/mongo-tools | UNKNOWN |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/nsf/termbox-go | v1.1.1 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.4.7 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.49.1 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.49.1 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.49.1 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.49.1 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.49.1 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.49.1 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.49.1 |  | go-module-binary-cataloger |
| github.com/samber/lo | v1.49.1 |  | go-module-binary-cataloger |
| github.com/tianon/gosu | v1.19.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/pbkdf2 | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/scram | v1.1.2 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/xdg-go/stringprep | v1.0.4 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| github.com/youmark/pkcs8 | v0.0.0-20240726163527-a2c0da244d78 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.3 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.3 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.3 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.3 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.3 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.3 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.3 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.3 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250128182459-e0ece0dbea4c |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250128182459-e0ece0dbea4c |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250128182459-e0ece0dbea4c |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250128182459-e0ece0dbea4c |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250128182459-e0ece0dbea4c |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250128182459-e0ece0dbea4c |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250128182459-e0ece0dbea4c |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250128182459-e0ece0dbea4c |  | go-module-binary-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.1.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.25.0 |  | go-module-binary-cataloger |
| gopkg.in/tomb.v2 | v2.0.0-20161208151619-d5d1b5820637 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gpgv | 2.2.27-3ubuntu2.4 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.7-1build1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gzip | 1.10-4ubuntu4.1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hostname | 3.23ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| init-system-helpers | 1.62 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| jq | 1.6-2.1ubuntu3.1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| js-yaml | 3.13.1 | MIT | javascript-package-cataloger |
| libacl1 | 2.3.1-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.4.14 | GPL-2.0-only | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-1build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.7-1build1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.7-1build1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblkid1 | 2.37.2-4ubuntu3.4 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbrotli1 | 1.0.9-2build6 | MIT | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5build1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.35-0ubuntu3.11 | GFDL-1.3-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.35-0ubuntu3.11 | GFDL-1.3-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.7.9-2.2build3 | GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap2 | 1:2.44-1ubuntu0.22.04.2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.46.5-2ubuntu1.2 |  | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.27-1 |  | dpkg-db-cataloger |
| libcurl4 | 7.81.0-1ubuntu1.21 | BSD-3-Clause, BSD-4-Clause, ISC, curl | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg1-0.8ubuntu3 |  | dpkg-db-cataloger |
| libdebconfclient0 | 0.261ubuntu1 | BSD-2-Clause | dpkg-db-cataloger |
| libext2fs2 | 1.46.5-2ubuntu1.2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| libffi8 | 3.4.2-4 |  | dpkg-db-cataloger |
| libgcc-s1 | 12.3.0-1ubuntu1~22.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.9.4-3ubuntu3 | GPL-2.0-only | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg-3ubuntu1 | GPL-2.0-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgnutls30 | 3.7.3-4ubuntu1.7 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.43-3 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.19.2-2ubuntu0.7 | GPL-2.0-only | dpkg-db-cataloger |
| libhogweed6 | 3.7.3-1build2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libidn2-0 | 2.3.2-2build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libjq1 | 1.6-2.1ubuntu3.1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| libk5crypto3 | 1.19.2-2ubuntu0.7 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.1-2ubuntu3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.19.2-2ubuntu0.7 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.19.2-2ubuntu0.7 | GPL-2.0-only | dpkg-db-cataloger |
| libldap-2.5-0 | 2.5.19+dfsg-0ubuntu0.22.04.1 |  | dpkg-db-cataloger |
| libldap-common | 2.5.19+dfsg-0ubuntu0.22.04.1 |  | dpkg-db-cataloger |
| liblz4-1 | 1.9.3-2build2 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.2.5-2ubuntu1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmount1 | 2.37.2-4ubuntu3.4 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libncurses6 | 6.3-2ubuntu0.1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libncursesw6 | 6.3-2ubuntu0.1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.7.3-1build2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.43.0-1ubuntu0.2 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2build2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnuma1 | 2.0.14-3ubuntu2 |  | dpkg-db-cataloger |
| libonig5 | 6.9.7.1-2build1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libp11-kit0 | 0.24.0-6build1 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.4.0-11ubuntu2.6 |  | dpkg-db-cataloger |
| libpam-modules-bin | 1.4.0-11ubuntu2.6 |  | dpkg-db-cataloger |
| libpam-runtime | 1.4.0-11ubuntu2.6 |  | dpkg-db-cataloger |
| libpam0g | 1.4.0-11ubuntu2.6 |  | dpkg-db-cataloger |
| libpcre2-8-0 | 10.39-3ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre3 | 2:8.39-13ubuntu0.22.04.1 |  | dpkg-db-cataloger |
| libprocps8 | 2:3.3.17-6ubuntu2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpsl5 | 0.21.0-1.2build2 | MIT | dpkg-db-cataloger |
| librtmp1 | 2.4+20151223.gitfa8646d.1-2build4 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsasl2-2 | 2.1.27+dfsg2-3ubuntu1.2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules | 2.1.27+dfsg2-3ubuntu1.2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.27+dfsg2-3ubuntu1.2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libseccomp2 | 2.5.3-2ubuntu3~22.04.1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.3-1build2 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.3-1build2 |  | dpkg-db-cataloger |
| libsemanage2 | 3.3-1build2 |  | dpkg-db-cataloger |
| libsepol2 | 3.3-1build1 |  | dpkg-db-cataloger |
| libsmartcols1 | 2.37.2-4ubuntu3.4 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libss2 | 1.46.5-2ubuntu1.2 |  | dpkg-db-cataloger |
| libssh-4 | 0.9.6-2ubuntu0.22.04.5 | BSD-2-Clause, BSD-3-Clause, LGPL-2.1-only | dpkg-db-cataloger |
| libssl3 | 3.0.2-0ubuntu1.20 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 12.3.0-1ubuntu1~22.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 249.11-0ubuntu3.17 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.18.0-4ubuntu0.1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.3-2ubuntu0.1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.2-2ubuntu0.1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.2-2ubuntu0.1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libudev1 | 249.11-0ubuntu3.17 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-1 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.37.2-4ubuntu3.4 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libzstd1 | 1.4.8+dfsg-3build1 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.8.1-2ubuntu2.2 | GPL-2.0-only | dpkg-db-cataloger |
| logsave | 1.46.5-2ubuntu1.2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| lsb-base | 11.1.0ubuntu4 | BSD-3-Clause, GPL-2.0-only | dpkg-db-cataloger |
| mawk | 1.3.4.20200120-3 | GPL-2.0-only | dpkg-db-cataloger |
| mongodb-database-tools | 100.13.0 |  | dpkg-db-cataloger |
| mongodb-mongosh | 2.5.9 | Apache-2.0 | dpkg-db-cataloger |
| mongodb-org | 7.0.25 |  | dpkg-db-cataloger |
| mongodb-org-database | 7.0.25 |  | dpkg-db-cataloger |
| mongodb-org-database-tools-extra | 7.0.25 |  | dpkg-db-cataloger |
| mongodb-org-mongos | 7.0.25 |  | dpkg-db-cataloger |
| mongodb-org-server | 7.0.25 |  | dpkg-db-cataloger |
| mongodb-org-shell | 7.0.25 |  | dpkg-db-cataloger |
| mongodb-org-tools | 7.0.25 |  | dpkg-db-cataloger |
| mount | 2.37.2-4ubuntu3.4 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ncurses-base | 6.3-2ubuntu0.1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.3-2ubuntu0.1 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| numactl | 2.0.14-3ubuntu2 |  | dpkg-db-cataloger |
| openssl | 3.0.2-0ubuntu1.20 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| passwd | 1:4.8.1-2ubuntu2.2 | GPL-2.0-only | dpkg-db-cataloger |
| perl-base | 5.34.0-3ubuntu1.5 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| procps | 2:3.3.17-6ubuntu2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| publicsuffix | 20211207.1025-1 | MPL-2.0 | dpkg-db-cataloger |
| sed | 4.8-1ubuntu2 | GPL-3.0-only | dpkg-db-cataloger |
| sensible-utils | 0.0.17 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| stdlib | go1.23.11 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.11 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.11 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.11 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.11 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.11 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.11 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.11 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.24.6 | BSD-3-Clause | go-module-binary-cataloger |
| sysvinit-utils | 3.01-1ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| tar | 1.34+dfsg-1ubuntu0.1.22.04.2 | GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tzdata | 2025b-0ubuntu0.22.04.1 | ICU | dpkg-db-cataloger |
| ubuntu-keyring | 2021.03.26 |  | dpkg-db-cataloger |
| usrmerge | 25ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| util-linux | 2.37.2-4ubuntu3.4 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| zlib1g | 1:1.2.11.dfsg-2ubuntu9.2 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/elasticsearch

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| HdrHistogram | 2.1.9 |  | java-archive-cataloger |
| SparseBitSet | 1.3 |  | java-archive-cataloger |
| accessors-smart | 2.5.2 |  | java-archive-cataloger |
| accessors-smart | 2.5.2 |  | java-archive-cataloger |
| aggregations | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| aggregations | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| alternatives | 1.24-2.el9 | GPL-2.0-only | rpm-db-cataloger |
| analysis-common | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| analysis-icu | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| analysis-smartcn | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| analysis-stempel | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| analysis-ukrainian | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| annotations | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| antlr4-runtime | 4.13.1 |  | java-archive-cataloger |
| apache-mime4j-core | 0.8.12 | Apache-2.0 | java-archive-cataloger |
| apache-mime4j-dom | 0.8.12 | Apache-2.0 | java-archive-cataloger |
| api-common | 2.3.1 |  | java-archive-cataloger |
| apm | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| apm-agent | 1.52.2 |  | java-archive-cataloger |
| apm-agent-cached-lookup-key | 1.52.2 |  | java-archive-cataloger |
| apm-agent-common | 1.52.2 |  | java-archive-cataloger |
| apm-agent-common | 1.52.2 |  | java-archive-cataloger |
| apm-agent-core | 1.52.2 |  | java-archive-cataloger |
| apm-agent-plugin-sdk | 1.52.2 |  | java-archive-cataloger |
| apm-agent-tracer | 1.52.2 |  | java-archive-cataloger |
| apm-apache-httpclient-common | 1.52.2 |  | java-archive-cataloger |
| apm-apache-httpclient3-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-apache-httpclient4-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-apache-httpclient5-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-api-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-asynchttpclient-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-aws-sdk-1-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-aws-sdk-2-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-aws-sdk-common | 1.52.2 |  | java-archive-cataloger |
| apm-awslambda-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-cassandra-core-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-cassandra3-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-cassandra4-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-dubbo-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-ecs-logging-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-es-restclient-plugin-5_6 | 1.52.2 |  | java-archive-cataloger |
| apm-es-restclient-plugin-6_4 | 1.52.2 |  | java-archive-cataloger |
| apm-es-restclient-plugin-7_x | 1.52.2 |  | java-archive-cataloger |
| apm-es-restclient-plugin-8_x | 1.52.2 |  | java-archive-cataloger |
| apm-es-restclient-plugin-common | 1.52.2 |  | java-archive-cataloger |
| apm-finagle-httpclient-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-grails-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-grpc-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-hibernate-search-plugin-5_x | 1.52.2 |  | java-archive-cataloger |
| apm-hibernate-search-plugin-6_x | 1.52.2 |  | java-archive-cataloger |
| apm-hibernate-search-plugin-common | 1.52.2 |  | java-archive-cataloger |
| apm-httpclient-core | 1.52.2 |  | java-archive-cataloger |
| apm-httpserver-core | 1.52.2 |  | java-archive-cataloger |
| apm-jakarta-websocket-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-java-concurrent-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-java-ldap-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-javalin-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jaxrs-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jaxws-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jboss-logging-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jdbc-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jdk-httpclient-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jdk-httpserver-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jedis-4-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jedis-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jms-jakarta | 1.52.2 |  | java-archive-cataloger |
| apm-jms-javax | 1.52.2 |  | java-archive-cataloger |
| apm-jms-plugin-base | 1.52.2 |  | java-archive-cataloger |
| apm-jmx-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jsf-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-jul-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-kafka-base-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-kafka-headers-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-kafka-spring-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-lettuce-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-log4j1-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-log4j2-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-logback-plugin-impl | 1.52.2 |  | java-archive-cataloger |
| apm-logging-plugin-common | 1.52.2 |  | java-archive-cataloger |
| apm-micrometer-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-mongodb-common | 1.52.2 |  | java-archive-cataloger |
| apm-mongodb3-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-mongodb4-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-okhttp-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-opentelemetry-embedded-metrics-sdk | 1.52.2 |  | java-archive-cataloger |
| apm-opentelemetry-metrics-bridge-common | 1.52.2 |  | java-archive-cataloger |
| apm-opentelemetry-metrics-bridge-latest | 1.52.2 |  | java-archive-cataloger |
| apm-opentelemetry-metrics-bridge-v1_14 | 1.52.2 |  | java-archive-cataloger |
| apm-opentelemetry-metricsdk-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-opentelemetry-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-opentracing-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-process-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-profiling-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-quartz-common | 1.52.2 |  | java-archive-cataloger |
| apm-quartz-plugin-1 | 1.52.2 |  | java-archive-cataloger |
| apm-quartz-plugin-2 | 1.52.2 |  | java-archive-cataloger |
| apm-rabbitmq-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-rabbitmq-spring5 | 1.52.2 |  | java-archive-cataloger |
| apm-reactor-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-redis-common | 1.52.2 |  | java-archive-cataloger |
| apm-redisson-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-scala-concurrent-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-scheduled-annotation-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-servlet-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-slf4j-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-sparkjava-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-spring-resttemplate-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-spring-webclient-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-spring-webflux-common | 1.52.2 |  | java-archive-cataloger |
| apm-spring-webflux-common-spring5 | 1.52.2 |  | java-archive-cataloger |
| apm-spring-webflux-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-spring-webflux-spring5 | 1.52.2 |  | java-archive-cataloger |
| apm-spring-webmvc-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-spring-webmvc-spring5 | 1.52.2 |  | java-archive-cataloger |
| apm-struts-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-tomcat-logging-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-urlconnection-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-vertx-common | 1.52.2 |  | java-archive-cataloger |
| apm-vertx3-plugin | 1.52.2 |  | java-archive-cataloger |
| apm-vertx4-plugin | 1.52.2 |  | java-archive-cataloger |
| arrow | 9.0.2 |  | java-archive-cataloger |
| arrow-format | 16.1.0 | Apache-2.0 | java-archive-cataloger |
| arrow-memory-core | 16.1.0 | Apache-2.0 | java-archive-cataloger |
| arrow-vector | 16.1.0 | Apache-2.0 | java-archive-cataloger |
| asm | 7.2 |  | java-archive-cataloger |
| asm | 7.2 |  | java-archive-cataloger |
| asm | 9.7.1 |  | java-archive-cataloger |
| asm | 9.7.1 |  | java-archive-cataloger |
| asm | 9.7.1 |  | java-archive-cataloger |
| asm-analysis | 7.2 |  | java-archive-cataloger |
| asm-analysis | 7.2 |  | java-archive-cataloger |
| asm-commons | 7.2 |  | java-archive-cataloger |
| asm-commons | 7.2 |  | java-archive-cataloger |
| asm-jdk-bridge | 0.0.2 |  | java-archive-cataloger |
| asm-tree | 7.2 |  | java-archive-cataloger |
| asm-tree | 7.2 |  | java-archive-cataloger |
| asm-tree | 9.7.1 |  | java-archive-cataloger |
| asm-util | 7.2 |  | java-archive-cataloger |
| audit-libs | 3.1.5-4.el9 |  | rpm-db-cataloger |
| auth | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| aws-core | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| aws-java-sdk-core | 1.12.746 |  | java-archive-cataloger |
| aws-java-sdk-s3 | 1.12.746 |  | java-archive-cataloger |
| aws-java-sdk-sts | 1.12.746 |  | java-archive-cataloger |
| aws-json-protocol | 2.28.13 | Apache-2.0 | java-archive-cataloger |
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
| bc-fips | 1.0.2.5 |  | java-archive-cataloger |
| bcpg-fips | 1.0.7.1 |  | java-archive-cataloger |
| bcpkix-jdk18on | 1.78.1 |  | java-archive-cataloger |
| bcprov-jdk18on | 1.78.1 |  | java-archive-cataloger |
| bcutil-jdk18on | 1.78.1 |  | java-archive-cataloger |
| bedrockruntime | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| blob-cache | 9.0.2 |  | java-archive-cataloger |
| byte-buddy-dep | 1.17.0 |  | java-archive-cataloger |
| bzip2-libs | 1.0.8-10.el9_5 |  | rpm-db-cataloger |
| ca-certificates | 2024.2.69_v8.0.303-91.4.el9_4 | MIT AND GPL-2.0-or-later | rpm-db-cataloger |
| checker-qual | 3.42.0 | MIT | java-archive-cataloger |
| checksums | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| checksums-spi | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| cli-launcher | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.15 | Apache-2.0 | java-archive-cataloger |
| commons-codec | 1.18.0 | Apache-2.0 | java-archive-cataloger |
| commons-collections4 | 4.4 | Apache-2.0 | java-archive-cataloger |
| commons-compress | 1.27.1 | Apache-2.0 | java-archive-cataloger |
| commons-io | 2.18.0 | Apache-2.0 | java-archive-cataloger |
| commons-lang3 | 3.17.0 | Apache-2.0 | java-archive-cataloger |
| commons-lang3 | 3.9 | Apache-2.0 | java-archive-cataloger |
| commons-logging | 1.2 |  | java-archive-cataloger |
| commons-logging | 1.2 |  | java-archive-cataloger |
| commons-logging | 1.2 |  | java-archive-cataloger |
| commons-logging | 1.2 |  | java-archive-cataloger |
| commons-logging | 1.2 |  | java-archive-cataloger |
| commons-math3 | 3.6.1 |  | java-archive-cataloger |
| commons-math3 | 3.6.1 |  | java-archive-cataloger |
| commons-math3 | 3.6.1 |  | java-archive-cataloger |
| compiler | 0.9.10 |  | java-archive-cataloger |
| compiler | 0.9.10 |  | java-archive-cataloger |
| compiler | 0.9.10 |  | java-archive-cataloger |
| concurrentlinkedhashmap-lru | 1.4.2 |  | java-archive-cataloger |
| content-type | 2.3 | Apache-2.0 | java-archive-cataloger |
| core | 9.0.2 | Apache-2.0 | java-archive-cataloger |
| coreutils-single | 8.32-39.el9 |  | rpm-db-cataloger |
| cryptacular | 1.2.5 |  | java-archive-cataloger |
| cryptacular | 1.2.5 |  | java-archive-cataloger |
| crypto-policies | 20250128-1.git5269e22.el9 | LGPL-2.1-or-later | rpm-db-cataloger |
| curl-minimal | 7.76.1-31.el9 | MIT | rpm-db-cataloger |
| cyrus-sasl-lib | 2.1.27-21.el9 |  | rpm-db-cataloger |
| data-streams | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| dejavu-sans-fonts | 2.37-18.el9 |  | rpm-db-cataloger |
| dnf-data | 4.14.0-25.el9 |  | rpm-db-cataloger |
| dot-prefix-validation | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| dsl-json | 1.9.3 |  | java-archive-cataloger |
| ecs-logging-core | 1.2.0 | Apache-2.0 | java-archive-cataloger |
| ecs-logging-core | 1.6.0 |  | java-archive-cataloger |
| elastic-apm-agent | 1.52.2 | Apache-2.0 | java-archive-cataloger |
| elastic-apm-agent-premain | 1.52.2 |  | java-archive-cataloger |
| elasticsearch | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-ansi-console | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-cli | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-core | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-core | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-dissect | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-dissect | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-dissect | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-entitlement | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-entitlement | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-entitlement-agent | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-entitlement-bridge | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-geo | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-geoip-cli | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-grok | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-h3 | 9.0.2 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-logging | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-lz4 | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-native | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-analysis-api | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-api | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-api | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-cli | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-plugin-scanner | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-rest-client | 9.0.2 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-rest-client | 9.0.2 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-rest-client | 9.0.2 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-rest-client-sniffer | 9.0.2 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-scripting-painless-spi | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-secure-sm | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-security-cli | 9.0.2 |  | java-archive-cataloger |
| elasticsearch-simdvec | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-sql-cli | 9.0.2 | Apache-2.0, LGPL-2.1-only | java-archive-cataloger |
| elasticsearch-ssl-config | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-ssl-config | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-ssl-config | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-ssl-config | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-tdigest | 9.0.2 | Apache-2.0 | java-archive-cataloger |
| elasticsearch-x-content | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| elasticsearch-x-content | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| endpoints-spi | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| eventstream | 1.0.1 |  | java-archive-cataloger |
| failureaccess | 1.0.1 |  | java-archive-cataloger |
| failureaccess | 1.0.1 |  | java-archive-cataloger |
| failureaccess | 1.0.1 |  | java-archive-cataloger |
| failureaccess | 1.0.1 |  | java-archive-cataloger |
| file-libs | 5.39-16.el9 |  | rpm-db-cataloger |
| filesystem | 3.16-5.el9 |  | rpm-db-cataloger |
| findutils | 1:4.8.0-7.el9 |  | rpm-db-cataloger |
| flatbuffers-java | 23.5.26 |  | java-archive-cataloger |
| fontbox | 2.0.33 | Apache-2.0 | java-archive-cataloger |
| fonts-filesystem | 1:2.0.5-7.el9.1 | MIT | rpm-db-cataloger |
| gawk | 5.1.0-6.el9 |  | rpm-db-cataloger |
| gax | 2.20.1 |  | java-archive-cataloger |
| gax-httpjson | 0.105.1 |  | java-archive-cataloger |
| gax-httpjson | 0.105.1 |  | java-archive-cataloger |
| gdbm-libs | 1:1.23-1.el9 |  | rpm-db-cataloger |
| geoip2 | 4.2.0 |  | java-archive-cataloger |
| glib2 | 2.68.4-16.el9 |  | rpm-db-cataloger |
| glibc | 2.34-168.el9_6.20 |  | rpm-db-cataloger |
| glibc-common | 2.34-168.el9_6.20 |  | rpm-db-cataloger |
| glibc-minimal-langpack | 2.34-168.el9_6.20 |  | rpm-db-cataloger |
| gmp | 1:6.2.0-13.el9 |  | rpm-db-cataloger |
| gnupg2 | 2.3.3-4.el9 |  | rpm-db-cataloger |
| gnutls | 3.8.3-6.el9 |  | rpm-db-cataloger |
| gobject-introspection | 1.68.0-11.el9 |  | rpm-db-cataloger |
| google-api-client | 2.1.1 |  | java-archive-cataloger |
| google-api-client | 2.1.1 |  | java-archive-cataloger |
| google-api-services-storage | v1-rev20220705-2.0.0 |  | java-archive-cataloger |
| google-api-services-storage-v1-rev20220705 | 2.0.0 |  | java-archive-cataloger |
| google-auth-library-credentials | 1.11.0 |  | java-archive-cataloger |
| google-auth-library-credentials | 1.11.0 |  | java-archive-cataloger |
| google-auth-library-oauth2-http | 1.11.0 |  | java-archive-cataloger |
| google-auth-library-oauth2-http | 1.11.0 |  | java-archive-cataloger |
| google-cloud-core | 2.8.28 |  | java-archive-cataloger |
| google-cloud-core-http | 2.8.28 |  | java-archive-cataloger |
| google-cloud-storage | 2.13.1 | Apache-2.0 | java-archive-cataloger |
| google-http-client | 1.42.3 |  | java-archive-cataloger |
| google-http-client | 1.42.3 |  | java-archive-cataloger |
| google-http-client-appengine | 1.42.3 |  | java-archive-cataloger |
| google-http-client-appengine | 1.42.3 |  | java-archive-cataloger |
| google-http-client-gson | 1.42.3 |  | java-archive-cataloger |
| google-http-client-gson | 1.42.3 |  | java-archive-cataloger |
| google-http-client-jackson2 | 1.42.3 |  | java-archive-cataloger |
| google-http-client-jackson2 | 1.42.3 |  | java-archive-cataloger |
| google-oauth-client | 1.34.1 | Apache-2.0 | java-archive-cataloger |
| google-oauth-client | 1.34.1 | Apache-2.0 | java-archive-cataloger |
| gpg-pubkey | 5a6340b3-6229229e |  | rpm-db-cataloger |
| gpg-pubkey | fd431d51-4ae0493b |  | rpm-db-cataloger |
| gpgme | 1.15.1-6.el9 |  | rpm-db-cataloger |
| grep | 3.6-5.el9 |  | rpm-db-cataloger |
| grpc-context | 1.49.2 |  | java-archive-cataloger |
| grpc-context | 1.49.2 |  | java-archive-cataloger |
| gson | 2.10 |  | java-archive-cataloger |
| gson | 2.10 |  | java-archive-cataloger |
| gson | 2.11.0 |  | java-archive-cataloger |
| gson | 2.12.1 | Apache-2.0 | java-archive-cataloger |
| gson | 2.12.1 | Apache-2.0 | java-archive-cataloger |
| guava | 32.0.1-jre |  | java-archive-cataloger |
| guava | 32.0.1-jre |  | java-archive-cataloger |
| guava | 32.0.1-jre |  | java-archive-cataloger |
| guava | 32.0.1-jre |  | java-archive-cataloger |
| guava | 32.0.1-jre |  | java-archive-cataloger |
| health-shards-availability | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| hppc | 0.8.1 |  | java-archive-cataloger |
| http-auth | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| http-auth-aws | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| http-auth-aws-eventstream | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| http-auth-spi | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| http-client-spi | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| httpasyncclient | 4.1.5 | Apache-2.0 | java-archive-cataloger |
| httpasyncclient | 4.1.5 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient-cache | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpclient-cache | 4.5.14 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore-nio | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| httpcore-nio | 4.4.16 | Apache-2.0 | java-archive-cataloger |
| icu4j | 68.2 |  | java-archive-cataloger |
| icu4j | 68.2 |  | java-archive-cataloger |
| icu4j | 68.2 |  | java-archive-cataloger |
| icu4j | 68.2 |  | java-archive-cataloger |
| identity-spi | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| ingest-attachment | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| ingest-common | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| ingest-geoip | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| ingest-user-agent | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| isorelax | 20090621 |  | java-archive-cataloger |
| jackson-annotations | 2.15.0 | Apache-2.0 | java-archive-cataloger |
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
| jackson-core | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-core | 2.17.2 |  | java-archive-cataloger |
| jackson-core | 2.17.2 |  | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-databind | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-dataformat-cbor | 2.15.0 |  | java-archive-cataloger |
| jackson-dataformat-cbor | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-dataformat-cbor | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jackson-dataformat-cbor | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-cbor | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-smile | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-smile | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-xml | 2.15.0 |  | java-archive-cataloger |
| jackson-dataformat-yaml | 2.17.2 |  | java-archive-cataloger |
| jackson-dataformat-yaml | 2.17.2 |  | java-archive-cataloger |
| jackson-datatype-jsr310 | 2.15.0 |  | java-archive-cataloger |
| jackson-module-jaxb-annotations | 2.15.0 | Apache-2.0 | java-archive-cataloger |
| jakarta.activation | 1.2.1 |  | java-archive-cataloger |
| jakarta.activation-api | 1.2.1 |  | java-archive-cataloger |
| jakarta.mail | 1.6.3 |  | java-archive-cataloger |
| jakarta.mail | 1.6.4 |  | java-archive-cataloger |
| jakarta.xml.bind-api | 2.3.3 |  | java-archive-cataloger |
| jansi | 2.4.0 |  | java-archive-cataloger |
| java-support | 8.4.0 |  | java-archive-cataloger |
| java-support | 8.4.0 |  | java-archive-cataloger |
| java-version-checker | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| jaxb-api | 2.2.2 | CDDL-1.0, GPL-2.0-only | java-archive-cataloger |
| jcip-annotations | 1.0 |  | java-archive-cataloger |
| jcip-annotations | 1.0-1 |  | java-archive-cataloger |
| jcip-annotations | 1.0-1 |  | java-archive-cataloger |
| jcip-annotations | 1.0-1 |  | java-archive-cataloger |
| jcl-over-slf4j | 2.0.16 | Apache-2.0 | java-archive-cataloger |
| jcodings | 1.0.44 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jctools-core | 4.0.5 |  | java-archive-cataloger |
| jdk | 24+36-3646 |  | java-jvm-cataloger |
| jempbox | 1.8.17 |  | java-archive-cataloger |
| jline-reader | 3.21.0 |  | java-archive-cataloger |
| jline-style | 3.21.0 |  | java-archive-cataloger |
| jline-terminal | 3.21.0 |  | java-archive-cataloger |
| jline-terminal-jna | 3.21.0 |  | java-archive-cataloger |
| jmespath-java | 1.12.746 |  | java-archive-cataloger |
| jna | 5.12.1 | Apache-2.0, LGPL-2.1-only | java-archive-cataloger |
| jna-platform | 5.12.1 | Apache-2.0, LGPL-2.1-only | java-archive-cataloger |
| joda-time | 2.10.10 |  | java-archive-cataloger |
| joda-time | 2.10.14 |  | java-archive-cataloger |
| joni | 2.1.29 |  | java-archive-cataloger |
| jopt-simple | 5.0.2 |  | java-archive-cataloger |
| jopt-simple | 5.0.2 |  | java-archive-cataloger |
| jrt-fs | 24 |  | java-archive-cataloger |
| json-c | 0.14-11.el9 | MIT | rpm-db-cataloger |
| json-glib | 1.6.6-1.el9 |  | rpm-db-cataloger |
| json-schema-validator | 1.0.48 |  | java-archive-cataloger |
| json-smart | 2.5.2 |  | java-archive-cataloger |
| json-smart | 2.5.2 |  | java-archive-cataloger |
| json-utils | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| jsr305 | 3.0.2 |  | java-archive-cataloger |
| jsr305 | 3.0.2 |  | java-archive-cataloger |
| jts-core | 1.15.0 |  | java-archive-cataloger |
| jul-ecs-formatter | 1.6.0 |  | java-archive-cataloger |
| juniversalchardet | 1.0.3 |  | java-archive-cataloger |
| keystore-cli | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| keyutils-libs | 1.6.3-1.el9 |  | rpm-db-cataloger |
| kibana | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| krb5-libs | 1.21.1-8.el9_6 | MIT | rpm-db-cataloger |
| lang-expression | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-mustache | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-mustache | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-mustache | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-painless | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| lang-tag | 1.7 | Apache-2.0 | java-archive-cataloger |
| lang-tag | 1.7 | Apache-2.0 | java-archive-cataloger |
| langpacks-core-en | 3.0-16.el9 |  | rpm-db-cataloger |
| langpacks-core-font-en | 3.0-16.el9 |  | rpm-db-cataloger |
| langpacks-en | 3.0-16.el9 |  | rpm-db-cataloger |
| legacy-geo | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| libacl | 2.3.1-4.el9 |  | rpm-db-cataloger |
| libarchive | 3.5.3-5.el9_6 |  | rpm-db-cataloger |
| libassuan | 2.5.5-3.el9 |  | rpm-db-cataloger |
| libattr | 2.5.1-3.el9 |  | rpm-db-cataloger |
| libblkid | 2.37.4-21.el9 |  | rpm-db-cataloger |
| libcap | 2.48-9.el9_2 |  | rpm-db-cataloger |
| libcap-ng | 0.8.2-7.el9 |  | rpm-db-cataloger |
| libcom_err | 1.46.5-7.el9 | MIT | rpm-db-cataloger |
| libcurl-minimal | 7.76.1-31.el9 | MIT | rpm-db-cataloger |
| libdnf | 0.69.0-13.el9 |  | rpm-db-cataloger |
| libevent | 2.1.12-8.el9_4 |  | rpm-db-cataloger |
| libffi | 3.4.2-8.el9 | MIT | rpm-db-cataloger |
| libgcc | 11.5.0-5.el9_5 |  | rpm-db-cataloger |
| libgcrypt | 1.10.0-11.el9 |  | rpm-db-cataloger |
| libgpg-error | 1.42-5.el9 |  | rpm-db-cataloger |
| libibverbs | 54.0-1.el9 |  | rpm-db-cataloger |
| libidn2 | 2.3.0-7.el9 |  | rpm-db-cataloger |
| libksba | 1.5.1-7.el9 |  | rpm-db-cataloger |
| libmodulemd | 2.13.0-2.el9 | MIT | rpm-db-cataloger |
| libmount | 2.37.4-21.el9 |  | rpm-db-cataloger |
| libnghttp2 | 1.43.0-6.el9 | MIT | rpm-db-cataloger |
| libnl3 | 3.11.0-1.el9 | LGPL-2.1-only | rpm-db-cataloger |
| libpcap | 14:1.10.0-4.el9 |  | rpm-db-cataloger |
| libpeas | 1.30.0-4.el9 |  | rpm-db-cataloger |
| librepo | 1.14.5-2.el9 |  | rpm-db-cataloger |
| libreport-filesystem | 2.15.2-6.el9 |  | rpm-db-cataloger |
| librhsm | 0.0.3-9.el9 |  | rpm-db-cataloger |
| libselinux | 3.6-3.el9 |  | rpm-db-cataloger |
| libsemanage | 3.6-5.el9_6 |  | rpm-db-cataloger |
| libsepol | 3.6-2.el9 |  | rpm-db-cataloger |
| libsigsegv | 2.13-4.el9 |  | rpm-db-cataloger |
| libsmartcols | 2.37.4-21.el9 |  | rpm-db-cataloger |
| libsolv | 0.7.24-3.el9 |  | rpm-db-cataloger |
| libstdc++ | 11.5.0-5.el9_5 |  | rpm-db-cataloger |
| libtasn1 | 4.16.0-9.el9 |  | rpm-db-cataloger |
| libtool-ltdl | 2.4.6-46.el9 |  | rpm-db-cataloger |
| libunistring | 0.9.10-15.el9 |  | rpm-db-cataloger |
| libusbx | 1.0.26-1.el9 |  | rpm-db-cataloger |
| libuuid | 2.37.4-21.el9 |  | rpm-db-cataloger |
| libverto | 0.3.2-3.el9 | MIT | rpm-db-cataloger |
| libxcrypt | 4.4.18-3.el9 |  | rpm-db-cataloger |
| libxml2 | 2.9.13-9.el9_6 | MIT | rpm-db-cataloger |
| libyaml | 0.2.5-7.el9 | MIT | rpm-db-cataloger |
| libzstd | 1.5.5-1.el9 |  | rpm-db-cataloger |
| log4j-1.2-api | 2.19.0 | Apache-2.0 | java-archive-cataloger |
| log4j-1.2-api | 2.19.0 | Apache-2.0 | java-archive-cataloger |
| log4j-1.2-api | 2.19.0 | Apache-2.0 | java-archive-cataloger |
| log4j-1.2-api | 2.19.0 | Apache-2.0 | java-archive-cataloger |
| log4j-api | 2.12.4 |  | java-archive-cataloger |
| log4j-api | 2.19.0 | Apache-2.0 | java-archive-cataloger |
| log4j-core | 2.12.4 |  | java-archive-cataloger |
| log4j-core | 2.19.0 |  | java-archive-cataloger |
| log4j-ecs-layout | 1.6.0 |  | java-archive-cataloger |
| log4j-slf4j-impl | 2.12.4 |  | java-archive-cataloger |
| log4j-slf4j-impl | 2.19.0 | Apache-2.0 | java-archive-cataloger |
| log4j2-ecs-layout | 1.2.0 | Apache-2.0 | java-archive-cataloger |
| log4j2-ecs-layout | 1.6.0 |  | java-archive-cataloger |
| logback-ecs-encoder | 1.6.0 |  | java-archive-cataloger |
| lua-libs | 5.4.4-4.el9 | MIT | rpm-db-cataloger |
| lucene-analysis-common | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-icu | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-icu | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-kuromoji | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-morfologik | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-smartcn | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-analysis-stempel | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-backward-codecs | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-codecs | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-core | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-expressions | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-facet | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-grouping | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-highlighter | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-join | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-memory | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-misc | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-queries | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-queryparser | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-sandbox | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-spatial-extras | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-spatial3d | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lucene-suggest | 10.1.0 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, ICU, MIT | java-archive-cataloger |
| lz4-java | 1.8.0 |  | java-archive-cataloger |
| lz4-libs | 1.9.3-5.el9 |  | rpm-db-cataloger |
| mapbox-vector-tile | 3.1.0 |  | java-archive-cataloger |
| mapper-extras | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| maxmind-db | 3.1.0 |  | java-archive-cataloger |
| metrics-core | 4.1.4 | Apache-2.0 | java-archive-cataloger |
| metrics-core | 4.1.4 | Apache-2.0 | java-archive-cataloger |
| metrics-spi | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| microdnf | 3.9.1-3.el9 |  | rpm-db-cataloger |
| ml-package-loader | 9.0.2 |  | java-archive-cataloger |
| morfologik-fsa | 2.1.1 |  | java-archive-cataloger |
| morfologik-stemming | 2.1.1 |  | java-archive-cataloger |
| morfologik-ukrainian-search | 3.7.5 |  | java-archive-cataloger |
| mpfr | 4.1.0-7.el9 |  | rpm-db-cataloger |
| msal4j | 1.16.2 |  | java-archive-cataloger |
| msal4j-persistence-extension | 1.3.0 |  | java-archive-cataloger |
| ncurses-base | 6.2-10.20210508.el9 | MIT | rpm-db-cataloger |
| ncurses-libs | 6.2-10.20210508.el9 | MIT | rpm-db-cataloger |
| nettle | 3.10.1-1.el9 |  | rpm-db-cataloger |
| netty-buffer | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-buffer | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-buffer | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-buffer | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-dns | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-dns | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http2 | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-http2 | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-codec-socks | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-common | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-common | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-common | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-common | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-handler-proxy | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-nio-client | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| netty-resolver | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver-dns | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-resolver-dns | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-classes-epoll | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-native-unix-common | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-native-unix-common | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-native-unix-common | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| netty-transport-native-unix-common | 4.1.118.Final | Apache-2.0 | java-archive-cataloger |
| nimbus-jose-jwt | 10.0.2 | Apache-2.0 | java-archive-cataloger |
| nimbus-jose-jwt | 10.0.2 |  | java-archive-cataloger |
| nimbus-jose-jwt-modified | 9.0.2 |  | java-archive-cataloger |
| nmap-ncat | 3:7.92-3.el9 |  | rpm-db-cataloger |
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
| openssl-fips-provider | 3.0.7-6.el9_5 |  | rpm-db-cataloger |
| openssl-fips-provider-so | 3.0.7-6.el9_5 |  | rpm-db-cataloger |
| openssl-libs | 1:3.2.2-6.el9_5.1 |  | rpm-db-cataloger |
| opentelemetry-api | 1.31.0 |  | java-archive-cataloger |
| opentelemetry-context | 1.31.0 |  | java-archive-cataloger |
| opentelemetry-semconv | 1.21.0-alpha |  | java-archive-cataloger |
| owasp-java-html-sanitizer | 20211018.2 |  | java-archive-cataloger |
| p11-kit | 0.25.3-3.el9_5 | BSD-3-Clause | rpm-db-cataloger |
| p11-kit-trust | 0.25.3-3.el9_5 | BSD-3-Clause | rpm-db-cataloger |
| parent-join | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| pcre | 8.44-4.el9 |  | rpm-db-cataloger |
| pcre2 | 10.40-6.el9 |  | rpm-db-cataloger |
| pcre2-syntax | 10.40-6.el9 |  | rpm-db-cataloger |
| pdfbox | 2.0.33 | Apache-2.0 | java-archive-cataloger |
| percolator | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| poi | 5.4.0 | Apache-2.0, MIT | java-archive-cataloger |
| poi-ooxml | 5.4.0 | Apache-2.0, MIT | java-archive-cataloger |
| poi-ooxml-lite | 5.4.0 | Apache-2.0, MIT | java-archive-cataloger |
| poi-scratchpad | 5.4.0 | Apache-2.0, MIT | java-archive-cataloger |
| popt | 1.18-8.el9 | MIT | rpm-db-cataloger |
| procps-ng | 3.3.17-14.el9 |  | rpm-db-cataloger |
| profiles | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| proto-google-common-protos | 2.9.6 | Apache-2.0 | java-archive-cataloger |
| proto-google-iam-v1 | 1.6.2 | Apache-2.0 | java-archive-cataloger |
| proto-google-iam-v1 | 1.6.2 | Apache-2.0 | java-archive-cataloger |
| protobuf-java | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java-util | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protobuf-java-util | 3.25.5 | BSD-3-Clause | java-archive-cataloger |
| protocol-core | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| rank-eval | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| rank-rrf | 9.0.2 |  | java-archive-cataloger |
| rank-vectors | 9.0.2 |  | java-archive-cataloger |
| reactive-streams | 1.0.4 |  | java-archive-cataloger |
| reactive-streams | 1.0.4 |  | java-archive-cataloger |
| reactive-streams-tck | 1.0.4 |  | java-archive-cataloger |
| reactor-core | 3.4.38 |  | java-archive-cataloger |
| reactor-netty-core | 1.0.45 |  | java-archive-cataloger |
| reactor-netty-http | 1.0.45 |  | java-archive-cataloger |
| readline | 8.1-4.el9 |  | rpm-db-cataloger |
| redhat-release | 9.6-0.1.el9 |  | rpm-db-cataloger |
| regions | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| reindex | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| reindex | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| repository-azure | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| repository-gcs | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| repository-s3 | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| repository-url | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| rest-root | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| retries | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| retries-spi | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| rootfiles | 8.1-34.el9 |  | rpm-db-cataloger |
| rpm | 4.16.1.3-37.el9 |  | rpm-db-cataloger |
| rpm-libs | 4.16.1.3-37.el9 |  | rpm-db-cataloger |
| runtime-fields-common | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| s2-geometry-library-java | 1.0.1 |  | java-archive-cataloger |
| sdk-core | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| sed | 4.8-9.el9 |  | rpm-db-cataloger |
| server-cli | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| setup | 2.13.7-10.el9 |  | rpm-db-cataloger |
| shadow-utils | 2:4.9-12.el9 |  | rpm-db-cataloger |
| siv-mode | 1.5.2 |  | java-archive-cataloger |
| slf4j-api | 1.7.36 |  | java-archive-cataloger |
| slf4j-api | 2.0.16 |  | java-archive-cataloger |
| slf4j-api | 2.0.6 |  | java-archive-cataloger |
| slf4j-api | 2.0.6 |  | java-archive-cataloger |
| slf4j-api | 2.0.6 |  | java-archive-cataloger |
| slf4j-api | 2.0.6 |  | java-archive-cataloger |
| slf4j-api | 2.0.6 |  | java-archive-cataloger |
| slf4j-api | 2.0.6 |  | java-archive-cataloger |
| slf4j-api | 2.0.6 |  | java-archive-cataloger |
| slf4j-nop | 2.0.16 |  | java-archive-cataloger |
| slf4j-nop | 2.0.6 |  | java-archive-cataloger |
| slf4j-nop | 2.0.6 |  | java-archive-cataloger |
| slf4j-nop | 2.0.6 |  | java-archive-cataloger |
| slf4j-nop | 2.0.6 |  | java-archive-cataloger |
| slf4j-nop | 2.0.6 |  | java-archive-cataloger |
| slf4j-nop | 2.0.6 |  | java-archive-cataloger |
| snakeyaml | 2.0 |  | java-archive-cataloger |
| snakeyaml | 2.0 |  | java-archive-cataloger |
| spatial | 9.0.2 |  | java-archive-cataloger |
| spatial4j | 0.7 |  | java-archive-cataloger |
| sql-action | 9.0.2 |  | java-archive-cataloger |
| sql-proto | 9.0.2 |  | java-archive-cataloger |
| sqlite-libs | 3.34.1-7.el9_3 |  | rpm-db-cataloger |
| stax2-api | 4.2.2 |  | java-archive-cataloger |
| super-csv | 2.4.0 |  | java-archive-cataloger |
| systemd-libs | 252-51.el9_6.1 |  | rpm-db-cataloger |
| tagsoup | 1.2.1 |  | java-archive-cataloger |
| third-party-jackson-core | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| threetenbp | 1.6.5 |  | java-archive-cataloger |
| tika-core | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-langdetect-tika | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-apple-module | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-html-module | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-microsoft-module | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-miscoffice-module | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-pdf-module | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-text-module | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-xml-module | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-xmp-commons | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| tika-parser-zip-commons | 2.9.3 | Apache-2.0 | java-archive-cataloger |
| transform | 9.0.2 |  | java-archive-cataloger |
| transport-netty4 | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| transport-netty4 | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| transport-netty4 | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| tzdata | 2025b-1.el9 |  | rpm-db-cataloger |
| unboundid-ldapsdk | 6.0.3 | GPL-2.0-only, LGPL-2.1-only | java-archive-cataloger |
| unzip | 6.0-58.el9_5 |  | rpm-db-cataloger |
| utils | 2.28.13 | Apache-2.0 | java-archive-cataloger |
| vector-tile | 9.0.2 |  | java-archive-cataloger |
| weak-lock-free | 0.18 |  | java-archive-cataloger |
| windows-service-cli | 9.0.2 | AGPL-3.0-only, SSPL-1.0 | java-archive-cataloger |
| woodstox-core | 6.7.0 |  | java-archive-cataloger |
| x-pack-aggregate-metric | 9.0.2 |  | java-archive-cataloger |
| x-pack-analytics | 9.0.2 |  | java-archive-cataloger |
| x-pack-apm-data | 9.0.2 |  | java-archive-cataloger |
| x-pack-async | 9.0.2 |  | java-archive-cataloger |
| x-pack-async-search | 9.0.2 |  | java-archive-cataloger |
| x-pack-autoscaling | 9.0.2 |  | java-archive-cataloger |
| x-pack-ccr | 9.0.2 |  | java-archive-cataloger |
| x-pack-constant-keyword | 9.0.2 |  | java-archive-cataloger |
| x-pack-core | 9.0.2 |  | java-archive-cataloger |
| x-pack-counted-keyword | 9.0.2 |  | java-archive-cataloger |
| x-pack-deprecation | 9.0.2 |  | java-archive-cataloger |
| x-pack-downsample | 9.0.2 |  | java-archive-cataloger |
| x-pack-enrich | 9.0.2 |  | java-archive-cataloger |
| x-pack-ent-search | 9.0.2 |  | java-archive-cataloger |
| x-pack-eql | 9.0.2 |  | java-archive-cataloger |
| x-pack-esql | 9.0.2 |  | java-archive-cataloger |
| x-pack-esql-compute | 9.0.2 |  | java-archive-cataloger |
| x-pack-esql-compute-ann | 9.0.2 |  | java-archive-cataloger |
| x-pack-esql-core | 9.0.2 |  | java-archive-cataloger |
| x-pack-fleet | 9.0.2 |  | java-archive-cataloger |
| x-pack-frozen-indices | 9.0.2 |  | java-archive-cataloger |
| x-pack-geoip-enterprise-downloader | 9.0.2 |  | java-archive-cataloger |
| x-pack-graph | 9.0.2 |  | java-archive-cataloger |
| x-pack-identity-provider | 9.0.2 |  | java-archive-cataloger |
| x-pack-ilm | 9.0.2 |  | java-archive-cataloger |
| x-pack-inference | 9.0.2 |  | java-archive-cataloger |
| x-pack-kql | 9.0.2 |  | java-archive-cataloger |
| x-pack-kql | 9.0.2 |  | java-archive-cataloger |
| x-pack-logsdb | 9.0.2 |  | java-archive-cataloger |
| x-pack-logstash | 9.0.2 |  | java-archive-cataloger |
| x-pack-mapper-version | 9.0.2 |  | java-archive-cataloger |
| x-pack-mapper-version | 9.0.2 |  | java-archive-cataloger |
| x-pack-mapper-version | 9.0.2 |  | java-archive-cataloger |
| x-pack-migrate | 9.0.2 |  | java-archive-cataloger |
| x-pack-ml | 9.0.2 |  | java-archive-cataloger |
| x-pack-monitoring | 9.0.2 |  | java-archive-cataloger |
| x-pack-old-lucene-versions | 9.0.2 |  | java-archive-cataloger |
| x-pack-otel-data | 9.0.2 |  | java-archive-cataloger |
| x-pack-profiling | 9.0.2 |  | java-archive-cataloger |
| x-pack-ql | 9.0.2 |  | java-archive-cataloger |
| x-pack-redact | 9.0.2 |  | java-archive-cataloger |
| x-pack-repositories-metering-api | 9.0.2 |  | java-archive-cataloger |
| x-pack-rollup | 9.0.2 |  | java-archive-cataloger |
| x-pack-searchable-snapshots | 9.0.2 |  | java-archive-cataloger |
| x-pack-searchbusinessrules | 9.0.2 |  | java-archive-cataloger |
| x-pack-searchbusinessrules | 9.0.2 |  | java-archive-cataloger |
| x-pack-security | 9.0.2 |  | java-archive-cataloger |
| x-pack-shutdown | 9.0.2 |  | java-archive-cataloger |
| x-pack-slm | 9.0.2 |  | java-archive-cataloger |
| x-pack-snapshot-based-recoveries | 9.0.2 |  | java-archive-cataloger |
| x-pack-snapshot-repo-test-kit | 9.0.2 |  | java-archive-cataloger |
| x-pack-sql | 9.0.2 |  | java-archive-cataloger |
| x-pack-stack | 9.0.2 |  | java-archive-cataloger |
| x-pack-template-resources | 9.0.2 |  | java-archive-cataloger |
| x-pack-text-structure | 9.0.2 |  | java-archive-cataloger |
| x-pack-unsigned-long | 9.0.2 |  | java-archive-cataloger |
| x-pack-voting-only-node | 9.0.2 |  | java-archive-cataloger |
| x-pack-watcher | 9.0.2 |  | java-archive-cataloger |
| x-pack-wildcard | 9.0.2 |  | java-archive-cataloger |
| x-pack-write-load-forecaster | 9.0.2 |  | java-archive-cataloger |
| xmlbeans | 5.3.0 | Apache-2.0, W3C-19980720 | java-archive-cataloger |
| xmlsec | 2.3.4 | Apache-2.0 | java-archive-cataloger |
| xmlsec | 2.3.4 | Apache-2.0 | java-archive-cataloger |
| xsdlib | 2022.7 |  | java-archive-cataloger |
| xz | 1.10 | 0BSD | java-archive-cataloger |
| xz-libs | 5.2.5-8.el9_0 |  | rpm-db-cataloger |
| zip | 3.0-35.el9 |  | rpm-db-cataloger |
| zlib | 1.2.11-40.el9 |  | rpm-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/rabbit

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| .otp-run-deps | 20250701.222004 |  | apk-db-cataloger |
| alpine-baselayout | 3.7.0-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.0-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.5-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.22.0-r0 | MIT | apk-db-cataloger |
| apk-tools | 2.14.9-r2 | GPL-2.0-only | apk-db-cataloger |
| bash | 5.2.37-r0 | GPL-3.0-or-later | apk-db-cataloger |
| busybox | 1.37.0-r18 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r18 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates-bundle | 20241121-r2 | MPL-2.0 AND MIT | apk-db-cataloger |
| erlang | 27.3.4.1 |  | binary-classifier-cataloger |
| gdbm | 1.24-r0 | GPL-3.0-or-later | apk-db-cataloger |
| libapk2 | 2.14.9-r2 | GPL-2.0-only | apk-db-cataloger |
| libbz2 | 1.0.8-r6 | bzip2-1.0.6 | apk-db-cataloger |
| libcrypto3 | 3.5.0-r0 | Apache-2.0 | apk-db-cataloger |
| libexpat | 2.7.1-r0 | MIT | apk-db-cataloger |
| libffi | 3.4.8-r0 | MIT | apk-db-cataloger |
| libgcc | 14.2.0-r6 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libintl | 0.24.1-r0 | LGPL-2.1-or-later | apk-db-cataloger |
| libncursesw | 6.5_p20250503-r0 | X11 | apk-db-cataloger |
| libpanelw | 6.5_p20250503-r0 | X11 | apk-db-cataloger |
| libproc2 | 4.0.4-r3 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libssl3 | 3.5.0-r0 | Apache-2.0 | apk-db-cataloger |
| libstdc++ | 14.2.0-r6 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| mpdecimal | 4.0.1-r0 | BSD-2-Clause | apk-db-cataloger |
| musl | 1.2.5-r10 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r10 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20250503-r0 | X11 | apk-db-cataloger |
| openssl | 3.3.4 |  | binary-classifier-cataloger |
| procps-ng | 4.0.4-r3 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| pyc | 3.12.11-r0 | PSF-2.0 | apk-db-cataloger |
| python3 | 3.12.11-r0 | PSF-2.0 | apk-db-cataloger |
| python3-pyc | 3.12.11-r0 | PSF-2.0 | apk-db-cataloger |
| python3-pycache-pyc0 | 3.12.11-r0 | PSF-2.0 | apk-db-cataloger |
| readline | 8.2.13-r1 | GPL-3.0-or-later | apk-db-cataloger |
| scanelf | 1.3.8-r1 | GPL-2.0-only | apk-db-cataloger |
| skalibs-libs | 2.14.4.0-r0 | ISC | apk-db-cataloger |
| sqlite-libs | 3.49.2-r0 | blessing | apk-db-cataloger |
| ssl_client | 1.37.0-r18 | GPL-2.0-only | apk-db-cataloger |
| su-exec | 0.2-r3 | MIT | apk-db-cataloger |
| tzdata | 2025b-r0 |  | apk-db-cataloger |
| utmps-libs | 0.1.3.1-r0 | ISC | apk-db-cataloger |
| xz-libs | 5.8.1-r0 | 0BSD, GPL-2.0-or-later, LGPL-2.1-or-later | apk-db-cataloger |
| zlib | 1.3.1-r2 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/redis

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| .redis-rundeps | 20250530.001408 |  | apk-db-cataloger |
| alpine-baselayout | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.5-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.21.3-r0 | MIT | apk-db-cataloger |
| apk-tools | 2.14.6-r3 | GPL-2.0-only | apk-db-cataloger |
| busybox | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates-bundle | 20241121-r1 | MPL-2.0 AND MIT | apk-db-cataloger |
| github.com/moby/sys/user | v0.1.0 |  | go-module-binary-cataloger |
| github.com/tianon/gosu | UNKNOWN |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.13.0 |  | go-module-binary-cataloger |
| libcrypto3 | 3.3.3-r0 | Apache-2.0 | apk-db-cataloger |
| libssl3 | 3.3.3-r0 | Apache-2.0 | apk-db-cataloger |
| musl | 1.2.5-r9 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r9 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| redis | 7.4.4 |  | binary-classifier-cataloger |
| scanelf | 1.3.8-r1 | GPL-2.0-only | apk-db-cataloger |
| ssl_client | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| stdlib | go1.18.2 | BSD-3-Clause | go-module-binary-cataloger |
| tzdata | 2025b-r0 |  | apk-db-cataloger |
| zlib | 1.3.1-r2 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/tika

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| SparseBitSet | 1.3 |  | java-archive-cataloger |
| adduser | 3.137ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| apache-mime4j-core | 0.8.11 |  | java-archive-cataloger |
| apache-mime4j-dom | 0.8.11 |  | java-archive-cataloger |
| apt | 2.7.14build2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| base-files | 13ubuntu10 |  | dpkg-db-cataloger |
| base-passwd | 3.6.3build1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.21-2ubuntu4 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| blinker | 1.7.0 |  | python-installed-package-cataloger |
| bsdutils | 1:2.39.3-9ubuntu6 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| byte-buddy | 1.14.9 |  | java-archive-cataloger |
| ca-certificates | 20240203 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| ca-certificates-java | 20240118 |  | dpkg-db-cataloger |
| ca-certificates-java | UNKNOWN |  | java-archive-cataloger |
| cabextract | 1.11-2 |  | dpkg-db-cataloger |
| chardet | 5.2.0 |  | python-installed-package-cataloger |
| commons-cli | 1.6.0 |  | java-archive-cataloger |
| commons-codec | 1.16.1 |  | java-archive-cataloger |
| commons-collections4 | 4.4 |  | java-archive-cataloger |
| commons-compress | 1.26.1 |  | java-archive-cataloger |
| commons-csv | 1.10.0 |  | java-archive-cataloger |
| commons-exec | 1.4.0 |  | java-archive-cataloger |
| commons-io | 2.15.1 |  | java-archive-cataloger |
| commons-lang3 | 3.14.0 |  | java-archive-cataloger |
| commons-math3 | 3.6.1 |  | java-archive-cataloger |
| coreutils | 9.4-3ubuntu6 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cryptography | 41.0.7 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| cryptography | 41.0.7 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| curvesapi | 1.08 |  | java-archive-cataloger |
| cxf-core | 3.5.8 |  | java-archive-cataloger |
| cxf-rt-frontend-jaxrs | 3.5.8 |  | java-archive-cataloger |
| cxf-rt-rs-client | 3.5.8 |  | java-archive-cataloger |
| cxf-rt-rs-security-cors | 3.5.8 |  | java-archive-cataloger |
| cxf-rt-security | 3.5.8 |  | java-archive-cataloger |
| cxf-rt-transports-http | 3.5.8 |  | java-archive-cataloger |
| cxf-rt-transports-http-jetty | 3.5.8 |  | java-archive-cataloger |
| dash | 0.5.12-6ubuntu5 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dbus | 1.14.10-4ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-bin | 1.14.10-4ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-daemon | 1.14.10-4ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-python | 1.3.2 |  | python-installed-package-cataloger |
| dbus-session-bus-common | 1.14.10-4ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dbus-system-bus-common | 1.14.10-4ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| dd-plist | 1.28 |  | java-archive-cataloger |
| debconf | 1.5.86ubuntu1 | BSD-2-Clause | dpkg-db-cataloger |
| debianutils | 5.17build1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| dec | 0.1.2 |  | java-archive-cataloger |
| diffutils | 1:3.10-1build1 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dirmngr | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| distro | 1.9.0 |  | python-installed-package-cataloger |
| distro-info | 1.7+build1 |  | python-installed-package-cataloger |
| distro-info | 1.7build1 | ISC | dpkg-db-cataloger |
| distro-info-data | 0.60ubuntu0.1 | ISC | dpkg-db-cataloger |
| dpkg | 1.22.6ubuntu6 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2.4~exp1ubuntu4 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| error_prone_annotations | 2.26.1 |  | java-archive-cataloger |
| failureaccess | 1.0.2 |  | java-archive-cataloger |
| findutils | 4.9.0-5build1 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| fontbox | 2.0.31 |  | java-archive-cataloger |
| fontconfig | 2.15.0-1.1ubuntu2 | HPND-sell-variant | dpkg-db-cataloger |
| fontconfig-config | 2.15.0-1.1ubuntu2 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-8 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-dejavu-mono | 2.37-8 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonts-freefont-ttf | 20211204+svn4273-2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-liberation | 1:2.1.5-3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| gcc-14-base | 14-20240412-0ubuntu1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| gdal | 3.8.4 | MIT | python-installed-package-cataloger |
| gdal-bin | 3.8.4+dfsg-3ubuntu3 | Apache-2.0, BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| gdal-data | 3.8.4+dfsg-3ubuntu3 | Apache-2.0, BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| gdal-plugins | 3.8.4+dfsg-3ubuntu3 | Apache-2.0, BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| gir1.2-girepository-2.0 | 1.80.1-1 | AFL-2.0, Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, CC0-1.0, FSFAP, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| gir1.2-glib-2.0 | 2.80.0-6ubuntu3.1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| gir1.2-packagekitglib-1.0 | 1.2.8-2build3 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| gnupg | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-utils | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg2 | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgv | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.11-4build1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| grizzly-framework | 3.0.1 |  | java-archive-cataloger |
| grizzly-http | 3.0.1 |  | java-archive-cataloger |
| grizzly-http-server | 3.0.1 |  | java-archive-cataloger |
| guava | 33.1.0-jre |  | java-archive-cataloger |
| gzip | 1.12-1ubuntu3 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hostname | 3.23+nmu2ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| httplib2 | 0.20.4 | MIT | python-installed-package-cataloger |
| init-system-helpers | 1.66ubuntu1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| iso-codes | 4.16.0-1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| istack-commons-runtime | 3.0.12 |  | java-archive-cataloger |
| j2objc-annotations | 3.0.0 |  | java-archive-cataloger |
| jackcess | 4.0.5 |  | java-archive-cataloger |
| jackcess-encrypt | 4.0.2 |  | java-archive-cataloger |
| jackson-annotations | 2.17.0 |  | java-archive-cataloger |
| jackson-core | 2.17.0 |  | java-archive-cataloger |
| jackson-databind | 2.17.0 |  | java-archive-cataloger |
| jackson-jaxrs-base | 2.17.0 |  | java-archive-cataloger |
| jackson-jaxrs-json-provider | 2.17.0 |  | java-archive-cataloger |
| jackson-module-jaxb-annotations | 2.17.0 |  | java-archive-cataloger |
| jai-imageio-core | 1.4.0 |  | java-archive-cataloger |
| jakarta.activation | 1.2.2 |  | java-archive-cataloger |
| jakarta.annotation-api | 1.3.5 |  | java-archive-cataloger |
| jakarta.websocket-api | 2.1.1 |  | java-archive-cataloger |
| jakarta.websocket-client-api | 2.0.0 |  | java-archive-cataloger |
| jakarta.ws.rs-api | 2.1.6 |  | java-archive-cataloger |
| jakarta.xml.bind-api | 2.3.3 |  | java-archive-cataloger |
| java-common | 0.75+exp1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| java-libpst | 0.9.3 |  | java-archive-cataloger |
| javax.servlet-api | 3.1.0 |  | java-archive-cataloger |
| jaxb-runtime | 2.3.6 |  | java-archive-cataloger |
| jbig2-imageio | 3.0.4 |  | java-archive-cataloger |
| jcl-over-slf4j | 2.0.10 |  | java-archive-cataloger |
| jempbox | 1.8.17 |  | java-archive-cataloger |
| jetty-continuation | 9.4.54.v20240208 |  | java-archive-cataloger |
| jetty-http | 9.4.54.v20240208 |  | java-archive-cataloger |
| jetty-io | 9.4.54.v20240208 |  | java-archive-cataloger |
| jetty-security | 9.4.54.v20240208 |  | java-archive-cataloger |
| jetty-server | 9.4.54.v20240208 |  | java-archive-cataloger |
| jetty-util | 9.4.54.v20240208 |  | java-archive-cataloger |
| jhighlight | 1.1.0 |  | java-archive-cataloger |
| jmatio | 1.5 |  | java-archive-cataloger |
| jrt-fs | 17.0.11 |  | java-archive-cataloger |
| json-simple | 1.1.1 |  | java-archive-cataloger |
| jsr305 | 3.0.2 |  | java-archive-cataloger |
| juniversalchardet | 2.4.0 |  | java-archive-cataloger |
| jwarc | 0.29.0 |  | java-archive-cataloger |
| keyboxd | 2.4.4-2ubuntu17 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| language-detector | 0.6 |  | java-archive-cataloger |
| launchpadlib | 1.11.0 |  | python-installed-package-cataloger |
| lazr-restfulclient | 0.14.6 |  | python-installed-package-cataloger |
| lazr-uri | 1.0.6 |  | python-installed-package-cataloger |
| libacl1 | 2.3.2-1build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaec0 | 1.1.2-1build1 | BSD-2-Clause | dpkg-db-cataloger |
| libaom3 | 3.8.2-2build1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, ISC | dpkg-db-cataloger |
| libapparmor1 | 4.0.0-beta3-0ubuntu3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libappstream5 | 1.0.2-1build6 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libapt-pkg6.0t64 | 2.7.14build2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libarchive13t64 | 3.7.2-2 | Apache-2.0, BSD-2-Clause, CC0-1.0 | dpkg-db-cataloger |
| libargon2-1 | 0~20190702+dfsg-4build1 | Apache-2.0 | dpkg-db-cataloger |
| libarmadillo12 | 1:12.6.7+dfsg-1build2 | Apache-2.0, GPL-2.0-only | dpkg-db-cataloger |
| libarpack2t64 | 3.9.1-1.1build2 | BSD-3-Clause | dpkg-db-cataloger |
| libassuan0 | 2.5.6-1build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libattr1 | 1:2.5.2-1build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.1.2-2.1build1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.1.2-2.1build1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libblas3 | 3.12.0-3build1 | BSD-3-Clause | dpkg-db-cataloger |
| libblkid1 | 2.39.3-9ubuntu6 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libblosc1 | 1.21.5+ds-1build1 | BSD-3-Clause, Zlib | dpkg-db-cataloger |
| libbrotli1 | 1.1.0-2build2 | MIT | dpkg-db-cataloger |
| libbsd0 | 0.12.1-1build1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5.1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.39-0ubuntu8.1 | GFDL-1.3-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.39-0ubuntu8.1 | GFDL-1.3-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2 | 1.18.0-3build1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.4-2build2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-5ubuntu2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcap2-bin | 1:2.66-5ubuntu2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcfitsio10t64 | 4.3.1-1.1build2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2.4~exp1ubuntu4 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.36-4build1 |  | dpkg-db-cataloger |
| libcryptsetup12 | 2:2.7.0-1ubuntu4 | Apache-2.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcurl3t64-gnutls | 8.5.0-2ubuntu10.1 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4t64 | 8.5.0-2ubuntu10.1 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libdatrie1 | 0.2.13-3build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libdb5.3t64 | 5.3.28+dfsg2-7 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdbus-1-3 | 1.14.10-4ubuntu4 | AFL-2.1, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libde265-0 | 1.0.15-1build3 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libdebconfclient0 | 0.271ubuntu3 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdeflate0 | 1.19-1build1 |  | dpkg-db-cataloger |
| libdevmapper1.02.1 | 2:1.02.185-3ubuntu3 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libduktape207 | 2.7.0+tests-0ubuntu3 | CC0-1.0 | dpkg-db-cataloger |
| libdw1t64 | 0.190-1.1build4 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libelf1t64 | 0.190-1.1build4 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libexpat1 | 2.6.1-2build1 | MIT | dpkg-db-cataloger |
| libext2fs2t64 | 1.47.0-2.4~exp1ubuntu4 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libfdisk1 | 2.39.3-9ubuntu6 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libffi8 | 3.4.6-1build1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libfontconfig1 | 2.15.0-1.1ubuntu2 | HPND-sell-variant | dpkg-db-cataloger |
| libfontenc1 | 1:1.1.8-1build1 | MIT | dpkg-db-cataloger |
| libfreetype6 | 2.13.2+dfsg-1build3 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT-Modern-Variant, Zlib | dpkg-db-cataloger |
| libfreexl1 | 2.0.0-1build2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libfribidi0 | 1.0.13-3build1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libfyba0t64 | 4.1.1-11build1 | GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| libgcc-s1 | 14-20240412-0ubuntu1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.3-2build1 | GPL-2.0-only | dpkg-db-cataloger |
| libgdal34t64 | 3.8.4+dfsg-3ubuntu3 | Apache-2.0, BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| libgeos-c1t64 | 3.12.1-3build1 | Apache-2.0, BSL-1.0, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libgeos3.12.1t64 | 3.12.1-3build1 | Apache-2.0, BSL-1.0, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libgeotiff5 | 1.7.1-5build1 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| libgfortran5 | 14-20240412-0ubuntu1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgif7 | 5.2.2-1ubuntu1 | ISC, MIT | dpkg-db-cataloger |
| libgirepository-1.0-1 | 1.80.1-1 | AFL-2.0, Apache-2.0, BSD-2-Clause, CC-BY-SA-3.0, CC0-1.0, FSFAP, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-0t64 | 2.80.0-6ubuntu3.1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-bin | 2.80.0-6ubuntu3.1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-data | 2.80.0-6ubuntu3.1 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgmp10 | 2:6.3.0+dfsg-2ubuntu6 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30t64 | 3.8.3-1.1ubuntu3.1 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 14-20240412-0ubuntu1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.47-3build2 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgraphite2-3 | 1.3.14-2build1 | GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.20.1-6ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| libgstreamer1.0-0 | 1.24.2-1 | GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libharfbuzz0b | 8.3.0-2build2 | Apache-2.0, CC0-1.0, FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, MIT, OFL-1.1 | dpkg-db-cataloger |
| libhdf4-0-alt | 4.2.16-4build1 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, NetCDF | dpkg-db-cataloger |
| libhdf5-103-1t64 | 1.10.10+repack-3.1ubuntu4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libhdf5-hl-100t64 | 1.10.10+repack-3.1ubuntu4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libheif-plugin-aomdec | 1.17.6-1ubuntu4 | BSD-3-Clause, BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libheif-plugin-libde265 | 1.17.6-1ubuntu4 | BSD-3-Clause, BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libheif1 | 1.17.6-1ubuntu4 | BSD-3-Clause, BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libhogweed6t64 | 3.9.1-2.2build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libicu74 | 74.2-1ubuntu3 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn2-0 | 2.3.7-2build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libjbig0 | 2.1-6.1ubuntu2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libjpeg-turbo8 | 2.1.5-2ubuntu2 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libjpeg8 | 8c-2ubuntu11 | LGPL-2.1-only | dpkg-db-cataloger |
| libjson-c5 | 0.17-1build1 |  | dpkg-db-cataloger |
| libk5crypto3 | 1.20.1-6ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-3build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkmlbase1t64 | 1.3.0-12build1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, Zlib | dpkg-db-cataloger |
| libkmldom1t64 | 1.3.0-12build1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, Zlib | dpkg-db-cataloger |
| libkmlengine1t64 | 1.3.0-12build1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, Zlib | dpkg-db-cataloger |
| libkmod2 | 31+20240202-2ubuntu7 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.20.1-6ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.20.1-6ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| libksba8 | 1.6.6-1build1 | FSFUL, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblapack3 | 3.12.0-3build1 | BSD-3-Clause | dpkg-db-cataloger |
| liblcms2-2 | 2.14-2build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| libldap2 | 2.6.7+dfsg-1~exp1ubuntu8 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| liblept5 | 1.82.0-3build4 | BSD-2-Clause | dpkg-db-cataloger |
| liblerc4 | 4.0.0+ds-4ubuntu2 | Apache-2.0 | dpkg-db-cataloger |
| libltdl7 | 2.4.7-7build1 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1build1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.6.1+really5.4.5-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmd0 | 1.1.0-2build1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libminizip1t64 | 1:1.3.dfsg-3.1ubuntu2 | Zlib | dpkg-db-cataloger |
| libmount1 | 2.39.3-9ubuntu6 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmspack0t64 | 0.11-1.1build1 | LGPL-2.1-only | dpkg-db-cataloger |
| libmysqlclient21 | 8.0.36-2ubuntu3 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only | dpkg-db-cataloger |
| libncursesw6 | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnetcdf19t64 | 1:4.9.2-5ubuntu4 | BSD-3-Clause, BSL-1.0, CC-BY-4.0, GPL-3.0-only, GPL-3.0-or-later, HDF5, NetCDF, Zlib | dpkg-db-cataloger |
| libnettle8t64 | 3.9.1-2.2build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.59.0-1ubuntu0.1 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnpth0t64 | 1.6-3.1build1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnspr4 | 2:4.35-1.1build1 | MPL-2.0 | dpkg-db-cataloger |
| libnss3 | 2:3.98-1build1 | MPL-2.0, Zlib | dpkg-db-cataloger |
| libodbc2 | 2.3.12-1build2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libodbcinst2 | 2.3.12-1build2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libogdi4.1 | 4.1.1+ds-3build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.0-2build3 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libp11-kit0 | 0.25.3-4ubuntu2 | Apache-2.0, BSD-3-Clause, FSFAP, FSFULLR, GPL-2.0-or-later, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, X11 | dpkg-db-cataloger |
| libpackagekit-glib2-18 | 1.2.8-2build3 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.3-5ubuntu5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.3-5ubuntu5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.3-5ubuntu5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-systemd | 255.4-1ubuntu8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.3-5ubuntu5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpango-1.0-0 | 1.52.1+ds-1build1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangocairo-1.0-0 | 1.52.1+ds-1build1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangoft2-1.0-0 | 1.52.1+ds-1build1 | Apache-2.0, Apache-2.0, Bitstream-Vera, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-4ubuntu2 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcsclite1 | 2.0.3-1build1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| libpixman-1-0 | 0.42.2-1build1 |  | dpkg-db-cataloger |
| libpng16-16t64 | 1.6.43-5build1 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpolkit-agent-1-0 | 124-2ubuntu1 | Apache-2.0, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpolkit-gobject-1-0 | 124-2ubuntu1 | Apache-2.0, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpoppler134 | 24.02.0-1ubuntu9 | Apache-2.0, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libpq5 | 16.2-1ubuntu4 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.4-4ubuntu3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libproj25 | 9.4.0-1build2 | Apache-2.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libpsl5t64 | 0.21.2-1.1build1 | MIT | dpkg-db-cataloger |
| libpython3-stdlib | 3.12.3-0ubuntu1 |  | dpkg-db-cataloger |
| libpython3.12-minimal | 3.12.3-1 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.12-stdlib | 3.12.3-1 | GPL-2.0-only | dpkg-db-cataloger |
| libqhull-r8.0 | 2020.2-6build1 | GPL-3.0-only, GPL-3.0-or-later, Qhull | dpkg-db-cataloger |
| libreadline8t64 | 8.2-4build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| librtmp1 | 2.4+20151223.gitfa8646d.1-2build7 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| librttopo1 | 1.1.0-3build2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsasl2-2 | 2.1.28+dfsg1-5ubuntu3 | BSD-2-Clause, BSD-3-Clause-Attribution, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.28+dfsg1-5ubuntu3 | BSD-2-Clause, BSD-3-Clause-Attribution, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, RSA-MD | dpkg-db-cataloger |
| libseccomp2 | 2.5.5-1ubuntu3 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.5-2ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| libsemanage-common | 3.5-1build5 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsemanage2 | 3.5-1build5 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsepol2 | 3.5-2build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsharpyuv0 | 1.3.2-0.4build3 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libsmartcols1 | 2.39.3-9ubuntu6 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsnappy1v5 | 1.1.10-1build1 | BSD-3-Clause, CC-BY-3.0, CC-BY-4.0, MIT | dpkg-db-cataloger |
| libspatialite8t64 | 5.1.0-3build1 | BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libsqlite3-0 | 3.45.1-1ubuntu2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2.4~exp1ubuntu4 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssh-4 | 0.10.6-2build2 | BSD-2-Clause, BSD-3-Clause, LGPL-2.1-only | dpkg-db-cataloger |
| libssl3t64 | 3.0.13-0ubuntu3 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 14-20240412-0ubuntu1 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libstemmer0d | 2.2.0-4build1 |  | dpkg-db-cataloger |
| libsuperlu6 | 6.0.1+dfsg1-1build1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsystemd-shared | 255.4-1ubuntu8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsystemd0 | 255.4-1ubuntu8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsz2 | 1.1.2-1build1 | BSD-2-Clause | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-3build1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtesseract5 | 5.3.4-1build5 | Apache-2.0 | dpkg-db-cataloger |
| libthai-data | 0.1.29-2build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libthai0 | 0.1.29-2build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtiff6 | 4.5.1+git230720-4ubuntu2 |  | dpkg-db-cataloger |
| libtinfo6 | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.4+ds-1.1build1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3t64 | 1.3.4+ds-1.1build1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libudev1 | 255.4-1ubuntu8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring5 | 1.1-2build1 | GFDL-1.2-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| libunwind8 | 1.6.2-3build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liburiparser1 | 0.9.7+dfsg-2build1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libuuid1 | 2.39.3-9ubuntu6 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libwebp7 | 1.3.2-0.4build3 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libwebpmux3 | 1.3.2-0.4build3 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| libx11-6 | 2:1.8.7-1build1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.8.7-1build1 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxau6 | 1:1.0.9-1build6 |  | dpkg-db-cataloger |
| libxcb-render0 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxcb-shm0 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxcb1 | 1.15-1ubuntu2 |  | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.3-0ubuntu6 |  | dpkg-db-cataloger |
| libxerces-c3.2t64 | 3.2.4+debian-1.2ubuntu2 | Apache-2.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libxext6 | 2:1.3.4-1build2 |  | dpkg-db-cataloger |
| libxml2 | 2.9.14+dfsg-1.3ubuntu3 | ISC | dpkg-db-cataloger |
| libxmlb2 | 0.3.18-1 | CC0-1.0, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libxrender1 | 1:0.9.10-1.1build1 | HPND-sell-variant | dpkg-db-cataloger |
| libxxhash0 | 0.8.2-2build1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libyaml-0-2 | 0.2.5-1build1 |  | dpkg-db-cataloger |
| libzstd1 | 1.5.5+dfsg2-2build1 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| listenablefuture | 9999.0-empty-to-avoid-conflict-with-guava |  | java-archive-cataloger |
| log4j-api | 2.23.1 | Apache-2.0 | java-archive-cataloger |
| log4j-core | 2.23.1 | Apache-2.0 | java-archive-cataloger |
| log4j-slf4j2-impl | 2.23.1 | Apache-2.0 | java-archive-cataloger |
| login | 1:4.13+dfsg1-4ubuntu3 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2.4~exp1ubuntu4 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| lsb-release | 12.0-2 | ISC | dpkg-db-cataloger |
| mawk | 1.3.4.20240123-1build1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 10.1.0 |  | dpkg-db-cataloger |
| metadata-extractor | 2.19.0 |  | java-archive-cataloger |
| microsoft-translator-java-api | 0.6.2 |  | java-archive-cataloger |
| mount | 2.39.3-9ubuntu6 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| mysql-common | 5.8+1.1.0build1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| ncurses-base | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| numpy | 1.26.4 | BSD-3-Clause | python-installed-package-cataloger |
| oauthlib | 3.2.2 |  | python-installed-package-cataloger |
| openjdk-17-jre-headless | 17.0.11+9-1 | GPL-2.0-only, MIT | dpkg-db-cataloger |
| openssl | 3.0.13-0ubuntu3 |  | dpkg-db-cataloger |
| packagekit | 1.2.8-2build3 | FSFAP, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| passwd | 1:4.13+dfsg1-4ubuntu3 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.7.6-7build3 |  | dpkg-db-cataloger |
| pdfbox | 2.0.31 |  | java-archive-cataloger |
| pdfbox-tools | 2.0.31 |  | java-archive-cataloger |
| perl-base | 5.38.2-3.2build2 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pinentry-curses | 1.2.1-3ubuntu5 | GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| polkitd | 124-2ubuntu1 | Apache-2.0, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| procps | 2:4.0.4-4ubuntu3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| proj-data | 9.4.0-1build2 | Apache-2.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| pygobject | 3.48.2 |  | python-installed-package-cataloger |
| pyjwt | 2.7.0 | MIT | python-installed-package-cataloger |
| pyparsing | 3.1.1 |  | python-installed-package-cataloger |
| python-apt | 2.7.7+ubuntu1 |  | python-installed-package-cataloger |
| python-apt-common | 2.7.7ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python-debian | 0.1.49+ubuntu2 | GPL-2.0-or-later | python-installed-package-cataloger |
| python3 | 3.12.3-0ubuntu1 |  | dpkg-db-cataloger |
| python3-apt | 2.7.7ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-blinker | 1.7.0-1 | BSD-3-Clause | dpkg-db-cataloger |
| python3-cffi-backend | 1.16.0-2build1 |  | dpkg-db-cataloger |
| python3-chardet | 5.2.0+dfsg-1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| python3-cryptography | 41.0.7-4build3 | Apache-2.0 | dpkg-db-cataloger |
| python3-dbus | 1.3.2-5build3 | AFL-2.1, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-debconf | 1.5.86ubuntu1 | BSD-2-Clause | dpkg-db-cataloger |
| python3-debian | 0.1.49ubuntu2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| python3-distro | 1.9.0-1 | Apache-2.0 | dpkg-db-cataloger |
| python3-distro-info | 1.7build1 | ISC | dpkg-db-cataloger |
| python3-distupgrade | 1:24.04.18 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-gdal | 3.8.4+dfsg-3ubuntu3 | Apache-2.0, BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, Info-ZIP, LGPL-2.0-only, LGPL-2.0-or-later, PostgreSQL, Qhull, Libpng, Zlib | dpkg-db-cataloger |
| python3-gi | 3.48.2-1 | LGPL-2.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| python3-httplib2 | 0.20.4-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| python3-jwt | 2.7.0-1 |  | dpkg-db-cataloger |
| python3-launchpadlib | 1.11.0-6 | LGPL-3.0-only, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| python3-lazr.restfulclient | 0.14.6-1 | LGPL-3.0-only, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| python3-lazr.uri | 1.0.6-3 | LGPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| python3-minimal | 3.12.3-0ubuntu1 |  | dpkg-db-cataloger |
| python3-numpy | 1:1.26.4+ds-6ubuntu1 | Apache-2.0, Apache-2.0, BSD-3-Clause, Zlib, Zlib | dpkg-db-cataloger |
| python3-oauthlib | 3.2.2-1 | BSD-3-Clause | dpkg-db-cataloger |
| python3-pkg-resources | 68.1.2-2ubuntu1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| python3-pyparsing | 3.1.1-1 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| python3-six | 1.16.0-4 |  | dpkg-db-cataloger |
| python3-software-properties | 0.99.48 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| python3-update-manager | 1:24.04.6 |  | dpkg-db-cataloger |
| python3-wadllib | 1.3.6-5 | LGPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| python3-yaml | 6.0.1-2build2 |  | dpkg-db-cataloger |
| python3.12 | 3.12.3-1 | GPL-2.0-only | dpkg-db-cataloger |
| python3.12-minimal | 3.12.3-1 | GPL-2.0-only | dpkg-db-cataloger |
| pyyaml | 6.0.1 | MIT | python-installed-package-cataloger |
| readline-common | 8.2-4build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| rome | 2.1.0 |  | java-archive-cataloger |
| rome-utils | 2.1.0 |  | java-archive-cataloger |
| rome-utils | 2.1.0 |  | java-archive-cataloger |
| sed | 4.9-2build1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sensible-utils | 0.0.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| sgml-base | 1.31 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| six | 1.16.0 | MIT | python-installed-package-cataloger |
| slf4j-api | 2.0.10 |  | java-archive-cataloger |
| software-properties-common | 0.99.48 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| stax2-api | 4.2.2 |  | java-archive-cataloger |
| systemd | 255.4-1ubuntu8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| systemd-dev | 255.4-1ubuntu8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| systemd-sysv | 255.4-1ubuntu8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| sysvinit-utils | 3.08-6ubuntu3 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| tar | 1.35+dfsg-3build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tesseract-ocr | 5.3.4-1build5 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-afr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-all | 5.3.4-1build5 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-amh | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ara | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-asm | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-aze | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-aze-cyrl | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bel | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ben | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bod | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bos | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bre | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-bul | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-cat | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ceb | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ces | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chi-sim | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chi-sim-vert | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chi-tra | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chi-tra-vert | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-chr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-cos | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-cym | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-dan | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-deu | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-div | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-dzo | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ell | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-eng | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-enm | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-epo | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-est | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-eus | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fao | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fas | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fil | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fin | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fra | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-frk | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-frm | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-fry | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-gla | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-gle | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-glg | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-grc | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-guj | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hat | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-heb | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hin | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hrv | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hun | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-hye | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-iku | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ind | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-isl | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ita | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ita-old | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-jav | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-jpn | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-jpn-vert | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kan | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kat | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kat-old | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kaz | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-khm | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kir | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kmr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kor | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-kor-vert | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-lao | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-lat | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-lav | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-lit | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ltz | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mal | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mar | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mkd | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mlt | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mon | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mri | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-msa | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-mya | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-nep | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-nld | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-nor | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-oci | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ori | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-osd | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-pan | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-pol | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-por | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-pus | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-que | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ron | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-rus | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-san | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-arab | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-armn | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-beng | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-cans | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-cher | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-cyrl | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-deva | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-ethi | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-frak | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-geor | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-grek | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-gujr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-guru | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hang | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hang-vert | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hans | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hans-vert | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hant | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hant-vert | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-hebr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-jpan | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-jpan-vert | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-khmr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-knda | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-laoo | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-latn | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-mlym | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-mymr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-orya | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-sinh | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-syrc | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-taml | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-telu | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-thaa | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-thai | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-tibt | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-script-viet | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-sin | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-slk | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-slv | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-snd | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-spa | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-spa-old | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-sqi | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-srp | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-srp-latn | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-sun | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-swa | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-swe | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-syr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tam | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tat | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tel | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tgk | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tha | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tir | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ton | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-tur | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-uig | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-ukr | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-urd | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-uzb | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-uzb-cyrl | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-vie | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-yid | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tesseract-ocr-yor | 1:4.1.0-2 | Apache-2.0 | dpkg-db-cataloger |
| tika-core | 2.9.2 |  | java-archive-cataloger |
| tika-emitter-fs | 2.9.2 |  | java-archive-cataloger |
| tika-langdetect-optimaize | 2.9.2 |  | java-archive-cataloger |
| tika-parser-apple-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-audiovideo-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-cad-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-code-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-crypto-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-digest-commons | 2.9.2 |  | java-archive-cataloger |
| tika-parser-font-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-html-commons | 2.9.2 |  | java-archive-cataloger |
| tika-parser-html-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-image-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-mail-commons | 2.9.2 |  | java-archive-cataloger |
| tika-parser-mail-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-microsoft-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-miscoffice-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-news-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-ocr-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-pdf-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-pkg-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-text-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-webarchive-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-xml-module | 2.9.2 |  | java-archive-cataloger |
| tika-parser-xmp-commons | 2.9.2 |  | java-archive-cataloger |
| tika-parser-zip-commons | 2.9.2 |  | java-archive-cataloger |
| tika-serialization | 2.9.2 |  | java-archive-cataloger |
| tika-server-core | 2.9.2 |  | java-archive-cataloger |
| tika-server-standard | 2.9.2 | Apache-2.0, EPL-2.0, GPL-2.0-only | java-archive-cataloger |
| tika-translate | 2.9.2 |  | java-archive-cataloger |
| tika-xmp | 2.9.2 |  | java-archive-cataloger |
| ttf-mscorefonts-installer | 3.8.1ubuntu1 |  | dpkg-db-cataloger |
| txw2 | 2.3.6 |  | java-archive-cataloger |
| tyrus-client | 2.0.2 |  | java-archive-cataloger |
| tyrus-container-grizzly-client | 2.0.2 |  | java-archive-cataloger |
| tyrus-core | 2.0.2 |  | java-archive-cataloger |
| tyrus-spi | 2.0.2 |  | java-archive-cataloger |
| tyrus-standalone-client | 2.0.2 |  | java-archive-cataloger |
| tzdata | 2024a-2ubuntu1 | ICU | dpkg-db-cataloger |
| ubuntu-keyring | 2023.11.28.1 |  | dpkg-db-cataloger |
| ubuntu-pro-client | 31.2.3 | GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| ubuntu-pro-client | 8001 |  | python-installed-package-cataloger |
| ubuntu-release-upgrader-core | 1:24.04.18 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| unixodbc-common | 2.3.12-1build2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| update-manager-core | 1:24.04.6 |  | dpkg-db-cataloger |
| update-notifier-common | 3.192.68build3 | LGPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.39.3-9ubuntu6 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| vorbis-java-core | 0.8 |  | java-archive-cataloger |
| vorbis-java-tika | 0.8 |  | java-archive-cataloger |
| wadllib | 1.3.6 |  | python-installed-package-cataloger |
| wget | 1.21.4-1ubuntu4 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| woodstox-core | 6.6.1 |  | java-archive-cataloger |
| x11-common | 1:7.7+23ubuntu3 |  | dpkg-db-cataloger |
| xfonts-encodings | 1:1.0.5-0ubuntu2 |  | dpkg-db-cataloger |
| xfonts-utils | 1:7.7+6build3 |  | dpkg-db-cataloger |
| xml-core | 0.19 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| xmlschema-core | 2.3.1 |  | java-archive-cataloger |
| xmpbox | 2.0.31 |  | java-archive-cataloger |
| xsdlib | 2022.7 |  | java-archive-cataloger |
| zlib1g | 1:1.3.dfsg-3.1ubuntu2 | Zlib | dpkg-db-cataloger |
| zstd | 1.5.5+dfsg2-2build1 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/rspamd

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.6.5-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.6.5-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.4-r1 | MIT | apk-db-cataloger |
| apk-tools | 2.14.4-r1 | GPL-2.0-only | apk-db-cataloger |
| busybox | 1.36.1-r30 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.36.1-r30 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates-bundle | 20250911-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| fasttext-libs | 0.9.2-r1 | MIT | apk-db-cataloger |
| glib | 2.80.5-r0 | LGPL-2.1-or-later | apk-db-cataloger |
| icu-data-full | 74.2-r1 | ICU | apk-db-cataloger |
| icu-libs | 74.2-r1 | ICU | apk-db-cataloger |
| libblkid | 2.40.1-r1 | LGPL-2.1-or-later | apk-db-cataloger |
| libbz2 | 1.0.8-r6 | bzip2-1.0.6 | apk-db-cataloger |
| libcrypto3 | 3.3.5-r0 | Apache-2.0 | apk-db-cataloger |
| libdw | 0.191-r0 | GPL-3.0-or-later AND ( GPL-2.0-or-later OR LGPL-3.0-or-later ) | apk-db-cataloger |
| libeconf | 0.6.3-r0 | MIT | apk-db-cataloger |
| libelf | 0.191-r0 | GPL-3.0-or-later AND ( GPL-2.0-or-later OR LGPL-3.0-or-later ) | apk-db-cataloger |
| libffi | 3.4.6-r0 | MIT | apk-db-cataloger |
| libgcc | 13.2.1_git20240309-r1 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libintl | 0.22.5-r0 | LGPL-2.1-or-later | apk-db-cataloger |
| libmount | 2.40.1-r1 | LGPL-2.1-or-later | apk-db-cataloger |
| libsodium | 1.0.19-r0 | ISC | apk-db-cataloger |
| libssl3 | 3.3.5-r0 | Apache-2.0 | apk-db-cataloger |
| libstdc++ | 13.2.1_git20240309-r1 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libstemmer | 2.2.0-r0 | BSD-3-Clause | apk-db-cataloger |
| luajit | 2.1_p20240314-r0 | MIT | apk-db-cataloger |
| musl | 1.2.5-r1 | MIT | apk-db-cataloger |
| musl-fts | 1.2.7-r6 | BSD-3-Clause | apk-db-cataloger |
| musl-utils | 1.2.5-r1 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| pcre2 | 10.43-r0 | BSD-3-Clause | apk-db-cataloger |
| rspamd | 3.8.4-r0 | Apache-2.0, BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, CC0-1.0, LGPL-2.1-or-later, LGPL-3.0-only, MIT, Zlib | apk-db-cataloger |
| rspamd-libs | 3.8.4-r0 | Apache-2.0, BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, CC0-1.0, LGPL-2.1-or-later, LGPL-3.0-only, MIT, Zlib | apk-db-cataloger |
| scanelf | 1.3.7-r2 | GPL-2.0-only | apk-db-cataloger |
| sqlite-libs | 3.45.3-r2 | blessing | apk-db-cataloger |
| ssl_client | 1.36.1-r30 | GPL-2.0-only | apk-db-cataloger |
| vectorscan | 5.4.11-r1 | BSD-3-Clause | apk-db-cataloger |
| xz-libs | 5.6.2-r1 | 0BSD, GPL-2.0-or-later, LGPL-2.1-or-later | apk-db-cataloger |
| zlib | 1.3.1-r1 | Zlib | apk-db-cataloger |
| zstd-libs | 1.5.6-r0 | BSD-3-Clause OR GPL-2.0-or-later | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/fluentd

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| abbrev | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| alpine-baselayout | 3.4.3-r2 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.4.3-r2 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.4-r1 | MIT | apk-db-cataloger |
| apk-tools | 2.14.0-r5 | GPL-2.0-only | apk-db-cataloger |
| async | 1.31.0 | MIT | ruby-installed-gemspec-cataloger |
| async-http | 0.60.2 | MIT | ruby-installed-gemspec-cataloger |
| async-io | 1.43.2 | MIT | ruby-installed-gemspec-cataloger |
| async-pool | 0.6.1 | MIT | ruby-installed-gemspec-cataloger |
| base64 | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| base64 | 0.2.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| benchmark | 0.2.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| bigdecimal | 1.4.4 | Ruby | ruby-installed-gemspec-cataloger |
| bigdecimal | 3.1.3 | Ruby, BSD-2-Clause | ruby-installed-gemspec-cataloger |
| bundler | 2.5.11 | MIT | ruby-installed-gemspec-cataloger |
| busybox | 1.36.1-r15 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.36.1-r15 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates | 20240226-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20230506-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| cgi | 0.3.7 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| concurrent-ruby | 1.3.1 | MIT | ruby-installed-gemspec-cataloger |
| concurrent_ruby | UNKNOWN |  | java-archive-cataloger |
| console | 1.25.2 | MIT | ruby-installed-gemspec-cataloger |
| cool.io | 1.8.1 | MIT | ruby-installed-gemspec-cataloger |
| csv | 3.2.6 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| date | 3.3.3 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| delegate | 0.3.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| did_you_mean | 1.6.3 | MIT | ruby-installed-gemspec-cataloger |
| digest | 3.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| drb | 2.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| drb | 2.2.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| elastic-transport | 8.4.1 | Apache-2.0 | ruby-installed-gemspec-cataloger |
| elasticsearch | 8.18.0 | Apache-2.0 | ruby-installed-gemspec-cataloger |
| elasticsearch-api | 8.18.0 | Apache-2.0 | ruby-installed-gemspec-cataloger |
| english | 0.7.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| erb | 4.0.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| error_highlight | 0.5.1 | MIT | ruby-installed-gemspec-cataloger |
| etc | 1.4.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| excon | 1.3.2 | MIT | ruby-installed-gemspec-cataloger |
| faraday | 2.14.0 | MIT | ruby-installed-gemspec-cataloger |
| faraday-excon | 2.4.0 | MIT | ruby-installed-gemspec-cataloger |
| faraday-net_http | 3.4.2 | MIT | ruby-installed-gemspec-cataloger |
| fcntl | 1.0.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| fiber-annotation | 0.2.0 | MIT | ruby-installed-gemspec-cataloger |
| fiber-local | 1.1.0 | MIT | ruby-installed-gemspec-cataloger |
| fiber-storage | 0.1.1 | MIT | ruby-installed-gemspec-cataloger |
| fiddle | 1.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| fileutils | 1.7.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| find | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| fluent-plugin-elasticsearch | 6.0.0 | Apache-2.0 | ruby-installed-gemspec-cataloger |
| fluentd | 1.17.0 | Apache-2.0 | ruby-installed-gemspec-cataloger |
| forwardable | 1.3.3 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| getoptlong | 0.2.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| gmp | 6.3.0-r0 | LGPL-3.0-or-later OR GPL-2.0-or-later | apk-db-cataloger |
| http_parser.rb | 0.8.0 | MIT | ruby-installed-gemspec-cataloger |
| io-console | 0.6.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| io-nonblock | 0.2.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| io-wait | 0.3.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| ipaddr | 1.2.5 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| irb | 1.6.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| json | 2.6.3 | Ruby | ruby-installed-gemspec-cataloger |
| json | 2.6.3 | Ruby | ruby-installed-gemspec-cataloger |
| libc-utils | 0.7.2-r5 | BSD-2-Clause AND BSD-3-Clause | apk-db-cataloger |
| libcrypto3 | 3.1.4-r5 | Apache-2.0 | apk-db-cataloger |
| libffi | 3.4.4-r3 | MIT | apk-db-cataloger |
| libgcc | 13.2.1_git20231014-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libncursesw | 6.4_p20231125-r0 | X11 | apk-db-cataloger |
| libssl3 | 3.1.4-r5 | Apache-2.0 | apk-db-cataloger |
| libucontext | 1.2-r2 | ISC | apk-db-cataloger |
| logger | 1.5.3 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| msgpack | 1.7.2 |  | ruby-installed-gemspec-cataloger |
| multi_json | 1.19.1 | MIT | ruby-installed-gemspec-cataloger |
| musl | 1.2.4_git20230717-r5 | MIT | apk-db-cataloger |
| musl-utils | 1.2.4_git20230717-r4 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| mutex_m | 0.1.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| ncurses-terminfo-base | 6.4_p20231125-r0 | X11 | apk-db-cataloger |
| net-http | 0.4.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| net-http | 0.9.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| net-protocol | 0.2.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| nio4r | 2.7.3 | BSD-2-Clause, MIT | ruby-installed-gemspec-cataloger |
| nkf | 0.1.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| observer | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| oj | 3.16.1 | MIT | ruby-installed-gemspec-cataloger |
| open-uri | 0.3.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| open3 | 0.1.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| openssl | 3.1.0 | Ruby | ruby-installed-gemspec-cataloger |
| optparse | 0.3.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| ostruct | 0.5.5 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| pathname | 0.2.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| pp | 0.4.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| prettyprint | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| primitives | UNKNOWN |  | java-archive-cataloger |
| protocol-hpack | 1.4.3 | MIT | ruby-installed-gemspec-cataloger |
| protocol-http | 0.24.7 | MIT | ruby-installed-gemspec-cataloger |
| protocol-http1 | 0.15.1 | MIT | ruby-installed-gemspec-cataloger |
| protocol-http2 | 0.15.1 | MIT | ruby-installed-gemspec-cataloger |
| pstore | 0.1.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| psych | 5.0.1 | MIT | ruby-installed-gemspec-cataloger |
| racc | 1.6.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| readline | 0.0.3 | Ruby | ruby-installed-gemspec-cataloger |
| readline | 8.2.1-r2 | GPL-2.0-or-later | apk-db-cataloger |
| readline-ext | 0.1.5 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| reline | 0.3.2 | Ruby | ruby-installed-gemspec-cataloger |
| resolv | 0.2.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| resolv-replace | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| rexml | 3.2.6 | BSD-2-Clause | ruby-installed-gemspec-cataloger |
| rinda | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| ruby | 3.2.8-r0 | Ruby AND BSD-2-Clause AND MIT | apk-db-cataloger |
| ruby-libs | 3.2.8-r0 | Ruby AND BSD-2-Clause AND MIT | apk-db-cataloger |
| ruby-webrick | 1.8.1-r0 | BSD-2-Clause | apk-db-cataloger |
| ruby2_keywords | 0.0.5 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| scanelf | 1.3.7-r2 | GPL-2.0-only | apk-db-cataloger |
| securerandom | 0.2.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| serverengine | 2.3.2 |  | ruby-installed-gemspec-cataloger |
| set | 1.0.3 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| shellwords | 0.1.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| sigdump | 0.2.5 | MIT | ruby-installed-gemspec-cataloger |
| singleton | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| ssl_client | 1.36.1-r15 | GPL-2.0-only | apk-db-cataloger |
| stringio | 3.0.4 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| strptime | 0.2.5 | BSD-2-Clause | ruby-installed-gemspec-cataloger |
| strscan | 3.0.7 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| syntax_suggest | 1.1.0 | MIT | ruby-installed-gemspec-cataloger |
| syslog | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| tempfile | 0.1.3 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| time | 0.2.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| timeout | 0.3.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| timers | 4.3.5 | MIT | ruby-installed-gemspec-cataloger |
| tini | 0.19.0-r2 | MIT | apk-db-cataloger |
| tmpdir | 0.1.3 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| traces | 0.11.1 | MIT | ruby-installed-gemspec-cataloger |
| tsort | 0.1.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| tzinfo | 2.0.6 | MIT | ruby-installed-gemspec-cataloger |
| tzinfo-data | 1.2024.1 | MIT | ruby-installed-gemspec-cataloger |
| un | 0.2.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| uri | 0.12.4 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| weakref | 0.1.2 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| webrick | 1.8.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| yajl-ruby | 1.4.3 | MIT | ruby-installed-gemspec-cataloger |
| yaml | 0.2.1 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |
| yaml | 0.2.5-r2 | MIT | apk-db-cataloger |
| zlib | 1.3.1-r0 | Zlib | apk-db-cataloger |
| zlib | 3.0.0 | BSD-2-Clause, Ruby | ruby-installed-gemspec-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/prometheus

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| busybox | 1.36.1 |  | binary-classifier-cataloger |
| cloud.google.com/go/auth | v0.9.3 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth | v0.9.3 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.4 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.4 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.5.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.5.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.14.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.14.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.7.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.7.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/compute/armcompute/v5 | v5.7.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/compute/armcompute/v5 | v5.7.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/network/armnetwork/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/network/armnetwork/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.2.2 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.2.2 |  | go-module-binary-cataloger |
| github.com/Code-Hex/go-generics-cache | v1.5.1 |  | go-module-binary-cataloger |
| github.com/Code-Hex/go-generics-cache | v1.5.1 |  | go-module-binary-cataloger |
| github.com/KimMachineGun/automemlimit | v0.6.1 |  | go-module-binary-cataloger |
| github.com/alecthomas/kingpin/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/alecthomas/kingpin/v2 | v2.4.0 |  | go-module-binary-cataloger |
| github.com/alecthomas/units | v0.0.0-20240626203959-61d1e3462e30 |  | go-module-binary-cataloger |
| github.com/alecthomas/units | v0.0.0-20240626203959-61d1e3462e30 |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/asaskevich/govalidator | v0.0.0-20230301143203-a9d515a09cc2 |  | go-module-binary-cataloger |
| github.com/asaskevich/govalidator | v0.0.0-20230301143203-a9d515a09cc2 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go | v1.55.5 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go | v1.55.5 |  | go-module-binary-cataloger |
| github.com/bboreham/go-loser | v0.0.0-20230920113527-fcc2c21820a3 |  | go-module-binary-cataloger |
| github.com/bboreham/go-loser | v0.0.0-20230920113527-fcc2c21820a3 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v4 | v4.3.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cilium/ebpf | v0.11.0 |  | go-module-binary-cataloger |
| github.com/cncf/xds/go | v0.0.0-20240423153145-555b57ec207b |  | go-module-binary-cataloger |
| github.com/cncf/xds/go | v0.0.0-20240423153145-555b57ec207b |  | go-module-binary-cataloger |
| github.com/containerd/cgroups/v3 | v3.0.3 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.5.0 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.5.0 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/dennwc/varint | v1.0.0 |  | go-module-binary-cataloger |
| github.com/dennwc/varint | v1.0.0 |  | go-module-binary-cataloger |
| github.com/digitalocean/godo | v1.122.0 |  | go-module-binary-cataloger |
| github.com/digitalocean/godo | v1.122.0 |  | go-module-binary-cataloger |
| github.com/distribution/reference | v0.5.0 |  | go-module-binary-cataloger |
| github.com/distribution/reference | v0.5.0 |  | go-module-binary-cataloger |
| github.com/docker/docker | v27.2.0+incompatible |  | go-module-binary-cataloger |
| github.com/docker/docker | v27.2.0+incompatible |  | go-module-binary-cataloger |
| github.com/docker/go-connections | v0.4.0 |  | go-module-binary-cataloger |
| github.com/docker/go-connections | v0.4.0 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/edsrzf/mmap-go | v1.1.0 |  | go-module-binary-cataloger |
| github.com/edsrzf/mmap-go | v1.1.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.11.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.11.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/go-control-plane | v0.13.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/go-control-plane | v0.13.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/protoc-gen-validate | v1.1.0 |  | go-module-binary-cataloger |
| github.com/envoyproxy/protoc-gen-validate | v1.1.0 |  | go-module-binary-cataloger |
| github.com/facette/natsort | v0.0.0-20181210072756-2cd4dd1e2dcb |  | go-module-binary-cataloger |
| github.com/facette/natsort | v0.0.0-20181210072756-2cd4dd1e2dcb |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.16.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.16.0 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.7.0 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.7.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/go-kit/kit | v0.12.0 |  | go-module-binary-cataloger |
| github.com/go-kit/log | v0.2.1 |  | go-module-binary-cataloger |
| github.com/go-kit/log | v0.2.1 |  | go-module-binary-cataloger |
| github.com/go-logfmt/logfmt | v0.6.0 |  | go-module-binary-cataloger |
| github.com/go-logfmt/logfmt | v0.6.0 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.2 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.2 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/analysis | v0.22.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/analysis | v0.22.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/errors | v0.22.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/errors | v0.22.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.20.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.20.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.20.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.20.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/loads | v0.21.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/loads | v0.21.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/spec | v0.20.14 |  | go-module-binary-cataloger |
| github.com/go-openapi/spec | v0.20.14 |  | go-module-binary-cataloger |
| github.com/go-openapi/strfmt | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/strfmt | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.22.9 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.22.9 |  | go-module-binary-cataloger |
| github.com/go-openapi/validate | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/validate | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-resty/resty/v2 | v2.13.1 |  | go-module-binary-cataloger |
| github.com/go-resty/resty/v2 | v2.13.1 |  | go-module-binary-cataloger |
| github.com/go-zookeeper/zk | v1.0.3 |  | go-module-binary-cataloger |
| github.com/go-zookeeper/zk | v1.0.3 |  | go-module-binary-cataloger |
| github.com/godbus/dbus/v5 | v5.0.4 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.1 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.1 |  | go-module-binary-cataloger |
| github.com/golang/groupcache | v0.0.0-20210331224755-41bb18bfe9da |  | go-module-binary-cataloger |
| github.com/golang/groupcache | v0.0.0-20210331224755-41bb18bfe9da |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.6.8 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.6.8 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.6.0 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.6.0 |  | go-module-binary-cataloger |
| github.com/google/go-querystring | v1.1.0 |  | go-module-binary-cataloger |
| github.com/google/go-querystring | v1.1.0 |  | go-module-binary-cataloger |
| github.com/google/gofuzz | v1.2.0 |  | go-module-binary-cataloger |
| github.com/google/gofuzz | v1.2.0 |  | go-module-binary-cataloger |
| github.com/google/pprof | v0.0.0-20240711041743-f6c9dda6c6da |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.8 |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.8 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.4 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.4 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.13.0 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.13.0 |  | go-module-binary-cataloger |
| github.com/gophercloud/gophercloud | v1.14.0 |  | go-module-binary-cataloger |
| github.com/gophercloud/gophercloud | v1.14.0 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.0 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.0 |  | go-module-binary-cataloger |
| github.com/grafana/regexp | v0.0.0-20240518133315-a468a5bfb3bc |  | go-module-binary-cataloger |
| github.com/grafana/regexp | v0.0.0-20240518133315-a468a5bfb3bc |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.22.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/consul/api | v1.29.4 |  | go-module-binary-cataloger |
| github.com/hashicorp/consul/api | v1.29.4 |  | go-module-binary-cataloger |
| github.com/hashicorp/cronexpr | v1.1.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/cronexpr | v1.1.2 |  | go-module-binary-cataloger |
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
| github.com/hashicorp/go-retryablehttp | v0.7.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-rootcerts | v1.0.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v0.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v0.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/nomad/api | v0.0.0-20240717122358-3d93bd3778f3 |  | go-module-binary-cataloger |
| github.com/hashicorp/nomad/api | v0.0.0-20240717122358-3d93bd3778f3 |  | go-module-binary-cataloger |
| github.com/hashicorp/serf | v0.10.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/serf | v0.10.1 |  | go-module-binary-cataloger |
| github.com/hetznercloud/hcloud-go/v2 | v2.13.1 |  | go-module-binary-cataloger |
| github.com/hetznercloud/hcloud-go/v2 | v2.13.1 |  | go-module-binary-cataloger |
| github.com/imdario/mergo | v0.3.16 |  | go-module-binary-cataloger |
| github.com/imdario/mergo | v0.3.16 |  | go-module-binary-cataloger |
| github.com/ionos-cloud/sdk-go/v6 | v6.2.1 |  | go-module-binary-cataloger |
| github.com/ionos-cloud/sdk-go/v6 | v6.2.1 |  | go-module-binary-cataloger |
| github.com/jmespath/go-jmespath | v0.4.0 |  | go-module-binary-cataloger |
| github.com/jmespath/go-jmespath | v0.4.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/jpillora/backoff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/jpillora/backoff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/julienschmidt/httprouter | v1.3.0 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.9 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.9 |  | go-module-binary-cataloger |
| github.com/kolo/xmlrpc | v0.0.0-20220921171641-a4b6fa1dd06b |  | go-module-binary-cataloger |
| github.com/kolo/xmlrpc | v0.0.0-20220921171641-a4b6fa1dd06b |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/linode/linodego | v1.40.0 |  | go-module-binary-cataloger |
| github.com/linode/linodego | v1.40.0 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.13 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.13 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mdlayher/socket | v0.4.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/socket | v0.4.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/vsock | v1.2.1 |  | go-module-binary-cataloger |
| github.com/mdlayher/vsock | v1.2.1 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.62 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.62 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.0 |  | go-module-binary-cataloger |
| github.com/moby/docker-image-spec | v1.3.1 |  | go-module-binary-cataloger |
| github.com/moby/docker-image-spec | v1.3.1 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/mwitkow/go-conntrack | v0.0.0-20190716064945-2f068394615f |  | go-module-binary-cataloger |
| github.com/mwitkow/go-conntrack | v0.0.0-20190716064945-2f068394615f |  | go-module-binary-cataloger |
| github.com/nsf/jsondiff | v0.0.0-20230430225905-43f6cf3098c1 |  | go-module-binary-cataloger |
| github.com/oklog/run | v1.1.0 |  | go-module-binary-cataloger |
| github.com/oklog/ulid | v1.3.1 |  | go-module-binary-cataloger |
| github.com/oklog/ulid | v1.3.1 |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opencontainers/image-spec | v1.0.2 |  | go-module-binary-cataloger |
| github.com/opencontainers/image-spec | v1.0.2 |  | go-module-binary-cataloger |
| github.com/opencontainers/runtime-spec | v1.0.2 |  | go-module-binary-cataloger |
| github.com/ovh/go-ovh | v1.6.0 |  | go-module-binary-cataloger |
| github.com/ovh/go-ovh | v1.6.0 |  | go-module-binary-cataloger |
| github.com/pbnjay/memory | v0.0.0-20210728143218-7b4eea64cf58 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/prometheus/alertmanager | v0.27.0 |  | go-module-binary-cataloger |
| github.com/prometheus/alertmanager | v0.27.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.20.3 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.20.3 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.1 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.59.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.59.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common/assets | v0.2.0 |  | go-module-binary-cataloger |
| github.com/prometheus/common/sigv4 | v0.1.0 |  | go-module-binary-cataloger |
| github.com/prometheus/common/sigv4 | v0.1.0 |  | go-module-binary-cataloger |
| github.com/prometheus/exporter-toolkit | v0.12.0 |  | go-module-binary-cataloger |
| github.com/prometheus/exporter-toolkit | v0.12.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.15.1 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.15.1 |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.0.0-20241022105352-91d80252c3e5 |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.0.0-20241022105352-91d80252c3e5 |  | go-module-binary-cataloger |
| github.com/scaleway/scaleway-sdk-go | v1.0.0-beta.30 |  | go-module-binary-cataloger |
| github.com/scaleway/scaleway-sdk-go | v1.0.0-beta.30 |  | go-module-binary-cataloger |
| github.com/simonpasquier/klog-gokit | v0.3.0 |  | go-module-binary-cataloger |
| github.com/simonpasquier/klog-gokit/v3 | v3.5.0 |  | go-module-binary-cataloger |
| github.com/simonpasquier/klog-gokit/v3 | v3.5.0 |  | go-module-binary-cataloger |
| github.com/sirupsen/logrus | v1.9.3 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.5 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.5 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/vultr/govultr/v2 | v2.17.2 |  | go-module-binary-cataloger |
| github.com/vultr/govultr/v2 | v2.17.2 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/xhit/go-str2duration/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/xhit/go-str2duration/v2 | v2.1.0 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.14.0 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.14.0 |  | go-module-binary-cataloger |
| go.opencensus.io | v0.24.0 |  | go-module-binary-cataloger |
| go.opencensus.io | v0.24.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/pdata | v1.14.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/pdata | v1.14.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/semconv | v0.108.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/semconv | v0.108.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.53.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.53.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.29.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.3.1 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/automaxprocs | v1.5.3 |  | go-module-binary-cataloger |
| go.uber.org/goleak | v1.3.0 |  | go-module-binary-cataloger |
| go.uber.org/goleak | v1.3.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.26.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.26.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20240119083558-1b970713d09a |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20240119083558-1b970713d09a |  | go-module-binary-cataloger |
| golang.org/x/net | v0.28.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.28.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.8.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.8.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.18.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.18.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.6.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.6.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.195.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.195.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20240827150818-7e3bb234dfed |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20240827150818-7e3bb234dfed |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20240903143218-8af14fe29dc1 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20240903143218-8af14fe29dc1 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.66.0 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.66.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.34.2 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.34.2 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/ini.v1 | v1.67.0 |  | go-module-binary-cataloger |
| gopkg.in/ini.v1 | v1.67.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| k8s.io/api | v0.31.0 |  | go-module-binary-cataloger |
| k8s.io/api | v0.31.0 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.31.0 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.31.0 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.31.0 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.31.0 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20240228011516-70dd3763d340 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20240228011516-70dd3763d340 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20240711033017-18e509b52bc8 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20240711033017-18e509b52bc8 |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20221116044647-bc3834ca7abd |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20221116044647-bc3834ca7abd |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v4 | v4.4.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v4 | v4.4.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.4.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.4.0 |  | go-module-binary-cataloger |
| stdlib | go1.23.2 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.2 | BSD-3-Clause | go-module-binary-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/grafana

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| @grafana-plugins/grafana-azure-monitor-datasource | 10.4.3 |  | javascript-package-cataloger |
| @grafana-plugins/grafana-pyroscope-datasource | 10.4.3 |  | javascript-package-cataloger |
| @grafana-plugins/grafana-testdata-datasource | 10.4.3 |  | javascript-package-cataloger |
| @grafana-plugins/parca | 10.4.3 |  | javascript-package-cataloger |
| @grafana-plugins/stackdriver | 10.4.3 |  | javascript-package-cataloger |
| @grafana-plugins/tempo | 10.4.3 |  | javascript-package-cataloger |
| alpine-baselayout | 3.4.3-r2 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.4.3-r2 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.4-r1 | MIT | apk-db-cataloger |
| apk-tools | 2.14.0-r5 | GPL-2.0-only | apk-db-cataloger |
| bash | 5.2.21-r0 | GPL-3.0-or-later | apk-db-cataloger |
| brotli-libs | 1.1.0-r1 | MIT | apk-db-cataloger |
| buf.build/gen/go/parca-dev/parca/bufbuild/connect-go | v1.4.1-20221222094228-8b1d3d0f62e6.1 |  | go-module-binary-cataloger |
| buf.build/gen/go/parca-dev/parca/protocolbuffers/go | v1.28.1-20221222094228-8b1d3d0f62e6.4 |  | go-module-binary-cataloger |
| busybox | 1.36.1-r15 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.36.1-r15 | GPL-2.0-only | apk-db-cataloger |
| c-ares | 1.27.0-r0 | MIT | apk-db-cataloger |
| ca-certificates | 20240226-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20230506-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| cloud.google.com/go | v0.112.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.2.3 |  | go-module-binary-cataloger |
| cloud.google.com/go/iam | v1.1.5 |  | go-module-binary-cataloger |
| cloud.google.com/go/kms | v1.15.5 |  | go-module-binary-cataloger |
| cloud.google.com/go/storage | v1.36.0 |  | go-module-binary-cataloger |
| curl | 8.5.0-r0 | curl | apk-db-cataloger |
| filippo.io/age | v1.1.1 |  | go-module-binary-cataloger |
| gcompat | 1.1.0-r4 | NCSA | apk-db-cataloger |
| github.com/Azure/azure-pipeline-go | v0.2.3 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go | v68.0.0+incompatible |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.9.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.5.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.5.1 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/keyvault/azkeys | v0.9.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/keyvault/internal | v0.7.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-storage-blob-go | v0.15.0 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest | v0.11.29 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/adal | v0.9.23 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/date | v0.3.0 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/to | v0.4.0 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/autorest/validation | v0.3.1 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/logger | v0.2.1 |  | go-module-binary-cataloger |
| github.com/Azure/go-autorest/tracing | v0.6.0 |  | go-module-binary-cataloger |
| github.com/Azure/go-ntlmssp | v0.0.0-20220621081337-cb9428e4ac1e |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.2.1 |  | go-module-binary-cataloger |
| github.com/BurntSushi/toml | v1.3.2 |  | go-module-binary-cataloger |
| github.com/FZambia/eagle | v0.1.0 |  | go-module-binary-cataloger |
| github.com/Masterminds/goutils | v1.1.1 |  | go-module-binary-cataloger |
| github.com/Masterminds/semver | v1.5.0 |  | go-module-binary-cataloger |
| github.com/Masterminds/semver/v3 | v3.1.1 |  | go-module-binary-cataloger |
| github.com/Masterminds/sprig/v3 | v3.2.2 |  | go-module-binary-cataloger |
| github.com/NYTimes/gziphandler | v1.1.1 |  | go-module-binary-cataloger |
| github.com/ProtonMail/go-crypto | v0.0.0-20230828082145-3c4c8a2d2371 |  | go-module-binary-cataloger |
| github.com/RoaringBitmap/roaring | v0.9.4 |  | go-module-binary-cataloger |
| github.com/VividCortex/mysqlerr | v0.0.0-20170204212430-6c6b55f8796f |  | go-module-binary-cataloger |
| github.com/agext/levenshtein | v1.2.1 |  | go-module-binary-cataloger |
| github.com/alecthomas/units | v0.0.0-20231202071711-9a357b53e9c9 |  | go-module-binary-cataloger |
| github.com/andybalholm/brotli | v1.0.5 |  | go-module-binary-cataloger |
| github.com/antlr/antlr4/runtime/Go/antlr/v4 | v4.0.0-20230305170008-8188dc5388df |  | go-module-binary-cataloger |
| github.com/apache/arrow/go/v15 | v15.0.0 |  | go-module-binary-cataloger |
| github.com/apapsch/go-jsonmerge/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/apparentlymart/go-textseg/v13 | v13.0.0 |  | go-module-binary-cataloger |
| github.com/armon/go-metrics | v0.4.1 |  | go-module-binary-cataloger |
| github.com/armon/go-radix | v1.0.0 |  | go-module-binary-cataloger |
| github.com/asaskevich/govalidator | v0.0.0-20230301143203-a9d515a09cc2 |  | go-module-binary-cataloger |
| github.com/aws/aws-sdk-go | v1.50.8 |  | go-module-binary-cataloger |
| github.com/axiomhq/hyperloglog | v0.0.0-20191112132149-a4c4c47bc57f |  | go-module-binary-cataloger |
| github.com/beevik/etree | v1.2.0 |  | go-module-binary-cataloger |
| github.com/benbjohnson/clock | v1.3.5 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/bits-and-blooms/bitset | v1.2.0 |  | go-module-binary-cataloger |
| github.com/blang/semver/v4 | v4.0.0 |  | go-module-binary-cataloger |
| github.com/blevesearch/go-porterstemmer | v1.0.3 |  | go-module-binary-cataloger |
| github.com/blevesearch/mmap-go | v1.0.4 |  | go-module-binary-cataloger |
| github.com/blevesearch/segment | v0.9.0 |  | go-module-binary-cataloger |
| github.com/blevesearch/snowballstem | v0.9.0 |  | go-module-binary-cataloger |
| github.com/blevesearch/vellum | v1.0.7 |  | go-module-binary-cataloger |
| github.com/blugelabs/bluge | v0.1.9 |  | go-module-binary-cataloger |
| github.com/blugelabs/bluge_segment_api | v0.2.0 |  | go-module-binary-cataloger |
| github.com/blugelabs/ice | v1.0.0 |  | go-module-binary-cataloger |
| github.com/bradfitz/gomemcache | v0.0.0-20190913173617-a41fca850d0b |  | go-module-binary-cataloger |
| github.com/bufbuild/connect-go | v1.10.0 |  | go-module-binary-cataloger |
| github.com/bufbuild/protocompile | v0.4.0 |  | go-module-binary-cataloger |
| github.com/bwmarrin/snowflake | v0.3.0 |  | go-module-binary-cataloger |
| github.com/caio/go-tdigest | v3.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/cenkalti/backoff/v4 | v4.2.1 |  | go-module-binary-cataloger |
| github.com/centrifugal/centrifuge | v0.30.2 |  | go-module-binary-cataloger |
| github.com/centrifugal/protocol | v0.10.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.2.0 |  | go-module-binary-cataloger |
| github.com/cheekybits/genny | v1.0.0 |  | go-module-binary-cataloger |
| github.com/chromedp/cdproto | v0.0.0-20230802225258-3cf4e6d46a89 |  | go-module-binary-cataloger |
| github.com/cloudflare/circl | v1.3.7 |  | go-module-binary-cataloger |
| github.com/cockroachdb/apd/v2 | v2.0.2 |  | go-module-binary-cataloger |
| github.com/cockroachdb/errors | v1.9.1 |  | go-module-binary-cataloger |
| github.com/cockroachdb/logtags | v0.0.0-20211118104740-dabe8e521a4f |  | go-module-binary-cataloger |
| github.com/cockroachdb/redact | v1.1.3 |  | go-module-binary-cataloger |
| github.com/coreos/go-semver | v0.3.1 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.5.0 |  | go-module-binary-cataloger |
| github.com/cpuguy83/go-md2man/v2 | v2.0.3 |  | go-module-binary-cataloger |
| github.com/cristalhq/jwt/v4 | v4.0.2 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/deepmap/oapi-codegen | v1.12.4 |  | go-module-binary-cataloger |
| github.com/dennwc/varint | v1.0.0 |  | go-module-binary-cataloger |
| github.com/dgraph-io/ristretto | v0.1.1 |  | go-module-binary-cataloger |
| github.com/dgryski/go-metro | v0.0.0-20211217172704-adc40b04c140 |  | go-module-binary-cataloger |
| github.com/dgryski/go-rendezvous | v0.0.0-20200823014737-9f7001d12a5f |  | go-module-binary-cataloger |
| github.com/dlmiddlecote/sqlstats | v1.0.2 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/dustin/go-humanize | v1.0.1 |  | go-module-binary-cataloger |
| github.com/edsrzf/mmap-go | v1.1.0 |  | go-module-binary-cataloger |
| github.com/elazarl/goproxy | v0.0.0-20230731152917-f99041a5c027 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.11.0 |  | go-module-binary-cataloger |
| github.com/emicklei/proto | v1.10.0 |  | go-module-binary-cataloger |
| github.com/evanphx/json-patch | v5.6.0+incompatible |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.15.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.15.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.15.0 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fsnotify/fsnotify | v1.7.0 |  | go-module-binary-cataloger |
| github.com/fullstorydev/grpchan | v1.1.1 |  | go-module-binary-cataloger |
| github.com/gchaincl/sqlhooks | v1.3.0 |  | go-module-binary-cataloger |
| github.com/getkin/kin-openapi | v0.120.0 |  | go-module-binary-cataloger |
| github.com/getsentry/sentry-go | v0.12.0 |  | go-module-binary-cataloger |
| github.com/go-asn1-ber/asn1-ber | v1.5.4 |  | go-module-binary-cataloger |
| github.com/go-jose/go-jose/v3 | v3.0.3 |  | go-module-binary-cataloger |
| github.com/go-kit/log | v0.2.1 |  | go-module-binary-cataloger |
| github.com/go-ldap/ldap/v3 | v3.4.4 |  | go-module-binary-cataloger |
| github.com/go-logfmt/logfmt | v0.6.0 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.1 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/analysis | v0.22.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/errors | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.20.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.20.4 |  | go-module-binary-cataloger |
| github.com/go-openapi/loads | v0.21.5 |  | go-module-binary-cataloger |
| github.com/go-openapi/runtime | v0.27.1 |  | go-module-binary-cataloger |
| github.com/go-openapi/spec | v0.20.14 |  | go-module-binary-cataloger |
| github.com/go-openapi/strfmt | v0.22.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.22.9 |  | go-module-binary-cataloger |
| github.com/go-openapi/validate | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-redis/redis/v8 | v8.11.5 |  | go-module-binary-cataloger |
| github.com/go-sourcemap/sourcemap | v2.1.3+incompatible |  | go-module-binary-cataloger |
| github.com/go-sql-driver/mysql | v1.7.1 |  | go-module-binary-cataloger |
| github.com/go-stack/stack | v1.8.1 |  | go-module-binary-cataloger |
| github.com/gobwas/glob | v0.2.3 |  | go-module-binary-cataloger |
| github.com/goccy/go-json | v0.10.2 |  | go-module-binary-cataloger |
| github.com/gofrs/uuid | v4.4.0+incompatible |  | go-module-binary-cataloger |
| github.com/gogo/googleapis | v1.4.1 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/gogo/status | v1.1.1 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v4 | v4.5.0 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.0 |  | go-module-binary-cataloger |
| github.com/golang-migrate/migrate/v4 | v4.7.0 |  | go-module-binary-cataloger |
| github.com/golang-sql/civil | v0.0.0-20220223132316-b832511892a9 |  | go-module-binary-cataloger |
| github.com/golang-sql/sqlexp | v0.1.0 |  | go-module-binary-cataloger |
| github.com/golang/glog | v1.2.0 |  | go-module-binary-cataloger |
| github.com/golang/groupcache | v0.0.0-20210331224755-41bb18bfe9da |  | go-module-binary-cataloger |
| github.com/golang/mock | v1.6.0 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.3 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/google/btree | v1.1.2 |  | go-module-binary-cataloger |
| github.com/google/cel-go | v0.17.7 |  | go-module-binary-cataloger |
| github.com/google/flatbuffers | v23.5.26+incompatible |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.6.8 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.6.0 |  | go-module-binary-cataloger |
| github.com/google/gofuzz | v1.2.0 |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.7 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/wire | v0.5.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.2 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.12.0 |  | go-module-binary-cataloger |
| github.com/gorilla/mux | v1.8.0 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.0 |  | go-module-binary-cataloger |
| github.com/grafana/alerting | v0.0.0-20240213130827-92f64f0f2a12 |  | go-module-binary-cataloger |
| github.com/grafana/cue | v0.0.0-20230926092038-971951014e3f |  | go-module-binary-cataloger |
| github.com/grafana/cuetsy | v0.1.11 |  | go-module-binary-cataloger |
| github.com/grafana/dataplane/sdata | v0.0.7 |  | go-module-binary-cataloger |
| github.com/grafana/dskit | v0.0.0-20240104111617-ea101a3b86eb |  | go-module-binary-cataloger |
| github.com/grafana/gofpdf | v0.0.0-20231002120153-857cc45be447 |  | go-module-binary-cataloger |
| github.com/grafana/grafana | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana | UNKNOWN |  | go-module-binary-cataloger |
| github.com/grafana/grafana-aws-sdk | v0.25.1 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-azure-sdk-go | v1.12.0 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-google-sdk-go | v0.1.0 |  | go-module-binary-cataloger |
| github.com/grafana/grafana-plugin-sdk-go | v0.218.0 |  | go-module-binary-cataloger |
| github.com/grafana/kindsys | v0.0.0-20230508162304-452481b63482 |  | go-module-binary-cataloger |
| github.com/grafana/prometheus-alertmanager | v0.25.1-0.20240208102907-e82436ce63e6 |  | go-module-binary-cataloger |
| github.com/grafana/pyroscope-go/godeltaprof | v0.1.6 |  | go-module-binary-cataloger |
| github.com/grafana/pyroscope/api | v0.3.0 |  | go-module-binary-cataloger |
| github.com/grafana/regexp | v0.0.0-20221123153739-15dc172cd2db |  | go-module-binary-cataloger |
| github.com/grafana/saml | v0.4.15-0.20231025143828-a6c0e9b86a4c |  | go-module-binary-cataloger |
| github.com/grafana/sqlds/v3 | v3.2.0 |  | go-module-binary-cataloger |
| github.com/grafana/tempo | v1.5.1-0.20230524121406-1dc1bfe7085b |  | go-module-binary-cataloger |
| github.com/grafana/thema | v0.0.0-20230712153715-375c1b45f3ed |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-middleware | v1.4.0 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/go-grpc-prometheus | v1.2.1-0.20191002090509-6af20e3a5340 |  | go-module-binary-cataloger |
| github.com/grpc-ecosystem/grpc-gateway/v2 | v2.19.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-hclog | v0.16.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-immutable-radix | v1.3.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-msgpack | v0.5.5 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-plugin | v1.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.4 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-sockaddr | v1.0.6 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-version | v1.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru | v0.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru/v2 | v2.0.7 |  | go-module-binary-cataloger |
| github.com/hashicorp/hcl/v2 | v2.17.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/memberlist | v0.5.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/yamux | v0.1.1 |  | go-module-binary-cataloger |
| github.com/huandu/xstrings | v1.3.2 |  | go-module-binary-cataloger |
| github.com/igm/sockjs-go/v3 | v3.0.2 |  | go-module-binary-cataloger |
| github.com/imdario/mergo | v0.3.16 |  | go-module-binary-cataloger |
| github.com/influxdata/influxdb-client-go/v2 | v2.12.3 |  | go-module-binary-cataloger |
| github.com/influxdata/line-protocol | v0.0.0-20210311194329-9aa0e372d097 |  | go-module-binary-cataloger |
| github.com/invopop/yaml | v0.2.0 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.5.0 |  | go-module-binary-cataloger |
| github.com/jhump/protoreflect | v1.15.1 |  | go-module-binary-cataloger |
| github.com/jmespath/go-jmespath | v0.4.0 |  | go-module-binary-cataloger |
| github.com/jmoiron/sqlx | v1.3.5 |  | go-module-binary-cataloger |
| github.com/jonboulle/clockwork | v0.4.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/jpillora/backoff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.4 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.2.5 |  | go-module-binary-cataloger |
| github.com/kr/pretty | v0.3.1 |  | go-module-binary-cataloger |
| github.com/kr/text | v0.2.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/lib/pq | v1.10.9 |  | go-module-binary-cataloger |
| github.com/linkedin/goavro/v2 | v2.10.0 |  | go-module-binary-cataloger |
| github.com/m3db/prometheus_remote_client_golang | v0.4.4 |  | go-module-binary-cataloger |
| github.com/magefile/mage | v1.15.0 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mattermost/xml-roundtrip-validator | v0.1.0 |  | go-module-binary-cataloger |
| github.com/mattetti/filebuffer | v1.0.1 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.13 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.13 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.13 |  | go-module-binary-cataloger |
| github.com/mattn/go-ieproxy | v0.0.3 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.19 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.19 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.19 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.13 |  | go-module-binary-cataloger |
| github.com/mattn/go-sqlite3 | v1.14.19 |  | go-module-binary-cataloger |
| github.com/matttproud/golang_protobuf_extensions | v1.0.4 |  | go-module-binary-cataloger |
| github.com/microsoft/go-mssqldb | v1.6.1-0.20240214161942-b65008136246 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.57 |  | go-module-binary-cataloger |
| github.com/mitchellh/copystructure | v1.2.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-testing-interface | v1.14.1 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-wordwrap | v1.0.1 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/reflectwalk | v1.0.2 |  | go-module-binary-cataloger |
| github.com/mithrandie/csvq | v1.17.10 |  | go-module-binary-cataloger |
| github.com/mithrandie/csvq-driver | v1.6.8 |  | go-module-binary-cataloger |
| github.com/mithrandie/go-file/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/mithrandie/go-text | v1.5.4 |  | go-module-binary-cataloger |
| github.com/mithrandie/ternary | v1.1.1 |  | go-module-binary-cataloger |
| github.com/moby/spdystream | v0.2.0 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/mohae/deepcopy | v0.0.0-20170929034955-c48cc78d4826 |  | go-module-binary-cataloger |
| github.com/mpvl/unique | v0.0.0-20150818121801-cbe035fff7de |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/mwitkow/go-conntrack | v0.0.0-20190716064945-2f068394615f |  | go-module-binary-cataloger |
| github.com/mxk/go-flowrate | v0.0.0-20140419014527-cca7078d478f |  | go-module-binary-cataloger |
| github.com/oklog/run | v1.1.0 |  | go-module-binary-cataloger |
| github.com/oklog/ulid | v1.3.1 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v0.0.5 |  | go-module-binary-cataloger |
| github.com/opentracing-contrib/go-stdlib | v1.0.0 |  | go-module-binary-cataloger |
| github.com/opentracing/opentracing-go | v1.2.0 |  | go-module-binary-cataloger |
| github.com/ory/fosite | v0.44.1-0.20230317114349-45a6785cc54f |  | go-module-binary-cataloger |
| github.com/ory/go-convenience | v0.1.0 |  | go-module-binary-cataloger |
| github.com/ory/x | v0.0.214 |  | go-module-binary-cataloger |
| github.com/patrickmn/go-cache | v2.1.0+incompatible |  | go-module-binary-cataloger |
| github.com/pborman/uuid | v1.2.0 |  | go-module-binary-cataloger |
| github.com/perimeterx/marshmallow | v1.1.5 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.18 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pmezard/go-difflib | v1.0.1-0.20181226105442-5d4384ee4fb2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.18.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.5.0 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.46.0 |  | go-module-binary-cataloger |
| github.com/prometheus/common/sigv4 | v0.1.0 |  | go-module-binary-cataloger |
| github.com/prometheus/exporter-toolkit | v0.11.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.12.0 |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.49.0 |  | go-module-binary-cataloger |
| github.com/protocolbuffers/txtpbfmt | v0.0.0-20220428173112-74888fd59c2b |  | go-module-binary-cataloger |
| github.com/redis/go-redis/v9 | v9.0.2 |  | go-module-binary-cataloger |
| github.com/redis/rueidis | v1.0.16 |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.3.4 |  | go-module-binary-cataloger |
| github.com/robfig/cron/v3 | v3.0.1 |  | go-module-binary-cataloger |
| github.com/rogpeppe/go-internal | v1.11.0 |  | go-module-binary-cataloger |
| github.com/rs/cors | v1.10.1 |  | go-module-binary-cataloger |
| github.com/russellhaering/goxmldsig | v1.4.0 |  | go-module-binary-cataloger |
| github.com/russross/blackfriday/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/sean-/seed | v0.0.0-20170313163322-e2103e2c3529 |  | go-module-binary-cataloger |
| github.com/segmentio/asm | v1.2.0 |  | go-module-binary-cataloger |
| github.com/segmentio/encoding | v0.3.6 |  | go-module-binary-cataloger |
| github.com/sergi/go-diff | v1.3.1 |  | go-module-binary-cataloger |
| github.com/shopspring/decimal | v1.2.0 |  | go-module-binary-cataloger |
| github.com/shurcooL/httpfs | v0.0.0-20230704072500-f1e31cf0ba5c |  | go-module-binary-cataloger |
| github.com/shurcooL/vfsgen | v0.0.0-20200824052919-0d455de96546 |  | go-module-binary-cataloger |
| github.com/spf13/cast | v1.5.0 |  | go-module-binary-cataloger |
| github.com/spf13/cobra | v1.8.0 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.5 |  | go-module-binary-cataloger |
| github.com/spyzhov/ajson | v0.9.0 |  | go-module-binary-cataloger |
| github.com/stoewer/go-strcase | v1.3.0 |  | go-module-binary-cataloger |
| github.com/stretchr/objx | v0.5.2 |  | go-module-binary-cataloger |
| github.com/stretchr/testify | v1.9.0 |  | go-module-binary-cataloger |
| github.com/teris-io/shortid | v0.0.0-20171029131806-771a37caa5cf |  | go-module-binary-cataloger |
| github.com/ua-parser/uap-go | v0.0.0-20211112212520-00c877edfe0f |  | go-module-binary-cataloger |
| github.com/uber/jaeger-client-go | v2.30.0+incompatible |  | go-module-binary-cataloger |
| github.com/uber/jaeger-lib | v2.4.1+incompatible |  | go-module-binary-cataloger |
| github.com/unknwon/bra | v0.0.0-20200517080246-1e3013ecaff8 |  | go-module-binary-cataloger |
| github.com/unknwon/com | v1.0.1 |  | go-module-binary-cataloger |
| github.com/unknwon/log | v0.0.0-20150304194804-e617c87089d3 |  | go-module-binary-cataloger |
| github.com/urfave/cli | v1.22.14 |  | go-module-binary-cataloger |
| github.com/urfave/cli/v2 | v2.25.0 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/vectordotdev/go-datemath | v0.1.1-0.20220323213446-f3954d0b18ae |  | go-module-binary-cataloger |
| github.com/wk8/go-ordered-map | v1.0.0 |  | go-module-binary-cataloger |
| github.com/xlab/treeprint | v1.2.0 |  | go-module-binary-cataloger |
| github.com/xrash/smetrics | v0.0.0-20201216005158-039620a65673 |  | go-module-binary-cataloger |
| github.com/yalue/merged_fs | v1.2.2 |  | go-module-binary-cataloger |
| github.com/yudai/gojsondiff | v1.0.0 |  | go-module-binary-cataloger |
| github.com/yudai/golcs | v0.0.0-20170316035057-ecda9a501e82 |  | go-module-binary-cataloger |
| github.com/zclconf/go-cty | v1.13.0 |  | go-module-binary-cataloger |
| github.com/zeebo/xxh3 | v1.0.2 |  | go-module-binary-cataloger |
| glibc | 2.35-r0 |  | apk-db-cataloger |
| glibc-bin | 2.35-r0 |  | apk-db-cataloger |
| go.etcd.io/etcd/api/v3 | v3.5.10 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.5.10 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.5.10 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.13.1 |  | go-module-binary-cataloger |
| go.opencensus.io | v0.24.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/collector/pdata | v1.0.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc | v0.49.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace | v0.49.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.46.1 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/propagators/jaeger | v1.22.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/samplers/jaegerremote | v0.18.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.22.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/jaeger | v1.10.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace | v1.24.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc | v1.24.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.22.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.24.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.22.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/proto/otlp | v1.1.0 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/goleak | v1.3.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.26.0 |  | go-module-binary-cataloger |
| gocloud.dev | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20231206192017-f3f8817b8deb |  | go-module-binary-cataloger |
| golang.org/x/mod | v0.14.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.18.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.6.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.20.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.15.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.5.0 |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20220907171357-04be3eba64a2 |  | go-module-binary-cataloger |
| gonum.org/v1/gonum | v0.12.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.155.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20240123012728-ef4313101c80 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20240123012728-ef4313101c80 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20240123012728-ef4313101c80 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.62.1 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.33.0 |  | go-module-binary-cataloger |
| gopkg.in/fsnotify/fsnotify.v1 | v1.4.7 |  | go-module-binary-cataloger |
| gopkg.in/inf.v0 | v0.9.1 |  | go-module-binary-cataloger |
| gopkg.in/ini.v1 | v1.67.0 |  | go-module-binary-cataloger |
| gopkg.in/mail.v2 | v2.3.1 |  | go-module-binary-cataloger |
| gopkg.in/natefinch/lumberjack.v2 | v2.2.1 |  | go-module-binary-cataloger |
| gopkg.in/square/go-jose.v2 | v2.6.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| k8s.io/api | v0.29.0 |  | go-module-binary-cataloger |
| k8s.io/apimachinery | v0.29.0 |  | go-module-binary-cataloger |
| k8s.io/apiserver | v0.29.0 |  | go-module-binary-cataloger |
| k8s.io/client-go | v0.29.0 |  | go-module-binary-cataloger |
| k8s.io/component-base | v0.29.0 |  | go-module-binary-cataloger |
| k8s.io/klog/v2 | v2.110.1 |  | go-module-binary-cataloger |
| k8s.io/kms | v0.29.0 |  | go-module-binary-cataloger |
| k8s.io/kube-aggregator | v0.29.0 |  | go-module-binary-cataloger |
| k8s.io/kube-openapi | v0.0.0-20240220201932-37d671a357a5 |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20230726121419-3b25d923346b |  | go-module-binary-cataloger |
| libc-utils | 0.7.2-r5 | BSD-2-Clause AND BSD-3-Clause | apk-db-cataloger |
| libcrypto3 | 3.1.4-r5 | Apache-2.0 | apk-db-cataloger |
| libcurl | 8.5.0-r0 | curl | apk-db-cataloger |
| libgcc | 13.2.1_git20231014-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libidn2 | 2.3.4-r4 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libncursesw | 6.4_p20231125-r0 | X11 | apk-db-cataloger |
| libssl3 | 3.1.4-r5 | Apache-2.0 | apk-db-cataloger |
| libucontext | 1.2-r2 | ISC | apk-db-cataloger |
| libunistring | 1.1-r2 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| musl | 1.2.4_git20230717-r4 | MIT | apk-db-cataloger |
| musl-obstack | 1.2.3-r2 | GPL-2.0-or-later | apk-db-cataloger |
| musl-utils | 1.2.4_git20230717-r4 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.4_p20231125-r0 | X11 | apk-db-cataloger |
| nghttp2-libs | 1.58.0-r0 | MIT | apk-db-cataloger |
| react-router | 6.21.3 | MIT | javascript-package-cataloger |
| readline | 8.2.1-r2 | GPL-2.0-or-later | apk-db-cataloger |
| scanelf | 1.3.7-r2 | GPL-2.0-only | apk-db-cataloger |
| sigs.k8s.io/apiserver-network-proxy/konnectivity-client | v0.28.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/json | v0.0.0-20221116044647-bc3834ca7abd |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v4 | v4.4.1 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.3.0 |  | go-module-binary-cataloger |
| ssl_client | 1.36.1-r15 | GPL-2.0-only | apk-db-cataloger |
| stdlib | go1.21.10 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.21.10 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.21.10 | BSD-3-Clause | go-module-binary-cataloger |
| tzdata | 2024a-r0 |  | apk-db-cataloger |
| xorm.io/builder | v0.3.6 |  | go-module-binary-cataloger |
| xorm.io/core | v0.7.3 |  | go-module-binary-cataloger |
| xorm.io/xorm | UNKNOWN |  | go-module-binary-cataloger |
| zlib | 1.3.1-r0 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/ollama

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| apt | 2.8.3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| base-files | 13ubuntu10.2 |  | dpkg-db-cataloger |
| base-passwd | 3.6.3build1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.21-2ubuntu4 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| bsdutils | 1:2.39.3-9ubuntu6.3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ca-certificates | 20240203 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| coreutils | 9.4-3ubuntu6 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| dash | 0.5.12-6ubuntu5 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| debconf | 1.5.86ubuntu1 | BSD-2-Clause | dpkg-db-cataloger |
| debianutils | 5.17build1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| diffutils | 1:3.10-1build1 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dpkg | 1.22.6ubuntu6.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| findutils | 4.9.0-5build1 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| gcc-14-base | 14.2.0-4ubuntu2~24.04 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| github.com/agnivade/levenshtein | v1.1.1 |  | go-module-binary-cataloger |
| github.com/apache/arrow/go/arrow | v0.0.0-20211112161151-bc219186db40 |  | go-module-binary-cataloger |
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
| github.com/leodido/go-urn | v1.4.0 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.14 |  | go-module-binary-cataloger |
| github.com/nlpodyssey/gopickle | v0.3.0 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v0.0.5 |  | go-module-binary-cataloger |
| github.com/ollama/ollama | UNKNOWN |  | go-module-binary-cataloger |
| github.com/pdevine/tensor | v0.0.0-20240510204454-f88f4562727c |  | go-module-binary-cataloger |
| github.com/pelletier/go-toml/v2 | v2.2.2 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.2.0 |  | go-module-binary-cataloger |
| github.com/spf13/cobra | v1.7.0 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.5 |  | go-module-binary-cataloger |
| github.com/ugorji/go/codec | v1.2.12 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/xtgo/set | v1.0.0 |  | go-module-binary-cataloger |
| go4.org/unsafe/assume-no-moving-gc | v0.0.0-20231121144256-b99613f794b6 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.36.0 |  | go-module-binary-cataloger |
| golang.org/x/exp | v0.0.0-20250218142911-aa4b98e5adaa |  | go-module-binary-cataloger |
| golang.org/x/image | v0.22.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.38.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.12.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.31.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.30.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.23.0 |  | go-module-binary-cataloger |
| golang.org/x/xerrors | v0.0.0-20200804184101-5ec99f83aff1 |  | go-module-binary-cataloger |
| gonum.org/v1/gonum | v0.15.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.34.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gorgonia.org/vecf32 | v0.9.0 |  | go-module-binary-cataloger |
| gorgonia.org/vecf64 | v0.9.0 |  | go-module-binary-cataloger |
| gpgv | 2.4.4-2ubuntu17.3 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
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
| libblkid1 | 2.39.3-9ubuntu6.3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5.1build0.1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.39-0ubuntu8.5 | GFDL-1.3-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.39-0ubuntu8.5 | GFDL-1.3-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.4-2build2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-5ubuntu2.2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.36-4build1 |  | dpkg-db-cataloger |
| libdb5.3t64 | 5.3.28+dfsg2-7 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libdebconfclient0 | 0.271ubuntu3 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libexpat1 | 2.6.1-2ubuntu0.3 | MIT | dpkg-db-cataloger |
| libext2fs2t64 | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi8 | 3.4.6-1build1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libgcc-s1 | 14.2.0-4ubuntu2~24.04 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.3-2build1 | GPL-2.0-only | dpkg-db-cataloger |
| libgmp10 | 2:6.3.0+dfsg-2ubuntu6.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30t64 | 3.8.3-1.1ubuntu3.4 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.47-3build2.1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libhogweed6t64 | 3.9.1-2.2build1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libidn2-0 | 2.3.7-2build1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1build1.1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.6.1+really5.4.5-1ubuntu0.2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmd0 | 1.1.0-2build1.1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount1 | 2.39.3-9ubuntu6.3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libncursesw6 | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8t64 | 3.9.1-2.2build1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnpth0t64 | 1.6-3.1build1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libp11-kit0 | 0.25.3-4ubuntu2.1 | Apache-2.0, BSD-3-Clause, FSFAP, FSFULLR, GPL-2.0-or-later, GPL-3.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later, X11 | dpkg-db-cataloger |
| libpam-modules | 1.5.3-5ubuntu5.4 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.3-5ubuntu5.4 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.3-5ubuntu5.4 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.3-5ubuntu5.4 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-4ubuntu2.1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.4-4ubuntu3.2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpython3-stdlib | 3.12.3-0ubuntu2.1 |  | dpkg-db-cataloger |
| libpython3.12-minimal | 3.12.3-1ubuntu0.9 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.12-stdlib | 3.12.3-1ubuntu0.9 | GPL-2.0-only | dpkg-db-cataloger |
| libreadline8t64 | 8.2-4build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libseccomp2 | 2.5.5-1ubuntu3.1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.5-2ubuntu2.1 | GPL-2.0-only | dpkg-db-cataloger |
| libsemanage-common | 3.5-1build5 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsemanage2 | 3.5-1build5 | GPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libsepol2 | 3.5-2build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsmartcols1 | 2.39.3-9ubuntu6.3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.45.1-1ubuntu2.5 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssl3t64 | 3.0.13-0ubuntu3.5 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++6 | 14.2.0-4ubuntu2~24.04 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 255.4-1ubuntu8.8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-3ubuntu0.24.04.1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo6 | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libudev1 | 255.4-1ubuntu8.8 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring5 | 1.1-2build1.1 | GFDL-1.2-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| libuuid1 | 2.39.3-9ubuntu6.3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libxxhash0 | 0.8.2-2build1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libzstd1 | 1.5.5+dfsg2-2build1.1 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-4ubuntu3.2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2.4~exp1ubuntu4.1 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| mawk | 1.3.4.20240123-1build1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 10.1.0 |  | dpkg-db-cataloger |
| mount | 2.39.3-9ubuntu6.3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ncurses-base | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4+20240113-1ubuntu2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| openssl | 3.0.13-0ubuntu3.5 |  | dpkg-db-cataloger |
| passwd | 1:4.13+dfsg1-4ubuntu3.2 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| perl-base | 5.38.2-3.2ubuntu0.1 | Artistic-2.0, Artistic-dist, BSD-3-Clause, FSFAP, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| procps | 2:4.0.4-4ubuntu3.2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| python3 | 3.12.3-0ubuntu2.1 |  | dpkg-db-cataloger |
| python3-minimal | 3.12.3-0ubuntu2.1 |  | dpkg-db-cataloger |
| python3.12 | 3.12.3-1ubuntu0.9 | GPL-2.0-only | dpkg-db-cataloger |
| python3.12-minimal | 3.12.3-1ubuntu0.9 | GPL-2.0-only | dpkg-db-cataloger |
| readline-common | 8.2-4build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| sed | 4.9-2build1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sensible-utils | 0.0.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| stdlib | go1.24.0 | BSD-3-Clause | go-module-binary-cataloger |
| sysvinit-utils | 3.08-6ubuntu3 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| tar | 1.35+dfsg-3build1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tzdata | 2025b-0ubuntu0.24.04.1 | ICU | dpkg-db-cataloger |
| ubuntu-keyring | 2023.11.28.1 |  | dpkg-db-cataloger |
| unminimize | 0.2.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.39.3-9ubuntu6.3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| zlib1g | 1:1.3.dfsg-3.1ubuntu2.1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/libretranslate

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| adduser | 3.118ubuntu2 | GPL-2.0-only | dpkg-db-cataloger |
| appdirs | 1.4.4 | MIT | python-installed-package-cataloger |
| apscheduler | 3.9.1 | MIT | python-installed-package-cataloger |
| apt | 2.0.11 | GPL-2.0-only | dpkg-db-cataloger |
| argos-translate-files | 1.3.0 |  | python-installed-package-cataloger |
| argostranslate | 1.9.6 |  | python-installed-package-cataloger |
| async-timeout | 5.0.1 |  | python-installed-package-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| babel | 2.12.1 |  | python-installed-package-cataloger |
| backports-tarfile | 1.2.0 | MIT | python-installed-package-cataloger |
| backports-zoneinfo | 0.2.1 | Apache-2.0 | python-installed-package-cataloger |
| base-files | 11ubuntu5.8 |  | dpkg-db-cataloger |
| base-passwd | 3.5.47 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.0-6ubuntu1.2 | GPL-3.0-only | dpkg-db-cataloger |
| beautifulsoup4 | 4.9.3 | MIT | python-installed-package-cataloger |
| binutils | 2.34-6ubuntu1.11 |  | dpkg-db-cataloger |
| binutils-common | 2.34-6ubuntu1.11 |  | dpkg-db-cataloger |
| binutils-x86-64-linux-gnu | 2.34-6ubuntu1.11 |  | dpkg-db-cataloger |
| bsdutils | 1:2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| build-essential | 12.8ubuntu1.1 |  | dpkg-db-cataloger |
| bzip2 | 1.0.8-2 | GPL-2.0-only | dpkg-db-cataloger |
| ca-certificates | 20240203~20.04.1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| cachelib | 0.13.0 | BSD-3-Clause | python-installed-package-cataloger |
| certifi | 2025.7.9 | MPL-2.0 | python-installed-package-cataloger |
| chardet | 5.2.0 |  | python-installed-package-cataloger |
| charset-normalizer | 3.4.2 | MIT | python-installed-package-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| click | 8.1.8 | BSD-3-Clause | python-installed-package-cataloger |
| commonmark | 0.9.1 | BSD-3-Clause | python-installed-package-cataloger |
| coreutils | 8.30-3ubuntu2 | GPL-3.0-only | dpkg-db-cataloger |
| cpp | 4:9.3.0-1ubuntu2 |  | dpkg-db-cataloger |
| cpp-9 | 9.4.0-1ubuntu1~20.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| ctranslate2 | 4.5.0 | MIT | python-installed-package-cataloger |
| cuda-cccl-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-command-line-tools-12-4 | 12.4.1-1 |  | dpkg-db-cataloger |
| cuda-compat-12-4 | 550.163.01-0ubuntu1 |  | dpkg-db-cataloger |
| cuda-compiler-12-4 | 12.4.1-1 |  | dpkg-db-cataloger |
| cuda-crt-12-4 | 12.4.131-1 |  | dpkg-db-cataloger |
| cuda-cudart-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-cudart-dev-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-cuobjdump-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-cupti-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-cupti-dev-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-cuxxfilt-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-driver-dev-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-gdb-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-libraries-12-4 | 12.4.1-1 |  | dpkg-db-cataloger |
| cuda-libraries-dev-12-4 | 12.4.1-1 |  | dpkg-db-cataloger |
| cuda-minimal-build-12-4 | 12.4.1-1 |  | dpkg-db-cataloger |
| cuda-nsight-compute-12-4 | 12.4.1-1 |  | dpkg-db-cataloger |
| cuda-nvcc-12-4 | 12.4.131-1 |  | dpkg-db-cataloger |
| cuda-nvdisasm-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-nvml-dev-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-nvprof-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-nvprune-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-nvrtc-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-nvrtc-dev-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-nvtx-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-nvvm-12-4 | 12.4.131-1 |  | dpkg-db-cataloger |
| cuda-opencl-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-opencl-dev-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-profiler-api-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-sanitizer-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-toolkit-12-4-config-common | 12.4.127-1 |  | dpkg-db-cataloger |
| cuda-toolkit-12-config-common | 12.9.79-1 |  | dpkg-db-cataloger |
| cuda-toolkit-config-common | 12.9.79-1 |  | dpkg-db-cataloger |
| dash | 0.5.10.2-6 |  | dpkg-db-cataloger |
| debconf | 1.5.73 | BSD-2-Clause | dpkg-db-cataloger |
| debianutils | 4.9.1 |  | dpkg-db-cataloger |
| deprecated | 1.2.18 | MIT | python-installed-package-cataloger |
| diffutils | 1:3.7-3 |  | dpkg-db-cataloger |
| dirmngr | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| dpkg | 1.19.7ubuntu3.2 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dpkg-dev | 1.19.7ubuntu3.2 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.45.5-2ubuntu1.2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| expiringdict | 1.2.2 |  | python-installed-package-cataloger |
| fdisk | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| filelock | 3.16.1 | Unlicense | python-installed-package-cataloger |
| findutils | 4.7.0-1ubuntu1 | GFDL-1.3-only, GPL-3.0-only | dpkg-db-cataloger |
| flask | 2.2.5 | BSD-3-Clause | python-installed-package-cataloger |
| flask-babel | 3.1.0 | BSD-3-Clause | python-installed-package-cataloger |
| flask-limiter | 2.6.3 | MIT | python-installed-package-cataloger |
| flask-session | 0.4.0 |  | python-installed-package-cataloger |
| flask-swagger | 0.2.14 | MIT | python-installed-package-cataloger |
| flask-swagger-ui | 4.11.1 | MIT | python-installed-package-cataloger |
| fontconfig-config | 2.13.1-2ubuntu3 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-1 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fsspec | 2025.3.0 | BSD-3-Clause | python-installed-package-cataloger |
| g++ | 4:9.3.0-1ubuntu2 |  | dpkg-db-cataloger |
| g++-9 | 9.4.0-1ubuntu1~20.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| gcc | 4:9.3.0-1ubuntu2 |  | dpkg-db-cataloger |
| gcc-10-base | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-9 | 9.4.0-1ubuntu1~20.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| gcc-9-base | 9.4.0-1ubuntu1~20.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| gevent | 24.2.1 | MIT | python-installed-package-cataloger |
| gnupg | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-l10n | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-utils | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg2 | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-wks-client | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-wks-server | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgv | 2.2.19-3ubuntu2.5 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| greenlet | 3.1.1 |  | python-installed-package-cataloger |
| grep | 3.4-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gunicorn | 23.0.0 | MIT | python-installed-package-cataloger |
| gzip | 1.10-0ubuntu4.1 |  | dpkg-db-cataloger |
| hostname | 3.23 | GPL-2.0-only | dpkg-db-cataloger |
| icu-devtools | 66.1-2ubuntu2.1 |  | dpkg-db-cataloger |
| idna | 3.10 | BSD-3-Clause | python-installed-package-cataloger |
| importlib-metadata | 8.0.0 | Apache-2.0 | python-installed-package-cataloger |
| importlib-metadata | 8.5.0 | Apache-2.0 | python-installed-package-cataloger |
| importlib-resources | 6.4.0 | Apache-2.0 | python-installed-package-cataloger |
| importlib-resources | 6.4.5 | Apache-2.0 | python-installed-package-cataloger |
| inflect | 7.3.1 | MIT | python-installed-package-cataloger |
| init-system-helpers | 1.57 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| itsdangerous | 2.1.2 | BSD-3-Clause | python-installed-package-cataloger |
| jaraco-collections | 5.1.0 | MIT | python-installed-package-cataloger |
| jaraco-context | 5.3.0 | MIT | python-installed-package-cataloger |
| jaraco-functools | 4.0.1 | MIT | python-installed-package-cataloger |
| jaraco-text | 3.12.1 | MIT | python-installed-package-cataloger |
| jinja2 | 3.1.6 |  | python-installed-package-cataloger |
| joblib | 1.4.2 |  | python-installed-package-cataloger |
| langdetect | 1.0.9 | MIT | python-installed-package-cataloger |
| lexilang | 1.0.6 |  | python-installed-package-cataloger |
| libacl1 | 2.2.53-6 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.0.11 | GPL-2.0-only | dpkg-db-cataloger |
| libasan5 | 9.4.0-1ubuntu1~20.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libasn1-8-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libaspell-dev | 0.60.8-1ubuntu0.1 | GFDL-1.2-only, GFDL-1.2-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libaspell15 | 0.60.8-1ubuntu0.1 | GFDL-1.2-only, GFDL-1.2-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libassuan0 | 2.5.3-7ubuntu2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libatomic1 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libattr1 | 1:2.4.48-5 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:2.8.5-2ubuntu6 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:2.8.5-2ubuntu6 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libbinutils | 2.34-6ubuntu1.11 |  | dpkg-db-cataloger |
| libblkid-dev | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libblkid1 | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbsd0 | 0.10.0-1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-2 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.31-0ubuntu9.18 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc-dev-bin | 2.31-0ubuntu9.18 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.31-0ubuntu9.18 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6-dev | 2.31-0ubuntu9.18 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcairo-gobject2 | 1.16.0-4ubuntu1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo-script-interpreter2 | 1.16.0-4ubuntu1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2 | 1.16.0-4ubuntu1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2-dev | 1.16.0-4ubuntu1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.7.9-2.1build1 | GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcc1-0 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libcom-err2 | 1.45.5-2ubuntu1.2 |  | dpkg-db-cataloger |
| libcrypt-dev | 1:4.4.10-10ubuntu4 |  | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.10-10ubuntu4 |  | dpkg-db-cataloger |
| libctf-nobfd0 | 2.34-6ubuntu1.11 |  | dpkg-db-cataloger |
| libctf0 | 2.34-6ubuntu1.11 |  | dpkg-db-cataloger |
| libcublas-12-4 | 12.4.5.8-1 |  | dpkg-db-cataloger |
| libcublas-dev-12-4 | 12.4.5.8-1 |  | dpkg-db-cataloger |
| libcufft-12-4 | 11.2.1.3-1 |  | dpkg-db-cataloger |
| libcufft-dev-12-4 | 11.2.1.3-1 |  | dpkg-db-cataloger |
| libcufile-12-4 | 1.9.1.3-1 |  | dpkg-db-cataloger |
| libcufile-dev-12-4 | 1.9.1.3-1 |  | dpkg-db-cataloger |
| libcurand-12-4 | 10.3.5.147-1 |  | dpkg-db-cataloger |
| libcurand-dev-12-4 | 10.3.5.147-1 |  | dpkg-db-cataloger |
| libcusolver-12-4 | 11.6.1.9-1 |  | dpkg-db-cataloger |
| libcusolver-dev-12-4 | 11.6.1.9-1 |  | dpkg-db-cataloger |
| libcusparse-12-4 | 12.3.1.170-1 |  | dpkg-db-cataloger |
| libcusparse-dev-12-4 | 12.3.1.170-1 |  | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg1-0.6ubuntu2 |  | dpkg-db-cataloger |
| libdebconfclient0 | 0.251ubuntu1 | BSD-2-Clause | dpkg-db-cataloger |
| libdpkg-perl | 1.19.7ubuntu3.2 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libelf1 | 0.176-1.1ubuntu0.1 | GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libexpat1 | 2.2.9-1ubuntu0.8 | MIT | dpkg-db-cataloger |
| libexpat1-dev | 2.2.9-1ubuntu0.8 | MIT | dpkg-db-cataloger |
| libext2fs2 | 1.45.5-2ubuntu1.2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| libfdisk1 | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libffi-dev | 3.3-4 |  | dpkg-db-cataloger |
| libffi7 | 3.3-4 |  | dpkg-db-cataloger |
| libfontconfig1 | 2.13.1-2ubuntu3 | HPND-sell-variant | dpkg-db-cataloger |
| libfontconfig1-dev | 2.13.1-2ubuntu3 | HPND-sell-variant | dpkg-db-cataloger |
| libfreetype-dev | 2.10.1-2ubuntu0.4 | Apache-2.0, BSD-3-Clause, FSFUL, FSFULLR, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, MPL-1.1, OFL-1.1, Zlib | dpkg-db-cataloger |
| libfreetype6 | 2.10.1-2ubuntu0.4 | Apache-2.0, BSD-3-Clause, FSFUL, FSFULLR, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, MPL-1.1, OFL-1.1, Zlib | dpkg-db-cataloger |
| libfreetype6-dev | 2.10.1-2ubuntu0.4 | Apache-2.0, BSD-3-Clause, FSFUL, FSFULLR, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, MPL-1.1, OFL-1.1, Zlib | dpkg-db-cataloger |
| libgcc-9-dev | 9.4.0-1ubuntu1~20.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgcc-s1 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.8.5-5ubuntu1.1 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm-compat4 | 1.18.1-5 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6 | 1.18.1-5 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libglib2.0-0 | 2.64.6-1~ubuntu20.04.9 | GPL-2.0-or-later | dpkg-db-cataloger |
| libglib2.0-bin | 2.64.6-1~ubuntu20.04.9 | GPL-2.0-or-later | dpkg-db-cataloger |
| libglib2.0-data | 2.64.6-1~ubuntu20.04.9 | GPL-2.0-or-later | dpkg-db-cataloger |
| libglib2.0-dev | 2.64.6-1~ubuntu20.04.9 | GPL-2.0-or-later | dpkg-db-cataloger |
| libglib2.0-dev-bin | 2.64.6-1~ubuntu20.04.9 | GPL-2.0-or-later | dpkg-db-cataloger |
| libgmp10 | 2:6.2.0+dfsg-4ubuntu0.1 | GPL-2.0-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgnutls30 | 3.6.13-2ubuntu1.12 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.37-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgssapi3-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libhcrypto4-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libheimbase1-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libheimntlm0-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libhogweed5 | 3.5.1+really3.5.1-2ubuntu0.2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libhx509-5-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libice-dev | 2:1.0.10-0ubuntu1 |  | dpkg-db-cataloger |
| libice6 | 2:1.0.10-0ubuntu1 |  | dpkg-db-cataloger |
| libicu-dev | 66.1-2ubuntu2.1 |  | dpkg-db-cataloger |
| libicu66 | 66.1-2ubuntu2.1 |  | dpkg-db-cataloger |
| libidn2-0 | 2.2.0-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libisl22 | 0.22.1-1 | BSD-2-Clause, LGPL-2.0-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libitm1 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libkrb5-26-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libksba8 | 1.3.5-2ubuntu0.20.04.2 | GPL-3.0-only | dpkg-db-cataloger |
| libldap-2.4-2 | 2.4.49+dfsg-2ubuntu1.10 |  | dpkg-db-cataloger |
| libldap-common | 2.4.49+dfsg-2ubuntu1.10 |  | dpkg-db-cataloger |
| liblsan0 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| liblz4-1 | 1.9.2-2ubuntu0.20.04.1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.2.4-1ubuntu1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblzo2-2 | 2.10-2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmount-dev | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmount1 | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmpc3 | 1.1.0-1 | LGPL-2.1-only | dpkg-db-cataloger |
| libmpdec2 | 2.4.2-3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libmpfr6 | 4.0.2-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libnccl-dev | 2.21.5-1+cuda12.4 | BSD-3-Clause | dpkg-db-cataloger |
| libnccl2 | 2.21.5-1+cuda12.4 | BSD-3-Clause | dpkg-db-cataloger |
| libncurses6 | 6.2-0ubuntu2.1 |  | dpkg-db-cataloger |
| libncursesw5 | 6.2-0ubuntu2.1 |  | dpkg-db-cataloger |
| libncursesw6 | 6.2-0ubuntu2.1 |  | dpkg-db-cataloger |
| libnettle7 | 3.5.1+really3.5.1-2ubuntu0.2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnpp-12-4 | 12.2.5.30-1 |  | dpkg-db-cataloger |
| libnpp-dev-12-4 | 12.2.5.30-1 |  | dpkg-db-cataloger |
| libnpth0 | 1.6-1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnvfatbin-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| libnvfatbin-dev-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| libnvjitlink-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| libnvjitlink-dev-12-4 | 12.4.127-1 |  | dpkg-db-cataloger |
| libnvjpeg-12-4 | 12.3.1.117-1 |  | dpkg-db-cataloger |
| libnvjpeg-dev-12-4 | 12.3.1.117-1 |  | dpkg-db-cataloger |
| libp11-kit0 | 0.23.20-1ubuntu0.1 | BSD-3-Clause, ISC | dpkg-db-cataloger |
| libpam-modules | 1.3.1-5ubuntu4.7 |  | dpkg-db-cataloger |
| libpam-modules-bin | 1.3.1-5ubuntu4.7 |  | dpkg-db-cataloger |
| libpam-runtime | 1.3.1-5ubuntu4.7 |  | dpkg-db-cataloger |
| libpam0g | 1.3.1-5ubuntu4.7 |  | dpkg-db-cataloger |
| libpcre16-3 | 2:8.39-12ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre2-16-0 | 10.34-7ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre2-32-0 | 10.34-7ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre2-8-0 | 10.34-7ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre2-dev | 10.34-7ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre2-posix2 | 10.34-7ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre3 | 2:8.39-12ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre3-dev | 2:8.39-12ubuntu0.1 |  | dpkg-db-cataloger |
| libpcre32-3 | 2:8.39-12ubuntu0.1 |  | dpkg-db-cataloger |
| libpcrecpp0v5 | 2:8.39-12ubuntu0.1 |  | dpkg-db-cataloger |
| libperl5.30 | 5.30.0-9ubuntu0.5 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| libpixman-1-0 | 0.38.4-0ubuntu2.1 |  | dpkg-db-cataloger |
| libpixman-1-dev | 0.38.4-0ubuntu2.1 |  | dpkg-db-cataloger |
| libpng-dev | 1.6.37-2 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpng16-16 | 1.6.37-2 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libprocps8 | 2:3.3.16-1ubuntu2.4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpthread-stubs0-dev | 0.4-1 |  | dpkg-db-cataloger |
| libpython3-stdlib | 3.8.2-0ubuntu2 |  | dpkg-db-cataloger |
| libpython3.8 | 3.8.10-0ubuntu1~20.04.18 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.8-dev | 3.8.10-0ubuntu1~20.04.18 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.8-minimal | 3.8.10-0ubuntu1~20.04.18 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.8-stdlib | 3.8.10-0ubuntu1~20.04.18 | GPL-2.0-only | dpkg-db-cataloger |
| libquadmath0 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libreadline8 | 8.0-4 | GPL-3.0-only | dpkg-db-cataloger |
| libretranslate | 1.7.2 | AGPL-3.0-only | python-installed-package-cataloger |
| libroken18-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsasl2-2 | 2.1.27+dfsg-2ubuntu0.1 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.27+dfsg-2ubuntu0.1 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libseccomp2 | 2.5.1-1ubuntu1~20.04.2 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.0-1build2 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1-dev | 3.0-1build2 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.0-1build2 |  | dpkg-db-cataloger |
| libsemanage1 | 3.0-1build2 |  | dpkg-db-cataloger |
| libsepol1 | 3.0-1ubuntu0.1 |  | dpkg-db-cataloger |
| libsepol1-dev | 3.0-1ubuntu0.1 |  | dpkg-db-cataloger |
| libsm-dev | 2:1.2.3-1 |  | dpkg-db-cataloger |
| libsm6 | 2:1.2.3-1 |  | dpkg-db-cataloger |
| libsmartcols1 | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.31.1-4ubuntu0.7 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.45.5-2ubuntu1.2 |  | dpkg-db-cataloger |
| libssl1.1 | 1.1.1f-1ubuntu2.24 | OpenSSL | dpkg-db-cataloger |
| libstdc++-9-dev | 9.4.0-1ubuntu1~20.04.2 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libstdc++6 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 245.4-4ubuntu3.24 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.16.0-2ubuntu0.1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtinfo5 | 6.2-0ubuntu2.1 |  | dpkg-db-cataloger |
| libtinfo6 | 6.2-0ubuntu2.1 |  | dpkg-db-cataloger |
| libtsan0 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libubsan1 | 10.5.0-1ubuntu1~20.04 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libudev1 | 245.4-4ubuntu3.24 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 0.9.10-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libwind0-heimdal | 7.7.0+dfsg-1ubuntu1.4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libx11-6 | 2:1.6.9-2ubuntu1.6 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.6.9-2ubuntu1.6 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-dev | 2:1.6.9-2ubuntu1.6 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libxau-dev | 1:1.0.9-0ubuntu1 |  | dpkg-db-cataloger |
| libxau6 | 1:1.0.9-0ubuntu1 |  | dpkg-db-cataloger |
| libxcb-render0 | 1.14-2 |  | dpkg-db-cataloger |
| libxcb-render0-dev | 1.14-2 |  | dpkg-db-cataloger |
| libxcb-shm0 | 1.14-2 |  | dpkg-db-cataloger |
| libxcb-shm0-dev | 1.14-2 |  | dpkg-db-cataloger |
| libxcb1 | 1.14-2 |  | dpkg-db-cataloger |
| libxcb1-dev | 1.14-2 |  | dpkg-db-cataloger |
| libxdmcp-dev | 1:1.1.3-0ubuntu1 |  | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.3-0ubuntu1 |  | dpkg-db-cataloger |
| libxext-dev | 2:1.3.4-0ubuntu1 |  | dpkg-db-cataloger |
| libxext6 | 2:1.3.4-0ubuntu1 |  | dpkg-db-cataloger |
| libxrender-dev | 1:0.9.10-1 | HPND-sell-variant | dpkg-db-cataloger |
| libxrender1 | 1:0.9.10-1 | HPND-sell-variant | dpkg-db-cataloger |
| libzstd1 | 1.4.4+dfsg-3ubuntu0.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Zlib | dpkg-db-cataloger |
| limits | 3.13.0 | MIT | python-installed-package-cataloger |
| linux-libc-dev | 5.4.0-216.236 | GPL-2.0-only | dpkg-db-cataloger |
| login | 1:4.8.1-1ubuntu5.20.04.5 | GPL-2.0-only | dpkg-db-cataloger |
| logsave | 1.45.5-2ubuntu1.2 | GPL-2.0-only, LGPL-2.0-only | dpkg-db-cataloger |
| lsb-base | 11.1.0ubuntu2 | BSD-3-Clause, GPL-2.0-only | dpkg-db-cataloger |
| lxml | 6.0.0 | BSD-3-Clause | python-installed-package-cataloger |
| make | 4.2.1-1.2 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| markupsafe | 2.1.5 | BSD-3-Clause | python-installed-package-cataloger |
| mawk | 1.3.4.20200120-2 | GPL-2.0-only | dpkg-db-cataloger |
| mime-support | 3.64ubuntu1 |  | dpkg-db-cataloger |
| more-itertools | 10.3.0 | MIT | python-installed-package-cataloger |
| morfessor | 2.0.6 |  | python-installed-package-cataloger |
| mount | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| mpmath | 1.3.0 |  | python-installed-package-cataloger |
| my-test-package | 1.0 |  | python-installed-package-cataloger |
| ncurses-base | 6.2-0ubuntu2.1 |  | dpkg-db-cataloger |
| ncurses-bin | 6.2-0ubuntu2.1 |  | dpkg-db-cataloger |
| networkx | 3.1 | BSD-3-Clause | python-installed-package-cataloger |
| nsight-compute-2024.1.1 | 2024.1.1.4-1 |  | dpkg-db-cataloger |
| numpy | 1.24.4 | BSD-3-Clause | python-installed-package-cataloger |
| nvidia-cublas-cu12 | 12.1.3.1 |  | python-installed-package-cataloger |
| nvidia-cuda-cupti-cu12 | 12.1.105 |  | python-installed-package-cataloger |
| nvidia-cuda-nvrtc-cu12 | 12.1.105 |  | python-installed-package-cataloger |
| nvidia-cuda-runtime-cu12 | 12.1.105 |  | python-installed-package-cataloger |
| nvidia-cudnn-cu12 | 8.9.2.26 |  | python-installed-package-cataloger |
| nvidia-cufft-cu12 | 11.0.2.54 |  | python-installed-package-cataloger |
| nvidia-curand-cu12 | 10.3.2.106 |  | python-installed-package-cataloger |
| nvidia-cusolver-cu12 | 11.4.5.107 |  | python-installed-package-cataloger |
| nvidia-cusparse-cu12 | 12.1.0.106 |  | python-installed-package-cataloger |
| nvidia-nccl-cu12 | 2.19.3 |  | python-installed-package-cataloger |
| nvidia-nvjitlink-cu12 | 12.9.86 | LicenseRef-NVIDIA-Proprietary | python-installed-package-cataloger |
| nvidia-nvtx-cu12 | 12.1.105 |  | python-installed-package-cataloger |
| openssl | 1.1.1f-1ubuntu2.24 | OpenSSL | dpkg-db-cataloger |
| packaging | 23.1 | Apache-2.0, BSD-2-Clause | python-installed-package-cataloger |
| packaging | 24.1 | Apache-2.0, BSD-2-Clause | python-installed-package-cataloger |
| packaging | 25.0 |  | python-installed-package-cataloger |
| passwd | 1:4.8.1-1ubuntu5.20.04.5 | GPL-2.0-only | dpkg-db-cataloger |
| patch | 2.7.6-6 |  | dpkg-db-cataloger |
| perl | 5.30.0-9ubuntu0.5 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-base | 5.30.0-9ubuntu0.5 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-modules-5.30 | 5.30.0-9ubuntu0.5 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pinentry-curses | 1.1.0-3build1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| pip | 25.0.1 | MIT | python-installed-package-cataloger |
| pkg-config | 0.29.1-0ubuntu4 |  | dpkg-db-cataloger |
| platformdirs | 4.2.2 | MIT | python-installed-package-cataloger |
| polib | 1.1.1 | MIT | python-installed-package-cataloger |
| procps | 2:3.3.16-1ubuntu2.4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| prometheus-client | 0.15.0 |  | python-installed-package-cataloger |
| protobuf | 5.29.5 |  | python-installed-package-cataloger |
| pygments | 2.19.2 | BSD-2-Clause | python-installed-package-cataloger |
| pysrt | 1.1.2 |  | python-installed-package-cataloger |
| python-pip-whl | 20.0.2-5ubuntu1.11 |  | dpkg-db-cataloger |
| python3 | 3.8.2-0ubuntu2 |  | dpkg-db-cataloger |
| python3-distutils | 3.8.10-0ubuntu1~20.04 |  | dpkg-db-cataloger |
| python3-lib2to3 | 3.8.10-0ubuntu1~20.04 |  | dpkg-db-cataloger |
| python3-minimal | 3.8.2-0ubuntu2 |  | dpkg-db-cataloger |
| python3-pkg-resources | 45.2.0-1ubuntu0.3 |  | dpkg-db-cataloger |
| python3-setuptools | 45.2.0-1ubuntu0.3 |  | dpkg-db-cataloger |
| python3-wheel | 0.34.2-1ubuntu0.1 | GPL-3.0-only | dpkg-db-cataloger |
| python3.8 | 3.8.10-0ubuntu1~20.04.18 | GPL-2.0-only | dpkg-db-cataloger |
| python3.8-dev | 3.8.10-0ubuntu1~20.04.18 | GPL-2.0-only | dpkg-db-cataloger |
| python3.8-minimal | 3.8.10-0ubuntu1~20.04.18 | GPL-2.0-only | dpkg-db-cataloger |
| pytz | 2025.2 | MIT | python-installed-package-cataloger |
| pyyaml | 6.0.2 | MIT | python-installed-package-cataloger |
| readline-common | 8.0-4 | GPL-3.0-only | dpkg-db-cataloger |
| redis | 4.4.4 | MIT | python-installed-package-cataloger |
| regex | 2024.11.6 |  | python-installed-package-cataloger |
| requests | 2.31.0 |  | python-installed-package-cataloger |
| rich | 12.6.0 | MIT | python-installed-package-cataloger |
| sacremoses | 0.0.53 |  | python-installed-package-cataloger |
| sed | 4.7-1 | GPL-3.0-only | dpkg-db-cataloger |
| sensible-utils | 0.0.12+nmu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| sentencepiece | 0.2.0 |  | python-installed-package-cataloger |
| setuptools | 45.2.0 |  | python-installed-package-cataloger |
| setuptools | 75.3.2 | MIT | python-installed-package-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| soupsieve | 2.7 | MIT | python-installed-package-cataloger |
| stanza | 1.1.1 |  | python-installed-package-cataloger |
| sympy | 1.13.3 |  | python-installed-package-cataloger |
| sysvinit-utils | 2.96-2.1ubuntu1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| tar | 1.30+dfsg-7ubuntu0.20.04.4 | GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tomli | 2.0.1 | MIT | python-installed-package-cataloger |
| torch | 2.2.0 |  | python-installed-package-cataloger |
| tqdm | 4.67.1 | MPL-2.0 AND MIT | python-installed-package-cataloger |
| translatehtml | 1.5.2 |  | python-installed-package-cataloger |
| triton | 2.2.0 |  | python-installed-package-cataloger |
| typeguard | 4.3.0 | MIT | python-installed-package-cataloger |
| typing-extensions | 4.12.2 |  | python-installed-package-cataloger |
| typing-extensions | 4.13.2 | PSF-2.0 | python-installed-package-cataloger |
| tzdata | 2025b-0ubuntu0.20.04.1 | ICU | dpkg-db-cataloger |
| tzlocal | 5.2 | MIT | python-installed-package-cataloger |
| ubuntu-keyring | 2020.02.11.4 |  | dpkg-db-cataloger |
| ucf | 3.0038+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| urllib3 | 2.2.3 |  | python-installed-package-cataloger |
| util-linux | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uuid-dev | 2.34-0.1ubuntu9.6 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| waitress | 2.1.2 |  | python-installed-package-cataloger |
| werkzeug | 2.3.8 | BSD-3-Clause | python-installed-package-cataloger |
| wheel | 0.34.2 | MIT | python-installed-package-cataloger |
| wheel | 0.43.0 | MIT | python-installed-package-cataloger |
| wrapt | 1.17.2 |  | python-installed-package-cataloger |
| x11-common | 1:7.7+19ubuntu14 |  | dpkg-db-cataloger |
| x11proto-core-dev | 2019.2-1ubuntu1 | MIT | dpkg-db-cataloger |
| x11proto-dev | 2019.2-1ubuntu1 | MIT | dpkg-db-cataloger |
| x11proto-xext-dev | 2019.2-1ubuntu1 | MIT | dpkg-db-cataloger |
| xorg-sgml-doctools | 1:1.11-1 | HPND-sell-variant, MIT | dpkg-db-cataloger |
| xtrans-dev | 1.4.0-1 | HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| xz-utils | 5.2.4-1ubuntu1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| zipp | 3.19.2 | MIT | python-installed-package-cataloger |
| zipp | 3.20.2 | MIT | python-installed-package-cataloger |
| zlib1g | 1:1.2.11.dfsg-2ubuntu1.5 | Zlib | dpkg-db-cataloger |
| zlib1g-dev | 1:1.2.11.dfsg-2ubuntu1.5 | Zlib | dpkg-db-cataloger |
| zope-event | 5.0 | ZPL-2.1 | python-installed-package-cataloger |
| zope-interface | 7.2 |  | python-installed-package-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/open-webui

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| Simple Launcher | 1.1.0.14 |  | pe-binary-package-cataloger |
| accelerate | 1.12.0 |  | python-installed-package-cataloger |
| adduser | 3.134 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| aiocache | 0.12.3 | BSD-3-Clause | python-installed-package-cataloger |
| aiofiles | 25.1.0 | Apache-2.0 | python-installed-package-cataloger |
| aiohappyeyeballs | 2.6.1 | PSF-2.0 | python-installed-package-cataloger |
| aiohttp | 3.13.2 | Apache-2.0 AND MIT | python-installed-package-cataloger |
| aiosignal | 1.4.0 |  | python-installed-package-cataloger |
| alembic | 1.17.2 | MIT | python-installed-package-cataloger |
| annotated-doc | 0.0.4 | MIT | python-installed-package-cataloger |
| annotated-types | 0.7.0 |  | python-installed-package-cataloger |
| anthropic | 0.75.0 | MIT | python-installed-package-cataloger |
| anyio | 4.12.0 | MIT | python-installed-package-cataloger |
| apscheduler | 3.11.1 | MIT | python-installed-package-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| argon2-cffi | 25.1.0 | MIT | python-installed-package-cataloger |
| argon2-cffi-bindings | 25.1.0 | MIT | python-installed-package-cataloger |
| asgiref | 3.11.0 | BSD-3-Clause | python-installed-package-cataloger |
| async-timeout | 5.0.1 |  | python-installed-package-cataloger |
| attrs | 25.4.0 | MIT | python-installed-package-cataloger |
| authlib | 1.6.6 | BSD-3-Clause | python-installed-package-cataloger |
| autocommand | 2.2.2 |  | python-installed-package-cataloger |
| av | 14.0.1 |  | python-installed-package-cataloger |
| azure-ai-documentintelligence | 1.0.2 |  | python-installed-package-cataloger |
| azure-common | 1.1.28 |  | python-installed-package-cataloger |
| azure-core | 1.37.0 |  | python-installed-package-cataloger |
| azure-identity | 1.25.1 | MIT | python-installed-package-cataloger |
| azure-search-documents | 11.6.0 |  | python-installed-package-cataloger |
| azure-storage-blob | 12.27.1 |  | python-installed-package-cataloger |
| backoff | 2.2.1 | MIT | python-installed-package-cataloger |
| backports-tarfile | 1.2.0 | MIT | python-installed-package-cataloger |
| base-files | 12.4+deb12u12 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b9 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| bcrypt | 5.0.0 | Apache-2.0 | python-installed-package-cataloger |
| beautifulsoup4 | 4.14.3 |  | python-installed-package-cataloger |
| bidict | 0.23.1 |  | python-installed-package-cataloger |
| binutils | 2.40-2 |  | dpkg-db-cataloger |
| binutils-common | 2.40-2 |  | dpkg-db-cataloger |
| binutils-x86-64-linux-gnu | 2.40-2 |  | dpkg-db-cataloger |
| bitarray | 3.8.0 | PSF-2.0 | python-installed-package-cataloger |
| black | 25.12.0 | MIT | python-installed-package-cataloger |
| blinker | 1.9.0 | MIT | python-installed-package-cataloger |
| boto3 | 1.42.14 | Apache-2.0 | python-installed-package-cataloger |
| botocore | 1.42.14 | Apache-2.0 | python-installed-package-cataloger |
| brotli | 1.2.0 | MIT | python-installed-package-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| build | 1.3.0 | MIT | python-installed-package-cataloger |
| build-essential | 12.9 |  | dpkg-db-cataloger |
| bzip2 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| ca-certificates | 20230311+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| cachetools | 6.2.4 | MIT | python-installed-package-cataloger |
| certifi | 2025.11.12 | MPL-2.0 | python-installed-package-cataloger |
| cffi | 2.0.0 | MIT | python-installed-package-cataloger |
| chardet | 5.2.0 |  | python-installed-package-cataloger |
| charset-normalizer | 3.4.4 | MIT | python-installed-package-cataloger |
| chromadb | 1.3.7 |  | python-installed-package-cataloger |
| cli | UNKNOWN |  | pe-binary-package-cataloger |
| cli-32 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-64 | UNKNOWN |  | pe-binary-package-cataloger |
| cli-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| click | 8.3.1 | BSD-3-Clause | python-installed-package-cataloger |
| colbert-ai | 0.2.22 |  | python-installed-package-cataloger |
| coloredlogs | 15.0.1 | MIT | python-installed-package-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cpp | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| cpp-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| cryptography | 46.0.3 | Apache-2.0 OR BSD-3-Clause | python-installed-package-cataloger |
| ctranslate2 | 4.6.2 |  | python-installed-package-cataloger |
| curl | 7.88.1-10+deb12u14 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dataclasses-json | 0.6.7 | MIT | python-installed-package-cataloger |
| datasets | 4.0.0 |  | python-installed-package-cataloger |
| ddgs | 9.10.0 | MIT | python-installed-package-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u2 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| defusedxml | 0.7.1 |  | python-installed-package-cataloger |
| deprecation | 2.1.0 |  | python-installed-package-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dill | 0.3.8 | BSD-3-Clause | python-installed-package-cataloger |
| distro | 1.9.0 |  | python-installed-package-cataloger |
| dnspython | 2.8.0 | ISC | python-installed-package-cataloger |
| docker | 7.1.0 | Apache-2.0 | python-installed-package-cataloger |
| docstring-parser | 0.17.0 | MIT | python-installed-package-cataloger |
| docx2txt | 0.9 |  | python-installed-package-cataloger |
| dpkg | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dpkg-dev | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| durationpy | 0.10 | MIT | python-installed-package-cataloger |
| e2fsprogs | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| ecdsa | 0.19.1 | MIT | python-installed-package-cataloger |
| einops | 0.8.1 | MIT | python-installed-package-cataloger |
| elastic-transport | 9.2.0 |  | python-installed-package-cataloger |
| elasticsearch | 9.2.0 | Apache-2.0 | python-installed-package-cataloger |
| emoji | 2.15.0 |  | python-installed-package-cataloger |
| et-xmlfile | 2.0.0 | MIT | python-installed-package-cataloger |
| events | 0.5 |  | python-installed-package-cataloger |
| fake-useragent | 2.2.0 | Apache-2.0 | python-installed-package-cataloger |
| fastapi | 0.126.0 | MIT | python-installed-package-cataloger |
| faster-whisper | 1.2.1 | MIT | python-installed-package-cataloger |
| ffmpeg | 5.1.6 |  | binary-classifier-cataloger |
| ffmpeg | 7.1 |  | binary-classifier-cataloger |
| ffmpeg | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| filelock | 3.20.0 | Unlicense | python-installed-package-cataloger |
| filetype | 1.2.0 | MIT | python-installed-package-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| firecrawl-py | 4.12.0 |  | python-installed-package-cataloger |
| flask | 3.1.2 | BSD-3-Clause | python-installed-package-cataloger |
| flatbuffers | 25.12.19 |  | python-installed-package-cataloger |
| fontconfig | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| fontconfig-config | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-6 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| fonttools | 4.61.1 | MIT | python-installed-package-cataloger |
| fpdf2 | 2.8.5 | LGPL-3.0-only | python-installed-package-cataloger |
| frozenlist | 1.8.0 | Apache-2.0 | python-installed-package-cataloger |
| fsspec | 2025.3.0 | BSD-3-Clause | python-installed-package-cataloger |
| ftfy | 6.3.1 | Apache-2.0 | python-installed-package-cataloger |
| g++ | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| g++-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| gcc-12 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| git | 1:2.39.5-0+deb12u2 | Apache-2.0, BSD-3-Clause, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| git-man | 1:2.39.5-0+deb12u2 | Apache-2.0, BSD-3-Clause, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| gitdb | 4.0.12 |  | python-installed-package-cataloger |
| gitpython | 3.1.45 | BSD-3-Clause | python-installed-package-cataloger |
| google-ai-generativelanguage | 0.6.15 |  | python-installed-package-cataloger |
| google-api-core | 2.28.1 |  | python-installed-package-cataloger |
| google-api-python-client | 2.187.0 |  | python-installed-package-cataloger |
| google-auth | 2.45.0 |  | python-installed-package-cataloger |
| google-auth-httplib2 | 0.3.0 |  | python-installed-package-cataloger |
| google-auth-oauthlib | 1.2.2 |  | python-installed-package-cataloger |
| google-cloud-core | 2.5.0 |  | python-installed-package-cataloger |
| google-cloud-storage | 3.7.0 |  | python-installed-package-cataloger |
| google-crc32c | 1.8.0 |  | python-installed-package-cataloger |
| google-genai | 1.56.0 | Apache-2.0 | python-installed-package-cataloger |
| google-generativeai | 0.8.6 |  | python-installed-package-cataloger |
| google-resumable-media | 2.8.0 |  | python-installed-package-cataloger |
| googleapis-common-protos | 1.72.0 |  | python-installed-package-cataloger |
| gpgv | 2.2.40-1.1+deb12u1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| greenlet | 3.3.0 | MIT AND Python-2.0 | python-installed-package-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| grpcio | 1.76.0 |  | python-installed-package-cataloger |
| grpcio-status | 1.71.2 |  | python-installed-package-cataloger |
| gui | UNKNOWN |  | pe-binary-package-cataloger |
| gui-32 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-64 | UNKNOWN |  | pe-binary-package-cataloger |
| gui-arm64 | UNKNOWN |  | pe-binary-package-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| h11 | 0.16.0 | MIT | python-installed-package-cataloger |
| h2 | 4.3.0 | MIT | python-installed-package-cataloger |
| hf-xet | 1.2.0 | Apache-2.0 | python-installed-package-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| hpack | 4.1.0 | MIT | python-installed-package-cataloger |
| html5lib | 1.1 |  | python-installed-package-cataloger |
| httpcore | 1.0.9 | BSD-3-Clause | python-installed-package-cataloger |
| httplib2 | 0.31.0 | MIT | python-installed-package-cataloger |
| httptools | 0.7.1 | MIT | python-installed-package-cataloger |
| httpx | 0.28.1 | BSD-3-Clause | python-installed-package-cataloger |
| httpx-sse | 0.4.3 | MIT | python-installed-package-cataloger |
| huggingface-hub | 0.36.0 |  | python-installed-package-cataloger |
| humanfriendly | 10.0 | MIT | python-installed-package-cataloger |
| hyperframe | 6.1.0 | MIT | python-installed-package-cataloger |
| idna | 3.11 | BSD-3-Clause | python-installed-package-cataloger |
| importlib-metadata | 8.0.0 | Apache-2.0 | python-installed-package-cataloger |
| importlib-metadata | 8.7.1 | Apache-2.0 | python-installed-package-cataloger |
| importlib-resources | 6.5.2 | Apache-2.0 | python-installed-package-cataloger |
| inflect | 7.3.1 | MIT | python-installed-package-cataloger |
| iniconfig | 2.3.0 | MIT | python-installed-package-cataloger |
| init-system-helpers | 1.65.2+deb12u1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| isodate | 0.7.2 | BSD-3-Clause | python-installed-package-cataloger |
| itsdangerous | 2.2.0 | BSD-3-Clause | python-installed-package-cataloger |
| jaraco-collections | 5.1.0 | MIT | python-installed-package-cataloger |
| jaraco-context | 5.3.0 | MIT | python-installed-package-cataloger |
| jaraco-functools | 4.0.1 | MIT | python-installed-package-cataloger |
| jaraco-text | 3.12.1 | MIT | python-installed-package-cataloger |
| jinja2 | 3.1.6 |  | python-installed-package-cataloger |
| jiter | 0.12.0 |  | python-installed-package-cataloger |
| jmespath | 1.0.1 | MIT | python-installed-package-cataloger |
| joblib | 1.5.3 | BSD-3-Clause | python-installed-package-cataloger |
| jq | 1.6-2.1+deb12u1 | CC-BY-3.0, GPL-2.0-only, GPL-2.0-or-later, MIT | dpkg-db-cataloger |
| jsonpatch | 1.33 |  | python-installed-package-cataloger |
| jsonpointer | 3.0.0 |  | python-installed-package-cataloger |
| jsonschema | 4.25.1 | MIT | python-installed-package-cataloger |
| jsonschema-specifications | 2025.9.1 | MIT | python-installed-package-cataloger |
| kubernetes | 33.1.0 |  | python-installed-package-cataloger |
| langchain | 1.2.0 | MIT | python-installed-package-cataloger |
| langchain-classic | 1.0.0 | MIT | python-installed-package-cataloger |
| langchain-community | 0.4.1 | MIT | python-installed-package-cataloger |
| langchain-core | 1.2.4 | MIT | python-installed-package-cataloger |
| langchain-text-splitters | 1.1.0 | MIT | python-installed-package-cataloger |
| langdetect | 1.0.9 | MIT | python-installed-package-cataloger |
| langgraph | 1.0.5 | MIT | python-installed-package-cataloger |
| langgraph-checkpoint | 3.0.1 | MIT | python-installed-package-cataloger |
| langgraph-prebuilt | 1.0.5 | MIT | python-installed-package-cataloger |
| langgraph-sdk | 0.3.1 | MIT | python-installed-package-cataloger |
| langsmith | 0.5.0 | MIT | python-installed-package-cataloger |
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
| libavcodec59 | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libavdevice59 | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libavfilter8 | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libavformat59 | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libavutil57 | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libbinutils | 2.40-2 |  | dpkg-db-cataloger |
| libblas3 | 3.11.0-2 | BSD-3-Clause | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbluray2 | 1:1.3.4-1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.0 | dpkg-db-cataloger |
| libbrotli1 | 1.0.9-2+b6 | MIT | dpkg-db-cataloger |
| libbs2b0 | 3.1.0+dfsg-7 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libbsd0 | 0.11.7-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC, libutil-David-Nugent | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc-dev-bin | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6-dev | 2.36-9+deb12u13 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcaca0 | 0.99.beta20-3 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libcairo-gobject2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2 | 1.16.0-7 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4+deb12u2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
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
| libdpkg-perl | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
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
| libgcrypt20 | 1.10.1-3 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm-compat4 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdk-pixbuf-2.0-0 | 2.42.10+dfsg-1+deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf2.0-common | 2.42.10+dfsg-1+deb12u2 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgfortran5 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgl1 | 1.6.0-1 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libgl1-mesa-dri | 22.3.6-1+deb12u1 | Apache-2.0, BSD-2-Clause, MIT | dpkg-db-cataloger |
| libglapi-mesa | 22.3.6-1+deb12u1 | Apache-2.0, BSD-2-Clause, MIT | dpkg-db-cataloger |
| libglib2.0-0 | 2.74.6-2+deb12u7 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglvnd0 | 1.6.0-1 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libglx-mesa0 | 22.3.6-1+deb12u1 | Apache-2.0, BSD-2-Clause, MIT | dpkg-db-cataloger |
| libglx0 | 1.6.0-1 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libgme0 | 0.6.3-6 | LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u5 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgprofng0 | 2.40-2 |  | dpkg-db-cataloger |
| libgraphite2-3 | 1.3.14-1 | GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libgsm1 | 1.0.22-1 | TU-Berlin-2.0 | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
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
| libk5crypto3 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.20.1-2+deb12u4 | GPL-2.0-only | dpkg-db-cataloger |
| liblapack3 | 3.11.0-2 | BSD-3-Clause | dpkg-db-cataloger |
| liblcms2-2 | 2.14-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| libldap-2.5-0 | 2.5.13+dfsg-5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| liblerc4 | 4.0.0+ds-2 | Apache-2.0 | dpkg-db-cataloger |
| liblilv-0-0 | 0.24.14-1 | BSD-3-Clause, ISC | dpkg-db-cataloger |
| libllvm15 | 1:15.0.6-4+b1 | Apache-2.0, BSD-3-Clause, BSD-3-Clause, MIT | dpkg-db-cataloger |
| liblsan0 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| liblua5.3-0 | 5.3.6-2 |  | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
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
| libnghttp2-14 | 1.52.0-1+deb12u2 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnorm1 | 1.5.9+dfsg-2 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause-UC | dpkg-db-cataloger |
| libnsl-dev | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnuma1 | 2.0.16-1 |  | dpkg-db-cataloger |
| libogg0 | 1.3.5-3 | BSD-3-Clause | dpkg-db-cataloger |
| libonig5 | 6.9.8-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libopenal-data | 1:1.19.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libopenal1 | 1:1.19.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.0-2+deb12u2 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libopenmpt0 | 0.6.9-1 | BSD-3-Clause, BSL-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, X11 | dpkg-db-cataloger |
| libopus0 | 1.3.1-3 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpango-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangocairo-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpangoft2-1.0-0 | 1.50.12+ds-1 | Apache-2.0, Apache-2.0, Bitstream-Vera, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, ICU, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, OFL-1.1, TCL | dpkg-db-cataloger |
| libpciaccess0 | 0.17-2 |  | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libperl5.36 | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| libpgm-5.3-0 | 5.3.128~dfsg-2 | BSD-3-Clause, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libpixman-1-0 | 0.42.2-1 |  | dpkg-db-cataloger |
| libplacebo208 | 4.208.0-3 | LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libpng16-16 | 1.6.39-2+deb12u1 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpocketsphinx3 | 0.8+5prealpha+1-15 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libpostproc56 | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libpsl5 | 0.21.2-1 | MIT | dpkg-db-cataloger |
| libpulse0 | 16.1+dfsg1-2+b1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpython3-dev | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| libpython3-stdlib | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| libpython3.11 | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-dev | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-minimal | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-stdlib | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
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
| libsodium23 | 1.0.18-1 | BSD-2-Clause, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libsord-0-0 | 0.16.14+git221008-1 | ISC | dpkg-db-cataloger |
| libsoxr0 | 0.1.3-4 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libspeex1 | 1.2.1-2 | BSD-3-Clause, GFDL-1.1-or-later, GFDL-1.2-only, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libsphinxbase3 | 0.8+5prealpha+1-16 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2+deb12u2 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libsratom-0-0 | 0.6.14-1 | ISC | dpkg-db-cataloger |
| libsrt1.5-gnutls | 1.5.1-1+deb12u1 | BSD-3-Clause, LGPL-2.1-only, LGPL-2.1-or-later, MPL-2.0, Zlib, Unlicense | dpkg-db-cataloger |
| libss2 | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssh-gcrypt-4 | 0.10.6-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, LGPL-2.1-only | dpkg-db-cataloger |
| libssh2-1 | 1.10.0-3+b1 |  | dpkg-db-cataloger |
| libssl3 | 3.0.17-1~deb12u3 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++-12-dev | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsvtav1enc1 | 1.4.1+dfsg-1 | BSD-2-Clause, BSD-3-Clause-Clear, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libswresample4 | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libswscale6 | 7:5.1.8-0+deb12u1 | BSD-1-Clause, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, IJG, ISC, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsystemd0 | 252.39-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2+deb12u1 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libthai-data | 0.1.29-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libthai0 | 0.1.29-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtheora0 | 1.1.1+dfsg.1-16.1+deb12u1 | BSD-3-Clause | dpkg-db-cataloger |
| libtiff6 | 4.5.0-6+deb12u3 |  | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc-dev | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtsan2 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libtwolame0 | 0.4.0-2 | LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libubsan1 | 12.2.0-14+deb12u1 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libudev1 | 252.39-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
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
| libvpx7 | 1.12.0-1+deb12u4 | BSD-3-Clause, ISC | dpkg-db-cataloger |
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
| libxml2 | 2.9.14+dfsg-1.3~deb12u4 | ISC | dpkg-db-cataloger |
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
| libzvbi-common | 0.2.41-1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libzvbi0 | 0.2.41-1 | BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| linux-libc-dev | 6.1.158-1 | BSD-2-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+deb12u1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2+b2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| loguru | 0.7.3 |  | python-installed-package-cataloger |
| lxml | 6.0.2 | BSD-3-Clause | python-installed-package-cataloger |
| make | 4.3-4.1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| mako | 1.3.10 | MIT | python-installed-package-cataloger |
| markdown | 3.10 | BSD-3-Clause | python-installed-package-cataloger |
| markdown-it-py | 4.0.0 |  | python-installed-package-cataloger |
| markupsafe | 2.1.5 | BSD-3-Clause | python-installed-package-cataloger |
| marshmallow | 3.26.1 | MIT | python-installed-package-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| mcp | 1.25.0 | MIT | python-installed-package-cataloger |
| mdurl | 0.1.2 | MIT | python-installed-package-cataloger |
| media-types | 10.0.0 |  | dpkg-db-cataloger |
| mmh3 | 5.2.0 | MIT | python-installed-package-cataloger |
| more-itertools | 10.3.0 | MIT | python-installed-package-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| mpmath | 1.3.0 |  | python-installed-package-cataloger |
| msal | 1.34.0 | MIT | python-installed-package-cataloger |
| msal-extensions | 1.3.1 |  | python-installed-package-cataloger |
| msoffcrypto-tool | 5.4.2 | MIT | python-installed-package-cataloger |
| multidict | 6.7.0 |  | python-installed-package-cataloger |
| multiprocess | 0.70.16 | BSD-3-Clause | python-installed-package-cataloger |
| mypy-extensions | 1.1.0 | MIT | python-installed-package-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| nest-asyncio | 1.6.0 |  | python-installed-package-cataloger |
| netbase | 6.4 | GPL-2.0-only | dpkg-db-cataloger |
| netcat-openbsd | 1.219-1 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| networkx | 3.6.1 | BSD-3-Clause | python-installed-package-cataloger |
| ninja | 1.13.0 |  | python-installed-package-cataloger |
| nltk | 3.9.2 |  | python-installed-package-cataloger |
| node | 24.11.1 |  | binary-classifier-cataloger |
| numpy | 2.2.6 | BSD-3-Clause | python-installed-package-cataloger |
| oauthlib | 3.3.1 | BSD-3-Clause | python-installed-package-cataloger |
| ocl-icd-libopencl1 | 2.3.1-1 | BSD-2-Clause | dpkg-db-cataloger |
| olefile | 0.47 |  | python-installed-package-cataloger |
| onnxruntime | 1.23.2 |  | python-installed-package-cataloger |
| open-webui | 0.6.43 |  | javascript-package-cataloger |
| openai | 2.14.0 | Apache-2.0 | python-installed-package-cataloger |
| opencv-python | 4.12.0.88 |  | python-installed-package-cataloger |
| opencv-python-headless | 4.12.0.88 |  | python-installed-package-cataloger |
| openpyxl | 3.1.5 | MIT | python-installed-package-cataloger |
| opensearch-protobufs | 0.19.0 | Apache-2.0 | python-installed-package-cataloger |
| opensearch-py | 3.1.0 | Apache-2.0 | python-installed-package-cataloger |
| openssl | 3.0.17-1~deb12u3 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| opentelemetry-api | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-otlp | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-otlp-proto-common | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-otlp-proto-grpc | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-exporter-otlp-proto-http | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-aiohttp-client | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-asgi | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-fastapi | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-httpx | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-logging | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-redis | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-requests | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-instrumentation-sqlalchemy | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-proto | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-sdk | 1.39.1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-semantic-conventions | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| opentelemetry-util-http | 0.60b1 | Apache-2.0 | python-installed-package-cataloger |
| oracledb | 3.4.1 | UPL-1.0 OR Apache-2.0 | python-installed-package-cataloger |
| orjson | 3.11.5 | Apache-2.0 OR MIT | python-installed-package-cataloger |
| ormsgpack | 1.12.1 | Apache-2.0 OR MIT | python-installed-package-cataloger |
| overrides | 7.7.0 |  | python-installed-package-cataloger |
| packaging | 24.2 | Apache-2.0, BSD-2-Clause | python-installed-package-cataloger |
| packaging | 25.0 |  | python-installed-package-cataloger |
| pandas | 2.3.3 |  | python-installed-package-cataloger |
| pandoc | 2.17.1.1-2~deb12u1 | CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MS-RL | dpkg-db-cataloger |
| pandoc-data | 2.17.1.1-2~deb12u1 | CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MS-RL | dpkg-db-cataloger |
| passwd | 1:4.13+dfsg1-1+deb12u1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.7.6-7 |  | dpkg-db-cataloger |
| pathspec | 0.12.1 | MPL-2.0 | python-installed-package-cataloger |
| peewee | 3.18.3 |  | python-installed-package-cataloger |
| peewee-migrate | 1.14.3 | MIT | python-installed-package-cataloger |
| perl | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-modules-5.36 | 5.36.0-7+deb12u3 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| pgvector | 0.4.2 | MIT | python-installed-package-cataloger |
| pillow | 12.0.0 | MIT-CMU | python-installed-package-cataloger |
| pinecone | 6.0.2 | Apache-2.0 | python-installed-package-cataloger |
| pinecone-plugin-interface | 0.0.7 | Apache-2.0 | python-installed-package-cataloger |
| pip | 24.0 | MIT | python-installed-package-cataloger |
| platformdirs | 4.2.2 | MIT | python-installed-package-cataloger |
| platformdirs | 4.5.1 | MIT | python-installed-package-cataloger |
| playwright | 1.57.0 | Apache-2.0 | python-installed-package-cataloger |
| playwright-core | 1.57.0-beta-1764944708000 | Apache-2.0 | javascript-package-cataloger |
| pluggy | 1.6.0 | MIT | python-installed-package-cataloger |
| portalocker | 3.2.0 | BSD-3-Clause | python-installed-package-cataloger |
| posthog | 5.4.0 | MIT | python-installed-package-cataloger |
| primp | 0.15.0 |  | python-installed-package-cataloger |
| propcache | 0.4.1 | Apache-2.0 | python-installed-package-cataloger |
| proto-plus | 1.27.0 |  | python-installed-package-cataloger |
| protobuf | 5.29.5 |  | python-installed-package-cataloger |
| psutil | 7.1.3 | BSD-3-Clause | python-installed-package-cataloger |
| psycopg2-binary | 2.9.11 |  | python-installed-package-cataloger |
| pyarrow | 20.0.0 |  | python-installed-package-cataloger |
| pyasn1 | 0.6.1 | BSD-2-Clause | python-installed-package-cataloger |
| pyasn1-modules | 0.4.2 |  | python-installed-package-cataloger |
| pybase64 | 1.4.3 | BSD-2-Clause | python-installed-package-cataloger |
| pyclipper | 1.4.0 | MIT | python-installed-package-cataloger |
| pycparser | 2.23 | BSD-3-Clause | python-installed-package-cataloger |
| pycrdt | 0.12.44 |  | python-installed-package-cataloger |
| pydantic | 2.12.5 | MIT | python-installed-package-cataloger |
| pydantic-core | 2.41.5 | MIT | python-installed-package-cataloger |
| pydantic-settings | 2.12.0 | MIT | python-installed-package-cataloger |
| pydub | 0.25.1 | MIT | python-installed-package-cataloger |
| pyee | 13.0.0 | MIT | python-installed-package-cataloger |
| pygments | 2.19.2 | BSD-2-Clause | python-installed-package-cataloger |
| pyjwt | 2.10.1 | MIT | python-installed-package-cataloger |
| pymdown-extensions | 10.19.1 | MIT | python-installed-package-cataloger |
| pymilvus | 2.6.5 |  | python-installed-package-cataloger |
| pymongo | 4.15.5 | Apache-2.0 | python-installed-package-cataloger |
| pymysql | 1.1.2 | MIT | python-installed-package-cataloger |
| pyodide | 0.28.2 | MPL-2.0 | javascript-package-cataloger |
| pypandoc | 1.16.2 | MIT | python-installed-package-cataloger |
| pyparsing | 3.2.5 | MIT | python-installed-package-cataloger |
| pypdf | 6.5.0 | BSD-3-Clause | python-installed-package-cataloger |
| pypika | 0.48.9 |  | python-installed-package-cataloger |
| pyproject-hooks | 1.2.0 | MIT | python-installed-package-cataloger |
| pytest | 8.4.2 | MIT | python-installed-package-cataloger |
| pytest-docker | 3.2.5 | MIT | python-installed-package-cataloger |
| python | 3.11.14 |  | binary-classifier-cataloger |
| python-dateutil | 2.9.0.post0 |  | python-installed-package-cataloger |
| python-dotenv | 1.2.1 | BSD-3-Clause | python-installed-package-cataloger |
| python-engineio | 4.12.3 | MIT | python-installed-package-cataloger |
| python-iso639 | 2025.11.16 |  | python-installed-package-cataloger |
| python-jose | 3.5.0 | MIT | python-installed-package-cataloger |
| python-magic | 0.4.27 | MIT | python-installed-package-cataloger |
| python-mimeparse | 2.0.0 | MIT | python-installed-package-cataloger |
| python-multipart | 0.0.21 | Apache-2.0 | python-installed-package-cataloger |
| python-oxmsg | 0.0.2 | MIT | python-installed-package-cataloger |
| python-pptx | 1.0.2 | MIT | python-installed-package-cataloger |
| python-socketio | 5.15.1 | MIT | python-installed-package-cataloger |
| python3 | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3-dev | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3-distutils | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-lib2to3 | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-minimal | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3.11 | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| python3.11-dev | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| python3.11-minimal | 3.11.2-6+deb12u6 | GPL-2.0-only | dpkg-db-cataloger |
| pytokens | 0.3.0 | MIT | python-installed-package-cataloger |
| pytube | 15.0.0 |  | python-installed-package-cataloger |
| pytz | 2025.2 | MIT | python-installed-package-cataloger |
| pyxlsb | 1.0.10 |  | python-installed-package-cataloger |
| pyyaml | 6.0.3 | MIT | python-installed-package-cataloger |
| qdrant-client | 1.16.2 | Apache-2.0 | python-installed-package-cataloger |
| rank-bm25 | 0.2.2 | Apache-2.0 | python-installed-package-cataloger |
| rapidfuzz | 3.14.3 | MIT | python-installed-package-cataloger |
| rapidocr-onnxruntime | 1.4.4 | Apache-2.0 | python-installed-package-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| redis | 7.1.0 | MIT | python-installed-package-cataloger |
| referencing | 0.37.0 | MIT | python-installed-package-cataloger |
| regex | 2025.11.3 | Apache-2.0 AND CNRI-Python | python-installed-package-cataloger |
| requests | 2.32.5 | Apache-2.0 | python-installed-package-cataloger |
| requests-oauthlib | 2.0.0 | ISC | python-installed-package-cataloger |
| requests-toolbelt | 1.0.0 |  | python-installed-package-cataloger |
| restrictedpython | 8.1 | ZPL-2.1 | python-installed-package-cataloger |
| rich | 13.9.4 | MIT | python-installed-package-cataloger |
| rpcsvc-proto | 1.4.3-1 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, MIT | dpkg-db-cataloger |
| rpds-py | 0.30.0 | MIT | python-installed-package-cataloger |
| rsa | 4.9.1 | Apache-2.0 | python-installed-package-cataloger |
| s3transfer | 0.16.0 |  | python-installed-package-cataloger |
| safetensors | 0.7.0 |  | python-installed-package-cataloger |
| scikit-learn | 1.8.0 | BSD-3-Clause | python-installed-package-cataloger |
| scipy | 1.16.3 | BSD-3-Clause | python-installed-package-cataloger |
| sed | 4.9-1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sentence-transformers | 5.2.0 |  | python-installed-package-cataloger |
| sentencepiece | 0.2.1 |  | python-installed-package-cataloger |
| setuptools | 79.0.1 |  | python-installed-package-cataloger |
| shapely | 2.1.2 |  | python-installed-package-cataloger |
| shared-mime-info | 2.2-1 |  | dpkg-db-cataloger |
| shellingham | 1.5.4 |  | python-installed-package-cataloger |
| simple-websocket | 1.1.0 | MIT | python-installed-package-cataloger |
| six | 1.17.0 | MIT | python-installed-package-cataloger |
| smmap | 5.0.2 | BSD-3-Clause | python-installed-package-cataloger |
| sniffio | 1.3.1 | MIT OR Apache-2.0 | python-installed-package-cataloger |
| socksio | 1.0.0 |  | python-installed-package-cataloger |
| soundfile | 0.13.1 |  | python-installed-package-cataloger |
| soupsieve | 2.8.1 | MIT | python-installed-package-cataloger |
| sqlalchemy | 2.0.45 | MIT | python-installed-package-cataloger |
| sse-starlette | 3.0.4 | BSD-3-Clause | python-installed-package-cataloger |
| starlette | 0.50.0 | BSD-3-Clause | python-installed-package-cataloger |
| starlette-compress | 1.6.1 | 0BSD | python-installed-package-cataloger |
| starsessions | 2.2.1 | MIT | python-installed-package-cataloger |
| sympy | 1.14.0 |  | python-installed-package-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tenacity | 9.1.2 |  | python-installed-package-cataloger |
| threadpoolctl | 3.6.0 | BSD-3-Clause | python-installed-package-cataloger |
| tiktoken | 0.12.0 | MIT | python-installed-package-cataloger |
| tokenizers | 0.22.1 |  | python-installed-package-cataloger |
| tomli | 2.0.1 | MIT | python-installed-package-cataloger |
| torch | 2.9.1+cpu | BSD-3-Clause | python-installed-package-cataloger |
| torchaudio | 2.9.1+cpu |  | python-installed-package-cataloger |
| torchvision | 0.24.1+cpu |  | python-installed-package-cataloger |
| tqdm | 4.67.1 | MPL-2.0 AND MIT | python-installed-package-cataloger |
| transformers | 4.57.3 |  | python-installed-package-cataloger |
| typeguard | 4.3.0 | MIT | python-installed-package-cataloger |
| typer | 0.20.1 | MIT | python-installed-package-cataloger |
| typing-extensions | 4.12.2 |  | python-installed-package-cataloger |
| typing-extensions | 4.15.0 | PSF-2.0 | python-installed-package-cataloger |
| typing-inspect | 0.9.0 | MIT | python-installed-package-cataloger |
| typing-inspection | 0.4.2 | MIT | python-installed-package-cataloger |
| tzdata | 2025.3 | Apache-2.0 | python-installed-package-cataloger |
| tzdata | 2025b-0+deb12u2 |  | dpkg-db-cataloger |
| tzlocal | 5.3.1 | MIT | python-installed-package-cataloger |
| ujson | 5.11.0 |  | python-installed-package-cataloger |
| unstructured | 0.18.21 | Apache-2.0 | python-installed-package-cataloger |
| unstructured-client | 0.42.6 | MIT | python-installed-package-cataloger |
| uritemplate | 4.2.0 |  | python-installed-package-cataloger |
| urllib3 | 2.6.2 | MIT | python-installed-package-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uuid-utils | 0.12.0 |  | python-installed-package-cataloger |
| uv | 0.9.18 |  | python-installed-package-cataloger |
| uvicorn | 0.37.0 | BSD-3-Clause | python-installed-package-cataloger |
| uvloop | 0.22.1 |  | python-installed-package-cataloger |
| validators | 0.35.0 | MIT | python-installed-package-cataloger |
| watchfiles | 1.1.1 | MIT | python-installed-package-cataloger |
| wcwidth | 0.2.14 | MIT | python-installed-package-cataloger |
| weaviate-client | 4.19.0 |  | python-installed-package-cataloger |
| webencodings | 0.5.1 |  | python-installed-package-cataloger |
| websocket-client | 1.9.0 | Apache-2.0 | python-installed-package-cataloger |
| websockets | 15.0.1 | BSD-3-Clause | python-installed-package-cataloger |
| werkzeug | 3.1.4 | BSD-3-Clause | python-installed-package-cataloger |
| wheel | 0.45.1 | MIT | python-installed-package-cataloger |
| wheel | 0.45.1 | MIT | python-installed-package-cataloger |
| wrapt | 1.17.3 |  | python-installed-package-cataloger |
| wsproto | 1.3.2 | MIT | python-installed-package-cataloger |
| x11-common | 1:7.7+23 |  | dpkg-db-cataloger |
| xkb-data | 2.35.1-1 |  | dpkg-db-cataloger |
| xlrd | 2.0.2 |  | python-installed-package-cataloger |
| xlsxwriter | 3.2.9 | BSD-2-Clause | python-installed-package-cataloger |
| xxhash | 3.6.0 |  | python-installed-package-cataloger |
| xz-utils | 5.4.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| yarl | 1.22.0 | Apache-2.0 | python-installed-package-cataloger |
| youtube-transcript-api | 1.2.3 | MIT | python-installed-package-cataloger |
| zipp | 3.19.2 | MIT | python-installed-package-cataloger |
| zipp | 3.23.0 | MIT | python-installed-package-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zlib1g-dev | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zstandard | 0.25.0 | BSD-3-Clause | python-installed-package-cataloger |

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
| Archive_Tar | 1.4.14 |  | php-pear-serialized-cataloger |
| Console_Getopt | 1.4.3 | BSD-2-Clause | php-pear-serialized-cataloger |
| PEAR | 1.10.15 |  | php-pear-serialized-cataloger |
| Structures_Graph | 1.1.1 |  | php-pear-serialized-cataloger |
| XML_Util | 1.4.5 |  | php-pear-serialized-cataloger |
| adduser | 3.134 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| apache2 | 2.4.62-1~deb12u2 | Apache-2.0, BSD-2-Clause-Darwin, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| apache2-bin | 2.4.62-1~deb12u2 | Apache-2.0, BSD-2-Clause-Darwin, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| apache2-data | 2.4.62-1~deb12u2 | Apache-2.0, BSD-2-Clause-Darwin, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| apache2-utils | 2.4.62-1~deb12u2 | Apache-2.0, BSD-2-Clause-Darwin, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| apt | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| aspell | 0.60.8-4+b1 | GFDL-1.2-only, GFDL-1.2-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| aspell-en | 2020.12.07-0-1 |  | dpkg-db-cataloger |
| autoconf | 2.71-3 | GFDL-1.3-only, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| bacon/bacon-qr-code | 2.0.8 | BSD-2-Clause | php-composer-installed-cataloger |
| bacon/bacon-qr-code | 2.0.8 | BSD-2-Clause | php-composer-installed-cataloger |
| base-files | 12.4+deb12u9 |  | dpkg-db-cataloger |
| base-passwd | 3.6.1 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.15-2+b7 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| binutils | 2.40-2 |  | dpkg-db-cataloger |
| binutils-common | 2.40-2 |  | dpkg-db-cataloger |
| binutils-x86-64-linux-gnu | 2.40-2 |  | dpkg-db-cataloger |
| bsdutils | 1:2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| bzip2 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| ca-certificates | 20230311 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| composer | 2.8.4 |  | binary-classifier-cataloger |
| coreutils | 9.1-1 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| cpp | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| cpp-12 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| curl | 7.88.1-10+deb12u8 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| dash | 0.5.12-2 | BSD-3-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dasprid/enum | 1.0.6 | BSD-2-Clause | php-composer-installed-cataloger |
| dasprid/enum | 1.0.6 | BSD-2-Clause | php-composer-installed-cataloger |
| debconf | 1.5.82 | BSD-2-Clause | dpkg-db-cataloger |
| debian-archive-keyring | 2023.3+deb12u1 |  | dpkg-db-cataloger |
| debianutils | 5.7-0.5~deb12u1 | GPL-2.0-only, GPL-2.0-or-later, SMAIL-GPL | dpkg-db-cataloger |
| dictionaries-common | 1.29.5 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| diffutils | 1:3.8-4 | FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| dirmngr | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| dpkg | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| dpkg-dev | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| e2fsprogs | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| emacsen-common | 3.0.5 |  | dpkg-db-cataloger |
| exif | 8.1.31 |  | php-interpreter-cataloger |
| file | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| findutils | 4.9.0-4 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| fontconfig-config | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-dejavu-core | 2.37-6 | GPL-2.0-only, GPL-2.0-or-later, Bitstream-Vera | dpkg-db-cataloger |
| g++ | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| g++-12 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc | 4:12.2.0-3 | GPL-2.0-only | dpkg-db-cataloger |
| gcc-12 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gcc-12-base | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| gd | 8.1.31 |  | php-interpreter-cataloger |
| germancoding/tls_icon | 1.4.1 | MIT | php-composer-installed-cataloger |
| gnupg | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-l10n | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-utils | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-wks-client | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-wks-server | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgv | 2.2.40-1.1 | BSD-3-Clause, CC0-1.0, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| grep | 3.8-5 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| guzzlehttp/guzzle | 7.9.2 | MIT | php-composer-installed-cataloger |
| guzzlehttp/guzzle | 7.9.2 | MIT | php-composer-installed-cataloger |
| guzzlehttp/promises | 2.0.3 | MIT | php-composer-installed-cataloger |
| guzzlehttp/promises | 2.0.3 | MIT | php-composer-installed-cataloger |
| guzzlehttp/psr7 | 2.7.0 | MIT | php-composer-installed-cataloger |
| guzzlehttp/psr7 | 2.7.0 | MIT | php-composer-installed-cataloger |
| gzip | 1.12-1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| hostname | 3.23+nmu1 | GPL-2.0-only | dpkg-db-cataloger |
| imagemagick-6-common | 8:6.9.11.60+dfsg-1.6+deb12u2 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| init-system-helpers | 1.65.2 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| intl | 8.1.31 |  | php-interpreter-cataloger |
| johndoh/contextmenu | 3.3.1 | GPL-3.0-or-later | php-composer-installed-cataloger |
| kolab/net_ldap3 | v1.1.5 | GPL-3.0-or-later | php-composer-installed-cataloger |
| kolab/net_ldap3 | v1.1.5 | GPL-3.0-or-later | php-composer-installed-cataloger |
| ldap | 8.1.31 |  | php-interpreter-cataloger |
| libacl1 | 2.3.1-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaom3 | 3.6.0-1+deb12u1 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, ISC | dpkg-db-cataloger |
| libapr1 | 1.7.2-3+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libaprutil1 | 1.6.3-1 | Apache-2.0 | dpkg-db-cataloger |
| libaprutil1-dbd-sqlite3 | 1.6.3-1 | Apache-2.0 | dpkg-db-cataloger |
| libaprutil1-ldap | 1.6.3-1 | Apache-2.0 | dpkg-db-cataloger |
| libapt-pkg6.0 | 2.6.1 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libargon2-1 | 0~20171227-0.3+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libasan8 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libaspell15 | 0.60.8-4+b1 | GFDL-1.2-only, GFDL-1.2-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libassuan0 | 2.5.5-5 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libatomic1 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libattr1 | 1:2.5.1-4 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit-common | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libaudit1 | 1:3.0.9-1 | GPL-1.0-only, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libbinutils | 2.40-2 |  | dpkg-db-cataloger |
| libblkid-dev | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libblkid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libbrotli1 | 1.0.9-2+b6 | MIT | dpkg-db-cataloger |
| libbsd0 | 0.11.7-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC, libutil-David-Nugent | dpkg-db-cataloger |
| libbz2-1.0 | 1.0.8-5+b1 | GPL-2.0-only | dpkg-db-cataloger |
| libc-bin | 2.36-9+deb12u9 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc-dev-bin | 2.36-9+deb12u9 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc-l10n | 2.36-9+deb12u9 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6 | 2.36-9+deb12u9 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libc6-dev | 2.36-9+deb12u9 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.3-1+b3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.66-4 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcc1-0 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libcom-err2 | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt-dev | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.33-2 |  | dpkg-db-cataloger |
| libctf-nobfd0 | 2.40-2 |  | dpkg-db-cataloger |
| libctf0 | 2.40-2 |  | dpkg-db-cataloger |
| libcurl4 | 7.88.1-10+deb12u8 | BSD-3-Clause, BSD-3-Clause, BSD-4-Clause-UC, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libdav1d6 | 1.0.0-2+deb12u1 | BSD-2-Clause, ISC | dpkg-db-cataloger |
| libdb5.3 | 5.3.28+dfsg2-1 | BSD-3-Clause, GPL-3.0-only, MS-PL, Sleepycat, X11, Zlib | dpkg-db-cataloger |
| libde265-0 | 1.0.11-1+deb12u2 | BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libdebconfclient0 | 0.270 | BSD-2-Clause, BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libdeflate0 | 1.14-1 |  | dpkg-db-cataloger |
| libdpkg-perl | 1.21.22 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libelf1 | 0.188-2.1 | BSD-2-Clause, GFDL-1.3-only, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libexpat1 | 2.5.0-1+deb12u1 | MIT | dpkg-db-cataloger |
| libext2fs2 | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libffi-dev | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libffi8 | 3.4.4-1 | GPL-2.0-or-later, GPL-3.0-or-later, MPL-1.1, X11 | dpkg-db-cataloger |
| libfftw3-double3 | 3.3.10-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libfontconfig1 | 2.14.1-4 | HPND-sell-variant | dpkg-db-cataloger |
| libfreetype6 | 2.12.1+dfsg-5+deb12u3 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, Zlib | dpkg-db-cataloger |
| libgcc-12-dev | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcc-s1 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.10.1-3 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm-compat4 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6 | 1.23-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libglib2.0-0 | 2.74.6-2+deb12u5 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-bin | 2.74.6-2+deb12u5 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-data | 2.74.6-2+deb12u5 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-dev | 2.74.6-2+deb12u5 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglib2.0-dev-bin | 2.74.6-2+deb12u5 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libgmp10 | 2:6.2.1+dfsg1-1.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30 | 3.7.9-2+deb12u3 | Apache-2.0, BSD-3-Clause, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.46-1 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgprofng0 | 2.40-2 |  | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.20.1-2+deb12u2 | GPL-2.0-only | dpkg-db-cataloger |
| libheif1 | 1.15.1-1+deb12u1 | BSD-3-Clause, BSD-4-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libhogweed6 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libicu72 | 72.1-3 | GPL-3.0-only, MIT | dpkg-db-cataloger |
| libidn2-0 | 2.3.3-1+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libisl23 | 0.25-1.1 | BSD-2-Clause, LGPL-2.0-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libitm1 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libjansson4 | 2.14-2 |  | dpkg-db-cataloger |
| libjbig0 | 2.1-6.1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libjpeg62-turbo | 1:2.1.5-2 | BSD-3-Clause, NTP, Zlib | dpkg-db-cataloger |
| libk5crypto3 | 1.20.1-2+deb12u2 | GPL-2.0-only | dpkg-db-cataloger |
| libkeyutils1 | 1.6.3-2 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libkrb5-3 | 1.20.1-2+deb12u2 | GPL-2.0-only | dpkg-db-cataloger |
| libkrb5support0 | 1.20.1-2+deb12u2 | GPL-2.0-only | dpkg-db-cataloger |
| libksba8 | 1.6.3-2 | FSFUL, GPL-3.0-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| liblcms2-2 | 2.14-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, IJG, MIT | dpkg-db-cataloger |
| libldap-2.5-0 | 2.5.13+dfsg-5 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| liblerc4 | 4.0.0+ds-2 | Apache-2.0 | dpkg-db-cataloger |
| liblqr-1-0 | 0.4.2-2.1 | GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| liblsan0 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libltdl7 | 2.4.7-7~deb12u1 | GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblua5.3-0 | 5.3.6-2 |  | dpkg-db-cataloger |
| liblz4-1 | 1.9.4-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| liblzma5 | 5.4.1-0.2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmagic-mgc | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| libmagic1 | 1:5.44-3 | BSD-2-Clause | dpkg-db-cataloger |
| libmagickcore-6.q16-6 | 8:6.9.11.60+dfsg-1.6+deb12u2 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmagickwand-6.q16-6 | 8:6.9.11.60+dfsg-1.6+deb12u2 | GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, ImageMagick, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmd0 | 1.0.4-2 | BSD-2-Clause, BSD-2-Clause, BSD-3-Clause, Beerware, ISC | dpkg-db-cataloger |
| libmount-dev | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmount1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libmpc3 | 1.3.1-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libmpfr6 | 4.2.0-1 | LGPL-3.0-only | dpkg-db-cataloger |
| libncursesw6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnettle8 | 3.8.1-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.52.0-1+deb12u2 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnpth0 | 1.6-3 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnsl-dev | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnsl2 | 1.3.0-2 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later, MIT | dpkg-db-cataloger |
| libnuma1 | 2.0.16-1 |  | dpkg-db-cataloger |
| libonig5 | 6.9.8-1 | BSD-2-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.0-2 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libp11-kit0 | 0.24.1-2 | Apache-2.0, BSD-3-Clause, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpam-modules | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-modules-bin | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam-runtime | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpam0g | 1.5.2-6+deb12u1 | BSD-3-Clause, Beerware, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later | dpkg-db-cataloger |
| libpcre2-16-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-32-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-8-0 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-dev | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libpcre2-posix3 | 10.42-1 | BSD-2-Clause, BSD-3-Clause, X11 | dpkg-db-cataloger |
| libperl5.36 | 5.36.0-7+deb12u1 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| libphp | 8.1.31 |  | php-interpreter-cataloger |
| libpkgconf3 | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| libpng16-16 | 1.6.39-2 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
| libpopt0 | 1.19+dfsg-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libpq5 | 15.10-0+deb12u1 | BSD-2-Clause, BSD-3-Clause, BSD-3-Clause, GPL-1.0-only, PostgreSQL, TCL | dpkg-db-cataloger |
| libproc2-0 | 2:4.0.2-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libpsl5 | 0.21.2-1 | MIT | dpkg-db-cataloger |
| libpython3-stdlib | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| libpython3.11-minimal | 3.11.2-6+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libpython3.11-stdlib | 3.11.2-6+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| libquadmath0 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libreadline8 | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| librtmp1 | 2.4+20151223.gitfa8646d.1-2+b2 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsasl2-2 | 2.1.28+dfsg-10 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libsasl2-modules-db | 2.1.28+dfsg-10 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, BSD-4-Clause-UC, FSFULLR, GPL-3.0-only, GPL-3.0-or-later, MIT-CMU, OpenSSL, RSA-MD | dpkg-db-cataloger |
| libseccomp2 | 2.5.4-1+deb12u1 | LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1 | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libselinux1-dev | 3.4-1+b6 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libsemanage-common | 3.4-1 |  | dpkg-db-cataloger |
| libsemanage2 | 3.4-1+b5 |  | dpkg-db-cataloger |
| libsepol-dev | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsepol2 | 3.4-2.1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, Zlib | dpkg-db-cataloger |
| libsmartcols1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libsodium23 | 1.0.18-1 | BSD-2-Clause, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libsqlite3-0 | 3.40.1-2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libss2 | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libssh2-1 | 1.10.0-3+b1 |  | dpkg-db-cataloger |
| libssl3 | 3.0.15-1~deb12u1 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libstdc++-12-dev | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libstdc++6 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libsystemd0 | 252.33-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libtasn1-6 | 4.19.0-2 | GFDL-1.3-only, GPL-3.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtext-iconv-perl | 1.7-8 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libtiff6 | 4.5.0-6+deb12u2 |  | dpkg-db-cataloger |
| libtinfo6 | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtirpc-common | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc-dev | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtirpc3 | 1.3.3+ds-1 | BSD-3-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| libtsan2 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libubsan1 | 12.2.0-14 | GFDL-1.2-only, GPL-2.0-only, GPL-3.0-only | dpkg-db-cataloger |
| libudev1 | 252.33-1~deb12u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring2 | 1.0-2 | GFDL-1.2-only, GFDL-1.2-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libuuid1 | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libwebp7 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebpdemux2 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libwebpmux3 | 1.2.4-0.2+deb12u1 | Apache-2.0 | dpkg-db-cataloger |
| libx11-6 | 2:1.8.4-2+deb12u2 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx11-data | 2:1.8.4-2+deb12u2 | BSD-1-Clause, HPND, HPND-sell-variant, MIT | dpkg-db-cataloger |
| libx265-199 | 3.5-2+b1 | GPL-2.0-only, GPL-2.0-or-later, ISC, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libxau6 | 1:1.0.9-1 |  | dpkg-db-cataloger |
| libxcb1 | 1.15-1 |  | dpkg-db-cataloger |
| libxdmcp6 | 1:1.1.2-3 |  | dpkg-db-cataloger |
| libxext6 | 2:1.3.4-1+b1 |  | dpkg-db-cataloger |
| libxml2 | 2.9.14+dfsg-1.3~deb12u1 | ISC | dpkg-db-cataloger |
| libxxhash0 | 0.8.1-1 | BSD-2-Clause, GPL-2.0-only | dpkg-db-cataloger |
| libzip4 | 1.7.3-1+b1 | GPL-3.0-only | dpkg-db-cataloger |
| libzstd1 | 1.5.4+dfsg2-5 | BSD-3-Clause, GPL-2.0-only, Zlib | dpkg-db-cataloger |
| linux-libc-dev | 6.1.124-1 | BSD-2-Clause, GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| locales | 2.36-9+deb12u9 | GPL-2.0-only, LGPL-2.1-only | dpkg-db-cataloger |
| login | 1:4.13+dfsg1-1+b1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| logsave | 1.47.0-2 | Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| m4 | 1.4.19-3 |  | dpkg-db-cataloger |
| make | 4.3-4.1 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| masterminds/html5 | 2.7.6 | MIT | php-composer-installed-cataloger |
| masterminds/html5 | 2.7.6 | MIT | php-composer-installed-cataloger |
| mawk | 1.3.4.20200120-3.1 | CC-BY-3.0, GPL-2.0-only, X11 | dpkg-db-cataloger |
| media-types | 10.0.0 |  | dpkg-db-cataloger |
| mount | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| ncurses-base | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| ncurses-bin | 6.4-4 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| opcache | 8.1.31 |  | php-interpreter-cataloger |
| openssl | 3.0.15-1~deb12u1 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| passwd | 1:4.13+dfsg1-1+b1 | BSD-3-Clause, GPL-1.0-only, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| patch | 2.7.6-7 |  | dpkg-db-cataloger |
| pdo_mysql | 8.1.31 |  | php-interpreter-cataloger |
| pdo_pgsql | 8.1.31 |  | php-interpreter-cataloger |
| pdo_sqlite | 8.1.31 |  | php-interpreter-cataloger |
| pear/auth_sasl | v1.1.0 |  | php-composer-installed-cataloger |
| pear/auth_sasl | v1.1.0 |  | php-composer-installed-cataloger |
| pear/console_commandline | v1.2.6 | MIT | php-composer-installed-cataloger |
| pear/console_commandline | v1.2.6 | MIT | php-composer-installed-cataloger |
| pear/console_getopt | v1.4.3 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/console_getopt | v1.4.3 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/crypt_gpg | v1.6.9 | LGPL-2.1-only | php-composer-installed-cataloger |
| pear/crypt_gpg | v1.6.9 | LGPL-2.1-only | php-composer-installed-cataloger |
| pear/mail_mime | 1.10.12 | BSD-3-Clause | php-composer-installed-cataloger |
| pear/mail_mime | 1.10.12 | BSD-3-Clause | php-composer-installed-cataloger |
| pear/net_ldap2 | v2.3.0 | LGPL-3.0-only | php-composer-installed-cataloger |
| pear/net_ldap2 | v2.3.0 | LGPL-3.0-only | php-composer-installed-cataloger |
| pear/net_sieve | 1.4.7 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/net_sieve | 1.4.7 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/net_smtp | 1.10.1 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/net_smtp | 1.10.1 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/net_socket | v1.2.2 |  | php-composer-installed-cataloger |
| pear/net_socket | v1.2.2 |  | php-composer-installed-cataloger |
| pear/pear-core-minimal | v1.10.15 | BSD-3-Clause | php-composer-installed-cataloger |
| pear/pear-core-minimal | v1.10.15 | BSD-3-Clause | php-composer-installed-cataloger |
| pear/pear_exception | v1.0.2 | BSD-2-Clause | php-composer-installed-cataloger |
| pear/pear_exception | v1.0.2 | BSD-2-Clause | php-composer-installed-cataloger |
| perl | 5.36.0-7+deb12u1 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-base | 5.36.0-7+deb12u1 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| perl-modules-5.36 | 5.36.0-7+deb12u1 | Artistic-2.0, Artistic-dist, BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, Zlib | dpkg-db-cataloger |
| php-cli | 8.1.31 |  | php-interpreter-cataloger |
| pinentry-curses | 1.2.1-1 | GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| pkg-config | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| pkgconf | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| pkgconf-bin | 1.8.1-1 | GPL-2.0-only, GPL-2.0-or-later, ISC, X11 | dpkg-db-cataloger |
| procps | 2:4.0.2-3 | GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| pspell | 8.1.31 |  | php-interpreter-cataloger |
| psr/http-client | 1.0.3 | MIT | php-composer-installed-cataloger |
| psr/http-client | 1.0.3 | MIT | php-composer-installed-cataloger |
| psr/http-factory | 1.1.0 | MIT | php-composer-installed-cataloger |
| psr/http-factory | 1.1.0 | MIT | php-composer-installed-cataloger |
| psr/http-message | 2.0 | MIT | php-composer-installed-cataloger |
| psr/http-message | 2.0 | MIT | php-composer-installed-cataloger |
| python3 | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3-distutils | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-lib2to3 | 3.11.2-3 |  | dpkg-db-cataloger |
| python3-minimal | 3.11.2-1+b1 |  | dpkg-db-cataloger |
| python3.11 | 3.11.2-6+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| python3.11-minimal | 3.11.2-6+deb12u5 | GPL-2.0-only | dpkg-db-cataloger |
| ralouphie/getallheaders | 3.0.3 | MIT | php-composer-installed-cataloger |
| ralouphie/getallheaders | 3.0.3 | MIT | php-composer-installed-cataloger |
| re2c | 3.0-2 | Apache-2.0, Apache-2.0, PHP-3.01 | dpkg-db-cataloger |
| readline-common | 8.2-1.3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| roundcube/plugin-installer | 0.3.8 | GPL-3.0-or-later | php-composer-installed-cataloger |
| roundcube/plugin-installer | 0.3.8 | GPL-3.0-or-later | php-composer-installed-cataloger |
| roundcube/rtf-html-php | v2.2 | GPL-2.0-only | php-composer-installed-cataloger |
| roundcube/rtf-html-php | v2.2 | GPL-2.0-only | php-composer-installed-cataloger |
| rpcsvc-proto | 1.4.3-1 | BSD-3-Clause, GPL-2.0-only, GPL-3.0-only, MIT | dpkg-db-cataloger |
| rsync | 3.2.7-1+deb12u2 | GPL-3.0-only | dpkg-db-cataloger |
| sed | 4.9-1 | BSD-4-Clause-UC, BSL-1.0, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC, X11 | dpkg-db-cataloger |
| sodium | 8.1.31 |  | php-interpreter-cataloger |
| symfony/deprecation-contracts | v2.5.3 | MIT | php-composer-installed-cataloger |
| symfony/deprecation-contracts | v2.5.3 | MIT | php-composer-installed-cataloger |
| sysvinit-utils | 3.06-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only | dpkg-db-cataloger |
| tar | 1.34+dfsg-1.2+deb12u1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tzdata | 2024b-0+deb12u1 |  | dpkg-db-cataloger |
| unzip | 6.0-28 |  | dpkg-db-cataloger |
| usr-is-merged | 37~deb12u1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| util-linux | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| util-linux-extra | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| uuid-dev | 2.38.1-5+deb12u3 | BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MIT | dpkg-db-cataloger |
| weird-birds/thunderbird_labels | v1.6.2 | BSD-2-Clause | php-composer-installed-cataloger |
| xz-utils | 5.4.1-0.2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| zip | 1.19.5 |  | php-interpreter-cataloger |
| zlib1g | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |
| zlib1g-dev | 1:1.2.13.dfsg-1 | Zlib | dpkg-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/minio

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| aead.dev/mem | v0.2.0 |  | go-module-binary-cataloger |
| aead.dev/minisign | v0.3.0 |  | go-module-binary-cataloger |
| aead.dev/minisign | v0.3.0 |  | go-module-binary-cataloger |
| basesystem | 11-13.el9 |  | rpm-db-cataloger |
| bash | 5.1.8-9.el9 |  | rpm-db-cataloger |
| cel.dev/expr | v0.19.0 |  | go-module-binary-cataloger |
| cloud.google.com/go | v0.116.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth | v0.13.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/auth/oauth2adapt | v0.2.6 |  | go-module-binary-cataloger |
| cloud.google.com/go/compute/metadata | v0.6.0 |  | go-module-binary-cataloger |
| cloud.google.com/go/iam | v1.2.2 |  | go-module-binary-cataloger |
| cloud.google.com/go/monitoring | v1.21.2 |  | go-module-binary-cataloger |
| cloud.google.com/go/storage | v1.46.0 |  | go-module-binary-cataloger |
| coreutils-single | 8.32-36.el9 |  | rpm-db-cataloger |
| curl | 8.11.0 |  | binary-classifier-cataloger |
| filesystem | 3.16-5.el9 |  | rpm-db-cataloger |
| filippo.io/edwards25519 | v1.1.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azcore | v1.16.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/azidentity | v1.8.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/internal | v1.10.0 |  | go-module-binary-cataloger |
| github.com/Azure/azure-sdk-for-go/sdk/storage/azblob | v1.5.0 |  | go-module-binary-cataloger |
| github.com/Azure/go-ntlmssp | v0.0.0-20221128193559-754e69321358 |  | go-module-binary-cataloger |
| github.com/AzureAD/microsoft-authentication-library-for-go | v1.3.1 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/detectors/gcp | v1.25.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/exporter/metric | v0.49.0 |  | go-module-binary-cataloger |
| github.com/GoogleCloudPlatform/opentelemetry-operations-go/internal/resourcemapping | v0.49.0 |  | go-module-binary-cataloger |
| github.com/IBM/sarama | v1.43.3 |  | go-module-binary-cataloger |
| github.com/VividCortex/ewma | v1.2.0 |  | go-module-binary-cataloger |
| github.com/VividCortex/ewma | v1.2.0 |  | go-module-binary-cataloger |
| github.com/acarl005/stripansi | v0.0.0-20180116102854-5a71ef0e047d |  | go-module-binary-cataloger |
| github.com/acarl005/stripansi | v0.0.0-20180116102854-5a71ef0e047d |  | go-module-binary-cataloger |
| github.com/alecthomas/participle | v0.7.1 |  | go-module-binary-cataloger |
| github.com/apache/thrift | v0.21.0 |  | go-module-binary-cataloger |
| github.com/asaskevich/govalidator | v0.0.0-20230301143203-a9d515a09cc2 |  | go-module-binary-cataloger |
| github.com/aymanbagabas/go-osc52/v2 | v2.0.1 |  | go-module-binary-cataloger |
| github.com/aymanbagabas/go-osc52/v2 | v2.0.1 |  | go-module-binary-cataloger |
| github.com/beevik/ntp | v1.4.3 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/buger/jsonparser | v1.1.1 |  | go-module-binary-cataloger |
| github.com/census-instrumentation/opencensus-proto | v0.4.1 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/bubbles | v0.20.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/bubbles | v0.20.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/bubbletea | v1.3.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/bubbletea | v1.3.3 |  | go-module-binary-cataloger |
| github.com/charmbracelet/lipgloss | v1.0.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/lipgloss | v1.0.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/ansi | v0.8.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/ansi | v0.8.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/term | v0.2.1 |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/term | v0.2.1 |  | go-module-binary-cataloger |
| github.com/cheggaaa/pb | v1.0.29 |  | go-module-binary-cataloger |
| github.com/cheggaaa/pb | v1.0.29 |  | go-module-binary-cataloger |
| github.com/cncf/xds/go | v0.0.0-20240905190251-b4127c9b8d78 |  | go-module-binary-cataloger |
| github.com/coreos/go-oidc/v3 | v3.11.0 |  | go-module-binary-cataloger |
| github.com/coreos/go-semver | v0.3.1 |  | go-module-binary-cataloger |
| github.com/coreos/go-semver | v0.3.1 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.5.0 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.5.0 |  | go-module-binary-cataloger |
| github.com/cosnicolaou/pbzip2 | v1.0.5 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.2-0.20180830191138-d8f796af33cc |  | go-module-binary-cataloger |
| github.com/dchest/siphash | v1.2.3 |  | go-module-binary-cataloger |
| github.com/docker/go-units | v0.5.0 |  | go-module-binary-cataloger |
| github.com/dustin/go-humanize | v1.0.1 |  | go-module-binary-cataloger |
| github.com/dustin/go-humanize | v1.0.1 |  | go-module-binary-cataloger |
| github.com/eapache/go-resiliency | v1.7.0 |  | go-module-binary-cataloger |
| github.com/eapache/go-xerial-snappy | v0.0.0-20230731223053-c322873962e3 |  | go-module-binary-cataloger |
| github.com/eapache/queue | v1.1.0 |  | go-module-binary-cataloger |
| github.com/eclipse/paho.mqtt.golang | v1.5.0 |  | go-module-binary-cataloger |
| github.com/elastic/go-elasticsearch/v7 | v7.17.10 |  | go-module-binary-cataloger |
| github.com/envoyproxy/go-control-plane | v0.13.1 |  | go-module-binary-cataloger |
| github.com/envoyproxy/protoc-gen-validate | v1.1.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.18.0 |  | go-module-binary-cataloger |
| github.com/fatih/structs | v1.1.0 |  | go-module-binary-cataloger |
| github.com/fatih/structs | v1.1.0 |  | go-module-binary-cataloger |
| github.com/felixge/fgprof | v0.9.5 |  | go-module-binary-cataloger |
| github.com/felixge/httpsnoop | v1.0.4 |  | go-module-binary-cataloger |
| github.com/fraugster/parquet-go | v0.12.0 |  | go-module-binary-cataloger |
| github.com/go-asn1-ber/asn1-ber | v1.5.7 |  | go-module-binary-cataloger |
| github.com/go-ini/ini | v1.67.0 |  | go-module-binary-cataloger |
| github.com/go-ini/ini | v1.67.0 |  | go-module-binary-cataloger |
| github.com/go-jose/go-jose/v4 | v4.0.5 |  | go-module-binary-cataloger |
| github.com/go-ldap/ldap/v3 | v3.4.8 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.2 |  | go-module-binary-cataloger |
| github.com/go-logr/stdr | v1.2.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/analysis | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/errors | v0.22.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/loads | v0.22.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/runtime | v0.28.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/spec | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/strfmt | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.23.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/validate | v0.24.0 |  | go-module-binary-cataloger |
| github.com/go-sql-driver/mysql | v1.8.1 |  | go-module-binary-cataloger |
| github.com/gobwas/httphead | v0.1.0 |  | go-module-binary-cataloger |
| github.com/gobwas/pool | v0.2.1 |  | go-module-binary-cataloger |
| github.com/gobwas/ws | v1.4.0 |  | go-module-binary-cataloger |
| github.com/goccy/go-json | v0.10.5 |  | go-module-binary-cataloger |
| github.com/goccy/go-json | v0.10.5 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v4 | v4.5.1 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v4 | v4.5.1 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v5 | v5.2.1 |  | go-module-binary-cataloger |
| github.com/golang/groupcache | v0.0.0-20210331224755-41bb18bfe9da |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/golang/snappy | v0.0.4 |  | go-module-binary-cataloger |
| github.com/gomodule/redigo | v1.9.2 |  | go-module-binary-cataloger |
| github.com/google/pprof | v0.0.0-20241210010833-40e02aabc2ad |  | go-module-binary-cataloger |
| github.com/google/s2a-go | v0.1.8 |  | go-module-binary-cataloger |
| github.com/google/shlex | v0.0.0-20191202100458-e7afc7fbc510 |  | go-module-binary-cataloger |
| github.com/google/shlex | v0.0.0-20191202100458-e7afc7fbc510 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/googleapis/enterprise-certificate-proxy | v0.3.4 |  | go-module-binary-cataloger |
| github.com/googleapis/gax-go/v2 | v2.14.0 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.3 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-uuid | v1.0.3 |  | go-module-binary-cataloger |
| github.com/inconshreveable/mousetrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/inconshreveable/mousetrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/aescts/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/dnsutils/v2 | v2.0.0 |  | go-module-binary-cataloger |
| github.com/jcmturner/gofork | v1.7.6 |  | go-module-binary-cataloger |
| github.com/jcmturner/gokrb5/v8 | v8.4.4 |  | go-module-binary-cataloger |
| github.com/jcmturner/rpc/v2 | v2.0.3 |  | go-module-binary-cataloger |
| github.com/jedib0t/go-pretty/v6 | v6.6.5 |  | go-module-binary-cataloger |
| github.com/jedib0t/go-pretty/v6 | v6.6.6 |  | go-module-binary-cataloger |
| github.com/jessevdk/go-flags | v1.6.1 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/juju/ratelimit | v1.0.2 |  | go-module-binary-cataloger |
| github.com/juju/ratelimit | v1.0.2 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.11 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.11 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.2.9 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.2.9 |  | go-module-binary-cataloger |
| github.com/klauspost/filepathx | v1.1.1 |  | go-module-binary-cataloger |
| github.com/klauspost/pgzip | v1.2.6 |  | go-module-binary-cataloger |
| github.com/klauspost/readahead | v1.4.0 |  | go-module-binary-cataloger |
| github.com/klauspost/reedsolomon | v1.12.4 |  | go-module-binary-cataloger |
| github.com/kr/fs | v0.1.0 |  | go-module-binary-cataloger |
| github.com/kylelemons/godebug | v1.1.0 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/blackmagic | v1.0.2 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/blackmagic | v1.0.2 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/httpcc | v1.0.1 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/httpcc | v1.0.1 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/httprc | v1.0.6 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/httprc | v1.0.6 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/iter | v1.0.2 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/iter | v1.0.2 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/jwx/v2 | v2.1.3 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/jwx/v2 | v2.1.3 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/option | v1.0.1 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/option | v1.0.1 |  | go-module-binary-cataloger |
| github.com/lib/pq | v1.10.9 |  | go-module-binary-cataloger |
| github.com/lithammer/shortuuid/v4 | v4.0.0 |  | go-module-binary-cataloger |
| github.com/lucasb-eyer/go-colorful | v1.2.0 |  | go-module-binary-cataloger |
| github.com/lucasb-eyer/go-colorful | v1.2.0 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.9.0 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-ieproxy | v0.0.12 |  | go-module-binary-cataloger |
| github.com/mattn/go-ieproxy | v0.0.12 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.16 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.16 |  | go-module-binary-cataloger |
| github.com/matttproud/golang_protobuf_extensions | v1.0.4 |  | go-module-binary-cataloger |
| github.com/matttproud/golang_protobuf_extensions | v1.0.4 |  | go-module-binary-cataloger |
| github.com/miekg/dns | v1.1.62 |  | go-module-binary-cataloger |
| github.com/minio/cli | v1.24.2 |  | go-module-binary-cataloger |
| github.com/minio/cli | v1.24.2 |  | go-module-binary-cataloger |
| github.com/minio/colorjson | v1.0.8 |  | go-module-binary-cataloger |
| github.com/minio/colorjson | v1.0.8 |  | go-module-binary-cataloger |
| github.com/minio/console | v1.7.6 |  | go-module-binary-cataloger |
| github.com/minio/crc64nvme | v1.0.1 |  | go-module-binary-cataloger |
| github.com/minio/csvparser | v1.0.0 |  | go-module-binary-cataloger |
| github.com/minio/dnscache | v0.1.1 |  | go-module-binary-cataloger |
| github.com/minio/dperf | v0.6.3 |  | go-module-binary-cataloger |
| github.com/minio/filepath | v1.0.0 |  | go-module-binary-cataloger |
| github.com/minio/filepath | v1.0.0 |  | go-module-binary-cataloger |
| github.com/minio/highwayhash | v1.0.3 |  | go-module-binary-cataloger |
| github.com/minio/kms-go/kes | v0.3.1 |  | go-module-binary-cataloger |
| github.com/minio/kms-go/kms | v0.4.0 |  | go-module-binary-cataloger |
| github.com/minio/madmin-go/v3 | v3.0.91 |  | go-module-binary-cataloger |
| github.com/minio/madmin-go/v3 | v3.0.94 |  | go-module-binary-cataloger |
| github.com/minio/mc | v0.0.0-20250208210632-10c50368c526 |  | go-module-binary-cataloger |
| github.com/minio/mc | v0.0.0-20250221160046-9eb205cb62c6 |  | go-module-binary-cataloger |
| github.com/minio/md5-simd | v1.1.2 |  | go-module-binary-cataloger |
| github.com/minio/md5-simd | v1.1.2 |  | go-module-binary-cataloger |
| github.com/minio/minio | v0.0.0-20250228095516-8c2c92f7afdc |  | go-module-binary-cataloger |
| github.com/minio/minio-go/v7 | v7.0.85 |  | go-module-binary-cataloger |
| github.com/minio/minio-go/v7 | v7.0.87 |  | go-module-binary-cataloger |
| github.com/minio/mux | v1.9.0 |  | go-module-binary-cataloger |
| github.com/minio/pkg/v3 | v3.0.29 |  | go-module-binary-cataloger |
| github.com/minio/pkg/v3 | v3.0.30 |  | go-module-binary-cataloger |
| github.com/minio/selfupdate | v0.6.0 |  | go-module-binary-cataloger |
| github.com/minio/selfupdate | v0.6.0 |  | go-module-binary-cataloger |
| github.com/minio/simdjson-go | v0.4.5 |  | go-module-binary-cataloger |
| github.com/minio/sio | v0.4.1 |  | go-module-binary-cataloger |
| github.com/minio/websocket | v1.6.0 |  | go-module-binary-cataloger |
| github.com/minio/xxml | v0.0.3 |  | go-module-binary-cataloger |
| github.com/minio/zipindex | v0.4.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/mapstructure | v1.5.0 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/montanaflynn/stats | v0.7.1 |  | go-module-binary-cataloger |
| github.com/muesli/ansi | v0.0.0-20230316100256-276c6243b2f6 |  | go-module-binary-cataloger |
| github.com/muesli/ansi | v0.0.0-20230316100256-276c6243b2f6 |  | go-module-binary-cataloger |
| github.com/muesli/cancelreader | v0.2.2 |  | go-module-binary-cataloger |
| github.com/muesli/cancelreader | v0.2.2 |  | go-module-binary-cataloger |
| github.com/muesli/reflow | v0.3.0 |  | go-module-binary-cataloger |
| github.com/muesli/reflow | v0.3.0 |  | go-module-binary-cataloger |
| github.com/muesli/termenv | v0.15.2 |  | go-module-binary-cataloger |
| github.com/muesli/termenv | v0.15.2 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/nats-io/nats.go | v1.37.0 |  | go-module-binary-cataloger |
| github.com/nats-io/nkeys | v0.4.7 |  | go-module-binary-cataloger |
| github.com/nats-io/nuid | v1.0.1 |  | go-module-binary-cataloger |
| github.com/nats-io/stan.go | v0.10.4 |  | go-module-binary-cataloger |
| github.com/ncw/directio | v1.0.5 |  | go-module-binary-cataloger |
| github.com/nsqio/go-nsq | v1.1.0 |  | go-module-binary-cataloger |
| github.com/oklog/ulid | v1.3.1 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v0.0.5 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v0.0.5 |  | go-module-binary-cataloger |
| github.com/philhofer/fwd | v1.1.3-0.20240916144458-20a13a1f6b7c |  | go-module-binary-cataloger |
| github.com/philhofer/fwd | v1.1.3-0.20240916144458-20a13a1f6b7c |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.21 |  | go-module-binary-cataloger |
| github.com/pkg/browser | v0.0.0-20240102092130-5ac0b6a4141c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/sftp | v1.13.7 |  | go-module-binary-cataloger |
| github.com/pkg/xattr | v0.4.10 |  | go-module-binary-cataloger |
| github.com/pkg/xattr | v0.4.10 |  | go-module-binary-cataloger |
| github.com/posener/complete | v1.2.3 |  | go-module-binary-cataloger |
| github.com/posener/complete | v1.2.3 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.20.5 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.20.5 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.1 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.62.0 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.62.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.15.1 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.15.1 |  | go-module-binary-cataloger |
| github.com/prometheus/prom2json | v1.4.1 |  | go-module-binary-cataloger |
| github.com/prometheus/prom2json | v1.4.1 |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.301.0 |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.301.0 |  | go-module-binary-cataloger |
| github.com/puzpuzpuz/xsync/v3 | v3.4.0 |  | go-module-binary-cataloger |
| github.com/rabbitmq/amqp091-go | v1.10.0 |  | go-module-binary-cataloger |
| github.com/rcrowley/go-metrics | v0.0.0-20201227073835-cf1acfcdf475 |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.4.7 |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.4.7 |  | go-module-binary-cataloger |
| github.com/rjeczalik/notify | v0.9.3 |  | go-module-binary-cataloger |
| github.com/rjeczalik/notify | v0.9.3 |  | go-module-binary-cataloger |
| github.com/rs/cors | v1.11.1 |  | go-module-binary-cataloger |
| github.com/rs/xid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/rs/xid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/safchain/ethtool | v0.5.10 |  | go-module-binary-cataloger |
| github.com/safchain/ethtool | v0.5.10 |  | go-module-binary-cataloger |
| github.com/secure-io/sio-go | v0.3.1 |  | go-module-binary-cataloger |
| github.com/secure-io/sio-go | v0.3.1 |  | go-module-binary-cataloger |
| github.com/shirou/gopsutil/v3 | v3.24.5 |  | go-module-binary-cataloger |
| github.com/shirou/gopsutil/v3 | v3.24.5 |  | go-module-binary-cataloger |
| github.com/tidwall/gjson | v1.18.0 |  | go-module-binary-cataloger |
| github.com/tidwall/gjson | v1.18.0 |  | go-module-binary-cataloger |
| github.com/tidwall/match | v1.1.1 |  | go-module-binary-cataloger |
| github.com/tidwall/match | v1.1.1 |  | go-module-binary-cataloger |
| github.com/tidwall/pretty | v1.2.1 |  | go-module-binary-cataloger |
| github.com/tidwall/pretty | v1.2.1 |  | go-module-binary-cataloger |
| github.com/tinylib/msgp | v1.2.5 |  | go-module-binary-cataloger |
| github.com/tinylib/msgp | v1.2.5 |  | go-module-binary-cataloger |
| github.com/tklauser/go-sysconf | v0.3.14 |  | go-module-binary-cataloger |
| github.com/tklauser/go-sysconf | v0.3.14 |  | go-module-binary-cataloger |
| github.com/tklauser/numcpus | v0.9.0 |  | go-module-binary-cataloger |
| github.com/tklauser/numcpus | v0.9.0 |  | go-module-binary-cataloger |
| github.com/unrolled/secure | v1.17.0 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/vbauerster/mpb/v8 | v8.9.2 |  | go-module-binary-cataloger |
| github.com/vbauerster/mpb/v8 | v8.9.2 |  | go-module-binary-cataloger |
| github.com/xdg/scram | v1.0.5 |  | go-module-binary-cataloger |
| github.com/xdg/stringprep | v1.0.3 |  | go-module-binary-cataloger |
| github.com/zeebo/xxh3 | v1.0.2 |  | go-module-binary-cataloger |
| glibc | 2.34-125.el9_5.1 |  | rpm-db-cataloger |
| glibc-common | 2.34-125.el9_5.1 |  | rpm-db-cataloger |
| glibc-minimal-langpack | 2.34-125.el9_5.1 |  | rpm-db-cataloger |
| go.etcd.io/etcd/api/v3 | v3.5.18 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/api/v3 | v3.5.18 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.5.18 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.5.18 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.5.18 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.5.18 |  | go-module-binary-cataloger |
| go.mongodb.org/mongo-driver | v1.17.2 |  | go-module-binary-cataloger |
| go.opencensus.io | v0.24.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/auto/sdk | v1.1.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/detectors/gcp | v1.32.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc | v0.57.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp | v0.58.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.33.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/metric | v1.33.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk | v1.33.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/sdk/metric | v1.32.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.33.0 |  | go-module-binary-cataloger |
| go.uber.org/atomic | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.27.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.27.0 |  | go-module-binary-cataloger |
| goftp.io/server/v2 | v2.0.1 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.35.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.35.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.35.0 |  | go-module-binary-cataloger |
| golang.org/x/oauth2 | v0.26.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.11.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.11.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.30.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.30.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.29.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.29.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.22.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.22.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.8.0 |  | go-module-binary-cataloger |
| google.golang.org/api | v0.213.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto | v0.0.0-20241113202542-65e8d215514f |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20250207221924-e9438ea467c6 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20250212204824-5a70512c5d8b |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20250207221924-e9438ea467c6 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20250212204824-5a70512c5d8b |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.70.0 |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.70.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.5 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.5 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gpg-pubkey | 5a6340b3-6229229e |  | rpm-db-cataloger |
| gpg-pubkey | fd431d51-4ae0493b |  | rpm-db-cataloger |
| libacl | 2.3.1-4.el9 |  | rpm-db-cataloger |
| libattr | 2.5.1-3.el9 |  | rpm-db-cataloger |
| libcap | 2.48-9.el9_2 |  | rpm-db-cataloger |
| libgcc | 11.5.0-5.el9_5 |  | rpm-db-cataloger |
| libselinux | 3.6-1.el9 |  | rpm-db-cataloger |
| libsepol | 3.6-1.el9 |  | rpm-db-cataloger |
| ncurses-base | 6.2-10.20210508.el9 | MIT | rpm-db-cataloger |
| ncurses-libs | 6.2-10.20210508.el9 | MIT | rpm-db-cataloger |
| pcre2 | 10.40-6.el9 |  | rpm-db-cataloger |
| pcre2-syntax | 10.40-6.el9 |  | rpm-db-cataloger |
| redhat-release | 9.5-0.6.el9 |  | rpm-db-cataloger |
| setup | 2.13.7-10.el9 |  | rpm-db-cataloger |
| stdlib | go1.23.6 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.23.6 | BSD-3-Clause | go-module-binary-cataloger |
| tzdata | 2025a-1.el9 |  | rpm-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/mc

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| aead.dev/minisign | v0.3.0 |  | go-module-binary-cataloger |
| basesystem | 11-13.el9 |  | rpm-db-cataloger |
| bash | 5.1.8-9.el9 |  | rpm-db-cataloger |
| coreutils-single | 8.32-36.el9 |  | rpm-db-cataloger |
| filesystem | 3.16-5.el9 |  | rpm-db-cataloger |
| github.com/VividCortex/ewma | v1.2.0 |  | go-module-binary-cataloger |
| github.com/acarl005/stripansi | v0.0.0-20180116102854-5a71ef0e047d |  | go-module-binary-cataloger |
| github.com/aymanbagabas/go-osc52/v2 | v2.0.1 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/bubbles | v0.20.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/bubbletea | v1.1.1 |  | go-module-binary-cataloger |
| github.com/charmbracelet/lipgloss | v0.13.0 |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/ansi | v0.3.2 |  | go-module-binary-cataloger |
| github.com/charmbracelet/x/term | v0.2.0 |  | go-module-binary-cataloger |
| github.com/cheggaaa/pb | v1.0.29 |  | go-module-binary-cataloger |
| github.com/coreos/go-semver | v0.3.1 |  | go-module-binary-cataloger |
| github.com/coreos/go-systemd/v22 | v22.5.0 |  | go-module-binary-cataloger |
| github.com/dustin/go-humanize | v1.0.1 |  | go-module-binary-cataloger |
| github.com/fatih/color | v1.17.0 |  | go-module-binary-cataloger |
| github.com/fatih/structs | v1.1.0 |  | go-module-binary-cataloger |
| github.com/go-ini/ini | v1.67.0 |  | go-module-binary-cataloger |
| github.com/goccy/go-json | v0.10.3 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/golang-jwt/jwt/v4 | v4.5.1 |  | go-module-binary-cataloger |
| github.com/golang/protobuf | v1.5.4 |  | go-module-binary-cataloger |
| github.com/google/shlex | v0.0.0-20191202100458-e7afc7fbc510 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/errwrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-multierror | v1.1.1 |  | go-module-binary-cataloger |
| github.com/inconshreveable/mousetrap | v1.1.0 |  | go-module-binary-cataloger |
| github.com/jedib0t/go-pretty/v6 | v6.5.9 |  | go-module-binary-cataloger |
| github.com/juju/ratelimit | v1.0.2 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.17.10 |  | go-module-binary-cataloger |
| github.com/klauspost/cpuid/v2 | v2.2.8 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/backoff/v2 | v2.0.8 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/blackmagic | v1.0.2 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/httpcc | v1.0.1 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/iter | v1.0.2 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/jwx | v1.2.30 |  | go-module-binary-cataloger |
| github.com/lestrrat-go/option | v1.0.1 |  | go-module-binary-cataloger |
| github.com/lucasb-eyer/go-colorful | v1.2.0 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.13 |  | go-module-binary-cataloger |
| github.com/mattn/go-ieproxy | v0.0.12 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.16 |  | go-module-binary-cataloger |
| github.com/matttproud/golang_protobuf_extensions | v1.0.4 |  | go-module-binary-cataloger |
| github.com/minio/cli | v1.24.2 |  | go-module-binary-cataloger |
| github.com/minio/colorjson | v1.0.8 |  | go-module-binary-cataloger |
| github.com/minio/filepath | v1.0.0 |  | go-module-binary-cataloger |
| github.com/minio/madmin-go/v3 | v3.0.70 |  | go-module-binary-cataloger |
| github.com/minio/mc | v0.0.0-20241121172154-1681e4497c09 |  | go-module-binary-cataloger |
| github.com/minio/md5-simd | v1.1.2 |  | go-module-binary-cataloger |
| github.com/minio/minio-go/v7 | v7.0.77 |  | go-module-binary-cataloger |
| github.com/minio/pkg/v3 | v3.0.20 |  | go-module-binary-cataloger |
| github.com/minio/selfupdate | v0.6.0 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-homedir | v1.1.0 |  | go-module-binary-cataloger |
| github.com/muesli/ansi | v0.0.0-20230316100256-276c6243b2f6 |  | go-module-binary-cataloger |
| github.com/muesli/cancelreader | v0.2.2 |  | go-module-binary-cataloger |
| github.com/muesli/reflow | v0.3.0 |  | go-module-binary-cataloger |
| github.com/muesli/termenv | v0.15.2 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/olekukonko/tablewriter | v0.0.5 |  | go-module-binary-cataloger |
| github.com/philhofer/fwd | v1.1.3-0.20240916144458-20a13a1f6b7c |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/pkg/xattr | v0.4.10 |  | go-module-binary-cataloger |
| github.com/posener/complete | v1.2.3 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.20.4 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.60.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.15.1 |  | go-module-binary-cataloger |
| github.com/prometheus/prom2json | v1.4.1 |  | go-module-binary-cataloger |
| github.com/prometheus/prometheus | v0.54.1 |  | go-module-binary-cataloger |
| github.com/rivo/uniseg | v0.4.7 |  | go-module-binary-cataloger |
| github.com/rjeczalik/notify | v0.9.3 |  | go-module-binary-cataloger |
| github.com/rs/xid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/safchain/ethtool | v0.4.1 |  | go-module-binary-cataloger |
| github.com/secure-io/sio-go | v0.3.1 |  | go-module-binary-cataloger |
| github.com/shirou/gopsutil/v3 | v3.24.5 |  | go-module-binary-cataloger |
| github.com/tidwall/gjson | v1.17.3 |  | go-module-binary-cataloger |
| github.com/tidwall/match | v1.1.1 |  | go-module-binary-cataloger |
| github.com/tidwall/pretty | v1.2.1 |  | go-module-binary-cataloger |
| github.com/tinylib/msgp | v1.2.2 |  | go-module-binary-cataloger |
| github.com/tklauser/go-sysconf | v0.3.14 |  | go-module-binary-cataloger |
| github.com/tklauser/numcpus | v0.8.0 |  | go-module-binary-cataloger |
| github.com/vbauerster/mpb/v8 | v8.8.3 |  | go-module-binary-cataloger |
| glibc | 2.34-125.el9_5.1 |  | rpm-db-cataloger |
| glibc-common | 2.34-125.el9_5.1 |  | rpm-db-cataloger |
| glibc-minimal-langpack | 2.34-125.el9_5.1 |  | rpm-db-cataloger |
| go.etcd.io/etcd/api/v3 | v3.5.16 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/pkg/v3 | v3.5.16 |  | go-module-binary-cataloger |
| go.etcd.io/etcd/client/v3 | v3.5.16 |  | go-module-binary-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.27.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.27.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.29.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.8.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.25.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.24.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.18.0 |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/api | v0.0.0-20240930140551-af27646dc61f |  | go-module-binary-cataloger |
| google.golang.org/genproto/googleapis/rpc | v0.0.0-20240930140551-af27646dc61f |  | go-module-binary-cataloger |
| google.golang.org/grpc | v1.67.1 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.34.2 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v3 | v3.0.1 |  | go-module-binary-cataloger |
| gpg-pubkey | 5a6340b3-6229229e |  | rpm-db-cataloger |
| gpg-pubkey | fd431d51-4ae0493b |  | rpm-db-cataloger |
| libacl | 2.3.1-4.el9 |  | rpm-db-cataloger |
| libattr | 2.5.1-3.el9 |  | rpm-db-cataloger |
| libcap | 2.48-9.el9_2 |  | rpm-db-cataloger |
| libgcc | 11.5.0-2.el9 |  | rpm-db-cataloger |
| libselinux | 3.6-1.el9 |  | rpm-db-cataloger |
| libsepol | 3.6-1.el9 |  | rpm-db-cataloger |
| ncurses-base | 6.2-10.20210508.el9 | MIT | rpm-db-cataloger |
| ncurses-libs | 6.2-10.20210508.el9 | MIT | rpm-db-cataloger |
| pcre2 | 10.40-6.el9 |  | rpm-db-cataloger |
| pcre2-syntax | 10.40-6.el9 |  | rpm-db-cataloger |
| redhat-release | 9.5-0.6.el9 |  | rpm-db-cataloger |
| setup | 2.13.7-10.el9 |  | rpm-db-cataloger |
| stdlib | go1.23.4 | BSD-3-Clause | go-module-binary-cataloger |
| tzdata | 2024b-2.el9 |  | rpm-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/alpine

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.7.0-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.7.0-r0 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.5-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.22.0-r0 | MIT | apk-db-cataloger |
| apk-tools | 2.14.9-r2 | GPL-2.0-only | apk-db-cataloger |
| bash | 5.2.37-r0 | GPL-3.0-or-later | apk-db-cataloger |
| busybox | 1.37.0-r18 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r18 | GPL-2.0-only | apk-db-cataloger |
| ca-certificates-bundle | 20241121-r2 | MPL-2.0 AND MIT | apk-db-cataloger |
| github.com/MakeNowJust/heredoc | v1.0.0 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/blang/semver/v4 | v4.0.0 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/chai2010/gettext-go | v1.0.2 |  | go-module-binary-cataloger |
| github.com/davecgh/go-spew | v1.1.1 |  | go-module-binary-cataloger |
| github.com/distribution/reference | v0.6.0 |  | go-module-binary-cataloger |
| github.com/emicklei/go-restful/v3 | v3.11.0 |  | go-module-binary-cataloger |
| github.com/exponent-io/jsonpath | v0.0.0-20210407135951-1de76d718b3f |  | go-module-binary-cataloger |
| github.com/fatih/camelcase | v1.0.0 |  | go-module-binary-cataloger |
| github.com/fxamacker/cbor/v2 | v2.7.0 |  | go-module-binary-cataloger |
| github.com/go-errors/errors | v1.4.2 |  | go-module-binary-cataloger |
| github.com/go-logr/logr | v1.4.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonpointer | v0.21.0 |  | go-module-binary-cataloger |
| github.com/go-openapi/jsonreference | v0.20.2 |  | go-module-binary-cataloger |
| github.com/go-openapi/swag | v0.23.0 |  | go-module-binary-cataloger |
| github.com/gogo/protobuf | v1.3.2 |  | go-module-binary-cataloger |
| github.com/google/btree | v1.1.3 |  | go-module-binary-cataloger |
| github.com/google/gnostic-models | v0.6.9 |  | go-module-binary-cataloger |
| github.com/google/go-cmp | v0.7.0 |  | go-module-binary-cataloger |
| github.com/google/shlex | v0.0.0-20191202100458-e7afc7fbc510 |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/gorilla/websocket | v1.5.4-0.20250319132907-e064f32e3674 |  | go-module-binary-cataloger |
| github.com/gregjones/httpcache | v0.0.0-20190611155906-901d90724c79 |  | go-module-binary-cataloger |
| github.com/jonboulle/clockwork | v0.4.0 |  | go-module-binary-cataloger |
| github.com/josharian/intern | v1.0.0 |  | go-module-binary-cataloger |
| github.com/json-iterator/go | v1.1.12 |  | go-module-binary-cataloger |
| github.com/liggitt/tabwriter | v0.0.0-20181228230101-89fcab3d43de |  | go-module-binary-cataloger |
| github.com/lithammer/dedent | v1.1.0 |  | go-module-binary-cataloger |
| github.com/mailru/easyjson | v0.7.7 |  | go-module-binary-cataloger |
| github.com/mitchellh/go-wordwrap | v1.0.1 |  | go-module-binary-cataloger |
| github.com/moby/spdystream | v0.5.0 |  | go-module-binary-cataloger |
| github.com/moby/term | v0.5.0 |  | go-module-binary-cataloger |
| github.com/modern-go/concurrent | v0.0.0-20180306012644-bacd9c7ef1dd |  | go-module-binary-cataloger |
| github.com/modern-go/reflect2 | v1.0.2 |  | go-module-binary-cataloger |
| github.com/monochromegane/go-gitignore | v0.0.0-20200626010858-205db1a8cc00 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/mxk/go-flowrate | v0.0.0-20140419014527-cca7078d478f |  | go-module-binary-cataloger |
| github.com/opencontainers/go-digest | v1.0.0 |  | go-module-binary-cataloger |
| github.com/peterbourgon/diskv | v2.0.1+incompatible |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.22.0 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.1 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.62.0 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.15.1 |  | go-module-binary-cataloger |
| github.com/russross/blackfriday/v2 | v2.1.0 |  | go-module-binary-cataloger |
| github.com/spf13/cobra | v1.8.1 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.5 |  | go-module-binary-cataloger |
| github.com/x448/float16 | v0.8.4 |  | go-module-binary-cataloger |
| github.com/xlab/treeprint | v1.2.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel | v1.33.0 |  | go-module-binary-cataloger |
| go.opentelemetry.io/otel/trace | v1.33.0 |  | go-module-binary-cataloger |
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
| k8s.io/kube-openapi | v0.0.0-20250318190949-c8a335a9a2ff |  | go-module-binary-cataloger |
| k8s.io/kubectl | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/kubernetes | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/metrics | UNKNOWN |  | go-module-binary-cataloger |
| k8s.io/utils | v0.0.0-20241104100929-3ea5e8cea738 |  | go-module-binary-cataloger |
| kubectl | 1.33.1-r5 | Apache-2.0 | apk-db-cataloger |
| libapk2 | 2.14.9-r2 | GPL-2.0-only | apk-db-cataloger |
| libcrypto3 | 3.5.5-r0 | Apache-2.0 | apk-db-cataloger |
| libncursesw | 6.5_p20250503-r0 | X11 | apk-db-cataloger |
| libssl3 | 3.5.5-r0 | Apache-2.0 | apk-db-cataloger |
| musl | 1.2.5-r10 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r10 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20250503-r0 | X11 | apk-db-cataloger |
| openssl | 3.5.5-r0 | Apache-2.0 | apk-db-cataloger |
| readline | 8.2.13-r1 | GPL-3.0-or-later | apk-db-cataloger |
| scanelf | 1.3.8-r1 | GPL-2.0-only | apk-db-cataloger |
| sigs.k8s.io/json | v0.0.0-20241010143419-9aa6b5e7a4b3 |  | go-module-binary-cataloger |
| sigs.k8s.io/kustomize/api | v0.19.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/kustomize/kustomize/v5 | v5.6.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/kustomize/kyaml | v0.19.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/randfill | v1.0.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/structured-merge-diff/v4 | v4.6.0 |  | go-module-binary-cataloger |
| sigs.k8s.io/yaml | v1.4.0 |  | go-module-binary-cataloger |
| ssl_client | 1.37.0-r18 | GPL-2.0-only | apk-db-cataloger |
| stdlib | go1.24.12 | BSD-3-Clause | go-module-binary-cataloger |
| zlib | 1.3.1-r2 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/elasticvue

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| alpine-baselayout | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.6.8-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.5-r0 | MIT | apk-db-cataloger |
| alpine-release | 3.21.3-r0 | MIT | apk-db-cataloger |
| aom-libs | 3.11.0-r0 | BSD-2-Clause | apk-db-cataloger |
| apk-tools | 2.14.6-r3 | GPL-2.0-only | apk-db-cataloger |
| brotli-libs | 1.1.0-r2 | MIT | apk-db-cataloger |
| busybox | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| c-ares | 1.34.5-r0 | MIT | apk-db-cataloger |
| ca-certificates | 20241121-r1 | MPL-2.0 AND MIT | apk-db-cataloger |
| ca-certificates-bundle | 20241121-r1 | MPL-2.0 AND MIT | apk-db-cataloger |
| curl | 8.12.1-r1 | curl | apk-db-cataloger |
| fontconfig | 2.15.0-r1 | MIT | apk-db-cataloger |
| freetype | 2.13.3-r0 | FTL OR GPL-2.0-or-later | apk-db-cataloger |
| geoip | 1.6.12-r5 | LGPL-2.1-or-later | apk-db-cataloger |
| gettext-envsubst | 0.22.5-r0 | GPL-3.0-or-later AND LGPL-2.1-or-later AND MIT | apk-db-cataloger |
| libavif | 1.0.4-r0 | BSD-2-Clause | apk-db-cataloger |
| libbsd | 0.12.2-r0 | BSD-3-Clause | apk-db-cataloger |
| libbz2 | 1.0.8-r6 | bzip2-1.0.6 | apk-db-cataloger |
| libcrypto3 | 3.3.3-r0 | Apache-2.0 | apk-db-cataloger |
| libcurl | 8.12.1-r1 | curl | apk-db-cataloger |
| libdav1d | 1.5.0-r0 | BSD-2-Clause | apk-db-cataloger |
| libedit | 20240808.3.1-r0 | BSD-3-Clause | apk-db-cataloger |
| libexpat | 2.7.0-r0 | MIT | apk-db-cataloger |
| libgcrypt | 1.10.3-r1 | LGPL-2.1-or-later AND GPL-2.0-or-later | apk-db-cataloger |
| libgd | 2.3.3-r9 | GD | apk-db-cataloger |
| libgpg-error | 1.51-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libice | 1.1.1-r6 | X11 | apk-db-cataloger |
| libidn2 | 2.3.7-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libintl | 0.22.5-r0 | LGPL-2.1-or-later | apk-db-cataloger |
| libjpeg-turbo | 3.0.4-r0 | BSD-3-Clause AND IJG AND Zlib | apk-db-cataloger |
| libmd | 1.1.0-r0 | BSD-2-Clause, BSD-3-Clause, Beerware, ISC | apk-db-cataloger |
| libncursesw | 6.5_p20241006-r3 | X11 | apk-db-cataloger |
| libpng | 1.6.47-r0 | Libpng | apk-db-cataloger |
| libpsl | 0.21.5-r3 | MIT | apk-db-cataloger |
| libsharpyuv | 1.4.0-r0 | BSD-3-Clause | apk-db-cataloger |
| libsm | 1.2.4-r4 | MIT | apk-db-cataloger |
| libssl3 | 3.3.3-r0 | Apache-2.0 | apk-db-cataloger |
| libunistring | 1.2-r0 | GPL-2.0-or-later OR LGPL-3.0-or-later | apk-db-cataloger |
| libuuid | 2.40.4-r1 | BSD-3-Clause | apk-db-cataloger |
| libwebp | 1.4.0-r0 | BSD-3-Clause | apk-db-cataloger |
| libx11 | 1.8.10-r0 | X11 | apk-db-cataloger |
| libxau | 1.0.11-r4 | MIT | apk-db-cataloger |
| libxcb | 1.16.1-r0 | MIT | apk-db-cataloger |
| libxdmcp | 1.1.5-r1 | MIT | apk-db-cataloger |
| libxext | 1.3.6-r2 | MIT | apk-db-cataloger |
| libxml2 | 2.13.4-r6 | MIT | apk-db-cataloger |
| libxpm | 3.5.17-r0 | X11 | apk-db-cataloger |
| libxslt | 1.1.42-r2 | X11 | apk-db-cataloger |
| libxt | 1.3.1-r0 | MIT | apk-db-cataloger |
| musl | 1.2.5-r9 | MIT | apk-db-cataloger |
| musl-utils | 1.2.5-r9 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| ncurses-terminfo-base | 6.5_p20241006-r3 | X11 | apk-db-cataloger |
| nghttp2-libs | 1.64.0-r0 | MIT | apk-db-cataloger |
| nginx | 1.27.5-r1 |  | apk-db-cataloger |
| nginx-module-geoip | 1.27.5-r1 |  | apk-db-cataloger |
| nginx-module-image-filter | 1.27.5-r1 |  | apk-db-cataloger |
| nginx-module-njs | 1.27.5.0.8.10-r1 |  | apk-db-cataloger |
| nginx-module-xslt | 1.27.5-r1 |  | apk-db-cataloger |
| pcre2 | 10.43-r0 | BSD-3-Clause | apk-db-cataloger |
| scanelf | 1.3.8-r1 | GPL-2.0-only | apk-db-cataloger |
| ssl_client | 1.37.0-r12 | GPL-2.0-only | apk-db-cataloger |
| tiff | 4.7.0-r0 | libtiff | apk-db-cataloger |
| tzdata | 2025b-r0 |  | apk-db-cataloger |
| xz-libs | 5.6.3-r1 | 0BSD, GPL-2.0-or-later, LGPL-2.1-or-later | apk-db-cataloger |
| zlib | 1.3.1-r2 | Zlib | apk-db-cataloger |
| zstd-libs | 1.5.6-r2 | BSD-3-Clause OR GPL-2.0-or-later | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/mongo-express

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| @ampproject/remapping | 2.2.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-crypto/ie11-detection | 2.0.2 | Apache-2.0 | javascript-package-cataloger |
| @aws-crypto/sha256-browser | 2.0.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-crypto/sha256-js | 2.0.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-crypto/sha256-js | 2.0.2 | Apache-2.0 | javascript-package-cataloger |
| @aws-crypto/supports-web-crypto | 2.0.2 | Apache-2.0 | javascript-package-cataloger |
| @aws-crypto/util | 2.0.2 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/abort-controller | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/client-cognito-identity | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/client-sso | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/client-sts | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/config-resolver | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-provider-cognito-identity | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-provider-env | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-provider-imds | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-provider-ini | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-provider-node | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-provider-process | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-provider-sso | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-provider-web-identity | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/credential-providers | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/fetch-http-handler | 3.204.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/hash-node | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/invalid-dependency | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/is-array-buffer | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-content-length | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-endpoint | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-host-header | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-logger | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-recursion-detection | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-retry | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-sdk-sts | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-serde | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-signing | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-stack | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/middleware-user-agent | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/node-config-provider | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/node-http-handler | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/property-provider | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/protocol-http | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/querystring-builder | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/querystring-parser | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/service-error-classification | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/shared-ini-file-loader | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/signature-v4 | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/smithy-client | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/types | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/url-parser | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-base64 | 3.202.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-base64-browser | 3.188.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-base64-node | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-body-length-browser | 3.188.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-body-length-node | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-buffer-from | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-config-provider | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-defaults-mode-browser | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-defaults-mode-node | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-endpoints | 3.202.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-hex-encoding | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-locate-window | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-middleware | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-uri-escape | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-user-agent-browser | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-user-agent-node | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-utf8-browser | 3.188.0 | Apache-2.0 | javascript-package-cataloger |
| @aws-sdk/util-utf8-node | 3.201.0 | Apache-2.0 | javascript-package-cataloger |
| @babel/code-frame | 7.18.6 | MIT | javascript-package-cataloger |
| @babel/compat-data | 7.19.4 | MIT | javascript-package-cataloger |
| @babel/core | 7.19.6 | MIT | javascript-package-cataloger |
| @babel/generator | 7.19.6 | MIT | javascript-package-cataloger |
| @babel/helper-compilation-targets | 7.19.3 | MIT | javascript-package-cataloger |
| @babel/helper-environment-visitor | 7.18.9 | MIT | javascript-package-cataloger |
| @babel/helper-function-name | 7.19.0 | MIT | javascript-package-cataloger |
| @babel/helper-hoist-variables | 7.18.6 | MIT | javascript-package-cataloger |
| @babel/helper-module-imports | 7.18.6 | MIT | javascript-package-cataloger |
| @babel/helper-module-transforms | 7.19.6 | MIT | javascript-package-cataloger |
| @babel/helper-simple-access | 7.19.4 | MIT | javascript-package-cataloger |
| @babel/helper-split-export-declaration | 7.18.6 | MIT | javascript-package-cataloger |
| @babel/helper-string-parser | 7.19.4 | MIT | javascript-package-cataloger |
| @babel/helper-validator-identifier | 7.19.1 | MIT | javascript-package-cataloger |
| @babel/helper-validator-option | 7.18.6 | MIT | javascript-package-cataloger |
| @babel/helpers | 7.19.4 | MIT | javascript-package-cataloger |
| @babel/highlight | 7.18.6 | MIT | javascript-package-cataloger |
| @babel/parser | 7.19.6 | MIT | javascript-package-cataloger |
| @babel/template | 7.18.10 | MIT | javascript-package-cataloger |
| @babel/traverse | 7.19.6 | MIT | javascript-package-cataloger |
| @babel/types | 7.19.4 | MIT | javascript-package-cataloger |
| @isaacs/cliui | 8.0.2 | ISC | javascript-package-cataloger |
| @isaacs/string-locale-compare | 1.1.0 | ISC | javascript-package-cataloger |
| @istanbuljs/load-nyc-config | 1.1.0 | ISC | javascript-package-cataloger |
| @istanbuljs/schema | 0.1.3 | MIT | javascript-package-cataloger |
| @jridgewell/gen-mapping | 0.1.1 | MIT | javascript-package-cataloger |
| @jridgewell/gen-mapping | 0.3.2 | MIT | javascript-package-cataloger |
| @jridgewell/resolve-uri | 3.1.0 | MIT | javascript-package-cataloger |
| @jridgewell/set-array | 1.1.2 | MIT | javascript-package-cataloger |
| @jridgewell/sourcemap-codec | 1.4.14 | MIT | javascript-package-cataloger |
| @jridgewell/trace-mapping | 0.3.14 | MIT | javascript-package-cataloger |
| @npmcli/agent | 2.2.2 | ISC | javascript-package-cataloger |
| @npmcli/arborist | 7.5.4 | ISC | javascript-package-cataloger |
| @npmcli/config | 8.3.4 | ISC | javascript-package-cataloger |
| @npmcli/fs | 3.1.1 | ISC | javascript-package-cataloger |
| @npmcli/git | 5.0.8 | ISC | javascript-package-cataloger |
| @npmcli/installed-package-contents | 2.1.0 | ISC | javascript-package-cataloger |
| @npmcli/map-workspaces | 3.0.6 | ISC | javascript-package-cataloger |
| @npmcli/metavuln-calculator | 7.1.1 | ISC | javascript-package-cataloger |
| @npmcli/name-from-folder | 2.0.0 | ISC | javascript-package-cataloger |
| @npmcli/node-gyp | 3.0.0 | ISC | javascript-package-cataloger |
| @npmcli/package-json | 5.2.0 | ISC | javascript-package-cataloger |
| @npmcli/promise-spawn | 7.0.2 | ISC | javascript-package-cataloger |
| @npmcli/query | 3.1.0 | ISC | javascript-package-cataloger |
| @npmcli/redact | 2.0.1 | ISC | javascript-package-cataloger |
| @npmcli/run-script | 8.1.0 | ISC | javascript-package-cataloger |
| @pkgjs/parseargs | 0.11.0 | MIT | javascript-package-cataloger |
| @sigstore/bundle | 2.3.2 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/core | 1.1.0 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/protobuf-specs | 0.3.2 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/sign | 2.3.2 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/tuf | 2.3.4 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/verify | 1.2.1 | Apache-2.0 | javascript-package-cataloger |
| @tufjs/canonical-json | 2.0.0 | MIT | javascript-package-cataloger |
| @tufjs/models | 2.0.1 | MIT | javascript-package-cataloger |
| @types/node | 14.18.30 | MIT | javascript-package-cataloger |
| @types/webidl-conversions | 6.1.1 | MIT | javascript-package-cataloger |
| @types/whatwg-url | 8.2.2 | MIT | javascript-package-cataloger |
| JSONStream | 1.3.5 | (MIT OR Apache-2.0) | javascript-package-cataloger |
| abbrev | 2.0.0 | ISC | javascript-package-cataloger |
| accepts | 1.3.8 | MIT | javascript-package-cataloger |
| acorn | 8.8.0 | MIT | javascript-package-cataloger |
| agent-base | 7.1.1 | MIT | javascript-package-cataloger |
| aggregate-error | 3.1.0 | MIT | javascript-package-cataloger |
| aggregate-error | 3.1.0 | MIT | javascript-package-cataloger |
| alpine-baselayout | 3.4.3-r2 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.4.3-r2 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.4-r1 | MIT | apk-db-cataloger |
| ansi-regex | 5.0.1 | MIT | javascript-package-cataloger |
| ansi-regex | 5.0.1 | MIT | javascript-package-cataloger |
| ansi-regex | 6.0.1 | MIT | javascript-package-cataloger |
| ansi-regex | 6.0.1 | MIT | javascript-package-cataloger |
| ansi-styles | 3.2.1 | MIT | javascript-package-cataloger |
| ansi-styles | 4.3.0 | MIT | javascript-package-cataloger |
| ansi-styles | 4.3.0 | MIT | javascript-package-cataloger |
| ansi-styles | 6.2.1 | MIT | javascript-package-cataloger |
| apk-tools | 2.14.4-r0 | GPL-2.0-only | apk-db-cataloger |
| append-transform | 2.0.0 | MIT | javascript-package-cataloger |
| aproba | 2.0.0 | ISC | javascript-package-cataloger |
| archy | 1.0.0 | MIT | javascript-package-cataloger |
| archy | 1.0.0 | MIT | javascript-package-cataloger |
| argparse | 1.0.10 | MIT | javascript-package-cataloger |
| array-flatten | 1.1.1 | MIT | javascript-package-cataloger |
| async | 3.2.4 | MIT | javascript-package-cataloger |
| balanced-match | 1.0.0 | MIT | javascript-package-cataloger |
| balanced-match | 1.0.2 | MIT | javascript-package-cataloger |
| base64-js | 1.3.1 | MIT | javascript-package-cataloger |
| bash | 5.2.21-r0 | GPL-3.0-or-later | apk-db-cataloger |
| basic-auth | 2.0.1 | MIT | javascript-package-cataloger |
| basic-auth-connect | 1.0.0 | MIT | javascript-package-cataloger |
| bin-links | 4.0.4 | ISC | javascript-package-cataloger |
| binary-extensions | 2.3.0 | MIT | javascript-package-cataloger |
| body-parser | 1.20.1 | MIT | javascript-package-cataloger |
| bootstrap-paginator | 1.0.2 | Apache-2.0 | javascript-package-cataloger |
| bowser | 2.11.0 | MIT | javascript-package-cataloger |
| brace-expansion | 1.1.11 | MIT | javascript-package-cataloger |
| brace-expansion | 2.0.1 | MIT | javascript-package-cataloger |
| browserslist | 4.21.3 | MIT | javascript-package-cataloger |
| bson | 1.1.5 | Apache-2.0 | javascript-package-cataloger |
| bson | 4.7.0 | Apache-2.0 | javascript-package-cataloger |
| bson | UNKNOWN |  | javascript-package-cataloger |
| buffer | 5.7.1 | MIT | javascript-package-cataloger |
| busboy | 1.6.0 | MIT | javascript-package-cataloger |
| busybox | 1.36.1-r19 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.36.1-r19 | GPL-2.0-only | apk-db-cataloger |
| bytes | 3.1.2 | MIT | javascript-package-cataloger |
| ca-certificates-bundle | 20240226-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| cacache | 18.0.3 | ISC | javascript-package-cataloger |
| caching-transform | 4.0.0 | MIT | javascript-package-cataloger |
| call-bind | 1.0.2 | MIT | javascript-package-cataloger |
| camelcase | 5.3.1 | MIT | javascript-package-cataloger |
| caniuse-lite | 1.0.30001400 | CC-BY-4.0 | javascript-package-cataloger |
| chalk | 2.4.2 | MIT | javascript-package-cataloger |
| chalk | 5.3.0 | MIT | javascript-package-cataloger |
| chownr | 2.0.0 | ISC | javascript-package-cataloger |
| ci-info | 4.0.0 | MIT | javascript-package-cataloger |
| cidr-regex | 4.1.1 | BSD-2-Clause | javascript-package-cataloger |
| clean-stack | 2.2.0 | MIT | javascript-package-cataloger |
| clean-stack | 2.2.0 | MIT | javascript-package-cataloger |
| cli-color | 2.0.3 | ISC | javascript-package-cataloger |
| cli-columns | 4.0.0 | MIT | javascript-package-cataloger |
| cliui | 6.0.0 | ISC | javascript-package-cataloger |
| cliui | 7.0.4 | ISC | javascript-package-cataloger |
| cmd-shim | 6.0.3 | ISC | javascript-package-cataloger |
| color-convert | 1.9.3 | MIT | javascript-package-cataloger |
| color-convert | 2.0.1 | MIT | javascript-package-cataloger |
| color-convert | 2.0.1 | MIT | javascript-package-cataloger |
| color-name | 1.1.3 | MIT | javascript-package-cataloger |
| color-name | 1.1.4 | MIT | javascript-package-cataloger |
| color-name | 1.1.4 | MIT | javascript-package-cataloger |
| commander | 2.20.3 | MIT | javascript-package-cataloger |
| commander | 6.2.1 | MIT | javascript-package-cataloger |
| common-ancestor-path | 1.0.1 | ISC | javascript-package-cataloger |
| commondir | 1.0.1 | MIT | javascript-package-cataloger |
| concat-map | 0.0.1 | MIT | javascript-package-cataloger |
| content-disposition | 0.5.4 | MIT | javascript-package-cataloger |
| content-type | 1.0.4 | MIT | javascript-package-cataloger |
| convert-source-map | 1.7.0 | MIT | javascript-package-cataloger |
| cookie | 0.4.0 | MIT | javascript-package-cataloger |
| cookie | 0.4.1 | MIT | javascript-package-cataloger |
| cookie | 0.4.2 | MIT | javascript-package-cataloger |
| cookie | 0.5.0 | MIT | javascript-package-cataloger |
| cookie-parser | 1.4.6 | MIT | javascript-package-cataloger |
| cookie-signature | 1.0.6 | MIT | javascript-package-cataloger |
| corepack | 0.29.4 | MIT | javascript-package-cataloger |
| cross-spawn | 7.0.3 | MIT | javascript-package-cataloger |
| cross-spawn | 7.0.3 | MIT | javascript-package-cataloger |
| csrf | 3.1.0 | MIT | javascript-package-cataloger |
| cssesc | 3.0.0 | MIT | javascript-package-cataloger |
| csurf | 1.11.0 | MIT | javascript-package-cataloger |
| d | 1.0.1 | ISC | javascript-package-cataloger |
| debug | 2.6.9 | MIT | javascript-package-cataloger |
| debug | 3.1.0 | MIT | javascript-package-cataloger |
| debug | 4.3.4 | MIT | javascript-package-cataloger |
| debug | 4.3.5 | MIT | javascript-package-cataloger |
| decamelize | 1.2.0 | MIT | javascript-package-cataloger |
| default-require-extensions | 3.0.0 | MIT | javascript-package-cataloger |
| depd | 1.1.2 | MIT | javascript-package-cataloger |
| depd | 2.0.0 | MIT | javascript-package-cataloger |
| destroy | 1.2.0 | MIT | javascript-package-cataloger |
| diff | 5.2.0 | BSD-3-Clause | javascript-package-cataloger |
| dotenv | 16.0.3 | BSD-2-Clause | javascript-package-cataloger |
| duplexer | 0.1.2 | MIT | javascript-package-cataloger |
| eastasianwidth | 0.2.0 | MIT | javascript-package-cataloger |
| ee-first | 1.1.1 | MIT | javascript-package-cataloger |
| ejson-shell-parser | 1.1.3 | MIT | javascript-package-cataloger |
| electron-to-chromium | 1.4.228 | ISC | javascript-package-cataloger |
| emoji-regex | 8.0.0 | MIT | javascript-package-cataloger |
| emoji-regex | 8.0.0 | MIT | javascript-package-cataloger |
| emoji-regex | 9.2.2 | MIT | javascript-package-cataloger |
| emoji-regex | 9.2.2 | MIT | javascript-package-cataloger |
| encodeurl | 1.0.2 | MIT | javascript-package-cataloger |
| encoding | 0.1.13 | MIT | javascript-package-cataloger |
| env-paths | 2.2.1 | MIT | javascript-package-cataloger |
| err-code | 2.0.3 | MIT | javascript-package-cataloger |
| errorhandler | 1.5.1 | MIT | javascript-package-cataloger |
| es5-ext | 0.10.62 | ISC | javascript-package-cataloger |
| es6-error | 4.1.1 | MIT | javascript-package-cataloger |
| es6-iterator | 2.0.3 | MIT | javascript-package-cataloger |
| es6-symbol | 3.1.3 | ISC | javascript-package-cataloger |
| es6-weak-map | 2.0.3 | ISC | javascript-package-cataloger |
| escalade | 3.1.1 | MIT | javascript-package-cataloger |
| escape-html | 1.0.3 | MIT | javascript-package-cataloger |
| escape-string-regexp | 1.0.5 | MIT | javascript-package-cataloger |
| esprima | 4.0.1 | BSD-2-Clause | javascript-package-cataloger |
| etag | 1.8.1 | MIT | javascript-package-cataloger |
| event-emitter | 0.3.5 | MIT | javascript-package-cataloger |
| event-stream | 4.0.1 | MIT | javascript-package-cataloger |
| exponential-backoff | 3.1.1 | Apache-2.0 | javascript-package-cataloger |
| express | 4.18.2 | MIT | javascript-package-cataloger |
| express-fileupload | 1.4.0 | MIT | javascript-package-cataloger |
| express-session | 1.17.3 | MIT | javascript-package-cataloger |
| ext | 1.4.0 | ISC | javascript-package-cataloger |
| fast-xml-parser | 4.0.11 | MIT | javascript-package-cataloger |
| fastest-levenshtein | 1.0.16 | MIT | javascript-package-cataloger |
| finalhandler | 1.2.0 | MIT | javascript-package-cataloger |
| find-cache-dir | 3.3.2 | MIT | javascript-package-cataloger |
| find-up | 4.1.0 | MIT | javascript-package-cataloger |
| flat | 5.0.2 | BSD-3-Clause | javascript-package-cataloger |
| flushwritable | 1.0.0 | MIT | javascript-package-cataloger |
| foreground-child | 2.0.0 | ISC | javascript-package-cataloger |
| foreground-child | 3.2.1 | ISC | javascript-package-cataloger |
| forwarded | 0.2.0 | MIT | javascript-package-cataloger |
| free-swig | 1.5.2 | MIT | javascript-package-cataloger |
| fresh | 0.5.2 | MIT | javascript-package-cataloger |
| from | 0.1.7 | MIT | javascript-package-cataloger |
| fromentries | 1.3.2 | MIT | javascript-package-cataloger |
| fs-minipass | 2.1.0 | ISC | javascript-package-cataloger |
| fs-minipass | 3.0.3 | ISC | javascript-package-cataloger |
| fs.realpath | 1.0.0 | ISC | javascript-package-cataloger |
| function-bind | 1.1.1 | MIT | javascript-package-cataloger |
| gensync | 1.0.0-beta.2 | MIT | javascript-package-cataloger |
| get-caller-file | 2.0.5 | ISC | javascript-package-cataloger |
| get-intrinsic | 1.1.2 | MIT | javascript-package-cataloger |
| get-package-type | 0.1.0 | MIT | javascript-package-cataloger |
| glob | 10.4.2 | ISC | javascript-package-cataloger |
| glob | 7.2.3 | ISC | javascript-package-cataloger |
| globals | 11.12.0 | MIT | javascript-package-cataloger |
| graceful-fs | 4.2.10 | ISC | javascript-package-cataloger |
| graceful-fs | 4.2.11 | ISC | javascript-package-cataloger |
| gridfs-stream | 1.1.1 | MIT | javascript-package-cataloger |
| has | 1.0.3 | MIT | javascript-package-cataloger |
| has-flag | 3.0.0 | MIT | javascript-package-cataloger |
| has-flag | 4.0.0 | MIT | javascript-package-cataloger |
| has-symbols | 1.0.3 | MIT | javascript-package-cataloger |
| hasha | 5.2.2 | MIT | javascript-package-cataloger |
| hosted-git-info | 7.0.2 | ISC | javascript-package-cataloger |
| html-entities | 2.3.3 | MIT | javascript-package-cataloger |
| html-escaper | 2.0.2 | MIT | javascript-package-cataloger |
| http-cache-semantics | 4.1.1 | BSD-2-Clause | javascript-package-cataloger |
| http-errors | 1.7.3 | MIT | javascript-package-cataloger |
| http-errors | 2.0.0 | MIT | javascript-package-cataloger |
| http-proxy-agent | 7.0.2 | MIT | javascript-package-cataloger |
| https-proxy-agent | 7.0.5 | MIT | javascript-package-cataloger |
| iconv-lite | 0.4.24 | MIT | javascript-package-cataloger |
| iconv-lite | 0.6.3 | MIT | javascript-package-cataloger |
| ieee754 | 1.1.13 | BSD-3-Clause | javascript-package-cataloger |
| ignore-walk | 6.0.5 | ISC | javascript-package-cataloger |
| imurmurhash | 0.1.4 | MIT | javascript-package-cataloger |
| imurmurhash | 0.1.4 | MIT | javascript-package-cataloger |
| indent-string | 4.0.0 | MIT | javascript-package-cataloger |
| indent-string | 4.0.0 | MIT | javascript-package-cataloger |
| inflight | 1.0.6 | ISC | javascript-package-cataloger |
| inherits | 2.0.4 | ISC | javascript-package-cataloger |
| ini | 4.1.3 | ISC | javascript-package-cataloger |
| init-package-json | 6.0.3 | ISC | javascript-package-cataloger |
| ip | 2.0.0 | MIT | javascript-package-cataloger |
| ip-address | 9.0.5 | MIT | javascript-package-cataloger |
| ip-regex | 5.0.0 | MIT | javascript-package-cataloger |
| ipaddr.js | 1.9.1 | MIT | javascript-package-cataloger |
| is-cidr | 5.1.0 | BSD-2-Clause | javascript-package-cataloger |
| is-fullwidth-code-point | 3.0.0 | MIT | javascript-package-cataloger |
| is-fullwidth-code-point | 3.0.0 | MIT | javascript-package-cataloger |
| is-json | 2.0.1 | ISC | javascript-package-cataloger |
| is-lambda | 1.0.1 | MIT | javascript-package-cataloger |
| is-promise | 2.2.2 | MIT | javascript-package-cataloger |
| is-stream | 2.0.1 | MIT | javascript-package-cataloger |
| is-typedarray | 1.0.0 | MIT | javascript-package-cataloger |
| is-windows | 1.0.2 | MIT | javascript-package-cataloger |
| isexe | 2.0.0 | ISC | javascript-package-cataloger |
| isexe | 2.0.0 | ISC | javascript-package-cataloger |
| isexe | 3.1.1 | ISC | javascript-package-cataloger |
| istanbul-lib-coverage | 3.2.0 | BSD-3-Clause | javascript-package-cataloger |
| istanbul-lib-hook | 3.0.0 | BSD-3-Clause | javascript-package-cataloger |
| istanbul-lib-instrument | 4.0.3 | BSD-3-Clause | javascript-package-cataloger |
| istanbul-lib-processinfo | 2.0.3 | ISC | javascript-package-cataloger |
| istanbul-lib-report | 3.0.0 | BSD-3-Clause | javascript-package-cataloger |
| istanbul-lib-source-maps | 4.0.1 | BSD-3-Clause | javascript-package-cataloger |
| istanbul-reports | 3.1.5 | BSD-3-Clause | javascript-package-cataloger |
| jackspeak | 3.4.0 | BlueOak-1.0.0 | javascript-package-cataloger |
| javascript-stringify | 2.0.1 | MIT | javascript-package-cataloger |
| js-tokens | 4.0.0 | MIT | javascript-package-cataloger |
| js-yaml | 3.14.1 | MIT | javascript-package-cataloger |
| jsbn | 1.1.0 | MIT | javascript-package-cataloger |
| jsesc | 2.5.2 | MIT | javascript-package-cataloger |
| json-parse-even-better-errors | 3.0.2 | MIT | javascript-package-cataloger |
| json-stringify-nice | 1.1.4 | ISC | javascript-package-cataloger |
| json2csv | 5.0.7 | MIT | javascript-package-cataloger |
| json5 | 2.2.1 | MIT | javascript-package-cataloger |
| jsonparse | 1.3.1 | MIT | javascript-package-cataloger |
| jsonparse | 1.3.1 | MIT | javascript-package-cataloger |
| just-diff | 6.0.2 | MIT | javascript-package-cataloger |
| just-diff-apply | 5.5.0 | MIT | javascript-package-cataloger |
| libc-utils | 0.7.2-r5 | BSD-2-Clause AND BSD-3-Clause | apk-db-cataloger |
| libcrypto3 | 3.1.7-r0 | Apache-2.0 | apk-db-cataloger |
| libgcc | 13.2.1_git20231014-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libncursesw | 6.4_p20231125-r0 | X11 | apk-db-cataloger |
| libnpmaccess | 8.0.6 | ISC | javascript-package-cataloger |
| libnpmdiff | 6.1.4 | ISC | javascript-package-cataloger |
| libnpmexec | 8.1.3 | ISC | javascript-package-cataloger |
| libnpmfund | 5.0.12 | ISC | javascript-package-cataloger |
| libnpmhook | 10.0.5 | ISC | javascript-package-cataloger |
| libnpmorg | 6.0.6 | ISC | javascript-package-cataloger |
| libnpmpack | 7.0.4 | ISC | javascript-package-cataloger |
| libnpmpublish | 9.0.9 | ISC | javascript-package-cataloger |
| libnpmsearch | 7.0.6 | ISC | javascript-package-cataloger |
| libnpmteam | 6.0.5 | ISC | javascript-package-cataloger |
| libnpmversion | 6.0.3 | ISC | javascript-package-cataloger |
| libssl3 | 3.1.7-r0 | Apache-2.0 | apk-db-cataloger |
| libstdc++ | 13.2.1_git20231014-r0 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| locate-path | 5.0.0 | MIT | javascript-package-cataloger |
| lodash | 4.17.21 | MIT | javascript-package-cataloger |
| lodash-es | 4.17.21 | MIT | javascript-package-cataloger |
| lodash.flattendeep | 4.4.0 | MIT | javascript-package-cataloger |
| lodash.get | 4.4.2 | MIT | javascript-package-cataloger |
| lodash.isfunction | 3.0.9 | MIT | javascript-package-cataloger |
| lodash.transform | 4.6.0 | MIT | javascript-package-cataloger |
| lru-cache | 10.2.2 | ISC | javascript-package-cataloger |
| lru-cache | 4.1.5 | ISC | javascript-package-cataloger |
| lru-cache | 5.1.1 | ISC | javascript-package-cataloger |
| lru-queue | 0.1.0 | MIT | javascript-package-cataloger |
| make-dir | 3.1.0 | MIT | javascript-package-cataloger |
| make-fetch-happen | 13.0.1 | ISC | javascript-package-cataloger |
| map-stream | 0.0.7 | MIT | javascript-package-cataloger |
| media-typer | 0.3.0 | MIT | javascript-package-cataloger |
| memoizee | 0.4.15 | ISC | javascript-package-cataloger |
| memory-pager | 1.5.0 | MIT | javascript-package-cataloger |
| memorystore | 1.6.7 | MIT | javascript-package-cataloger |
| merge-descriptors | 1.0.1 | MIT | javascript-package-cataloger |
| method-override | 3.0.0 | MIT | javascript-package-cataloger |
| methods | 1.1.2 | MIT | javascript-package-cataloger |
| mime | 1.6.0 | MIT | javascript-package-cataloger |
| mime-db | 1.52.0 | MIT | javascript-package-cataloger |
| mime-types | 2.1.35 | MIT | javascript-package-cataloger |
| minimatch | 3.1.2 | ISC | javascript-package-cataloger |
| minimatch | 9.0.5 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 5.0.0 | ISC | javascript-package-cataloger |
| minipass | 7.1.2 | ISC | javascript-package-cataloger |
| minipass-collect | 2.0.1 | ISC | javascript-package-cataloger |
| minipass-fetch | 3.0.5 | MIT | javascript-package-cataloger |
| minipass-flush | 1.0.5 | ISC | javascript-package-cataloger |
| minipass-pipeline | 1.2.4 | ISC | javascript-package-cataloger |
| minipass-sized | 1.0.3 | ISC | javascript-package-cataloger |
| minizlib | 2.1.2 | MIT | javascript-package-cataloger |
| mkdirp | 1.0.4 | MIT | javascript-package-cataloger |
| moment | 2.29.4 | MIT | javascript-package-cataloger |
| mongo-express | 1.0.2 | MIT | javascript-package-cataloger |
| mongodb | 4.13.0 | Apache-2.0 | javascript-package-cataloger |
| mongodb-connection-string-url | 2.5.4 | Apache-2.0 | javascript-package-cataloger |
| mongodb-extended-json | 1.11.0 | Apache-2.0 | javascript-package-cataloger |
| mongodb-language-model | 1.6.1 | Apache-2.0 | javascript-package-cataloger |
| mongodb-query-parser | 2.4.6 | Apache-2.0 | javascript-package-cataloger |
| morgan | 1.10.0 | MIT | javascript-package-cataloger |
| ms | 2.0.0 | MIT | javascript-package-cataloger |
| ms | 2.1.1 | MIT | javascript-package-cataloger |
| ms | 2.1.2 | MIT | javascript-package-cataloger |
| ms | 2.1.2 | MIT | javascript-package-cataloger |
| ms | 2.1.3 | MIT | javascript-package-cataloger |
| ms | 2.1.3 | MIT | javascript-package-cataloger |
| musl | 1.2.4_git20230717-r4 | MIT | apk-db-cataloger |
| musl-utils | 1.2.4_git20230717-r4 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| mute-stream | 1.0.0 | ISC | javascript-package-cataloger |
| ncurses-terminfo-base | 6.4_p20231125-r0 | X11 | apk-db-cataloger |
| negotiator | 0.6.3 | MIT | javascript-package-cataloger |
| negotiator | 0.6.3 | MIT | javascript-package-cataloger |
| next-tick | 1.0.0 | MIT | javascript-package-cataloger |
| next-tick | 1.1.0 | ISC | javascript-package-cataloger |
| node | 20.18.1 |  | binary-classifier-cataloger |
| node-gyp | 10.1.0 | MIT | javascript-package-cataloger |
| node-preload | 0.2.1 | MIT | javascript-package-cataloger |
| node-releases | 2.0.6 | MIT | javascript-package-cataloger |
| nopt | 7.2.1 | ISC | javascript-package-cataloger |
| normalize-package-data | 6.0.2 | BSD-2-Clause | javascript-package-cataloger |
| npm | 10.8.2 | Artistic-2.0 | javascript-package-cataloger |
| npm-audit-report | 5.0.0 | ISC | javascript-package-cataloger |
| npm-bundled | 3.0.1 | ISC | javascript-package-cataloger |
| npm-install-checks | 6.3.0 | BSD-2-Clause | javascript-package-cataloger |
| npm-normalize-package-bin | 3.0.1 | ISC | javascript-package-cataloger |
| npm-package-arg | 11.0.2 | ISC | javascript-package-cataloger |
| npm-packlist | 8.0.2 | ISC | javascript-package-cataloger |
| npm-pick-manifest | 9.1.0 | ISC | javascript-package-cataloger |
| npm-profile | 10.0.0 | ISC | javascript-package-cataloger |
| npm-registry-fetch | 17.1.0 | ISC | javascript-package-cataloger |
| npm-user-validate | 2.0.1 | BSD-2-Clause | javascript-package-cataloger |
| nyc | 15.1.0 | ISC | javascript-package-cataloger |
| object-inspect | 1.12.2 | MIT | javascript-package-cataloger |
| on-finished | 2.3.0 | MIT | javascript-package-cataloger |
| on-finished | 2.4.1 | MIT | javascript-package-cataloger |
| on-headers | 1.0.2 | MIT | javascript-package-cataloger |
| once | 1.4.0 | ISC | javascript-package-cataloger |
| p-limit | 2.3.0 | MIT | javascript-package-cataloger |
| p-locate | 4.1.0 | MIT | javascript-package-cataloger |
| p-map | 3.0.0 | MIT | javascript-package-cataloger |
| p-map | 4.0.0 | MIT | javascript-package-cataloger |
| p-try | 2.2.0 | MIT | javascript-package-cataloger |
| package-hash | 4.0.0 | ISC | javascript-package-cataloger |
| package-json-from-dist | 1.0.0 | BlueOak-1.0.0 | javascript-package-cataloger |
| pacote | 18.0.6 | ISC | javascript-package-cataloger |
| parse-conflict-json | 3.0.1 | ISC | javascript-package-cataloger |
| parseurl | 1.3.3 | MIT | javascript-package-cataloger |
| path-exists | 4.0.0 | MIT | javascript-package-cataloger |
| path-is-absolute | 1.0.1 | MIT | javascript-package-cataloger |
| path-key | 3.1.1 | MIT | javascript-package-cataloger |
| path-key | 3.1.1 | MIT | javascript-package-cataloger |
| path-scurry | 1.11.1 | BlueOak-1.0.0 | javascript-package-cataloger |
| path-to-regexp | 0.1.7 | MIT | javascript-package-cataloger |
| pause-stream | 0.0.11 | Apache-2.0, MIT | javascript-package-cataloger |
| performance-now | 2.1.0 | MIT | javascript-package-cataloger |
| picocolors | 1.0.0 | ISC | javascript-package-cataloger |
| pkg-dir | 4.2.0 | MIT | javascript-package-cataloger |
| postcss-selector-parser | 6.1.0 | MIT | javascript-package-cataloger |
| proc-log | 3.0.0 | ISC | javascript-package-cataloger |
| proc-log | 4.2.0 | ISC | javascript-package-cataloger |
| process-on-spawn | 1.0.0 | MIT | javascript-package-cataloger |
| proggy | 2.0.0 | ISC | javascript-package-cataloger |
| promise-all-reject-late | 1.0.1 | ISC | javascript-package-cataloger |
| promise-call-limit | 3.0.1 | ISC | javascript-package-cataloger |
| promise-inflight | 1.0.1 | ISC | javascript-package-cataloger |
| promise-retry | 2.0.1 | MIT | javascript-package-cataloger |
| promzard | 1.0.2 | ISC | javascript-package-cataloger |
| proxy-addr | 2.0.7 | MIT | javascript-package-cataloger |
| pseudomap | 1.0.2 | ISC | javascript-package-cataloger |
| punycode | 2.1.1 | MIT | javascript-package-cataloger |
| qrcode-terminal | 0.12.0 |  | javascript-package-cataloger |
| qs | 6.11.0 | BSD-3-Clause | javascript-package-cataloger |
| raf | 3.4.1 | MIT | javascript-package-cataloger |
| random-bytes | 1.0.0 | MIT | javascript-package-cataloger |
| range-parser | 1.2.1 | MIT | javascript-package-cataloger |
| raw-body | 2.5.1 | MIT | javascript-package-cataloger |
| read | 3.0.1 | ISC | javascript-package-cataloger |
| read-cmd-shim | 4.0.0 | ISC | javascript-package-cataloger |
| read-package-json-fast | 3.0.2 | ISC | javascript-package-cataloger |
| readline | 8.2.1-r2 | GPL-2.0-or-later | apk-db-cataloger |
| release-zalgo | 1.0.0 | ISC | javascript-package-cataloger |
| require-directory | 2.1.1 | MIT | javascript-package-cataloger |
| require-main-filename | 2.0.0 | ISC | javascript-package-cataloger |
| resolve-from | 5.0.0 | MIT | javascript-package-cataloger |
| retry | 0.12.0 | MIT | javascript-package-cataloger |
| rimraf | 3.0.2 | ISC | javascript-package-cataloger |
| rndm | 1.2.0 | MIT | javascript-package-cataloger |
| safe-buffer | 5.1.1 | MIT | javascript-package-cataloger |
| safe-buffer | 5.1.2 | MIT | javascript-package-cataloger |
| safe-buffer | 5.2.1 | MIT | javascript-package-cataloger |
| safer-buffer | 2.1.2 | MIT | javascript-package-cataloger |
| safer-buffer | 2.1.2 | MIT | javascript-package-cataloger |
| saslprep | 1.0.3 | MIT | javascript-package-cataloger |
| scanelf | 1.3.7-r2 | GPL-2.0-only | apk-db-cataloger |
| semver | 6.3.0 | ISC | javascript-package-cataloger |
| semver | 7.6.2 | ISC | javascript-package-cataloger |
| send | 0.18.0 | MIT | javascript-package-cataloger |
| serve-favicon | 2.5.0 | MIT | javascript-package-cataloger |
| serve-static | 1.15.0 | MIT | javascript-package-cataloger |
| set-blocking | 2.0.0 | ISC | javascript-package-cataloger |
| setprototypeof | 1.1.1 | ISC | javascript-package-cataloger |
| setprototypeof | 1.2.0 | ISC | javascript-package-cataloger |
| shebang-command | 2.0.0 | MIT | javascript-package-cataloger |
| shebang-command | 2.0.0 | MIT | javascript-package-cataloger |
| shebang-regex | 3.0.0 | MIT | javascript-package-cataloger |
| shebang-regex | 3.0.0 | MIT | javascript-package-cataloger |
| side-channel | 1.0.4 | MIT | javascript-package-cataloger |
| signal-exit | 3.0.7 | ISC | javascript-package-cataloger |
| signal-exit | 4.1.0 | ISC | javascript-package-cataloger |
| sigstore | 2.3.1 | Apache-2.0 | javascript-package-cataloger |
| smart-buffer | 4.2.0 | MIT | javascript-package-cataloger |
| smart-buffer | 4.2.0 | MIT | javascript-package-cataloger |
| socks | 2.7.1 | MIT | javascript-package-cataloger |
| socks | 2.8.3 | MIT | javascript-package-cataloger |
| socks-proxy-agent | 8.0.4 | MIT | javascript-package-cataloger |
| source-map | 0.6.1 | BSD-3-Clause | javascript-package-cataloger |
| sparse-bitfield | 3.0.3 | MIT | javascript-package-cataloger |
| spawn-wrap | 2.0.0 | ISC | javascript-package-cataloger |
| spdx-correct | 3.2.0 | Apache-2.0 | javascript-package-cataloger |
| spdx-exceptions | 2.5.0 | CC-BY-3.0 | javascript-package-cataloger |
| spdx-expression-parse | 3.0.1 | MIT | javascript-package-cataloger |
| spdx-expression-parse | 3.0.1 | MIT | javascript-package-cataloger |
| spdx-expression-parse | 4.0.0 | MIT | javascript-package-cataloger |
| spdx-license-ids | 3.0.18 | CC0-1.0 | javascript-package-cataloger |
| split | 1.0.1 | MIT | javascript-package-cataloger |
| sprintf-js | 1.0.3 | BSD-3-Clause | javascript-package-cataloger |
| sprintf-js | 1.1.3 | BSD-3-Clause | javascript-package-cataloger |
| ssl_client | 1.36.1-r19 | GPL-2.0-only | apk-db-cataloger |
| ssri | 10.0.6 | ISC | javascript-package-cataloger |
| statuses | 1.5.0 | MIT | javascript-package-cataloger |
| statuses | 2.0.1 | MIT | javascript-package-cataloger |
| stream-combiner | 0.2.2 | MIT | javascript-package-cataloger |
| streamsearch | 1.1.0 | MIT | javascript-package-cataloger |
| string-width | 4.2.0 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 5.1.2 | MIT | javascript-package-cataloger |
| string-width | 5.1.2 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 7.1.0 | MIT | javascript-package-cataloger |
| strip-ansi | 7.1.0 | MIT | javascript-package-cataloger |
| strip-bom | 4.0.0 | MIT | javascript-package-cataloger |
| strnum | 1.0.5 | MIT | javascript-package-cataloger |
| supports-color | 5.5.0 | MIT | javascript-package-cataloger |
| supports-color | 7.2.0 | MIT | javascript-package-cataloger |
| supports-color | 9.4.0 | MIT | javascript-package-cataloger |
| tar | 6.2.1 | ISC | javascript-package-cataloger |
| test-exclude | 6.0.0 | ISC | javascript-package-cataloger |
| text-table | 0.2.0 | MIT | javascript-package-cataloger |
| through | 2.3.8 | MIT | javascript-package-cataloger |
| timers-ext | 0.1.7 | ISC | javascript-package-cataloger |
| tini | 0.19.0-r2 | MIT | apk-db-cataloger |
| tiny-relative-date | 1.3.0 | MIT | javascript-package-cataloger |
| to-fast-properties | 2.0.0 | MIT | javascript-package-cataloger |
| toidentifier | 1.0.0 | MIT | javascript-package-cataloger |
| toidentifier | 1.0.1 | MIT | javascript-package-cataloger |
| tr46 | 3.0.0 | MIT | javascript-package-cataloger |
| treeverse | 3.0.0 | ISC | javascript-package-cataloger |
| tslib | 1.14.1 | 0BSD | javascript-package-cataloger |
| tslib | 2.4.0 | 0BSD | javascript-package-cataloger |
| tsscmp | 1.0.6 | MIT | javascript-package-cataloger |
| tuf-js | 2.2.1 | MIT | javascript-package-cataloger |
| type | 1.2.0 | ISC | javascript-package-cataloger |
| type | 2.1.0 | ISC | javascript-package-cataloger |
| type-fest | 0.8.1 | (MIT OR CC0-1.0) | javascript-package-cataloger |
| type-is | 1.6.18 | MIT | javascript-package-cataloger |
| typedarray-to-buffer | 3.1.5 | MIT | javascript-package-cataloger |
| uglify-js | 3.15.5 | BSD-2-Clause | javascript-package-cataloger |
| uid-safe | 2.1.5 | MIT | javascript-package-cataloger |
| unique-filename | 3.0.0 | ISC | javascript-package-cataloger |
| unique-slug | 4.0.0 | ISC | javascript-package-cataloger |
| unpipe | 1.0.0 | MIT | javascript-package-cataloger |
| update-browserslist-db | 1.0.5 | MIT | javascript-package-cataloger |
| util-deprecate | 1.0.2 | MIT | javascript-package-cataloger |
| utils-merge | 1.0.1 | MIT | javascript-package-cataloger |
| uuid | 8.3.2 | MIT | javascript-package-cataloger |
| validate-npm-package-license | 3.0.4 | Apache-2.0 | javascript-package-cataloger |
| validate-npm-package-name | 5.0.1 | ISC | javascript-package-cataloger |
| vary | 1.1.2 | MIT | javascript-package-cataloger |
| walk-up-path | 3.0.1 | ISC | javascript-package-cataloger |
| webidl-conversions | 7.0.0 | BSD-2-Clause | javascript-package-cataloger |
| whatwg-url | 11.0.0 | MIT | javascript-package-cataloger |
| which | 2.0.2 | ISC | javascript-package-cataloger |
| which | 2.0.2 | ISC | javascript-package-cataloger |
| which | 4.0.0 | ISC | javascript-package-cataloger |
| which-module | 2.0.0 | ISC | javascript-package-cataloger |
| wrap-ansi | 6.2.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 7.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 7.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 8.1.0 | MIT | javascript-package-cataloger |
| wrappy | 1.0.2 | ISC | javascript-package-cataloger |
| write-file-atomic | 3.0.3 | ISC | javascript-package-cataloger |
| write-file-atomic | 5.0.1 | ISC | javascript-package-cataloger |
| y18n | 4.0.3 | ISC | javascript-package-cataloger |
| y18n | 5.0.8 | ISC | javascript-package-cataloger |
| yallist | 2.1.2 | ISC | javascript-package-cataloger |
| yallist | 3.0.2 | ISC | javascript-package-cataloger |
| yallist | 4.0.0 | ISC | javascript-package-cataloger |
| yargs | 15.4.1 | MIT | javascript-package-cataloger |
| yargs | 17.5.1 | MIT | javascript-package-cataloger |
| yargs-parser | 18.1.3 | ISC | javascript-package-cataloger |
| yargs-parser | 21.1.1 | ISC | javascript-package-cataloger |
| yarn | 1.22.22 | BSD-2-Clause | javascript-package-cataloger |
| zlib | 1.3.1-r0 | Zlib | apk-db-cataloger |

### registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/redisinsight

| Package | Version | License | Found by |
| ------- | --------| ------- | -------- |
| 1to2 | 1.0.0 | MIT | javascript-package-cataloger |
| 1to2 | 1.0.0 | MIT | javascript-package-cataloger |
| @babel/runtime | 7.22.5 | MIT | javascript-package-cataloger |
| @colors/colors | 1.5.0 | MIT | javascript-package-cataloger |
| @colors/colors | 1.5.0 | MIT | javascript-package-cataloger |
| @dabh/diagnostics | 2.0.3 | MIT | javascript-package-cataloger |
| @gar/promisify | 1.1.3 | MIT | javascript-package-cataloger |
| @glideapps/ts-necessities | 2.1.3 | MIT | javascript-package-cataloger |
| @ioredis/commands | 1.2.0 | MIT | javascript-package-cataloger |
| @isaacs/cliui | 8.0.2 | ISC | javascript-package-cataloger |
| @isaacs/string-locale-compare | 1.1.0 | ISC | javascript-package-cataloger |
| @lukeed/csprng | 1.1.0 | MIT | javascript-package-cataloger |
| @lukeed/uuid | 2.0.1 | MIT | javascript-package-cataloger |
| @mapbox/node-pre-gyp | 1.0.11 | BSD-3-Clause | javascript-package-cataloger |
| @microsoft/tsdoc | 0.14.2 | MIT | javascript-package-cataloger |
| @nestjs/common | 10.3.7 | MIT | javascript-package-cataloger |
| @nestjs/core | 10.3.7 | MIT | javascript-package-cataloger |
| @nestjs/event-emitter | 2.0.4 | MIT | javascript-package-cataloger |
| @nestjs/mapped-types | 2.0.5 | MIT | javascript-package-cataloger |
| @nestjs/platform-express | 10.3.7 | MIT | javascript-package-cataloger |
| @nestjs/platform-socket.io | 10.3.7 | MIT | javascript-package-cataloger |
| @nestjs/serve-static | 3.0.1 | MIT | javascript-package-cataloger |
| @nestjs/swagger | 7.3.1 | MIT | javascript-package-cataloger |
| @nestjs/typeorm | 9.0.1 | MIT | javascript-package-cataloger |
| @nestjs/websockets | 10.3.7 | MIT | javascript-package-cataloger |
| @npmcli/arborist | 6.3.0 | ISC | javascript-package-cataloger |
| @npmcli/config | 6.2.1 | ISC | javascript-package-cataloger |
| @npmcli/disparity-colors | 3.0.0 | ISC | javascript-package-cataloger |
| @npmcli/fs | 1.1.1 | ISC | javascript-package-cataloger |
| @npmcli/fs | 3.1.0 | ISC | javascript-package-cataloger |
| @npmcli/git | 4.1.0 | ISC | javascript-package-cataloger |
| @npmcli/installed-package-contents | 2.0.2 | ISC | javascript-package-cataloger |
| @npmcli/map-workspaces | 3.0.4 | ISC | javascript-package-cataloger |
| @npmcli/metavuln-calculator | 5.0.1 | ISC | javascript-package-cataloger |
| @npmcli/move-file | 1.1.2 | MIT | javascript-package-cataloger |
| @npmcli/name-from-folder | 2.0.0 | ISC | javascript-package-cataloger |
| @npmcli/node-gyp | 3.0.0 | ISC | javascript-package-cataloger |
| @npmcli/package-json | 4.0.1 | ISC | javascript-package-cataloger |
| @npmcli/promise-spawn | 6.0.2 | ISC | javascript-package-cataloger |
| @npmcli/query | 3.0.0 | ISC | javascript-package-cataloger |
| @npmcli/run-script | 6.0.2 | ISC | javascript-package-cataloger |
| @nuxtjs/opencollective | 0.3.2 | MIT | javascript-package-cataloger |
| @okta/okta-auth-js | 7.3.0 |  | javascript-package-cataloger |
| @okta/okta-auth-js | 7.3.0 |  | javascript-package-cataloger |
| @okta/okta-auth-js | 7.3.0 | Apache-2.0 | javascript-package-cataloger |
| @peculiar/asn1-schema | 2.3.6 | MIT | javascript-package-cataloger |
| @peculiar/json-schema | 1.1.12 | MIT | javascript-package-cataloger |
| @peculiar/webcrypto | 1.4.3 | MIT | javascript-package-cataloger |
| @pkgjs/parseargs | 0.11.0 | MIT | javascript-package-cataloger |
| @redis/bloom | 1.2.0 | MIT | javascript-package-cataloger |
| @redis/client | 1.5.11 | MIT | javascript-package-cataloger |
| @redis/graph | 1.1.0 | MIT | javascript-package-cataloger |
| @redis/json | 1.0.6 | MIT | javascript-package-cataloger |
| @redis/search | 1.1.5 | MIT | javascript-package-cataloger |
| @redis/time-series | 1.0.5 | MIT | javascript-package-cataloger |
| @segment/analytics-core | 1.6.0 | MIT | javascript-package-cataloger |
| @segment/analytics-generic-utils | 1.2.0 | MIT | javascript-package-cataloger |
| @segment/analytics-node | 2.1.2 | MIT | javascript-package-cataloger |
| @sigstore/protobuf-specs | 0.1.0 | Apache-2.0 | javascript-package-cataloger |
| @sigstore/tuf | 1.0.2 | Apache-2.0 | javascript-package-cataloger |
| @socket.io/component-emitter | 3.1.0 | MIT | javascript-package-cataloger |
| @sqltools/formatter | 1.2.5 | MIT | javascript-package-cataloger |
| @tokenizer/token | 0.3.0 | MIT | javascript-package-cataloger |
| @tootallnate/once | 1.1.2 | MIT | javascript-package-cataloger |
| @tootallnate/once | 2.0.0 | MIT | javascript-package-cataloger |
| @tufjs/canonical-json | 1.0.0 | MIT | javascript-package-cataloger |
| @tufjs/models | 1.0.4 | MIT | javascript-package-cataloger |
| @types/cookie | 0.4.1 | MIT | javascript-package-cataloger |
| @types/cors | 2.8.13 | MIT | javascript-package-cataloger |
| @types/node | 18.16.1 | MIT | javascript-package-cataloger |
| @types/node | 18.16.1 | MIT | javascript-package-cataloger |
| @types/triple-beam | 1.3.2 | MIT | javascript-package-cataloger |
| @types/urijs | 1.19.25 | MIT | javascript-package-cataloger |
| @types/validator | 13.7.17 | MIT | javascript-package-cataloger |
| Base64 | 1.1.0 | (Apache-2.0 OR WTFPL) | javascript-package-cataloger |
| abbrev | 1.1.1 | ISC | javascript-package-cataloger |
| abbrev | 1.1.1 | ISC | javascript-package-cataloger |
| abbrev | 2.0.0 | ISC | javascript-package-cataloger |
| abort-controller | 3.0.0 | MIT | javascript-package-cataloger |
| abort-controller | 3.0.0 | MIT | javascript-package-cataloger |
| accepts | 1.3.8 | MIT | javascript-package-cataloger |
| address | 1.2.2 | MIT | javascript-package-cataloger |
| adm-zip | 0.5.10 | MIT | javascript-package-cataloger |
| agent-base | 6.0.2 | MIT | javascript-package-cataloger |
| agent-base | 6.0.2 | MIT | javascript-package-cataloger |
| agentkeepalive | 4.3.0 | MIT | javascript-package-cataloger |
| agentkeepalive | 4.5.0 | MIT | javascript-package-cataloger |
| aggregate-error | 3.1.0 | MIT | javascript-package-cataloger |
| aggregate-error | 3.1.0 | MIT | javascript-package-cataloger |
| alpine-baselayout | 3.4.3-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-baselayout-data | 3.4.3-r1 | GPL-2.0-only | apk-db-cataloger |
| alpine-keys | 2.4-r1 | MIT | apk-db-cataloger |
| ansi-regex | 5.0.1 | MIT | javascript-package-cataloger |
| ansi-regex | 5.0.1 | MIT | javascript-package-cataloger |
| ansi-regex | 6.0.1 | MIT | javascript-package-cataloger |
| ansi-regex | 6.0.1 | MIT | javascript-package-cataloger |
| ansi-styles | 4.3.0 | MIT | javascript-package-cataloger |
| ansi-styles | 4.3.0 | MIT | javascript-package-cataloger |
| ansi-styles | 6.2.1 | MIT | javascript-package-cataloger |
| any-promise | 1.3.0 | MIT | javascript-package-cataloger |
| apk-tools | 2.14.0-r2 | GPL-2.0-only | apk-db-cataloger |
| app-root-path | 3.1.0 | MIT | javascript-package-cataloger |
| append-field | 1.0.0 | MIT | javascript-package-cataloger |
| aproba | 2.0.0 | ISC | javascript-package-cataloger |
| aproba | 2.0.0 | ISC | javascript-package-cataloger |
| archy | 1.0.0 | MIT | javascript-package-cataloger |
| are-we-there-yet | 2.0.0 | ISC | javascript-package-cataloger |
| are-we-there-yet | 3.0.1 | ISC | javascript-package-cataloger |
| are-we-there-yet | 3.0.1 | ISC | javascript-package-cataloger |
| are-we-there-yet | 4.0.0 | ISC | javascript-package-cataloger |
| argparse | 2.0.1 | Python-2.0 | javascript-package-cataloger |
| array-flatten | 1.1.1 | MIT | javascript-package-cataloger |
| asn1 | 0.2.6 | MIT | javascript-package-cataloger |
| asn1js | 3.0.5 | BSD-3-Clause | javascript-package-cataloger |
| async | 3.2.4 | MIT | javascript-package-cataloger |
| asynckit | 0.4.0 | MIT | javascript-package-cataloger |
| atob | 2.1.2 | (MIT OR Apache-2.0) | javascript-package-cataloger |
| axios | 1.6.8 | MIT | javascript-package-cataloger |
| balanced-match | 1.0.2 | MIT | javascript-package-cataloger |
| balanced-match | 1.0.2 | MIT | javascript-package-cataloger |
| base64-js | 1.5.1 | MIT | javascript-package-cataloger |
| base64-js | 1.5.1 | MIT | javascript-package-cataloger |
| base64id | 2.0.0 | MIT | javascript-package-cataloger |
| bcrypt-pbkdf | 1.0.2 | BSD-3-Clause | javascript-package-cataloger |
| beep-boop | 1.2.3 |  | javascript-package-cataloger |
| bin-links | 4.0.2 | ISC | javascript-package-cataloger |
| binary-extensions | 2.2.0 | MIT | javascript-package-cataloger |
| bl | 4.1.0 | MIT | javascript-package-cataloger |
| body-parser | 1.20.2 | MIT | javascript-package-cataloger |
| brace-expansion | 1.1.11 | MIT | javascript-package-cataloger |
| brace-expansion | 1.1.11 | MIT | javascript-package-cataloger |
| brace-expansion | 1.1.11 | MIT | javascript-package-cataloger |
| brace-expansion | 2.0.1 | MIT | javascript-package-cataloger |
| brace-expansion | 2.0.1 | MIT | javascript-package-cataloger |
| broadcast-channel | 4.17.0 | MIT | javascript-package-cataloger |
| browser-or-node | 2.1.1 | MIT | javascript-package-cataloger |
| btoa | 1.2.1 | (MIT OR Apache-2.0) | javascript-package-cataloger |
| buffer | 5.7.1 | MIT | javascript-package-cataloger |
| buffer | 6.0.3 | MIT | javascript-package-cataloger |
| buffer | 6.0.3 | MIT | javascript-package-cataloger |
| buffer-equal-constant-time | 1.0.1 | BSD-3-Clause | javascript-package-cataloger |
| buffer-from | 1.1.2 | MIT | javascript-package-cataloger |
| buildcheck | 0.0.6 | MIT | javascript-package-cataloger |
| builtins | 5.0.1 | MIT | javascript-package-cataloger |
| busboy | 1.6.0 | MIT | javascript-package-cataloger |
| busybox | 1.36.1-r5 | GPL-2.0-only | apk-db-cataloger |
| busybox-binsh | 1.36.1-r5 | GPL-2.0-only | apk-db-cataloger |
| bytes | 3.1.2 | MIT | javascript-package-cataloger |
| ca-certificates-bundle | 20230506-r0 | MPL-2.0 AND MIT | apk-db-cataloger |
| cacache | 15.3.0 | ISC | javascript-package-cataloger |
| cacache | 17.1.3 | ISC | javascript-package-cataloger |
| call-bind | 1.0.2 | MIT | javascript-package-cataloger |
| chalk | 4.1.2 | MIT | javascript-package-cataloger |
| chalk | 5.3.0 | MIT | javascript-package-cataloger |
| chownr | 1.1.4 | ISC | javascript-package-cataloger |
| chownr | 2.0.0 | ISC | javascript-package-cataloger |
| chownr | 2.0.0 | ISC | javascript-package-cataloger |
| ci-info | 3.8.0 | MIT | javascript-package-cataloger |
| cidr-regex | 3.1.1 | BSD-2-Clause | javascript-package-cataloger |
| class-transformer | 0.2.3 | MIT | javascript-package-cataloger |
| class-validator | 0.14.0 | MIT | javascript-package-cataloger |
| clean-stack | 2.2.0 | MIT | javascript-package-cataloger |
| clean-stack | 2.2.0 | MIT | javascript-package-cataloger |
| cli-columns | 4.0.0 | MIT | javascript-package-cataloger |
| cli-highlight | 2.1.11 | ISC | javascript-package-cataloger |
| cli-table3 | 0.6.3 | MIT | javascript-package-cataloger |
| client-list | 0.0.2 |  | javascript-package-cataloger |
| cliui | 7.0.4 | ISC | javascript-package-cataloger |
| cliui | 8.0.1 | ISC | javascript-package-cataloger |
| clone | 1.0.4 | MIT | javascript-package-cataloger |
| clone | 2.1.2 | MIT | javascript-package-cataloger |
| cluster-key-slot | 1.1.2 | Apache-2.0 | javascript-package-cataloger |
| cmd-shim | 6.0.1 | ISC | javascript-package-cataloger |
| collection-utils | 1.0.1 | Apache-2.0 | javascript-package-cataloger |
| color | 3.2.1 | MIT | javascript-package-cataloger |
| color-convert | 1.9.3 | MIT | javascript-package-cataloger |
| color-convert | 2.0.1 | MIT | javascript-package-cataloger |
| color-convert | 2.0.1 | MIT | javascript-package-cataloger |
| color-name | 1.1.3 | MIT | javascript-package-cataloger |
| color-name | 1.1.4 | MIT | javascript-package-cataloger |
| color-name | 1.1.4 | MIT | javascript-package-cataloger |
| color-string | 1.9.1 | MIT | javascript-package-cataloger |
| color-support | 1.1.3 | ISC | javascript-package-cataloger |
| color-support | 1.1.3 | ISC | javascript-package-cataloger |
| colorspace | 1.1.4 | MIT | javascript-package-cataloger |
| columnify | 1.6.0 | MIT | javascript-package-cataloger |
| combined-stream | 1.0.8 | MIT | javascript-package-cataloger |
| common-ancestor-path | 1.0.1 | ISC | javascript-package-cataloger |
| concat-map | 0.0.1 | MIT | javascript-package-cataloger |
| concat-map | 0.0.1 | MIT | javascript-package-cataloger |
| concat-stream | 1.6.2 | MIT | javascript-package-cataloger |
| concat-stream | 2.0.0 | MIT | javascript-package-cataloger |
| connect-timeout | 1.9.0 | MIT | javascript-package-cataloger |
| consola | 2.15.3 | MIT | javascript-package-cataloger |
| console-control-strings | 1.1.0 | ISC | javascript-package-cataloger |
| console-control-strings | 1.1.0 | ISC | javascript-package-cataloger |
| content-disposition | 0.5.4 | MIT | javascript-package-cataloger |
| content-type | 1.0.5 | MIT | javascript-package-cataloger |
| cookie | 0.4.2 | MIT | javascript-package-cataloger |
| cookie | 0.6.0 | MIT | javascript-package-cataloger |
| cookie-signature | 1.0.6 | MIT | javascript-package-cataloger |
| core-js | 3.31.0 | MIT | javascript-package-cataloger |
| core-util-is | 1.0.3 | MIT | javascript-package-cataloger |
| corepack | 0.19.0 | MIT | javascript-package-cataloger |
| cors | 2.8.5 | MIT | javascript-package-cataloger |
| cpu-features | 0.0.9 | MIT | javascript-package-cataloger |
| cross-fetch | 3.1.7 | MIT | javascript-package-cataloger |
| cross-fetch | 4.0.0 | MIT | javascript-package-cataloger |
| cross-fetch-polyfill | 0.0.0 | MIT | javascript-package-cataloger |
| cross-fetch-polyfill | 0.0.0 | MIT | javascript-package-cataloger |
| cross-spawn | 7.0.3 | MIT | javascript-package-cataloger |
| cssesc | 3.0.0 | MIT | javascript-package-cataloger |
| date-fns | 2.29.3 | MIT | javascript-package-cataloger |
| debug | 2.6.9 | MIT | javascript-package-cataloger |
| debug | 2.6.9 | MIT | javascript-package-cataloger |
| debug | 2.6.9 | MIT | javascript-package-cataloger |
| debug | 2.6.9 | MIT | javascript-package-cataloger |
| debug | 4.3.4 | MIT | javascript-package-cataloger |
| debug | 4.3.4 | MIT | javascript-package-cataloger |
| debug | 4.3.5 | MIT | javascript-package-cataloger |
| decompress-response | 6.0.0 | MIT | javascript-package-cataloger |
| deep-extend | 0.6.0 | MIT | javascript-package-cataloger |
| defaults | 1.0.4 | MIT | javascript-package-cataloger |
| delayed-stream | 1.0.0 | MIT | javascript-package-cataloger |
| delegates | 1.0.0 | MIT | javascript-package-cataloger |
| delegates | 1.0.0 | MIT | javascript-package-cataloger |
| denque | 2.1.0 | Apache-2.0 | javascript-package-cataloger |
| depd | 1.1.2 | MIT | javascript-package-cataloger |
| depd | 2.0.0 | MIT | javascript-package-cataloger |
| depd | 2.0.0 | MIT | javascript-package-cataloger |
| destroy | 1.2.0 | MIT | javascript-package-cataloger |
| detect-libc | 2.0.1 | Apache-2.0 | javascript-package-cataloger |
| detect-node | 2.1.0 | MIT | javascript-package-cataloger |
| detect-port | 1.5.1 | MIT | javascript-package-cataloger |
| diff | 5.1.0 | BSD-3-Clause | javascript-package-cataloger |
| dotenv | 16.0.3 | BSD-2-Clause | javascript-package-cataloger |
| dset | 3.1.3 | MIT | javascript-package-cataloger |
| eastasianwidth | 0.2.0 | MIT | javascript-package-cataloger |
| ecdsa-sig-formatter | 1.0.11 | Apache-2.0 | javascript-package-cataloger |
| ee-first | 1.1.1 | MIT | javascript-package-cataloger |
| emoji-regex | 8.0.0 | MIT | javascript-package-cataloger |
| emoji-regex | 8.0.0 | MIT | javascript-package-cataloger |
| emoji-regex | 9.2.2 | MIT | javascript-package-cataloger |
| emoji-regex | 9.2.2 | MIT | javascript-package-cataloger |
| enabled | 2.0.0 | MIT | javascript-package-cataloger |
| encodeurl | 1.0.2 | MIT | javascript-package-cataloger |
| encoding | 0.1.13 | MIT | javascript-package-cataloger |
| encoding | 0.1.13 | MIT | javascript-package-cataloger |
| end-of-stream | 1.4.4 | MIT | javascript-package-cataloger |
| engine.io | 6.5.1 | MIT | javascript-package-cataloger |
| engine.io-client | 6.5.3 | MIT | javascript-package-cataloger |
| engine.io-client | UNKNOWN |  | javascript-package-cataloger |
| engine.io-client | UNKNOWN |  | javascript-package-cataloger |
| engine.io-client | UNKNOWN |  | javascript-package-cataloger |
| engine.io-parser | 5.1.0 | MIT | javascript-package-cataloger |
| engine.io-parser | 5.2.2 | MIT | javascript-package-cataloger |
| engine.io-parser | UNKNOWN |  | javascript-package-cataloger |
| engine.io-parser | UNKNOWN |  | javascript-package-cataloger |
| engine.io-parser | UNKNOWN |  | javascript-package-cataloger |
| engine.io-parser | UNKNOWN |  | javascript-package-cataloger |
| env-paths | 2.2.1 | MIT | javascript-package-cataloger |
| env-paths | 2.2.1 | MIT | javascript-package-cataloger |
| err-code | 2.0.3 | MIT | javascript-package-cataloger |
| err-code | 2.0.3 | MIT | javascript-package-cataloger |
| escalade | 3.1.1 | MIT | javascript-package-cataloger |
| escape-html | 1.0.3 | MIT | javascript-package-cataloger |
| etag | 1.8.1 | MIT | javascript-package-cataloger |
| event-target-shim | 5.0.1 | MIT | javascript-package-cataloger |
| event-target-shim | 5.0.1 | MIT | javascript-package-cataloger |
| eventemitter2 | 6.4.9 | MIT | javascript-package-cataloger |
| eventemitter3 | 4.0.7 | MIT | javascript-package-cataloger |
| events | 3.3.0 | MIT | javascript-package-cataloger |
| events | 3.3.0 | MIT | javascript-package-cataloger |
| expand-template | 2.0.3 | (MIT OR WTFPL) | javascript-package-cataloger |
| explain-plugin | 0.0.1 |  | javascript-package-cataloger |
| exponential-backoff | 3.1.1 | Apache-2.0 | javascript-package-cataloger |
| express | 4.19.2 | MIT | javascript-package-cataloger |
| fast-safe-stringify | 2.1.1 | MIT | javascript-package-cataloger |
| fast-text-encoding | 1.0.6 | Apache-2.0 | javascript-package-cataloger |
| fastest-levenshtein | 1.0.16 | MIT | javascript-package-cataloger |
| fecha | 4.2.3 | MIT | javascript-package-cataloger |
| file-stream-rotator | 1.0.0 | MIT | javascript-package-cataloger |
| file-type | 16.5.4 | MIT | javascript-package-cataloger |
| finalhandler | 1.2.0 | MIT | javascript-package-cataloger |
| fn.name | 1.1.0 | MIT | javascript-package-cataloger |
| follow-redirects | 1.15.6 | MIT | javascript-package-cataloger |
| foreground-child | 3.1.1 | ISC | javascript-package-cataloger |
| form-data | 4.0.0 | MIT | javascript-package-cataloger |
| forwarded | 0.2.0 | MIT | javascript-package-cataloger |
| fresh | 0.5.2 | MIT | javascript-package-cataloger |
| fs-constants | 1.0.0 | MIT | javascript-package-cataloger |
| fs-extra | 10.1.0 | MIT | javascript-package-cataloger |
| fs-minipass | 2.1.0 | ISC | javascript-package-cataloger |
| fs-minipass | 2.1.0 | ISC | javascript-package-cataloger |
| fs-minipass | 3.0.2 | ISC | javascript-package-cataloger |
| fs.realpath | 1.0.0 | ISC | javascript-package-cataloger |
| fs.realpath | 1.0.0 | ISC | javascript-package-cataloger |
| function-bind | 1.1.1 | MIT | javascript-package-cataloger |
| function-bind | 1.1.1 | MIT | javascript-package-cataloger |
| gauge | 3.0.2 | ISC | javascript-package-cataloger |
| gauge | 4.0.4 | ISC | javascript-package-cataloger |
| gauge | 4.0.4 | ISC | javascript-package-cataloger |
| gauge | 5.0.1 | ISC | javascript-package-cataloger |
| generic-pool | 3.9.0 | MIT | javascript-package-cataloger |
| get-caller-file | 2.0.5 | ISC | javascript-package-cataloger |
| get-intrinsic | 1.2.0 | MIT | javascript-package-cataloger |
| github-from-package | 0.0.0 | MIT | javascript-package-cataloger |
| glob | 10.2.7 | ISC | javascript-package-cataloger |
| glob | 7.2.3 | ISC | javascript-package-cataloger |
| glob | 7.2.3 | ISC | javascript-package-cataloger |
| glob | 7.2.3 | ISC | javascript-package-cataloger |
| glob | 8.1.0 | ISC | javascript-package-cataloger |
| graceful-fs | 4.2.11 | ISC | javascript-package-cataloger |
| graceful-fs | 4.2.11 | ISC | javascript-package-cataloger |
| graph-plugin | 0.0.1 |  | javascript-package-cataloger |
| has | 1.0.3 | MIT | javascript-package-cataloger |
| has | 1.0.3 | MIT | javascript-package-cataloger |
| has-flag | 4.0.0 | MIT | javascript-package-cataloger |
| has-symbols | 1.0.3 | MIT | javascript-package-cataloger |
| has-unicode | 2.0.1 | ISC | javascript-package-cataloger |
| has-unicode | 2.0.1 | ISC | javascript-package-cataloger |
| highlight.js | 10.7.3 | BSD-3-Clause | javascript-package-cataloger |
| hosted-git-info | 6.1.1 | ISC | javascript-package-cataloger |
| http-cache-semantics | 4.1.1 | BSD-2-Clause | javascript-package-cataloger |
| http-cache-semantics | 4.1.1 | BSD-2-Clause | javascript-package-cataloger |
| http-errors | 1.6.3 | MIT | javascript-package-cataloger |
| http-errors | 2.0.0 | MIT | javascript-package-cataloger |
| http-proxy-agent | 4.0.1 | MIT | javascript-package-cataloger |
| http-proxy-agent | 5.0.0 | MIT | javascript-package-cataloger |
| https-proxy-agent | 5.0.1 | MIT | javascript-package-cataloger |
| https-proxy-agent | 5.0.1 | MIT | javascript-package-cataloger |
| humanize-ms | 1.2.1 | MIT | javascript-package-cataloger |
| humanize-ms | 1.2.1 | MIT | javascript-package-cataloger |
| iconv-lite | 0.4.24 | MIT | javascript-package-cataloger |
| iconv-lite | 0.6.3 | MIT | javascript-package-cataloger |
| iconv-lite | 0.6.3 | MIT | javascript-package-cataloger |
| ieee754 | 1.2.1 | BSD-3-Clause | javascript-package-cataloger |
| ieee754 | 1.2.1 | BSD-3-Clause | javascript-package-cataloger |
| ignore-walk | 6.0.3 | ISC | javascript-package-cataloger |
| imurmurhash | 0.1.4 | MIT | javascript-package-cataloger |
| imurmurhash | 0.1.4 | MIT | javascript-package-cataloger |
| indent-string | 4.0.0 | MIT | javascript-package-cataloger |
| indent-string | 4.0.0 | MIT | javascript-package-cataloger |
| infer-owner | 1.0.4 | ISC | javascript-package-cataloger |
| inflight | 1.0.6 | ISC | javascript-package-cataloger |
| inflight | 1.0.6 | ISC | javascript-package-cataloger |
| inherits | 2.0.3 | ISC | javascript-package-cataloger |
| inherits | 2.0.4 | ISC | javascript-package-cataloger |
| inherits | 2.0.4 | ISC | javascript-package-cataloger |
| ini | 1.3.8 | ISC | javascript-package-cataloger |
| ini | 4.1.1 | ISC | javascript-package-cataloger |
| init-package-json | 5.0.0 | ISC | javascript-package-cataloger |
| ioredis | 5.3.2 | MIT | javascript-package-cataloger |
| ip | 2.0.0 | MIT | javascript-package-cataloger |
| ip-address | 9.0.5 | MIT | javascript-package-cataloger |
| ip-regex | 4.3.0 | MIT | javascript-package-cataloger |
| ipaddr.js | 1.9.1 | MIT | javascript-package-cataloger |
| is-arrayish | 0.3.2 | MIT | javascript-package-cataloger |
| is-cidr | 4.0.2 | BSD-2-Clause | javascript-package-cataloger |
| is-core-module | 2.12.1 | MIT | javascript-package-cataloger |
| is-extglob | 2.1.1 | MIT | javascript-package-cataloger |
| is-fullwidth-code-point | 3.0.0 | MIT | javascript-package-cataloger |
| is-fullwidth-code-point | 3.0.0 | MIT | javascript-package-cataloger |
| is-glob | 4.0.3 | MIT | javascript-package-cataloger |
| is-lambda | 1.0.1 | MIT | javascript-package-cataloger |
| is-lambda | 1.0.1 | MIT | javascript-package-cataloger |
| is-stream | 2.0.1 | MIT | javascript-package-cataloger |
| is-url | 1.2.4 | MIT | javascript-package-cataloger |
| isarray | 1.0.0 | MIT | javascript-package-cataloger |
| isexe | 2.0.0 | ISC | javascript-package-cataloger |
| isexe | 2.0.0 | ISC | javascript-package-cataloger |
| iterare | 1.2.1 | ISC | javascript-package-cataloger |
| jackspeak | 2.2.1 | BlueOak-1.0.0 | javascript-package-cataloger |
| jose | 5.4.0 | MIT | javascript-package-cataloger |
| js-base64 | 3.7.7 | BSD-3-Clause | javascript-package-cataloger |
| js-cookie | 3.0.5 | MIT | javascript-package-cataloger |
| js-yaml | 4.1.0 | MIT | javascript-package-cataloger |
| jsbn | 1.1.0 | MIT | javascript-package-cataloger |
| json-parse-even-better-errors | 3.0.0 | MIT | javascript-package-cataloger |
| json-stringify-nice | 1.1.4 | ISC | javascript-package-cataloger |
| jsonfile | 6.1.0 | MIT | javascript-package-cataloger |
| jsonparse | 1.3.1 | MIT | javascript-package-cataloger |
| jsonpath-plus | 6.0.1 | MIT | javascript-package-cataloger |
| jsonwebtoken | 9.0.2 | MIT | javascript-package-cataloger |
| just-diff | 6.0.2 | MIT | javascript-package-cataloger |
| just-diff-apply | 5.5.0 | MIT | javascript-package-cataloger |
| jwa | 1.4.1 | MIT | javascript-package-cataloger |
| jws | 3.2.2 | MIT | javascript-package-cataloger |
| keytar | 7.9.0 | MIT | javascript-package-cataloger |
| kuler | 2.0.0 | MIT | javascript-package-cataloger |
| libc-utils | 0.7.2-r5 | BSD-2-Clause AND BSD-3-Clause | apk-db-cataloger |
| libcrypto3 | 3.1.5-r0 | Apache-2.0 | apk-db-cataloger |
| libgcc | 12.2.1_git20220924-r10 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| libnpmaccess | 7.0.2 | ISC | javascript-package-cataloger |
| libnpmdiff | 5.0.19 | ISC | javascript-package-cataloger |
| libnpmexec | 6.0.3 | ISC | javascript-package-cataloger |
| libnpmfund | 4.0.19 | ISC | javascript-package-cataloger |
| libnpmhook | 9.0.3 | ISC | javascript-package-cataloger |
| libnpmorg | 5.0.4 | ISC | javascript-package-cataloger |
| libnpmpack | 5.0.19 | ISC | javascript-package-cataloger |
| libnpmpublish | 7.5.0 | ISC | javascript-package-cataloger |
| libnpmsearch | 6.0.2 | ISC | javascript-package-cataloger |
| libnpmteam | 5.0.3 | ISC | javascript-package-cataloger |
| libnpmversion | 4.0.2 | ISC | javascript-package-cataloger |
| libphonenumber-js | 1.10.37 | MIT | javascript-package-cataloger |
| libphonenumber-js/build | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/core | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/max | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/max/metadata | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/min | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/min/metadata | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/mobile | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/mobile/examples | UNKNOWN |  | javascript-package-cataloger |
| libphonenumber-js/mobile/metadata | UNKNOWN |  | javascript-package-cataloger |
| libssl3 | 3.1.5-r0 | Apache-2.0 | apk-db-cataloger |
| libstdc++ | 12.2.1_git20220924-r10 | GPL-2.0-or-later AND LGPL-2.1-or-later | apk-db-cataloger |
| lodash | 4.17.21 | MIT | javascript-package-cataloger |
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
| lru-cache | 6.0.0 | ISC | javascript-package-cataloger |
| lru-cache | 6.0.0 | ISC | javascript-package-cataloger |
| lru-cache | 7.18.3 | ISC | javascript-package-cataloger |
| lru-cache | 9.1.1 | ISC | javascript-package-cataloger |
| make-dir | 3.1.0 | MIT | javascript-package-cataloger |
| make-fetch-happen | 11.1.1 | ISC | javascript-package-cataloger |
| make-fetch-happen | 9.1.0 | ISC | javascript-package-cataloger |
| media-typer | 0.3.0 | MIT | javascript-package-cataloger |
| merge-descriptors | 1.0.1 | MIT | javascript-package-cataloger |
| methods | 1.1.2 | MIT | javascript-package-cataloger |
| mime | 1.6.0 | MIT | javascript-package-cataloger |
| mime-db | 1.52.0 | MIT | javascript-package-cataloger |
| mime-types | 2.1.35 | MIT | javascript-package-cataloger |
| mimic-response | 3.1.0 | MIT | javascript-package-cataloger |
| minimatch | 3.1.2 | ISC | javascript-package-cataloger |
| minimatch | 3.1.2 | ISC | javascript-package-cataloger |
| minimatch | 3.1.2 | ISC | javascript-package-cataloger |
| minimatch | 5.1.6 | ISC | javascript-package-cataloger |
| minimatch | 9.0.3 | ISC | javascript-package-cataloger |
| minimist | 1.2.8 | MIT | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 3.3.6 | ISC | javascript-package-cataloger |
| minipass | 5.0.0 | ISC | javascript-package-cataloger |
| minipass | 5.0.0 | ISC | javascript-package-cataloger |
| minipass-collect | 1.0.2 | ISC | javascript-package-cataloger |
| minipass-collect | 1.0.2 | ISC | javascript-package-cataloger |
| minipass-fetch | 1.4.1 | MIT | javascript-package-cataloger |
| minipass-fetch | 3.0.3 | MIT | javascript-package-cataloger |
| minipass-flush | 1.0.5 | ISC | javascript-package-cataloger |
| minipass-flush | 1.0.5 | ISC | javascript-package-cataloger |
| minipass-json-stream | 1.0.1 | MIT | javascript-package-cataloger |
| minipass-pipeline | 1.2.4 | ISC | javascript-package-cataloger |
| minipass-pipeline | 1.2.4 | ISC | javascript-package-cataloger |
| minipass-sized | 1.0.3 | ISC | javascript-package-cataloger |
| minipass-sized | 1.0.3 | ISC | javascript-package-cataloger |
| minizlib | 2.1.2 | MIT | javascript-package-cataloger |
| minizlib | 2.1.2 | MIT | javascript-package-cataloger |
| mkdirp | 0.5.6 | MIT | javascript-package-cataloger |
| mkdirp | 1.0.4 | MIT | javascript-package-cataloger |
| mkdirp | 1.0.4 | MIT | javascript-package-cataloger |
| mkdirp | 2.1.6 | MIT | javascript-package-cataloger |
| mkdirp | 2.1.6 | MIT | javascript-package-cataloger |
| mkdirp-classic | 0.5.3 | MIT | javascript-package-cataloger |
| ms | 2.0.0 | MIT | javascript-package-cataloger |
| ms | 2.0.0 | MIT | javascript-package-cataloger |
| ms | 2.0.0 | MIT | javascript-package-cataloger |
| ms | 2.0.0 | MIT | javascript-package-cataloger |
| ms | 2.0.0 | MIT | javascript-package-cataloger |
| ms | 2.1.2 | MIT | javascript-package-cataloger |
| ms | 2.1.2 | MIT | javascript-package-cataloger |
| ms | 2.1.2 | MIT | javascript-package-cataloger |
| ms | 2.1.3 | MIT | javascript-package-cataloger |
| ms | 2.1.3 | MIT | javascript-package-cataloger |
| multer | 1.4.4-lts.1 | MIT | javascript-package-cataloger |
| musl | 1.2.4-r2 | MIT | apk-db-cataloger |
| musl-utils | 1.2.4-r2 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | apk-db-cataloger |
| mute-stream | 1.0.0 | ISC | javascript-package-cataloger |
| mz | 2.7.0 | MIT | javascript-package-cataloger |
| nan | 2.17.0 | MIT | javascript-package-cataloger |
| nan | 2.18.0 | MIT | javascript-package-cataloger |
| napi-build-utils | 1.0.2 | MIT | javascript-package-cataloger |
| negotiator | 0.6.3 | MIT | javascript-package-cataloger |
| negotiator | 0.6.3 | MIT | javascript-package-cataloger |
| nest-winston | 1.9.1 | MIT | javascript-package-cataloger |
| nestjs-form-data | 1.8.7 | MIT | javascript-package-cataloger |
| node | 18.18.2 |  | binary-classifier-cataloger |
| node-abi | 3.40.0 | MIT | javascript-package-cataloger |
| node-addon-api | 4.3.0 | MIT | javascript-package-cataloger |
| node-cache | 5.1.2 | MIT | javascript-package-cataloger |
| node-fetch | 2.6.12 | MIT | javascript-package-cataloger |
| node-fetch | 2.6.9 | MIT | javascript-package-cataloger |
| node-fetch | 2.7.0 | MIT | javascript-package-cataloger |
| node-gyp | 8.4.1 | MIT | javascript-package-cataloger |
| node-gyp | 9.4.0 | MIT | javascript-package-cataloger |
| node-version-compare | 1.0.3 | MIT | javascript-package-cataloger |
| nopt | 5.0.0 | ISC | javascript-package-cataloger |
| nopt | 6.0.0 | ISC | javascript-package-cataloger |
| nopt | 7.2.0 | ISC | javascript-package-cataloger |
| normalize-package-data | 5.0.0 | BSD-2-Clause | javascript-package-cataloger |
| npm | 9.8.1 | Artistic-2.0 | javascript-package-cataloger |
| npm-audit-report | 5.0.0 | ISC | javascript-package-cataloger |
| npm-bundled | 3.0.0 | ISC | javascript-package-cataloger |
| npm-install-checks | 6.1.1 | BSD-2-Clause | javascript-package-cataloger |
| npm-normalize-package-bin | 3.0.1 | ISC | javascript-package-cataloger |
| npm-package-arg | 10.1.0 | ISC | javascript-package-cataloger |
| npm-packlist | 7.0.4 | ISC | javascript-package-cataloger |
| npm-pick-manifest | 8.0.1 | ISC | javascript-package-cataloger |
| npm-profile | 7.0.1 | ISC | javascript-package-cataloger |
| npm-registry-fetch | 14.0.5 | ISC | javascript-package-cataloger |
| npm-user-validate | 2.0.0 | BSD-2-Clause | javascript-package-cataloger |
| npmlog | 5.0.1 | ISC | javascript-package-cataloger |
| npmlog | 6.0.2 | ISC | javascript-package-cataloger |
| npmlog | 6.0.2 | ISC | javascript-package-cataloger |
| npmlog | 7.0.1 | ISC | javascript-package-cataloger |
| nw-pre-gyp-module-test | 0.0.1 |  | javascript-package-cataloger |
| object-assign | 4.1.1 | MIT | javascript-package-cataloger |
| object-hash | 2.2.0 | MIT | javascript-package-cataloger |
| object-hash | 3.0.0 | MIT | javascript-package-cataloger |
| object-inspect | 1.12.3 | MIT | javascript-package-cataloger |
| oblivious-set | 1.1.1 | MIT | javascript-package-cataloger |
| on-finished | 2.3.0 | MIT | javascript-package-cataloger |
| on-finished | 2.4.1 | MIT | javascript-package-cataloger |
| on-headers | 1.0.2 | MIT | javascript-package-cataloger |
| once | 1.4.0 | ISC | javascript-package-cataloger |
| once | 1.4.0 | ISC | javascript-package-cataloger |
| one-time | 1.0.0 | MIT | javascript-package-cataloger |
| p-cancelable | 2.1.1 | MIT | javascript-package-cataloger |
| p-finally | 1.0.0 | MIT | javascript-package-cataloger |
| p-map | 4.0.0 | MIT | javascript-package-cataloger |
| p-map | 4.0.0 | MIT | javascript-package-cataloger |
| p-queue | 6.6.2 | MIT | javascript-package-cataloger |
| p-timeout | 3.2.0 | MIT | javascript-package-cataloger |
| pacote | 15.2.0 | ISC | javascript-package-cataloger |
| pagent | UNKNOWN |  | pe-binary-package-cataloger |
| pako | 0.2.9 | MIT | javascript-package-cataloger |
| pako | 1.0.11 | (MIT AND Zlib) | javascript-package-cataloger |
| parse-conflict-json | 3.0.1 | ISC | javascript-package-cataloger |
| parseurl | 1.3.3 | MIT | javascript-package-cataloger |
| path-is-absolute | 1.0.1 | MIT | javascript-package-cataloger |
| path-is-absolute | 1.0.1 | MIT | javascript-package-cataloger |
| path-key | 3.1.1 | MIT | javascript-package-cataloger |
| path-scurry | 1.9.2 | BlueOak-1.0.0 | javascript-package-cataloger |
| path-to-regexp | 0.1.7 | MIT | javascript-package-cataloger |
| path-to-regexp | 0.2.5 | MIT | javascript-package-cataloger |
| path-to-regexp | 3.2.0 | MIT | javascript-package-cataloger |
| peek-readable | 4.1.0 | MIT | javascript-package-cataloger |
| pluralize | 8.0.0 | MIT | javascript-package-cataloger |
| postcss-selector-parser | 6.0.13 | MIT | javascript-package-cataloger |
| prebuild-install | 7.1.1 | MIT | javascript-package-cataloger |
| proc-log | 3.0.0 | ISC | javascript-package-cataloger |
| process | 0.11.10 | MIT | javascript-package-cataloger |
| process | 0.11.10 | MIT | javascript-package-cataloger |
| process-nextick-args | 2.0.1 | MIT | javascript-package-cataloger |
| promise-all-reject-late | 1.0.1 | ISC | javascript-package-cataloger |
| promise-call-limit | 1.0.2 | ISC | javascript-package-cataloger |
| promise-inflight | 1.0.1 | ISC | javascript-package-cataloger |
| promise-inflight | 1.0.1 | ISC | javascript-package-cataloger |
| promise-retry | 2.0.1 | MIT | javascript-package-cataloger |
| promise-retry | 2.0.1 | MIT | javascript-package-cataloger |
| promzard | 1.0.0 | ISC | javascript-package-cataloger |
| proxy-addr | 2.0.7 | MIT | javascript-package-cataloger |
| proxy-from-env | 1.1.0 | MIT | javascript-package-cataloger |
| pump | 3.0.0 | MIT | javascript-package-cataloger |
| pvtsutils | 1.3.2 | MIT | javascript-package-cataloger |
| pvutils | 1.1.3 | MIT | javascript-package-cataloger |
| qrcode-terminal | 0.12.0 |  | javascript-package-cataloger |
| qs | 6.11.0 | BSD-3-Clause | javascript-package-cataloger |
| quicktype-core | 23.0.116 | Apache-2.0 | javascript-package-cataloger |
| range-parser | 1.2.1 | MIT | javascript-package-cataloger |
| raw-body | 2.5.2 | MIT | javascript-package-cataloger |
| rc | 1.2.8 | (BSD-2-Clause OR MIT OR Apache-2.0) | javascript-package-cataloger |
| read | 2.1.0 | ISC | javascript-package-cataloger |
| read-cmd-shim | 4.0.0 | ISC | javascript-package-cataloger |
| read-package-json | 6.0.4 | ISC | javascript-package-cataloger |
| read-package-json-fast | 3.0.2 | ISC | javascript-package-cataloger |
| readable-stream | 2.3.8 | MIT | javascript-package-cataloger |
| readable-stream | 3.6.2 | MIT | javascript-package-cataloger |
| readable-stream | 3.6.2 | MIT | javascript-package-cataloger |
| readable-stream | 4.4.0 | MIT | javascript-package-cataloger |
| readable-stream | 4.5.2 | MIT | javascript-package-cataloger |
| readable-web-to-node-stream | 3.0.2 | MIT | javascript-package-cataloger |
| redis | 4.6.10 | MIT | javascript-package-cataloger |
| redis-errors | 1.2.0 | MIT | javascript-package-cataloger |
| redis-parser | 3.0.0 | MIT | javascript-package-cataloger |
| redisearch | 0.0.1 |  | javascript-package-cataloger |
| redisinsight-api | 2.52.0 |  | javascript-package-cataloger |
| redistimeseries | 0.0.1 |  | javascript-package-cataloger |
| reflect-metadata | 0.1.13 | Apache-2.0 | javascript-package-cataloger |
| regenerator-runtime | 0.13.11 | MIT | javascript-package-cataloger |
| require-directory | 2.1.1 | MIT | javascript-package-cataloger |
| retry | 0.12.0 | MIT | javascript-package-cataloger |
| retry | 0.12.0 | MIT | javascript-package-cataloger |
| rimraf | 3.0.2 | ISC | javascript-package-cataloger |
| rimraf | 3.0.2 | ISC | javascript-package-cataloger |
| rxjs | 7.8.1 | Apache-2.0 | javascript-package-cataloger |
| rxjs/ajax | UNKNOWN |  | javascript-package-cataloger |
| rxjs/fetch | UNKNOWN |  | javascript-package-cataloger |
| rxjs/operators | UNKNOWN |  | javascript-package-cataloger |
| rxjs/testing | UNKNOWN |  | javascript-package-cataloger |
| rxjs/webSocket | UNKNOWN |  | javascript-package-cataloger |
| safe-buffer | 5.1.2 | MIT | javascript-package-cataloger |
| safe-buffer | 5.2.1 | MIT | javascript-package-cataloger |
| safe-buffer | 5.2.1 | MIT | javascript-package-cataloger |
| safe-stable-stringify | 2.4.3 | MIT | javascript-package-cataloger |
| safer-buffer | 2.1.2 | MIT | javascript-package-cataloger |
| safer-buffer | 2.1.2 | MIT | javascript-package-cataloger |
| scanelf | 1.3.7-r1 | GPL-2.0-only | apk-db-cataloger |
| semver | 7.5.4 | ISC | javascript-package-cataloger |
| semver | 7.5.4 | ISC | javascript-package-cataloger |
| send | 0.18.0 | MIT | javascript-package-cataloger |
| serve-static | 1.15.0 | MIT | javascript-package-cataloger |
| set-blocking | 2.0.0 | ISC | javascript-package-cataloger |
| set-blocking | 2.0.0 | ISC | javascript-package-cataloger |
| setprototypeof | 1.1.0 | ISC | javascript-package-cataloger |
| setprototypeof | 1.2.0 | ISC | javascript-package-cataloger |
| sha.js | 2.4.11 | (MIT AND BSD-3-Clause) | javascript-package-cataloger |
| shebang-command | 2.0.0 | MIT | javascript-package-cataloger |
| shebang-regex | 3.0.0 | MIT | javascript-package-cataloger |
| side-channel | 1.0.4 | MIT | javascript-package-cataloger |
| signal-exit | 3.0.7 | ISC | javascript-package-cataloger |
| signal-exit | 3.0.7 | ISC | javascript-package-cataloger |
| signal-exit | 4.0.2 | ISC | javascript-package-cataloger |
| sigstore | 1.7.0 | Apache-2.0 | javascript-package-cataloger |
| simple-concat | 1.0.1 | MIT | javascript-package-cataloger |
| simple-get | 4.0.1 | MIT | javascript-package-cataloger |
| simple-swizzle | 0.2.2 | MIT | javascript-package-cataloger |
| smart-buffer | 4.2.0 | MIT | javascript-package-cataloger |
| smart-buffer | 4.2.0 | MIT | javascript-package-cataloger |
| socket.io | 4.7.1 | MIT | javascript-package-cataloger |
| socket.io-adapter | 2.5.2 | MIT | javascript-package-cataloger |
| socket.io-client | 4.7.5 |  | javascript-package-cataloger |
| socket.io-client | 4.7.5 |  | javascript-package-cataloger |
| socket.io-client | 4.7.5 | MIT | javascript-package-cataloger |
| socket.io-parser | 4.2.4 | MIT | javascript-package-cataloger |
| socks | 2.7.1 | MIT | javascript-package-cataloger |
| socks | 2.8.3 | MIT | javascript-package-cataloger |
| socks-proxy-agent | 6.2.1 | MIT | javascript-package-cataloger |
| socks-proxy-agent | 7.0.0 | MIT | javascript-package-cataloger |
| source-map | 0.6.1 | BSD-3-Clause | javascript-package-cataloger |
| source-map-support | 0.5.21 | MIT | javascript-package-cataloger |
| spdx-correct | 3.2.0 | Apache-2.0 | javascript-package-cataloger |
| spdx-exceptions | 2.3.0 | CC-BY-3.0 | javascript-package-cataloger |
| spdx-expression-parse | 3.0.1 | MIT | javascript-package-cataloger |
| spdx-license-ids | 3.0.13 | CC0-1.0 | javascript-package-cataloger |
| sprintf-js | 1.1.3 | BSD-3-Clause | javascript-package-cataloger |
| sqlite3 | 5.1.6 | BSD-3-Clause | javascript-package-cataloger |
| ssh2 | 1.15.0 | MIT | javascript-package-cataloger |
| ssl_client | 1.36.1-r5 | GPL-2.0-only | apk-db-cataloger |
| ssri | 10.0.4 | ISC | javascript-package-cataloger |
| ssri | 8.0.1 | ISC | javascript-package-cataloger |
| stack-trace | 0.0.10 | MIT | javascript-package-cataloger |
| standard-as-callback | 2.1.0 | MIT | javascript-package-cataloger |
| statuses | 1.5.0 | MIT | javascript-package-cataloger |
| statuses | 2.0.1 | MIT | javascript-package-cataloger |
| streamsearch | 1.1.0 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 4.2.3 | MIT | javascript-package-cataloger |
| string-width | 5.1.2 | MIT | javascript-package-cataloger |
| string-width | 5.1.2 | MIT | javascript-package-cataloger |
| string_decoder | 1.1.1 | MIT | javascript-package-cataloger |
| string_decoder | 1.3.0 | MIT | javascript-package-cataloger |
| string_decoder | 1.3.0 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 6.0.1 | MIT | javascript-package-cataloger |
| strip-ansi | 7.1.0 | MIT | javascript-package-cataloger |
| strip-ansi | 7.1.0 | MIT | javascript-package-cataloger |
| strip-json-comments | 2.0.1 | MIT | javascript-package-cataloger |
| strtok3 | 6.3.0 | MIT | javascript-package-cataloger |
| supports-color | 7.2.0 | MIT | javascript-package-cataloger |
| supports-color | 9.4.0 | MIT | javascript-package-cataloger |
| swagger-ui-dist | 4.18.3 | Apache-2.0 | javascript-package-cataloger |
| swagger-ui-dist | 5.11.2 | Apache-2.0 | javascript-package-cataloger |
| swagger-ui-express | 4.6.2 | MIT | javascript-package-cataloger |
| tar | 6.1.15 | ISC | javascript-package-cataloger |
| tar | 6.2.1 | ISC | javascript-package-cataloger |
| tar-fs | 2.1.1 | MIT | javascript-package-cataloger |
| tar-stream | 2.2.0 | MIT | javascript-package-cataloger |
| text-hex | 1.0.0 | MIT | javascript-package-cataloger |
| text-table | 0.2.0 | MIT | javascript-package-cataloger |
| thenify | 3.3.1 | MIT | javascript-package-cataloger |
| thenify-all | 1.6.0 | MIT | javascript-package-cataloger |
| tiny-emitter | 1.1.0 | MIT | javascript-package-cataloger |
| tiny-inflate | 1.0.3 | MIT | javascript-package-cataloger |
| tiny-relative-date | 1.3.0 | MIT | javascript-package-cataloger |
| toidentifier | 1.0.1 | MIT | javascript-package-cataloger |
| token-types | 4.2.1 | MIT | javascript-package-cataloger |
| tr46 | 0.0.3 | MIT | javascript-package-cataloger |
| treeverse | 3.0.0 | ISC | javascript-package-cataloger |
| triple-beam | 1.3.0 | MIT | javascript-package-cataloger |
| tslib | 2.5.0 | 0BSD | javascript-package-cataloger |
| tslib | 2.5.0 | 0BSD | javascript-package-cataloger |
| tslib | 2.5.0 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.0 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.2 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.2 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.2 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.2 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.2 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.3 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.3 | 0BSD | javascript-package-cataloger |
| tslib | 2.6.3 | 0BSD | javascript-package-cataloger |
| tuf-js | 1.1.7 | MIT | javascript-package-cataloger |
| tunnel-agent | 0.6.0 | Apache-2.0 | javascript-package-cataloger |
| tunnel-ssh | 5.1.2 | MIT | javascript-package-cataloger |
| tweetnacl | 0.14.5 | Unlicense | javascript-package-cataloger |
| type-is | 1.6.18 | MIT | javascript-package-cataloger |
| typedarray | 0.0.6 | MIT | javascript-package-cataloger |
| typeorm | 0.3.15 | MIT | javascript-package-cataloger |
| uid | 2.0.2 | MIT | javascript-package-cataloger |
| unicode-properties | 1.4.1 | MIT | javascript-package-cataloger |
| unicode-trie | 2.0.0 | MIT | javascript-package-cataloger |
| unique-filename | 1.1.1 | ISC | javascript-package-cataloger |
| unique-filename | 3.0.0 | ISC | javascript-package-cataloger |
| unique-slug | 2.0.2 | ISC | javascript-package-cataloger |
| unique-slug | 4.0.0 | ISC | javascript-package-cataloger |
| universalify | 2.0.0 | MIT | javascript-package-cataloger |
| unload | 2.3.1 | Apache-2.0 | javascript-package-cataloger |
| unpipe | 1.0.0 | MIT | javascript-package-cataloger |
| urijs | 1.19.11 | MIT | javascript-package-cataloger |
| util-deprecate | 1.0.2 | MIT | javascript-package-cataloger |
| util-deprecate | 1.0.2 | MIT | javascript-package-cataloger |
| utils-merge | 1.0.1 | MIT | javascript-package-cataloger |
| uuid | 8.3.2 | MIT | javascript-package-cataloger |
| uuid | 9.0.0 | MIT | javascript-package-cataloger |
| validate-npm-package-license | 3.0.4 | Apache-2.0 | javascript-package-cataloger |
| validate-npm-package-name | 5.0.0 | ISC | javascript-package-cataloger |
| validator | 13.9.0 | MIT | javascript-package-cataloger |
| vary | 1.1.2 | MIT | javascript-package-cataloger |
| walk-up-path | 3.0.1 | ISC | javascript-package-cataloger |
| wcwidth | 1.0.1 | MIT | javascript-package-cataloger |
| webcrypto-core | 1.7.7 | MIT | javascript-package-cataloger |
| webcrypto-shim | 0.1.7 | MIT | javascript-package-cataloger |
| webidl-conversions | 3.0.1 | BSD-2-Clause | javascript-package-cataloger |
| whatwg-url | 5.0.0 | MIT | javascript-package-cataloger |
| which | 2.0.2 | ISC | javascript-package-cataloger |
| which | 2.0.2 | ISC | javascript-package-cataloger |
| which | 2.0.2 | ISC | javascript-package-cataloger |
| which | 3.0.1 | ISC | javascript-package-cataloger |
| wide-align | 1.1.5 | ISC | javascript-package-cataloger |
| wide-align | 1.1.5 | ISC | javascript-package-cataloger |
| winston | 3.8.2 | MIT | javascript-package-cataloger |
| winston-daily-rotate-file | 4.7.1 | MIT | javascript-package-cataloger |
| winston-transport | 4.5.0 | MIT | javascript-package-cataloger |
| wordwrap | 1.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 7.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 7.0.0 | MIT | javascript-package-cataloger |
| wrap-ansi | 8.1.0 | MIT | javascript-package-cataloger |
| wrappy | 1.0.2 | ISC | javascript-package-cataloger |
| wrappy | 1.0.2 | ISC | javascript-package-cataloger |
| write-file-atomic | 5.0.1 | ISC | javascript-package-cataloger |
| ws | 8.11.0 | MIT | javascript-package-cataloger |
| xhr2 | 0.1.3 | MIT | javascript-package-cataloger |
| xmlhttprequest-ssl | 2.0.0 | MIT | javascript-package-cataloger |
| xtend | 4.0.2 | MIT | javascript-package-cataloger |
| y18n | 5.0.8 | ISC | javascript-package-cataloger |
| y18n | 5.0.8 | ISC | javascript-package-cataloger |
| yallist | 4.0.0 | ISC | javascript-package-cataloger |
| yallist | 4.0.0 | ISC | javascript-package-cataloger |
| yaml | 2.4.1 | ISC | javascript-package-cataloger |
| yargs | 16.2.0 | MIT | javascript-package-cataloger |
| yargs | 17.7.1 | MIT | javascript-package-cataloger |
| yargs-parser | 20.2.9 | ISC | javascript-package-cataloger |
| yargs-parser | 21.1.1 | ISC | javascript-package-cataloger |
| yarn | 1.22.19 | BSD-2-Clause | javascript-package-cataloger |
| zlib | 1.2.13-r1 | Zlib | apk-db-cataloger |

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
| base-files | 13.8+deb13u3 | GPL-2.0-or-later | dpkg-db-cataloger |
| base-passwd | 3.6.7 | GPL-2.0-only | dpkg-db-cataloger |
| bash | 5.2.37-2+b7 | BSD-4-Clause-UC, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, Latex2e | dpkg-db-cataloger |
| bsdutils | 1:2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| ca-certificates | 20250419 | GPL-2.0-only, GPL-2.0-or-later, MPL-2.0 | dpkg-db-cataloger |
| cabextract | 1.11-2 |  | dpkg-db-cataloger |
| chromium | 144.0.7559.96-1~deb13u1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, BSL-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, ICU, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT, MPL-1.1, MPL-2.0, MS-PL, Zlib | dpkg-db-cataloger |
| chromium-common | 144.0.7559.96-1~deb13u1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, BSL-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, ICU, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MIT, MPL-1.1, MPL-2.0, MS-PL, Zlib | dpkg-db-cataloger |
| coinor-libcbc3.1 | 2.10.12+ds-1 | EPL-1.0, EPL-2.0, FSFUL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only | dpkg-db-cataloger |
| coinor-libcgl1 | 0.60.9+ds-1 | EPL-1.0, EPL-2.0, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, X11 | dpkg-db-cataloger |
| coinor-libclp1 | 1.17.10+ds-1 | EPL-1.0, EPL-2.0, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, X11 | dpkg-db-cataloger |
| coinor-libcoinmp0 | 1.8.4+dfsg-2 | CPL-1.0, EPL-1.0, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| coinor-libcoinutils3v5 | 2.11.11+ds-5 | EPL-1.0, GPL-3.0-only | dpkg-db-cataloger |
| coinor-libosi1v5 | 0.108.10+ds-2 | EPL-1.0, EPL-2.0, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, X11 | dpkg-db-cataloger |
| commons-lang3 | 3.12.0 |  | java-archive-cataloger |
| coreutils | 9.7-3 | BSD-4-Clause-UC, FSFULLR, GFDL-1.3-only, GPL-3.0-only, GPL-3.0-or-later, ISC | dpkg-db-cataloger |
| culmus | 0.140-3 | GPL-2.0-only | dpkg-db-cataloger |
| curl | 8.18.0-1~bpo13+1 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
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
| dirmngr | 2.4.7-21+deb13u1+b1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| dpkg | 1.22.21 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| emacsen-common | 3.0.8 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| file | 1:5.46-5 | BSD-2-Clause | dpkg-db-cataloger |
| findutils | 4.10.0-3 | BSD-3-Clause, FSFAP, FSFULLR, GFDL-1.3-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, X11 | dpkg-db-cataloger |
| fontconfig | 2.15.0-2.3 | HPND-sell-variant | dpkg-db-cataloger |
| fontconfig-config | 2.15.0-2.3 | HPND-sell-variant | dpkg-db-cataloger |
| fonts-arphic-ukai | 0.2.20080216.2-5 | GPL-2.0-only | dpkg-db-cataloger |
| fonts-arphic-uming | 0.2.20080216.2-11 | GPL-2.0-only | dpkg-db-cataloger |
| fonts-beng | 2:1.3 | ISC | dpkg-db-cataloger |
| fonts-beng-extra | 3.6.0-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only | dpkg-db-cataloger |
| fonts-cantarell | 0.303.1-4 | CC0-1.0, OFL-1.1 | dpkg-db-cataloger |
| fonts-comic-neue | 2.51-4 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-courier-prime | 0+git20190115-4 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-crosextra-caladea | 20200211-2 | Apache-2.0, OFL-1.1 | dpkg-db-cataloger |
| fonts-crosextra-carlito | 20230309-2 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-culmus | 0.140-3 | GPL-2.0-only | dpkg-db-cataloger |
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
| fonts-hosny-amiri | 1.001-1 |  | dpkg-db-cataloger |
| fonts-indic | 2:1.4 | ISC | dpkg-db-cataloger |
| fonts-ipafont-gothic | 00303-23 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-ipafont-mincho | 00303-23 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-kalapi | 1.0-5 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-knda | 2:1.3.1 | ISC | dpkg-db-cataloger |
| fonts-league-spartan | 2.210-2 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-liberation | 1:2.1.5-3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-liberation2 | 1:2.1.5-3 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-linuxlibertine | 5.3.0-6 | GPL-2.0-only, GPL-2.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-lklug-sinhala | 0.6-4 | GPL-2.0-only | dpkg-db-cataloger |
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
| fonts-noto-ui-core | 20201225-2 | GPL-3.0-only, GPL-3.0-or-later, OFL-1.1 | dpkg-db-cataloger |
| fonts-opensymbol | 4:102.12+LibO25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| fonts-orya | 2:1.3 | ISC | dpkg-db-cataloger |
| fonts-orya-extra | 2.0-6 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-pagul | 1.0-9 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-recommended | 2 |  | dpkg-db-cataloger |
| fonts-sahadeva | 1.0-5 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-samyak-deva | 1.2.2-6 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-samyak-gujr | 1.2.2-6 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-samyak-mlym | 1.2.2-6 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-samyak-taml | 1.2.2-6 | GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| fonts-sarai | 1.0-3 | GPL-2.0-only, GPL-2.0-only | dpkg-db-cataloger |
| fonts-sil-abyssinica | 2.201-1 | OFL-1.1-RFN | dpkg-db-cataloger |
| fonts-sil-annapurna | 2.000-2 | OFL-1.1 | dpkg-db-cataloger |
| fonts-sil-gentium | 20081126:1.03-4 | OFL-1.1 | dpkg-db-cataloger |
| fonts-sil-gentium-basic | 1.102-1.1 | OFL-1.1 | dpkg-db-cataloger |
| fonts-sil-padauk | 5.001-1 | OFL-1.1 | dpkg-db-cataloger |
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
| fonts-thai-tlwg | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-garuda | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-garuda-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-kinnari | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-kinnari-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-laksaman | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-laksaman-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-loma | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-loma-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-mono | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-mono-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-norasi | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-norasi-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-purisa | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-purisa-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-sawasdee | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-sawasdee-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-typewriter | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-typewriter-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-typist | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-typist-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-typo | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-typo-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-umpush | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-umpush-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-waree | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| fonts-tlwg-waree-ttf | 1:0.7.3-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
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
| github.com/andybalholm/brotli | v1.2.0 |  | go-module-binary-cataloger |
| github.com/aymerick/douceur | v0.2.0 |  | go-module-binary-cataloger |
| github.com/barasher/go-exiftool | v1.10.0 |  | go-module-binary-cataloger |
| github.com/beorn7/perks | v1.0.1 |  | go-module-binary-cataloger |
| github.com/bodgit/plumbing | v1.3.0 |  | go-module-binary-cataloger |
| github.com/bodgit/sevenzip | v1.6.1 |  | go-module-binary-cataloger |
| github.com/bodgit/windows | v1.0.1 |  | go-module-binary-cataloger |
| github.com/cespare/xxhash/v2 | v2.3.0 |  | go-module-binary-cataloger |
| github.com/chromedp/cdproto | v0.0.0-20250803210736-d308e07a266d |  | go-module-binary-cataloger |
| github.com/chromedp/chromedp | v0.14.2 |  | go-module-binary-cataloger |
| github.com/chromedp/sysutil | v1.1.0 |  | go-module-binary-cataloger |
| github.com/clipperhouse/uax29/v2 | v2.2.0 |  | go-module-binary-cataloger |
| github.com/dlclark/regexp2 | v1.11.5 |  | go-module-binary-cataloger |
| github.com/dsnet/compress | v0.0.2-0.20230904184137-39efe44ab707 |  | go-module-binary-cataloger |
| github.com/go-json-experiment/json | v0.0.0-20251027170946-4849db3c2f7e |  | go-module-binary-cataloger |
| github.com/gobwas/httphead | v0.1.0 |  | go-module-binary-cataloger |
| github.com/gobwas/pool | v0.2.1 |  | go-module-binary-cataloger |
| github.com/gobwas/ws | v1.4.0 |  | go-module-binary-cataloger |
| github.com/gomarkdown/markdown | v0.0.0-20250810172220-2e2c11897d1a |  | go-module-binary-cataloger |
| github.com/google/uuid | v1.6.0 |  | go-module-binary-cataloger |
| github.com/gorilla/css | v1.0.1 |  | go-module-binary-cataloger |
| github.com/gotenberg/gotenberg/v8 | v8.26.0 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-cleanhttp | v0.5.2 |  | go-module-binary-cataloger |
| github.com/hashicorp/go-retryablehttp | v0.7.8 |  | go-module-binary-cataloger |
| github.com/hashicorp/golang-lru/v2 | v2.0.7 |  | go-module-binary-cataloger |
| github.com/hhrutter/lzw | v1.0.0 |  | go-module-binary-cataloger |
| github.com/hhrutter/pkcs7 | v0.2.0 |  | go-module-binary-cataloger |
| github.com/hhrutter/tiff | v1.0.2 |  | go-module-binary-cataloger |
| github.com/klauspost/compress | v1.18.3 |  | go-module-binary-cataloger |
| github.com/klauspost/pgzip | v1.2.6 |  | go-module-binary-cataloger |
| github.com/labstack/echo/v4 | v4.15.0 |  | go-module-binary-cataloger |
| github.com/labstack/gommon | v0.4.2 |  | go-module-binary-cataloger |
| github.com/mattn/go-colorable | v0.1.14 |  | go-module-binary-cataloger |
| github.com/mattn/go-isatty | v0.0.20 |  | go-module-binary-cataloger |
| github.com/mattn/go-runewidth | v0.0.19 |  | go-module-binary-cataloger |
| github.com/mholt/archives | v0.1.5 |  | go-module-binary-cataloger |
| github.com/microcosm-cc/bluemonday | v1.0.27 |  | go-module-binary-cataloger |
| github.com/mikelolasagasti/xz | v1.0.1 |  | go-module-binary-cataloger |
| github.com/minio/minlz | v1.0.1 |  | go-module-binary-cataloger |
| github.com/munnerz/goautoneg | v0.0.0-20191010083416-a7dc8b61c822 |  | go-module-binary-cataloger |
| github.com/nwaples/rardecode/v2 | v2.2.2 |  | go-module-binary-cataloger |
| github.com/pdfcpu/pdfcpu | v0.11.1 |  | go-module-binary-cataloger |
| github.com/pierrec/lz4/v4 | v4.1.25 |  | go-module-binary-cataloger |
| github.com/pkg/errors | v0.9.1 |  | go-module-binary-cataloger |
| github.com/prometheus/client_golang | v1.23.2 |  | go-module-binary-cataloger |
| github.com/prometheus/client_model | v0.6.2 |  | go-module-binary-cataloger |
| github.com/prometheus/common | v0.67.5 |  | go-module-binary-cataloger |
| github.com/prometheus/procfs | v0.19.2 |  | go-module-binary-cataloger |
| github.com/shirou/gopsutil/v4 | v4.25.12 |  | go-module-binary-cataloger |
| github.com/sorairolake/lzip-go | v0.3.8 |  | go-module-binary-cataloger |
| github.com/spf13/afero | v1.15.0 |  | go-module-binary-cataloger |
| github.com/spf13/pflag | v1.0.10 |  | go-module-binary-cataloger |
| github.com/tklauser/go-sysconf | v0.3.16 |  | go-module-binary-cataloger |
| github.com/tklauser/numcpus | v0.11.0 |  | go-module-binary-cataloger |
| github.com/ulikunitz/xz | v0.5.15 |  | go-module-binary-cataloger |
| github.com/valyala/bytebufferpool | v1.0.0 |  | go-module-binary-cataloger |
| github.com/valyala/fasttemplate | v1.2.2 |  | go-module-binary-cataloger |
| gnupg | 2.4.7-21+deb13u1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gnupg-l10n | 2.4.7-21+deb13u1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| go.uber.org/multierr | v1.11.0 |  | go-module-binary-cataloger |
| go.uber.org/zap | v1.27.1 |  | go-module-binary-cataloger |
| go.yaml.in/yaml/v2 | v2.4.3 |  | go-module-binary-cataloger |
| go4.org | v0.0.0-20260112195520-a5071408f32f |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.43.0 |  | go-module-binary-cataloger |
| golang.org/x/crypto | v0.47.0 |  | go-module-binary-cataloger |
| golang.org/x/image | v0.32.0 |  | go-module-binary-cataloger |
| golang.org/x/net | v0.49.0 |  | go-module-binary-cataloger |
| golang.org/x/sync | v0.19.0 |  | go-module-binary-cataloger |
| golang.org/x/sys | v0.40.0 |  | go-module-binary-cataloger |
| golang.org/x/term | v0.39.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.30.0 |  | go-module-binary-cataloger |
| golang.org/x/text | v0.33.0 |  | go-module-binary-cataloger |
| golang.org/x/time | v0.14.0 |  | go-module-binary-cataloger |
| google.golang.org/protobuf | v1.36.11 |  | go-module-binary-cataloger |
| gopkg.in/yaml.v2 | v2.4.0 |  | go-module-binary-cataloger |
| gpg | 2.4.7-21+deb13u1+b1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpg-agent | 2.4.7-21+deb13u1+b1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgconf | 2.4.7-21+deb13u1+b1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| gpgsm | 2.4.7-21+deb13u1+b1 | BSD-3-Clause, CC0-1.0, GPL-2.0-or-later, GPL-2.0-only, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
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
| jrt-fs | 21.0.10 |  | java-archive-cataloger |
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
| libc-bin | 2.41-12+deb13u1 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libc6 | 2.41-12+deb13u1 | BSD-2-Clause, BSL-1.0, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, SunPro, Unicode-DFS-2016 | dpkg-db-cataloger |
| libcairo-gobject2 | 1.18.4-1+b1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcairo2 | 1.18.4-1+b1 | LGPL-2.1-only | dpkg-db-cataloger |
| libcap-ng0 | 0.8.5-4+b1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcap2 | 1:2.75-10+b3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcap2-bin | 1:2.75-10+b3 | BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libcdr-0.1-1 | 0.1.7-1+b3 | MPL-2.0 | dpkg-db-cataloger |
| libclone-perl | 0.47-1+b1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libcloudproviders0 | 0.3.6-2 | LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libclucene-contribs1t64 | 2.3.3.4+dfsg-1.2+b1 | Apache-2.0, LGPL-2.1-only | dpkg-db-cataloger |
| libclucene-core1t64 | 2.3.3.4+dfsg-1.2+b1 | Apache-2.0, LGPL-2.1-only | dpkg-db-cataloger |
| libcmis-0.6-6t64 | 0.6.2-2.1+b1 |  | dpkg-db-cataloger |
| libcolamd3 | 1:7.10.1+dfsg-1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, LPPL-1.0+, LPPL-1.3c+ | dpkg-db-cataloger |
| libcolord2 | 1.4.7-3 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
| libcom-err2 | 1.47.2-3+b7 | 0BSD, Apache-2.0, Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, ISC, Kazlib, LGPL-2.0-only, Latex2e | dpkg-db-cataloger |
| libcrypt1 | 1:4.4.38-1 |  | dpkg-db-cataloger |
| libcups2t64 | 2.4.10-3+deb13u2 | Apache-2.0, BSD-2-Clause, FSFUL, Zlib | dpkg-db-cataloger |
| libcurl3t64-gnutls | 8.18.0-1~bpo13+1 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
| libcurl4t64 | 8.18.0-1~bpo13+1 | BSD-4-Clause-UC, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, ISC, OLDAP-2.8, X11, curl | dpkg-db-cataloger |
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
| libfreetype6 | 2.13.3+dfsg-1 | BSD-3-Clause, BSL-1.0, FSFAP, FTL, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT-Modern-Variant, Zlib | dpkg-db-cataloger |
| libfribidi0 | 1.0.16-1 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgbm1 | 25.0.7-2 | Apache-2.0, BSD-2-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| libgcc-s1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgcrypt20 | 1.11.0-7 | GPL-2.0-only | dpkg-db-cataloger |
| libgdbm-compat4t64 | 1.24-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdbm6t64 | 1.24-2 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | dpkg-db-cataloger |
| libgdk-pixbuf-2.0-0 | 2.42.12+dfsg-4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgdk-pixbuf2.0-common | 2.42.12+dfsg-4 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgfortran5 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgl1 | 1.7.0-1+b2 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libgl1-mesa-dri | 25.0.7-2 | Apache-2.0, BSD-2-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| libglib2.0-0t64 | 2.84.4-3~deb13u2 | AFL-2.0, Apache-2.0, CC-BY-SA-3.0, CC0-1.0, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, MPL-1.1, Unicode-DFS-2016, bzip2-1.0.6 | dpkg-db-cataloger |
| libglvnd0 | 1.7.0-1+b2 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libglx-mesa0 | 25.0.7-2 | Apache-2.0, BSD-2-Clause, GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, MIT | dpkg-db-cataloger |
| libglx0 | 1.7.0-1+b2 | Apache-2.0, BSD-1-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libgmp10 | 2:6.3.0+dfsg-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgnutls30t64 | 3.8.9-3+deb13u1 | Apache-2.0, BSD-3-Clause, FSFAP, GFDL-1.3-only, GPL-3.0-only, LGPL-3.0-only | dpkg-db-cataloger |
| libgomp1 | 14.2.0-19 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
| libgpg-error0 | 1.51-4 | BSD-3-Clause, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libgpgme11t64 | 1.24.2-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgpgmepp6t64 | 1.24.2-3 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libgraphite2-3 | 1.3.14-2+b1 | GPL-1.0-only, GPL-1.0-or-later, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, MPL-1.1 | dpkg-db-cataloger |
| libgssapi-krb5-2 | 1.21.3-5 | GPL-2.0-only | dpkg-db-cataloger |
| libgstreamer-plugins-base1.0-0 | 1.26.2-1 | BSD-3-Clause, CC-BY-SA-4.0, GPL-2.0-or-later, LGPL-2.0-or-later, LGPL-2.1-or-later | dpkg-db-cataloger |
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
| libmhash2 | 0.9.9.9-10 | LGPL-2.0-only | dpkg-db-cataloger |
| libminizip1t64 | 1:1.3.dfsg+really1.3.1-1+b1 | Zlib | dpkg-db-cataloger |
| libmount1 | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libmp3lame0 | 3.100-6+b3 | BSD-3-Clause, GPL-1.0-only, GPL-1.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libmpg123-0t64 | 1.32.10-1 | LGPL-2.1-only | dpkg-db-cataloger |
| libmspack0t64 | 0.11-1.1+b1 | LGPL-2.1-only | dpkg-db-cataloger |
| libmspub-0.1-1 | 0.1.4-3+b5 | MPL-2.0 | dpkg-db-cataloger |
| libmwaw-0.3-3 | 0.3.22-1+b2 | MPL-2.0 | dpkg-db-cataloger |
| libmythes-1.2-0 | 2:1.2.5-1+b2 |  | dpkg-db-cataloger |
| libncursesw6 | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libnet-http-perl | 6.23-1 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libnet-ssleay-perl | 1.94-3 | Artistic-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libnettle8t64 | 3.10.1-1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnghttp2-14 | 1.64.0-1.1 | BSD-2-Clause, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libnghttp3-9 | 1.12.0-1~bpo13+1 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT | dpkg-db-cataloger |
| libngtcp2-16 | 1.16.0-1~bpo13+2 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libngtcp2-crypto-gnutls8 | 1.16.0-1~bpo13+2 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libngtcp2-crypto-ossl0 | 1.16.0-1~bpo13+2 | FSFAP, FSFUL, FSFULLR, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, MIT | dpkg-db-cataloger |
| libnpth0t64 | 1.8-3 | LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libnspr4 | 2:4.36-1 | MPL-2.0 | dpkg-db-cataloger |
| libnss3 | 2:3.110-1 | MPL-2.0, Zlib | dpkg-db-cataloger |
| libnumbertext-1.0-0 | 1.0.11-4+b2 | BSD-3-Clause, CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libnumbertext-data | 1.0.11-4 | BSD-3-Clause, CC-BY-SA-3.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| libodfgen-0.1-1 | 0.1.8-2+b2 | MPL-2.0 | dpkg-db-cataloger |
| libogg0 | 1.3.5-3+b2 | BSD-3-Clause | dpkg-db-cataloger |
| libopenh264-8 | 2.6.0+dfsg-2 | Apache-2.0, BSD-2-Clause, MPL-2.0 | dpkg-db-cataloger |
| libopenjp2-7 | 2.5.3-2.1~deb13u1 | Libpng, libtiff, MIT, Zlib | dpkg-db-cataloger |
| libopus0 | 1.5.2-2 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| liborc-0.4-0t64 | 1:0.4.41-1 | BSD-2-Clause, BSD-3-Clause | dpkg-db-cataloger |
| liborcus-0.20-0 | 0.20.2-2~bpo13+1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, MPL-2.0 | dpkg-db-cataloger |
| liborcus-parser-0.20-0 | 0.20.2-2~bpo13+1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, MIT, MPL-2.0 | dpkg-db-cataloger |
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
| libpng16-16t64 | 1.6.48-1+deb13u1 | Apache-2.0, BSD-3-Clause, GPL-2.0-only, GPL-2.0-or-later, Libpng | dpkg-db-cataloger |
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
| libreoffice | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-base | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-base-core | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-base-drivers | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-calc | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-common | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-core | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-draw | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-impress | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-math | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-report-builder-bin | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-style-colibre | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-base | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-calc | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-common | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-draw | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-impress | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-math | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-uiconfig-writer | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libreoffice-writer | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
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
| libsndfile1 | 1.2.2-2+b1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, FSFAP, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, NTP | dpkg-db-cataloger |
| libsqlite3-0 | 3.46.1-7 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| libssh2-1t64 | 1.11.1-1 | ISC | dpkg-db-cataloger |
| libssl3t64 | 3.5.4-1~deb13u1 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
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
| libtiff6 | 4.7.0-3+deb13u1 |  | dpkg-db-cataloger |
| libtimedate-perl | 2.3300-2 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| libtinfo6 | 6.5+20250216-2 | BSD-3-Clause, X11 | dpkg-db-cataloger |
| libtry-tiny-perl | 0.32-1 |  | dpkg-db-cataloger |
| libudev1 | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| libunistring5 | 1.3-2 | BSD-3-Clause, GFDL-1.2-or-later, GFDL-1.3-or-later, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, Unicode-DFS-2016, X11, BSD-3-Clause, GFDL-1.2-or-later, GFDL-1.3-or-later, ISC, Unicode-DFS-2016 | dpkg-db-cataloger |
| libuno-cppu3t64 | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libuno-cppuhelpergcc3-3t64 | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libuno-purpenvhelpergcc3-3t64 | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libuno-sal3t64 | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| libuno-salhelpergcc3-3t64 | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
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
| libxml-parser-perl | 2.47-1+b3 | GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
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
| openjdk | 21.0.10 |  | java-jvm-cataloger |
| openssl | 3.5.4-1~deb13u1 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
| openssl-provider-legacy | 3.5.4-1~deb13u1 | Apache-2.0, GPL-1.0-only, GPL-1.0-or-later | dpkg-db-cataloger |
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
| python3-jaraco.context | 6.0.1-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-jaraco.functools | 4.1.0-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-jaraco.text | 4.0.0-1 | GPL-2.0-only, GPL-2.0-or-later | dpkg-db-cataloger |
| python3-minimal | 3.13.5-1 |  | dpkg-db-cataloger |
| python3-more-itertools | 10.7.0-1 |  | dpkg-db-cataloger |
| python3-pkg-resources | 78.1.1-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| python3-setuptools | 78.1.1-0.1 | Apache-2.0, BSD-3-Clause | dpkg-db-cataloger |
| python3-typeguard | 4.4.2-1 |  | dpkg-db-cataloger |
| python3-typing-extensions | 4.13.2-1 |  | dpkg-db-cataloger |
| python3-uno | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
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
| stdlib | go1.25.5 | BSD-3-Clause | go-module-binary-cataloger |
| stdlib | go1.25.5 | BSD-3-Clause | go-module-binary-cataloger |
| systemd | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| systemd-sysv | 257.9-1~deb13u1 | CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| sysvinit-utils | 3.14-4 | GPL-2.0-only, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-only, LGPL-2.1-only, LGPL-2.1-or-later | dpkg-db-cataloger |
| tar | 1.35+dfsg-3.1 | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| tini | 0.19.0-3+b5 |  | dpkg-db-cataloger |
| tomli | 2.0.1 |  | python-installed-package-cataloger |
| ttf-mscorefonts-installer | 3.8.1 |  | dpkg-db-cataloger |
| typeguard | 4.3.0 | MIT | python-installed-package-cataloger |
| typeguard | 4.4.2 | MIT | python-installed-package-cataloger |
| typing-extensions | 4.12.2 |  | python-installed-package-cataloger |
| typing-extensions | 4.13.2 | PSF-2.0 | python-installed-package-cataloger |
| tzdata | 2025b-4+deb13u1 |  | dpkg-db-cataloger |
| ucf | 3.0052 | GPL-2.0-only | dpkg-db-cataloger |
| uno-libs-private | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| ure | 4:25.8.4-1~bpo13+1 | Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-SA-3.0, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.0-only, LGPL-3.0-only, LGPL-3.0-or-later, MIT, MPL-1.1, MPL-2.0 | dpkg-db-cataloger |
| util-linux | 2.41-5 | BSD-2-Clause, BSD-3-Clause, BSD-4-Clause, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, ISC, LGPL-2.0-only, LGPL-2.0-or-later, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later | dpkg-db-cataloger |
| wget | 1.25.0-2 | GFDL-1.2-only, GPL-3.0-only | dpkg-db-cataloger |
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
