import secrets, string

def generate_token():
    characters = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(characters) for i in range(20))
    return token

