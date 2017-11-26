from collections import defaultdict, deque, namedtuple
import random
import math
import scipy.stats

class Sample:
	def __init__(self):
		self._values = []

	def append(self, value):
		self._values.append(value)

	def mean(self):
		return sum(self._values) / len(self._values)

	def var(self):
		mean = self.mean()
		temp = 0
		for value in self._values:
			temp += (value - mean)**2
		return temp / (len(self._values) - 1)

	def margin(self, conf):
		n = len(self._values)
		z = scipy.stats.t(n-1).ppf(1 - (1-conf)/2)
		return z * math.sqrt(self.var() / n)

class SampleFunction:
	def __init__(self):
		self._times = []
		self._values = []

	def append(self, time, value):
		self._times.append(time)
		self._values.append(value)

	def mean(self):
		area = 0
		for i in range(len(self._values) - 1):
			area += self._values[i] * (self._times[i+1] - self._times[i])
		return area / (self._times[-1] - self._times[0])

class Customer:
	def __init__(self, color):
		self.color = color
		self._start = defaultdict(list)
		self._endof = defaultdict(list)

	def start(self, name, time):
		self._start[name].append(time)

	def endof(self, name, time):
		self._endof[name].append(time)

	def totaltime(self, name):
		if len(self._start[name]) != len(self._endof[name]):
			raise ValueError('customer.totaltime(name): mismatched times')
		total = 0
		for tstart, tend in zip(self._start[name], self._endof[name]):
			total += tend - tstart
		return total

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
		ns1 = ns and self._service.queue == 'queue1'
		ns2 = ns and self._service.queue == 'queue2'
		nq1 = len(self._queue1)
		nq2 = len(self._queue2)
		n1 = nq1 + ns1
		n2 = nq2 + ns2

		self._samplefs['Nq1'].append(self._tnow, nq1)
		self._samplefs['Nq2'].append(self._tnow, nq2)
		self._samplefs['N1'].append(self._tnow, n1)
		self._samplefs['N2'].append(self._tnow, n2)

	def _samplecustomer(self, customer):
		w1 = customer.totaltime('W1')
		w2 = customer.totaltime('W2')
		x1 = customer.totaltime('X1')
		x2 = customer.totaltime('X2')
		t1 = w1 + x1
		t2 = w2 + x2

		self._samples['W1'].append(w1)
		self._samples['W2'].append(w2)
		self._samples['T1'].append(t1)
		self._samples['T2'].append(t2)

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

		return dict(self._samples), dict(self._samplefs)

	def _updateservice(self):
		if self._service is None:
			if len(self._queue1) > 0:
				customer = self._queue1.pop()
				customer.endof('W1', self._tnow)
				customer.start('X1', self._tnow)
				self._service = Service(customer, 'queue1')
				self._addevent('endofserv1')
			elif len(self._queue2) > 0:
				customer = self._queue2.pop()
				customer.endof('W2', self._tnow)
				customer.start('X2', self._tnow)
				self._service = Service(customer, 'queue2')
				self._addevent('endofserv2')
		elif self._service.queue is 'queue2':
			if len(self._queue1) > 0:
				customer = self._service.customer
				customer.endof('X2', self._tnow)
				customer.start('W2', self._tnow)
				self._queue2.append(customer)
				customer = self._queue1.pop()
				customer.endof('W1', self._tnow)
				customer.start('X1', self._tnow)
				self._service = Service(customer, 'queue1')
				self._rmevent('endofserv2')
				self._addevent('endofserv1')

	def _arrival(self):
		self._addevent('arrival')
		customer = Customer(self._color)
		customer.start('W1', self._tnow)
		self._queue1.appendleft(customer)
		self._updateservice()
		self._sampleall()
			
	def _endofserv1(self):
		customer = self._service.customer
		customer.endof('X1', self._tnow)
		customer.start('W2', self._tnow)
		self._service = None
		self._queue2.appendleft(customer)
		self._updateservice()
		self._sampleall()

	def _endofserv2(self):
		customer = self._service.customer
		customer.endof('X2', self._tnow)
		self._service = None
		self._updateservice()
		self._sampleall()
		if customer.color == self._color:
			self._samplecustomer(customer)

stats = defaultdict(Sample)
queue = Queue(0.4)
queue.simround(5e4)
for i in range(10):
	print('round {}'.format(i+1), end='\r')
	smps, smpfs = queue.simround(1e4)

	for name, sample in smps.items() | smpfs.items():
		name = 'E[' + name + ']'
		stats[name].append(sample.mean())
	for name, sample in smps.items():
		name = 'V(' + name + ')'
		stats[name].append(sample.var())

for name, stat in sorted(stats.items()):
	mean = stat.mean()
	rmargin = stat.margin(0.95) / mean
	print('{:>6} ={:8.3f} +-{:5.2f}%'.format(
		name, mean, 100 * rmargin))
