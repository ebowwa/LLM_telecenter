from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import TimeoutException, InvalidStateException
from fastapi import HTTPException
from retrying import retry
from .auto_reply_module import GPT4SMSAutoReply
import logging
from .sms_manager import SmsManager

# Import the necessary functions
from .mms_manager import download_multimedia_content, store_multimedia_content

logger = logging.getLogger(__name__)
auto_reply = GPT4SMSAutoReply(api_key='YOUR_GPT4_API_KEY')  # replace 'YOUR_GPT4_API_KEY' with your actual GPT4 API key
forwarding_number = None  # replace with the forwarding number if needed
api_key = None
auto_answer_calls_enabled = False  # Set default value to False

def handle_incoming_sms(sms):
    logger.info(f"Received SMS from {sms.number}: {sms.text}")

    if auto_reply.auto_reply_enabled:
        response_message = auto_reply.handle_incoming_sms(sms.number, sms.text)
        
        if response_message is not None:
            ModemManager.send_sms(sms.number, response_message)
            logger.info(f"Response SMS sent to {sms.number}: {response_message}")
    else:
        logger.info("Auto-reply is disabled. No response generated.")

def handle_incoming_call(call):
    global forwarding_number, auto_answer_calls_enabled
    logger.info(f"Incoming call from {call.number}")
    if forwarding_number is not None:
        response = ModemManager.write(f'AT+CCFC=1,3,"{forwarding_number}"')
        if "OK" in response:
            logger.info("Call forwarded")
        else:
            logger.error("Failed to forward call")
    elif auto_answer_calls_enabled:
        call.answer()
    else:
        logger.info("Auto-answer calls is disabled. Call not answered.")

class ModemManager:
    modem = None

    @staticmethod
    def init_modem(config):
        try:
            ModemManager.modem = GsmModem(config.port, config.baudrate)
            ModemManager.modem.connect(config.pin)
            ModemManager.modem.smsReceivedCallback = handle_incoming_sms
            ModemManager.modem.incomingCallCallback = handle_incoming_call
            logger.info("Modem initialized and connected")
            return {"message": "Modem initialized and connected"}
        except Exception as e:
            logger.error(f"Failed to initialize and connect modem: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def check_modem_connected():
        if ModemManager.modem is None:
            raise HTTPException(status_code=500, detail="Modem is not connected")

    @staticmethod
    def write(data):
        ModemManager.check_modem_connected()
        # print(f"Sending AT command: {data}")  # Added print statement for each AT command
        response = ModemManager.modem.write(data)
        return response


    @staticmethod
    def get_apn():
        try:
            ModemManager.check_modem_connected()
            response = ModemManager.write('AT+CGDCONT?')
            return {"response": response}
        except Exception as e:
            logger.error(f"Failed to get APN: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def set_apn(apn_config):
        try:
            ModemManager.check_modem_connected()
            ModemManager.write(f'AT+CGDCONT=1,"IP","{apn_config.apn}"')
            logger.info("APN set")
            return {"message": "APN set"}
        except Exception as e:
            logger.error(f"Failed to set APN: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def send_sms(recipient, message):
        try:
            ModemManager.check_modem_connected()
            retry_send_sms(recipient, message)
            logger.info("SMS sent")
            return {"message": "SMS sent"}
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def make_call(recipient):
        try:
            ModemManager.check_modem_connected()
            ModemManager.modem.dial(recipient)
            logger.info("Call made")
            return {"message": "Call made"}
        except Exception as e:
            logger.error(f"Failed to make call: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def enable_auto_answer_calls():
        global auto_answer_calls_enabled
        auto_answer_calls_enabled = True
        logger.info("Auto-answer calls enabled")
        return {"message": "Auto-answer calls enabled"}

    @staticmethod
    def disable_auto_answer_calls():
        global auto_answer_calls_enabled
        auto_answer_calls_enabled = False
        logger.info("Auto-answer calls disabled")
        return {"message": "Auto-answer calls disabled"}

    @staticmethod
    def list_messages(delete=False, memory=None):
        sms_manager = SmsManager(ModemManager.modem)
        sms_manager.list_messages(delete, memory)

    @staticmethod
    def delete_messages(del_flag=4, memory=None):
        sms_manager = SmsManager(ModemManager.modem)
        sms_manager.delete_messages(del_flag, memory)

    @staticmethod
    def process_mms_messages():
        messages = ModemManager.modem.send_at_command('AT+CMGL="ALL"')

        for message in messages:
            if "MMS" in message:
                index = message.split(",")[0].split(":")[1]
                status = message.split(",")[1].replace("\"", "")
                sender = message.split(",")[2].replace("\"", "")
                content = message.split("\\n")[1]

                if "http://" in content or "https://" in content:
                    url = content.split(" ")[-1]
                    multimedia_content = download_multimedia_content(url)
                else:
                    multimedia_content = content

                if multimedia_content is not None:
                    file_path = store_multimedia_content(multimedia_content)
                    logger.info(f"Index: {index}, Status: {status}, Sender: {sender}, Content: {content}, File Path: {file_path}")
                else:
                    logger.error(f"Failed to download or extract multimedia content for message index {index}.")

    @staticmethod
    def send_at_command(command, expected_response=None):
        response = ModemManager.write(command)
        if expected_response is not None and expected_response not in response:
            raise Exception(f"Expected response '{expected_response}' not found in '{response}'")
        return response

    def establish_ppp_connection(self):
        self.send_at_command('AT+CGDCONT?')
        self.send_at_command('AT+CGATT=1')
        self.send_at_command('AT+CGDATA=?')
        self.send_at_command('AT+CGACT=1')

    def configure_mms(self):
        self.send_at_command('AT+CMMSINIT')
        self.send_at_command('AT+CMMSCURL="some.url.com"')
        self.send_at_command('AT+CMMSCID=1')
        self.send_at_command('AT+CMMSPROTO="1.1.1.1",8080')
        self.send_at_command('AT+SAPBR=3,1,"Contype","GPRS"')
        self.send_at_command('AT+SAPBR=3,1,"APN","foobar"')
        self.send_at_command('AT+SAPBR=1,1')

    def send_mms_message(self, recipient, content, content_type, size, latency):
        self.enter_mms_edit_mode()
        self.download_multimedia_content(content_type, size, latency)
        self.set_recipient(recipient)
        self.view_mms_message_content()
        self.send_mms_message()
        self.exit_mms_edit_mode()

    def enter_mms_edit_mode(self):
        self.send_at_command('AT+CMMSEDIT=1', 'OK')

    def download_multimedia_content(self, content_type, size, latency):
        self.send_at_command(f'AT+CMMSDOWN="{content_type}",{size},{latency}', 'CONNECT')

    def set_recipient(self, recipient_number):
        self.send_at_command(f'AT+CMMSRECP="{recipient_number}"', 'OK')

    def view_mms_message_content(self):
        return self.send_at_command('AT+CMMSVIEW')

    def send_mms_message(self):
        self.send_at_command('AT+CMMSSEND', 'OK')

    def exit_mms_edit_mode(self):
        self.send_at_command('AT+CMMSEDIT=0', 'OK')

@retry(stop_max_attempt_number=3, wait_fixed=2000)
async def retry_send_sms(recipient, message):
    ModemManager.send_sms(recipient, message)
