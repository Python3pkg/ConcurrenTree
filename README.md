## SIMPLE VERSION:

[JSON](http://json.org/) is a format that lets you take programming-type objects, like a list or a dictionary, and encode them as text. You can encode pretty much anything as JSON.

MCP is the open standard protocol I'm working on, which allows you to connect to a worldwide network and share document updates. These documents can hold any JSON object, have a permissions system built in, and it's set up so you can't download an out-of-date copy of the document or have "write collisions" (where two people try to write at the same time, so nobody knows what it actually should be).

Orchard is a proof-of-concept MCP node with a friendly web interface. It encrypts all your data when storing it to disk, and part of MCP is that all data going through it is encrypted anyways. There are no central servers, and it's designed so that the network works just as well with just you and your friend, as it does years down the road with thousands of people on it.

The point of it is not so much MCP, though. That's the underlying protocol. The important thing is what you can build *on top* of MCP, like a distributed version of Google Wave, or a software repository that supports live typing for code collaboration in real time. It's even possible to have a P2P image editor made out of nothing but a web page!

## TECHNICAL VERSION:

ConcurrenTree is a concurrency solution that does the heavy lifting for you.
It was originally called OT+, but has diverged so much from OT that the name
was beginning to be deceptive.

Designed for distributed networks where there is no guarantee that Machine A
and Machine B have even vaguely similar pictures of a document, CTree is a new
and revolutionary concurrency model that can resolve just about anything. It
includes formatting standards, a protocol for network sync/introduction, and
some example code showing you how to write clients in Javascript.

Why start from scratch, when there's already OT? Well, nothing's stopping you
from using OT if you have stiff memory constraints, as in theory memory usage
is not CTree's strong suite. However, OT has a lot of conceptual problems: it
forces you to track the state of a server in order to submit customized ops,
it uses complex and arcane algorithms that require advanced theorem proving
programs to test, and there is no standard set of those algorithms (meaning
my OT doesn't speak the same language as your OT unless we spend days of work
minimum making sure our algorithms are functionally equivalent, and when I say
days, I'm assuming each of us have half a dozen well-paid competent workers).

CTrees solve all these problems and more. There is no state-tracking, because
any operation can be safely submitted to any peer. And because of that, there's
no need for obtuse and ill-defined algorithms. And because of that, we've
been able to make a simple system with clearly defined correct ways to process
data, no ambiguity or fuzziness here, making it easy to port the model to other
programming languages without wondering constantly whether you're doing it
right. The right way makes sense, you can trust your gut.

This code is under heavy construction, and it's important to understand what
CTree is and is not, so you don't end up waiting for features that are not
going to be added. For example, authentication. The protocol being designed
for ConcurrenTree includes operation signing but leaves the majority of auth
to the larger project implementing CTree to do stuff. CTree is not so much its
own thing, as it is something that's embedded in other projects as a simple
backend that handles all your network concurrency.

Demo
====

With the most recent library code, you can get started now and see how much
stuff the library just automagically handles for you. You'll need to install
the files by running "install.sh" as root. Then start up two python terminals, and
call them Bridget and Bob. The code is divided into multiple parts, each of
which is sectioned out by who should be calling that part of the code. It is,
however, fully chronological, and should be called in the order it's given.

	### Starting up communication

	# Both

	from ConcurrenTree.model.mcp import engine
	e = engine.Engine()
	g = e.make('hello','goodbye')
	g.host_table
	localip = '127.0.0.1'
	bob = ['udp4', [localip, 3939], "bob"]
	bridget = ['udp4', [localip, 3940], "bridget"]

	# "Bob"
	g.client(bob, ["rotate", 3])

	# "Bridget"
	g.client(bridget, ["rotate", -7])
	g.resolve_set(bob, ["rotate", 3])
	g.hello(bob)
	g.dm(bob, "Hello, Bob!")

	# Bob again
	g.dm(bridget, "Hey there, Bridget :)")

	### Track 1 Ops

	# Both
	helloname = g.mkname(bob, "hello")
	hello = g.document(helloname)
	hw = hello.content

	# Bob
	g.add_participant(helloname, bridget)
	hw["goofy"] = "gorsh"

	# Bridget
	hw
	hello.permissions
	hw["Blabarsylt"] = "Swedish jelly"
	hw["Blabarsylt"] = "Made of blueberries"

	# Bob
	hello.pretty()
	hello.routes_to(bob)

	### RSA

	# Bob

	from ConcurrenTree.util import crypto
	key = crypto.make(['rsa', None]).proto()
	g.resolve_set(bob, key)
	g.hello(bridget)

	# Bridget

	g.dm(bob, "Your RSA works, Bob.")
	from ConcurrenTree.util import crypto
	key = crypto.make(['rsa', None]).proto()
	g.resolve_set(bridget, key)
	g.hello(bob)

	# Bob

	g.dm(bridget, "As does yours. Hooray for bidirectionally encrypted communication!")

Dependencies
============
* python 2.6.6+
* Works with python-gevent, but doesn't need it.
* pycrypto (2.3): https://www.dlitz.net/software/pycrypto/
