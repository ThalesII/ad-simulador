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
		return (self._sumsqr - self.average()**2) / (self._num - 1)

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
	def __init__(self, color):
		self.color = color

Event = namedtuple('Event', 'time, kind')

Service = namedtuple('Service', 'customer, queue')

class Queue:
	def __init__(self, lambd):
		self._tnow = 0
		self._color = 0
		self._lambd = lambd
		self._service = None
		self._queue1 = deque()
		self._queue2 = deque()
		self._events = []

		self._addevent('arrival')

	def _resettime(self):
		for i, event in enumerate(self._events):
			time, kind = event
			self._events[i] = Event(time - self._tnow, kind)
		self._tnow = 0

	def _clearsamples(self):
		self._samples = defaultdict(Sample)
		self._samplefs = defaultdict(SampleFunction)

	def _sampleall(self):
		ns = self._service is not None
		self._samplefs['ns'].append(self._tnow, ns)
		nq1 = len(self._queue1)
		self._samplefs['nq1'].append(self._tnow, nq1)
		nq2 = len(self._queue2)
		self._samplefs['nq2'].append(self._tnow, nq2)

	def _samplecustomer(self, customer):
		t1 = customer.tendofserv1 - customer.tarrival
		self._samples['t1'].append(t1)
		t2 = customer.tendofserv2 - customer.tendofserv1
		self._samples['t2'].append(t2)

	def _addevent(self, kind):
		if kind == 'arrival':
			time = self._tnow + random.expovariate(self._lambd)
		if kind == 'endofserv1' or kind == 'endofserv2':
			time = self._tnow + random.expovariate(1)
		event = Event(time, kind)
		self._events.append(event)

	def _rmevent(self, kind):
		for event in self._events:
			if event.kind == kind:
				self._events.remove(event)
				break
		else:
			raise ValueError('queue._rmevent(kind): kind not in events')

	def _nextevent(self):
		event = min(self._events)
		self._events.remove(event)
		return event

	def _statistics(self):
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
		self._resettime()
		self._color += 1
		self._clearsamples()
		self._sampleall()

		while n > 0:
			time, kind = self._nextevent()
			self._tnow = time
			if kind == 'arrival':
				self._arrival()
			if kind == 'endofserv1':
				self._endofserv1()
			if kind == 'endofserv2':
				if self._service.customer.color == self._color:
					n -= 1
				self._endofserv2()

		self._sampleall()
		return self._statistics()

	def _updateservice(self):
		if self._service is None:
			if len(self._queue1) > 0:
				customer = self._queue1.pop()
				self._service = Service(customer, 'queue1')
				self._addevent('endofserv1')
			elif len(self._queue2) > 0:
				customer = self._queue2.pop()
				self._service = Service(customer, 'queue2')
				self._addevent('endofserv2')
		elif self._service.queue is 'queue2':
			if len(self._queue1) > 0:
				self._queue2.append(self._service.customer)
				customer = self._queue1.pop()
				self._service = Service(customer, 'queue1')
				self._rmevent('endofserv2')
				self._addevent('endofserv1')

	def _arrival(self):
		self._addevent('arrival')
		customer = Customer(self._color)
		customer.tarrival = self._tnow
		self._queue1.appendleft(customer)
		self._updateservice()
		self._sampleall()
			
	def _endofserv1(self):
		customer = self._service.customer
		customer.tendofserv1 = self._tnow
		self._service = None
		self._queue2.appendleft(customer)
		self._updateservice()
		self._sampleall()

	def _endofserv2(self):
		customer = self._service.customer
		customer.tendofserv2 = self._tnow
		self._service = None
		self._updateservice()
		self._sampleall()
		if customer.color == self._color:
			self._samplecustomer(customer)

queue = Queue(0.4)
for i in range(20):
	stats = queue.simround(50000)
	print('round {}'.format(i+1))
	for key, value in stats.items():
		print('  {} = {:2.3f}'.format(key, value), end=',')
	print()
