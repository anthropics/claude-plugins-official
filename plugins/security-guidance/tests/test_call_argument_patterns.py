"""yaml.load, torch.load and np.load rules read the whole argument list of the call."""
import time

import pytest

import security_reminder_hook as hook

YAML, TORCH, NUMPY = "unsafe_yaml_load", "torch_unsafe_load", "pickle_wrapper_load"


def fires(rule, code):
    return rule in {name for name, _ in hook.check_patterns("t.py", code)}


@pytest.mark.parametrize("rule, code", [
    (YAML, "yaml.load(open(path), Loader=yaml.SafeLoader)"),
    (YAML, "yaml.load(m.group(1), SafeLoader)"),
    (YAML, "yaml.load(f, Loader=yaml.CSafeLoader)"),
    (YAML, "yaml.load(f.read(), Loader=CSafeLoader)"),
    (YAML, "yaml.load(\n    open(p),\n    Loader=yaml.SafeLoader,\n)"),
    (YAML, "yaml.load(s.replace(')', ''), Loader=yaml.SafeLoader)"),
    (YAML, "yaml.load(s.replace('\\'', ''), Loader=yaml.SafeLoader)"),
    (TORCH, 'torch.load(os.path.join(d, "m.pt"), weights_only=True)'),
    (TORCH, 'torch.load(str(os.path.join(root(), "m.pt")), weights_only=True)'),
    (TORCH, "torch.load(\n    path,\n    map_location=torch.device('cpu'),\n    weights_only=True,\n)"),
    (TORCH, "torch.load(\r\n    path(),\r\n    weights_only=True,\r\n)"),
    (TORCH, "torch.load(\n    path,\n    # the model's device (cpu\n    weights_only=True)"),
    (NUMPY, "np.load(os.path.join(d, 'x.npy'))"),
])
def test_safe_call_is_quiet(rule, code):
    assert not fires(rule, code)


@pytest.mark.parametrize("rule, code", [
    (YAML, "yaml.load(f)"),
    (YAML, "yaml.load(open(p), Loader=yaml.Loader)"),
    (YAML, "yaml.load(open(p), Loader=yaml.UnsafeLoader)"),
    (YAML, "yaml.load(\n    open(p),\n    Loader=yaml.Loader,\n)"),
    (TORCH, "torch.load(os.path.join(d, 'm.pt'))"),
    (TORCH, "torch.load(os.path.join(d, 'm.pt'), weights_only=False)"),
    (TORCH, "torch.load(\n    path,\n    weights_only=False,\n)"),
    (NUMPY, "np.load(path, allow_pickle=True)"),
    (NUMPY, "np.load(os.path.join(d, 'x.npy'), allow_pickle=True)"),
    (NUMPY, "np.load(\n    path(),\n    allow_pickle=True,\n)"),
])
def test_unsafe_call_fires(rule, code):
    assert fires(rule, code)


@pytest.mark.parametrize("rule, code", [
    # Another call or a comment after the closing bracket.
    (YAML, "yaml.load(f)  # TODO use SafeLoader"),
    (YAML, "yaml.load(open(p))  # TODO use SafeLoader"),
    (YAML, "yaml.load(f), yaml.load(g, Loader=yaml.SafeLoader)"),
    (YAML, "yaml.load(f())\nyaml.load(g, Loader=yaml.SafeLoader)"),
    (YAML, "yaml.load(s.replace('(', '')) or SafeThing()"),
    (TORCH, "torch.load(p()) if old else torch.load(p, weights_only=True)"),
    # A comment or string inside the argument list.
    (TORCH, "torch.load(\n    path,  # weights_only=True breaks this\n)"),
    (TORCH, "torch.load(\n    path('weights_only=True'),\n    'weights_only=True'\n)"),
    # An argument of a nested call.
    (TORCH, "torch.load(\n    fetch(url, weights_only=True),\n)"),
])
def test_safe_keyword_elsewhere_does_not_hide_an_unsafe_call(rule, code):
    assert fires(rule, code)


@pytest.mark.parametrize("code", [
    "np.load(p()); other(q, allow_pickle=True)",
    "np.load(p())  # allow_pickle=True is not needed",
    "np.load(\n    path,  # allow_pickle=True is not needed\n)",
    "np.load(\n    fetch(q, allow_pickle=True),\n)",
])
def test_allow_pickle_elsewhere_does_not_fire(code):
    assert not fires(NUMPY, code)


# Text today's rules already accept stays accepted.
@pytest.mark.parametrize("rule, code", [
    (YAML, "yaml.load(s, get_loader(yaml.SafeLoader))"),
    (TORCH, "torch.load(p, **dict(weights_only=True))"),
])
def test_previously_quiet_stays_quiet(rule, code):
    assert not fires(rule, code)


@pytest.mark.parametrize("head", ["yaml.load(", "torch.load(", "np.load("])
@pytest.mark.parametrize("body", [
    "(", "()", "(a", "((a))x", "\"'", '("', "\n", "#", "# a\n", "(((a)(b))", "\\'", "'\\",
    "{head}", "{head}a()", "{head}((", "{head}(((a", "{head}'", "{head}#",
])
def test_large_file_is_matched_quickly(head, body):
    body = body.replace("{head}", head)
    text = head + body * (60000 // len(body))
    start = time.perf_counter()
    hook.check_patterns("t.py", text)
    # Seconds only when matching is far worse than linear; normally tens of ms.
    assert time.perf_counter() - start < 5


@pytest.mark.parametrize("text", [
    "yaml.load(\n  SafeConfigPath.read_text(),\n)",
    "yaml.load(\n  cfg[SafeKey],\n  Loader=yaml.Loader,\n)",
])
def test_a_word_starting_with_safe_is_not_a_safe_loader(text):
    assert fires("unsafe_yaml_load", text)
