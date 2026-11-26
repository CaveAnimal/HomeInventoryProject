# BL-001 — Read-only share links for a household

- **Status:** parked
- **Origin:** [summary_suggestions GOALS.md](../support/summary_suggestions/GOALS.md) WS-4 (was ⚠️ MAYBE, proposed decision PD-5). Moved to the backlog by owner review on 2026-11-24.

## Idea
A revocable, expiring link that lets someone outside the household (a family member, an executor or an insurance adjuster) view one household's inventory without an account.

## Why deferred
Outside access conflicts with the local-first, LAN-only model (llm_vision D-001). Making it safe needs a decision on remote access that nothing in the current plan requires.

## What it would take
- A token table (household, scope, expiry, revoked flag) and a read-only view that ignores everything outside the token's scope.
- A way to reach the app from outside: the owner's VPN, or a static exported report instead of a live link. That was the earlier leaning for PD-5.

## Depends on
WS-4 households and login. The simpler alternative, a static report the client sends themselves, is covered by WS-3.

## Revisit when
A licensed client asks for remote viewing, or WS-4 settles how the app can be reached from outside.
