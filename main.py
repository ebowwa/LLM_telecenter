from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import TimeoutException, InvalidStateException
from fastapi import HTTPException
from retrying import retry
import json
import uvicorn
import re
import logging
import traceback

# Import the auto-reply module
from auto_reply_module import GPT4SMSAutoReply

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the forwarding number
forwarding_number = None

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

class ApnConfig(BaseModel):
    apn: str

modem = None
modem_connected = False  # Global variable to keep track of modem's connection status

class ApiKey(BaseModel):
    api_key: str

@app.post("/set_api_key")
async def set_api_key(api_key_param: ApiKey):
    global auto_reply
    auto_reply.api_key = api_key_param.api_key
    logger.info("API key set")
    return {"message": "API key set"}


def handle_incoming_sms(sms):
    # Log the incoming SMS message
    logger.info(f"Received SMS from {sms.number}: {sms.text}")

    # Generate a response using the auto-reply module
    response_message = auto_reply.handle_incoming_sms(sms.number, sms.text)
    
    # Send the response as an SMS
    if response_message is not None:
        modem.sendSms(sms.number, response_message)
        logger.info(f"Response SMS sent to {sms.number}: {response_message}")

def handle_incoming_call(call):
    global forwarding_number
    logger.info(f"Incoming call from {call.number}")
    if forwarding_number is not None:
        # Forward the call
        response = modem.write(f'AT+CCFC=1,3,"{forwarding_number}"')
        if "OK" in response:
            logger.info("Call forwarded")
        else:
            logger.error("Failed to forward call")
    else:
        # Handle the call according to existing logic
        call.answer()

def check_modem_connected():
    if not modem_connected:
        raise HTTPException(status_code=500, detail="Modem is not connected")

@app.post("/init_modem")
async def init_modem(config: ModemConfig):
    global modem, modem_connected
    try:
        modem = GsmModem(config.port, config.baudrate)
        modem.connect(config.pin)
        modem.smsReceivedCallback = handle_incoming_sms
        modem.incomingCallCallback = handle_incoming_call
        
        if config.apn is not None:
            modem.write(f'AT+CGDCONT=1,"IP","{config.apn}"')
            logger.info("APN set")
        
        if config.ussd_activation_code is not None:
            response = modem.sendUssd(config.ussd_activation_code)
            logger.info(f"USSD activated: {response}")
        
        modem_connected = True  # Update connection status
        logger.info("Modem initialized and connected")
        return {"message": "Modem initialized and connected"}
    except Exception as e:
        modem_connected = False  # Update connection status
        logger.error(f"Failed to initialize and connect modem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_apn")
async def get_apn():
    try:
        check_modem_connected()
        response = modem.write('AT+CGDCONT?')
        return {"response": response}
    except Exception as e:
        logger.error(f"Failed to get APN: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set_apn")
async def set_apn(apn_config: ApnConfig):
    try:
        check_modem_connected()
        modem.write(f'AT+CGDCONT=1,"IP","{apn_config.apn}"')
        logger.info("APN set")
        return {"message": "APN set"}
    except Exception as e:
        logger.error(f"Failed to set APN: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send_sms")
async def send_sms(sms: Sms):
    try:
        check_modem_connected()
        await retry_send_sms(sms.recipient, sms.message)
        logger.info("SMS sent")
        return {"message": "SMS sent"}
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@retry(stop_max_attempt_number=3, wait_fixed=2000)
async def retry_send_sms(recipient: str, message: str):
    modem.sendSms(recipient, message)

@app.post("/make_call")
async def make_call(call: Call):
    try:
        check_modem_connected()
        modem.dial(call.recipient)
        logger.info("Call made")
        return {"message": "Call made"}
    except Exception as e:
        logger.error(f"Failed to make call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set_forwarding_number")
async def set_forwarding_number(forwarding_number_param: ForwardingNumber):
    global forwarding_number
    forwarding_number = forwarding_number_param.forwarding_number
    logger.info(f"Forwarding number set to {forwarding_number}")
    return {"message": "Forwarding number set"}

@app.post("/reset_forwarding_number")
async def reset_forwarding_number():
    global forwarding_number
    forwarding_number = None
    logger.info("Forwarding number reset")
    return {"message": "Forwarding number reset"}

@app.post("/enable_auto_reply")
async def enable_auto_reply():
    auto_reply.enable_auto_reply()
    return {"message": "Auto-reply enabled"}

@app.post("/disable_auto_reply")
async def disable_auto_reply():
    auto_reply.disable_auto_reply()
    return {"message": "Auto-reply disabled"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
