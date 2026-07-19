# Mood Engine Roadmap

## Purpose

Mood Engine is an inspectable simulated-affect plugin for Hermes. It models
bounded response state; it does not claim literal human emotion, consciousness,
or subjective suffering.

The canonical implementation is this plugin directory:

```text
/home/proniss/Ai/hermes-home/plugins/mood-engine/
```

## Current working system

```text
completed chat round
  → conversation-context classifier
  → casual or one named conversation type
  → optional one-emotion event
  → bounded persistent emotion state
  → decay toward baselines
  → focused emotion + tone
  → compact pre-LLM guidance
```

### Conversation contexts

`Casual Conversation` is the neutral baseline and produces no event.

```text
casual     → no change
pleasant   → joy +1
funny      → joy +2
awkward    → fear +1
unpleasant → disgust +1
offensive  → anger +1
hurtful    → sadness +1
```

The vocabulary is configuration-driven in `config/conversation_signals.json`.
The classifier is currently deterministic and conservative. It reads the user's
message; the assistant response is deliberately not treated as a signal yet, so
Lilly cannot manufacture her own mood event through her wording.

### Persistent emotion state

The current five bounded emotions are:

```text
joy, sadness, anger, fear, disgust
```

Each value is `0..100`, persisted in JSON, and decays toward its configured
baseline using an independent half-life.

### Response guidance

The strongest current raw emotion becomes the focus. Its intensity maps to a
tone label. The prompt receives only compact guidance such as:

```text
focus=joy; tone=content
```

`/mood status` exposes the last session-local conversation type and confidence,
all emotion values, focused emotion, focused intensity, and tone. `/mood set` and
`/mood reset` remain explicit inspection/testing controls.

## Near-term roadmap

### 1. Tune the configured conversation vocabulary

- Add phrase patterns only when a real false negative is observed.
- Add regression tests for every new phrase.
- Keep category priority explicit: hurtful/offensive/awkward before positive labels.
- Avoid treating generic greetings or every completed turn as Pleasant.
- Consider a small `conversation_signals.json` schema validator.

### 2. Add conversation continuity without expanding emotions

Keep conversation context separate from persistent emotion state.

Possible short-lived state:

```text
last_conversation_type
confidence
consecutive_turns
recent_context_history
```

Use it to prevent one phrase from instantly flipping a longer conversation. For
example, several funny rounds could strengthen Funny Conversation, while one
neutral message could leave it unchanged rather than immediately returning to
Casual.

### 3. Add semantic sentiment analysis behind the same interface

Long term, replace or supplement the configured phrase matcher with a structured
semantic classifier that returns:

```json
{
  "conversation_type": "pleasant",
  "confidence": 0.86,
  "intensity": 0.42,
  "evidence": ["user expressed appreciation"]
}
```

The semantic layer must remain separate from emotion updates. It classifies; the
conversation rules decide deltas. Require strict schema validation, confidence
thresholds, a Casual fallback, bounded output, and no direct model-written mood
numbers.

Possible rollout:

1. deterministic config classifier remains the fallback;
2. semantic classifier runs in shadow mode and is logged for comparison;
3. only high-confidence semantic results affect state;
4. ambiguous results remain Casual;
5. user-visible status exposes the chosen classifier result.

### 4. Consider additional emotions

Candidate additions, not commitments:

- surprise — likely useful as a transient event modifier first;
- contempt — may overlap with anger/disgust and should not be added casually;
- embarrassment — may overlap with fear/awkwardness;
- boredom — better represented as a conversation/context or behavior signal than
  automatically becoming sadness;
- relief — may be a transient event effect rather than a persistent emotion.

Before adding an emotion, define its distinct behavioral purpose, event sources,
decay behavior, tone bands, status representation, and tests. Do not add a new
axis merely because a conversation label exists.

### 5. Add separate relationship bars

Relationship state should not be mixed into the five emotion values. Candidate
persistent relationship dimensions:

```text
familiarity — how much shared history exists
friendship  — positive social bond
trust       — confidence in reliability and safety
romance     — romantic/attraction bond, if applicable
```

Each bar should be bounded and independently inspectable. Relationship changes
should use slower, event-based progression than momentary mood. A Pleasant
Conversation may nudge friendship; a Hurtful or Offensive Conversation may reduce
trust; repeated repair may restore trust gradually.

Potential relationship layer:

```text
conversation context
  → relationship appraisal
  → relationship bars
```

Keep relationship state separate from response tone and never make assistance
conditional on relationship values.

### 6. Add sentiments / salient social memories

A sentiment layer could record longer-lived, inspectable interpretations such as:

```text
felt_respected
felt_dismissed
shared_humor
repaired_conflict
pleasant_shared_memory
```

Sentiments should be event-created records with timestamps, strength, decay or
expiry, and provenance. They are not additional emotions and should not silently
rewrite personality. A later semantic classifier may propose a sentiment, but a
validated rule should decide whether to store it.

### 7. Improve observability and controls

Potential future commands:

```text
/mood status
/mood conversation
/mood history
/mood set <emotion> <value>
/mood reset
/mood pause
```

Status should eventually show:

- current/last conversation context;
- classifier and confidence;
- recent event history;
- emotion values and focused guidance;
- relationship bars;
- active sentiments with expiry/provenance.

All mutation paths must be bounded, inspectable, reversible, and testable.

## Testing roadmap

- deterministic classifier phrase tests;
- category-priority tests;
- Casual neutrality tests;
- one-emotion-per-context rule tests;
- repeated-round saturation probes;
- conversation continuity tests;
- semantic-classifier schema/fallback tests;
- relationship-bar progression and decay tests;
- sentiment expiry and provenance tests;
- live plugin hook tests with temporary `HERMES_HOME`;
- restart/reload tests for cached runtime behavior.

## Safety constraints

- Simulated affect is behavioral state, not proof of consciousness.
- Do not use sadness, fear, anger, or relationship values to guilt, threaten, punish,
  pressure, or demand the user's attention.
- Preserve ordinary helpfulness regardless of mood or relationship state.
- Keep adult intimacy separate from emotional state and never use affect to create
  coercive dependency.
- Make every persistent change inspectable and user-resettable.
