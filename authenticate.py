import base64
import time
import json
import hmac
import hashlib

def b64e(s):
    return base64.b64encode(s.encode(encoding='utf-8')).decode()


def b64d(s):
    return base64.b64decode(s).decode(encoding='utf-8')

def get_secret_key():
        return "secret@4"

def base64url_encode(s):
    encoded = b64e(s)
    source_chars, target_chars = '+/', '-_'
    for cs,ct in zip(source_chars, target_chars):
        encoded = encoded.replace(cs, ct)
    while encoded[-1]=='=':
        encoded = encoded[:-1]
    return encoded

def tokenize(data):
    """
    generates token that holds the data
    @params
    data : dict
        the data to include in the payload
    """
    expire_time = 86400
    headers = {'alg':'HS256','typ':'JWT'}
    payload = data
    payload["sub"]="none"
    payload['exp']=int(time.time()) + expire_time
    jwt = generate_jwt(headers, payload)
    return jwt

def generate_jwt(headers, payload):
    secret = get_secret_key()
    headers_encoded = base64url_encode(json.dumps(headers))
    payload_encoded = base64url_encode(json.dumps(payload))
    data = "{}.{}".format(headers_encoded, payload_encoded)
        
    signature = hmac.new(bytes(secret, 'UTF-8'), data.encode(), hashlib.sha256).hexdigest()
    signature_encoded = base64url_encode(signature)
    jwt = "{}.{}.{}".format(headers_encoded,payload_encoded,signature_encoded)
    return jwt

def decompose_jwt(jwt):
    # returns payload in $jwt, doesn't verify
    tokenParts = jwt.split('.')
    header = b64d(tokenParts[0])
    payload = b64d(tokenParts[1])
    signature_provided = tokenParts[2]
    payload_json = json.loads(payload)
    return payload_json

def is_jwt_valid(jwt):
    # split the jwt
    if jwt is None or len(jwt)==0:
        return False
    secret = get_secret_key()
    tokenParts = jwt.split('.')
    if len(tokenParts)!=3:
        return False
    header = b64d(tokenParts[0])
    payload = b64d(tokenParts[1])
    signature_provided = tokenParts[2]
    
    # check the expiration time - note this will cause an error if there is no 'exp' claim in the jwt
    payload_json = payload
    if not "exp" in payload_json:
        return False
    expiration = payload[exp]
    is_token_expired = (expiration - time.time()) <= 0
    
    #build a signature based on the header and payload using the secret
    base64_url_header = base64url_encode(header)
    base64_url_payload = base64url_encode(payload)
    data = "{}.{}".format(base64_url_header, base64_url_payload)
    signature = hmac.new(bytes(secret, 'UTF-8'), data.encode(), hashlib.sha256).hexdigest()
    base64_url_signature = base64url_encode(signature)
    
    # verify it matches the signature provided in the jwt
    is_signature_valid = (base64_url_signature==signature_provided)
        
    if is_token_expired or not is_signature_valid:
        return False
    else:
        return True

def detokenize_from_request(headers, bypass=False):
    """
    checks if token came with request and returns contents of token payload
    @params : bypass => set up token-data to handle as if user requested
    """
    if "Authorization" in headers:
        auth = headers["Authorization"]
        auth_data = auth.split(" ")
        token = auth_data[1]
        if not is_jwt_valid(token):
            return None
        return decompose_jwt(token)
    else:
        if bypass:
            return {"username":"guest"}
        return None