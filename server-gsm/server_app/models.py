
from pydantic import BaseModel

class Sms(BaseModel):
    recipient: str
    message: str

class Call(BaseModel):
    recipient: str

class ForwardingNumber(BaseModel):
    forwarding_number: str

class UssdCode(BaseModel):
    ussd_code: str

class ModemConfig(BaseModel):
    port: str
    baudrate: int
    pin: str
    apn: str = None  # APN is optional
    ussd_activation_code: str = None  # USSD activation code is optional
    auto_answer_calls: bool = True  # New field with default value True

class ApnConfig(BaseModel):
    apn: str

class ApiKey(BaseModel):
    api_key: str
