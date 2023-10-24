# sms_manager.py

from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import GsmModemException

class SmsManager:
    def __init__(self, port, baudrate):
        self.modem = GsmModem(port, baudrate)
        self.modem.connect()

    def list_messages(self, delete=False, memory=None):
        try:
            messages = self.modem.listStoredSms(delete=delete, memory=memory)
            if messages:
                print("SMS messages:")
                for msg in messages:
                    print(f"Index: {msg.index}, Status: {msg.status}, Number: {msg.number}, Time: {msg.time}, Message: {msg.text}")
            else:
                print("No SMS messages found.")
        except GsmModemException as e:
            print(f"Failed to list SMS messages: {e}")

    def read_all_sms(self):
        sms_indexes = []
        try:
            sms_list = self.modem.listStoredSms()
            for sms in sms_list:
                print(f"Index: {sms.index}, Sender: {sms.number}, Content: {sms.text}")
                sms_indexes.append(sms.index)
        except Exception as e:
            print(f"An error occurred while reading SMS messages: {e}")
        return sms_indexes

    def delete_sms_at_indexes(self, indexes, del_flag=4, memory=None):
        try:
            for index in indexes:
                try:
                    self.modem.deleteStoredSms(index, delFlag=del_flag, memory=memory)
                    print(f"Deleted message at index {index}")
                except Exception as e:
                    print(f"Failed to delete message at index {index}: {e}")

            print("SMS deletion complete")
        except Exception as e:
            print(f"An error occurred while deleting SMS messages: {e}")

# Example usage
#if __name__ == "__main__":
    #port = "/dev/ttyS0"  # Replace with your serial port
    #baudrate = 115200

    #sms_manager = SmsManager(port, baudrate)

    # List SMS messages
    #sms_manager.list_messages()

    # Read all SMS messages and get their indexes
    #sms_indexes = sms_manager.read_all_sms()

    # Delete the read SMS messages
    #sms_manager.delete_sms_at_indexes(sms_indexes)

    # Do not disconnect if you plan to use the modem for other operations
