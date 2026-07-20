# Mood Engine

A standalone, offline engine for modeling inspectable emotional state, with an optional Hermes Agent plugin adapter.

See the [roadmap](plan.md) for planned work including additional emotions,
relationship bars, semantic analysis improvements, and bounded response
self-reinforcement.

## Current capabilities

- Five bounded emotions: joy, sadness, anger, fear, and disgust
- Deterministic response guidance from the focused emotion
- In-memory runtime coordinator for the full event-to-guidance pipeline
- Configurable baseline values in `config/baseline_rules.json` (currently all zero)
- Data-driven event effects in `config/emotion_rules.json`
- Conversation-context classification for completed chat rounds
- Neutral `Casual Conversation` baseline with no emotion change
- Configurable mood-swing presets for fixed or confidence/intensity-scaled deltas
- Centralized tuning knobs in `config.yml` (from tracked `config.example.yml`) for classifier, mood swing, decay, and baselines
- Configurable half-lives in the centralized YAML configuration
- Versioned runtime state persistence
- Float precision internally, whole-number floor-rounded display values

## Focused response

Response guidance selects one focused emotion and its raw intensity.

```text
focus=<emotion>; intensity=<0-100>
```

The focused emotion is whichever stored emotion currently has the highest value.
When all values are zero, focus is `neutral` and intensity is `0`.

Joy currently has four tone states:

- intensity `1-24` → `content`
- intensity `25-49` → `happy`
- intensity `50-74` → `excited`
- intensity `75-100` → `ecstatic`

Anger currently has four tone states:

- intensity `1-24` → `annoyed`
- intensity `25-49` → `irritated`
- intensity `50-74` → `aggressive`
- intensity `75-100` → `scathing`

Sadness currently has four tone states:

- intensity `1-24` → `downcast`
- intensity `25-49` → `sad`
- intensity `50-74` → `heavy`
- intensity `75-100` → `sorrowful`

Fear currently has four tone states:

- intensity `1-24` → `uneasy`
- intensity `25-49` → `wary`
- intensity `50-74` → `anxious`
- intensity `75-100` → `horrified`

Disgust currently has four tone states:

- intensity `1-24` → `put_off`
- intensity `25-49` → `grossed_out`
- intensity `50-74` → `disgusted`
- intensity `75-100` → `repulsed`

The prompt-facing payload is intentionally minimal:

```text
focus=<emotion>; tone=<label>
```

If a tone profile has optional behavior guidance, it is appended:

```text
focus=sadness; tone=sorrowful; behavior=Speak gently and reflectively. Avoid cheerfulness, teasing, and excessive enthusiasm.
```

Neutral and tones without profiles omit `behavior` entirely. `/mood status` still
exposes intensity for inspection, but it is not sent to the model until we
deliberately add another response dimension.

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

## In-session command

The plugin registers an explicit slash command for controlled testing:

```text
/mood status
/mood set anger 100
/mood set joy 42.5
/mood set sadness 0
/mood reset
```

`/mood status` reports:

- the last classified conversation type, classifier confidence, and classifier intensity for this session;
- all persistent emotion values;
- focused emotion, raw intensity, tone, and optional behavior guidance.

Conversation classification is session-local and resets to Casual Conversation when
Hermes restarts or the session is reset. After changing plugin code, restart Hermes
before testing so the running process loads the new plugin module.

Supported emotions are `joy`, `sadness`, `anger`, `fear`, and `disgust`. Values
must be numbers from 0 through 100. `/mood reset` restores all five values to
the configured baselines. The command updates the live cached runtime
and persists the result immediately, so the next `pre_llm_call` can derive new
guidance without restarting the process.

## Chat-round classification

After a completed turn, the plugin classifies the user's message into one simple
conversation context: `casual`, `pleasant`, `funny`, `awkward`, `unpleasant`,
`offensive`, or `hurtful`. Casual is neutral and creates no event. The other
contexts map to exactly one primary emotion:

- `pleasant` → joy +1
- `funny` → joy +2
- `awkward` → fear +1
- `unpleasant` → disgust +1
- `offensive` → anger +1
- `hurtful` → sadness +1

The vocabulary and event labels are configuration-driven. `config/emotion_rules.json`
is the source of truth for allowed labels and their emotion deltas;
`config/conversation_signals.json` supplies the deterministic fallback patterns.
The preferred classifier mode is semantic: it calls Hermes' active model through
`ctx.llm.complete_structured(...)` and asks for a schema-validated label,
confidence, and intensity. If semantic analysis is unavailable, invalid, or below
the confidence threshold, the configured pattern fallback is used. Unmatched or
ambiguous wording remains Casual Conversation.

The active mood-swing preset is configured in `config.yml` under
`mood_swing.active_preset`. Copy `config.example.yml` to `config.yml` to create
a local override; if no override exists, the plugin automatically uses the
example defaults. `default` preserves the original fixed event deltas.
`beta` applies:

```text
base delta × ((1 + confidence) + (1 + intensity))
```

This experimental scaling is bounded by the emotion state's `0..100` limits.
Change `active_preset` and restart Hermes to switch behavior.

After changing plugin code, restart Hermes before testing so the running process
loads the new module. Avoid editing `state.json` manually while Hermes is running:
the plugin keeps an in-memory runtime and may write that cached state back during
session reset.

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
