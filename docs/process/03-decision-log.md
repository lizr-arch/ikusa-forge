# Decision Log

Use this file to record decisions that should survive long conversations.

## Template

```markdown
## YYYY-MM-DD - Decision title

### Decision

### Context

### Alternatives considered

### Consequences

### Revisit trigger
```

---

## 2026-05-15 - Use C# host + Python simulator for Phase 1

### Decision

Phase 1 uses C# as host and Python as the combat simulator.

The first implementation should call Python as a subprocess rather than embed Python.NET.

### Context

The project needs fast rules iteration, hot-reload-like workflow, deterministic simulation, and clear replay/report output.

### Alternatives considered

1. Godot GDScript first
2. Godot C# first
3. C# + embedded Python.NET immediately
4. Python-only prototype
5. C# host + Python subprocess

### Consequences

Pros:

- faster iteration
- simple debugging
- simulator can be tested without engine
- crash isolation
- future migration path to Python.NET or C#

Cons:

- subprocess overhead
- two-language boundary
- eventual runtime integration work remains

### Revisit trigger

Revisit when:

- one battle run becomes too slow
- Godot integration requires in-process execution
- packaging becomes a blocker
- Python/C# data DTO drift becomes painful
