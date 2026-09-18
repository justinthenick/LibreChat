"""Regression tests for triage behavior, not evidence of model quality."""
import hashlib
from pathlib import Path
import unittest

from triage import report, scan

ROOT = Path(__file__).resolve().parents[2]


class TriageTests(unittest.TestCase):
    def codes(self, text):
        return {finding["code"] for finding in scan(text)}

    def test_unattributed_claim_is_not_repaired_by_other_columns(self):
        text = """| Claim | Strength | Evidence | Source-licensed unresolved point |
| --- | --- | --- | --- |
| A passenger in a dark coat boarded the 6:40 ferry | Character recollection | A deckhand remembers this | Passenger identity |"""
        self.assertIn("claim-attribution", self.codes(text))

    def test_attributed_claim(self):
        text = """| Claim | Strength | Evidence | Source-licensed unresolved point |
| --- | --- | --- | --- |
| A deckhand remembers a passenger in a dark coat boarding the 6:40 ferry | Character recollection | Chapter 3 | Passenger identity |"""
        self.assertNotIn("claim-attribution", self.codes(text))

    def test_verbatim_claim_header(self):
        text = "| ID | Claim: verbatim source passage | Evidence type |\n| --- | --- | --- |\n| A1 | A passenger boarded | Character recollection |"
        self.assertIn("claim-attribution", self.codes(text))

    def test_reordered_columns(self):
        text = "| Evidence | Claim |\n| --- | --- |\n| A deckhand remembers | A passenger boarded the ferry |"
        self.assertIn("claim-attribution", self.codes(text))

    def test_table_boundary_does_not_leak(self):
        text = "| Evidence | Claim |\n| --- | --- |\n\n| Character | Explicit role |\n| --- | --- |\n| Deckhand | Passenger boarded |"
        self.assertNotIn("claim-attribution", self.codes(text))

    def test_location_in_aggregate_sentence(self):
        self.assertIn("location-scope", self.codes(
            "At the harbour, Vale finds fabric and a deckhand remembers a passenger."))

    def test_wrapped_aggregate_sentence(self):
        self.assertIn("location-scope", self.codes(
            "At the harbour, Vale finds fabric and\n"
            "a deckhand remembers a passenger."))

    def test_separate_sentences_do_not_inherit(self):
        self.assertNotIn("location-scope", self.codes(
            "At the harbour, Vale finds fabric. A deckhand remembers a passenger."))

    def test_location_heading_scopes_until_sibling(self):
        text = "## Harbour\n- A deckhand remembers a passenger.\n## Other evidence\n- A deckhand remembers a passenger."
        self.assertEqual([f["line"] for f in scan(text) if f["code"] == "location-scope"], [2])

    def test_location_in_table_cell(self):
        self.assertIn("location-scope", self.codes(
            "| Ending | At the harbour, Vale finds fabric and a deckhand remembers a passenger |"))

    def test_unnamed_role_does_not_license_identity(self):
        self.assertIn("unlicensed-unknown", self.codes(
            "| Deckhand | **Identity of the deckhand** |"))

    def test_passenger_uncertainty_is_not_deckhand_uncertainty(self):
        self.assertNotIn("unlicensed-unknown", self.codes(
            "| Deckhand | None established |\n"
            "The deckhand says he cannot tell whether the passenger was Leon."))

    def test_question_in_goals_beliefs_is_flagged(self):
        text = """| Character/source label | Explicit role/history | Explicit goals/beliefs | Explicit relationships/interactions |
| --- | --- | --- | --- |
| Inspector Vale | None established | ID-13 ("M. knew about harbour before I mentioned it?") | None established |"""
        self.assertIn("question-as-belief", self.codes(text))

    def test_question_outside_goals_beliefs_is_not_flagged(self):
        text = """| Character/source label | Explicit role/history | Explicit goals/beliefs | Explicit relationships/interactions |
| --- | --- | --- | --- |
| Inspector Vale | None established | None established | ID-13 ("M. knew about harbour before I mentioned it?") |"""
        self.assertNotIn("question-as-belief", self.codes(text))

    def test_nonempty_goals_beliefs_is_advisory_for_fixture(self):
        text = """| Character/source label | Explicit role/history | Explicit goals/beliefs | Explicit relationships/interactions |
| --- | --- | --- | --- |
| Mara | None established | S-12 ("Mara says Leon hated boats.") | None established |"""
        self.assertIn("goals-beliefs-scope", self.codes(text))

    def test_none_established_goals_beliefs_is_clean(self):
        text = """| Character/source label | Explicit role/history | Explicit goals/beliefs | Explicit relationships/interactions |
| --- | --- | --- | --- |
| Mara | None established | None established | None established |"""
        self.assertNotIn("goals-beliefs-scope", self.codes(text))

    def test_service_name_is_not_boarding_time(self):
        self.assertIn("service-time-promotion", self.codes(
            "- S-17: passenger boarding the 6:40 ferry [boarding time]"))

    def test_service_name_without_promoted_time_is_clean(self):
        self.assertNotIn("service-time-promotion", self.codes(
            "- S-17: A deckhand remembers a passenger boarding the 6:40 ferry."))

    def test_shortened_claim_with_source_id_is_flagged(self):
        self.assertIn("shortened-claim", self.codes(
            "- S-06: ...walking toward the harbour shortly after seven."))

    def test_complete_claim_without_ellipsis_is_clean(self):
        self.assertNotIn("shortened-claim", self.codes(
            "- S-06: A neighbour, Mrs Pell, tells Vale that she saw someone walking."))

    def test_possessive_notebook_action_is_flagged(self):
        self.assertIn("possessive-action", self.codes(
            "| Inspector Vale | None established | None established | keeps a notebook (S13) |"))

    def test_source_notebook_wording_is_clean(self):
        self.assertNotIn("possessive-action", self.codes(
            'S13: "Vale’s notebook contains the line: “M. knew about harbour before I mentioned it?”"'))

    def test_scene_location_summary_is_flagged(self):
        self.assertIn("scene-location-summary", self.codes(
            "- Presentation order follows scenes at the cottage (Chapter 1), north road (Chapter 2), harbour (Chapter 3)."))

    def test_plain_presentation_order_is_clean(self):
        self.assertNotIn("scene-location-summary", self.codes(
            "- Chapter 1: presentation order S01-S07."))

    def test_recorded_question_id_in_role_history_is_flagged(self):
        text = """| ID | Claim: verbatim source passage | Evidence type |
| --- | --- | --- |
| ID 13 | "Vale's notebook contains: M. knew about harbour before I mentioned it?" | Recorded question |

| Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs | Uncertainty IDs about this subject |
| --- | --- | --- | --- | --- |
| "M." | ID 13 | None established | None established | U-3 |"""
        self.assertIn("question-as-typed-field", self.codes(text))

    def test_recorded_question_id_in_relationship_is_flagged(self):
        text = """| ID | Claim: verbatim source passage | Evidence type |
| --- | --- | --- |
| ID-13 | "M. knew about harbour before I mentioned it?" | Recorded question |

| Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs | Uncertainty IDs about this subject |
| --- | --- | --- | --- | --- |
| "M." | None established | None established | ID-13 | U-3 |"""
        self.assertIn("question-as-typed-field", self.codes(text))

    def test_recorded_question_with_only_uid_is_clean(self):
        text = """| ID | Claim: verbatim source passage | Evidence type |
| --- | --- | --- |
| ID 13 | "M. knew about harbour before I mentioned it?" | Recorded question |

| Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs | Uncertainty IDs about this subject |
| --- | --- | --- | --- | --- |
| "M." | None established | None established | None established | U-3 |"""
        self.assertNotIn("question-as-typed-field", self.codes(text))

    def test_speaker_does_not_inherit_addressee_meaning_uncertainty(self):
        text = """| U-ID | Unresolved subject | Neutral unresolved point |
| --- | --- | --- |
| U-6 | Addressee and meaning of Mara's whisper | Unknown |

| Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs | Uncertainty IDs about this subject |
| --- | --- | --- | --- | --- |
| Mara | ID 3 | None established | ID 5 | U-6 |"""
        self.assertIn("source-speaker-uncertainty", self.codes(text))

    def test_speaker_without_other_subject_uncertainty_is_clean(self):
        text = """| U-ID | Unresolved subject | Neutral unresolved point |
| --- | --- | --- |
| U-6 | Addressee and meaning of Mara's whisper | Unknown |

| Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs | Uncertainty IDs about this subject |
| --- | --- | --- | --- | --- |
| Mara | ID 3 | None established | ID 5 | None established |"""
        self.assertNotIn("source-speaker-uncertainty", self.codes(text))

    def test_typed_role_history_prose_is_flagged(self):
        text = """| Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs |
| --- | --- | --- | --- |
| Leon | Brother of Mara (E-03); possessive association with car (E-08) | None established | E-03 |"""
        self.assertIn("typed-field-prose", self.codes(text))

    def test_typed_fields_ids_only_are_clean(self):
        text = """| Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs |
| --- | --- | --- | --- |
| Leon | E-03 | None established | E-03 |"""
        self.assertNotIn("typed-field-prose", self.codes(text))

    def test_deckhand_goal_paraphrase_is_flagged(self):
        text = """| Character/source label | Explicit role/history: source IDs | Explicit goals/beliefs: source IDs | Explicit relationships/interactions: source IDs |
| --- | --- | --- | --- |
| A deckhand | E-17 | Remembers a passenger in a dark coat (E-17) | None established |"""
        codes = self.codes(text)
        self.assertIn("typed-field-prose", codes)
        self.assertIn("goals-beliefs-scope", codes)

    def test_time_bearing_parenthetical_annotation_is_flagged(self):
        text = """## Time-bearing source claims
- E-01: "At 7:10 p.m., Mara finds the back door open." (Narrated timestamp: 7:10 p.m.)"""
        self.assertIn("chronology-annotation", self.codes(text))

    def test_time_bearing_canonical_claim_without_annotation_is_clean(self):
        text = """## Time-bearing source claims
- E-01: "At 7:10 p.m., Mara finds the back door open.""""
        self.assertNotIn("chronology-annotation", self.codes(text))

    def test_explained_none_chronology_is_flagged(self):
        text = """## Established event chronology
None established. The manuscript has several timestamps."""
        self.assertIn("none-section-explanation", self.codes(text))

    def test_bare_none_chronology_is_clean(self):
        text = """## Established event chronology
None established"""
        self.assertNotIn("none-section-explanation", self.codes(text))

    def test_negated_example_remains_advisory(self):
        result = report("Do not invent identity of the deckhand.")
        self.assertTrue(result["findings"])
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertFalse(result["semantic_pass"])

    def test_clean_capture_never_becomes_pass(self):
        result = report("A deckhand remembers a passenger in a dark coat boarding the 6:40 ferry.")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertFalse(result["semantic_pass"])

    def test_original_fixture_is_unchanged(self):
        data = (ROOT / "benchmarks/MIG-001/fixture.md").read_bytes()
        git_blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        self.assertEqual(hashlib.sha1(git_blob).hexdigest(), "bca3ccecaad38051d8a99fa223bfe6d32d5dd4b7")


if __name__ == "__main__":
    unittest.main()
