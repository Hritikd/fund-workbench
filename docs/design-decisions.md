# Design decisions

## A claims ledger instead of a chat window

A chat response is difficult to audit and reuse. A claim record has a topic, statement, evidence status, source ID, quote, confidence, and note. That structure supports filtering, comparison, export, and later correction.

## Deterministic fallback

The project must be useful before a user configures a paid model. The fallback extracts checkable sentences with transparent rules. It is less semantically capable and labels its output accordingly.

## Schema-constrained AI

AI-assisted extraction uses the Responses API and a Pydantic schema. Schema adherence prevents missing fields; post-model validation still enforces business rules and source integrity.

## No automated investment verdict

The thesis score measures literal term coverage for routing. It is deliberately labelled as a triage score and exposes every matched, missing, and excluded term. The final memo remains “Needs human review.”

## Local first, no persistence

The first release avoids accounts, databases, and telemetry. This reduces setup and data exposure. It also means there is no collaboration, history, authentication, or durable audit log yet.

## Portable artifacts

JSON and Markdown exports let teams connect the output to their existing document, CRM, or approval process. The project avoids defining another proprietary workspace format.
