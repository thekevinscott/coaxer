"""RED probe for the diff-cover CI gate (issue #65, PR #67).

Intentionally untested — the next commit either reverts this file or adds a
test, demonstrating that the new diff-coverage check fires on uncovered new
lines. Do not import from outside this module.
"""


def red_probe(x: int) -> int:
    if x < 0:
        return -x
    return x * 2
