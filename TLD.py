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

MyPostfix = "ir"
ROOTHOST = Farima
ROOTPort = 12346
IPForAgents = Alireza
PortForAgents = 12348
AuthoritativeHost = Alireza
AuthoritativePort = 12347

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
IPTLDTable = []
IPnamePairs = namedtuple("IPName", "hostname IP expTime")
toRootConnections = []

def set_interval(func, sec):
	def func_wrapper():
		set_interval(func, sec)
		func()
	t = threading.Timer(sec, func_wrapper)
	t.start()
	return t

def Timer():
	def interval_generator():
		print "Checking..."
		for i in range(0, len(toRootConnections)):
			if(toRootConnections[i] >= 5):
				print "thread: " + str(i) + " has more than 5 query per min. new thread created."
				thread.start_new_thread(listenToRoot, ( ))
			toRootConnections[i] = 0
	set_interval(interval_generator, CONST_ONE_MIN)

def cacheTimer():
	def interval_generator():
		toDeleted = []
		for i in range(0, len(IPTLDTable)):
			IPTLDTable[i] = IPTLDTable[i]._replace(expTime = IPTLDTable[i].expTime - 1)
			if(IPTLDTable[i].expTime <= 0):
				print "Domain: " + IPTLDTable[i].hostname + " with IP: " + IPTLDTable[i].IP + " is deleted."
				toDeleted.append(i)
		for i in range(0, len(toDeleted)):
			IPTLDTable.pop(toDeleted[i])
		
	set_interval(interval_generator, CONST_ONE_SEC)

def findPostfixIndex(name):
	postfix = name[::-1].split(".", 2)[1][::-1] + "." +  name[::-1].split(".", 2)[0][::-1]
	for x in range(0, len(Connections['Postfixes'])):
		if(Connections['Postfixes'][x] == postfix):
			return x
	return -1

def addDomain(Domain, IP, ExpTime):
	for i in range(0, len(IPTLDTable)):
		if(IPTLDTable[i].hostname == Domain):
			IPTLDTable[i] = IPTLDTable[i]._replace(expTime = ExpTime)
			return -1
	x = IPnamePairs(Domain, IP, ExpTime)
	print "Domain with name: " + Domain + " and IP: " + IP + " and ExpTime: " + str(ExpTime) + " is added!"
	IPTLDTable.append(x)
	return 0

def updateDataBase(TLD_Conn, IPForAgents, PortForAgents, postfix):
	Connections['IPs'].append(IPForAgents)
	Connections['PORTs'].append(PortForAgents)
	Connections['Sockets'].append(TLD_Conn)
	Connections['Postfixes'].append(postfix)

def connect_to_Root(host, port):
    s = socket.socket()
    print "Connecting to root"
    s.connect((host, port))
    print "Connected to root"
    return s

def removeMsg(idx):
	Messages['msgIDs'].pop(idx)
	Messages['Sockets'].pop(idx)

def listenToCurrentAuthoritative(AuthoritativeConn):
	received = AuthoritativeConn.recv(1024)
	message = json.loads(received)
	updateDataBase(AuthoritativeConn, message['IPForAgents'], message['PortForAgents'], message['Postfix'])
	print 'Authoritative Connected with IPForAgents: ' + message['IPForAgents'] + ', PortForAgents' + str(message['PortForAgents']) + " Postfix: " + message['Postfix']
	while True:
		recvd = AuthoritativeConn.recv(1024)
		if(len(recvd) == 0):
			return -1
		recursiveMsg = json.loads(recvd)
		if(recursiveMsg['IPFound'] == "True"):
			addDomain(recursiveMsg['DomainName'], recursiveMsg['IP'], CONST_EXPIRETIME)
		for x in range(0, len(Messages['Sockets'])):
			if(Messages['msgIDs'][x] == recursiveMsg['Identification']):
				Messages['Sockets'][x].send(recvd)
				removeMsg(x)

def readMessage(s, incorrect):
    try:
        received = s.recv(2048)
        return json.loads(received), True
    except:
        return incorrect, False

def listenToRoot():
	myNumber = len(toRootConnections)
	toRootConnections.append(0)
	MSGToRoot = {
		'IPForAgents': "",
		'PortForAgents':[],
		'Postfix': ""
	}
	MSGToRoot['IPForAgents'] = IPForAgents
	MSGToRoot['PortForAgents'] = PortForAgents
	MSGToRoot['Postfix'] = MyPostfix
	RootSocket = connect_to_Root(ROOTHOST, ROOTPort)
	RootSocket.send(json.dumps(MSGToRoot))
	while True:
		message, correct = readMessage(RootSocket, None)
		if correct:
			print "New message from root. TLD #" + str(myNumber) + ": " + json.dumps(message)
			toRootConnections[myNumber] += 1 
			for idx in range(0, len(IPTLDTable)):
				if(message['DomainName'] == IPTLDTable[idx].hostname and IPTLDTable[idx].expTime >= 0):
					message['QorR'] = "Reply" #!!! mishe taghir dadesh
					message['IPFound'] = "True"
					message['IP'] = IPTLDTable[idx].IP
					RootSocket.send(json.dumps(message))
			if(message['IPFound'] == "False"):
				tld = findPostfixIndex(message['DomainName'])
				if(tld == -1):
					message['IPFound'] = "False"										
					message['IPForSearch'] = "NOTFOUND"
					RootSocket.send(json.dumps(message))
				else:
					Messages['msgIDs'].append(message['Identification'])
					Messages['Sockets'].append(RootSocket)
					Connections['Sockets'][tld].send(json.dumps(message))
					print "sent message to Authoritative: " + json.dumps(message)

def listenToCurrentAgent(AgentConn):
	while True:
		message, correct = readMessage(AgentConn, None)
		if correct:
			for idx in range(0, len(IPTLDTable)):
				if(message['DomainName'] == IPTLDTable[idx].hostname):
					message['QorR'] = "Reply" #!!! mishe taghir dadesh
					message['IPFound'] = "True"
					message['IP'] = IPTLDTable[idx].IP
					AgentConn.send(json.dumps(message))
			if(message['IPFound'] == "False"):
				tld = findPostfixIndex(message['DomainName'])
				if(tld == -1):
					message['IPFound'] = "False"										
					message['IPForSearch'] = "NOTFOUND"
					AgentConn.send(json.dumps(message))
				else:
					message['IPForSearch'] = Connections['IPs'][tld]
					message['PORTForSearch'] = Connections['PORTs'][tld]
					AgentConn.send(json.dumps(message))

def listenToAgents(AgentsSocket):
	print "listening to Agents..."
	for i in range(0 , 5):
		AgentConn, addr = AgentsSocket.accept()
		print 'Agent Connected with ' + addr[0] + ':' + str(addr[1])	
		thread.start_new_thread(listenToCurrentAgent, (AgentConn, ))

MyPostfix = raw_input('Please Insert This TLD Postfix:')
ROOTHOST = raw_input('Please Insert Root Host:')
ROOTPort = int(raw_input('Please Insert Root Port:'))
IPForAgents = raw_input('Please Insert Agents Host:')
PortForAgents = int(raw_input('Please Insert Agents Port:'))
AuthoritativeHost = raw_input('Please Insert Authoritatives Host:')
AuthoritativePort = int(raw_input('Please Insert Authoritatives Port:'))

with open('initial_' + MyPostfix) as f:
  lines = f.readlines()
  for i in range(0, len(lines)):
    addDomain(lines[i].split(" ")[0], lines[i].split(" ")[1], int(lines[i].split(" ")[2][:-1]))

AuthoritativesSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
AgentsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
AuthoritativesSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
AgentsSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


print 'Socket Authoritatives and Agents created'
try:
    AuthoritativesSocket.bind((AuthoritativeHost, AuthoritativePort))
    AgentsSocket.bind((IPForAgents, PortForAgents))
except socket.error as msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
print 'Sockets bind complete'

AuthoritativesSocket.listen(10)
AgentsSocket.listen(10)
print 'Sockets now listening'
thread.start_new_thread(listenToRoot, ())
thread.start_new_thread(listenToAgents, (AgentsSocket, ))
Timer()
cacheTimer()
for i in range(0 , 5):
	AuthoritativeConn, addr = AuthoritativesSocket.accept()
	thread.start_new_thread(listenToCurrentAuthoritative, (AuthoritativeConn, ))