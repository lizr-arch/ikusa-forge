# Project Brief

## Working title

**Ikusa Forge**

## Subtitle

Formation Auto-Battle Lab

## One-line pitch

A tactical auto-battle system where players win by composing units, weapons, skills, synergies, and formations before the fight.

## Core loop

```text
Scout enemy
  -> build squad
  -> assign weapons / skills
  -> choose formation
  -> simulate automatic battle
  -> inspect replay and report
  -> adjust build
```

## Design focus

The first version should prove:

- formation matters
- equipment matters
- synergies matter
- battle results are explainable
- replay/debug tools make iteration fast

## Anti-goals

Do not start with:

- complex art
- complex animation
- a full campaign
- Godot scene polish
- large content volume

The first useful artifact is a **combat lab**, not a finished game demo.
