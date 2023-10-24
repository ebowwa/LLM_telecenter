from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from flask import request, jsonify
from server_app.models import Sms, Call, ForwardingNumber, UssdCode, ModemConfig, ApnConfig, ApiKey
from server_app.modem_manager import ModemManager
from server_app.auto_reply_manager import AutoReplyManager
from server_app.auto_reply_module import GPT4SMSAutoReply
from server_app.mms_manager import download_multimedia_content, store_multimedia_content
from server_app.sms_manager import SmsManager
import logging
import traceback
from retrying import retry
import uuid
import shutil
import os


app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the forwarding number
forwarding_number = None
multimedia_dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'multimedia')


@app.post("/set_api_key")
async def set_api_key(api_key_param: ApiKey):
    return AutoReplyManager.set_api_key(api_key_param.api_key)

@app.post("/init_modem")
async def init_modem(config: ModemConfig):
    return ModemManager.init_modem(config)

@app.get("/get_apn")
async def get_apn():
    return ModemManager.get_apn()

@app.post("/set_apn")
async def set_apn(apn_config: ApnConfig):
    return ModemManager.set_apn(apn_config)

@app.post("/send_sms")
async def send_sms(sms: Sms):
    return ModemManager.send_sms(sms)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
async def retry_send_sms(recipient: str, message: str):
    ModemManager.sendSms(recipient, message)

@app.post("/make_call")
async def make_call(call: Call):
    return ModemManager.make_call(call)

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
    return AutoReplyManager.enable_auto_reply()

@app.post("/disable_auto_reply")
async def disable_auto_reply():
    return AutoReplyManager.disable_auto_reply()

@app.post("/delete_all_sms")
async def delete_all_sms_endpoint():
    try:
        sms_indexes = SmsManager.read_all_sms()  # Use the SmsManager to read SMS indexes
        SmsManager.delete_sms_at_indexes(sms_indexes)  # Use the SmsManager to delete SMS messages
        logger.info("All SMS messages deleted")
        return {"message": "All SMS messages deleted"}
    except Exception as e:
        logger.error(f"Failed to delete SMS messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
@app.get("/list_sms")
async def list_sms_endpoint():
    try:
        sms_indexes = SmsManager.read_all_sms()  # Use the SmsManager to list SMS messages
        logger.info("SMS messages listed successfully")
        return {"message": "SMS messages listed"}
    except Exception as e:
        logger.error(f"Failed to list SMS messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enable_auto_answer_calls")
async def enable_auto_answer_calls():
    return ModemManager.enable_auto_answer_calls()

@app.post("/disable_auto_answer_calls")
async def disable_auto_answer_calls():
    return ModemManager.disable_auto_answer_calls()

@staticmethod
def set_api_key(api_key):
    global auto_reply
    auto_reply = GPT4SMSAutoReply(api_key)
    logger.info("API key set")
    return {"message": "API key set"}


@app.post("/process_mms")
async def process_mms():
    try:
        modem_manager = ModemManager.get_modem()  # Get the modem instance
        modem_manager.process_mms_messages()  # Call the process_mms_messages method to process MMS messages
        logger.info("MMS messages processed successfully")
        return {"message": "MMS messages processed"}
    except Exception as e:
        logger.error(f"Failed to process MMS messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))