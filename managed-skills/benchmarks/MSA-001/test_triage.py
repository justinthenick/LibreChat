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
