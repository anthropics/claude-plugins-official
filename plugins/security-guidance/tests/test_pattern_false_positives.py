"""Ordinary code that the edit warnings used to fire on, next to the real uses
that still have to."""
import time

import pytest

import security_reminder_hook as hook

EVAL, FUNCTION, INNER, OUTER = (
    "eval_injection", "new_function_injection", "innerHTML_xss", "outerHTML_xss")


def fired(path, content):
    return [rule for rule, _ in hook.check_patterns(path, content)]


QUIET = [
    ("t.js", "await page.$$eval('.btn', ns => ns.length)\n"),
    ("t.js", "await page.$eval('#id', e => e.tagName)\n"),
    ("t.ts", "await page.$eval('a', (el: HTMLLinkElement) => el.href)\n"),
    ("t.ts", "await page.$eval('a', (el): string => el.href)\n"),
    ("t.js", "await page.$eval(\n  '.row',\n  async function (el) { return el.id }\n)\n"),
    ("t.js", "await frame.$$eval(`.row a`, (els, min) => els.length > min, 3)\n"),
    ("t.js", "await handle.$eval('[a=\"b\"]', async ({ href }) => href)\n"),
    ("t.js", "const r = new FunctionRegistry()\n"),
    ("t.tsx", "const c = new FunctionComponent()\n"),
    ("t.js", "return new Function_(a)\n"),
    ("t.js", "if (el.innerHTML === expected) { pass() }\n"),
    ("t.js", "if (el.innerHTML == expected) { pass() }\n"),
    ("t.js", "if (el.innerHTML=== expected) { pass() }\n"),
    ("t.js", "expect(el.outerHTML === golden).toBe(true)\n"),
]

CAUGHT = [
    (EVAL, "c.js", "const v = eval(userInput)\n"),
    (EVAL, "c.py", "v = eval(user_input)\n"),
    # AngularJS evaluates an expression string, on whatever the scope is called.
    (EVAL, "c.js", "$scope.$eval(attrs.expr)\n"),
    (EVAL, "c.js", "scope.$eval(userInput)\n"),
    (EVAL, "c.js", "this.$eval(expr)\n"),
    (EVAL, "c.js", "element.scope().$eval(expr)\n"),
    (EVAL, "c.js", "scope.$parent.$eval(expr, { $event: ev })\n"),
    (EVAL, "c.js", "scope.$eval(expr, locals)\n"),
    (EVAL, "c.js", "const $eval = eval; $eval(code)\n"),
    # A page function given as a string, or by name.
    (EVAL, "c.js", "await page.$eval('a', 'e => ' + body)\n"),
    (EVAL, "c.js", "await page.$eval('a', readHref)\n"),
    # An expression or selector that is not a constant.
    (EVAL, "c.js", "scope.$eval(expr, () => x)\n"),
    (EVAL, "c.js", "$eval(code, x => 1)\n"),
    (EVAL, "c.js", "scope.$eval('cb(' + x + ')', cb => 1)\n"),
    (EVAL, "c.js", "scope.$eval(`cb(${x})`, cb => 1)\n"),
    # An eval inside or after the page function call.
    (EVAL, "c.js", "await page.$eval('a', el => eval(el.dataset.code))\n"),
    (EVAL, "c.js", "await page.$eval(eval(sel), el => el.id)\n"),
    (EVAL, "c.js", "await page.$eval('a', el => el.id)\nscope.$eval(expr)\n"),
    (EVAL, "c.js", "await page.$eval('a', el => el.id)\neval(code)\n"),
    # The shape only excuses `$eval(`.
    (EVAL, "c.js", "eval('a', el => el.id)\n"),
    (FUNCTION, "c.js", "const f = new Function('a', body)\n"),
    (FUNCTION, "c.js", "const f = new Function ('a', body)\n"),
    (FUNCTION, "c.ts", "const f = new Function<any>(body)\n"),
    (FUNCTION, "c.js", "const f = new Function`return 1`\n"),
    (FUNCTION, "c.js", "Reflect.apply(new Function, null, [])\n"),
    (FUNCTION, "c.js", "new Function"),
    (FUNCTION, "c.js", "new FunctionConstructor(body)\n"),
    (FUNCTION, "c.js", "new FunctionRegistry(); new Function(body)\n"),
    (INNER, "c.js", "el.innerHTML = html\n"),
    (INNER, "c.js", "el.innerHTML=html\n"),
    (INNER, "c.js", "el.innerHTML =\n  html\n"),
    (INNER, "c.js", "el.innerHTML ="),
    (INNER, "c.js", "if (el.innerHTML === a) el.innerHTML = b\n"),
    (OUTER, "c.js", "el.outerHTML = html\n"),
    (OUTER, "c.js", "el.outerHTML=html\n"),
    (OUTER, "c.js", "if (el.outerHTML !== a && el.outerHTML === c) el.outerHTML = b\n"),
]


@pytest.mark.parametrize("path,content", QUIET)
def test_ordinary_code_gets_no_warning(path, content):
    assert fired(path, content) == []


@pytest.mark.parametrize("rule,path,content", CAUGHT)
def test_real_use_still_warns_once(rule, path, content):
    assert fired(path, content).count(rule) == 1


@pytest.mark.parametrize("path,unit", [
    ("t.js", "$eval("), ("t.js", "$eval('"), ("t.js", "$eval(`"), ("t.js", "$eval('a',("),
    ("t.js", "$eval('a' "), ("t.js", "$eval('a',(b): "), ("t.js", ".innerHTML "),
])
def test_repeated_openings_stay_quick(path, unit):
    start = time.monotonic()
    hook.check_patterns(path, unit * (200_000 // len(unit)))
    assert time.monotonic() - start < 5
