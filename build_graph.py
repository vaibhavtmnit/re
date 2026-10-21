"""Build an assistant-curated SFTR research graph; no model API or network calls."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT.parent
SCHEMA = "0.1.0"
RUN = "run:sftr-seed-v1"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def build():
    previous = ROOT / "graph.json"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # Regenerating this same research edition preserves its recording timestamp.
    if previous.exists():
        now = json.loads(previous.read_text(encoding="utf-8"))["recorded_at"]
    nodes, edges = {}, []

    def node(kind, ident, **props):
        assert ident not in nodes, ident
        nodes[ident] = dict(id=ident, type=kind, schema_version=SCHEMA,
                            recorded_at=now, created_by=RUN, properties=props)
        return ident

    def edge(kind, src, dst, **props):
        ident = "edge:" + sha(canonical([kind, src, dst, props]).encode())[:24]
        assert not any(e["id"] == ident for e in edges), ident
        edges.append(dict(id=ident, type=kind, from_id=src, to_id=dst,
                          recorded_at=now, created_by=RUN, properties=props))
        return ident

    def cite(src, span, paths, role="supports", basis="explicit_text"):
        return edge("CITES", src, span, role=role, claim_paths=paths, support_basis=basis)

    manifest = json.loads((CORPUS / "source_manifest.json").read_text(encoding="utf-8"))
    sources = {s["source_id"]: s for s in manifest["sources"]}
    source_lines = {}
    for sid in ["D04", "D05", "D06"]:
        s = sources[sid]
        raw = (CORPUS / s["local_text"]).read_bytes()
        if sha(raw) != s["sha256_text_snapshot"]:
            raise ValueError(f"Source hash changed: {sid}; review and create a new edition")
        source_lines[sid] = {int(m[1]): line for line in raw.decode("utf-8").splitlines()
                             if (m := re.match(r"L(\d+)(?:@P[^:]+)?:", line))}
        doc = node("SourceDocument", f"document:{sid}", title=s["title"],
                   publisher=s["publisher"], document_kind="guidance" if sid == "D06" else "legislation",
                   canonical_uri=s["url"])
        ver = node("SourceVersion", f"source-version:{sid}:collected-v1",
                   version_label="ESMA70-151-2838 EN, cover 2021-03-29" if sid == "D06" else "original adopted EU text",
                   identity_status="identified", publication_date="2021-03-29" if sid == "D06" else "2019-03-22",
                   jurisdiction_labels=["EU"], language="en")
        edge("VERSION_OF", ver, doc)
        artifact = node("Artifact", f"artifact:{sid}:text", artifact_class="source_material",
                        representation="extracted_text", media_type="text/plain", location="../" + s["local_text"],
                        sha256=sha(raw), acquired_at={"date": s["retrieved_on"], "time": "unknown"},
                        completeness={"numbered_lines": "complete", "visual_fidelity": "unverified"},
                        quality_flags=["flattened_tables", "line_wrapped_xml", "original_binary_not_available"])
        edge("REPRESENTS", artifact, ver)

    spans = {}

    def span(key, sid, first, last, kind="prose"):
        content = "\n".join(source_lines[sid][i] for i in range(first, last + 1)) + "\n"
        ident = node("SourceSpan", f"span:{key}",
                     locator={"kind": "text_lines", "line_namespace": "web_extraction", "start": first, "end": last},
                     content=content, content_sha256=sha(content.encode("utf-8")), span_kind=kind,
                     quality_flags=["text_only_check_visual_source_before_approval"])
        edge("LOCATED_IN", ident, f"artifact:{sid}:text")
        spans[key] = ident
        return ident

    span("open-offer", "D06", 4325, 4334)
    span("novation", "D06", 4394, 4405)
    span("client-perspective", "D06", 4463, 4467)
    span("open-offer-example", "D06", 4335, 4393, "example")
    edge("HAS_CONTEXT", spans["novation"], spans["client-perspective"], role="neighbouring passage")
    edge("HAS_CONTEXT", spans["open-offer-example"], spans["open-offer"], role="heading")

    eu = node("ReportingProfile", "profile:eu-source-research", regime="SFTR", jurisdiction="EU",
              regulator="ESMA/EU technical standards", specification_label="Original RTS/ITS plus collected guideline; research only",
              repository="unspecified", definition_status="partial")
    uk = node("ReportingProfile", "profile:uk-target-research", regime="UK SFTR", jurisdiction="UK",
              regulator="FCA", specification_label="Target technical package applicable from 2024-11-25; contents not acquired",
              repository="unspecified", definition_status="partial")

    fields = {
        "2.2": ("Report tracking number", "identifier", (272, 283), (359, 361)),
        "2.5": ("Cleared", "boolean", (294, 294), (368, 369)),
        "2.6": ("Clearing timestamp", "timestamp", (295, 295), (370, 371)),
        "2.7": ("CCP", "identifier", (296, 298), (372, 372)),
        "2.9": ("Master agreement type", "code", (307, 311), (375, 402)),
        "2.10": ("Other master agreement type", "string", (312, 316), (403, 405)),
        "2.12": ("Execution timestamp", "timestamp", (320, 320), (409, 410)),
    }
    fv = {}
    for fid, (name, typ, definition, fmt) in fields.items():
        stable = node("Field", f"field:sftr:{fid}", namespace="sftr", table_id=2,
                      field_number=int(fid.split(".")[1]), display_name=name)
        ds = span(f"definition-{fid}", "D04", *definition, kind="definition")
        fs = span(f"format-{fid}", "D05", *fmt, kind="definition")
        text = nodes[ds]["properties"]["content"]
        ver = node("FieldVersion", f"field-version:{fid}:eu-original", definition_text=text,
                   value_type=typ, record_family="transaction", cardinality={"min": "unknown", "max": 1},
                   units="not_applicable", nullability="conditional_unresolved", aliases=[name, fid],
                   definition_status="partial")
        fv[fid] = ver
        edge("VERSION_OF", ver, stable)
        edge("FOR_PROFILE", ver, eu)
        cite(ver, ds, ["/definition_text"])
        cite(ver, fs, ["/value_type"])
        edge("MENTIONS_FIELD", ds, stable, text_location=nodes[ds]["properties"]["locator"],
             match_kind="explicit", ambiguity_status="resolved")
        constraints, representation, completeness = {}, "composite", "partial"
        if typ == "boolean":
            constraints, representation, completeness = {"values": [True, False]}, "enum", "complete"
        elif typ == "timestamp":
            constraints, representation = {"timezone": "UTC", "source_format": "YYYY-MM-DDThh:mm:ssZ"}, "date/time"
        elif fid == "2.9":
            format_text = nodes[fs]["properties"]["content"]
            values = sorted(set(re.findall(r"[\u2018']([A-Z]{4})[\u2019']", format_text)))
            assert "OTHR" in values and "GMRA" in values
            constraints, representation = {"values": values, "approval": "unreviewed_original_EU_list"}, "enum"
        elif fid == "2.10":
            constraints = {"max_length": 50, "character_set": "alphanumeric_in_source; implementation_pending"}
        elif fid == "2.7":
            constraints = {"standard": "ISO 17442 LEI", "length": 20, "reference_validation": "not_implemented"}
        else:
            constraints = {"max_length": 52, "character_set": "unresolved_source_wording; not_compiled"}
        domain = node("DomainVersion", f"domain:{fid}:eu-original", value_type=typ,
                      representation=representation, constraints=constraints, completeness=completeness,
                      version_label="original ITS research definition")
        edge("HAS_DOMAIN", ver, domain)
        cite(domain, fs, ["/constraints"])

    context_info = {
        "clearing_model": ("code", "Clearing business model", ["open_offer", "novation", "dbv", "other"]),
        "reporting_role": ("code", "Role of the reporting party in this clearing relationship", ["ccp", "clearing_member", "client", "other"]),
        "prior_bilateral_uti": ("identifier", "UTI of the original bilateral transaction", None),
        "clearing_ccp_lei": ("identifier", "LEI of the CCP that cleared this transaction", None),
    }
    for name, (typ, desc, values) in context_info.items():
        ctx = node("ContextDefinition", "context:" + name, name=name, description=desc,
                   value_type=typ, scope="transaction",
                   acquisition_contract={"provider": "unresolved_upstream_business_system", "lookup_key": "unresolved",
                                         "as_of": "clearing_event", "completeness": "unresolved"},
                   availability_status="not_connected")
        cite(ctx, spans["open-offer"] if name in ["clearing_model", "clearing_ccp_lei"] else spans["novation"],
             ["/description"], basis="interpretation")
        if values:
            node("DomainVersion", "domain:context:" + name, value_type="code", representation="enum",
                 constraints={"values": values, "origin": "internal_normalization_not_regulatory_codes"},
                 completeness="partial", version_label="seed-v1")

    def issue(key, description, kind="ambiguous meaning", scope="release"):
        return node("Issue", "issue:" + key, issue_kind=kind, description=description,
                    blocking_scope=scope, resolution_state="open")

    shared_issues = [
        issue("uk-applicability", "UK workbook/schema contents and applicable amendments have not been adjudicated.", "missing reference"),
        issue("source-fidelity", "Text snapshots lack original layout; verify relevant originals before approval.", "extraction damage"),
        issue("scope", "Resolve product, action, level, reporting perspective and identity/time scope for each requirement.", "ambiguous meaning", "compilation_and_release"),
        issue("qualifications", "The local passages were read; full exception and cross-reference review is incomplete.", "missing reference", "compilation_and_release"),
        issue("context-contract", "Clearing model, roles, prior UTI and CCP lookup contracts are not connected.", "missing context", "runtime_and_release"),
        issue("field-domain", "Definition versions are original EU research bindings; nullability and current UK domains are unresolved.", "missing reference"),
    ]
    rtn_issue = issue("rtn-strength", "D04 says prior UTI is not required for CCPs; D06 says only CM/client, not CCP. Resolve whether prohibition is justified in the exact scenario before compiling R08.", "ambiguous meaning", "compilation_and_release")

    def ref(name):
        return {"ref": name}

    def literal(typ, value, domain=None):
        result = {"type": typ, "value": value}
        if domain:
            result["domain_id"] = domain
        return {"literal": result}

    def op(name, *args):
        return {"op": name, "args": list(args)}

    def context_eq(name, value):
        return op("eq", ref(name), literal("code", value, "domain:context:" + name))

    def model_guard(model, roles):
        role_expr = [context_eq("reporting_role", role) for role in roles]
        return op("and", context_eq("clearing_model", model), role_expr[0] if len(role_expr) == 1 else op("or", *role_expr))

    def present_equal(field_ref, target):
        return op("and", op("is_present", ref(field_ref)), op("eq", ref(field_ref), target))

    rules = []
    roles = ["ccp", "clearing_member", "client"]
    for prefix, model, evidence in [("open", "open_offer", "open-offer"), ("novation", "novation", "novation")]:
        comparator = "eq" if model == "open_offer" else "gt"
        rules += [
            (f"{prefix}: cleared flag", model_guard(model, roles), present_equal("f_2_5", literal("boolean", True)), evidence, "presence"),
            (f"{prefix}: timestamp relationship", model_guard(model, roles),
             op("and", op("is_present", ref("f_2_6")), op("is_present", ref("f_2_12")), op(comparator, ref("f_2_6"), ref("f_2_12"))), evidence, "comparison"),
            (f"{prefix}: CCP identity", model_guard(model, roles), present_equal("f_2_7", ref("clearing_ccp_lei")), evidence, "comparison"),
        ]
    rules += [
        ("novation: CM/client prior UTI", model_guard("novation", ["clearing_member", "client"]),
         present_equal("f_2_2", ref("prior_bilateral_uti")), "novation", "comparison"),
        ("novation: CCP tracking-number absence hypothesis", model_guard("novation", ["ccp"]),
         op("is_absent", ref("f_2_2")), "novation", "presence"),
        ("other agreement name: necessary agreement type", op("is_present", ref("f_2_10")),
         op("and", op("is_present", ref("f_2_9")), op("eq", ref("f_2_9"), literal("code", "OTHR", "domain:2.9:eu-original"))),
         "definition-2.10", "comparison"),
    ]

    def references(expr, path):
        if "ref" in expr:
            yield expr["ref"], path
        for i, child in enumerate(expr.get("args", [])):
            yield from references(child, f"{path}/args/{i}")

    for i, (title, when, assertion, evidence, kind) in enumerate(rules, 1):
        rid = f"R{i:02d}"
        req = node("Requirement", "requirement:" + rid, title=title, requirement_family="master_agreement" if i == 9 else "clearing")
        paths = {}
        for part, expr in [("when", when), ("assertion", assertion)]:
            for binding, path in references(expr, "/" + part):
                paths.setdefault(binding, []).append(path)
        bindings = {}
        for binding in paths:
            if binding.startswith("f_"):
                fid = binding[2:].replace("_", ".")
                bindings[binding] = dict(kind="field", field_version_id=fv[fid], record_alias="current", value_type=fields[fid][1])
            else:
                bindings[binding] = dict(kind="context", context_definition_id="context:" + binding,
                                         subject_alias="transaction", value_type=context_info[binding][0])
        rv = node("RequirementVersion", "requirement-version:" + rid + ":v1", origin="source_extracted",
                  normativity="unresolved" if i == 8 else "obligation", requirement_kind=kind,
                  interpretation=title, bindings=bindings,
                  evaluation_scope={"record_family": "transaction", "subject_kind": "transaction", "aliases": ["current", "transaction"],
                                    "identity_key": {"unresolved": {"reason": "Resolve reporting identity and scope", "issue_id": "issue:scope"}},
                                    "time_basis": {"unresolved": {"reason": "Resolve applicable time basis", "issue_id": "issue:scope"}}},
                  when=when,
                  unless={"unresolved": {"reason": "Complete exception and cross-reference review", "issue_id": "issue:qualifications"}},
                  assertion=assertion, definition_state="partial",
                  open_questions=["Confirm UK applicability, reporting scope and qualifications."] +
                                 (["Does not-required versus not-by justify a prohibition?"] if i == 8 else []))
        edge("VERSION_OF", rv, req)
        cite(rv, spans[evidence], ["/when", "/assertion"], basis="interpretation")
        if i <= 8:
            cite(rv, spans["client-perspective"] if i >= 4 else spans["open-offer"], ["/when"], role="context", basis="interpretation")
        if i in [7, 8]:
            cite(rv, spans["definition-2.2"], ["/assertion"], role="qualifies", basis="interpretation")
        for binding, occurrences in paths.items():
            b = bindings[binding]
            edge("USES_FIELD" if b["kind"] == "field" else "USES_CONTEXT", rv,
                 b.get("field_version_id", b.get("context_definition_id")),
                 occurrence_paths=occurrences,
                 roles=sorted({"condition" if p.startswith("/when") else "assertion" for p in occurrences}))
        assessment = node("ApplicabilityAssessment", "assessment:" + rid + ":uk:v1", conclusion="unresolved",
                          validity_interval={"from": {"kind": "unknown"}, "to": {"kind": "unknown"}},
                          date_basis="unresolved", reasoning="Original EU source interpretation; UK adoption and current technical package not adjudicated.",
                          open_questions=["Resolve the target UK specification and applicable interval."])
        edge("ASSESSES", assessment, rv)
        edge("FOR_PROFILE", assessment, uk)
        for iss in shared_issues:
            if iss == "issue:context-contract" and i == 9:
                continue
            edge("AFFECTS", iss, rv)
        if i == 8:
            edge("AFFECTS", rtn_issue, rv)

    # Preserve nearby example mentions without inventing rule dependencies.
    for fid in ["2.5", "2.6", "2.7", "2.9", "2.10", "2.12"]:
        edge("MENTIONS_FIELD", spans["open-offer-example"], "field:sftr:" + fid,
             text_location=nodes[spans["open-offer-example"]]["properties"]["locator"],
             match_kind="explicit", ambiguity_status="resolved")

    for n in list(nodes.values()):
        if n["type"] in ["SourceSpan", "Artifact"]:
            edge("READ", RUN, n["id"])
        if n["type"] in ["RequirementVersion", "FieldVersion", "DomainVersion", "ContextDefinition", "Issue", "ApplicabilityAssessment"]:
            edge("PRODUCED", RUN, n["id"])
    node("ExtractionRun", RUN, task_kind="assistant_curated_seed_graph", model_or_tool="Conversational assistant with deterministic Python serialization",
         prompt_or_config_hash=sha(Path(__file__).read_bytes()), started_at=now, finished_at=now,
         run_status="seed_export_complete", usage={"model_tokens": "unavailable", "model_api_calls_from_builder": 0},
         extensions={"seed:method": "Manually curated from source passages in the assistant session; not an automated extraction benchmark or independent review."})

    graph = dict(schema_version=SCHEMA, dataset_version="seed-v1", recorded_at=now,
                 status="research_candidates_only", nodes=list(nodes.values()), edges=edges)
    write_json(ROOT / "graph.json", graph)
    for name, records in [("nodes.jsonl", graph["nodes"]), ("edges.jsonl", edges)]:
        (ROOT / name).write_bytes(("\n".join(canonical(r) for r in records) + "\n").encode("utf-8"))

    # A replaceable research snapshot, never an append-only production review store.
    db = sqlite3.connect(ROOT / "graph.sqlite")
    db.execute("PRAGMA foreign_keys=ON")
    with db:
        db.executescript("""
            DROP TABLE IF EXISTS edges; DROP TABLE IF EXISTS nodes; DROP TABLE IF EXISTS objects;
            CREATE TABLE objects(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('node','edge')));
            CREATE TABLE nodes(id TEXT PRIMARY KEY REFERENCES objects(id), type TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE edges(id TEXT PRIMARY KEY REFERENCES objects(id), type TEXT NOT NULL,
                from_id TEXT NOT NULL REFERENCES objects(id), to_id TEXT NOT NULL REFERENCES objects(id), payload TEXT NOT NULL);
            CREATE INDEX edge_from_type ON edges(from_id,type);
            CREATE INDEX edge_to_type ON edges(to_id,type);
        """)
        db.executemany("INSERT INTO objects VALUES (?,?)", [(n["id"], "node") for n in graph["nodes"]] + [(e["id"], "edge") for e in edges])
        db.executemany("INSERT INTO nodes VALUES (?,?,?)", [(n["id"], n["type"], canonical(n)) for n in graph["nodes"]])
        db.executemany("INSERT INTO edges VALUES (?,?,?,?,?)", [(e["id"], e["type"], e["from_id"], e["to_id"], canonical(e)) for e in edges])
    db.close()
    from render_graph import render
    render(graph, ROOT)
    from validate_graph import validate
    report = validate(graph, ROOT)
    write_json(ROOT / "integrity_report.json", report)
    if report["errors"]:
        raise ValueError(report["errors"])
    outputs = ["graph.json", "nodes.jsonl", "edges.jsonl", "graph.sqlite", "graph.html", "graph.mmd", "integrity_report.json"]
    write_json(ROOT / "manifest.json", {"dataset_version": "seed-v1", "schema_version": SCHEMA, "recorded_at": now,
               "method": "assistant_curated_not_independently_reviewed", "source_ids": ["D04", "D05", "D06"],
               "field_ids": list(fields), "requirement_count": 9, "node_count": len(nodes), "edge_count": len(edges),
               "release_count": 0, "files": {p: sha((ROOT / p).read_bytes()) for p in outputs}})
    print(json.dumps({k: report[k] for k in ["node_count", "edge_count", "requirement_count", "errors", "release_ready_count"]}, indent=2))


if __name__ == "__main__":
    build()
