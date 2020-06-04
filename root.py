import json
import socket
import threading
import sys
import thread
import time
from collections import namedtuple
import random
from random import randint

Alireza = "192.168.43.11"
Farima = "192.168.43.58"

CONST_ONE_MIN = 60
CONST_ONE_SEC = 1
CONST_EXPIRETIME = 20

IPForAgents = Farima
PortForAgents = 12345
HOSTforTLDs = Farima
PORTforTLDs = 12346
#database:
Connections = {
	'IPs': [],
	'PORTs': [],
	'Sockets': [],
	'Postfixes': []
}

Messages = {
	'msgIDs': [],
	'Sockets': []
}

IProotTable = []
IPnamePairs = namedtuple("IPName", "hostname IP expTime")

Message = {
	'Identification': [],
	'QorR': "",		#it could be "Query", "Reply"
	'RorI': "",		#it could be "Recursion", "Iterative"
	'AorN': "",		#it could be "Authoritative", "NOT"
	'IPFound': "",	#it could be "True", "False"
	'DomainNAme': "",
	'IP': "",
	'IPForSearch':"", "NOTFOUND"
	'PORTForSearch':""  
}


def set_interval(func, sec):
	def func_wrapper():
		set_interval(func, sec)
		func()
	t = threading.Timer(sec, func_wrapper)
	t.start()
	return t

def cacheTimer():
	def interval_generator():
		toDeleted = []
		for i in range(0, len(IProotTable)):
			IProotTable[i] = IProotTable[i]._replace(expTime = IProotTable[i].expTime - 1)
			if(IProotTable[i].expTime <= 0):
				print "Domain: " + IProotTable[i].hostname + " with IP: " + IProotTable[i].IP + " is deleted."
				toDeleted.append(i)
		for i in range(0, len(toDeleted)):
			IProotTable.pop(toDeleted[i])
	set_interval(interval_generator, CONST_ONE_SEC)


def findPostfixIndex(name):
	postfix = name[::-1].split(".")[0][::-1]
	for x in range(0, len(Connections['Postfixes'])):
		if(Connections['Postfixes'][x] == postfix):
			return x
	return -1

def addDomain(Domain, IP, expTime):
	for i in range(0, len(IProotTable)):
		if(IProotTable[i].hostname == Domain):
			IProotTable[i].expTime = IProotTable[i]._replace(expTime = expTime)
			return -1
	x = IPnamePairs(Domain, IP, expTime)
	IProotTable.append(x)
	print "Domain with name: " + Domain + " and IP: " + IP + " and ExpTime: " + str(expTime) + " is added!"
	return 0

def removeMsg(idx):
	Messages['msgIDs'].pop(idx)
	Messages['Sockets'].pop(idx)

def listenToCurrentTLD(TLD_Conn):
	received = TLD_Conn.recv(1024)
	if(len(received) == 0):
		return -1
	message = json.loads(received)
	print "TLD Connected: IPForAgents: " + message['IPForAgents'] + " PortForAgents: " + str(message['PortForAgents']) + " Postfix: " + message['Postfix']
	updateDataBase(TLD_Conn, message['IPForAgents'], message['PortForAgents'], message['Postfix'])
	while True:
		recvd = TLD_Conn.recv(1024)
		if(len(recvd) == 0):
			return -1;
		recursiveMsg = json.loads(recvd)
		if(recursiveMsg['IPFound'] == "True"):
			addDomain(recursiveMsg['DomainName'], recursiveMsg['IP'], CONST_EXPIRETIME)
		for x in range(0, len(Messages['Sockets'])):
			if(Messages['msgIDs'][x] == recursiveMsg['Identification']):
				Messages['Sockets'][x].send(recvd)
				removeMsg(x)

		

def updateDataBase(TLD_Conn, IPForAgents, PORTforAgents, postfix):
	Connections['IPs'].append(IPForAgents)
	Connections['PORTs'].append(PORTforAgents)
	Connections['Sockets'].append(TLD_Conn)
	Connections['Postfixes'].append(postfix)

	
def readMessage(s, incorrect):
    try:
        received = s.recv(2048)
        if(len(received) == 0):
			return -1
        print received
        return json.loads(received), True
    except:
        return incorrect, False

def ListenToCurrentAgent(Agent_Conn):
	print "listen to current agent"
	while True:
		message, correct = readMessage(Agent_Conn, None)
		if correct:
			for idx in range(0, len(IProotTable)):
				if(message['DomainName'] == IProotTable[idx].hostname and IProotTable[idx].expTime >= 0):
					message['QorR'] = "Reply"
					message['IPFound'] = "True"
					message['IP'] = IProotTable[idx].IP
					Agent_Conn.send(json.dumps(message))
					print "1"
					break
			if(message['IPFound'] == "False"):
				tld = findPostfixIndex(message['DomainName'])
				if(tld == -1):
					message['IPFound'] = "False"										
					message['IPForSearch'] = "NOTFOUND"
					print "2"
					Agent_Conn.send(json.dumps(message))
				elif(message['RorI'] == "Iterative"):
					message['IPForSearch'] = Connections['IPs'][tld]
					message['PORTForSearch'] = Connections['PORTs'][tld]
					print "3"
					Agent_Conn.send(json.dumps(message))
				elif(message['RorI'] == "Recursion"):
					Messages['msgIDs'].append(message['Identification'])
					Messages['Sockets'].append(Agent_Conn)
					print "4" 
					Connections['Sockets'][tld].send(json.dumps(message))

def listenToTLDsSocket(TLDSocket):
	print "Wait for TLDs"
	while True:
		TLD_Conn, address = TLDSocket.accept()
		print 'TLD Connected with ' + address[0] + ':' + str(address[1])	
		thread.start_new_thread(listenToCurrentTLD, (TLD_Conn, ))
    
# IPForAgents = raw_input('Please Insert Agents Host:')
# PortForAgents = int(raw_input('Please Insert Agents Port:'))
# HOSTforTLDs = raw_input('Please Insert TLDs Host:')
# PORTforTLDs = int(raw_input('Please Insert TLD Port:'))

with open('initial_root') as f:
	lines = f.readlines()
	for i in range(0, len(lines)):
		addDomain(lines[i].split(" ")[0], lines[i].split(" ")[1], int(lines[i].split(" ")[2][:-1]))

cacheTimer()

AgentsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
TLDSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
AgentsSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
TLDSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print 'Sockets created'

try:
    AgentsSocket.bind((IPForAgents, PortForAgents))
except socket.error as msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()     
print 'Socket1 bind complete'

try:
    TLDSocket.bind((HOSTforTLDs, PORTforTLDs))
except socket.error as msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()     
print 'Socket2 bind complete'


AgentsSocket.listen(10)
TLDSocket.listen(10)
print 'Sockets now listening'
thread.start_new_thread(listenToTLDsSocket, (TLDSocket, ))
for i in range(0 , 5):
    Agent_Conn, addr = AgentsSocket.accept()
    print 'Connected with ' + addr[0] + ':' + str(addr[1])
    thread.start_new_thread(ListenToCurrentAgent, (Agent_Conn, ))