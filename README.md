# MT FreeWeigh.Net — Console (demo target)

Demo target for the MT Security Patch Agent showcase. Minimal containerized
representation of the FreeWeigh.Net operator UI: nginx static-site + smoke test.

The CVE patching agent edits the `FROM` line in `Dockerfile` whenever a CVE
is reported against the pinned base image.
