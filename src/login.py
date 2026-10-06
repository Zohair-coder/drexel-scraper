import time
from urllib.parse import urlsplit

from playwright.sync_api import (
    Page,
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from requests import Session

import config
import totp

# The unattended browser has no passkey. Report cancellation to Microsoft's
# existing sign-in flow rather than leaving a native WebAuthn dialog pending.
# Microsoft then offers the account's other allowed methods. This does not
# authenticate a passkey or change the account's authentication requirements.
CANCEL_UNAVAILABLE_PASSKEY = """
(() => {
    if (!["login.microsoft.com", "login.microsoftonline.com"].includes(location.hostname)) return;
    if (!navigator.credentials || !navigator.credentials.get) return;
    const originalGet = navigator.credentials.get.bind(navigator.credentials);
    navigator.credentials.get = (options) => {
        if (options && options.publicKey) {
            return Promise.reject(new DOMException(
                "No passkey available in unattended browser", "NotAllowedError"
            ));
        }
        return originalGet(options);
    };
})();
"""


def _wait_for_login_result(page: Page) -> str:
    result = page.wait_for_function(
        """() => {
            const visible = selector => {
                const element = document.querySelector(selector);
                return element && element.getClientRects().length > 0;
            };
            if (location.origin === 'https://connect.drexel.edu' && visible('#logoutLink')) {
                return 'signed-in';
            }
            if (visible('#idSubmit_ProofUp_Redirect')) return 'registration';
            if (visible('#idBtn_Back') && document.body.innerText.includes('Stay signed in?')) {
                return 'stay-signed-in';
            }
            const error = document.querySelector('#idDiv_SAOTCC_Error');
            if (visible('#idDiv_SAOTCC_Error') && error.textContent.trim()) return 'invalid-code';
            return false;
        }"""
    )
    try:
        return str(result.json_value())
    finally:
        result.dispose()


def _sign_in(page: Page) -> None:
    stage = "Drexel sign-in"
    try:
        page.goto("https://connect.drexel.edu")
        page.locator("button[name='_eventId_proceed']").click()

        stage = "Microsoft username"
        page.locator("input[name='loginfmt']").fill(config.drexel_email)
        page.get_by_role("button", name="Next", exact=True).click()

        stage = "password method selection"
        # The username form also contains a password input. Wait for the real
        # password submit button or the account-specific method chooser.
        password_option = page.get_by_role("button", name="Use my password", exact=True)
        password_submit = page.get_by_role("button", name="Sign in", exact=True)
        password_option.or_(password_submit).first.wait_for()
        if password_option.is_visible():
            password_option.click()

        stage = "Microsoft password"
        password_submit.wait_for()
        page.locator("input[name='passwd']").fill(config.drexel_password)
        password_submit.click()

        stage = "verification-code method selection"
        code_option = page.locator("[data-value='PhoneAppOTP']")
        code_input = page.locator("input[name='otc']")
        code_option.or_(code_input).first.wait_for()
        if code_option.is_visible():
            code_option.click()

        stage = "verification-code entry"
        code_input.wait_for()
        if config.drexel_mfa_secret_key is not None:
            # Generate only after the code form is ready, with enough validity
            # remaining to submit it before the next 30-second TOTP interval.
            remaining = 30 - time.time() % 30
            if remaining < 5:
                page.wait_for_timeout((remaining + 0.1) * 1000)
            mfa_token = totp.get_token(config.drexel_mfa_secret_key)
        else:
            mfa_token = input("Please input your MFA verification code: ")
        code_input.fill(mfa_token)
        page.get_by_role("button", name="Verify", exact=True).click()

        stage = "return to Drexel after MFA"
        result = _wait_for_login_result(page)
        if result == "stay-signed-in":
            page.get_by_role("button", name="No", exact=True).click()
            result = _wait_for_login_result(page)
        if result == "registration":
            raise RuntimeError(
                "Microsoft requires interactive security-information registration. "
                "Complete the prompt in a normal browser and keep both the passkey "
                "and TOTP method registered."
            )
        if result == "invalid-code":
            raise RuntimeError(
                "Microsoft rejected the verification code. Check the registered "
                "TOTP secret and system clock."
            )
        if result != "signed-in":
            raise RuntimeError("Microsoft authentication did not return to Drexel")
    except PlaywrightTimeoutError:
        # Playwright call logs and URLs can contain credential values and
        # authentication query parameters. Report only the stage and hostname.
        raise RuntimeError(
            f"Login timed out during {stage} at {urlsplit(page.url).hostname}."
        ) from None


def login_with_drexel_connect(session: Session) -> Session:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            context.add_init_script(CANCEL_UNAVAILABLE_PASSKEY)
            page = context.new_page()
            _sign_in(page)

            for cookie in context.cookies():
                session.cookies.set(  # type: ignore[no-untyped-call]
                    cookie["name"],
                    cookie["value"],
                    domain=cookie["domain"],
                    path=cookie["path"],
                )
            return session
        finally:
            browser.close()
