from collections import defaultdict, deque
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
	def __init__(self):
		# self.tarrival = time
		# self.color = color
		pass

class Queue:
	def __init__(self, alpha):
		self._tnow = 0
		self._alpha = alpha
		self._queue = deque()
		# self._queue2 = deque()
		# self._color = 0
		self._events = []

		self.addevent('arrival')

	def clearsamples(self):
		# self._samples = defaultdict(Sample)
		self._samplefs = defaultdict(SampleFunction)

	def sampleserver(self):
		n = len(self._queue)
		self._samplefs['ns'].append(self._tnow, n > 0)

	def samplequeue(self):
		n = len(self._queue)
		self._samplefs['nq'].append(self._tnow, max(0, n-1))

	def sampleall(self):
		self.sampleserver()
		self.samplequeue()

	def addevent(self, kind):
		if kind == 'arrival':
			time = self._tnow + random.expovariate(self._alpha)
		if kind == 'endofserv':
			time = self._tnow + random.expovariate(1)
		self._events.append((time, kind))

	def nextevent(self):
		event = min(self._events)
		self._events.remove(event)
		return event

	def statistics(self):
		stats = {}
		for key, samplef in self._samplefs.items():
			key = 'E[' + key + ']'
			stats[key] = samplef.average()
		return stats

	def simround(self, n):
		self.clearsamples()
		self.sampleall()

		while n > 0:
			time, kind = self.nextevent()
			self._tnow = time
			if kind == 'arrival':
				self.arrival()
			if kind == 'endofserv':
				self.endofserv()
				n -= 1

		self.sampleall()
		return self.statistics()

	def arrival(self):
		self._queue.appendleft(Customer())
		self.addevent('arrival')
		if len(self._queue) == 1:
			self.addevent('endofserv')
			self.sampleserver()
		else:
			self.samplequeue()

	def endofserv(self):
		customer = self._queue.pop()
		if len(self._queue) == 0:
			self.sampleserver()
		else:
			self.addevent('endofserv')
			self.samplequeue()

queue = Queue(0.8)
for i in range(20):
	stats = queue.simround(1000)
	print('{}: {}'.format(i+1, stats))
