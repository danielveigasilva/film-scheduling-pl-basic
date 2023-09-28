import numpy as np
import pandas as pd
from docplex.mp.model import Model

def gerateOccupancy(slot):
    if (slot >= slots.index('08:00') & slot < slots.index('09:00')):
        return 0.00679
    elif (slot >= slots.index('09:00') & slot < slots.index('11:00')):
        return 0.02612
    elif (slot >= slots.index('11:00') & slot < slots.index('13:00')):
        return 0.10398
    elif (slot >= slots.index('13:00') & slot < slots.index('15:00')):
        return 0.17594
    elif (slot >= slots.index('15:00') & slot < slots.index('17:00')):
        return 0.12979
    elif (slot >= slots.index('17:00') & slot < slots.index('19:00')):
        return 0.3756
    elif (slot >= slots.index('19:00') & slot < slots.index('21:00')):
        return 0.16402
    else:
        return 0.17761

def gerateConfigs(movie, slots, delta):
    nSlotsMovie = int(int(movie['length'])/delta)
    nSlots = len(slots)
    lastSlot = nSlots - 1
    configs = []
    for slotStart in range(nSlots):
        slotEnd = slotStart + nSlotsMovie - 1
        if (slotEnd <= lastSlot):
            config = np.pad([1]*nSlotsMovie, (slotStart, nSlots-slotEnd-1), 'constant', constant_values=(0, 0))
            configs.append(config)
        else:
            break
    return configs

def predic(s, mc):
    occupancy = sum(movies_configs[mc][t] * gerateOccupancy(t) for t in range(len(slots)))
    occupancy = occupancy / sum(movies_configs[mc][t] for t in range(len(slots)))

    return screens[s]['seating'] * movies[movies_configs_movies[mc]]['rate'] * occupancy

screens = [{'name':'Sala 1', 'seating' : 50, 'type' : 'regular'},
         {'name':'Sala 2', 'seating' : 85, 'type' : 'regular'},
         {'name':'Sala 3', 'seating' : 70, 'type' : 'regular'},
         {'name':'Sala 4', 'seating' : 100, 'type' : 'regular'},
         {'name':'Sala 5', 'seating' : 100, 'type' : 'regular'},
         {'name':'Sala 6', 'seating' : 100, 'type' : 'regular'}]

#TODO: Dataset MovieLens

movies = [{'name':'BillyLynn\'sLongHalftimeWalk',   'length': 110, 'rate': 0.284},
          {'name':'Doctor Strange',                 'length': 115, 'rate': 0.238},
          {'name':'Deepwater Horizon',              'length': 105, 'rate': 0.16},
          {'name':'I Am Not Madame Bovary',         'length': 140, 'rate': 0.095},
          {'name':'ONE PIECE FILM: GOLD',           'length': 120, 'rate': 0.062},
          {'name':'Scandal Maker',                  'length': 105, 'rate': 0.04},
          {'name':'The Warriors Gate',              'length': 110, 'rate': 0.03},
          {'name':'The New Adventures of Aladdin',  'length': 100, 'rate': 0.026},
          {'name':'Escape Route',                   'length': 110, 'rate': 0.018},
          {'name':'Mr. Donkey',                     'length': 100, 'rate': 0.016}]

t0 = '08:00'
tf = '23:35'
deltaT = 5

date = '2023-09-28T'
slots = np.arange(np.datetime64(date + t0), np.datetime64(date + tf), np.timedelta64(deltaT, 'm'))
slots = [pd.to_datetime(str(d)).strftime('%H:%M') for d in slots]

movies_configs = []
movies_configs_movies = []

for movieIndex in range(len(movies)):
    configs = gerateConfigs(movies[movieIndex], slots, deltaT)
    movies_configs_movies = movies_configs_movies + [movieIndex]*len(configs)
    movies_configs = movies_configs + configs

model = Model('Film Scheduling')

X = model.binary_var_matrix(len(screens),len(movies_configs), name='x')
model.maximize(model.sum(X[s,mc]*predic(s, mc) for s in range(len(screens)) for mc in range(len(movies_configs))))

#Sem choque de horários
for s in range(len(screens)):
    for t in range(len(slots)):
        model.add_constraint(model.sum(X[s,mc] * movies_configs[mc][t] for mc in range(len(movies_configs))) <= 1)

#Todas as Salas devem ser utilizadas
for s in range(len(screens)):
    model.add_constraint(model.sum(X[s,mc] for mc in range(len(movies_configs))) >= 1)

#Um filme tem que ser exibido pelo menos 1 vez e no maximo 3 vezes ao dia
for movieIndex in range(len(movies)):
    configs = [i for i in range(len(movies_configs_movies)) if movies_configs_movies[i] == movieIndex]
    model.add_constraint(model.sum(X[s,mc] for s in range(len(screens)) for mc in configs) >= 1)
    model.add_constraint(model.sum(X[s,mc] for s in range(len(screens)) for mc in configs) <= 3)

sol = model.solve()
results = [v.name.split('_') + [sol.get_value(v)] for v in model.iter_variables()]
results = [[int(r[1]), int(r[2])] for r in results if r[3] == 1]

#TODO: Exibir dados do modelo, valor da função objetivo, quatidade de variaveis, etc..

screenIndex_temp = -1

results = sorted(results, key=lambda result : (result[0], slots[[s for s in range(len(slots)) if movies_configs[result[1]][s] == 1 ][0]]))

for result in results:
    screenIndex = result[0]
    movieConfigIntex = result[1]
    movieIndex = movies_configs_movies[movieConfigIntex]
    
    slotsIndexs = [s for s in range(len(slots)) if movies_configs[movieConfigIntex][s] == 1 ]

    if (screenIndex != screenIndex_temp):
        print('\n#' + screens[screenIndex]['name'] + ':')
        screenIndex_temp = screenIndex

    print(' * ' + movies[movieIndex]['name'] + ' (' + slots[slotsIndexs[0]] + ' - ' + slots[slotsIndexs[-1]] + ')')

