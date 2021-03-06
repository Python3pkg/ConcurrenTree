from ejtp.util.crashnicely import Guard
from ejtp.util.hasher import strict
from ConcurrenTree import operation
from .demo import bob, bridget, demo_data
from sys import stderr
import random
import json

class MessageProcessor(object):

	# Convenience accessors

	@property
	def client(self):
		return self.gear.client

	@property
	def hosts(self):
		return self.gear.hosts

	@property
	def interface(self):
		return self.gear.interface

class Writer(MessageProcessor):
	def __init__(self, gear):
		self.gear = gear

	def send(self, target, data, wrap_sender=True):
		data['ackc'] = str(random.randint(0, 2**32))
		self.client.write_json(target, data, wrap_sender)

	# Message creators

	def hello(self, target):
		# Send your EJTP encryption credentials to an interface
		self.send(target,
			{
				'type':'mcp-hello',
				'interface':self.interface,
				'key':self.hosts.crypto_get(self.interface),
			},
			False,
		)

	def error(self, target, code=500, message="", data={}):
		self.send(target, {
			"type":"mcp-error",
			"code":code,
			"msg":message,
			"data":data
		})

	def op_callback(self, target, docname, op_hash, callback):
		'''
		Set up a conditional, self-detaching callback for an expected op msg.
		'''
		if callback:
			def wrapped_callback(grid, label, data):
				if match(data, {
						'type':'mcp-error',
						'code':321,
						'sender':target,
						'data':{
							'res_type':'op',
							'id':op_hash
						}
					}):
					grid.detach()
					grid.detach('recv_op')
					return
				elif match(data, {
   						'type':'mcp-op',
						'docname':docname,
						'sender':target,
					}) and data['op'].hash == op_hash:
					grid.detach()
					grid.detach('recv_error')
					callback(grid, label, data)
			self.gear.evgrid.register('recv_error', wrapped_callback)
			self.gear.evgrid.register('recv_op', wrapped_callback)

	def pull_op(self, target, docname, op_hash, callback=None):
		'''
		Pull one op (shorthand alias to pull_ops, basically)

		>>> gbob, gbrg, helloname, hellobob, hellobrg, hwbob, hwbrg = demo_data()
		>>> ophash = '079eeae801303fd811fe3f443c66528a6add7e42' # Real op
		>>> def callback(grid, label, data):
		...	 print "YES, THIS IS CALLBACK"
		...	 print data['op'].hash
		...	 print data['op'].hash == ophash
		>>> gbob.writer.pull_op(bridget, helloname, ophash, callback)
		YES, THIS IS CALLBACK
		079eeae801303fd811fe3f443c66528a6add7e42
		True
		>>> gbob.writer.pull_op(bridget, helloname, ophash) # Make sure callback is cleared
		'''
		self.op_callback(target, docname, op_hash, callback)
		self.pull_ops(target, docname, [op_hash])

	def pull_ops(self, target, docname, hashes, callback=None):
		'''
		Retrieve one or more operations by instruction hash.

		The callback will be called for every op response where the hash
		is present, so it's 

		>>> gbob, gbrg, helloname, hellobob, hellobrg, hwbob, hwbrg = demo_data()
		>>> ophashes = [
		...    '079eeae801303fd811fe3f443c66528a6add7e42', # Real op
		...    'X79eeae801303fd811fe3f443c66528a6add7e42', # Real op
		... ]

		>>> gbob.writer.pull_op(bridget, helloname, ophashes[0]) # Real op
		>>> gbob.writer.pull_op(bridget, helloname, ophashes[1]) # Fake op
		Error from: [u'udp4', [u'127.0.0.1', 3940], u'bridget'] , code 321
		u'Resource not found'
		{"id":"X79eeae801303fd811fe3f443c66528a6add7e42","res_type":"op"}

		>>> gbob.writer.pull_ops(bridget, helloname, ophashes) # Both
		Error from: [u'udp4', [u'127.0.0.1', 3940], u'bridget'] , code 321
		u'Resource not found'
		{"id":"X79eeae801303fd811fe3f443c66528a6add7e42","res_type":"op"}

		>>> def callback(grid, label, data):
		...    print "hash:", data['op'].hash
		>>> gbob.writer.pull_ops(bridget, helloname, ophashes, callback) # Both 
		hash: 079eeae801303fd811fe3f443c66528a6add7e42
		Error from: [u'udp4', [u'127.0.0.1', 3940], u'bridget'] , code 321
		u'Resource not found'
		{"id":"X79eeae801303fd811fe3f443c66528a6add7e42","res_type":"op"}
		>>> gbob.evgrid['recv_op'] # Ensure that the error clears out the callback
		[]
		'''
		for op_hash in hashes:
			self.op_callback(target, docname, op_hash, callback)
		self.send(target, {
			"type":"mcp-pull-ops",
			"docname": docname,
			"hashes":hashes,
		})

	def op(self, docname, op, targets=[]):
		# Send an operation frame.
		# targets defaults to document.routes_to for every sender.
		proto = op.proto()
		proto['type'] = 'mcp-op'
		proto['docname'] = docname

		targets = targets or self.gear.document(docname).routes_to(self.interface)

		for i in targets:
			self.send(i, proto)

	def pull_index(self, target, docname, callback=None):
		'''
		Retrieve a remote source's personal index for a document.

		>>> gbob, gbrg, helloname, hellobob, hellobrg, hwbob, hwbrg = demo_data()
		>>> def callback(grid, label, data):
		...    hashes = data['hashes']
		...    sorted_keys = hashes.keys()
		...    sorted_keys.sort()
		...    for key in sorted_keys:
		...        print "%s: %r" % (key, hashes[key])
		>>> gbob.writer.pull_index(bridget, helloname)
		>>> gbob.writer.pull_index(bridget, helloname, callback)
		079eeae801303fd811fe3f443c66528a6add7e42: u'\\\\_2^[Z\\\\2Z2*/Z)*_-]+Z*\\\\2./ZZ^*.))1_Z++*)['
		34004f4763524e87cfe4f5b5f915266f80bbbfe7: u'+0_].)]^Z[_1_++)Z/.,-_2*[[^00/0\\\\,*-*.)-+'
		44d0cb0c7e9b77eb053294915fdb031abd98adc5: u'\\\\[../)[_,+2)/\\\\Z)Z)^0/**.Z0_[/[*^[*_]./]\\\\'
		45e9f1b0334e99aac9c012b1cd1e25a2ce18c5d7: u'10)0Z.-.]+*0*\\\\.^\\\\,)//,.,_21-+[[*Z]Z2-\\\\/['
		47b01407c24b8be47fe5df780f4959c01be196ae: u'^_1[,0\\\\2].*_,_Z^2+*]2*-1/0+-1Z,\\\\[[2\\\\Z+0.'
		790742eb7a29172333fe025c2622ea18c5286d68: u'],-^-2,_)]2.[)/\\\\10Z\\\\\\\\-\\\\[2\\\\Z-+ZZZ21*2\\\\0.,'
		9bf7b64433a119b91b8790b3697712db8ee5b090: u'*[\\\\\\\\20\\\\1[\\\\0\\\\Z.2,[0^Z.+-^0^])0Z\\\\[.*^2Z))*'
		bc41162db8b81392569a5bedf52c7414212df665: u'^0**/0.^,0])\\\\_Z^0**0])^\\\\0^_0-000.2--,]\\\\_'
		c5467b8ced86280298b6df359835e23bf9742ca7: u'\\\\1,2^/^[1-.1]),2^,.Z/+0,[],.\\\\^*-)1).)/*1'
		d251f86d43c808ee5cbe8231ca8545419649d7c0: u']^\\\\,\\\\2.0[0^^+Z*]+0*21_1]Z2+-/2Z.^000))+.'
		ed61a0b09322e3b5e0361a015c275f7e46057d52: u',Z[/.1^^.^/]^\\\\0/2221*_0\\\\Z[).^[,/_\\\\\\\\_-,[]'
		>>> gbob.writer.pull_index(bridget, helloname)
	 
		'''
		if callback:
			def wrapped_callback(grid, label, data):
				if data['docname'] == docname and data['sender'] == target:
					grid.detach()
					callback(grid, label, data)
			self.gear.evgrid.register('recv_index', wrapped_callback)
		self.send(target, {
			"type":"mcp-pull-index",
			"docname":docname,
		})

	def index(self, target, docname, hashes):
		self.send(target, {
			"type":"mcp-index",
			"docname":docname,
			"hashes":hashes,
		})

	def pull_snapshot(self, target, docname, callback=None):
		'''
		Retrieve a flattened copy of the document from a remote.

		>>> gbob, gbrg, helloname, hellobob, hellobrg, hwbob, hwbrg = demo_data()
		>>> def callback(grid, label, data):
		...    content = data['content']
		...    keys = content.keys()
		...    keys.sort()
		...    for k in keys:
		...        print k, ":", strict(content[k])
		>>> gbob.writer.pull_snapshot(bridget, helloname)
		>>> gbob.writer.pull_snapshot(bridget, helloname, callback)
		content : {"Blabarsylt":"Made of blueberries","goofy":"gorsh"}
		permissions : {"graph":{"edges":{},"vertices":{}},"read":{"[\\"udp4\\",[\\"127.0.0.1\\",3939],\\"bob\\"]":true,"[\\"udp4\\",[\\"127.0.0.1\\",3940],\\"bridget\\"]":true},"write":{"[\\"udp4\\",[\\"127.0.0.1\\",3939],\\"bob\\"]":true,"[\\"udp4\\",[\\"127.0.0.1\\",3940],\\"bridget\\"]":true}}
		routing : {"[\\"udp4\\",[\\"127.0.0.1\\",3939],\\"bob\\"]":{},"[\\"udp4\\",[\\"127.0.0.1\\",3940],\\"bridget\\"]":{}}
		
		'''
		if callback:
			def wrapped_callback(grid, label, data):
				if data['docname'] == docname and data['sender'] == target:
					grid.detach()
					callback(grid, label, data)
			self.gear.evgrid.register('recv_snapshot', wrapped_callback)
		self.send(target, {
			"type":"mcp-pull-snapshot",
			"docname":docname,
		})

	def snapshot(self, target, docname, snapshot):
		self.send(target, {
			"type":"mcp-snapshot",
			"docname":docname,
			"content":snapshot
		})

	def ack(self, target, codes):
		self.send(target, {
			"type":"mcp-ack",
			"ackr":codes,
		})

class Reader(MessageProcessor):
	def __init__(self, gear):
		self.gear = gear

	def acknowledge(self, content, sender):
		if 'ackc' in content and content['type'] != 'mcp-ack':
			ackc = content['ackc']
			self.gear.writer.ack(sender, [ackc])
			return False
		elif 'ackr' in content and content['type'] == 'mcp-ack':
			return True
		else:
			print("Malformed frame:\n%s" % json.dumps(content, indent=2), file=stderr)

	def read(self, content, sender=None):
		try:
			content = json.loads(content)
		except:
			print("COULD NOT PARSE JSON:")
			print(content)
		t = content['type']
		if self.acknowledge(content, sender): return
		fname = t.replace('-','_')
		if hasattr(self, fname):
			return getattr(self, fname)(content, sender)
		else:
			print("Unknown msg type %r" % t)

	# Message handlers

	def mcp_hello(self, content, sender):
		self.gear.gv.hello(content['interface'], content['key'])

	def mcp_op(self, content, sender):
		docname = content['docname']
		op = operation.Operation(content['instructions'])
		vrequest = self.gear.gv.op(sender, docname, op)
		self.gear.evgrid.happen('recv_op', {
			'type':'mcp-op',
			'docname':docname,
			'op':op,
			'sender':sender,
			'vrequest':vrequest,
		})

	def mcp_pull_index(self, content, sender):
		docname = content['docname']
		doc = self.gear.document(docname)
		result = {}
		for x in doc.applied:
			result[x] = self.client.sign(x)
		self.gear.writer.index(sender, docname, result)

	def mcp_index(self, content, sender):
		content['sender'] = sender
		self.gear.evgrid.happen('recv_index', content)

	def mcp_pull_snapshot(self, content, sender):
		docname = content['docname']
		doc = self.gear.document(docname)
		self.gear.writer.snapshot(sender, docname, doc.flatten())

	def mcp_snapshot(self, content, sender):
		content['sender'] = sender
		self.gear.evgrid.happen('recv_snapshot', content)

	def mcp_pull_ops(self, content, sender):
		docname = content['docname']
		hashes = content['hashes']
		doc = self.gear.document(docname)
		known_ops = doc.private['ops']['known']

		for h in hashes:
			if h in known_ops:
				op_proto = known_ops[h]
				op = operation.Operation(instructions = op_proto['instructions'])
				self.gear.writer.op(docname, op, [sender])
			else:
				self.gear.writer.error(sender,
					code     = 321,
					message  = "Resource not found",
					data     = {
						'res_type': 'op',
						'id':h,
					}
				)

	def mcp_error(self, content, sender):
		print("Error from:", sender, ", code", content["code"])
		print(repr(content['msg']))
		if 'data' in content and content['data']:
			print(strict(content['data']))
		content['sender'] = sender
		self.gear.evgrid.happen('recv_error', content)

def match(d1, d2):
	'''
	Tests if dict d1 matches the template of properties given by d2.

	>>> match({}, {'horse':'feathers'})
	False
	>>> match({'horse':'saddles'}, {'horse':'feathers'})
	False
	>>> match({'horse':'feathers'}, {})
	True
	>>> match({'horse':'feathers'}, {'horse':'feathers'})
	True
	'''
	for key in d2:
		if (not key in d1) or d1[key] != d2[key]:
			d1val = None
			if key in d1:
				d1val = d1[key]
			return False
	return True
