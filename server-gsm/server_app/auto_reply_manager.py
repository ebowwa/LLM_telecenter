from .auto_reply_module import GPT4SMSAutoReply
import logging

logger = logging.getLogger(__name__)
API_KEY = None
auto_reply = None

class AutoReplyManager:
    @staticmethod
    def set_api_key(api_key):
        global auto_reply
        auto_reply = GPT4SMSAutoReply(api_key)
        logger.info("API key set")
        return {"message": "API key set"}
    
    @staticmethod
    def enable_auto_reply():
        if auto_reply:
            auto_reply.enable_auto_reply()
            return {"message": "Auto reply enabled"}
        else:
            return {"message": "API key not set. Auto reply cannot be enabled."}
    
    @staticmethod
    def disable_auto_reply():
        if auto_reply:
            auto_reply.disable_auto_reply()
            return {"message": "Auto reply disabled"}
        else:
            return {"message": "Auto reply is already disabled."}
