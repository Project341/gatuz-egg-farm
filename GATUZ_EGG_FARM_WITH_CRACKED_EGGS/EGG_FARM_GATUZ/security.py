import hashlib,secrets,hmac
def make_password(password):
 salt=secrets.token_hex(16); digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),240000).hex(); return digest,salt
def verify_password(password,digest,salt):
 return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),240000).hex(),digest)
