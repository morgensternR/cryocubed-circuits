from machine import I2C, Pin
#for mem_address in mem_address_list:
#MEssage Description - Each [] = [1 byte]
#[MSB total record 1 size in bytes][LSB total record size in bytes]
#[Length of Record 1 Name][Reocrd 1 name character]*N_characters[length of type stirng][type ins tring]*Ntype_characters[Record 1 data]
#[MSB total record 2 size in bytes][LSB total record size in bytes]
#[Length of Record 2 Name][Reocrd 2 name character]*N_characters[type ins tring]*Ntype_characters[Record 2 data]


class FM24C64B:
    def __init__(self, i2c_object):
        self.addr = 0x50
        self.i2c = i2c_object
        self.mem_address = 0x00 #sets address to be written to
        self.total_bytes_on_record = 0 #keeps track of total bytes written for reading back
        self.record_list = [] #keeps track of each record written len
        self.read()
    def write(self, data_name, data, adc_bits =16 , mem_address = None):
        #self.wipe()
        if mem_address == 0x00:
            overwrite_check = input("You may overwrite previous records. A .wipe() is recommended unless you know exactly what you're replacing, Continue? 'True' or 'False':")
            if overwrite_check =='True':
                pass
            else:
                print("Record not overwritten")
                return
            
        if data > 2**adc_bits:
            raise Exception('data exceeds input paramter adc_bits')
        
        message = self.encode(data_name,data)
        if mem_address == None:
            mem_address = self.mem_address
        if type(message) != bytes:
            print("Message must be in bytes([message])")
        self.i2c.writeto(self.addr, bytes([mem_address>>8, mem_address&0xFF]) + message)
        
        self.record_list.append(len(message))
        self.total_bytes_on_record += len(message)
        #sets new mem address to write the location of the previous bytes written +1
        self.mem_address += len(message)
        
    def read(self, mem_address= 0x00, num_bytes = None):
        self.i2c.writeto(self.addr, bytes([mem_address>>8, mem_address&0xFF]))
        if num_bytes == None:
            data = self.i2c.readfrom(self.addr,2**13)
        else:
            data = self.i2c.readfrom(self.addr,num_bytes)
        list_of_dict = self.decode(data)
        return tuple(list_of_dict)
    
    def wipe(self):
        message = bytearray([0]*2**13)
        self.i2c.writeto(self.addr, bytes([0x00>>8, 0x00&0xFF]) + message)
    def encode(self, data_name, data):
        if type(data_name) != str:
            raise Exception('data_name must be a string!')
        
        record_name_len = bytearray([len(data_name)])
        record_name_byte_array = bytearray(data_name.encode('ascii'))

        record_data_type = bytearray(type(data).__name__.encode('ascii'))
        record_data_type_len = bytearray([len(record_data_type)])

        record_data = data.to_bytes(2, 'big', True)

        record_total = record_name_len + record_name_byte_array + record_data_type_len + record_data_type + record_data
        total_size = len(record_total).to_bytes(2, 'big')
        full_message = total_size + record_total
        return full_message

    def decode(self, message):
        dict_collection = []
        start_index = 0
        record_len = int.from_bytes(message[start_index:2], 'big')
        end_index = record_len + 2
        if record_len == 0:
            print('No Record Lengths Found!')
            pass
        while record_len != 0:
            

            record_name_len = int.from_bytes(message[start_index+2:start_index + 3], 'big')#+1 location in byte list
            record_name = message[start_index + 3:start_index + 3+record_name_len].decode('ascii')#+1 location in byte list
            record_data_type_len = int.from_bytes(message[start_index + 3+record_name_len:start_index + 3 + record_name_len+1], 'big')
            record_data_type = message[start_index + 3 + record_name_len+1:start_index + 3+record_name_len+1+record_data_type_len].decode('ascii')#+1 location in byte list
            record_data = int.from_bytes(message[start_index + 3+record_name_len+1+record_data_type_len:end_index], 'big', True)
            if record_data > 0x7fff:
                record_data -= 0x10000
            self.record_list.append(message[start_index:end_index])
            dict_collection.append(self.output_to_dict(record_len, record_name, record_data_type, record_data))
        
            start_index = end_index
            record_len = int.from_bytes(message[start_index:start_index + 2], 'big')
            end_index = start_index + record_len + 2
            
            if (end_index - 2) > self.total_bytes_on_record:
                self.total_bytes_on_record = end_index - 2 #End record on last iteration has 0 length so -2 to get to last record. 
        return dict_collection
    
    def output_to_dict(self, record_len, record_name, record_data_type, record_data):
        output = {
        'record_len' : record_len,
        'record_name': record_name,
        'record_data_type': record_data_type,
        'record_data': record_data,
        }
        return output
    
    
    
#For testing purposes
#i2c = I2C(1, scl=Pin(23, Pin.PULL_UP), sda=Pin(22, Pin.PULL_UP),  freq=400000)
#mem_chip = FM24C64B(i2c) 