from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus.transaction import ModbusSocketFramer
import socket
import json
import time
import os
from threading import Thread

tcp_server_host = '127.0.0.1'
tcp_server_port = 8888
tcp_server = None
ue_client = None

modbus_server_host = '127.0.0.1'
modbus_server_port = 502
modbus_client = None

def create_socket():
    global tcp_server
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((tcp_server_host, tcp_server_port))
    tcp_server.listen(10)
    print('Start Listening on ' + tcp_server_host + ' ' + str(tcp_server_port))
    accept()

def accept():
    global tcp_server
    while True:
        connect, address = tcp_server.accept()
        thread = Thread(target=handle,args=(connect, address))
        thread.setDaemon(True)
        thread.start()

def handle(connect, address):
    print(address)
    connection = can_connect(address)
    if connection is not True:
        connect.close()
    global ue_client
    ue_client = connect
    data = None
    while connection:
        try:
            data = connect.recv(65535)
        except Exception as e:
            print(e)
            break
        if len(data) == 0:
            connect.close()
            ue_client = None
            connection = False
    print('close Thread')
    cleanup()
    os._exit(0)

def can_connect(address):
    if address[0] != '127.0.0.1':
        return False
    return True

def create_modbus_client():
    global modbus_client
    modbus_client = ModbusTcpClient(modbus_server_host, modbus_server_port)
    connection = modbus_client.connect()
    if not connection:
        print("無法連線到PLC")
    else:
        print("已連線到PLC")
        request_modbus_data()

def request_modbus_data():
    while True:
        try:
            discrete_inputs = modbus_client.read_discrete_inputs(1024, count=22, slave=1)
            inputs = discrete_inputs.bits
            data = {"data": inputs}
            json_data = json.dumps(data)
            global ue_client
            if ue_client != None:
                ue_client.sendall((str(json_data) + '##').encode('utf-8'))
                time.sleep(0.2)
        except ModbusException as exc:
            print(f"Received ModbusException({exc})")
        if discrete_inputs.isError():
            print(f"Received Modbus library error({discrete_inputs})")


def cleanup():
    print('clean up')
    global modbus_client
    if modbus_client != None:
        modbus_client.close()
    global ue_client
    if ue_client != None:
        ue_client.close()

if __name__ == '__main__':
    thread = Thread(target=create_modbus_client)
    thread.setDaemon(True)
    thread.start()
    create_socket()