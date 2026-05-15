# Review Checklist

Use this checklist when reviewing Codex output.

## 1. Scope

- Did the PR stay inside the requested milestone?
- Did it avoid premature Godot/full-game work?
- Did it avoid adding unnecessary dependencies?

## 2. Architecture

- Is combat logic UI-free?
- Is config read from JSON at runtime?
- Is xlsx only used by exporter/tooling?
- Is C# host only invoking/reading, not duplicating combat rules?
- Is HTML viewer only consuming replay/report?

## 3. Determinism

- Does every battle accept a seed?
- Does same seed + same config generate same replay?
- Is randomness wrapped in one deterministic RNG module?

## 4. Data validation

- Are duplicate ids detected?
- Are missing references detected?
- Are invalid numeric fields detected?
- Are error messages useful?

## 5. Replay

- Does replay contain enough information to reconstruct visible battle state?
- Are events typed consistently?
- Are tick values stable?
- Are source/target ids resolvable?

## 6. Report

- Does report explain output, tanking, kills, and skill triggers?
- Does it include key moments?
- Does it avoid vague statements that cannot be traced to events?

## 7. Tests

- Are tests runnable locally?
- Do tests cover determinism?
- Do tests cover one skill or synergy?
- Do tests cover at least one invalid config?

## 8. Developer experience

- Are commands documented?
- Are generated outputs easy to find?
- Are errors readable?
- Is the first demo battle easy to run?

## 9. Completion report

The Codex report must include:

- changed files
- commands run
- test output
- generated artifacts
- known limitations
- next step recommendation
