import hmac
import base64
import struct
import time
import hashlib


# https://stackoverflow.com/questions/8529265/google-authenticator-implementation-in-python
def get_token(secret: str) -> str:
    period = 30
    interval_no = int(time.time() // period)
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", interval_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    h = (struct.unpack(">I", h[o : o + 4])[0] & 0x7FFFFFFF) % 1000000
    return str(h).zfill(6)

if __name__ == "__main__":
    import config
    if config.drexel_mfa_secret_key is not None:
        print(get_token(config.drexel_mfa_secret_key))
    else:
        print(f"Please set your MFA secret key to run this script. See {config.environ_help_url} for more information and help")
