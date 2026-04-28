import subprocess
import sys

seeds = [
    "seed/seed_times.py",                   # times primeiro
    "seed/seed_corinthians.py",             # id 1
    "seed/seed_atletico_mineiro.py",        # id 2
    "seed/seed_athletico_paranaense.py",    # id 3
    "seed/seed_bahia.py",                   # id 4
    "seed/seed_botafogo.py",                # id 5
    "seed/seed_bragantino.py",              # id 6
    "seed/seed_chapecoense.py",             # id 7
    "seed/seed_coritiba.py",                # id 8
    "seed/seed_cruzeiro.py",                # id 9
    "seed/seed_flamengo.py",                # id 10
    "seed/seed_fluminense.py",              # id 11
    "seed/seed_gremio.py",                  # id 12
    "seed/seed_internacional.py",           # id 13
    "seed/seed_mirassol.py",                # id 14
    "seed/seed_palmeiras.py",               # id 15
    "seed/seed_remo.py",                    # id 16
    "seed/seed_santos.py",                  # id 17
    "seed/seed_sao_paulo.py",               # id 18
    "seed/seed_vasco.py",                   # id 19
    "seed/seed_vitoria.py",                 # id 20
]

for seed in seeds:
    print(f"\n{'='*40}")
    print(f"Rodando {seed}...")
    print('='*40)
    result = subprocess.run([sys.executable, seed])
    if result.returncode != 0:
        print(f"ERRO ao rodar {seed}, abortando!")
        break

print("\nTodos os seeds concluidos!")