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