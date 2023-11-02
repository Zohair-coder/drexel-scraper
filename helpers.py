from requests import Session
from requests.exceptions import HTTPError
import time

def send_request(session: Session, url: str, method: str = "GET", json: dict = {}, headers: dict = {}):
    try:
        resp = send_request_helper(session, url, method, json, headers)
        resp.raise_for_status()
    except Exception as ex:
        retries = 10
        for _ in range(retries):
            try:
                resp = send_request_helper(session, url, method, json, headers)
                resp.raise_for_status()
            except Exception as inner_ex:
                if isinstance(inner_ex, HTTPError) and inner_ex.response.status_code == 429 and inner_ex.response.headers.get("Retry-After") is not None:
                    if inner_ex.response.headers.get("Retry-After"):
                        time.sleep(int(inner_ex.response.headers["Retry-After"]))
                    else:
                        time.sleep(1)
                continue
            return resp   
        
        if isinstance(ex, HTTPError):
            resp_headers = ex.response.headers
            resp_text = ex.response.text
            raise Exception("Error sending HTTP request to {}.\nResponse headers: {}\nResponse text received: {}".format(url, resp_headers, resp_text)) from ex
        raise Exception("Error sending HTTP request to {}.".format(url)) from ex
    
    return resp 

def send_request_helper(session: Session, url: str, method: str, json: dict, headers: dict):
    timeout = 2
    if method == "GET":
        resp = session.get(url, headers=headers, timeout=timeout)
    elif method == "POST":
        resp = session.post(url, json=json, headers=headers, timeout=timeout)
    else:
        raise Exception("Invalid method: {}".format(method))
    return resp