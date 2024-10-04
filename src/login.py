from playwright.sync_api import sync_playwright, ElementHandle
import config
import totp
from requests import Session


def login_with_drexel_connect(session: Session) -> Session:
    # extra timeout waits added because sometimes
    # page would load without the selected element
    # being rendered
    # a better approach would be welcome
    extra_timeout = 2000

    # ideally we would also want all our query
    # selectors in config.py so that they can be
    # changed easily if the site changes

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://connect.drexel.edu")

        page.wait_for_timeout(extra_timeout)

        sign_in = page.query_selector("button[name='_eventId_proceed']")
        assert isinstance(
            sign_in, ElementHandle
        ), "Sign in button on Drexel Connect not found"
        sign_in.click()

        page.wait_for_selector("input[name='loginfmt']")
        page.wait_for_timeout(extra_timeout)

        email_input = page.query_selector("input[name='loginfmt']")
        assert isinstance(
            email_input, ElementHandle
        ), "Email field on Microsoft Online not found"
        email_input.fill(config.drexel_email)

        page.get_by_text("Next").click()

        page.wait_for_selector("input[name='passwd']")
        page.wait_for_timeout(extra_timeout)

        password_input = page.query_selector("input[name='passwd']")
        assert isinstance(
            password_input, ElementHandle
        ), "Password field on Microsoft Online not found"
        password_input.fill(config.drexel_password)

        page.wait_for_selector("input[type='submit']")
        page.wait_for_timeout(extra_timeout)
        page.get_by_text("Sign in").click()

        if config.use_microsoft_authenticator:
            page.wait_for_selector("input[name='otc']")
            page.wait_for_timeout(extra_timeout)

            mfa_input = page.query_selector("input[name='otc']")
            assert isinstance(
                mfa_input, ElementHandle
            ), "MFA input field on Microsoft Online not found"
            mfa_input.fill(input("Please input your Microsoft Authenticator verification code: "))

            page.wait_for_selector("input[type='submit']")
            page.wait_for_timeout(extra_timeout)

            submit_button = page.query_selector("input[type='submit']")
            assert isinstance(
                submit_button, ElementHandle
            ), "Submit button on Microsoft Online for MFA not found"
            submit_button.click()
        else:
            if config.drexel_mfa_secret_key is not None:
                mfa_token = totp.get_token(config.drexel_mfa_secret_key)
            else:
                mfa_token = input("Please input your MFA verification code: ")

            page.wait_for_selector("input[name='otc']")
            page.wait_for_timeout(extra_timeout)

            mfa_input = page.query_selector("input[name='otc']")
            assert isinstance(
                mfa_input, ElementHandle
            ), "MFA input field on Microsoft Online not found"
            mfa_input.fill(mfa_token)

            page.wait_for_selector("input[type='submit']")
            page.wait_for_timeout(extra_timeout)

            submit_button = page.query_selector("input[type='submit']")
            assert isinstance(
                submit_button, ElementHandle
            ), "Submit button on Microsoft Online for MFA not found"
            submit_button.click()

        page.wait_for_url("https://connect.drexel.edu/**")
        page.wait_for_timeout(extra_timeout)

        for cookie in context.cookies():
            session.cookies.set(
                cookie["name"], cookie["value"], domain=cookie["domain"]
            )  # type: ignore

        browser.close()
        return session
