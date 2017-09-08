
class AssaultTeam:
    type = 'Unknown'
    XY = (0, 0)
    maxSoldiers = 0
    maxVehicles = 0
    maxMorale = 0
    curSoldiers = 0
    curVehicles = 0
    curMorale = 0
    thresholdSoldiers = 0.5
    thresholdVehicles = 0.5
    thresholdMorale = 0.5
    inQueue = False
    inBattle = False
    canDeploy = False
    canReinforce = False
    Moving = False

    def __init__(self, type, XY, (maxSoldiers, maxVehicles, maxMorale)):
        self.type = type
        self.XY = XY
        self.maxMorale = maxMorale
        self.maxSoldiers = maxSoldiers
        self.maxVehicles = maxVehicles

    def setType(self, type):
        self.type = type
    def setMorale(self, morale):
        self.curMorale = morale
    def setSoldiers(self, soldiers):
        self.curSoldiers = soldiers
    def setVehicles(self, vehicles):
        self.curVehicles = vehicles

    def setStatus(self, array):
        self.curSoldiers, self.curVehicles, self.curMorale, self.inQueue, self.canDeploy, self.Moving, self.canReinforce, self.inBattle = array

    def setThreshold(self, parameter, threshold):
        if str(parameter).lower() == 'morale':
            self.thresholdMorale = threshold
        if str(parameter).lower() == 'soldiers':
            self.thresholdSoldiers = threshold
        if str(parameter).lower() == 'vehicles':
            self.thresholdVehicles = threshold

    def getType(self):
        return self.type
    def getPos(self):
        return self.XY
    def getIconPos(self):
        return (self.XY[0] + 290, self.XY[1] + 28)
    def getSoldiers(self):
        return self.curMorale
    def getVehicles(self):
        return self.curMorale
    def getMorale(self):
        return self.curMorale

    def needsVehicles(self):
        if self.curVehicles < self.thresholdVehicles * self.maxVehicles:
            return True
        return False

    def needsSoldiers(self):
        if self.curSoldiers < self.thresholdSoldiers * self.maxSoldiers:
            return True
        return False

    def needsRest(self):
        return self.curMorale < self.thresholdMorale * self.maxMorale

    def needsReinforcements(self):
        return self.needsVehicles() | self.needsSoldiers()

    def hasSoldiers(self):
        return self.curSoldiers > 0
    def hasVehicles(self):
        return self.curSoldiers > 0
    def hasMaxMorale(self):
        return self.curMorale >= self.maxMorale

    def isKIA(self):
        if self.curMorale * self.curSoldiers <= 0:
            return True
        return False

    def isDeployed(self):
        return self.hasSoldiers()

    def canBeReinforced(self):
        return self.canReinforce

    def canBeDeployed(self):
        return self.canDeploy & self.hasMaxMorale()

    def isReady(self):
        return (not self.needsRest()) & \
               (not self.needsVehicles()) & \
               (not self.needsSoldiers()) &\
               (not self.isMoving()) & \
               (not self.isInBattle()) & \
               (not self.isInQueue())

    def isInQueue(self):
        return self.inQueue

    def isMoving(self):
        return self.Moving

    def isInBattle(self):
        return self.inBattle