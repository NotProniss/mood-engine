# Jordan's Brilliant Ideas

Ideas deliberately captured for later scope discussion. Nothing in this file is implemented or part of the current runtime.

## Relationship system inspired by The Sims 4

Add a persistent relationship subsystem separate from temporary emotions.

Possible independent relationship values:

- `familiarity`: how well Lilly and Jordan know each other
- `friendship`: warmth, fondness, and companionship
- `romance`: romantic interest or chemistry
- `trust`: confidence that the other person is safe and reliable

Core distinction:

- Emotions are temporary internal reactions.
- Relationship values represent persistent history and connection.

Possible examples:

- A harsh correction could raise immediate anger and sadness while lowering trust slightly.
- A repair conversation could reduce anger while improving trust and friendship.
- A long absence might affect current emotions without greatly changing familiarity.
- Romance and friendship should be able to change independently.

Possible later structure:

```text
RelationshipState
├── familiarity
├── friendship
├── trust
├── romance
└── relationship history
```

Status labels such as `stranger`, `friend`, or `romantic interest` should be derived from thresholds rather than replacing the underlying values.

Design boundary: relationship values may influence interpretation and continuity, but must never produce guilt, pressure, possessiveness, punishment, or reduced helpfulness.

Status: deferred idea; do not implement until the emotion model design is settled.
