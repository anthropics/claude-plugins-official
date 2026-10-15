import pytest

import security_reminder_hook as hook


def fired(path, content):
    return {rule for rule, _ in hook.check_patterns(path, content)}


QUIET = [
    ("t.js", "await page.$$eval('.btn', ns => ns.length)\n"),
    ("t.js", "await page.$eval('#id', e => e.tagName)\n"),
    ("t.js", "const r = new FunctionRegistry()\n"),
    ("t.tsx", "const c = new FunctionComponent()\n"),
    ("t.js", "if (el.innerHTML === expected) { pass() }\n"),
    ("t.js", "if (el.innerHTML == expected) { pass() }\n"),
    ("t.js", "expect(el.outerHTML === golden).toBe(true)\n"),
    ("doc.md", "Never pass verify=False to requests.\n"),
    ("README.md", 'Add `<script src="https://cdn.x/l.js"></script>` to your page.\n'),
    ("t.js", "const doc = ET.parse(payload)\n"),
    ("guide.md", "```python\nsubprocess.run(cmd, shell=True)\n```\n"),
    ("notes.rst", "tree = ET.parse(path)\n"),
    ("README.MD", "Never pass verify=False to requests.\n"),
    ("guide.markdown", "Never pass verify=False to requests.\n"),
]

CAUGHT = [
    ("c.js", "const v = eval(userInput)\n", "eval_injection"),
    ("c.py", "v = eval(user_input)\n", "eval_injection"),
    ("c.js", "const f = new Function('a', body)\n", "new_function_injection"),
    ("c.js", "const f = new Function ('a', body)\n", "new_function_injection"),
    ("c.js", "const f = new\n  Function(body)\n", "new_function_injection"),
    ("c.ts", "const f = new Function<any>(body)\n", "new_function_injection"),
    ("c.js", "new Function", "new_function_injection"),
    ("c.js", "$scope.$eval(attrs.expr)\n", "eval_injection"),
    ("c.js", "scope.$eval(userInput)\n", "eval_injection"),
    ("page.mdx", '<script src="https://cdn.x/l.js"></script>\n', "script_src_without_sri"),
    ("page.mdx", "export const a = new https.Agent({ rejectUnauthorized: false })\n", "tls_verification_disabled"),
    ("c.js", "el.innerHTML = html\n", "innerHTML_xss"),
    ("c.js", "el.innerHTML=html\n", "innerHTML_xss"),
    ("c.js", "el.outerHTML = html\n", "outerHTML_xss"),
    ("c.js", "el.outerHTML=html\n", "outerHTML_xss"),
    ("c.py", "requests.get(url, verify=False)\n", "tls_verification_disabled"),
    ("c.go", "tr := &tls.Config{InsecureSkipVerify: true}\n", "tls_verification_disabled"),
    ("compose.yaml", "environment:\n  - NODE_TLS_REJECT_UNAUTHORIZED=0\n", "tls_verification_disabled"),
    ("agent.yml", "rejectUnauthorized: false\n", "tls_verification_disabled"),
    ("index.html", '<script src="https://cdn.x/l.js"></script>\n', "script_src_without_sri"),
    ("c.py", "tree = ET.parse(path)\n", "xml_unsafe_parse"),
    ("tool", "d = minidom.parseString(s)\n", "xml_unsafe_parse"),
    ("c.py", "subprocess.run(cmd, shell=True)\n", "python_subprocess_shell"),
    ("tool", "subprocess.run(cmd, shell=True)\n", "python_subprocess_shell"),
    ("ci.yml", "run: python -c 'subprocess.run(cmd, shell=True)'\n", "python_subprocess_shell"),
]


@pytest.mark.parametrize("path,content", QUIET)
def test_benign_code_gets_no_warning(path, content):
    assert fired(path, content) == set()


@pytest.mark.parametrize("path,content,rule", CAUGHT)
def test_real_use_still_warns(path, content, rule):
    assert rule in fired(path, content)
