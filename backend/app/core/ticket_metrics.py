"""
Ticket Metrics — Conformity Scoring Engine

Mathematical logic for calculating conformity KPI between task requirements
and actual code implementation. Used by the Auditor agent.
"""

import re
import difflib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ConformityVerdict(str, Enum):
    EXEMPLARY = "EXEMPLARY"
    COMPLIANT = "COMPLIANT"
    NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT"
    NON_COMPLIANT = "NON_COMPLIANT"


@dataclass
class CriterionResult:
    criterion: str
    status: str
    evidence: str
    notes: str
    score: float


@dataclass
class ConformityReport:
    task_id: str
    conformity_score: float
    verdict: ConformityVerdict
    requirement_coverage: Dict[str, Any]
    code_quality: Dict[str, Any]
    architecture: Dict[str, Any]
    traceability: Dict[str, Any]
    summary: str
    recommendations: List[str]


WEIGHTS = {
    "requirement_coverage": 0.40,
    "code_quality": 0.25,
    "architecture": 0.20,
    "traceability": 0.15,
}

VERDICT_THRESHOLDS = {
    ConformityVerdict.EXEMPLARY: 90,
    ConformityVerdict.COMPLIANT: 75,
    ConformityVerdict.NEEDS_IMPROVEMENT: 60,
}


def calculate_requirement_coverage(
    criteria: List[str],
    git_diff: str,
    changed_files: List[str],
    spec_documents: Dict[str, str]
) -> Dict[str, Any]:
    """
    Analyze each acceptance criterion against the git diff.
    Returns score (0-100) and per-criterion details.
    """
    if not criteria:
        return {"score": 100.0, "details": []}

    details = []
    fully_met = 0
    partially_met = 0

    for criterion in criteria:
        result = _evaluate_criterion(criterion, git_diff, changed_files, spec_documents)
        details.append(result)

        if result.status == "FULLY_MET":
            fully_met += 1
        elif result.status == "PARTIALLY_MET":
            partially_met += 1

    total = len(criteria)
    score = ((fully_met * 1.0) + (partially_met * 0.5)) / total * 100

    return {
        "score": round(score, 1),
        "details": [
            {
                "criterion": d.criterion,
                "status": d.status,
                "evidence": d.evidence,
                "notes": d.notes
            }
            for d in details
        ]
    }


def _evaluate_criterion(
    criterion: str,
    git_diff: str,
    changed_files: List[str],
    spec_documents: Dict[str, str]
) -> CriterionResult:
    """Evaluate a single acceptance criterion against the implementation."""
    criterion_lower = criterion.lower()
    diff_lower = git_diff.lower()

    keywords = _extract_keywords(criterion)
    matches = sum(1 for kw in keywords if kw in diff_lower)
    keyword_ratio = matches / len(keywords) if keywords else 0

    file_relevance = _check_file_relevance(criterion, changed_files, spec_documents)

    if keyword_ratio >= 0.7 and file_relevance:
        status = "FULLY_MET"
        score = 1.0
    elif keyword_ratio >= 0.3 or file_relevance:
        status = "PARTIALLY_MET"
        score = 0.5
    else:
        status = "NOT_MET"
        score = 0.0

    evidence = _find_evidence(criterion, git_diff, changed_files)
    notes = _generate_notes(criterion, status, keyword_ratio, file_relevance)

    return CriterionResult(
        criterion=criterion,
        status=status,
        evidence=evidence,
        notes=notes,
        score=score
    )


def _extract_keywords(criterion: str) -> List[str]:
    """Extract meaningful keywords from a criterion."""
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "be", "are", "was", "were", "been", "have", "has", "had", "do", "does", "did", "will", "would", "should", "could", "may", "might", "must", "can", "this", "that", "these", "those", "it", "its", "their", "our", "your", "his", "her", "my", "me", "us", "them", "he", "she", "we", "you", "i"}

    words = re.findall(r'\b\w+\b', criterion.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return keywords[:10]


def _check_file_relevance(
    criterion: str,
    changed_files: List[str],
    spec_documents: Dict[str, str]
) -> bool:
    """Check if changed files are relevant to the criterion."""
    criterion_lower = criterion.lower()
    relevant_terms = _extract_keywords(criterion_lower)

    for file_path in changed_files:
        file_lower = file_path.lower()
        for term in relevant_terms:
            if term in file_lower:
                return True

    for spec_name, spec_content in spec_documents.items():
        if any(term in spec_content.lower() for term in relevant_terms):
            for file_path in changed_files:
                if file_path in spec_content:
                    return True

    return False


def _find_evidence(criterion: str, git_diff: str, changed_files: List[str]) -> str:
    """Find specific code evidence for a criterion."""
    keywords = _extract_keywords(criterion)
    evidence_parts = []

    for file_path in changed_files[:3]:
        evidence_parts.append(f"Modified: {file_path}")

    lines = git_diff.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            context = '\n'.join(lines[max(0, i-2):i+3])
            evidence_parts.append(f"Diff excerpt:\n{context[:300]}")
            break

    return "; ".join(evidence_parts) if evidence_parts else "No direct evidence found in diff"


def _generate_notes(criterion: str, status: str, keyword_ratio: float, file_relevance: bool) -> str:
    """Generate human-readable notes for the evaluation."""
    if status == "FULLY_MET":
        return f"Strong match: {keyword_ratio:.0%} keywords found in relevant files"
    elif status == "PARTIALLY_MET":
        issues = []
        if keyword_ratio < 0.5:
            issues.append(f"only {keyword_ratio:.0%} keywords matched")
        if not file_relevance:
            issues.append("changed files don't appear relevant")
        return "Partial: " + "; ".join(issues)
    else:
        return "No matching implementation found in diff"


def calculate_code_quality(
    git_diff: str,
    changed_files: List[str],
    language: str = "python"
) -> Dict[str, Any]:
    """
    Evaluate code quality from the diff.
    Checks: error handling, validation, typing, security, tests.
    """
    findings = []
    score = 100.0

    diff_lower = git_diff.lower()

    checks = [
        ("try/except blocks", r"except\s+\w+", 5, "Missing error handling"),
        ("input validation", r"validate|check|assert|raise", 5, "No input validation detected"),
        ("type hints", r":\s*\w+\s*=" if language == "python" else r":\s*\w+", 5, "Missing type hints"),
        ("security: no hardcoded secrets", r"password\s*=\s*[\"'][^\"']+[\"']|api_key\s*=\s*[\"'][^\"']+[\"']|secret\s*=\s*[\"'][^\"']+[\"']", -10, "Potential hardcoded secret"),
        ("security: proper hashing", r"bcrypt|argon2|scrypt|pbkdf2", 5, "Weak or missing password hashing"),
        ("logging", r"log\.(info|error|warning|debug)", 3, "No logging"),
        ("docstrings/comments", r'""".*?"""|\'\'\'.*?\'\'\'|#\s+\w', 3, "Missing documentation"),
    ]

    for name, pattern, weight, message in checks:
        matches = len(re.findall(pattern, git_diff, re.IGNORECASE | re.DOTALL))
        if weight > 0:
            if matches == 0:
                findings.append(f"⚠️ {message}")
                score -= abs(weight)
            else:
                findings.append(f"✅ {name} present ({matches} occurrences)")
        else:
            if matches > 0:
                findings.append(f"❌ {message} ({matches} occurrences)")
                score += weight

    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 1),
        "findings": findings
    }


def calculate_architecture_adherence(
    git_diff: str,
    changed_files: List[str],
    project_patterns: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Evaluate adherence to project architecture patterns.
    Checks: layer separation, naming conventions, dependency direction.
    """
    findings = []
    score = 100.0

    default_patterns = {
        "service_layer": ["service", "services"],
        "repository_layer": ["repository", "repositories", "repo"],
        "routes_layer": ["routes", "controllers", "endpoints", "api"],
        "models_layer": ["models", "entities", "schemas"],
        "middleware": ["middleware", "interceptors"],
        "utils": ["utils", "helpers", "common"],
    }
    patterns = project_patterns or default_patterns

    file_layers = {}
    for file_path in changed_files:
        file_lower = file_path.lower()
        for layer, keywords in patterns.items():
            if any(kw in file_lower for kw in keywords):
                file_layers[file_path] = layer
                break
        else:
            file_layers[file_path] = "unknown"

    layer_counts = {}
    for layer in file_layers.values():
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    if len(layer_counts) > 3:
        findings.append(f"⚠️ Changes span {len(layer_counts)} layers: {', '.join(layer_counts.keys())}")
        score -= 10
    else:
        findings.append(f"✅ Changes focused on {len(layer_counts)} layer(s): {', '.join(layer_counts.keys())}")

    route_files = [f for f, l in file_layers.items() if l == "routes_layer"]
    service_files = [f for f, l in file_layers.items() if l == "service_layer"]
    model_files = [f for f, l in file_layers.items() if l == "models_layer"]

    if route_files and not service_files and not model_files:
        findings.append("⚠️ Routes modified without service/model changes — logic may be in routes")
        score -= 15
    elif route_files and service_files:
        findings.append("✅ Routes and services both modified — proper layer separation")

    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 1),
        "findings": findings,
        "layer_distribution": layer_counts
    }


def calculate_traceability(
    git_diff: str,
    commit_messages: List[str],
    task_id: str,
    branch_name: str = ""
) -> Dict[str, Any]:
    """
    Evaluate traceability: task ID in commits, branch names, PR descriptions.
    """
    findings = []
    score = 100.0

    task_id_pattern = task_id.replace("T", "T?").replace("0", "0?")

    commit_refs = sum(1 for msg in commit_messages if task_id in msg)
    if commit_refs > 0:
        findings.append(f"✅ Task ID {task_id} found in {commit_refs} commit message(s)")
    else:
        findings.append(f"⚠️ Task ID {task_id} NOT found in commit messages")
        score -= 30

    if task_id in branch_name:
        findings.append(f"✅ Task ID in branch name: {branch_name}")
    else:
        findings.append(f"ℹ️ Task ID not in branch name: {branch_name}")
        score -= 10

    pr_keywords = ["fixes", "closes", "resolves", "implements", "addresses"]
    pr_refs = sum(1 for msg in commit_messages for kw in pr_keywords if kw in msg.lower())
    if pr_refs > 0:
        findings.append(f"✅ PR linking keywords found ({pr_refs})")
    else:
        findings.append("ℹ️ No PR linking keywords in commits")
        score -= 5

    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 1),
        "findings": findings,
        "commit_references": commit_refs
    }


def calculate_conformity_score(
    requirement_coverage: Dict[str, Any],
    code_quality: Dict[str, Any],
    architecture: Dict[str, Any],
    traceability: Dict[str, Any]
) -> float:
    """Calculate weighted conformity score from all dimensions."""
    score = (
        requirement_coverage["score"] * WEIGHTS["requirement_coverage"] +
        code_quality["score"] * WEIGHTS["code_quality"] +
        architecture["score"] * WEIGHTS["architecture"] +
        traceability["score"] * WEIGHTS["traceability"]
    )
    return round(score, 1)


def determine_verdict(score: float) -> ConformityVerdict:
    """Determine verdict from numeric score."""
    for verdict, threshold in sorted(VERDICT_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
        if score >= threshold:
            return verdict
    return ConformityVerdict.NON_COMPLIANT


def generate_recommendations(
    requirement_coverage: Dict[str, Any],
    code_quality: Dict[str, Any],
    architecture: Dict[str, Any],
    traceability: Dict[str, Any]
) -> List[str]:
    """Generate actionable recommendations from all evaluations."""
    recommendations = []

    for detail in requirement_coverage.get("details", []):
        if detail["status"] in ("PARTIALLY_MET", "NOT_MET"):
            recommendations.append(
                f"Requirement: {detail['criterion']} — {detail['notes']}"
            )

    for finding in code_quality.get("findings", []):
        if finding.startswith("⚠️") or finding.startswith("❌"):
            recommendations.append(f"Code Quality: {finding[2:]}")

    for finding in architecture.get("findings", []):
        if finding.startswith("⚠️"):
            recommendations.append(f"Architecture: {finding[2:]}")

    for finding in traceability.get("findings", []):
        if finding.startswith("⚠️"):
            recommendations.append(f"Traceability: {finding[2:]}")

    return recommendations[:10]


def build_conformity_report(
    task_id: str,
    task_title: str,
    criteria: List[str],
    git_diff: str,
    changed_files: List[str],
    spec_documents: Dict[str, str],
    commit_messages: List[str] = None,
    branch_name: str = "",
    language: str = "python"
) -> ConformityReport:
    """Build complete conformity report for a task."""
    commit_messages = commit_messages or []

    req_cov = calculate_requirement_coverage(criteria, git_diff, changed_files, spec_documents)
    code_qual = calculate_code_quality(git_diff, changed_files, language)
    arch = calculate_architecture_adherence(git_diff, changed_files)
    trace = calculate_traceability(git_diff, commit_messages, task_id, branch_name)

    score = calculate_conformity_score(req_cov, code_qual, arch, trace)
    verdict = determine_verdict(score)
    recommendations = generate_recommendations(req_cov, code_qual, arch, trace)

    summary = _generate_summary(score, verdict, req_cov, code_qual, arch, trace)

    return ConformityReport(
        task_id=task_id,
        conformity_score=score,
        verdict=verdict,
        requirement_coverage=req_cov,
        code_quality=code_qual,
        architecture=arch,
        traceability=trace,
        summary=summary,
        recommendations=recommendations
    )


def _generate_summary(
    score: float,
    verdict: ConformityVerdict,
    req_cov: Dict,
    code_qual: Dict,
    arch: Dict,
    trace: Dict
) -> str:
    """Generate human-readable summary."""
    verdict_labels = {
        ConformityVerdict.EXEMPLARY: "Exemplary implementation",
        ConformityVerdict.COMPLIANT: "Compliant with minor notes",
        ConformityVerdict.NEEDS_IMPROVEMENT: "Needs improvement before approval",
        ConformityVerdict.NON_COMPLIANT: "Non-compliant — significant gaps"
    }

    parts = [
        f"**{verdict_labels[verdict]}** (Score: {score}/100)",
        f"- Requirements: {req_cov['score']}/100",
        f"- Code Quality: {code_qual['score']}/100",
        f"- Architecture: {arch['score']}/100",
        f"- Traceability: {trace['score']}/100"
    ]

    not_met = sum(1 for d in req_cov.get("details", []) if d["status"] == "NOT_MET")
    if not_met:
        parts.append(f"- ⚠️ {not_met} requirement(s) not met")

    return "\n".join(parts)


def report_to_json(report: ConformityReport) -> Dict[str, Any]:
    """Serialize ConformityReport to JSON-compatible dict."""
    return {
        "task_id": report.task_id,
        "conformity_score": report.conformity_score,
        "verdict": report.verdict.value,
        "requirement_coverage": report.requirement_coverage,
        "code_quality": report.code_quality,
        "architecture": report.architecture,
        "traceability": report.traceability,
        "summary": report.summary,
        "recommendations": report.recommendations
    }