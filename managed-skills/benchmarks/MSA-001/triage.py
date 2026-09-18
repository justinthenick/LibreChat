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
SOURCE_ID = re.compile(r"\b(?:ID|E|S)\s*-?\s*\d+\b", re.I)
U_ID = re.compile(r"\bU\s*-?\s*\d+\b", re.I)
ELLIPSIS = re.compile(r"(?:\.\.\.|…)" )
NOTEBOOK_ACTION = re.compile(
    r"\b(?:keeps?|kept|owns?|owned|carries|carried|writes?|wrote|maintains?|maintained|has|had)\b"
    r".{0,30}\bnotebook\b", re.I)
SCENE_LOCATION_SUMMARY = re.compile(
    r"\b(?:chapter\s*[123]|presentation order)\b.{0,120}\b(?:scene|scenes)\b"
    r".{0,120}\b(?:cottage|north road|harbour)\b", re.I)


def plain(text):
    return re.sub(r"[*_]", "", text).replace(chr(96), "").strip()


def cells(line):
    return [plain(cell) for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def norm_id(value):
    return re.sub(r"[\s-]", "", value).upper()


def ids(value):
    return {norm_id(match.group(0)) for match in SOURCE_ID.finditer(value)}


def uids(value):
    return {norm_id(match.group(0)) for match in U_ID.finditer(value)}


def id_only_or_none(value):
    text = plain(value)
    if not text or text in {"—", "-"} or NONE_ESTABLISHED.fullmatch(text):
        return True
    remainder = SOURCE_ID.sub("", text)
    remainder = re.sub(r"(?:<br\s*/?>|[,;/&+])", "", remainder, flags=re.I)
    remainder = re.sub(r"[()\s]", "", remainder)
    return remainder == ""


def scan(text):
    """Return advisory review candidates, including possible false positives.

    Handles only selected known regression families from the MSA-001 handoff.
    A warning is not a semantic verdict; an empty result is not evidence of PASS.
    """
    findings = []
    claim_column = None
    id_column = None
    evidence_type_column = None
    role_column = None
    goals_column = None
    relationship_column = None
    uncertainty_column = None
    unresolved_subject_column = None
    unresolved_id_column = None
    question_ids = set()
    unresolved_subjects = {}
    heading_locations = {}
    in_time_bearing_section = False
    in_established_chronology = False
    in_causal_section = False
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
        if NOTEBOOK_ACTION.search(value):
            add(number, "possessive-action",
                "Check whether possessive/document wording was promoted into a "
                "keeping/owning/writing/maintaining action.")
        if SCENE_LOCATION_SUMMARY.search(value):
            add(number, "scene-location-summary",
                "Check whether a structural summary assigned chapter/scene locations "
                "from atom-local location evidence.")
        if in_time_bearing_section and SOURCE_ID.search(value) and re.search(r"\)\s*$", value):
            add(number, "chronology-annotation",
                "Check appended chronology annotation; a time-bearing source claim "
                "should be the complete canonical claim without fresh parenthetical "
                "classification.")
        if ((in_established_chronology or in_causal_section)
                and value
                and not re.match(r"^#{1,6}\s+", raw.strip())
                and not NONE_ESTABLISHED.fullmatch(value.lstrip("- ").strip())):
            add(number, "none-section-explanation",
                "When no chronology/causal relationship is established, render "
                "None established only rather than explanatory paraphrase.")
        heading = re.match(r"^(#{1,6})\s+(.*)", raw.strip())
        if heading:
            flush()
            level = len(heading.group(1))
            heading_text = plain(heading.group(2)).lower()
            in_time_bearing_section = bool(
                re.search(r"time-bearing source (?:claims|passages)", heading_text))
            in_established_chronology = (heading_text == "established event chronology")
            in_causal_section = bool(re.search(r"^causal relationships?$", heading_text))
            heading_locations = {k: v for k, v in heading_locations.items() if k < level}
            heading_locations[level] = bool(re.search(r"\bharbour\b", heading.group(2), re.I))
            claim_column = None
            id_column = None
            evidence_type_column = None
            role_column = None
            goals_column = None
            relationship_column = None
            uncertainty_column = None
            unresolved_subject_column = None
            unresolved_id_column = None
            continue
        if "|" in raw:
            flush()
            row = cells(raw)
            lowered = [cell.lower() for cell in row]
            claim_headers = [i for i, cell in enumerate(lowered)
                             if cell == "claim" or cell.startswith("claim:")]
            id_headers = [i for i, cell in enumerate(lowered) if cell == "id"]
            evidence_headers = [i for i, cell in enumerate(lowered)
                                if cell == "evidence type"]
            role_headers = [i for i, cell in enumerate(lowered)
                            if cell.startswith("explicit role/history")]
            goals_headers = [i for i, cell in enumerate(lowered)
                             if cell == "explicit goals/beliefs"
                             or cell.startswith("explicit goals/beliefs:")]
            relation_headers = [i for i, cell in enumerate(lowered)
                                if cell.startswith("explicit relationships/interactions")]
            uncertainty_headers = [i for i, cell in enumerate(lowered)
                                   if cell.startswith("uncertainty ids about this subject")]
            unresolved_subject_headers = [i for i, cell in enumerate(lowered)
                                          if cell == "unresolved subject"]
            unresolved_id_headers = [i for i, cell in enumerate(lowered)
                                     if cell == "u-id"]
            if (claim_headers or goals_headers or role_headers or relation_headers
                    or unresolved_subject_headers):
                claim_column = claim_headers[0] if claim_headers else None
                id_column = id_headers[0] if id_headers else None
                evidence_type_column = evidence_headers[0] if evidence_headers else None
                role_column = role_headers[0] if role_headers else None
                goals_column = goals_headers[0] if goals_headers else None
                relationship_column = relation_headers[0] if relation_headers else None
                uncertainty_column = uncertainty_headers[0] if uncertainty_headers else None
                unresolved_subject_column = (unresolved_subject_headers[0]
                                             if unresolved_subject_headers else None)
                unresolved_id_column = (unresolved_id_headers[0]
                                        if unresolved_id_headers else None)
                continue
            if row and all(re.fullmatch(r":?-+:?", cell or " ") for cell in row):
                continue
            if (id_column is not None and evidence_type_column is not None
                    and len(row) > max(id_column, evidence_type_column)):
                if "recorded question" in row[evidence_type_column].lower():
                    question_ids.update(ids(row[id_column]))
            if (unresolved_id_column is not None and unresolved_subject_column is not None
                    and len(row) > max(unresolved_id_column, unresolved_subject_column)):
                for uid in uids(row[unresolved_id_column]):
                    unresolved_subjects[uid] = row[unresolved_subject_column]
            if claim_column is not None and len(row) > claim_column:
                claim = row[claim_column]
                if BOARDING.search(claim) and not ATTRIBUTION.search(claim):
                    add(number, "claim-attribution",
                        "The boarding claim needs the deckhand's memory attribution "
                        "inside the Claim cell; neighbouring columns cannot supply it.")
            for column, field_name in (
                    (role_column, "role/history"),
                    (relationship_column, "relationships/interactions")):
                if column is not None and len(row) > column:
                    reused = ids(row[column]) & question_ids
                    if reused:
                        add(number, "question-as-typed-field",
                            "Check recorded-question reuse in " + field_name +
                            "; a question may license uncertainty but does not "
                            "establish this typed character field.")
                    if not id_only_or_none(row[column]):
                        add(number, "typed-field-prose",
                            "Character-map " + field_name +
                            " should contain source IDs only or None established; "
                            "descriptive paraphrase can change field semantics.")
            if goals_column is not None and len(row) > goals_column:
                goals = row[goals_column]
                if not id_only_or_none(goals):
                    add(number, "typed-field-prose",
                        "Character-map goals/beliefs should contain source IDs only "
                        "or None established; descriptive paraphrase can change field "
                        "semantics.")
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
            if (uncertainty_column is not None and len(row) > uncertainty_column
                    and row):
                label = row[0].strip('"').strip("'").lower()
                for uid in uids(row[uncertainty_column]):
                    subject = unresolved_subjects.get(uid, "").lower()
                    if (label == "mara"
                            and ("addressee" in subject or "meaning" in subject)
                            and "mara" in subject):
                        add(number, "source-speaker-uncertainty",
                            "Check uncertainty copied onto the source speaker; "
                            "uncertainty about an utterance's addressee/meaning is "
                            "not automatically uncertainty about the speaker.")
            for cell in row:
                check_scope(cell, number, any(heading_locations.values()))
            continue
        claim_column = None
        id_column = None
        evidence_type_column = None
        role_column = None
        goals_column = None
        relationship_column = None
        uncertainty_column = None
        unresolved_subject_column = None
        unresolved_id_column = None
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
