#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check actual OpenSSL interoperability and private file handling in the ttyd init helper."""

from pathlib import Path
import stat
import subprocess
import sys
import tempfile


def run(*command):
    return subprocess.run(command, check=True, capture_output=True).stdout


def main():
    source = Path(sys.argv[1]).read_text()
    helper = source[source.index("luci_tls_pem()"):source.index("ttyd_instance()")]
    with tempfile.TemporaryDirectory(prefix="ttyd-tls-check-") as temporary:
        directory = Path(temporary)
        runtime = directory / "runtime"
        script = directory / "normalize.sh"
        script.write_text(helper.replace("/var/run/ttyd-luci", str(runtime)) + '\nluci_tls_pem "$@"\n')
        for algorithm, options in [
            ("ec", ["ec", "-pkeyopt", "ec_paramgen_curve:prime256v1"]),
            ("rsa", ["rsa:2048"]),
        ]:
            key = directory / (algorithm + ".key")
            cert = directory / (algorithm + ".crt")
            run("openssl", "req", "-x509", "-newkey", *options, "-nodes", "-days", "1",
                "-subj", "/CN=ci.invalid", "-keyout", str(key), "-out", str(cert))
            der_key = directory / (algorithm + ".key.der")
            der_cert = directory / (algorithm + ".crt.der")
            run("openssl", "pkey", "-in", str(key), "-outform", "DER", "-out", str(der_key))
            run("openssl", "x509", "-in", str(cert), "-outform", "DER", "-out", str(der_cert))
            for encoding, input_cert, input_key in [("pem", cert, key), ("der", der_cert, der_key)]:
                name = algorithm + "_" + encoding
                before = (input_cert.read_bytes(), input_key.read_bytes())
                run("sh", str(script), str(input_cert), str(input_key), name)
                output_cert = runtime / (name + ".crt")
                output_key = runtime / (name + ".key")
                assert run("openssl", "x509", "-in", str(cert), "-noout", "-fingerprint", "-sha256") == \
                    run("openssl", "x509", "-in", str(output_cert), "-noout", "-fingerprint", "-sha256")
                assert run("openssl", "pkey", "-in", str(key), "-pubout") == \
                    run("openssl", "pkey", "-in", str(output_key), "-pubout")
                assert stat.S_IMODE(output_cert.stat().st_mode) == 0o600
                assert stat.S_IMODE(output_key.stat().st_mode) == 0o600
                assert (input_cert.read_bytes(), input_key.read_bytes()) == before
        assert stat.S_IMODE(runtime.stat().st_mode) == 0o700
        broken = directory / "broken"
        broken.write_text("invalid certificate or key\n")
        for name, input_cert, input_key in [("bad_cert", broken, key), ("bad_key", cert, broken)]:
            result = subprocess.run(["sh", str(script), str(input_cert), str(input_key), name],
                                    capture_output=True)
            assert result.returncode != 0
            assert not list(runtime.glob(name + ".*"))
    print("EC/RSA DER and PEM normalize correctly; original files remain intact; private files stay private; invalid inputs fail closed.")


if __name__ == "__main__":
    main()
