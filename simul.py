import argparse
from collections import *
from fila import *
import random

# Configura parser de argumentos
parser = argparse.ArgumentParser()
parser.add_argument('RHO', type=float, help='utilização do sistema')
parser.add_argument('M', type=int, help='tamanho da fase transiente')
parser.add_argument('N', type=int, help='tamanho das rodadas incial')
parser.add_argument('K', type=int, help='número de rodadas')

def main(rho, m, n, k):
	"""Chamado recursivamente até encontrar o intervalo desejado"""
	stats = defaultdict(Sample) # Dicionário contendo estatísticas
	queue = Queue(rho/2)        # Sistema de filas
	queue.simround(m)           # Simula fase transiente
	for i in range(k):
		print('N {}: round {} '.format(n, i+1), end='\r')
		smps, smpfs = queue.simround(n) # Simula rodada

		# Adiciona estatísticas ao dicionário
		for name, sample in smps.items() | smpfs.items():
			name = 'E[%s]' % name
			stats[name].append(sample.mean())
		for name, sample in smps.items():
			name = 'V(%s)' % name
			stats[name].append(sample.var())

	for stat in stats.values():
		low, high = stat.mean_interval(0.05)
		rmargin = (high - low) / stat.mean()
		if rmargin > 0.05:
			return main(rho, m, 2*n, k)

	# Imprime as estatísticas encontradas e intervalos de confiança
	print('N {}          '.format(n))
	for name, stat in sorted(stats.items()):
		mean = stat.mean()
		low, high = stat.mean_interval(0.05)
		rmargin = (high - low) / mean
		print('{:>6} ={:8.3f} {:5.2f}%'.format(name, mean, 100*rmargin))

if __name__ == '__main__':
	random.seed(0)
	args = parser.parse_args()
	main(args.RHO, args.M, args.N, args.K)
