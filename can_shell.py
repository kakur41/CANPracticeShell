#!/usr/bin/env python3

import cmd
import pika
import hashlib
import random
import time
import sys
import threading

class ECU:
    def __init__(self, exchange_name):
        self.exchange_name = exchange_name
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='fanout')

    def send_periodic(self, message, interval):
        def periodic_task():
            while True:
                self.channel.basic_publish(exchange=self.exchange_name, routing_key='', body=message)
                # print(f"Sent: {message}")
                time.sleep(interval/1000)
        
        threading.Thread(target=periodic_task).start()

    def send_event(self, message):
        self.channel.basic_publish(exchange=self.exchange_name, routing_key='', body=message)
        # print(f"Sent: {message}")

class CANShell(cmd.Cmd):

    def __init__(self):
        super().__init__()
        self.exchange_name = self.get_exchange_name()

    def get_exchange_name(self):
        user_input = input("Enter an arbitrary string for identification: ")
        hashed_value = hashlib.md5(user_input.encode()).hexdigest()
        # print(f"Using : {hashed_value}")
        print(f"Interface : vcan0")
        return hashed_value

    prompt = '(CAN) '

    def do_cansend(self, args):
        """Send a CAN message.
    Usage: cansend vcan0 CAN_ID#DATA
    Example: cansend vcan0 111#1122334455667788
        """
        if args == "-h":
            print(self.do_cansend.__doc__)
            return
        try:
            args_list = args.split()
            if not args_list or args_list[0] != 'vcan0':
                print("No such device")
                return
            _, message = args.split(maxsplit=1)
        except ValueError:
            print("Invalid arguments. Type 'cansend -h' for help.")
            return
        can_id, data = message.split('#')
        if int(can_id) < 0 or 0x1ff < int(can_id) :
            print("wrong canid")
            return
        if len(data) % 2 != 0:
            print("wrong data")
            return
        message = f"TX#{can_id}#{data}"
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.exchange_declare(exchange=self.exchange_name, exchange_type='fanout')
        channel.basic_publish(exchange=self.exchange_name, routing_key='', body=message)
        connection.close()
        # print(f"Sent: {message}")

    def do_cangen(self, args):
        """Generate and send random or incremental CAN messages.
    Usage:
        cangen vcan0 [-I (i|r|CAN_ID)] [-D (i|r|DATA)] [-L (i|r|DATA_LENGTH)] [-g (INTERVAL(ms))]
        i: Incremental value
        r: Random value
    Examples:
        cangen vcan0 -I i -D r -L 8 -g 0.5
        cangen vcan0 -I r -D i -L 8 -g 1
        cangen vcan0 -I 123 -D 1122334455667788 -L 8 -g 1
        """
        if args == "-h":
            print(self.do_cangen.__doc__)
            return
        args_list = args.split()
        if not args_list or args_list[0] != 'vcan0':
            print("No such device")
            return
        can_id_arg = 'r' if '-I' not in args_list else args_list[args_list.index('-I') + 1]
        can_data_arg = 'r' if '-D' not in args_list else args_list[args_list.index('-D') + 1]
        data_length_arg = '8' if '-L' not in args_list else args_list[args_list.index('-L') + 1]
        interval = 1000 if '-g' not in args_list else float(args_list[args_list.index('-g') + 1])

        # Initializing can_id_value and can_data_value based on the arguments
        can_id_value = random.randint(0, 0x7FF) if can_id_arg == 'r' else 0
        can_data_value = random.randint(0, 0xFFFFFFFFFFFFFFFF) if can_data_arg == 'r' else 0
        data_length_value = 0  # Initial value for incremental data length

        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.exchange_declare(exchange=self.exchange_name, exchange_type='fanout')

        try:
            while True:
                # Updating data_length_value based on the argument
                if data_length_arg == 'i':
                    data_length_value = (data_length_value + 1) % 9  # Increment and wrap around at 8
                elif data_length_arg == 'r':
                    data_length_value = random.randint(1, 16)  # Random value between 1 and 16
                else:
                    data_length_value = int(data_length_arg)  # Specific value

                # Adjusting data length by padding with zeros or truncating
                adjusted_data_value = (f'{can_data_value:0{data_length_value * 2}x}'[:data_length_value * 2]).zfill(data_length_value * 2)
                if can_id_value < 0 or 0x1ff < can_id_value :
                    print("wrong canid")
                    return
                if len(adjusted_data_value) % 2 != 0:
                    print("wrong data")
                    return
                message = f"TX#{hex(can_id_value)[2:]}#{adjusted_data_value}"
                channel.basic_publish(exchange=self.exchange_name, routing_key='', body=message)
                # print(f"Sent: {message}")

                # Updating can_id_value and can_data_value for the next iteration
                if can_id_arg == 'i':
                    can_id_value = (can_id_value + 1) & 0x7FF
                elif can_id_arg == 'r':
                    can_id_value = random.randint(0, 0x7FF)

                if can_data_arg == 'i':
                    can_data_value = (can_data_value + 1) & 0xFFFFFFFFFFFFFFFF
                elif can_data_arg == 'r':
                    can_data_value = random.randint(0, 0xFFFFFFFFFFFFFFFF)

                time.sleep(interval / 1000)  # User specified interval (in milliseconds)
        except KeyboardInterrupt:
            connection.close()


    def do_candump(self, args):
        """Receive and display CAN messages.
    Usage: candump vcan0 [-a] [-x]
        """
        ecu = ECU(self.exchange_name)
        ###########   custom   ############
        ecu.send_periodic("RX#201#1122334455667788",500)
        ###################################
        if args == "-h":
            print(self.do_candump.__doc__)
            return
        args_list = args.split()
        if not args_list or args_list[0] != 'vcan0':
            print("No such device")
            return
        try:
            interface = args_list.pop(0)
        except IndexError:
            print("Invalid arguments. Type 'candump -h' for help.")
            return

        show_ascii = '-a' in args_list
        show_extended = '-x' in args_list

        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.exchange_declare(exchange=self.exchange_name, exchange_type='fanout')
        result = channel.queue_declare(queue='', exclusive=False)
        queue_name = result.method.queue
        channel.queue_bind(exchange=self.exchange_name, queue=queue_name)

        def callback(ch, method, properties, body):
            parts = body.decode().split("#")
            tx_info, can_id, can_data = parts if len(parts) == 3 else (None, *parts)
            data_bytes = [can_data[i:i + 2] for i in range(0, len(can_data), 2)]
            formatted_can_id = f"{int(can_id, 16):03X}"
            formatted_data_length = f"[{len(data_bytes)}]"
            formatted_data_bytes = ' '.join(data_bytes)
            if show_ascii:
                formatted_ascii = f"'{''.join([chr(int(byte, 16)) if 32 <= int(byte, 16) <= 126 else '.' for byte in data_bytes])}'"
            else:
                formatted_ascii = ''
            formatted_extended = f'{tx_info} - - ' if show_extended and tx_info else ''
            output_message = f"{interface}  {formatted_extended}{formatted_can_id}  {formatted_data_length}  {formatted_data_bytes}  {formatted_ascii}\n"
            sys.stdout.write(output_message)
            sys.stdout.flush()
            ###########   custom   ############
            if tx_info=="TX" and can_id == "123":
                ecu.send_event("RX#124#456789ABCDEF")
            ###################################

        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True, consumer_tag="")
        
        channel.start_consuming()
        connection.close()

        
    def do_exit(self, args):
        """Exit the shell."""
        return True

if __name__ == '__main__':
    CANShell().cmdloop()
