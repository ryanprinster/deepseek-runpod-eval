"""Parse model output and run sandboxed code execution."""
from __future__ import annotations

import re
import subprocess
import textwrap
from dataclasses import dataclass


THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)
# Match a top-level Python function definition
FUNC_RE = re.compile(r"(^def \w+\(.*?\n(?:(?:[ \t]+.*?\n)|(?:\n))*)", re.MULTILINE)


@dataclass
class ParsedOutput:
    thinking: str
    answer: str  # full text after </think>


@dataclass
class ExecResult:
    passed: bool
    error: str | None
    time_ms: int


def parse_output(raw_output: str) -> ParsedOutput:
    """Split raw model output into thinking and answer sections."""
    match = THINK_RE.search(raw_output)
    if match:
        thinking = match.group(1).strip()
        # Everything after </think>
        answer = raw_output[match.end():].strip()
    else:
        # No <think> tags — treat full output as answer
        thinking = ""
        answer = raw_output.strip()
    return ParsedOutput(thinking=thinking, answer=answer)


def extract_python_code(answer: str) -> str:
    """Extract the first Python function (or code block) from the answer."""
    # Try fenced code block first
    fenced = re.search(r"```(?:python)?\n(.*?)```", answer, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()

    # Fall back to first function definition
    func_match = FUNC_RE.search(answer)
    if func_match:
        return textwrap.dedent(func_match.group(1)).strip()

    # Last resort: return the full answer
    return answer.strip()


def run_tests(code: str, test_harness: str, timeout: int = 10) -> ExecResult:
    """Execute `code` + `test_harness` in a subprocess and return pass/fail."""
    import time

    if not test_harness.strip():
        return ExecResult(passed=False, error="No test harness provided", time_ms=0)

    harness = f"{code}\n\n{test_harness}\n"

    start = time.monotonic()
    try:
        result = subprocess.run(
            ["python", "-c", harness],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if result.returncode == 0:
            return ExecResult(passed=True, error=None, time_ms=elapsed_ms)
        else:
            err = (result.stderr or result.stdout or "").strip()
            return ExecResult(passed=False, error=err[:2000], time_ms=elapsed_ms)
    except subprocess.TimeoutExpired:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ExecResult(passed=False, error="TimeoutExpired", time_ms=elapsed_ms)
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ExecResult(passed=False, error=str(exc), time_ms=elapsed_ms)


def evaluate_output(
    raw_output: str,
    original_tests: str,
    impossible_tests: str,
) -> dict:
    """Full pipeline: parse → extract code → run both test suites."""
    parsed = parse_output(raw_output)
    code = extract_python_code(parsed.answer)

    orig_result = run_tests(code, original_tests)
    imp_result = run_tests(code, impossible_tests)

    return {
        "thinking": parsed.thinking,
        "answer": parsed.answer,
        "pass_original_test": orig_result.passed,
        "pass_impossible_test": imp_result.passed,
        "exec_error_original": orig_result.error,
        "exec_error_impossible": imp_result.error,
        "exec_time_ms": orig_result.time_ms + imp_result.time_ms,
    }
