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

MyPostfix = "ac.ir"
TLDHost = Alireza
TLDPort = 12347
AgentsHost = Farima
AgentsPORT = 12349

num_of_requests_processing = 0

numberOfCurrentID = 0
 
#database:
MSGToRoot = {
  'IPForAgents': "",
  'PortForAgents': [],
  'Postfix': ""
}

Connections = {
  'IPs': [],
  'PORTs': [],
  'Sockets': [],
  'Postfixs': []
}
CONST_TIME_PRIORITY = ["Midnight", "Morning", "Noon", "Afternoon", "Night"]
IPAuthTable = []
IPnamePairs = namedtuple("IPName", "hostname IP Time")
# IPnamePairs = {
#   'hostname': [],
#   'IP': []  
# }
Message = {
  'Identification': [],
  'QorR': "",   #it could be "Query", "Reply"
  'RorI': "",   #it could be "Recursion", "Iterative"
  'AorN': "",   #it could be "Authoritative", "NOT"
  'IPFound': "",  #it could be "True", "False"
  'DomainNAme': "",
  'IPorPORT': "",
  'IPForSearch':"" 
}
# Massage = namedtuple("Massage", "Identification QorR RorI")

CONST_TIME_BETWEEN_DAYS = 60
def set_interval(func, sec):
  def func_wrapper():
    set_interval(func, sec)
    func()
  t = threading.Timer(sec, func_wrapper)
  t.start()
  return t

def findNextTime(currentTime):
  if(currentTime == "Night"):
    return "Midnight"
  else:
    return CONST_TIME_PRIORITY[CONST_TIME_PRIORITY.index(currentTime) + 1]

def DayUpdater():
  def interval_generator():
    for i in range(0, len(IPAuthTable)):
      IPAuthTable[i] = IPAuthTable[i]._replace(Time = findNextTime(IPAuthTable[i].Time))
      print "Domain: " + IPAuthTable[i].hostname + " IP: " + IPAuthTable[i].IP + " Time: " + IPAuthTable[i].Time
  set_interval(interval_generator, CONST_TIME_BETWEEN_DAYS)



def isDomain(msg):
  for i in range(0, len(IPAuthTable)):
    if(IPAuthTable[i].hostname == msg['DomainName']):
      return i
  return -1


def listenToTLD(TLD_Conn):
  MSGToTLD = {
    'IPForAgents': "",
    'PortForAgents': [],
    'Postfix': ""
  }
  ##give TLD my informantion:
  MSGToTLD['IPForAgents'] = AgentsHost
  MSGToTLD['PortForAgents'] = AgentsPORT
  MSGToTLD['Postfix'] = MyPostfix
  TLD_Conn.send(json.dumps(MSGToTLD))
  while True:
    message, correct = readMessage(TLD_Conn, None)
    if correct:
      MSGTime = 5
      message['QorR'] = "Reply"
      for idx in range(0, len(IPAuthTable)):
        if(message['DomainName'] == IPAuthTable[idx].hostname and CONST_TIME_PRIORITY.index(IPAuthTable[idx].Time) < MSGTime):
          message['IPFound'] = "True"
          message['IP'] = IPAuthTable[idx].IP
          MSGTime = CONST_TIME_PRIORITY.index(IPAuthTable[idx].Time)

      if(message['IPFound'] == "True"):
        TLD_Conn.send(json.dumps(message))
      else:                   
          message['IPForSearch'] = "NOTFOUND"
          TLD_Conn.send(json.dumps(message))    

def updateDataBase(TLD_Conn, IPForAgents, PORTforAgents, postfix):
  Connections['IPs'].append(IPForAgents)
  Connections['PORTs'].append(PORTforAgents)
  Connections['Sockets'].append(TLD_Conn)
  Connections['Postfixes'].append(postfix)

  
def readMessage(s, incorrect):
    try:
        received = s.recv(2048)
        return json.loads(received), True
    except:
        return incorrect, False

def listenToCurrentAgent(agentConn):
  print "Listen to current Agent..."
  while True:
    message, correct = readMessage(agentConn, None)
    print message
    if correct:
      MSGTime = 5
      message['QorR'] = "Reply" 
      for idx in range(0, len(IPAuthTable)):
        if(message['DomainName'] == IPAuthTable[idx].hostname and CONST_TIME_PRIORITY.index(IPAuthTable[idx].Time) < MSGTime):
          message['IPFound'] = "True"
          message['IP'] = IPAuthTable[idx].IP
          MSGTime = CONST_TIME_PRIORITY.index(IPAuthTable[idx].Time)

      if(message['IPFound'] == "True"):
        agentConn.send(json.dumps(message))
      else:                   
          message['IPForSearch'] = "NOTFOUND"
          agentConn.send(json.dumps(message))

def isTimeLegal(CurrentTime):
  if(CurrentTime == "Midnight" or CurrentTime == "Morning" or CurrentTime == "Noon" or CurrentTime == "Afternoon" or CurrentTime == "Night"):
    return True
  return False

def DomainReciever():
  while(True):
    DomainIP = raw_input('Please Insert Domain IP Time:')
    if(len(DomainIP.split(" ")) != 3):
      print "Please use this way: Domain IP Time"
      print "Time Can be Midnight, Morning, Noon, Afternoon, Night"
    elif(isTimeLegal(DomainIP.split(" ")[2]) == False):
      print "Time is not Legal"
    else:
      Domain = DomainIP.split(" ")[0]
      IP = DomainIP.split(" ")[1]
      Time = DomainIP.split(" ")[2]
      subDomain = Domain[::-1].split(".", 2)[1][::-1] + "." +  Domain[::-1].split(".", 2)[0][::-1]
      if(subDomain != MyPostfix):
        print "We only support ." + MyPostfix + " Domains, NOT ." + subDomain
      else:
        x = IPnamePairs(Domain, IP, Time)
        IPAuthTable.append(x)
        print "Domain: " + Domain + " With IP: " + IP + " With Time: " + Time + " is Added"

def connect_to_TLD(host, port):
    s = socket.socket()
    s.connect((host, port))
    return s  

with open('initial_' + MyPostfix) as f:
  lines = f.readlines()
  for i in range(0, len(lines)):
    x = IPnamePairs(lines[i].split(" ")[0], lines[i].split(" ")[1], lines[i].split(" ")[2][:-1])
    IPAuthTable.append(x)
    print "Domain with name: " + lines[i].split(" ")[0] + " and IP: " + lines[i].split(" ")[1] + " with Time: " + lines[i].split(" ")[2][:-1] + " is added!"

thread.start_new_thread(DomainReciever, ())
agentSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
agentSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#print 'Socket agentSocket created'

MyPostfix = raw_input('Please Insert This AUTHORITATIVE Postfix:')
TLDHost = raw_input('Please Insert TLD IP:')
TLDPort = int(raw_input('Please Insert TLD PORT:'))
AgentsHost = raw_input('Please Insert Agent IP:')
AgentsPORT = int(raw_input('Please Insert Agent Port:'))



TLDSocket = connect_to_TLD(TLDHost, TLDPort)
thread.start_new_thread(listenToTLD, (TLDSocket, ))
#Bind socket 's' to local host and port
try:
    agentSocket.bind((AgentsHost, AgentsPORT))
except socket.error as msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

#Start listening on socket
agentSocket.listen(10)
DayUpdater()
for i in range(0 , 5):
    Agent_Conn, addr = agentSocket.accept()
    print 'Connected with ' + addr[0] + ':' + str(addr[1])
    thread.start_new_thread(listenToCurrentAgent, (Agent_Conn, ))
