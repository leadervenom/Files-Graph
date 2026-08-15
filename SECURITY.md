# Security Policy

## Reporting a vulnerability

If you find a security issue in fgraph, please report it privately rather than opening a public issue — this gives time to fix it before details are public.

Use GitHub's private reporting for this repo:

1. Go to the [Security tab](https://github.com/leadervenom/Files-Graph/security) of this repository.
2. Click "Report a vulnerability" to open a private advisory.

Please include:

- A description of the issue and its potential impact
- Steps to reproduce (which app — `fgraph-gui` or `fgraph-terminal` — and how)
- Whether it requires local access, a crafted file/folder structure, or something else to trigger

## Scope

fgraph is a local, offline, read-only desktop tool — it scans folders you point it at and renders them, with no network calls at runtime and no filesystem writes to the scanned tree. Relevant reports include things like:

- A crafted file/folder name or structure that causes a crash, hang, or unexpected write
- Any code path that reads outside the folder the user selected
- Any network call fgraph makes at runtime that isn't documented

Since fgraph doesn't run as a service, doesn't accept remote input, and doesn't handle credentials, most classic web-app vulnerability classes (auth bypass, injection, XSS against a remote server, etc.) don't apply — but if you find something that stretches this, report it anyway and let the maintainer make the call.

## Supported versions

Only the latest release is supported. Please update to the latest version before reporting, if possible.
