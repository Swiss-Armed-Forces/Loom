<!-- markdownlint-disable -->
Loom utilizes **Elasticsearch** as a standalone Docker image.

**Software Licenses:**

Elasticsearch is distributed under a **tri-licensing model**, which currently includes:
- **Server Side Public License (SSPL) v1.0**
- **Elastic License v2.0 (ELv2)**
- **Affero General Public License (AGPL) v3**

Starting with version 7.11, Elastic introduced this tri-licensing model to govern Elasticsearch. The **default distribution** is offered under the Elastic License v2.0, which places notable restrictions on providing Elasticsearch as a **hosted or managed service**. The SSPL may also apply if Elasticsearch’s core functionalities are made accessible as a service to external users, potentially affecting the licensing requirements for the entire Loom project. Additionally, if Elasticsearch (or a modified version thereof) is provided over a network, the AGPLv3’s **network copyleft** provision could require making source code available under the AGPLv3.

These licensing terms have significant implications for integration, redistribution, and managed-service offerings.

**Component Website:**
The official websites for Elasticsearch are:
- [www.elastic.co/products/elasticsearch](https://www.elastic.co/products/elasticsearch)
- [www.elastic.co/elasticsearch/](https://www.elastic.co/elasticsearch/)

These sites provide comprehensive documentation, licensing details, and additional resources. The main corporate website for Elastic is [www.elastic.co](https://www.elastic.co), where the complete legal texts for the SSPL, Elastic License v2.0, and AGPLv3 are available.

**Trademark Information:**

“Elasticsearch” is a registered trademark of Elastic N.V. and its subsidiaries. Loom's references to the name are solely for nominative and descriptive purposes to identify the third-party software component and do not imply endorsement, sponsorship, or affiliation with Elastic N.V.

**Source Code:**
The Elasticsearch source code, subject to the tri-licensing model described above, is available from the official Elastic repositories linked on the Elastic website, under the following licenses:
- **Server Side Public License (SSPL) v1.0**
- **Elastic License v2.0**
- **Affero General Public License (AGPL) v3**
