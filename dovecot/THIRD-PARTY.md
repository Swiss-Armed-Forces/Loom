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

The Dovecot IMAP server software is developed and maintained by Open-Xchange (formerly Dovecot Oy, acquired in 2015). The name "Dovecot" in the context of the email server software is associated with Open-Xchange. No registered trademark for "Dovecot" as a software product has been confirmed at the time of this writing. Use of the name in Loom's materials is solely for nominative and descriptive purposes to identify the third-party software component and does not imply endorsement or affiliation with Open-Xchange.

**Source Code:** <https://github.com/dovecot/core>
