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
    token_parts = jwt.split('.')
    if len(token_parts) != 3:
        return None
    header_part, payload_part, signature_part = token_parts
    try:
        header = b64d(header_part)
        payload = b64d(payload_part+"==")
        signature_provided = signature_part
        headers_json = json.loads(header)
        payload_json = json.loads(payload)
        return headers_json, payload_json, signature_provided
    except Exception as e:
        print(e)
        return None


def is_jwt_valid(jwt):
    # split the jwt
    if jwt is None or len(jwt)==0:
        return False
    decompose = decompose_jwt(jwt)
    if decompose is None:
        return False
    headers, payload, signature_provided = decompose
    
    # check the expiration time - note this will cause an error if there is no 'exp' claim in the jwt
    if not "exp" in payload:
        return False
    expiration = payload["exp"]
    is_token_expired = (expiration - time.time()) <= 0
    
    #build a signature based on the header and payload using the secret
    test_jwt = generate_jwt(headers, payload)
    test_jwt_parts = test_jwt.split(".")
    test_jwt_signature = test_jwt_parts[2]
    
    # verify it matches the signature provided in the jwt
    is_signature_valid = (test_jwt_signature==signature_provided)
        
    if is_token_expired or not is_signature_valid:
        return False
    else:
        return True

def detokenize_from_request(request, bypass=False):
    """
    """
    if bypass:
        pass
    auth_data = request.headers.get("authorization")
    if auth_data is not None and (auth_data.startswith("bearer") or auth_data.startswith("Bearer")):
        spl = auth_data.split(" ")
        if len(spl)==2:
            token = spl[1]
            if not is_jwt_valid(token):
                return None
            return decompose_jwt(token)