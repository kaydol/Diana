
class AssaultTeam:
    name = 'Assault Team'
    XY = (0, 0)
    maxSoldiers = 0
    maxVehicles = 0
    maxMorale = 0
    curSoldiers = 0
    curVehicles = 0
    curMorale = 0
    thresholdSoldiers = 0.5
    thresholdVehicles = 0.5
    thresholdMorale = 0.3
    inQueue = False
    inBattle = False
    canBeDeployed = False

    def __init__(self, name, XY, (maxSoldiers, maxVehicles, maxMorale)):
        self.name = name
        self.XY = XY
        self.maxMorale = maxMorale
        self.maxSoldiers = maxSoldiers
        self.maxVehicles = maxVehicles

    def setName(self, name):
        self.name = name
    def setMorale(self, morale):
        self.curMorale = morale
    def setSoldiers(self, soldiers):
        self.curSoldiers = soldiers
    def setVehicles(self, vehicles):
        self.curVehicles = vehicles

    def setStatus(self, array):
        self.curSoldiers, self.curVehicles, self.curMorale, self.inQueue, self.canBeDeployed, self.inBattle = array

    def setThreshold(self, parameter, threshold):
        if str(parameter).lower() == 'morale':
            self.thresholdMorale = threshold
        if str(parameter).lower() == 'soldiers':
            self.thresholdSoldiers = threshold
        if str(parameter).lower() == 'vehicles':
            self.thresholdVehicles = threshold

    def getName(self):
        return self.name
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
        if self.curMorale < self.thresholdMorale * self.maxMorale:
            return True
        return False

    def needsReinforcements(self):
        return self.needsVehicles() | self.needsSoldiers()

    def hasSoldiers(self):
        return self.curSoldiers > 0
    def hasVehicles(self):
        return self.curSoldiers > 0
    def hasMaxMorale(self):
        return self.curMorale >= self.maxMorale

    def isKIA(self):
        if self.curMorale * self.curSoldiers == 0:
            return True
        return False

    def isDeployed(self):
        return self.hasSoldiers()

    def canBeDeployed(self):
        return self.canBeDeployed

    def isReady(self):
        return (not self.needsRest()) & (not self.needsVehicles()) & (not self.needsSoldiers())

    def isInQueue(self):
        return self.inQueue

    def isInBattle(self):
        return self.inBattle