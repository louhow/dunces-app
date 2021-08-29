from cryptography.fernet import Fernet


class CipherSuite:
  def __init__(self, app_key: str):
    self._cipher_suite = Fernet(app_key.encode())

  def encrypt(self, unsecure: str) -> str:
    return self._cipher_suite.encrypt(unsecure.encode())\
      .decode()

  def decrypt(self, encrypted: str) -> str:
    return self._cipher_suite.decrypt(encrypted.encode())\
      .decode()
