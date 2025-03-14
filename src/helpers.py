from requests import Session, Response
from requests.exceptions import HTTPError
import time
from typing import Any


def send_request(
    session: Session,
    url: str,
    method: str = "GET",
    json: dict[str, Any] = {},
    headers: dict[str, str] = {},
    data: dict[str, Any] = {},
) -> Response:
    try:
        headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        )
        resp = send_request_helper(session, url, method, json, headers, data)
        resp.raise_for_status()
    except Exception as ex:
        retries = 10
        for _ in range(retries):
            try:
                resp = send_request_helper(session, url, method, json, headers, data)
                resp.raise_for_status()
            except Exception as inner_ex:
                if (
                    isinstance(inner_ex, HTTPError)
                    and inner_ex.response.status_code == 429
                ):
                    if inner_ex.response.headers.get("Retry-After"):
                        time.sleep(int(inner_ex.response.headers["Retry-After"]))
                        continue
                time.sleep(2)
                continue
            return resp

        if isinstance(ex, HTTPError):
            resp_headers = ex.response.headers
            resp_text = ex.response.text
            raise Exception(
                "Error sending HTTP request to {}.\nResponse headers: {}\nResponse text received: {}".format(
                    url, resp_headers, resp_text
                )
            ) from ex
        raise Exception("Error sending HTTP request to {}.".format(url)) from ex

    return resp


def send_request_helper(
    session: Session,
    url: str,
    method: str,
    json: dict[str, Any],
    headers: dict[str, str],
    data: dict[str, Any],
) -> Response:
    timeout = 2
    if method == "GET":
        resp = session.get(url, headers=headers, timeout=timeout)
    elif method == "POST":
        resp = session.post(url, json=json, data=data, headers=headers, timeout=timeout)
    else:
        raise Exception("Invalid method: {}".format(method))
    return resp
