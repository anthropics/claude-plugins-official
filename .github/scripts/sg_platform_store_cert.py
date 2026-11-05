"""A Windows certificate store entry that OpenSSL cannot read: does Python's default TLS context
still build, and do the plugin's API calls still connect and still verify?

Usage: sg_platform_store_cert.py <main plugin dir> <pull request plugin dir>

Adds test certificates, one at a time, to the current user's "CA" store (which makes nothing
trusted), runs the checks, and removes each one again. Every certificate here is a throwaway
self-signed test certificate, damaged on purpose; no private key is kept anywhere.
"""
import base64
import hashlib
import inspect
import os
import ssl
import struct
import subprocess
import sys
import tempfile

VALID = base64.b64decode(
    "MIIDHzCCAgegAwIBAgIUOc9sRb2irMM4tVz+MQXfAetMqk0wDQYJKoZIhvcNAQELBQAwHzEdMBsGA1UEAwwUc2cgdGVzdCB1bnJlbGF0ZWQgQ0EwHhcNMjYxMDIxMTYyMTEzWhcNMjYxMTIwMTYyMTEzWjAfMR0wGwYDVQQDDBRzZyB0ZXN0IHVucmVsYXRlZCBDQTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJem7dZt60IjCVS8hLJFacbGIdCwitR+EwfK3RfRbtGUeR8VDfAI2uQUF9KNCQQ0jUDLAzKxTXhje5bDW4eBs/HC86uYBPRvSmSnkh0QXc9FRGsoryI5smLtr//mFoXmyCd/xdX/mThEoamP50mH+mCrwt9UuiS8uUPD0EXMsfKSyWJLx+fPzcquOClCx+RAhGqtFhUMLZvAhRAzwodJaZ+6Rmuajii9W3YuTwUASK00IVF9m+DrvdwMSZBtOC6psyli9boD908SHI1YAR0u5hAeMUVbMC/09gNXrMeuoVghygluujCxUrPfsMtxYBE3+F6S7AbXwBDXjgTfDLP6cSMCAwEAAaNTMFEwHQYDVR0OBBYEFBzXby0JI0yF361xBLC1d/uTc8NjMB8GA1UdIwQYMBaAFBzXby0JI0yF361xBLC1d/uTc8NjMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAG/cFyLiNq1wIUceHcx04Z/frqpzCk360w6HcJ4lfWEEE1Yeyt++3dnKpkvxUT6FvAa63aIXQmaZIRZNtF6bpB937ycGovbCPMIDXj0KLwxYORqQ/kCjh6o8nCMxJ6H2UJ1Wkhvy4t4d0cYKwYxwxLo8cZ+nRn5cwYWlJBTXvVMHP5+WuYYSuatvBmpgCTdR96Setu2CMF+WohyiqXIYCrZDkNyOYS0t9hhzHK9C08eCHsHqE1KaAjUomjGjGjDehtujwBqVi9saCedXFX93MRtiZhVSBC9FHkOYdYYSdmCQi/PBpfMXaPFcfvR9gNKDaxKRRQxaQfrvv+OIVKhP+Z8=")
SUBJECT_A = base64.b64decode(
    "MIIBkjCCATmgAwIBAgIUbv89EXoDEbZBR6jKRVAU1V/0fGgwCgYIKoZIzj0EAwIwHzEdMBsGA1UEAwwUc2cgdGVzdCB1bnJlbGF0ZWQgQ0EwHhcNMjYxMDIxMTYyMjQ1WhcNMzYxMDE4MTYyMjQ1WjAfMR0EGwYDVQQDDBRzZyB0ZXN0IHVucmVsYXRlZCBDQTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABPNt0cYQuFTK2120/wnrAXDuqQUE8Cu0MpykWGDKTpymrBpKT9tB3wtr6Z951brKADRTgA7sKsIRoo9WmwnJKdyjUzBRMB0GA1UdDgQWBBQbn4fFArXUPihIY/CG7IxtVswc1DAfBgNVHSMEGDAWgBQbn4fFArXUPihIY/CG7IxtVswc1DAPBgNVHRMBAf8EBTADAQH/MAoGCCqGSM49BAMCA0cAMEQCIDuCfFRxNvoQhAXHiaA+Pgd7nuZ7hHVE16dERXHiVT6JAiACb2vks3dsL40uUAQ7MEoy37JzJExADeVOBhztTqTkkw==")
SUBJECT_B = base64.b64decode(
    "MIIBkjCCATmgAwIBAgIUbv89EXoDEbZBR6jKRVAU1V/0fGgwCgYIKoZIzj0EAwIwHzEdMBsGA1UEAwwUc2cgdGVzdCB1bnJlbGF0ZWQgQ0EwHhcNMjYxMDIxMTYyMjQ1WhcNMzYxMDE4MTYyMjQ1WjAfMB0wGwYDVQQDDBRzZyB0ZXN0IHVucmVsYXRlZCBDQTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABPNt0cYQuFTK2120/wnrAXDuqQUE8Cu0MpykWGDKTpymrBpKT9tB3wtr6Z951brKADRTgA7sKsIRoo9WmwnJKdyjUzBRMB0GA1UdDgQWBBQbn4fFArXUPihIY/CG7IxtVswc1DAfBgNVHSMEGDAWgBQbn4fFArXUPihIY/CG7IxtVswc1DAPBgNVHRMBAf8EBTADAQH/MAoGCCqGSM49BAMCA0cAMEQCIDuCfFRxNvoQhAXHiaA+Pgd7nuZ7hHVE16dERXHiVT6JAiACb2vks3dsL40uUAQ7MEoy37JzJExADeVOBhztTqTkkw==")
CN = b"sg test unrelated CA"

REPORT = []


def say(line=""):
    print(line, flush=True)
    REPORT.append(line)


def _tlv(data, at):
    length, header = data[at + 1], 2
    if length & 0x80:
        n = length & 0x7F
        length, header = int.from_bytes(data[at + 2:at + 2 + n], "big"), 2 + n
    return header, length


def _der(tag, body):
    n = len(body)
    if n < 0x80:
        return bytes([tag, n]) + body
    size = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([tag, 0x80 | len(size)]) + size + body


def candidates():
    # A subject name that is not valid UTF-8.
    name = bytearray(VALID)
    name[VALID.find(CN, VALID.find(CN) + 1) + 3] = 0xFF
    # A serial number with a leading zero byte it must not have.
    h, n = _tlv(VALID, 0)
    outer = VALID[h:h + n]
    h, n = _tlv(outer, 0)
    tbs, rest = outer[h:h + n], outer[h + n:]
    h, n = _tlv(tbs, 0)
    version, at = tbs[:h + n], h + n
    h, n = _tlv(tbs, at)
    serial, tail = tbs[at + h:at + h + n], tbs[at + h + n:]
    padded = _der(0x30, _der(0x30, version + _der(0x02, b"\x00" + serial) + tail) + rest)
    # A serial number under the wrong type.
    tag = bytearray(VALID)
    tag[13] = 0x04
    return [
        ("name not UTF-8", bytes(name)),
        ("serial with illegal padding", padded),
        ("subject name wrongly nested (1)", SUBJECT_A),
        ("subject name wrongly nested (2)", SUBJECT_B),
        ("serial under the wrong type", bytes(tag)),
    ]


def run(cmd, **kw):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                       errors="replace", timeout=300, **kw)
    return p.returncode, p.stdout.strip()


def last(text, n=1):
    return " | ".join(text.splitlines()[-n:]) if text else ""


def context_builds():
    code, out = run([sys.executable, "-c", "import ssl; ssl.create_default_context(); print('builds')"])
    return "builds" if code == 0 else "FAILS: " + last(out)


def in_store(der):
    return any(cert == der for cert, _, _ in ssl.enum_certificates("CA"))


REG_KEY = r"Software\Microsoft\SystemCertificates\CA\Certificates"


def add(der, path):
    code, out = run(["certutil", "-user", "-addstore", "CA", path])
    if in_store(der):
        return "certutil"
    say(f"  certutil: exit {code}: {last(out, 2)}")
    code, out = run(["powershell", "-NoProfile", "-Command",
                     "$s = New-Object System.Security.Cryptography.X509Certificates.X509Store('CA','CurrentUser');"
                     "$s.Open('ReadWrite');"
                     "$c = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 -ArgumentList '%s';"
                     "$s.Add($c); $s.Close()" % path])
    if in_store(der):
        return "X509Store"
    say(f"  X509Store: exit {code}: {last(out, 2)}")
    import winreg
    thumb = hashlib.sha1(der).hexdigest().upper()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY + "\\" + thumb) as key:
        winreg.SetValueEx(key, "Blob", 0, winreg.REG_BINARY, struct.pack("<III", 32, 1, len(der)) + der)
    if in_store(der):
        return "registry"
    say("  registry entry: not listed by the store")
    return None


def remove(der):
    thumb = hashlib.sha1(der).hexdigest().upper()
    run(["certutil", "-user", "-delstore", "CA", thumb])
    if in_store(der):
        run(["powershell", "-NoProfile", "-Command",
             "Remove-Item -Path 'Cert:\\CurrentUser\\CA\\%s' -ErrorAction SilentlyContinue" % thumb])
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_KEY + "\\" + thumb)
    except OSError:
        pass
    return not in_store(der)


CONNECT = r"""
import sys, urllib.request, urllib.error
import llm
op = getattr(llm, "_urlopen", None) or (lambda r, t: urllib.request.urlopen(r, timeout=t))
for url in sys.argv[1:]:
    try:
        op(urllib.request.Request(url, method="HEAD"), 20)
        print(url, "-> connected")
    except urllib.error.HTTPError as e:
        print(url, "-> connected, HTTP", e.code)
    except urllib.error.URLError as e:
        print(url, "-> refused:", type(e.reason).__name__, str(e.reason)[:110])
    except Exception as e:
        print(url, "-> FAILED before a request:", type(e).__name__, str(e)[:110])
print("store entries left out:", getattr(llm, "_store_certs_skipped", "n/a"))
"""

API = "https://api.anthropic.com/"
MUST_REFUSE = ["https://wrong.host.badssl.com/", "https://self-signed.badssl.com/",
               "https://untrusted-root.badssl.com/", "https://expired.badssl.com/"]


def connect(plugin, urls):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "SSL_CERT"))}
    code, out = run([sys.executable, "-c", CONNECT] + urls, cwd=os.path.join(plugin, "hooks"), env=env)
    return out if code == 0 else f"exit {code}: {last(out, 3)}"


def main():
    main_plugin, pr_plugin = (os.path.abspath(p) for p in sys.argv[1:3])
    say(f"Python {sys.version.split()[0]} {os.environ.get('PROCESSOR_ARCHITECTURE', '')}, {ssl.OPENSSL_VERSION}")
    source = inspect.getsource(ssl.SSLContext._load_windows_store_certs)
    say("this Python loads the store: "
        + ("one certificate at a time" if "for cert" in source and "except" in source else "in one call"))
    say(f"store before: CA {len(ssl.enum_certificates('CA'))} entries, ROOT {len(ssl.enum_certificates('ROOT'))}; "
        f"default context {context_builds()}")
    say("pull request has the change: " + str(os.path.exists(
        os.path.join(pr_plugin, "tests", "test_tls_store_unreadable_cert.py"))))
    say("clean store, main: " + connect(main_plugin, [API]).replace("\n", " ; "))
    say("clean store, pull request: " + connect(pr_plugin, [API]).replace("\n", " ; "))
    refusals_done = suite_done = False
    work = tempfile.mkdtemp(prefix="sg-store-cert-")
    for number, (label, der) in enumerate(candidates(), 1):
        say()
        say(f"== candidate {number}: {label}")
        path = os.path.join(work, f"candidate{number}.cer")
        with open(path, "wb") as f:
            f.write(der)
        try:
            how = add(der, path)
            if how is None:
                say("  Windows did not take it into the store")
                continue
            builds = context_builds()
            say(f"  in the store (through {how}); default context {builds}")
            say("  main: " + connect(main_plugin, [API]).replace("\n", " ; "))
            say("  pull request: " + connect(pr_plugin, [API]).replace("\n", " ; "))
            if builds != "builds" and not refusals_done:
                refusals_done = True
                for line in connect(pr_plugin, MUST_REFUSE).splitlines():
                    say("  pull request, must be refused: " + line)
            if builds != "builds" and not suite_done:
                suite_done = True
                code, out = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                 "tests/test_tls_store_unreadable_cert.py"], cwd=pr_plugin)
                say(f"  new test file with this store: exit {code}: {last(out)}")
                if code:
                    say("  " + last(out, 25))
        finally:
            say("  removed: " + str(remove(der)) + f"; default context {context_builds()}")
    say()
    say(f"store after: CA {len(ssl.enum_certificates('CA'))} entries; default context {context_builds()}")
    # The report again as annotations, for reading through the API.
    text, part = "\n".join(REPORT), 0
    while text and part < 9:
        chunk, text = text[:3000], text[3000:]
        part += 1
        chunk = chunk.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
        print(f"::notice title=store cert {sys.version.split()[0]} part {part}::{chunk}")


if __name__ == "__main__":
    main()
