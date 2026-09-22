# Security and privacy

Fund Workbench is an early open-source project. Treat it as a review aid, not a secure document room.

## Current data flow

- The local app has no database and no telemetry.
- Uploaded documents are processed in memory by the running Streamlit process.
- Deterministic mode sends nothing to a model provider.
- AI-assisted mode sends extracted source text to the configured OpenAI API account.
- AI requests set `store=False`; provider and organization retention settings still apply.
- Markdown and JSON exports are downloaded or written where the user chooses.

## User responsibilities

- Do not upload or transmit confidential material without authority.
- Never commit API keys or sensitive source documents.
- Use a secret manager or environment variable for credentials.
- Review every generated claim and memo before using it in a decision.
- Run the app locally when handling non-public data.

## Known limitations

- PDF text extraction does not perform OCR.
- Prompt injection inside documents is treated as source text, but model behavior is not a security boundary.
- Source verification checks provenance within supplied documents; it does not establish that an independent source is accurate.
- The app does not provide authentication, tenant isolation, encryption at rest, or an audit log.
- Streamlit’s default deployment settings are not a substitute for an organization’s access controls.

## Report a vulnerability

Do not open a public issue for a vulnerability or include real sensitive data in a report. Contact the maintainer privately through the repository owner’s GitHub profile with a synthetic reproduction.
