from test_init import execute_cmd

import pytest


@pytest.fixture
def get_args():
    args = {
        "GroupLauncher": None,
        "GroupAmsi": "reflection",
        "GroupTransport": "http",
        "GroupClipExec": "none",
        "CheckboxProxy": "false",
        "CheckboxTLS1.2": "false",
        "RadioFingerprint": "true",
        "RadioNoVerification": "false",
        "RadioCertStore": "false",
    }
    yield args


def test_vbs(get_args):
    from powerhub.payloads import create_vbs
    args = get_args
    args['GroupLauncher'] = 'vbs'
    filename, payload = create_vbs(args)
    assert filename == 'powerhub-vbs-reflection-http.vbs'

    import tempfile
    tmpf = tempfile.NamedTemporaryFile('w', delete=False)
    tmpf.write(payload)
    tmpf.close()

    execute_cmd("ssh win10 del C:/Windows/Temp/powerhub.vbs")
    execute_cmd("scp %s win10:C:/Windows/Temp/powerhub.vbs" % tmpf.name)
    out = execute_cmd("ssh win10 cscript.exe C:/Windows/Temp/powerhub.vbs")
    assert "Windows Script Host" in out
    assert "error" not in out


def test_gcc(get_args):
    from powerhub.payloads import create_exe
    args = get_args
    args['GroupLauncher'] = 'mingw32-64bit'
    filename, payload = create_exe(args)
    assert filename == 'powerhub-mingw32-64bit-reflection-http.exe'
    assert b"DOS" in payload
    assert payload.startswith(b'MZ')


def test_mcs(get_args):
    from powerhub.payloads import create_dotnet
    args = get_args
    args['GroupLauncher'] = 'dotnetexe-64bit'
    filename, payload = create_dotnet(args)
    assert filename == 'powerhub-dotnetexe-64bit-reflection-http.exe'
    assert b"DOS" in payload
    assert payload.startswith(b'MZ')
