"""
Fermín González Pereiro

Práctica 2
"""

import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

PED = 2
SOUTH = 1
NORTH = 0

"""
Usamos esta leyenda para los turnos que empleamos en la práctica
0: el turno lo tienen los coches del norte
1: el turno lo tienen los coches del sur
2: el turno lo tienen los peatones
Los turnos se ceden de la siguiente manera:
    Los coches norte (turno 0) se lo ceden a coches sur (turno 1) y estos a los peatones (turno 2), 
    los cuales se lo vuelven a ceder a los coches norte (turno 0). Los turnos se ceden siempre que haya 
    gente esperando, en caso contrario se cede al turno restante, nuevamente si hay alguien en él esperando
"""

NCARS = 50 #número de coches
NPED = 10 #número de peatones
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (12, 5) # normal 12s, 5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        
        self.south_car = Value('i',0) #nº coches vienen del sur atravesando el puente
        self.north_car = Value('i',0) #nº coches vienen del norte atravesando el puente
        self.pedestrians = Value('i',0) #nº peatones atravesando el puente
        
        self.south_car_waiting = Value('i', 0) #nº coches que vienen del sur esperando
        self.north_car_waiting = Value('i', 0) #nº coches que vienen del norte esperando
        self.pedestrians_waiting = Value('i', 0) #nº peatones esperando
        
        self.south_car_condition = Condition(self.mutex)
        self.north_car_condition = Condition(self.mutex)
        self.pedestrian_condition = Condition(self.mutex)
        self.turn = Value('i', 0) #escogemos inicializarlo de esta forma
        
    # Se tiene que cumplir que sea tu turno o que esten esperando menos de 5 peatones y coches
    #del norte, además de no haber ni cohes del norte ni peatones en el puente.
    #En los otros dos casos es análogo
    def pass_car_from_south(self): 
        return self.north_car.value == 0 and self.pedestrians.value == 0 and \
            ((self.north_car_waiting.value <= 5 and self.pedestrians_waiting.value <= 5) or \
             self.turn.value == SOUTH) 
    
    def pass_car_from_north(self): 
        return self.south_car.value == 0 and self.pedestrians.value == 0 and \
            ((self.south_car_waiting.value <= 5 and self.pedestrians_waiting.value <= 5) or \
             self.turn.value == NORTH)     
    
    def pass_pedestrian(self): 
        return self.north_car.value == 0 and self.south_car.value == 0 and \
            ((self.north_car_waiting.value <= 5 and self.south_car_waiting.value <= 5) or \
             self.turn.value == PED)       
        
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        if direction == SOUTH: 
            self.south_car_waiting.value += 1
            self.south_car_condition.wait_for(self.pass_car_from_south)
            self.south_car_waiting.value -= 1
            self.south_car.value += 1
        else:
            self.north_car_waiting.value += 1
            self.north_car_condition.wait_for(self.pass_car_from_north)
            self.north_car_waiting.value -= 1
            self.north_car.value += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        if direction == SOUTH:
            self.south_car.value -= 1
            if self.pedestrians_waiting.value > 0: #si hay peatones esperando se les cede el turno
                self.turn.value = PED
            elif self.north_car_waiting.value > 0: #en caso contrario, se le cede a los coches del norte (si hay esperando)
                self.turn.value = NORTH
            if self.south_car.value == 0: #notificamos si no quedan coches del sur en el puente
                self.pedestrian_condition.notify_all()
                self.north_car_condition.notify_all()
        else: #dirección norte
            self.north_car.value -= 1
            if self.south_car_waiting.value > 0: #si hay coches sur esperando se les cede el turno
                self.turn.value = SOUTH
            elif self.pedestrians_waiting.value > 0: #en caso contrario, se le cede a los peatones (si hay esperando)
                self.turn.value = PED
            if self.north_car.value == 0: #notificamos si no quedan coches del norte en el puente
                self.south_car_condition.notify_all()
                self.pedestrian_condition.notify_all()
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.pedestrians_waiting.value += 1
        self.pedestrian_condition.wait_for(self.pass_pedestrian)
        self.pedestrians_waiting.value -= 1
        self.pedestrians.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.pedestrians.value -= 1
        if self.north_car_waiting.value > 0: #si hay coches norte esperando se les cede el turno
            self.turn.value = NORTH
        elif self.south_car_waiting.value > 0: #en caso contrario, se le cede a los coches del sur (si hay esperando)
            self.turn.value = SOUTH
        if self.pedestrians.value == 0: #notificamos si no quedan peatones en el puente
            self.north_car_condition.notify_all()
            self.south_car_condition.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

#Para los delays utilizamos los datos de las normales
def delay_car_north() -> None:
    factor = random.gauss(TIME_IN_BRIDGE_CARS[0], TIME_IN_BRIDGE_CARS[1]) #normal (12,5)
    if factor <= 0:
        time.sleep(0.01)
    else:
        time.sleep(factor)

def delay_car_south() -> None:
    factor = random.gauss(TIME_IN_BRIDGE_CARS[0], TIME_IN_BRIDGE_CARS[1])
    if factor <= 0:
        time.sleep(0.01)
    else:
        time.sleep(factor)

def delay_pedestrian() -> None:
    factor = random.gauss(TIME_IN_BRIDGE_PEDESTRIAN[0], TIME_IN_BRIDGE_PEDESTRIAN[1]) #normal (1,0.5)
    if factor <= 0:
        time.sleep(0.01)
    else:
        time.sleep(factor)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}") 
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}") 
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}") 
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED)) # a new pedestrian enters each 5s

    for p in plst:
        p.join()

def gen_cars(monitor) -> Monitor:
    cid = 0
    plst = []
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_CARS)) # a new car enters each 0.5s

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars = Process(target=gen_cars, args=(monitor,))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars.start()
    gped.start()
    gcars.join()
    gped.join()


if __name__ == '__main__':
    main()