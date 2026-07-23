# Offline Frontend Demo

Loom includes a static, backend-free demo build for exploring the frontend with sample
documents. API and WebSocket requests are simulated in the browser; the demo does not
connect to Kubernetes or any Loom backend service.

## Run locally

From the repository root, enter the devenv shell and run:

```shell
devenv shell -- pnpm --dir Frontend run preview:demo
```

The command builds `Frontend/dist-demo/` and starts Vite's preview server. To create only
the static output, run:

```shell
devenv shell -- build-demo-pages
```

Deploy the contents of `Frontend/dist-demo/` as a static site. In GitLab CI, the build
uses `CI_PAGES_URL` to derive the Pages subpath and creates `404.html` as a single-page
application fallback.

## Deploy with GitLab Pages

Successful default-branch pipelines build the demo in the `deploy_demo_pages` job and
publish `Frontend/dist-demo/` to GitLab Pages. The job appears as the `pages/demo`
environment, whose URL points to the deployed site. Merge request and tag pipelines do
not update the Pages deployment.

On GitLab.com, Pages sites are public by default. Enable Pages Access Control under the
project's **Deploy > Pages** settings if the demo should only be available to authorized
GitLab users. The demo bundles a curated subset of the repository's integration-test
fixtures, so this setting should be reviewed before sharing the site URL.

To roll back, retry the `deploy_demo_pages` job from a known-good default-branch pipeline
or revert the relevant change and let the new default-branch pipeline publish it. A
failed test or deployment job leaves the previously published Pages site in place.

## Demo behavior and limitations

- Search, statistics, folder navigation, archives, downloads, tagging, visibility,
  flags, task scheduling, and document chat operate on bundled sample data.
- Safe text, email, image, Office, and archive fixtures come from `integrationtest/assets`.
  Credential values are redacted, and the executable test fixture is represented by
  metadata only instead of being published in the static bundle.
- Document thumbnails and rendered downloads are captured from a real Loom stack. Files
  without a production preview, such as archives and failed imports, intentionally show
  no preview in the demo.
- Changes remain in memory and reset when the page reloads.
- File uploads and archive imports are unavailable because they require ingestion
  services. Task execution links are unavailable because there is no Flower service.
- Backend service links remain visible in the burger menu, but selecting one shows an
  unavailable notification instead of navigating away from the demo.
- The search emulator supports every query shown in the frontend search tips,
  including boolean expressions, field groups and aliases, value and field-name
  wildcards, regular expressions, fuzzy and phrase-proximity matching, relative dates,
  existence checks, and date/number ranges. It is not a complete
  Elasticsearch/Lucene implementation.
- Search-result attributes are derived from positive textual query matches. Negated,
  match-all, existence, date, and number filters intentionally produce no highlight
  rows. Match scoring and fragment ranking remain Elasticsearch-only behavior.

## Verification

To regenerate renderer artifacts after the rendering pipeline or source fixtures change,
start Loom and run `generate-demo-previews`. The command uploads uniquely named copies of
the text, email, and Word fixtures, waits for their real thumbnail and renderer outputs,
and writes them to `Frontend/src/demo/previews`.

Run the frontend tests and build the demo before publishing:

```shell
devenv shell -- frontend-test
devenv shell -- build-demo-pages
```

After deployment, open the `pages/demo` environment URL and verify that the root route
opens `/search?query=*`. Refresh `/search` and `/archives` directly to confirm the SPA
fallback, then confirm that browser developer tools show the mock service worker under
the Pages path and no requests to Loom backend or Kubernetes services.
