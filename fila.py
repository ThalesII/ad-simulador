from collections import defaultdict, deque, namedtuple
import random

class Sample:
	def __init__(self):
		self._num = 0
		self._sum = 0
		self._sumsqr = 0

	def append(self, value):
		self._num += 1
		self._sum += value
		self._sumsqr += value**2

	def average(self):
		return self._sum / self._num

	def variance(self):
		## Conferir fórmula
		return (self._sumsqr - self._sum**2) / (1 - self._num)

class SampleFunction:
	def __init__(self):
		self._tstart = None
		self._area = 0

	def append(self, time, value):
		if self._tstart is None:
			self._tstart = time
			self._tlast = time
			self._value = value
		else:
			self._area += self._value * (time - self._tlast)
			self._tlast = time
			self._value = value

	def average(self):
		return self._area / (self._tlast - self._tstart)

class Customer:
	def __init__(self, tarrival, color):
		self.tarrival = tarrival
		self.color = color

Event = namedtuple('Event', 'time, kind')

class Queue:
	def __init__(self, alpha):
		self._tnow = 0
		self._color = 0
		self._alpha = alpha
		self._queue1 = deque()
		self._queue2 = deque()
		self._events = []

		self.addevent('arrival')

	def newcolor(self):
		self._color += 1

	def clearsamples(self):
		self._samples = defaultdict(Sample)
		self._samplefs = defaultdict(SampleFunction)

	def sampleserver(self):
		ns = len(self._queue1) > 0 or len(self._queue2) > 0
		self._samplefs['ns'].append(self._tnow, ns)

	def samplequeue1(self):
		n1 = len(self._queue1)
		self._samplefs['nq1'].append(self._tnow, max(0, n1-1))

	def samplequeue2(self):
		n2 = len(self._queue2)
		self._samplefs['nq2'].append(self._tnow, max(0, n2-1))

	def sampleall(self):
		self.sampleserver()
		self.samplequeue1()
		self.samplequeue2()

	def samplecustomer(self, customer):
		t1 = customer.tendofserv1 - customer.tarrival
		self._samples['t1'].append(t1)
		t2 = customer.tendofserv2 - customer.tendofserv1
		self._samples['t2'].append(t2)

	def addevent(self, kind):
		if kind == 'arrival':
			time = self._tnow + random.expovariate(self._alpha)
		if kind == 'endofserv1' or kind == 'endofserv2':
			time = self._tnow + random.expovariate(1)
		event = Event(time, kind)
		self._events.append(event)

	def rmevent(self, kind):
		for event in self._events:
			if event.kind == kind:
				self._events.remove(event)
				break
		else:
			# ValueError?
			pass

	def nextevent(self):
		event = min(self._events)
		self._events.remove(event)
		return event

	def statistics(self):
		stats = {}
		for key, sample in self._samples.items():
			ekey = 'E[' + key + ']'
			stats[ekey] = sample.average()
			vkey = 'V(' + key + ')'
			stats[vkey] = sample.variance()
		for key, samplef in self._samplefs.items():
			ekey = 'E[' + key + ']'
			stats[ekey] = samplef.average()
		return stats

	def simround(self, n):
		self.clearsamples()
		self.sampleall()
		self.newcolor()

		while n > 0:
			time, kind = self.nextevent()
			self._tnow = time
			if kind == 'arrival':
				self.arrival()
			if kind == 'endofserv1':
				self.endofserv1()
			if kind == 'endofserv2':
				self.endofserv2()
				n -= 1

		self.sampleall()
		return self.statistics()

	def arrival(self):
		customer = Customer(self._tnow, self._color)
		self._queue1.appendleft(customer)
		self.addevent('arrival')
		if len(self._queue1) == 1:
			self.addevent('endofserv1')
			self.sampleserver()
			if len(self._queue2) > 0:
				self.rmevent('endofserv2')
				self.samplequeue2()
		else:
			self.samplequeue1()

	def endofserv1(self):
		customer = self._queue1.pop()
		customer.tendofserv1 = self._tnow
		self._queue2.appendleft(customer)
		if len(self._queue1) == 0:
			self.addevent('endofserv2')
			self.samplequeue2()
		else:
			self.addevent('endofserv1')
			self.samplequeue1()

	def endofserv2(self):
		customer = self._queue2.pop()
		customer.tendofserv2 = self._tnow
		if customer.color == self._color:
			self.samplecustomer(customer)

		if len(self._queue2) == 0:
			self.sampleserver()
		else:
			self.addevent('endofserv2')
			self.samplequeue2()

queue = Queue(0.4)
for i in range(20):
	stats = queue.simround(5000)
	print('round {}'.format(i+1))
	for key, value in stats.items():
		print('    {} = {:2.3f}'.format(key, value), end=', ')
	print()
