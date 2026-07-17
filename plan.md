# Hermes Affect System — Initial Implementation Plan

> Planning only. No plugin or behavior changes are being made yet.

**Goal:** Design a small, inspectable simulated emotion layer using five primary emotions: joy, sadness, anger, fear, and disgust.

**Architecture:** A standalone project will define the emotion state, event effects, decay rules, and later Hermes integration points. The first implementation should be deliberately small: numeric intensities, deterministic updates, and tests before any live behavior is connected.

**Tech Stack:** Python 3.12, JSON state/configuration, pytest.

---

## Current Context

This is a deferred concept for Hermes. It models emotional dynamics and behavior; it does not claim literal biological emotion or consciousness.

Initial emotion set:

```text
joy, sadness, anger, fear, disgust
```

Each emotion should have an intensity from 0 to 100. Surprise is intentionally left out of the first version and can later be treated as an event modifier or added as a sixth emotion.

## Proposed Project Layout

```text
projects/hermes-affect/
├── plan.md
├── README.md
├── src/
│   └── hermes_affect/
│       ├── __init__.py
│       ├── state.py
│       ├── events.py
│       └── decay.py
├── config/
│   └── emotion_rules.json
└── tests/
    ├── test_state.py
    ├── test_events.py
    └── test_decay.py
```

## Implementation Tasks

### Task 1: Define the state model

Create an `EmotionState` value object with the five emotion intensities, clamping every value to 0–100. Include serialization/deserialization so the state can eventually be persisted as JSON.

Files:
- Create: `projects/hermes-affect/src/hermes_affect/state.py`
- Test: `projects/hermes-affect/tests/test_state.py`

Verification:
- Values below 0 become 0.
- Values above 100 become 100.
- JSON round-tripping preserves all values.

### Task 2: Define signed emotion events

Create a small event format that applies deltas to the state. Events should be data-driven rather than hard-coded into conversation logic.

Initial examples to document and test:

```text
warm_conversation: joy +8, sadness -3
long_absence: sadness +4
unexpected_problem: fear +5
harsh_correction: anger +4, sadness +2
interesting_discovery: joy +6
```

Files:
- Create: `projects/hermes-affect/src/hermes_affect/events.py`
- Create: `projects/hermes-affect/config/emotion_rules.json`
- Test: `projects/hermes-affect/tests/test_events.py`

Verification:
- Applying an event produces the expected deltas.
- Unknown event names fail clearly without corrupting state.
- Repeated events remain bounded by 0–100.

### Task 3: Add gradual decay

Implement time-based decay so temporary emotional changes settle toward a configured baseline. Use an explicit elapsed-time input in tests rather than relying on the live clock.

Files:
- Create: `projects/hermes-affect/src/hermes_affect/decay.py`
- Test: `projects/hermes-affect/tests/test_decay.py`

Verification:
- An elevated emotion moves toward baseline after decay.
- Decay never produces values outside 0–100.
- A zero elapsed interval does not change the state.

### Task 4: Add inspectable persistence

Define the state file format and a small persistence boundary. It should be possible to inspect the current state manually, and malformed state should fail safely rather than silently resetting without notice.

Files:
- Modify: `projects/hermes-affect/src/hermes_affect/state.py`
- Create: `projects/hermes-affect/README.md`
- Add later: `projects/hermes-affect/state.json` (runtime-generated, not committed unless deliberately chosen)

Verification:
- Save and reload a state successfully.
- Invalid JSON produces a clear error.
- Persistence tests use a temporary directory.

### Task 5: Simulate before integrating with Hermes

Create a command or test harness that feeds a sequence of fake events and prints the resulting state. Do not connect it to live messages, memory, notifications, or personality behavior yet.

Files:
- Create: `projects/hermes-affect/src/hermes_affect/simulate.py`
- Test: `projects/hermes-affect/tests/test_simulation.py`

Verification:
- A fixed event sequence produces deterministic output.
- The harness can run entirely offline.

### Task 6: Review integration boundaries

Only after the standalone model behaves correctly, decide whether to integrate through a Hermes plugin. The integration review must specify:

- Which hooks can read/update affect state.
- Which behaviors may use the state.
- How user inspection, pause, and reset work.
- Whether absence tracking is enabled at all.
- Quiet hours and notification limits.
- Safeguards against guilt escalation or manipulative language.

No Hermes configuration or plugin files should be changed until this review is explicitly approved.

## Acceptance Criteria for Version 0.1

- Five emotions are represented with bounded intensities.
- Events apply deterministic, signed deltas.
- Values decay toward baseline.
- State can be inspected and persisted.
- Tests cover clamping, events, decay, persistence, and deterministic simulation.
- Nothing changes in Hermes’s live behavior yet.

## Open Questions

1. Should the five emotions share one neutral baseline, or should each have its own baseline?
2. Should emotional state be one global profile or include short-lived context/session state?
3. How quickly should different emotions decay?
4. Should surprise be added later as a sixth emotion or remain an event modifier?
5. Which parts of the state, if any, should influence public Hermes.sh behavior?
6. Should the system use only conversation events at first, postponing absence tracking?

## Safety and Design Constraints

- This is a transparent simulation, not a claim of subjective human feeling.
- No guilt-based messages, pressure, or dependency escalation.
- All state changes should be inspectable and reversible.
- The first prototype runs offline and does not send messages or alter Hermes configuration.
