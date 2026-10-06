"""Exercise Microsoft login transitions in Chromium without real credentials."""

import os
import sys
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def login_module(monkeypatch):
    monkeypatch.setenv("DREXEL_EMAIL", "test@example.test")
    monkeypatch.setenv("DREXEL_PASSWORD", "test-password")
    import login

    monkeypatch.setattr(login.config, "drexel_email", "test@example.test")
    monkeypatch.setattr(login.config, "drexel_password", "test-password")
    # Public RFC 6238 test secret, not an account credential.
    monkeypatch.setattr(
        login.config, "drexel_mfa_secret_key", "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    )
    return login


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def login_page(browser, login_module):
    context = browser.new_context()
    context.add_init_script(login_module.CANCEL_UNAVAILABLE_PASSKEY)
    page = context.new_page()
    page.set_default_timeout(5000)
    yield page
    context.close()


def mock_sign_in(page, *, passkey=False, outcome="success"):
    """Serve real forms, navigation, and a WebAuthn request via network routes."""
    visited = []
    first_method = "passkey" if passkey else "password"
    second_method = "mfa-methods" if passkey else "code"
    pages = {
        "/": """
            <button name="_eventId_proceed"
              onclick="location.href='https://login.microsoftonline.com/username'">Sign in</button>
        """,
        "/username": f"""
            <input name="loginfmt">
            <!-- Microsoft also renders a password input on its username page. -->
            <input name="passwd" type="password">
            <button onclick="if (document.querySelector('[name=loginfmt]').value === 'test@example.test')
              location.href='/{first_method}'">Next</button>
        """,
        "/passkey": """
            <script>
            navigator.credentials.get({publicKey: {
                challenge: new Uint8Array([1, 2, 3]), timeout: 60000
            }}).catch(error => {
                if (error.name === 'NotAllowedError') location.href='/methods';
            });
            </script>
        """,
        "/methods": """
            <h1>Choose a way to sign in</h1>
            <div role="button" onclick="location.href='/password'">Use my password</div>
        """,
        "/password": f"""
            <input name="passwd" type="password">
            <button onclick="if (document.querySelector('[name=passwd]').value === 'test-password')
              location.href='/{second_method}'">Sign in</button>
        """,
        "/mfa-methods": """
            <h1>Verify your identity</h1>
            <div role="button" data-value="FidoKey">Face, fingerprint, PIN or security key</div>
            <div role="button" data-value="PhoneAppOTP"
              onclick="location.href='/code'">Use a verification code</div>
        """,
        "/code": r"""
            <input name="otc">
            <button onclick="if (/^\d{6}$/.test(document.querySelector('[name=otc]').value))
              location.href='/result'">Verify</button>
        """,
        "/result": {
            "success": "<script>location.href='https://connect.drexel.edu/signed-in'</script>",
            "kmsi": """
                <h1>Stay signed in?</h1>
                <button id="idBtn_Back"
                  onclick="location.href='https://connect.drexel.edu/signed-in'">No</button>
            """,
            "registration": '<button id="idSubmit_ProofUp_Redirect">Next</button>',
            "invalid-code": '<div id="idDiv_SAOTCC_Error">Invalid verification code</div>',
        }[outcome],
        "/signed-in": '<a id="logoutLink">SIGN OUT</a>',
    }

    def respond(route):
        path = urlsplit(route.request.url).path
        visited.append(path)
        route.fulfill(content_type="text/html", body=pages.get(path, "Unknown page"))

    page.context.route("**/*", respond)
    return visited


@pytest.mark.parametrize("passkey", [False, True])
@pytest.mark.parametrize("outcome", ["success", "kmsi"])
def test_password_totp_login(login_page, login_module, passkey, outcome):
    visited = mock_sign_in(login_page, passkey=passkey, outcome=outcome)

    login_module._sign_in(login_page)

    assert login_page.url == "https://connect.drexel.edu/signed-in"
    assert {"/password", "/code", "/result"}.issubset(visited)
    if passkey:
        assert {"/passkey", "/methods", "/mfa-methods"}.issubset(visited)


@pytest.mark.parametrize(
    "outcome, message",
    [
        ("registration", "requires interactive security-information registration"),
        ("invalid-code", "rejected the verification code"),
    ],
)
def test_login_explains_actionable_failures(login_page, login_module, outcome, message):
    mock_sign_in(login_page, passkey=True, outcome=outcome)

    with pytest.raises(RuntimeError, match=message):
        login_module._sign_in(login_page)


def test_timeout_does_not_expose_credentials_or_url_queries(login_page, login_module):
    login_page.set_default_timeout(1000)

    def respond(route):
        if urlsplit(route.request.url).hostname == "connect.drexel.edu":
            body = """
                <button name="_eventId_proceed" onclick="location.href=
                'https://login.microsoftonline.com/error?token=private-token'">Sign in</button>
            """
        else:
            body = '<input type="password" value="test-password"><div>Unexpected page</div>'
        route.fulfill(content_type="text/html", body=body)

    login_page.context.route("**/*", respond)
    with pytest.raises(RuntimeError, match="Microsoft username") as error:
        login_module._sign_in(login_page)

    assert "login.microsoftonline.com" in str(error.value)
    assert "test-password" not in str(error.value)
    assert "private-token" not in str(error.value)
    assert error.value.__suppress_context__


def test_passkey_cancellation_is_scoped_to_microsoft(login_page, login_module):
    login_page.context.route("**/*", lambda route: route.fulfill(body="<p>Test</p>"))
    login_page.goto("https://example.test")
    result = login_page.evaluate(
        """async script => {
            navigator.credentials.get = async () => 'original-get';
            eval(script);
            return await navigator.credentials.get({publicKey: {}});
        }""",
        login_module.CANCEL_UNAVAILABLE_PASSKEY,
    )
    assert result == "original-get"
