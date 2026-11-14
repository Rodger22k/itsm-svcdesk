# ai-generated: 100% - OpenAI Codex implemented P-14 to P-24 from CI-SPEC.md; the student ran the official practice test
"""Turn labelled defects and scanner SARIF into a per-tool confusion matrix.

The implementation follows Laboratory 5 CI-SPEC.md rules P-14 through P-24.
It intentionally uses only the Python standard library because the grader runs it
with ``python -S -E``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import unquote


COURSE_CLASSES = {
    "secret",
    "injection",
    "deserialization",
    "weak-crypto",
    "insecure-transport",
    "path-traversal",
    "ssrf",
    "vulnerable-dependency",
    "misconfiguration",
    "access-control",
}

CWE_CLASSES = {
    "secret": {259, 260, 321, 798},
    "injection": {74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336},
    "deserialization": {502},
    "weak-crypto": {261, 326, 327, 328, 330, 331, 338, 759, 760, 916},
    "insecure-transport": {295, 297, 319, 322, 757},
    "path-traversal": {22, 23, 35, 36, 73},
    "ssrf": {918},
    "vulnerable-dependency": {937, 1035, 1104, 1395},
    "misconfiguration": {16, 215, 250, 489, 668, 732, 1188},
    "access-control": {284, 285, 639, 862, 863},
}

CWE_PATTERN = re.compile(r"(?<![A-Za-z0-9])CWE-([0-9]+)", re.IGNORECASE)
PACKAGE_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
NON_TOOL_CHARACTER = re.compile(r"[^a-z0-9]+")
PACKAGE_SEPARATOR = re.compile(r"[-_.]+")


def array_entries(value: object) -> list:
    """Return an array's entries, or no entries for every non-array value."""
    return value if isinstance(value, list) else []


def tool_id(run: dict) -> str:
    """Map a SARIF driver name to the P-15 tool id."""
    tool = run.get("tool")
    driver = tool.get("driver") if isinstance(tool, dict) else None
    name = driver.get("name") if isinstance(driver, dict) else None
    if not isinstance(name, str):
        return "unknown"

    cleaned = name.strip()
    lowered = cleaned.lower()
    if lowered in {"trivy", "grype", "osv-scanner", "gitleaks"}:
        return lowered
    if lowered in {
        "semgrep",
        "semgrep oss",
        "semgrep ce",
        "semgrep community edition",
        "semgrep pro",
    }:
        return "semgrep"

    identifier = NON_TOOL_CHARACTER.sub("-", lowered).strip("-")
    return identifier or "unknown"


def first_physical_location(result: dict) -> dict | None:
    """Return the first location's physicalLocation when it is an object."""
    locations = array_entries(result.get("locations"))
    if not locations or not isinstance(locations[0], dict):
        return None
    physical = locations[0].get("physicalLocation")
    return physical if isinstance(physical, dict) else None


def scoped_file(uri: str, set_root: str) -> str | None:
    """Normalize a URI and return its path from the last set-root component."""
    path = unquote(uri)
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]

    components = path.split("/")
    positions = [index for index, component in enumerate(components) if component == set_root]
    if not positions:
        return None
    return "/".join(components[positions[-1] :])


def result_lines(physical: dict) -> tuple[int | None, int | None]:
    """Read P-18's inclusive start and end lines."""
    region = physical.get("region")
    if not isinstance(region, dict):
        return None, None

    start = region.get("startLine")
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        return None, None

    end = region.get("endLine")
    if not isinstance(end, int) or isinstance(end, bool):
        end = start
    if end < start:
        end = start
    return start, end


def string_tags(properties: object) -> list[str]:
    """Return only string entries from properties.tags."""
    if not isinstance(properties, dict):
        return []
    return [tag for tag in array_entries(properties.get("tags")) if isinstance(tag, str)]


def matching_rule(driver: object, result: dict) -> dict | None:
    """Find the first driver rule whose id equals the present result ruleId."""
    result_rule_id = result.get("ruleId")
    if result_rule_id is None or not isinstance(driver, dict):
        return None

    for candidate in array_entries(driver.get("rules")):
        if not isinstance(candidate, dict):
            continue
        candidate_id = candidate.get("id")
        if candidate_id is not None and candidate_id == result_rule_id:
            return candidate
    return None


def result_classes(result: dict, driver: object, identifier: str) -> set[str]:
    """Classify one result using the first productive P-19 source."""
    properties = result.get("properties")
    explicit_class = properties.get("class") if isinstance(properties, dict) else None
    if isinstance(explicit_class, str) and explicit_class in COURSE_CLASSES:
        return {explicit_class}

    rule = matching_rule(driver, result)
    rule_tags = string_tags(rule.get("properties")) if isinstance(rule, dict) else []

    if identifier == "gitleaks":
        return {"secret"}
    if identifier in {"grype", "osv-scanner"}:
        return {"vulnerable-dependency"}
    if identifier == "trivy":
        trivy_classes = set()
        lowered_tags = {tag.lower() for tag in rule_tags}
        if "vulnerability" in lowered_tags:
            trivy_classes.add("vulnerable-dependency")
        if "secret" in lowered_tags:
            trivy_classes.add("secret")
        if "misconfiguration" in lowered_tags:
            trivy_classes.add("misconfiguration")
        if trivy_classes:
            return trivy_classes

    cwe_numbers = set()
    for tag in string_tags(properties) + rule_tags:
        cwe_numbers.update(int(match.group(1)) for match in CWE_PATTERN.finditer(tag))

    classes = {
        class_name
        for class_name, numbers in CWE_CLASSES.items()
        if numbers.intersection(cwe_numbers)
    }
    return classes or {"other"}


def result_is_kept(result: dict) -> bool:
    """Apply P-16's kind and suppressions filters."""
    kind = result.get("kind")
    if kind is not None and kind != "fail":
        return False

    suppressions = result.get("suppressions")
    return suppressions is None or not suppressions


def process_result(result: dict, driver: object, identifier: str, set_root: str) -> dict | None:
    """Convert one kept, in-scope SARIF result into the fields used for matching."""
    if not result_is_kept(result):
        return None

    physical = first_physical_location(result)
    if physical is None:
        return None
    artifact = physical.get("artifactLocation")
    uri = artifact.get("uri") if isinstance(artifact, dict) else None
    if not isinstance(uri, str) or not uri:
        return None

    file_name = scoped_file(uri, set_root)
    if file_name is None:
        return None

    start, end = result_lines(physical)
    message = result.get("message")
    message_text = message.get("text") if isinstance(message, dict) else None
    if not isinstance(message_text, str):
        message_text = None

    raw_rule_id = result.get("ruleId")
    fp_rule_id = raw_rule_id if isinstance(raw_rule_id, str) else None

    return {
        "file": file_name,
        "start": start,
        "end": end,
        "classes": result_classes(result, driver, identifier),
        "message": message_text,
        "rule_id": fp_rule_id,
    }


def normalize_package(value: str) -> str:
    """Apply PEP 503-style punctuation normalization used by P-20."""
    return PACKAGE_SEPARATOR.sub("-", value.lower())


def message_names_package(message: str | None, package: str) -> bool:
    """Return whether one normalized message token equals the package name."""
    if message is None:
        return False
    expected = normalize_package(package)
    for raw_token in PACKAGE_TOKEN_PATTERN.findall(message):
        token = raw_token.strip("._-")
        if token and normalize_package(token) == expected:
            return True
    return False


def matches_defect(result: dict, defect: dict) -> bool:
    """Apply P-20 to one processed result and one labelled defect."""
    defect_class = defect["class"]
    if result["file"] != defect["file"] or defect_class not in result["classes"]:
        return False

    if defect_class == "vulnerable-dependency":
        return message_names_package(result["message"], defect["package"])

    if result["start"] is None:
        return False
    return result["start"] <= defect["end_line"] and defect["start_line"] <= result["end"]


def rounded_ratio(numerator: int, denominator: int) -> float | None:
    """Return a four-decimal ratio, or null for a zero denominator."""
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def tool_matrix(defects: list[dict], results: list[dict]) -> dict:
    """Count TP, FP and FN for one merged tool, then calculate P-22 scores."""
    matched_defects: set[int] = set()
    unmatched_results: set[tuple] = set()

    for result in results:
        matches = {
            index
            for index, defect in enumerate(defects)
            if matches_defect(result, defect)
        }
        if matches:
            matched_defects.update(matches)
        else:
            unmatched_results.add(
                (result["rule_id"], result["file"], result["start"], result["end"])
            )

    tp = len(matched_defects)
    fp = len(unmatched_results)
    fn = len(defects) - tp
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": rounded_ratio(tp, tp + fp),
        "recall": rounded_ratio(tp, tp + fn),
        "f1": rounded_ratio(2 * tp, 2 * tp + fp + fn),
    }


def confusion_matrix(labels: dict, sarif_documents: list[dict]) -> dict:
    """Build the complete P-21/P-22 matrix for all runs in all documents."""
    set_root = labels["set"]
    defects = labels["defects"]
    results_by_tool: dict[str, list[dict]] = {}

    for document in sarif_documents:
        if not isinstance(document, dict):
            continue
        for run in array_entries(document.get("runs")):
            if not isinstance(run, dict):
                continue
            identifier = tool_id(run)
            results_by_tool.setdefault(identifier, [])

            tool = run.get("tool")
            driver = tool.get("driver") if isinstance(tool, dict) else None
            for raw_result in array_entries(run.get("results")):
                if not isinstance(raw_result, dict):
                    continue
                processed = process_result(raw_result, driver, identifier, set_root)
                if processed is not None:
                    results_by_tool[identifier].append(processed)

    tools = {
        identifier: tool_matrix(defects, results_by_tool[identifier])
        for identifier in sorted(results_by_tool)
    }
    return {"set": set_root, "defects": len(defects), "tools": tools}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="per-tool confusion matrix of SARIF against labels (CI-SPEC.md P-23)"
    )
    parser.add_argument("--labels", required=True, help="the labels file (P-14)")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)

    with open(args.labels, encoding="utf-8") as handle:
        labels = json.load(handle)
    documents = []
    for path in args.sarif:
        with open(path, encoding="utf-8") as handle:
            documents.append(json.load(handle))

    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
