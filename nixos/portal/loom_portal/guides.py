"""How to install what the page hands out, per platform.

Plain data, so that `page.py` stays a renderer and the suite can assert the content
without parsing HTML.

The desktop steps are the ones `cicd/generate_client_certificate.sh` already writes into
its `README.txt`, deliberately kept in step with it: an operator issuing by hand and a
visitor using the portal are installing the same two things, and two sets of instructions
that drift is how one of them becomes wrong. The phone steps are new here, because the
script writes a file for somebody at a terminal and this page is mostly read on a phone
that has just joined the network.

Two things in here are the ones people get wrong, and both are called out in a `note`
rather than buried in a step:

  * **iOS stores a certificate and trusts it separately.** Installing the profile is not
    enough; `Certificate Trust Settings` has a switch that has to be turned on, several
    screens away from where the file was installed.
  * **A PKCS#12 bundle carries no trust.** Importing the identity does not stop the
    warning about `*.loom`; the anchor is a separate file with a separate, deliberate
    step. This is the single most skipped instruction in the whole flow.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GuideContext:
    """What the steps have to name, as this box spells it."""

    anchor_filename: str = "loom-server-ca.pem"
    identity_filename: str = "the .p12 file"
    frontend_host: str = "frontend.loom"


@dataclass(frozen=True)
class InstallGuide:
    """One platform's steps."""

    platform: str
    steps: list[str] = field(default_factory=list)
    note: str = ""


def anchor_guides(context: GuideContext) -> list[InstallGuide]:
    """Installing the certificate Loom serves, so the browser stops warning."""
    anchor = context.anchor_filename
    return [
        InstallGuide(
            platform="Android",
            steps=[
                "Tap the download above; Android saves it to Downloads.",
                "Settings, then Security and privacy, then More security settings.",
                "Encryption & credentials, then Install a certificate, "
                "then CA certificate.",
                'Confirm "Install anyway" and pick the downloaded file.',
            ],
            note=(
                "Chrome and Firefox honour a certificate installed this way. Other apps "
                "on Android 7 and later do not, which is a decision Android makes and "
                "nothing on this box can change."
            ),
        ),
        InstallGuide(
            platform="iPhone or iPad",
            steps=[
                "Tap the download above and allow the profile when Safari asks.",
                "Settings, then Profile Downloaded, then Install, "
                "and enter your passcode.",
                "Settings, General, About, Certificate Trust Settings.",
                'Turn the switch for "*.loom" on.',
            ],
            note=(
                "The last step is separate from installing the profile and is the one "
                "that is usually missed. Without it the certificate is stored and "
                "trusted for nothing."
            ),
        ),
        InstallGuide(
            platform="Firefox",
            steps=[
                "Settings, Privacy & Security, Certificates, View Certificates.",
                f"The Authorities tab, then Import, and pick {anchor}.",
                'Tick "Trust this CA to identify websites".',
            ],
            note=(
                "The tick is the point. Importing without it stores the certificate and "
                "trusts nothing."
            ),
        ),
        InstallGuide(
            platform="Windows",
            steps=[
                f"certutil -user -addstore Root {anchor}",
                "Confirm the prompt; it is asking whether to trust a new root.",
            ],
            note="Chrome and Edge both read this store.",
        ),
        InstallGuide(
            platform="macOS",
            steps=[
                f"security add-trusted-cert -r trustRoot "
                f"-k ~/Library/Keychains/login.keychain-db {anchor}",
            ],
            note="Safari and Chrome both read this keychain.",
        ),
        InstallGuide(
            platform="Linux",
            steps=[
                f"sudo cp {anchor} /usr/local/share/ca-certificates/"
                f"{anchor.replace('.pem', '.crt')}",
                "sudo update-ca-certificates",
            ],
            note=(
                f"Or pass it per call: curl --cacert {anchor} "
                f"https://{context.frontend_host}/. Chrome on Linux uses Firefox's NSS "
                "database rather than this one."
            ),
        ),
    ]


def identity_guides(context: GuideContext) -> list[InstallGuide]:
    """Installing the client certificate, so Loom lets the browser in."""
    identity = context.identity_filename
    return [
        InstallGuide(
            platform="Android",
            steps=[
                "Tap the download above.",
                "Settings, Security and privacy, More security settings, "
                "Encryption & credentials, Install a certificate.",
                "Choose VPN & app user certificate and pick the downloaded file.",
                "Leave the password prompt empty.",
            ],
        ),
        InstallGuide(
            platform="iPhone or iPad",
            steps=[
                "Tap the download above and allow the profile when Safari asks.",
                "Settings, Profile Downloaded, Install.",
                "Leave the password prompt empty.",
            ],
        ),
        InstallGuide(
            platform="Firefox",
            steps=[
                "Settings, Privacy & Security, Certificates, View Certificates.",
                f"Your Certificates, then Import, and pick {identity}.",
                "Leave the password prompt empty.",
            ],
        ),
        InstallGuide(
            platform="Chrome, Edge and Safari",
            steps=[
                f"Windows: certutil -user -importpfx My {identity}",
                f"macOS: security import {identity} "
                "-k ~/Library/Keychains/login.keychain-db",
                "Linux: the same NSS database Firefox uses, Your Certificates tab.",
            ],
        ),
        InstallGuide(
            platform="curl, mc and anything else on a terminal",
            steps=[
                "Take the .zip above instead; it holds the same certificate and its "
                "key as PEM.",
                f"curl --cacert {context.anchor_filename} --cert NAME.crt "
                f"--key NAME.key https://{context.frontend_host}/",
            ],
            note=(
                "The same call without --cert and --key must fail during the handshake. "
                "If it succeeds, mutual TLS is not actually on."
            ),
        ),
    ]
