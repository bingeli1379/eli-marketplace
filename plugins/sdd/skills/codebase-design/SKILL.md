---
name: codebase-design
description: >
  Use when designing or reviewing a module's interface — deciding how much surface to
  expose, where to put a seam, whether to introduce an abstraction, or whether code is
  testable through its interface. Provides the deep-module vocabulary (depth, seam,
  adapter, leverage, locality) shared by the architect, reviewers, and engineers.
  Stack-agnostic; complements clean-architecture (layering) and ddd (domain model).
user-invocable: false
---

# Codebase Design

Design **deep modules**: a lot of behaviour behind a small interface, placed at a clean
seam, testable through that interface. Use this language and these principles wherever
code is being designed or restructured. The aim is leverage for callers, locality for
maintainers, and testability for everyone.

This is the **interface-shape** lens. It is orthogonal to:

- **`clean-architecture`** — *where* code lives (Domain / Application / Infrastructure / Api layering). A mandated layer is never "over-engineering"; depth applies *within* each layer.
- **`ddd`** — *what* the domain means (aggregates, value objects, events). Depth says nothing about domain semantics, only about the size of the surface you expose.

When all three apply, layering and domain boundaries win on *placement*; this skill governs *how big the interface at that placement should be*.

## Glossary

Use these terms exactly — don't substitute "component," "service," "API," or "boundary." Consistent language is the whole point.

- **Module** — anything with an interface and an implementation. Deliberately scale-agnostic: a function, class, package, or tier-spanning slice. *Avoid*: unit, component, service.
- **Interface** — everything a caller must know to use the module correctly: the type signature, but also invariants, ordering constraints, error modes, required configuration, and performance characteristics. *Avoid*: API, signature (too narrow — they refer only to the type-level surface).
- **Implementation** — what's inside a module, its body of code. Distinct from **Adapter**: a thing can be a small adapter with a large implementation (a Postgres repo) or a large adapter with a small implementation (an in-memory fake).
- **Depth** — leverage at the interface: how much behaviour a caller (or test) can exercise per unit of interface they have to learn. A module is **deep** when a large amount of behaviour sits behind a small interface, **shallow** when the interface is nearly as complex as the implementation.
- **Seam** *(Michael Feathers)* — a place where you can alter behaviour without editing in that place; the *location* at which a module's interface lives. Where to put the seam is its own design decision, distinct from what goes behind it. *Avoid*: boundary (overloaded with DDD's bounded context).
- **Adapter** — a concrete thing that satisfies an interface at a seam. Describes *role* (what slot it fills), not substance (what's inside).
- **Leverage** — what callers get from depth: more capability per unit of interface they learn. One implementation pays back across N call sites and M tests.
- **Locality** — what maintainers get from depth: change, bugs, knowledge, and verification concentrate in one place rather than spreading across callers. Fix once, fixed everywhere.

## Deep vs shallow

**Deep module** = small interface + lots of implementation:

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│  Deep Implementation│  ← Complex logic hidden
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (avoid):

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing an interface, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can be internally composed of small, mockable, swappable parts — they just aren't part of the interface. A module can have **internal seams** (private to its implementation, used by its own tests) as well as the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. If you want to test *past* the interface, the module is probably the wrong shape. (This is why deep modules and `test-driven-development` reinforce each other — a deep interface is a natural test seam.)
- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't introduce a seam unless something actually varies across it. This is the depth-side statement of the architect's lazy-by-default rule: a second implementation is the evidence that promotes a YAGNI abstraction into a justified one.

## Designing for testability

Good interfaces make testing natural:

1. **Accept dependencies, don't create them.**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Return results, don't produce side effects.**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small surface area.** Fewer methods = fewer tests needed. Fewer params = simpler test setup.

## How sdd roles use this

- **architect** (`/propose`) — when defining a contract or choosing where to put a seam, prefer the deepest interface that satisfies the spec. Record a new seam in a Decision Record only when a *second* adapter justifies it (one adapter → inline, no seam).
- **review-engineer** — apply the deletion test and the "shallow module" smell to changed code. A wrapper that only delegates (`wrapper` over-engineering tag) is a shallow module by another name; a leaking interface (caller must know internal ordering/state) is a depth failure even if it compiles.
- **engineers** — when a test is hard to write, the interface is usually wrong (too many collaborators created inside, side effects instead of return values). Fix the shape, don't mock around it.

## Rejected framings

- **Depth as ratio of implementation-lines to interface-lines** (Ousterhout): rewards padding the implementation. Use depth-as-leverage instead.
- **"Interface" as the TypeScript `interface` keyword or a class's public methods**: too narrow — interface here includes every fact a caller must know.
- **"Boundary"**: overloaded with DDD's bounded context. Say **seam** or **interface**.
