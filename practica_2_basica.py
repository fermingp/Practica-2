"""
Fermín González Pereiro

Solución sencilla de la Práctica 2
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 50
NPED = 10
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
        
        self.south_car_condition = Condition(self.mutex)
        self.north_car_condition = Condition(self.mutex)
        self.pedestrian_condition = Condition(self.mutex)
        
    def pass_car_from_south(self): 
        return self.north_car.value == 0 and self.pedestrians.value == 0 
    
    def pass_car_from_north(self): 
        return self.south_car.value == 0 and self.pedestrians.value == 0 
    
    def pass_pedestrian(self): 
        return self.north_car.value == 0 and self.south_car.value == 0 

    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        if direction == SOUTH:
            self.south_car_condition.wait_for(self.pass_car_from_south)
            self.south_car.value += 1
        else:
            self.north_car_condition.wait_for(self.pass_car_from_north)
            self.north_car.value += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        if direction == SOUTH:
            self.south_car.value -= 1
            if self.south_car.value == 0:
                self.north_car_condition.notify_all()
                self.pedestrian_condition.notify_all()                    
        else:
            self.north_car.value -= 1
            if self.north_car.value == 0:
                self.south_car_condition.notify_all()
                self.pedestrian_condition.notify_all()  
        self.mutex.release()
        

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.pedestrian_condition.wait_for(self.pass_pedestrian)
        self.pedestrians.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.pedestrians.value -= 1
        if self.pedestrians.value == 0:
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
        time.sleep(random.expovariate(1/TIME_PED))

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
        time.sleep(random.expovariate(1/TIME_CARS))

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