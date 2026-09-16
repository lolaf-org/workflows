#!/usr/bin/env python3
"""Check that each repository's .github/dependabot.yml contains templates/dependabot-common.yml.

"Contains" is structural, so comments and ordering never matter:
- a mapping contains another when it has each of its keys, with a value that contains the template's;
- a list contains another when each template item is contained by some item of the list, except that
  `updates` entries are paired by (package-ecosystem, directory) so that a mismatch names the block;
- anything else must be equal.

Anything a repository adds beyond the template - a benchmark group, a held dependency - is its own.

    dependabot-drift.py owner/repo [owner/repo ...]   check those repositories' default branches
    dependabot-drift.py --file path [--file path ...] check local files
    dependabot-drift.py --self-test                   check the template against itself and a mutation
"""

import copy
import pathlib
import sys
import urllib.request

import yaml

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "templates" / "dependabot-common.yml"


def update_key(update):
    return update.get("package-ecosystem"), update.get("directory")


def missing(template, actual, path):
    """Yield a description of every part of `template` that `actual` does not contain."""
    if isinstance(template, dict):
        if not isinstance(actual, dict):
            yield f"{path}: expected a mapping, found {actual!r}"
            return
        for key, value in template.items():
            if key not in actual:
                yield f"{path}.{key}: missing"
            else:
                yield from missing(value, actual[key], f"{path}.{key}")
    elif isinstance(template, list):
        if not isinstance(actual, list):
            yield f"{path}: expected a list, found {actual!r}"
            return
        if path == "$.updates":
            by_key = {update_key(u): u for u in actual if isinstance(u, dict)}
            for update in template:
                key = update_key(update)
                label = f"{path}[{key[0]} {key[1]}]"
                if key not in by_key:
                    yield f"{label}: missing"
                else:
                    yield from missing(update, by_key[key], label)
            return
        for item in template:
            if not any(not list(missing(item, candidate, path)) for candidate in actual):
                yield f"{path}: no item contains {item!r}"
    elif template != actual:
        yield f"{path}: expected {template!r}, found {actual!r}"


def check(name, text, template):
    problems = list(missing(template, yaml.safe_load(text), "$"))
    for problem in problems:
        print(f"::error title={name}::{problem}")
    print(f"{name}: {'drifted' if problems else 'contains the template'}")
    return not problems


def fetch(repo):
    url = f"https://raw.githubusercontent.com/{repo}/HEAD/.github/dependabot.yml"
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def self_test(template):
    assert not list(missing(template, template, "$")), "the template must contain itself"
    extended = copy.deepcopy(template)
    extended["updates"][1]["groups"]["extra"] = {"patterns": ["org.example:*"]}
    extended["updates"][1]["groups"]["maven-plugins"]["patterns"].append("org.example:plugin")
    assert not list(missing(template, extended, "$")), "additions must be allowed"
    changed = copy.deepcopy(template)
    changed["updates"][0]["schedule"]["interval"] = "daily"
    del changed["updates"][1]["groups"]["test-libraries"]["patterns"][0]
    found = list(missing(template, changed, "$"))
    assert len(found) == 2, f"a change and a removal must both be reported, got {found}"
    print("self-test passed")
    return True


def main(args):
    template = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    if args == ["--self-test"]:
        return self_test(template)
    if not args:
        print(__doc__)
        return False
    results = []
    if args[0] == "--file":
        paths = args[1::2]
        results = [check(p, pathlib.Path(p).read_text(encoding="utf-8"), template) for p in paths]
    else:
        results = [check(repo, fetch(repo), template) for repo in args]
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
