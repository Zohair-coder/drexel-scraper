from requests import Session
from requests.exceptions import HTTPError
import time

def send_get_request(session: Session, url: str):
    resp = session.get(url)

    try:
        resp.raise_for_status()
    except HTTPError as e:
        retries = 10
        wait = 1
        for _ in range(retries):
            time.sleep(wait)
            resp = session.get(url)
            try:
                resp.raise_for_status()
            except HTTPError as e:
                wait *= 2
                continue
            return resp   
        
        resp_text = e.response.text
        raise Exception("Error sending HTTP request to {}. Response received: {}".format(url, resp_text)) from e
    
    return resp 