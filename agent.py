import json
import socket
import threading
import sys
import thread
import time
import random
from random import randint

Alireza = "192.168.43.11"
Farima = "192.168.43.58"
RootIP = Farima
RootPort = 12345
ClientIP = Alireza
ClientPort = 12344

numberOfCurrentID = 0
numberOfCurrentClientID = 0
Connections = {
	'IP': [],
	'PORT': [],
	'Socket': [],
	'Postfix': []
}

def connect_to_DNS(host, port):
    s = socket.socket()
    s.connect((host, port))
    return s

def listenToClient(ClientSocket, ServerSocket, ClientID):
	Message = {
		'Identification': [],
		'QorR': "",		#it could be "Query", "Reply"
		'RorI': "",		#it could be "Recursion", "Iterative"
		'AorN': "",		#it could be "Authoritative", "NOT"
		'IPFound': "",	#it could be "True", "False"
		'DomainName': "",
		'IP': "",
		'IPForSearch': "",		#if IP wasn't Found, IPForSearch = "NOTFOUND"
		'PORTForSearch': ""
	}
	while(True):
		global numberOfCurrentID
		ClientSocket.send("Please Enter Your Domain: ")
		RecDomain = ClientSocket.recv(1024)
		if(len(RecDomain) == 0):
			print "Connection Lost"
			return -1
		RecDomain = RecDomain[:-2]
		ClientSocket.send("Please Enter 'I' for Iterative model and 'R' for Recursion model: ")
		RecModel = ClientSocket.recv(1024)
		if(len(RecModel) == 0):
			print "Connection Lost"
			return -1
		RecModel = RecModel[:-2]
		print "New Query with Domain:" + RecDomain + " and Model: " + RecModel
		Message['Identification'] = numberOfCurrentID
		Message['QorR'] = "Query"
		Message['IPFound'] = "False"
		if(RecModel == "I"):
			Message['RorI'] = "Iterative"
		else:
			Message['RorI'] = "Recursion"
		Message['DomainName'] = RecDomain
		numberOfCurrentID += 1
		ServerSocket.send(json.dumps(Message))


def listenToDNS(DNSSocket, ClientSocket, ClientID):
	while(True):
		received = DNSSocket.recv(1024)
		print received
		if(len(received) == 0):
			print "Connection Lost"
			return -1
		else:
			Decoded = json.loads(received)
			if(Decoded['IPFound'] == "True"):
				ClientSocket.send("IP for Domain: " + Decoded['DomainName'] + " is: " + Decoded['IP'])
			else:
				if(Decoded['IPForSearch'] == "NOTFOUND"):
					ClientSocket.send("IP for Domain: " + Decoded['DomainName'] + " wasn't Found.")
				else:
					IsSent = False
					for i in range(0,len(Connections['IP'])):
						if(Connections['IP'][i] == Decoded['IPForSearch'] and Connections['PORT'][i] == Decoded['PORTForSearch']):
							IsSent = True
							Connections['Socket'][i].send(received)
							break
					if(IsSent == False):
						Connections['IP'].append(Decoded['IPForSearch'])
						Connections['PORT'].append(Decoded['PORTForSearch'])
						TMPSocket = connect_to_DNS(Decoded['IPForSearch'], Decoded['PORTForSearch'])
						Connections['Socket'].append(TMPSocket)
						print "Connection Creating, IP: " + Decoded['IPForSearch'] + " PORT: " + str(Decoded['PORTForSearch']) + "..."
						thread.start_new_thread(listenToDNS, (TMPSocket ,Client_Conn, ClientID))
						print "Connection is Created"
						TMPSocket.send(received)
						print "Request Sent to DNS"

RootIP = raw_input('Please Insert Root IP:')
RootPort = int(raw_input('Please Insert Root Port:'))
ClientIP = raw_input('Please Insert Agent IP:')
ClientPort = int(raw_input('Please Insert Agent Port:'))

print "hello world"
RootSocket = connect_to_DNS(RootIP, RootPort)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print 'Socket created'

try:
    s.bind((ClientIP, ClientPort))
except socket.error as msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
     
print 'Socket bind complete'
s.listen(10)
print 'Socket now listening'

while True:
    Client_Conn, addr = s.accept()
    print 'User Connected with ' + addr[0] + ':' + str(addr[1])
    thread.start_new_thread(listenToClient, (Client_Conn, RootSocket, numberOfCurrentClientID))
    thread.start_new_thread(listenToDNS, (RootSocket, Client_Conn, numberOfCurrentClientID))
    numberOfCurrentClientID += 1