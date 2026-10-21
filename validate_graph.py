"""Structural checks for this seed graph, not regulatory or full ontology approval."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

REQUIRED = {
    "SourceDocument": "title publisher document_kind canonical_uri",
    "SourceVersion": "version_label identity_status publication_date jurisdiction_labels language",
    "Artifact": "artifact_class representation media_type location sha256 acquired_at completeness quality_flags",
    "SourceSpan": "locator content content_sha256 span_kind quality_flags",
    "ReportingProfile": "regime jurisdiction regulator specification_label repository definition_status",
    "Field": "namespace table_id field_number display_name",
    "FieldVersion": "definition_text value_type record_family cardinality units nullability aliases definition_status",
    "DomainVersion": "value_type representation constraints completeness version_label",
    "ContextDefinition": "name description value_type scope acquisition_contract availability_status",
    "Requirement": "title requirement_family",
    "RequirementVersion": "origin normativity requirement_kind interpretation bindings evaluation_scope when unless assertion definition_state open_questions",
    "ApplicabilityAssessment": "conclusion validity_interval date_basis reasoning open_questions",
    "ExtractionRun": "task_kind model_or_tool prompt_or_config_hash started_at finished_at run_status usage",
    "Issue": "issue_kind description blocking_scope resolution_state",
}
SIGNATURES = {
    "VERSION_OF": {("SourceVersion", "SourceDocument"), ("FieldVersion", "Field"), ("RequirementVersion", "Requirement")},
    "REPRESENTS": {("Artifact", "SourceVersion")},
    "LOCATED_IN": {("SourceSpan", "Artifact")},
    "HAS_CONTEXT": {("SourceSpan", "SourceSpan")},
    "FOR_PROFILE": {("FieldVersion", "ReportingProfile"), ("ApplicabilityAssessment", "ReportingProfile")},
    "HAS_DOMAIN": {("FieldVersion", "DomainVersion")},
    "MENTIONS_FIELD": {("SourceSpan", "Field")},
    "USES_FIELD": {("RequirementVersion", "FieldVersion")},
    "USES_CONTEXT": {("RequirementVersion", "ContextDefinition")},
    "ASSESSES": {("ApplicabilityAssessment", "RequirementVersion")},
}


def validate(graph, root):
    errors = []
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = graph["edges"]
    ids = [n["id"] for n in graph["nodes"]] + [e["id"] for e in edges]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate node/edge IDs")

    def fail(message):
        errors.append(message)

    def outgoing(ident, typ):
        return [e for e in edges if e["from_id"] == ident and e["type"] == typ]

    def pointer(value, path):
        for key in path.lstrip("/").split("/"):
            key = key.replace("~1", "/").replace("~0", "~")
            value = value[int(key)] if isinstance(value, list) else value[key]
        return value

    for n in nodes.values():
        typ, p = n["type"], n["properties"]
        if typ not in REQUIRED:
            fail(f"Unsupported node type in this seed validator: {typ}")
            continue
        for key in REQUIRED[typ].split():
            if key not in p:
                fail(f"{n['id']}: missing {key}")
        if n.get("schema_version") != "0.1.0":
            fail(f"{n['id']}: unexpected schema version")
        if n.get("created_by") not in nodes or nodes[n["created_by"]]["type"] != "ExtractionRun":
            fail(f"{n['id']}: invalid producer")
        expected = {"SourceVersion": ["VERSION_OF"], "FieldVersion": ["VERSION_OF", "FOR_PROFILE", "HAS_DOMAIN"],
                    "RequirementVersion": ["VERSION_OF"], "SourceSpan": ["LOCATED_IN"],
                    "ApplicabilityAssessment": ["ASSESSES", "FOR_PROFILE"], "Artifact": ["REPRESENTS"]}.get(typ, [])
        for relation in expected:
            if len(outgoing(n["id"], relation)) != 1:
                fail(f"{n['id']}: expected one {relation}")
        if typ == "Artifact":
            path = (root / p["location"]).resolve()
            if not path.is_relative_to(root.parent.resolve()):
                fail(f"{n['id']}: artifact outside corpus")
            elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != p["sha256"]:
                fail(f"{n['id']}: artifact hash mismatch")
        if typ == "ApplicabilityAssessment" and p["conclusion"] != "unresolved":
            fail(f"{n['id']}: seed has no reviewed applicability approval")

    for e in edges:
        a, b = nodes.get(e["from_id"]), nodes.get(e["to_id"])
        if a is None or b is None:
            fail(f"{e['id']}: dangling endpoint")
            continue
        typ = e["type"]
        pair = (a["type"], b["type"])
        if typ in SIGNATURES:
            valid = pair in SIGNATURES[typ]
        elif typ == "CITES":
            valid = a["type"] in ["RequirementVersion", "FieldVersion", "DomainVersion", "ContextDefinition"] and b["type"] == "SourceSpan"
            for path in e["properties"].get("claim_paths", []):
                try:
                    pointer(a["properties"], path)
                except (KeyError, IndexError, ValueError, TypeError):
                    fail(f"{e['id']}: invalid claim path {path}")
        elif typ == "READ":
            valid = a["type"] == "ExtractionRun" and b["type"] in ["SourceSpan", "Artifact"]
        elif typ == "PRODUCED":
            valid = a["type"] == "ExtractionRun" and b["type"] in ["RequirementVersion", "FieldVersion", "DomainVersion", "ContextDefinition", "Issue", "ApplicabilityAssessment"]
        elif typ == "AFFECTS":
            valid = a["type"] == "Issue" and b["type"] == "RequirementVersion"
        else:
            valid = False
        if not valid:
            fail(f"{e['id']}: invalid {typ} endpoints {pair}")

    for n in nodes.values():
        if n["type"] != "SourceSpan":
            continue
        p = n["properties"]
        if hashlib.sha256(p["content"].encode("utf-8")).hexdigest() != p["content_sha256"]:
            fail(f"{n['id']}: span content hash mismatch")
        links = outgoing(n["id"], "LOCATED_IN")
        if len(links) != 1 or links[0]["to_id"] not in nodes:
            continue
        artifact = nodes[links[0]["to_id"]]["properties"]
        path = root / artifact["location"]
        if not path.exists():
            continue
        loc = p["locator"]
        if loc["line_namespace"] != "web_extraction":
            fail(f"{n['id']}: wrong locator namespace")
        indexed = {int(m[1]): line for line in path.read_text(encoding="utf-8").splitlines()
                   if (m := re.match(r"L(\d+)(?:@P[^:]+)?:", line))}
        try:
            expected = "\n".join(indexed[i] for i in range(loc["start"], loc["end"] + 1)) + "\n"
            if p["content"] != expected:
                fail(f"{n['id']}: evidence differs from located source text")
        except KeyError:
            fail(f"{n['id']}: unresolved evidence location")

    def infer(expr, bindings, usage, path):
        if "unresolved" in expr:
            ident = expr["unresolved"].get("issue_id")
            if ident not in nodes or nodes[ident]["type"] != "Issue":
                fail(f"{path}: unresolved slot lacks issue")
            return "boolean"
        if "ref" in expr:
            name = expr["ref"]
            if name not in bindings:
                fail(f"{path}: unbound expression reference {name}")
                return "unknown"
            usage.setdefault(name, []).append(path)
            return bindings[name]["value_type"]
        if "literal" in expr:
            lit = expr["literal"]
            if lit["type"] == "boolean" and type(lit["value"]) is not bool:
                fail(f"{path}: invalid Boolean literal")
            if lit["type"] == "code":
                domain = nodes.get(lit.get("domain_id"))
                if not domain or domain["type"] != "DomainVersion" or lit["value"] not in domain["properties"]["constraints"].get("values", []):
                    fail(f"{path}: unbound or invalid code literal")
            return lit["type"]
        operator, args = expr.get("op"), expr.get("args", [])
        types = [infer(v, bindings, usage, f"{path}/args/{i}") for i, v in enumerate(args)]
        if operator in ["and", "or"]:
            if len(args) < 2 or any(t != "boolean" for t in types):
                fail(f"{path}: invalid Boolean operator arguments")
        elif operator in ["eq", "gt"]:
            if len(types) != 2 or types[0] != types[1]:
                fail(f"{path}: incompatible comparison types")
        elif operator in ["is_present", "is_absent"]:
            if len(args) != 1:
                fail(f"{path}: invalid presence operator arity")
        else:
            fail(f"{path}: unsupported operator {operator}")
        return "boolean"

    reqs = [n for n in nodes.values() if n["type"] == "RequirementVersion"]
    for n in reqs:
        p, usage = n["properties"], {}
        for part in ["when", "unless", "assertion"]:
            if infer(p[part], p["bindings"], usage, "/" + part) != "boolean":
                fail(f"{n['id']}: {part} is not Boolean")
        expected_links = set()
        for binding, locations in usage.items():
            b = p["bindings"][binding]
            kind = "USES_FIELD" if b["kind"] == "field" else "USES_CONTEXT"
            target = b.get("field_version_id", b.get("context_definition_id"))
            if target not in nodes or nodes[target]["properties"].get("value_type") != b["value_type"]:
                fail(f"{n['id']}: invalid binding target or type: {binding}")
            roles = sorted({"condition" if path.startswith("/when") else "assertion" for path in locations})
            expected_links.add((kind, target, tuple(sorted(locations)), tuple(roles)))
        actual_links = {(e["type"], e["to_id"], tuple(sorted(e["properties"]["occurrence_paths"])), tuple(e["properties"]["roles"]))
                        for e in edges if e["from_id"] == n["id"] and e["type"] in ["USES_FIELD", "USES_CONTEXT"]}
        if expected_links != actual_links or set(p["bindings"]) != set(usage):
            fail(f"{n['id']}: expression/dependency graph mismatch")
        if not outgoing(n["id"], "CITES"):
            fail(f"{n['id']}: no evidence")
        if p["definition_state"] != "partial" or "unresolved" not in p["unless"]:
            fail(f"{n['id']}: seed scope/qualifications cannot be silently approved")
    return dict(node_count=len(nodes), edge_count=len(edges), requirement_count=len(reqs),
                release_ready_count=0, errors=errors,
                checks=["node payload presence", "endpoint types and cardinalities", "source hashes and exact spans",
                        "expression references and seed operator typing", "literal domains", "dependency edge equivalence",
                        "unresolved approvals preserved"],
                limitations=["Seed subset checker, not a complete ontology validator", "No independent regulatory review",
                             "No trade validation engine or regulatory accuracy evaluation executed"])


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    result = validate(json.loads((root / "graph.json").read_text(encoding="utf-8")), root)
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["errors"]))
