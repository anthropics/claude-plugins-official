#!/usr/bin/env python3
"""Print, per runner image, how each tested tree's suite differs from main's."""
import os
import sys
import xml.etree.ElementTree as ET


SKIP_REASONS = {}
FAILURE_TEXT = {}
# Failing tests whose whole failure text is printed for every tree.
FULL_TEXT_FOR = ("test_agentic_commit_review_runs", "test_findings_not_replaced_by_the_inner_cli_warning")
FULL_TEXT = {}
# Trees whose behaviour-check output is printed: main and the pull requests the checks were written for.
EXTRAS_FOR = {"main", "6628", "6721", "6722", "6807", "6808", "6875", "6922"}
LATER = []
FIRST = []


def read_suite(folder):
    path = os.path.join(folder, "junit.xml")
    if not os.path.exists(path):
        return None
    outcomes = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        name = "%s::%s" % (case.get("classname", ""), case.get("name", ""))
        skipped = case.find("skipped")
        failure = case.find("failure") if case.find("failure") is not None else case.find("error")
        if failure is not None:
            outcomes[name] = "failed"
            FAILURE_TEXT[(folder, name)] = (
                (failure.text or failure.get("message", ""))[-3000:]
                + "\n--- captured stderr ---\n" + (case.findtext("system-err") or "")[-1500:])
            FULL_TEXT[(folder, name)] = (failure.text or failure.get("message", ""))[-20000:]
        elif skipped is not None:
            outcomes[name] = "skipped"
            SKIP_REASONS[name] = skipped.get("message", "")
        else:
            outcomes[name] = "passed"
    return outcomes


def module_of(name):
    """tests.test_x.TestY::test_z -> test_x; a module-level skip has no class part."""
    parts = [p for p in name.replace("::", ".").split(".") if p.startswith("test_")]
    return parts[0] if parts else name


def read_text(folder, name):
    try:
        with open(os.path.join(folder, name), encoding="utf-8", errors="replace") as handle:
            return handle.read().strip()
    except OSError:
        return "?"


def main(root):
    trees = {}
    for entry in sorted(os.listdir(root)):
        if not entry.startswith("results-"):
            continue
        image, _, ref = entry[len("results-"):].rpartition("-")
        trees.setdefault(image, {})[ref] = os.path.join(root, entry)
    for entry in sorted(os.listdir(root)):
        if entry.startswith("sdk-"):
            for name in ("launcher-choice.txt", "sdk-bootstrap.txt"):
                LATER.append("\n## %s: %s\n\n```\n%s\n```" % (entry[len("sdk-"):], name, read_text(os.path.join(root, entry), name)))
    for image, refs in trees.items():
        base = read_suite(refs["main"]) if "main" in refs else None
        print("\n## %s\n" % image)
        print("| Tree | Commit | Passed | Failed | Skipped | Launch exit | Five launches | Fails here, not on main |")
        print("|---|---|---|---|---|---|---|---|")
        details, extra, skips = [], [], {}
        base_modules = {module_of(n) for n in base or {}}
        for ref in sorted(refs, key=lambda r: (r != "main", r)):
            suite = read_suite(refs[ref])
            sha = read_text(refs[ref], "sha")[:8]
            launch = read_text(refs[ref], "launch.exit")
            timing = [ln.split(": ")[1] for ln in read_text(refs[ref], "launch.txt").splitlines()
                      if ln.startswith("five launches")]
            launch = "%s | %s" % (launch, timing[0] if timing else "?")
            if suite is None:
                print("| %s | %s | no result | | | %s | |" % (ref, sha, launch))
                continue
            failed = sorted(n for n, o in suite.items() if o == "failed")
            counts = [sum(1 for o in suite.values() if o == kind) for kind in ("passed", "failed", "skipped")]
            if ref == "main" or base is None:
                added = []
                cell = "baseline" if ref == "main" else "no baseline"
            else:
                added = [n for n in failed if base.get(n) != "failed"]
                cell = str(len(added))
            print("| %s | %s | %d | %d | %d | %s | %s |" % (ref, sha, counts[0], counts[1], counts[2], launch, cell))
            for name in failed:
                if name.endswith(FULL_TEXT_FOR):
                    FIRST.append("\n## %s, %s: `%s` (whole failure text)\n\n```\n%s\n```"
                                 % (image, ref, name, FULL_TEXT.get((refs[ref], name), "")))
            if ref == "main":
                details.append(("main (baseline failures)", failed))
            elif added:
                marked = ["%s%s" % (n, "" if n in base else " (new test)") for n in added]
                details.append((ref, marked))
                seen = set()
                for name in added:
                    text = FAILURE_TEXT.get((refs[ref], name), "")
                    last = text.strip().splitlines()[-1:] or [""]
                    if last[0][:60] not in seen:
                        seen.add(last[0][:60])
                        FIRST.append("\n## %s, %s: `%s` (end of the failure text)\n\n```\n%s\n```"
                                     % (image, ref, name, text))
            if base is not None and ref != "main":
                per_file = {}
                for name, outcome in suite.items():
                    module = module_of(name)
                    if module not in base_modules:
                        per_file.setdefault(module, {"passed": 0, "failed": 0, "skipped": 0})[outcome] += 1
                for module, tally in sorted(per_file.items()):
                    extra.append("- %s adds `%s`: %d passed, %d failed, %d skipped"
                                 % (ref, module, tally["passed"], tally["failed"], tally["skipped"]))
            for name in sorted(n for n, o in suite.items() if o == "skipped"):
                skips.setdefault("%s: %s" % (name, SKIP_REASONS.get(name, "")), []).append(ref)
        for title, names in details:
            print("\n**%s**\n" % title)
            for name in names:
                print("- `%s`" % name)
        if extra:
            print("\n**Test files a tree adds over main**\n")
            print("\n".join(extra))
        if skips:
            print("\n**Skipped tests (trees)**\n")
            for text, where in sorted(skips.items()):
                print("- `%s` (%s)" % (text, ", ".join(where)))
        for ref in sorted(refs, key=lambda r: (r != "main", r)):
            if read_text(refs[ref], "launch.exit") != "0" or ref == "main":
                print("\n**%s launcher**\n\n```\n%s\n```" % (ref, read_text(refs[ref], "launch.txt")))
        for ref in sorted(refs, key=lambda r: (r != "main", r)):
            if ref in EXTRAS_FOR:
                LATER.append("\n## %s, %s: behaviour checks\n\n```\n%s\n```"
                             % (image, ref, read_text(refs[ref], "extras.txt")))
    print("\n".join(FIRST + LATER))


if __name__ == "__main__":
    main(sys.argv[1])
