import numpy as np
import time

from mesa import Agent, Model
from mesa.space import ContinuousSpace
from mesa.time import RandomActivation

def isSignalClose(selfo, distance, close=0):
    return (
        (selfo.direction == 1 and 0 <= (selfo.mySignal.pos[0]+close) - selfo.pos[0] <= distance) or
        (selfo.direction == 2 and 0 <= selfo.pos[0] - (selfo.mySignal.pos[0]-close) <= distance) or
        (selfo.direction == 3 and 0 <= (selfo.mySignal.pos[1]+close) - selfo.pos[1] <= distance) or
        (selfo.direction == 4 and 0 <= selfo.pos[1] - (selfo.mySignal.pos[1]-close) <= distance)
    )

# ----------- CLASE DE LOS AUTOS ----------- #
class Car(Agent):
    def __init__(self, model: Model, pos, speed, dir, semaforo):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.mySignal = semaforo
        self.stopForSignal = False

        # dir = {1: right, 2: left, 3: down, 4: up}
        self.direction = dir

        # Speed se representa en un arreglo: [speedX, speedY]
        self.speed = speed

    def step(self):
        semaforo = self.mySignal.light

        if(semaforo == "g"):
            self.stopForSignal = False

        if((semaforo == "r" or semaforo == "y") and not self.mySignal.carSawMe and isSignalClose(self, 10)):
            self.stopForSignal = True
            self.speed = np.array([0.0, 0.0]) if isSignalClose(self, 0.5) else self.speed*0.9
            self.mySignal.carSawMe = True
        
        elif(self.stopForSignal):
            self.speed = np.array([0.0, 0.0]) if isSignalClose(self, 0.5) else self.speed*0.95

        else:
            objectAhead = self.objectAhead()
            
            new_speed = self.accelerate() if objectAhead == None else self.decelerate(objectAhead)            
            new_speed = 1 if new_speed > 1 else 0 if new_speed < 0 else new_speed

            self.speed = np.array(
                [new_speed, 0.0] if self.direction == 1 or self.direction == 2 
                else [0.0, new_speed]
            )

        vel = 0.4

        new_pos = self.pos + (
            np.array([vel, 0.0]) if self.direction == 1 else 
            np.array([-vel, 0.0]) if self.direction == 2 else 
            np.array([0.0, vel]) if self.direction == 3 else 
            np.array([0.0, -vel])
        )* self.speed

        self.model.space.move_agent(self, new_pos)

    def objectAhead(self):
        # Variable que indica el radio de cuadros a los que debe estar el vecino de enfrente para comprobar que está delante. fl = frontLength
        fl = 4 # Front length vertical

        # Se pasa por cada vecino que está a 2 bloques de distancia
        for neighbor in self.model.space.get_neighbors(self.pos, 14):
            if (((self.direction == 1 and neighbor.pos[0] > self.pos[0] or
                self.direction == 2 and neighbor.pos[0] < self.pos[0]) and 
                self.pos[1]-fl <= neighbor.pos[1] <= self.pos[1]+fl) or 
                ((self.direction == 3 and neighbor.pos[1] > self.pos[1] or
                self.direction == 4 and neighbor.pos[1] < self.pos[1]) and 
                self.pos[0]-fl <= neighbor.pos[0] <= self.pos[0]+fl)):

                # Si el vecino es un auto moviendose a la misma dirección, se regresa dicho auto
                # Si no, es necesario detenerse por completo
                return neighbor if type(neighbor) == type(self) and neighbor.direction == self.direction else Car(self.model, (0,0), self.speed*0.85, 0, None)

        return None

    def accelerate(self):
        return self.speed[0] + 0.05 if self.direction == 1 or self.direction == 2 else self.speed[1] + 0.05

    def decelerate(self, car_ahead):
        if car_ahead.speed[0] < 1.5 and car_ahead.speed[1] < 1.5:
            return self.speed[0]*0.75 if self.direction == 1 or self.direction == 2 else self.speed[1]*0.75

        return self.speed[0]*0.9 if self.direction == 1 or self.direction == 2 else self.speed[1]*0.9

    
# ----------- CLASE DE LOS SEMAFOROS ----------- #
class Signal(Agent):
    def __init__(self, model, pos, color):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.light = color
        self.carSawMe = False


# ----------- CLASE DE LOS PEATONES ----------- #
class Pedestrian(Agent):
    def __init__(self, model: Model, pos, dir, semaforo):
        super().__init__(model.next_id(), model)
        self.pos = pos
        # dir = {1: right, 2: left, 3: down, 4: up}
        self.direction = dir
        # Speed se representa en un arreglo: [speedX, speedY]
        self.speed = 0.5
        self.mySignal = semaforo
        self.stopped = False

    def step(self):
        vel = 0.25

        if(self.objectAhead() or (self.mySignal.light != "g" and isSignalClose(self, 2, 11))):
            self.speed = self.speed*0.5
            self.stopped = True
        else:
            self.speed = 0.5
            self.stopped = False

        new_pos = self.pos + (
            np.array([vel, 0.0]) if self.direction == 1 else 
            np.array([-vel, 0.0]) if self.direction == 2 else 
            np.array([0.0, vel]) if self.direction == 3 else 
            np.array([0.0, -vel])
        )* self.speed

        self.model.space.move_agent(self, new_pos)

    def objectAhead(self):

        # Se pasa por cada vecino que está a ciertos bloques de distancia
        for neighbor in self.model.space.get_neighbors(self.pos, 4):
            if (type(neighbor) == type(self) and self.direction == neighbor.direction and 
            # (self.pos[0] != neighbor.pos[0] or self.pos[1] != neighbor.pos[1])
            
            ((self.direction == 1 and neighbor.pos[0] > self.pos[0] or
                self.direction == 2 and neighbor.pos[0] < self.pos[0]) and 
                self.pos[1] == neighbor.pos[1]) or 
                ((self.direction == 3 and neighbor.pos[1] > self.pos[1] or
                self.direction == 4 and neighbor.pos[1] < self.pos[1]) and 
                self.pos[0] == neighbor.pos[0])

            ):
                return True

        return False


class Street(Model):
    def __init__(self):
        super().__init__()
        self.sizeGrid = 150

        self.space = ContinuousSpace(self.sizeGrid, self.sizeGrid, True)
        self.schedule = RandomActivation(self)

        self.startTime = time.time()
        self.signalDuration = 10 # seconds
        self.yellowOff = True

        self.posSignalA = 55
        self.posSignalB = 95
        # Creamos los semaforos
        self.signals = [
            Signal(self, np.array([self.posSignalA, self.posSignalB]), "g"), # For cars going right
            Signal(self, np.array([self.posSignalB, self.posSignalA]), "g"), # For cars going left
            Signal(self, np.array([self.posSignalA, self.posSignalA]), "r"), # For cars going down
            Signal(self, np.array([self.posSignalB, self.posSignalB]), "r") # For cars going up
        ]

        for signal in self.signals:
            self.space.place_agent(signal, signal.pos)
            self.schedule.add(signal)

        # Creamos los autos
        posCarA = 70
        posCarB = 80

        speeds = [[0.5, 0.0], [0.0, 0.5]]
        coordinates = [
            (lambda x: np.array([x, posCarB])), 
            (lambda x: np.array([x, posCarA])), 
            (lambda x: np.array([posCarA, x])), 
            (lambda x: np.array([posCarB, x]))
        ]
        for i in range(4):
            positions = self.findPos(20, 2, 2)
            for pxy in positions:
                car = Car(self, coordinates[i](pxy), np.array(speeds[i//2]), i+1, self.signals[i])
                self.space.place_agent(car, car.pos)
                self.schedule.add(car)

        # Creamos los peatones
        posPedA = 62
        posPedB = 88

        speeds = [[0.5, 0.0], [0.0, 0.5]]
        coordinates2 = [
            (lambda x: np.array([x, posPedB])), 
            (lambda x: np.array([x, posPedA])), 
            (lambda x: np.array([posPedA, x])),
            (lambda x: np.array([posPedB, x]))
        ]
        for i in range(4):
            positions = self.findPos(5, 1, 1)
            for pxy in positions:
                pedestrian = Pedestrian(self, coordinates2[i](pxy), i+1, self.signals[i])
                self.space.place_agent(pedestrian, pedestrian.pos)
                self.schedule.add(pedestrian)

    def step(self):
        self.schedule.step()

        if(time.time() > self.startTime + 7 and self.yellowOff):
            if(self.signals[0].light == "g"):
                self.signals[0].light = "y"
                self.signals[1].light = "y"
            else: 
                self.signals[2].light = "y"
                self.signals[3].light = "y"
            self.yellowOff = False

        elif(time.time() > self.startTime + self.signalDuration):
            for i in range(4):
                if(self.signals[i].light == "r"):
                    self.signals[i].light = "g"
                elif(self.signals[i].light == "y"):
                    self.signals[i].light = "r"
                self.signals[i].carSawMe = False
            self.startTime = time.time()
            self.yellowOff = True

    def findPos(self, step, cantA, cantB):
        return np.append(
                np.random.choice(np.arange(0, self.posSignalA, step), cantA, replace=False),
                np.random.choice(np.arange(self.posSignalB, self.sizeGrid, step), cantB, replace=False),
            )