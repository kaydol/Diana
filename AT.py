
class AssaultTeam:
    index = 0
    maxSoldiers = 0
    maxVehicles = 0
    maxMorale = 0
    curSoldiers = 0
    curVehicles = 0
    curMorale = 0
    thresholdSoldiers = 0.5
    thresholdVehicles = 0.5
    thresholdMorale = 0.4

    def AssaultTeam(self, index, maxSoldiers, maxVehicles, maxMorale):
        self.index = index
        self.maxMorale = maxMorale
        self.maxSoldiers = maxSoldiers
        self.maxVehicles = maxVehicles

    def setMorale(self, morale):
        self.curMorale = morale
    def setSoldiers(self, soldiers):
        self.curSoldiers = soldiers
    def setVehicles(self, vehicles):
        self.curVehicles = vehicles

    def setMoraleThreshold(self, threshold):
        self.thresholdMorale = threshold
    def setSoldiersThreshold(self, threshold):
        self.thresholdSoldiers = threshold
    def setVehiclesThreshold(self, threshold):
        self.thresholdVehicles = threshold

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

    def isKIA(self):
        if self.curMorale * self.curSoldiers == 0:
            return True
        return False

    def canBeDeployed(self):
        return ( self.curMorale == self.maxMorale ) & ( self.curSoldiers + self.curVehicles == 0 )

    def canBeReinforced(self):
        return self.needsVehicles() | self.needsSoldiers()

    def isReady(self):
        return self.needsRest() & self.needsVehicles() & self.needsSoldiers() == False