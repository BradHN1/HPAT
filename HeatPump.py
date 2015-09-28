

class HeatPump :
    """Data and methods for calculation of heat pump parameters"""
    def __init__(self, Manufacturer, Brand, AHRICertNumber, OutdoorUnit,IndoorUnits,VariableSpeed,HSPFregIV,SEER,EER_95,EnergyStar, DuctedDuctless,Zones) :

        self.Manufacturer=Manufacturer
        self.Brand=Brand
        self.AHRICertNumber=AHRICertNumber
        self.OutdoorUnit=OutdoorUnit
        self.IndoorUnits=IndoorUnits
        self.VariableSpeed=VariableSpeed
        self.HSPFregIV=HSPFregIV
        self.SEER=SEER
        self.EER_95=EER_95
        self.EnergyStar=EnergyStar
        self.DuctedDuctless=DuctedDuctless
        self.Zones=Zones 
        
        self.tData = []
        self.CAPMin = []
        self.CAPRated = []
        self.CAPMax = []
        self.COPMin = []
        self.COPRated = []
        self.COPMax = []

    def parametrize(self):
    #  COP/Q = c*T^2 + b*T + c : The constant part of the polynomial fit of the heat pump data
        a_Max = [] 
        a_Min = []  
        b_Max = [] 
        b_Min = [] # (1 To HP_MAX, 1 To HP_FIT) As Single
        c_Max = [] # (1 To HP_MAX, 1 To HP_FIT) As Single
        c_Min = [] # (1 To HP_MAX, 1 To HP_FIT) As Single
        T_Min = [] # The min operating temperature of heat pumps

        # not used?
#       Q_Abs_Max = [] # Absolute Maximum possible capacity
#       Q_Abs_Min = [] # Absolute Maximum possible capacity as given in the datasheet (not temperature dependant !)
#       electric_Abs_E_Max = [] # (1 To HP_MAX, 1 To HP_FIT) As Single
#       electric_Abs_E_Min = [] # (1 To HP_MAX, 1 To HP_FIT) As Single


        # parametrizations of capacity and coefficient of performance
        c_Min.append([0.0,0.0])
            
        bMinCAP = (CAPMin[0]-CAPMin[2])/(47-5)
        bMinCOP = (COPMin[0]-COPMin[2])/(47-5)
        b_Min.append([bMinCOP,bMinCAP])
                
        aMinCAP = CAPMin[2] - 5.*bMinCAP
        aMinCOP = COPMin[2] - 5.*bMinCOP
        a_Min.append([aMinCOP,aMinCAP])
                
        c_Max.append([0.0,0.0])
            
        bMaxCAP = (CAPMax[0]-CAPMax[2])/(47-5)
        bMaxCOP = (COPMax[0]-COPMax[2])/(47-5)
        b_Max.append([bMaxCOP,bMaxCAP])
                
        aMaxCAP = CAPMax[2] - 5.*bMaxCAP
        aMaxCOP = COPMax[2] - 5.*bMaxCOP
        a_Max.append([aMaxCOP,aMaxCAP])

    def MaxCapacity(self,temp):

        if temp>self.tData[0]:
            # warmer than the 47 deg point
            capacity_Max = self.CAPMax[0]
        elif temp <= self.tData[-1]:
            # colder than the coldest point specified
            # question as to how heat pump will perform here - assume it doesn't function at that temperature
            capacity_Max = self.CAPMax[-1]
        else:
            for i in range(len(self.tData)-1):
                if temp > self.tData[i+1] and temp<= self.tData[i] :
                    # linear interpolation between the nearest reported points
                    frac = (temp-self.tData[i])/float(self.tData[i+1] - self.tData[i])
                    capacity_Max = self.CAPMax[i] + frac * (self.CAPMax[i+1] - self.CAPMax[i])
                    break
        return capacity_Max
        
    def MinCapacity(self,temp):

        if temp>self.tData[0]:
            # warmer than the 47 deg point
            capacity_Min = self.CAPMin[0]
        elif temp <= self.tData[-1]:
            # colder than the coldest point specified
            # question as to how heat pump will perform here - assume it doesn't function at that temperature
            capacity_Min = self.CAPMin[-1]
        else:
            for i in range(len(self.tData)-1):
                if temp > self.tData[i+1] and temp<= self.tData[i] :
                    # linear interpolation between the nearest reported points
                    frac = (temp-self.tData[i])/float(self.tData[i+1] - self.tData[i])
                    capacity_Min = self.CAPMin[i] + frac * (self.CAPMin[i+1] - self.CAPMin[i])
                    break
        return capacity_Min
         
    def COPatMinCapacity(self,temp):

        if temp>self.tData[0]:
            # warmer than the 47 deg point
            COP_Min = self.COPMin[0]
        elif temp <= self.tData[-1]:
            # colder than the coldest point specified
            # question as to how heat pump will perform here - assume it doesn't function at that temperature
            COP_Min = self.COPMin[-1]
        else:
            for i in range(len(self.tData)-1):
                if temp > self.tData[i+1] and temp<= self.tData[i] :
                    # linear interpolation between the nearest reported points
                    frac = (temp-self.tData[i])/float(self.tData[i+1] - self.tData[i])
                    COP_Min = self.COPMin[i] + frac * (self.COPMin[i+1] - self.COPMin[i]) 
                    break
        return COP_Min
        
    def COPatMaxCapacity(self,temp):

        if temp>self.tData[0]:
            # warmer than the 47 deg point
            COP_Max = self.COPMax[0]
        elif temp <= self.tData[-1]:
            # colder than the coldest point specified
            # question as to how heat pump will perform here - assume it doesn't function at that temperature
            COP_Max = self.COPMax[-1]
        else:
            for i in range(len(self.tData)-1):
                if temp > self.tData[i+1] and temp<= self.tData[i] :
                    # linear interpolation between the nearest reported points
                    frac = (temp-self.tData[i])/float(self.tData[i+1] - self.tData[i])
                    COP_Max = self.COPMax[i] + frac * (self.COPMax[i+1] - self.COPMax[i])
                    break
        return COP_Max


                    
            
