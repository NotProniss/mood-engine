# Mood Engine

A standalone, offline engine for modeling inspectable emotional state, with an optional Hermes Agent plugin adapter.

## Current capabilities

- Five bounded emotions: joy, sadness, anger, fear, and disgust
- Deterministic response guidance derived from expression signals
- In-memory runtime coordinator for the full event-to-guidance pipeline
- Configurable cheerful baseline values in `config/baseline_rules.json`
- Data-driven event effects in `config/emotion_rules.json`
- Contextual appraisal for explained absences (`EventContext`)
- Configurable half-lives in `config/decay_rules.json`
- Versioned runtime state persistence
- Float precision internally, whole-number floor-rounded display values

## Development

```bash
.venv/bin/python -m pytest
```

## Hermes plugin development

This repository is structured so it can be copied directly into Hermes' user
plugin directory during the early GitHub-first phase.

```bash
mkdir -p ~/.hermes/plugins
cp -a mood-engine ~/.hermes/plugins/mood-engine
hermes plugins enable mood-engine
```

After restarting Hermes, the plugin is discovered from its `plugin.yaml` and
root `__init__.py`. The current adapter is intentionally inert while the
standalone integration hooks are being designed; the reusable engine is in the
`mood_engine/` package and can be tested without Hermes.

The eventual install flow may use a pip entry point, but manual repository
installation keeps this first version easy to inspect and remove.

## Runtime state

The runtime state is deliberately separate from configuration. It may look like:

```json
{
  "emotions": {
    "anger": 0.0,
    "disgust": 0.0,
    "fear": 3.5,
    "joy": 42.7,
    "sadness": 8.2
  },
  "updated_at": "2026-07-16T12:00:00+00:00",
  "version": 1
}
```

Loading a state applies decay for the time since `updated_at`. The first prototype does not connect to Hermes behavior or send messages.
