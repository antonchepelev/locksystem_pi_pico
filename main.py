import time
from machine import I2C, Pin, SoftSPI
from modules.I2C_LCD import I2CLcd
from modules.keypad import KeyPad
from modules.mfrc522 import MFRC522
from utils.password_utils import hash_password, password_exists
from utils.activity_logger import activity_logger

class LockSystem:

    def __init__(self):
        self.i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
        self.devices = self.i2c.scan()
        self.lock = Pin(16,Pin.OUT)
        self.keyPad = KeyPad(13, 12, 11, 10, 9, 8, 7, 6)
        self.lcd = I2CLcd(self.i2c, self.devices[0], 2, 16)
        self.password_storage = "password.txt"
        self.welcome_string = "Press any key to unlock"
        self.options_menu = "Please press on the letters to see the individual options"
        self.rfid_sck = Pin(2, Pin.OUT)
        self.rfid_copi = Pin(3, Pin.OUT) # Controller out, peripheral in
        self.rfid_cipo = Pin(4, Pin.OUT) # Controller in, peripheral out
        self.rfid_spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=self.rfid_sck, mosi=self.rfid_copi, miso=self.rfid_cipo)
        self.rfid_sda = Pin(5, Pin.OUT)
        self.rfid_reader = MFRC522(self.rfid_spi, self.rfid_sda)
        self.rfid_key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    def string_looper(self, string):
        self.lock.value(1)
        while True:
            for start_index in range(len(string)):
                end_index = start_index + 16
                current_chunk = string[start_index:end_index]

                current_chunk_2 = string[end_index:end_index + 16]
                self.lcd.clear()

                self.lcd.move_to(0, 0)
                self.lcd.putstr(current_chunk)

                self.lcd.move_to(0, 1)
                self.lcd.putstr(current_chunk_2)
                time.sleep(.5)

                keyvalue = self.keyPad.scan()

                if keyvalue is not None:
                    self.lcd.clear()
                    return
                
    def display_text(self,line_1,line_2,blink):
        
        if isinstance(line_1, str) and isinstance(line_2, str) and isinstance(blink, bool):
            self.lcd.clear()
            self.lcd.move_to(0, 0)
            self.lcd.putstr(line_1)

            self.lcd.move_to(0, 1)
            self.lcd.putstr(line_2)
            
            if blink:
                self.lcd.blink_cursor_on()
            else:
                self.lcd.blink_cursor_off()
                self.lcd.hide_cursor()
        else:
            raise ValueError("line_1 and line_2 must be strings, and blink must be a boolean")

        

    
    def key(self):
        keyvalue = self.keyPad.scan()
        if keyvalue == "*":
            self.lcd.clear()
            self.lcd.putstr("Goodbye")
            time.sleep(1)
            self.lcd.clear()
            self.welcome = True
            self.string_looper(self.welcome_string)
        if keyvalue == "#":
            self.string_looper(self.options_menu)
        elif keyvalue == "A":
            self.lcd.clear()
            self.input_password()
        elif keyvalue == "B":
            self.lcd.clear()
            self.check_lock()
        elif keyvalue == "C":
            self.lcd.clear()
            self.create_password()
        elif keyvalue == "D":
            self.lcd.clear()
            self.read_rfid_card()
        elif keyvalue is not None:
            self.lcd.putstr(keyvalue)
            time.sleep_ms(300)
            return keyvalue

    def run(self):
        while True:
            self.key()

    def input_password(self,rfid=False):
        if password_exists(self.password_storage):
            self.display_text("Password:", "", True)
            password_input = self.get_password_input()

            if not self.check_password(password_input):
                self.display_text("Incorrect", "", False)
                time.sleep(2)
                self.input_password()
            elif rfid == True and self.check_password(password_input):
                return str(hash_password(password_input))
                
            elif self.check_password(password_input) and rfid == False:
                self.access_granted()
        else:
            self.create_password()

    def get_password_input(self):
        password_input = ""
        disallowed_keys = ["A", "B", "C", "D", "*"]
        while len(password_input) < 5:
            keyvalue = self.keyPad.scan()
            if keyvalue == "#":
                break
            elif keyvalue is not None and keyvalue not in disallowed_keys:
                password_input += keyvalue
                self.lcd.putstr("*")
                time.sleep_ms(200)
        return password_input

    def check_password(self, password_input):
        with open(self.password_storage, "r") as file:
            password = file.readline()
        return str(hash_password(password_input)) == password

    def access_granted(self):
        self.display_text("Access Granted", "Unlocked", False)
        self.lock.value(0)
        activity_logger("Unlocked")
        time.sleep(2)

    def create_password(self):
        if password_exists(self.password_storage):
            self.display_text("Password on file. Please reset.", "", False)
            time.sleep(2)
            self.reset_password()
        else:
            self.display_text("Create Password:", "", True)
            password_input = self.get_password_input()
            self.save_password(password_input)
            self.display_text("Password Created", "", False)
            activity_logger("Password Created")
            time.sleep(2)
            self.string_looper(self.welcome_string)

    def reset_password(self):
        self.display_text("Old Password:", "", True)
        password_input = self.get_password_input()
        if not self.check_password(password_input):
            self.reset_password()
        with open(self.password_storage, "w") as file:
            file.write("")
        activity_logger("Password Reset")
        self.create_password()

    def save_password(self, password_input):
        with open(self.password_storage, "w") as file:
            file.write(str(hash_password(password_input)))
    
    def check_lock(self):
        
        if not self.lock.value() == 1:
            self.lock.value(1)
            self.display_text("Locked", "", False)
            activity_logger("Locked")
        else:
            self.lcd.putstr("Already Locked")
    
    
    def rfid(self):
        pass
        
        
     
    def read_rfid_card(self):
        card_data = ""
        while True:
            try:
                (status, tag_type) = self.rfid_reader.request(self.rfid_reader.CARD_REQIDL)#Read the card type number
                if status == self.rfid_reader.OK:
                    print('Find the card!')
                    (status, raw_uid) = self.rfid_reader.anticoll()#Reads the card serial number of the selected card
                    if status == self.rfid_reader.OK:
                        print('New Card Detected')
                        
                        if self.rfid_reader.select_tag(raw_uid) == self.rfid_reader.OK:
                            with open(self.password_storage, "r") as file:
                                password = file.readline()
                                
                            card_info = self.rfid_reader.Read_Data(self.rfid_key, raw_uid).replace('\x00', '')
                                
                            
                            print(f"password: {repr(password)}")
                            print(f"card: {repr(card_info)}")
                            
                            
                            count = ""
                            for i in card_info:
                                count += i
                                
                            print(len(count))
                            
                            time.sleep(1)
                            if password == card_info:
                                print("YOOOO")
                                
          
                        
                
            except KeyboardInterrupt:
                break
            
        
            
       
             
    #possibly make a function that writes to card when password changed
            
    
    def add_rfid_card(self):
       
        while True:
            (status, tag_type) = self.rfid_reader.request(self.rfid_reader.CARD_REQIDL)#Read the card type number
            if status == self.rfid_reader.OK:
                print('Find the card!')
                (status, raw_uid) = self.rfid_reader.anticoll()#Reads the card serial number of the selected card
                if status == self.rfid_reader.OK:
                    print('New Card Detected')
                    print('  - Tag Type: 0x%02x' % tag_type)
                    print('  - uid: 0x%02x%02x%02x%02x' % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                    print('')
                    if self.rfid_reader.select_tag(raw_uid) == self.rfid_reader.OK:
                        data = self.input_password(rfid=True)          
                        self.rfid_reader.Write_Data(self.rfid_key, raw_uid, data)
                        
        
        
        
if __name__ == "__main__":
    lock_system = LockSystem()
    lock_system.string_looper(lock_system.welcome_string)
    lock_system.run()



