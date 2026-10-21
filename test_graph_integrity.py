"""Mutation tests for evidence and dependency integrity, not regulatory truth."""
import copy
import hashlib
import json
import unittest
from pathlib import Path

from validate_graph import validate

ROOT = Path(__file__).resolve().parent


class IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / "graph.json").read_text(encoding="utf-8"))

    def setUp(self):
        self.graph = copy.deepcopy(self.original)

    def node(self, ident):
        return next(n for n in self.graph["nodes"] if n["id"] == ident)

    def errors(self):
        return validate(self.graph, ROOT)["errors"]

    def test_generated_graph_integrity(self):
        self.assertEqual(self.errors(), [])

    def test_rewritten_evidence_cannot_pass_by_rehashing_itself(self):
        p = self.node("span:open-offer")["properties"]
        p["content"] = p["content"].replace("equal to", "after")
        self.assertNotEqual(p["content"], self.node("span:novation")["properties"]["content"])
        p["content_sha256"] = hashlib.sha256(p["content"].encode()).hexdigest()
        self.assertTrue(any("differs from located source" in e for e in self.errors()))

    def test_unknown_field_binding_is_rejected(self):
        p = self.node("requirement-version:R02:v1")["properties"]
        p["bindings"]["f_2_6"]["field_version_id"] = "field-version:invented"
        self.assertTrue(any("invalid binding target" in e for e in self.errors()))

    def test_nearby_example_field_cannot_become_an_unevidenced_edge(self):
        e = copy.deepcopy(next(e for e in self.graph["edges"] if e["from_id"] == "requirement-version:R02:v1" and e["type"] == "USES_FIELD"))
        e["id"] = "edge:injected"
        e["to_id"] = "field-version:2.10:eu-original"
        self.graph["edges"].append(e)
        self.assertTrue(any("dependency graph mismatch" in e for e in self.errors()))

    def test_timestamp_cannot_bind_to_boolean_field(self):
        p = self.node("requirement-version:R02:v1")["properties"]
        p["bindings"]["f_2_6"]["field_version_id"] = "field-version:2.5:eu-original"
        self.assertTrue(any("invalid binding target or type" in e for e in self.errors()))

    def test_unknown_operator_is_rejected(self):
        self.node("requirement-version:R02:v1")["properties"]["assertion"]["op"] = "execute_python"
        self.assertTrue(any("unsupported operator" in e for e in self.errors()))

    def test_unreviewed_applicability_cannot_become_approved(self):
        self.node("assessment:R02:uk:v1")["properties"]["conclusion"] = "applicable"
        self.assertTrue(any("no reviewed applicability" in e for e in self.errors()))

    def test_unresolved_exception_cannot_be_replaced_with_false(self):
        self.node("requirement-version:R08:v1")["properties"]["unless"] = {"literal": {"type": "boolean", "value": False}}
        self.assertTrue(any("cannot be silently approved" in e for e in self.errors()))

    def test_missing_source_endpoint_is_rejected(self):
        e = next(e for e in self.graph["edges"] if e["type"] == "CITES")
        e["to_id"] = "span:missing"
        self.assertTrue(any("dangling endpoint" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
