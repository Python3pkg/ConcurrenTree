''' 

Classes for BCP message processing.

'''

import socket
from threading import Lock, Thread
from time import sleep
from json import decoder.JSONDecoder as Decoder
from json import dumps
from Queue import Queue

import operation

class Peer:
	''' Represents a remote endpoint. '''
	def __init__(self):
		self.selected = None
		self.subscriptions = {}
		self.read = {}
		self.ops = []

class Connection:
	''' A connection between two Peers '''
	def __init__(self, docHandler, authHandler, socket, extensions = {}, log=[]):
		self.docs = docHandler
		self.auth = authHandler
		self.socket = socket
		self.socket.setblocking(False)
		self.extensions = extensions
		self.logtypes = log

		self.buffer = ""
		self.outbuffer = ""
		self.decoder = Decoder()
		self.log = Queue()
		self.here = Peer()
		self.there = Peer()

	def recv(self):
		''' 
			Returns True if there was data to read,
			False if there was a timeout.
		'''
		try:
			self.feed(self.socket.recv(4096))
			return True
		except socket.timeout:
			return False

	def send(self):
		sent = self.socket.send(self.outbuffer)
		self.outbuffer = self.outbuffer[sent:]
		return self.outbuffer != ""

	def exchange(self):
		flag = True
		while flag:
			flag = self.recv() or self.send()

	def feed(self, string=""):
		''' Read a string into the buffer and process it '''
		self.buffer += string
		try:
			obj, length = self.decoder.raw_decode(self.buffer)
			msg, self.buffer = self.buffer[:length], self.buffer[length:]
			self.dedict(obj, msg)
			self.feed()
		except:
			pass

	def extend(self, name, callback):
		self.extensions[name] = callback

	def unextend(self, name):
		del self.extensions[name]

	def push(self, msgtype, **kwargs):
		kwargs['type'] = msgtype
		outbuffer += dumps(kwargs)

	def select(self, docname):
		if self.here.selected != docname:
			self.push("select", docname=docname)

	def dedict(self, obj, objstring):
		''' 
			The part of the Peer class that analyzes the
			remote communication.
		'''
		obt = obj['type']
		if obt in self.logtypes:
			self.log.put((obj, self.there.selected))
		if obt in self.extensions:
			self.extensions[obt](obj)
			return
		if obt=='select':
			self.there.selected = obj['docname']
		elif obt=='op':
			op = operation.Operation(protostring=objstring)
			op.apply(self.docs[self.there.selected])
		elif obt=='ad':
			if not obj['hash'] in self.here.ops:
				self.select(self.there.selected)
				self.push("getop", hash=obj['hash'])
		elif obt=='getop':
			op = self.docs[self.there.selected].operations[obj['hash']]
			self.outbuffer += str(op)
		elif obt=='check':
			pass
		elif obt=='thash':
			pass
		elif obt=='get':
			pass
		elif obt=='era':
			pass
		elif obt=='subscribe':
			if "subtype" not in obj or obj['subtype']=="live":
				# live subscription
				for name in obj['docnames']:
					self.there.subscriptions[name] = ("live")
			elif obj['subtype']=="notify":
				# notify subscription (ad-only)
				for name in obj['docnames']:
					self.there.subscriptions[name] = ("notify")
			elif obj['subtype']=="marked":
				# notify subscription (read/unread)
				for name in obj['docnames']:
					self.there.subscriptions[name] = ("marked", 0) # TODO use tree hash

		elif obt=='unsubscribe':
			if "docnames" in obj and len(obj['docnames']) > 0:
				for name in obj['docnames']:
					del self.there.subscriptions[name]
			else:
				self.there.subscriptions.clear()

class Pool:
	''' A BCP "router" that forwards messages between connections. '''
	def __init__(self, docHandler, authHandler):
		self.lock = Lock()
		self.stoprunning = False
		self.connections = []
		self.docs = docHandler
		self.auth = authHandler

	def connect(self, socket):
		''' Add a connection to the Pool '''
		with self.lock:
			conn = Connection(self.docs, self.auth, socket, log=['op','ad'])
			self.connections.append(conn)
			return conn

	def remove(self, conn):
		''' Remove a connection. May be a socket or a BCP.Connection '''
		with self.lock:
			kill = conn
			for i in self.connections:
				if i.socket==conn:
					kill = i
			self.connections.remove(kill)

	def run(self):
		while True:
			sleep(.001)
			with self.lock:
				for conn in self.connections:
					if self.stoprunning:
						return
					conn.exchange()
					# process connection log
					self.spread(conn)

	def spread(self, conn):
		ads = []
		while not conn.log.empty():
			obj = conn.log.get()
			
		for other in self.others(conn):
			

	def others(self, conn):
		result = self.connections
		result.remove(conn)
		return result

class ClosedError(Exception):
	pass

class ServerPool:
	''' A collection of server objects that provide real
	or virtual peers. '''

	def __init__(self):
		self.servers = []
		self.lock = Lock()
		self.closed = False

	def start(self, cls, *args, **kwargs):
		''' Add a server to the pool '''
		server = cls(*args, **kwargs)
		thread = Thread(target=server.run)
		thread.start()
		with self.lock:
			self.check_closed()
			self.servers.append((server, thread))

	def run(self):
		''' Run the pool, allowing interserver communication '''
		while not self.closed:
			with self.lock():
				pass

	def close(self):
		with self.lock():
			self.check_closed()
			self.closed = True
			for i in self.servers:
				i[0].close()
			for i in self.servers:
				i[1].join()

	def check_closed(self):
		if self.closed:
			raise ClosedError("ServerPool is closed")

class PoolServer:
	''' Base class for ServerPool Servers. '''
	def run(self):
		''' Start the server running '''
		raise NotImplementedError()

	def close(self):
		''' Stop the server, terminating self.run '''
		raise NotImplementedError()