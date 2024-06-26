from requests import Session
from requests.exceptions import JSONDecodeError
from bs4 import BeautifulSoup, Tag
import re
from typing import Any

import config
import totp
from helpers import send_request


def login_with_drexel_connect(session: Session) -> Session:
    response = send_request(session, config.drexel_connect_base_url, method="GET")
    assert response.status_code == 200, "Failed to get Drexel Connect login page"
    soup = BeautifulSoup(response.text, "html.parser")

    csrf_token = extract_csrf_token(soup)
    form_action_path = extract_form_action_path(soup)

    login_payload = {
        "j_username": config.drexel_username,
        "j_password": config.drexel_password,
        "csrf_token": csrf_token,
        "_eventId_proceed": "",
    }

    # this should send the credentials and send the MFA request
    response = send_request(
        session,
        config.drexel_connect_base_url + form_action_path,
        data=login_payload,
        method="POST",
    )
    assert (
        response.status_code == 200
    ), "Failed to send request to Drexel Connect with username and password"

    soup = BeautifulSoup(response.text, "html.parser")
    data = parse_initial_mfa_page(soup)

    # the intial MFA page does not have the 'verification code' form field
    # the following two requests are sent to fetch the html page with the 'verification code' form field
    response = send_request(
        session,
        config.drexel_connect_base_url + data["url"],
        data=data["form-data"],
        method="POST",
    )
    assert (
        response.status_code == 200
    ), "Failed to request MFA code page from Drexel Connect"

    try:
        json_response = response.json()
    except JSONDecodeError:
        raise Exception(
            "Failed to decode JSON response from Drexel Connect. Response: {}".format(
                response.text
            )
        )

    data = {
        json_response["csrfN"]: json_response["csrfV"],
        "_eventId": json_response["actValue"],
    }

    response = send_request(
        session,
        config.drexel_connect_base_url + json_response["flowExURL"],
        data=data,
        method="POST",
    )
    # the response should be in HTML format that contains the 'verification code' form field
    assert (
        response.status_code == 200
    ), "Failed to receive MFA code page from Drexel Connect"
    soup = BeautifulSoup(response.text, "html.parser")

    parsed_data = parse_final_mfa_page(soup)

    if config.drexel_mfa_secret_key is not None:
        mfa_token = totp.get_token(config.drexel_mfa_secret_key)
    else:
        mfa_token = input("Please input your MFA verification code: ")

    data = {
        "csrf_token": parsed_data["csrf_token"],
        "_eventId": "proceed",
        "j_mfaToken": mfa_token,
    }

    # this request sends the MFA code to Drexel Connect
    response = send_request(
        session,
        config.drexel_connect_base_url + parsed_data["url"],
        data=data,
        method="POST",
    )
    assert (
        response.status_code == 200
    ), "Failed to send MFA code to Drexel Connect (final step)"

    # the session should now have the required cookies to access the TMS website
    return session


def extract_csrf_token(soup: BeautifulSoup) -> str:
    csrf_token_input_tag = soup.find("input", {"name": "csrf_token"})

    if not isinstance(csrf_token_input_tag, Tag):
        raise Exception("Could not find CSRF token.")

    csrf_token = csrf_token_input_tag["value"]

    if not isinstance(csrf_token, str):
        raise Exception(
            f"CSRF token was not a string. Found: {csrf_token} of type: {type(csrf_token)}"
        )

    return csrf_token


def extract_form_action_path(soup: BeautifulSoup) -> str:
    # the form is a child of a div with id "login-box"
    login_box_div = soup.find("div", {"id": "login-box"})

    if not isinstance(login_box_div, Tag):
        raise Exception("Could not find login box div.")

    login_form = login_box_div.find("form")

    if not isinstance(login_form, Tag):
        raise Exception("Could not find login form.")

    form_action_path = login_form["action"]

    if not isinstance(form_action_path, str):
        raise Exception(
            f"Form action path was not a string. Found: {form_action_path} of type: {type(form_action_path)}"
        )

    return form_action_path


def parse_initial_mfa_page(soup: BeautifulSoup) -> dict[str, Any]:
    data = {}

    # get the first script tag that isn't empty
    script_tag = soup.find("script", string=lambda text: text and len(text) > 0)

    if not isinstance(script_tag, Tag):
        raise Exception("Could not find non-empty script tag.")

    script_content = script_tag.string

    if not isinstance(script_content, str):
        raise Exception(
            f"Script content was not a string. Found: {script_content} of type: {type(script_content)}"
        )

    url_match = re.search(
        r"url:\s*['\"](/idp/profile/cas/login\?execution=[^'\"]+)['\"]", script_content
    )
    if not url_match:
        raise Exception("Could not find MFA URL.")

    event_id_match = event_id_match = re.search(
        r"data:\s*'_eventId=([^'&]+)&csrf_token", script_content
    )
    if not event_id_match:
        raise Exception("Could not find MFA event ID.")

    csrf_token_match = re.search(r"csrf_token=([^'&]+)", script_content)
    if not csrf_token_match:
        raise Exception("Could not find MFA CSRF token.")

    data["url"] = url_match.group(1)
    data["form-data"] = {
        "_eventId": event_id_match.group(1),
        "csrf_token": csrf_token_match.group(1),
    }

    return data


def parse_final_mfa_page(soup: BeautifulSoup) -> dict[str, str]:
    data: dict[str, str] = {}

    # get form by id "otp"
    form = soup.find("form", {"id": "otp"})

    if not isinstance(form, Tag):
        raise Exception("Could not find OTP form.")

    url = form["action"]

    if not isinstance(url, str):
        raise Exception(f"Action was not a string. Found: {url} of type: {type(url)}")

    csrf_token_input = form.find("input", {"name": "csrf_token"})

    if not isinstance(csrf_token_input, Tag):
        raise Exception("Could not find CSRF token input.")

    csrf_token = csrf_token_input["value"]

    if not isinstance(csrf_token, str):
        raise Exception(
            f"CSRF token was not a string. Found: {csrf_token} of type: {type(csrf_token)}"
        )

    data["url"] = url
    data["csrf_token"] = csrf_token

    return data
