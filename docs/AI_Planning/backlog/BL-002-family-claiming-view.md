# BL-002 — Family claiming / voting view for downsizing

- **Status:** parked
- **Origin:** [summary_suggestions GOALS.md](../support/summary_suggestions/GOALS.md) WS-5 (was ⚠️ MAYBE). Moved to the backlog by owner review on 2026-11-24.

## Idea
During downsizing or estate work, family members browse items marked Gift/Undecided and claim or vote on what they want. Conflicts are shown to the household owner to resolve.

## Why deferred
Family members would each need access, either accounts on the client's install or share links (BL-001). The core downsizing workflow (disposition + recipient assigned by the owner, in WS-5) works without it.

## What it would take
- A claims table (item, family member, preference rank, note, timestamp).
- A claiming page per family member, and a conflict-resolution view for the owner.
- Reuse of WS-4 accounts (member role) or BL-001 links.

## Depends on
WS-5 disposition/recipient, plus WS-4 accounts or BL-001.

## Revisit when
WS-5 is done and a real downsizing job shows that assigning recipients by hand is a bottleneck.
