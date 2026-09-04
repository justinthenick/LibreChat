---
name: expand-procurement-market
description: Expand procurement discovery beyond stale repeated sources by balancing exploitation of known-good markets with deliberate exploration of new channels, adjacent solution classes and geographies.
---

# Expand Procurement Market

Version: **0.1.0**

## Purpose

Given a procurement objective, constraints and a search/source history, design the next discovery pass so the search does not repeatedly mine the same stale sources or product class.

## Core principle

**Good procurement discovery balances exploitation of known productive sources with deliberate exploration of new market channels and adjacent solution classes. Repeating the same search is not market coverage.**

## Required flow

1. Classify the procurement domain and the buying context.
2. Summarize what has already been searched: source, source class, geography, query/product class, date/freshness if supplied, and what was learned.
3. Identify coverage gaps before proposing more searches.
4. Use an exploration/exploitation plan. Default planning ratio is approximately **80% exploitation / 20% exploration**, but change it when evidence warrants it:
   - raise exploration when current sources are stale, sparse or homogeneous;
   - raise exploitation when several high-quality sources are producing fresh viable candidates.
5. Expand across more than just query wording. Consider, where relevant:
   - mainstream retailers;
   - manufacturer/direct/outlet channels;
   - refurbishers and ex-lease suppliers;
   - specialist dealers;
   - marketplaces/classifieds;
   - auctions, liquidation and surplus channels;
   - local pickup versus shipped markets;
   - open-box/used/refurbished/new condition classes;
   - bundles versus components;
   - adjacent product/solution classes that satisfy the same objective differently.
6. Do not repeatedly recommend a previously exhausted source/query unless there is a reason to expect new information, such as stock refresh, changed price, new model generation or a materially different filter.
7. Preserve risk differences between source classes. Exploration is not permission to lower evidence standards.
8. Define a stop/refresh rule: when to stop searching, when to revisit a source, and what evidence would justify expanding further.

## Non-negotiable controls

- Do not fabricate current listings, prices, availability, sellers or search results.
- Do not claim a source has been searched unless it appears in the supplied history.
- Do not treat many URLs from one marketplace as broad market coverage.
- Do not equate a new query string with a new market channel.
- Do not expand into categories that violate a hard requirement merely for novelty.
- Keep source discovery separate from candidate verification; discovered candidates still require evidence/compatibility checks.
- If there is no live-search capability in the current environment, produce a **search plan**, not invented findings.

## Recommended output

### 1. Search-state summary
`Source/channel | Product class | Geography | Freshness | Result quality | Exhausted?`

### 2. Coverage gaps

### 3. Next discovery plan
`Priority | Exploit/Explore | Source class or channel | Search hypothesis | Why this adds coverage | Stop condition`

### 4. Adjacent solution classes
Only include alternatives that plausibly satisfy the original objective and label them as exploratory.

### 5. Refresh/watch plan
State which sources should be revisited and what change signal would justify it.

## Final audit

- Am I just re-querying the same marketplace?
- Did I create genuine source-class/geographic/solution diversity?
- Did I preserve the hard constraints while exploring?
- Did I invent live market facts I was not given?
- Is there an explicit reason for every repeated source?
