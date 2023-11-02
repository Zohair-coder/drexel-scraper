from requests import Session
from requests.exceptions import HTTPError
import time

def send_request(session: Session, url: str, method: str = "GET", json: dict = {}, headers: dict = {}):
    
    resp = send_request_helper(session, url, method, json, headers)

    try:
        resp.raise_for_status()
    except HTTPError as e:
        retries = 10
        wait = 1
        for _ in range(retries):
            time.sleep(wait)

            resp = send_request_helper(session, url, method, json, headers)
            try:
                resp.raise_for_status()
            except HTTPError as e:
                if e.response.status_code == 429 and e.response.headers.get("Retry-After") is not None:
                    time.sleep(int(e.response.headers["Retry-After"]))
                wait *= 2
                continue
            return resp   
        
        resp_headers = e.response.headers
        resp_text = e.response.text
        raise Exception("Error sending HTTP request to {}.\nResponse headers: {}\nResponse text received: {}".format(url, resp_headers, resp_text)) from e
    
    return resp 

def send_request_helper(session, url, method, json, headers):
    if method == "GET":
        resp = session.get(url)
    elif method == "POST":
        resp = session.post(url, json=json, headers=headers)
    else:
        raise Exception("Invalid method: {}".format(method))
    return resp