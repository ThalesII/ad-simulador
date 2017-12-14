from collections import *
import random
import math
import scipy.stats

class Sample:
	"""Coleta amostra de uma v.a. e calcula estatísticas"""
	def __init__(self):
		self._values = []

	def append(self, value):
		"""Adiciona um valor à amostra"""
		self._values.append(value)

	def mean(self):
		"""Calcula a média amostral (estimador para a esperança)"""
		return sum(self._values) / len(self._values)

	def var(self):
		"""Calcula a variância amostral (estimador para a variância)"""
		mean = self.mean()
		temp = 0
		for value in self._values:
			temp += (value - mean)**2
		return temp / (len(self._values) - 1)

	def mean_interval(self, alpha):
		"""Calcula o intervalo de confiança para a esperança dado alpha"""
		n = len(self._values)
		mean = self.mean()
		var = self.var()
		ts = scipy.stats.t(n-1)
		low = mean + ts.ppf(alpha/2) * math.sqrt(var / n)
		high = mean + ts.ppf(1 - alpha/2) * math.sqrt(var / n)
		return low, high

	def var_interval(self, alpha):
		"""Calcula o intervalo de confiança para a variânica dado alpha"""
		n = len(self._values)
		var = self.var()
		x2 = scipy.stats.chi2(n-1)
		low = (n-1) * var / x2.ppf(1 - alpha/2)
		high = (n-1) * var / x2.ppf(alpha/2)
		return low, high

class SampleFunction:
	"""Coleta amostra de um processo estocástico e calcula estatísticas"""
	def __init__(self):
		self._times = []
		self._values = []

	def append(self, time, value):
		"""Adiciona um valor à amostra"""
		self._times.append(time)
		self._values.append(value)

	def mean(self):
		"""Calcula a média amostral (estimador para a esperança)"""
		area = 0
		for i in range(len(self._values) - 1):
			area += self._values[i] * (self._times[i+1] - self._times[i])
		return area / (self._times[-1] - self._times[0])

class Customer:
	"""Armazena informações e coleta dados sobre um freguês"""
	def __init__(self, color):
		self.color = color
		self.x1 = random.expovariate(1)
		self.x2 = random.expovariate(1)
		self._start = defaultdict(list)
		self._endof = defaultdict(list)

	def start(self, name, time):
		"""Marca tempo de início de uma etapa"""
		self._start[name].append(time)

	def endof(self, name, time):
		"""Marca tempo de término de uma etapa"""
		self._endof[name].append(time)

	def totaltime(self, name):
		"""Calcula tempo total que o freguês passou em uma etapa"""
		if len(self._start[name]) != len(self._endof[name]):
			raise ValueError('customer.totaltime(name): mismatched times')
		total = 0
		for tstart, tend in zip(self._start[name], self._endof[name]):
			total += tend - tstart
		return total

# Representa um evento do simulador, armazena tempo e tipo do evento
Event = namedtuple('Event', 'time, kind')

# Representa um serviço em execução, armazena freguês e fila de origem
Service = namedtuple('Service', 'customer, queue')

class Queue:
	"""Realiza a simulação do sistema de filas e coleta estatísticas"""
	def __init__(self, lambd):
		self._tnow = 0
		self._color = 0
		self._lambd = lambd
		self._service = None
		self._queue1 = deque()
		self._queue2 = deque()
		self._events = []

		# Prepara o simulador para execução com o primeiro evento de chegada
		self._addevent('arrival', random.expovariate(self._lambd))

	def _clearsamples(self):
		"""Inicializa todas as amostras para coleta de nova rodada"""
		self._samples = defaultdict(Sample)
		self._samplefs = defaultdict(SampleFunction)

	def _sampleall(self):
		"""Coleta valores relativos ao estado atual do sistema de filas"""
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
		"""Coleta valores relativos ao freguês saindo do sistema"""
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

	def _addevent(self, kind, dtime):
		"""Cria um novo evento e insere na lista"""
		event = Event(self._tnow + dtime, kind)
		self._events.append(event)

	def _rmevent(self, kind):
		"""Remove um evento da lista"""
		for event in self._events:
			if event.kind == kind:
				self._events.remove(event)
				break
		else:
			raise ValueError('queue._rmevent(kind): kind not in events')

	def _nextevent(self):
		"""Retorna o próximo evento em ordem cronológica"""
		event = min(self._events)
		self._events.remove(event)
		return event

	def simround(self, n):
		"""Simula uma rodada do simulador e coleta `n` fregueses no total"""
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
		"""Seleciona próximo serviço com base no estado atual do sistema"""
		if self._service is None:
			if len(self._queue1) > 0:
				customer = self._queue1.pop()
				customer.endof('W1', self._tnow)
				customer.start('X1', self._tnow)
				self._service = Service(customer, 'queue1')
				self._addevent('endofserv1', customer.x1)
			elif len(self._queue2) > 0:
				customer = self._queue2.pop()
				self._service = Service(customer, 'queue2')
				self._addevent('endofserv2', customer.x2 - customer.totaltime('X2'))
				customer.endof('W2', self._tnow)
				customer.start('X2', self._tnow)
		elif self._service.queue is 'queue2':
			if len(self._queue1) > 0:
				customer = self._service.customer
				self._queue2.append(customer)
				customer.endof('X2', self._tnow)
				customer.start('W2', self._tnow)

				customer = self._queue1.pop()
				self._service = Service(customer, 'queue1')
				self._rmevent('endofserv2')
				self._addevent('endofserv1', customer.x1)
				customer.endof('W1', self._tnow)
				customer.start('X1', self._tnow)

	def _arrival(self):
		"""Trata evento de chegada de freguês"""
		self._addevent('arrival', random.expovariate(self._lambd))
		customer = Customer(self._color)
		customer.start('W1', self._tnow)
		self._queue1.appendleft(customer)
		self._updateservice()
		self._sampleall()
			
	def _endofserv1(self):
		"""Trata evento de fim de serviço para um freguês da fila 1"""
		customer = self._service.customer
		customer.endof('X1', self._tnow)
		customer.start('W2', self._tnow)
		self._service = None
		self._queue2.appendleft(customer)
		self._updateservice()
		self._sampleall()

	def _endofserv2(self):
		"""Trata evento de fim de serviço para um freguês da fila 2"""
		customer = self._service.customer
		customer.endof('X2', self._tnow)
		self._service = None
		self._updateservice()
		self._sampleall()
		# Apenas coleta estatísticas de fregueses que chegaram essa rodada
		if customer.color == self._color:
			self._samplecustomer(customer)

