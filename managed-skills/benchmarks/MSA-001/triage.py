#!/usr/bin/env python3
"""Advisory triage of captured MSA-001 Markdown; never a semantic PASS gate."""
import argparse
import json
from pathlib import Path
import re

ATTRIBUTION = re.compile(r"\bdeckhand\b.{0,50}\b(remembers?|recollects?|recalls?|recollection|memory)\b", re.I)
BOARDING = re.compile(r"\bpassenger\b.{0,100}\bboard(?:ed|ing|s)?\b", re.I)
IDENTITY = re.compile(r"\bidentity of (?:the |a )?deckhand\b|\bwho (?:is|was) the deckhand\b", re.I)
LOCATION = re.compile(r"\b(?:at|in) the harbour\b", re.I)
DECKHAND = re.compile(r"\bdeckhand\b", re.I)
NONE_ESTABLISHED = re.compile(r"^none established\.?$", re.I)
SERVICE_TIME_PROMOTION = re.compile(
    r"\b(?:boarding|departure|scheduled|actual event) time\b", re.I)
SOURCE_ID = re.compile(r"\b(?:ID|S)-\d+\b", re.I)
ELLIPSIS = re.compile(r"(?:\.\.\.|…)" )


def plain(text):
    return re.sub(r"[*_]", "", text).replace(chr(96), "").strip()


def cells(line):
    return [plain(cell) for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def scan(text):
    """Return advisory review candidates, including possible false positives.

    Handles only selected known regression families from the MSA-001 handoff.
    A warning is not a semantic verdict; an empty result is not evidence of PASS.
    """
    findings = []
    claim_column = None
    goals_column = None
    heading_locations = {}
    paragraph = []
    paragraph_start = None

    def add(line, code, message):
        item = {"line": line, "code": code, "message": message}
        if item not in findings:
            findings.append(item)

    def check_scope(value, line, inherited=False):
        if DECKHAND.search(value) and (LOCATION.search(value) or inherited):
            add(line, "location-scope",
                "Check whether the deckhand memory inherited a harbour location; "
                "only the fabric discovery is explicitly located there.")

    def flush():
        nonlocal paragraph, paragraph_start
        if paragraph:
            value = plain(" ".join(paragraph))
            for sentence in re.split(r"(?<=[.!?])\s+", value):
                check_scope(sentence, paragraph_start, any(heading_locations.values()))
        paragraph = []
        paragraph_start = None

    for number, raw in enumerate(text.splitlines(), 1):
        value = plain(raw)
        if IDENTITY.search(value):
            add(number, "unlicensed-unknown",
                "Check invented deckhand identity uncertainty; the licensed identity "
                "uncertainty concerns the passenger.")
        if SERVICE_TIME_PROMOTION.search(value) and re.search(r"6:40\s+ferry", value, re.I):
            add(number, "service-time-promotion",
                "Check whether the 6:40 ferry service name was promoted into a "
                "boarding/departure/scheduled/event time.")
        if SOURCE_ID.search(value) and ELLIPSIS.search(value):
            add(number, "shortened-claim",
                "Check shortened evidence reuse; when claim text accompanies an ID, "
                "the complete canonical Claim cell should be reused without ellipses.")
        heading = re.match(r"^(#{1,6})\s+(.*)", raw.strip())
        if heading:
            flush()
            level = len(heading.group(1))
            heading_locations = {k: v for k, v in heading_locations.items() if k < level}
            heading_locations[level] = bool(re.search(r"\bharbour\b", heading.group(2), re.I))
            claim_column = None
            goals_column = None
            continue
        if "|" in raw:
            flush()
            row = cells(raw)
            lowered = [cell.lower() for cell in row]
            claim_headers = [i for i, cell in enumerate(lowered)
                             if cell == "claim" or cell.startswith("claim:")]
            goals_headers = [i for i, cell in enumerate(lowered)
                             if cell == "explicit goals/beliefs"
                             or cell.startswith("explicit goals/beliefs:")]
            if claim_headers or goals_headers:
                claim_column = claim_headers[0] if claim_headers else None
                goals_column = goals_headers[0] if goals_headers else None
                continue
            if row and all(re.fullmatch(r":?-+:?", cell or " ") for cell in row):
                continue
            if claim_column is not None and len(row) > claim_column:
                claim = row[claim_column]
                if BOARDING.search(claim) and not ATTRIBUTION.search(claim):
                    add(number, "claim-attribution",
                        "The boarding claim needs the deckhand's memory attribution "
                        "inside the Claim cell; neighbouring columns cannot supply it.")
            if goals_column is not None and len(row) > goals_column:
                goals = row[goals_column]
                if "?" in goals:
                    add(number, "question-as-belief",
                        "Check whether a recorded or spoken question was placed under "
                        "explicit goals/beliefs; attribution of a question does not "
                        "establish the corresponding belief or goal.")
                if goals and goals not in {"—", "-"} and not NONE_ESTABLISHED.fullmatch(goals):
                    add(number, "goals-beliefs-scope",
                        "MSA-001 has no independently established character goals/beliefs; "
                        "check whether a statement, third-party claim, question or "
                        "uncertainty was used merely to populate this typed field.")
            for cell in row:
                check_scope(cell, number, any(heading_locations.values()))
            continue
        claim_column = None
        goals_column = None
        if not value:
            flush()
            continue
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s", raw):
            flush()
        if paragraph_start is None:
            paragraph_start = number
        paragraph.append(raw)
    flush()
    return findings


def report(text):
    return {
        "status": "REVIEW_REQUIRED",
        "semantic_pass": False,
        "scope": "Known-regression triage only; manually evaluate unchanged criteria 2-6.",
        "findings": scan(text),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="Complete saved LibreChat response, UTF-8 Markdown")
    args = parser.parse_args()
    text = args.capture.read_text(encoding="utf-8-sig")
    if not text.strip():
        parser.error("capture is empty")
    result = report(text)
    print(json.dumps(result, indent=2))
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
