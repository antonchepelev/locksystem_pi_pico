
import ubinascii
import uhashlib

def hash_password(password):
    sha256_hash = uhashlib.sha256(password.encode('utf-8')).digest()
    return ubinascii.hexlify(sha256_hash)


def password_exists(password_storage_path): #takes password file path as param
    with open(password_storage_path,"r") as file:
            password = file.readline()
    
    if password != "": #condition that checks weather there is a password on file or not
        return True
    else:
        return False

