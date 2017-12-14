import argparse
from collections import *
from fila import *
import random

# Configura parser e coleta argumentos
parser = argparse.ArgumentParser()
parser.add_argument('rho', metavar='RHO', type=float,
	help='utilização do sistema')
parser.add_argument('m', metavar='M', type=int, default=1e4,
	help='tamanho da fase transiente')
parser.add_argument('k', metavar='K', type=int, default=10,
	help='número de rodadas')
args = parser.parse_args()

# Configura seed do gerador
random.seed(0)

# Encontra o tamanho mínimo da rodada para o intervalo de confiança desejado
for expn in range(2, 32):
	n = 1 << expn

	stats = defaultdict(Sample) # Dicionário contendo estatísticas
	queue = Queue(args.rho/2)   # Sistema de filas
	queue.simround(args.m)      # Simula fase transiente
	for i in range(args.k):
		print('N {}: round {} '.format(n, i+1), end='\r')
		smps, smpfs = queue.simround(n) # Simula rodada coletando estatísticas

		# Adiciona estatísticas ao dicionário
		for name, sample in smps.items() | smpfs.items():
			name = 'E[' + name + ']'
			stats[name].append(sample.mean())
		for name, sample in smps.items():
			name = 'V(' + name + ')'
			stats[name].append(sample.var())

	rmargin = []
	for stat in stats.values():
		low, high = stat.mean_interval(0.05)
		rmargin.append((high - low) / stat.mean())

	if max(rmargin) < 0.05:
		print('N {}          '.format(n))
		break

# Imprime a média das estatísticas coletadas e seus intervalos de confiança
for name, stat in sorted(stats.items()):
	mean = stat.mean()
	low, high = stat.mean_interval(0.05)
	rmargin = (high - low) / mean
	
	print('{:>6} ={:8.3f} {:5.2f}%'.format(
		name, mean, 100*rmargin))
