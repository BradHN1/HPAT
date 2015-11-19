# Copyright (c) 2015 CSEC (Comprehensive Sustainable Energy Committee), Town of Concord
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# adapted from VBA code, Author: Jonah Kadoko
# Date: 04-10-15
# Description:
# This piece of code is part of a larger code that will eventually be integrated into a much larger code 
# to be used to analyse cold-climate heat pumps for the Tufts ME 145 project.
# Converted to Python 3.4 by Brad Hubbard-Nelson, 5/7/2015

# recently added:
# thermal resistance - improve calculation robustness
# generalize to natural gas for comparison
# HVAC efficiency a settable parameter for comparison
# programmable thermostats for baseline system for comparison
# dual fuel system
# heat pump cooling
# 
#
# to do:
# dehumidifier usage

from HeatPump import *          # new heat pump class

from datetime import datetime, date, time
from pylab import *

# Heating system types

HEAT_TYPE_OIL = 0
EFFICIENCY_HVAC_OIL = 0.75
ENERGY_CONTENT_OIL = 139000    # from http://www.engineeringtoolbox.com/energy-content-d_868.html
KGCO2_PER_UNIT_OIL = 72.93*1e-6*ENERGY_CONTENT_OIL

HEAT_TYPE_GAS = 1
EFFICIENCY_HVAC_GAS = 0.90
ENERGY_CONTENT_GAS = 1050      # listed as 950-1150 from http://www.engineeringtoolbox.com/energy-content-d_868.html
KGCO2_PER_UNIT_GAS = 53.06*1e-6*ENERGY_CONTENT_GAS      # http://www.epa.gov/climateleadership/documents/emission-factors.pdf

HEAT_TYPE_ELEC = 2
EFFICIENCY_HVAC_ELEC = 0.75
ENERGY_CONTENT_ELEC = 3412                              # from http://www.engineeringtoolbox.com/energy-content-d_868.html
KGCO2_PER_UNIT_ELEC = (722/2.2)*1e-3

HEAT_TYPE_LPG = 3
EFFICIENCY_HVAC_LPG = 0.75
ENERGY_CONTENT_LPG = 91330                              # from http://www.engineeringtoolbox.com/energy-content-d_868.html
KGCO2_PER_UNIT_LPG = 62.*1e-6*ENERGY_CONTENT_LPG

HEAT_TYPE_OTHER = 4
EFFICIENCY_HVAC_OTHER = 1.0
ENERGY_CONTENT_OTHER = 1
KGCO2_PER_UNIT_OTHER = 0


class HeatPumpAnalysis :    
    """Data and methods for calculation of heat pump parameters"""
    def __init__(self) :
        # Heat pump parameters

        self.HPList = []         # list of all defined heat pumps
        self.HPChoice = []       # new: list of chosen heat pumps (objects from HPList, can be repeated)

        self.HEAT_NAME_OIL = "Fuel Oil"
        self.HEAT_NAME_GAS = "Natural Gas"
        self.HEAT_NAME_ELEC = "Electric Resistance"
        self.HEAT_NAME_LPG = "Propane"

        self.UNITS_OIL = "Gallons"
        self.UNITS_GAS = "SCF"
        self.UNITS_ELEC = "KWh"
        self.UNITS_LPG = "Gallons"

        self.STANDARD_PRICE_OIL = 3.20      # Dec 2014 price - varied substantially in 2015
        self.STANDARD_PRICE_GAS = 0.01447   # average MA price 2015
        self.STANDARD_PRICE_ELEC = 0.15
        self.STANDARD_PRICE_LPG = 3.105                              # average Ma LPG price 2015

        # Baseline heating scenario - for which the usage data applies
        self.BaseHeatType = self.HEAT_NAME_OIL
        self.BaseHvacEfficiency = EFFICIENCY_HVAC_OIL
        self.BaseEnergyContent = ENERGY_CONTENT_OIL     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
        self.BaseEnergyUnits = self.UNITS_OIL
        self.BaseKgCO2PerUnit = KGCO2_PER_UNIT_OIL
        self.BaseCostPerUnit = self.STANDARD_PRICE_OIL
        self.BaseInflationRate = 0.05

        # supplemental system - augments the HeatPump system to meet necessary capacity
        self.SuppHeatType = self.BaseHeatType
        self.SuppHvacEfficiency = self.BaseHvacEfficiency
        self.SuppEnergyContent = self.BaseEnergyContent     
        self.SuppEnergyUnits = self.BaseEnergyUnits
        self.SuppKgCO2PerUnit = self.BaseKgCO2PerUnit
        self.SuppCostPerUnit = self.BaseCostPerUnit

        self.SuppOutdoorTempNABL = 0         # automatically enable supplemental system below this temperature
        self.SuppInflationRate = self.BaseInflationRate

        # water heating system - augments the HeatPump system to meet necessary capacity
        self.WaterHeatType = self.BaseHeatType
        self.WaterHeatEfficiency = self.BaseHvacEfficiency
        self.WaterEnergyContent = self.BaseEnergyContent
        self.WaterEnergyUnits = self.BaseEnergyUnits
        self.WaterKgCO2PerUnit = self.BaseKgCO2PerUnit
        self.WaterCostPerUnit = self.BaseCostPerUnit

        self.WaterHeatMonthlyBTU = 2.4e6
        # in WaterEnergyUnits if same as BaseEnergyUnits are subtracted from heat load
        self.WaterHeatMonthlyUsage = self.WaterHeatMonthlyBTU/self.WaterEnergyContent    
        self.WaterHeatCombinedBill = True   # if the fuel for water heating is combined with the fuel from heating (not separately metered)
        self.HPWaterHeaterCOP = 0.0

        self.ElecEnergyContent = ENERGY_CONTENT_ELEC
        self.ElecKgCO2PerUnit = KGCO2_PER_UNIT_ELEC
        self.ElectricInflationRate = self.BaseInflationRate

        self.AlternativeReplacementCost = 0
        self.AlternativeReplacementYears = 0

        self.HeatPumpAverageUnits = 0
        self.BaseAverageUnits = 0
        self.BLACAverageUnits = 0
        self.SuppAverageUnits = 0

        self.T_Outdoor = [] # (1 To SITE_DATA_MAX) As Single ' outdoor temperature
        self.WinterHPSetPoint = 65       # formerly T_Indoor : indoor temperaure as provided by the user
        self.SummerHPSetPoint = 78
        self.WinterBLSetPoint = self.WinterHPSetPoint
        self.SummerBLSetPoint = self.SummerHPSetPoint
        self.BaselineAC = 0      # none
        self.BaselineSEER = 0

        # times at which the temperature data was taken, this includes date and time
        self.t_Data = []    # (1 To SITE_DATA_MAX) As Date 
        self.t_Start = 0
        self.t_End = 0

        # Customer Specific parameters
        self.fuelDeliveryHeader = ""
        self.purchase_Date = []
        self.purchase_Quantity = []
        self.purchase_Cost = []
        self.numDeliveries = 0
        self.last_Purchase = -1
        self.current_Heating_Year = 2003         # at the very least, current heating year

        self.turn_ON_Date  = datetime.date(2015,9,15)   # As Date # winter time on which the customer is likely to turn the HVAC
        self.turn_OFF_Date  = datetime.date(2015,6,1)  # As Date # turn off HVAC heating

        # average resistance is calculated per purchase period
        self.approx_Resistance = [] # (1 To PURCHASES_MAX, 1 To 2) As Double 
        self.average_Resistance = -1.0

        # arrays indexed by time (calculated from temperature vs time data)
        self.timeArray = []
        self.Q_required = []         # Double # based on resistance and outdoor temperatures only
        self.QC_required = []         # Double # based on resistance and outdoor temperatures only
        self.electric_Required = []  # Min consumption, Approximate requirement, Max consumption (for each heat pump)

        self.capacity_Max = []       # maximum capacity of each heat pump in the heating period
        self.capacity_Min = []       # minimum capacity of each heat pump in the heating period
        self.supplemental_Heat = []  # additional heat required to meet heating requirements per hour
        self.COP_Ave = []            #  
        self.baselineAC_pwr = []
        self.heatpumpAC_pwr = []

        self.KWhByYear = []
        self.SuppUnitsByYear = []
        self.SuppUsesByYear = []
        self.BaseUnitsByYear = []
        self.BaseCostByYear = []
        self.BLAC_KWhByYear = []
        self.HPAC_KWhByYear = []
  
        self.updateGraph = False
        self.updateTemp = True
        self.updateResistance = True

        workingDirectory = './Residential Profiles/'
        # filename = 'FP Oil Deliveries.txt'
        filename = 'Default Oil Deliveries.txt'
        purchasesFile = workingDirectory + filename
        self.numDeliveries = self.loadFuelDeliveries(purchasesFile)
    
    def SetBLScenario(self,BLT) :
        
        if BLT == HEAT_TYPE_OIL :    # oil
            self.BaseHeatType = self.HEAT_NAME_OIL
            self.BaseHvacEfficiency = EFFICIENCY_HVAC_OIL
            self.BaseEnergyContent = ENERGY_CONTENT_OIL     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.BaseEnergyUnits = self.UNITS_OIL
            self.BaseKgCO2PerUnit = KGCO2_PER_UNIT_OIL
            self.BaseCostPerUnit = self.STANDARD_PRICE_OIL
        elif BLT == HEAT_TYPE_GAS : # natural gas
            self.BaseHeatType = self.HEAT_NAME_GAS
            self.BaseHvacEfficiency = EFFICIENCY_HVAC_GAS
            self.BaseEnergyContent = ENERGY_CONTENT_GAS     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.BaseEnergyUnits = self.UNITS_GAS
            self.BaseKgCO2PerUnit = KGCO2_PER_UNIT_GAS
            self.BaseCostPerUnit = self.STANDARD_PRICE_GAS
        elif BLT == HEAT_TYPE_ELEC : # electric
            self.BaseHeatType = self.HEAT_NAME_ELEC
            self.BaseHvacEfficiency = EFFICIENCY_HVAC_ELEC
            self.BaseEnergyContent = ENERGY_CONTENT_ELEC     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.BaseEnergyUnits = self.UNITS_ELEC
            self.BaseKgCO2PerUnit = KGCO2_PER_UNIT_ELEC
            self.BaseCostPerUnit = self.STANDARD_PRICE_ELEC
        elif BLT == HEAT_TYPE_LPG : # propane
            self.BaseHeatType = self.HEAT_NAME_LPG
            self.BaseHvacEfficiency = EFFICIENCY_HVAC_LPG
            self.BaseEnergyContent = ENERGY_CONTENT_LPG     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.BaseEnergyUnits = self.UNITS_LPG
            self.BaseKgCO2PerUnit = KGCO2_PER_UNIT_LPG
            self.BaseCostPerUnit = self.STANDARD_PRICE_LPG
           
        else:
            self.BaseHeatType = self.HEAT_NAME_OIL
            self.BaseHvacEfficiency = EFFICIENCY_HVAC_OIL
            self.BaseEnergyContent = ENERGY_CONTENT_OIL     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.BaseEnergyUnits = self.UNITS_OIL
            self.BaseKgCO2PerUnit = KGCO2_PER_UNIT_OIL
            self.BaseCostPerUnit = self.STANDARD_PRICE_OIL
            print("Other baseline heating types not supported")
        print("Baseline scenario chosen: "+self.BaseHeatType)

        # for now, assume supplemental system is same as the baseline system
        self.SuppHeatType = self.BaseHeatType
        self.SuppHvacEfficiency = self.BaseHvacEfficiency
        self.SuppEnergyContent = self.BaseEnergyContent     
        self.SuppEnergyUnits = self.BaseEnergyUnits
        self.SuppKgCO2PerUnit = self.BaseKgCO2PerUnit
        self.SuppCostPerUnit = self.BaseCostPerUnit
    
        self.updateResistance = True
    
    def SetSuppHeat(self,BLT) :
        if BLT == HEAT_TYPE_OIL :    # oil
            self.SuppHeatType = self.HEAT_NAME_OIL
            self.SuppHvacEfficiency = EFFICIENCY_HVAC_OIL
            self.SuppEnergyContent = ENERGY_CONTENT_OIL     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.SuppEnergyUnits = self.UNITS_OIL
            self.SuppKgCO2PerUnit = KGCO2_PER_UNIT_OIL
            self.SuppCostPerUnit = self.STANDARD_PRICE_OIL
        elif BLT == HEAT_TYPE_GAS : # natural gas
            self.SuppHeatType = self.HEAT_NAME_GAS
            self.SuppHvacEfficiency = EFFICIENCY_HVAC_GAS
            self.SuppEnergyContent = ENERGY_CONTENT_GAS     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.SuppEnergyUnits = self.UNITS_GAS
            self.SuppKgCO2PerUnit = KGCO2_PER_UNIT_GAS
            self.SuppCostPerUnit = self.STANDARD_PRICE_GAS
        elif BLT == HEAT_TYPE_ELEC : # electric
            self.SuppHeatType = self.HEAT_NAME_ELEC
            self.SuppHvacEfficiency = EFFICIENCY_HVAC_ELEC
            self.SuppEnergyContent = ENERGY_CONTENT_ELEC     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.SuppEnergyUnits = self.UNITS_ELEC
            self.SuppKgCO2PerUnit = KGCO2_PER_UNIT_ELEC
            self.SuppCostPerUnit = self.STANDARD_PRICE_ELEC
        elif BLT == HEAT_TYPE_LPG : # propane
            self.SuppHeatType = self.HEAT_NAME_LPG
            self.SuppHvacEfficiency = EFFICIENCY_HVAC_LPG
            self.SuppEnergyContent = ENERGY_CONTENT_LPG     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.SuppEnergyUnits = self.UNITS_LPG
            self.SuppKgCO2PerUnit = KGCO2_PER_UNIT_LPG
            self.SuppCostPerUnit = self.STANDARD_PRICE_LPG
        else:        
            self.SuppHeatType = "None"
            self.SuppHvacEfficiency = 0
            self.SuppEnergyContent = 0     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            self.SuppEnergyUnits = "???"
            self.SuppKgCO2PerUnit = 0
            self.SuppCostPerUnit = 0
        print("Supplemental system chosen: "+self.SuppHeatType)

        self.updateResistance = True

    def SetBLWScenario(self,BLT) :
        if BLT == HEAT_TYPE_OIL :    # oil
            self.WaterHeatType = self.HEAT_NAME_OIL
            self.WaterHeatEfficiency = EFFICIENCY_HVAC_OIL
            self.WaterEnergyContent = ENERGY_CONTENT_OIL
            self.WaterEnergyUnits = self.UNITS_OIL
            self.WaterKgCO2PerUnit = KGCO2_PER_UNIT_OIL
            self.WaterCostPerUnit = self.STANDARD_PRICE_OIL
        elif BLT == HEAT_TYPE_ELEC :    # electric resistance
            self.WaterHeatType = self.HEAT_NAME_ELEC
            self.WaterHeatEfficiency = EFFICIENCY_HVAC_ELEC
            self.WaterEnergyContent = ENERGY_CONTENT_ELEC
            self.WaterEnergyUnits = self.UNITS_ELEC
            self.WaterKgCO2PerUnit = KGCO2_PER_UNIT_ELEC
            self.WaterCostPerUnit = self.STANDARD_PRICE_ELEC
        elif BLT == HEAT_TYPE_GAS :    # gas
            self.WaterHeatType = self.HEAT_NAME_GAS
            self.WaterHeatEfficiency = EFFICIENCY_HVAC_GAS
            self.WaterEnergyContent = ENERGY_CONTENT_GAS
            self.WaterEnergyUnits = self.UNITS_GAS
            self.WaterKgCO2PerUnit = KGCO2_PER_UNIT_GAS
            self.WaterCostPerUnit = self.STANDARD_PRICE_GAS
        elif BLT == HEAT_TYPE_LPG :    # LPG
            self.WaterHeatType = self.HEAT_NAME_LPG
            self.WaterHeatEfficiency = EFFICIENCY_HVAC_LPG
            self.WaterEnergyContent = ENERGY_CONTENT_LPG
            self.WaterEnergyUnits = self.UNITS_LPG
            self.WaterKgCO2PerUnit = KGCO2_PER_UNIT_LPG
            self.WaterCostPerUnit = self.STANDARD_PRICE_LPG

        print("Water scenario chosen: "+self.WaterHeatType)
        self.WaterHeatMonthlyUsage = self.WaterHeatMonthlyBTU/self.WaterEnergyContent      

        self.UpdateResistance = True

    def SetBLAScenario(self,BLA) :
        if BLA == 0 :    # none
            self.BaselineAC = 0
        elif BLA == 1 :    # window units, how many
            self.BaselineAC = 1
        elif BLA == 2 :    # central
            self.BaselineAC = 2

    def loadFuelDeliveries(self,purchasesFile):

        # this was take from previous code tested using First Parish oil purchases
        # input = open('./Residential Profiles/FP Oil Deliveries.txt')
        self.numDeliveries = 0
        self.purchase_Quantity.clear()
        self.purchase_Cost.clear()
        self.purchase_Date.clear()
    
        # read the purchases file
        self.fuelDeliveryHeader = ""
    
        try:
            input = open(purchasesFile,'r', encoding='latin-1')

        except:
            print("Unable to open input file")
            return
        
        test = input.read()
        lines = test.split('\n')
        input.close()
    
        LN = 0      # step through data starting at first line
        while True:
            print(lines[LN])
            self.fuelDeliveryHeader += lines[LN]
            LN += 1
        
            if lines[LN].find('Heat source: ')>=0 :
                HeatSource = lines[LN]
                if HeatSource.find(self.HEAT_NAME_OIL)>=0 :
                    self.SetBLScenario(HEAT_TYPE_OIL)
                elif HeatSource.find(self.HEAT_NAME_GAS)>=0 :
                    self.SetBLScenario(HEAT_TYPE_GAS)
                elif HeatSource.find(self.HEAT_NAME_ELEC)>=0 :
                    self.SetBLScenario(HEAT_TYPE_ELEC)
                elif HeatSource.find(self.HEAT_NAME_LPG)>=0 :
                    self.SetBLScenario(HEAT_TYPE_LPG)
            
            if lines[LN].find('$$')>=0 :
                LN += 1 
                break;    # locate where the data starts
        print('====================')

        if self.BaseHeatType == self.HEAT_NAME_OIL:
            self.lastPrice = self.STANDARD_PRICE_OIL
        elif self.BaseHeatType == self.HEAT_NAME_GAS:
            self.lastPrice = self.STANDARD_PRICE_GAS
        elif self.BaseHeatType == self.HEAT_NAME_ELEC:
            self.lastPrice = self.STANDARD_PRICE_ELEC
        elif self.BaseHeatType == self.HEAT_NAME_LPG:
            self.lastPrice = self.STANDARD_PRICE_LPG
    
        first = True
        while True:
            if (LN<len(lines)):
                tokens = lines[LN].split('\t')
            else:
                break
            if len(tokens)<3:
                break           # or blank lines at end of file
            
            LN += 1
    
            if not first:
                prevYear = year
            if tokens[0].isalnum():         # first delivery of a year
                year = int(tokens[0])
    
            if tokens[3].isalpha():
                continue         # skip maintenance records
        
            quantity = tokens[3].replace(',','')
            try:
                quantity = float(quantity)
            except:
                quantity = 0.0

            cost = tokens[2][tokens[2].find('$')+1:]
            try:
                cost = cost.replace(',','')
                cost = float(cost)
            except:
                cost = 0.0
            
            if cost>0 and quantity>0:
                self.lastPrice = cost/quantity
            elif quantity>0:
                cost = self.lastPrice*quantity 
            elif cost==0.0 and quantity==0.0:
                break
            
            if first:
                prevDeliveryDate = date(year,1,1)
                prevMonth = 12
                prevYear = year-1
            else:
                prevDeliveryDate = DeliveryDate
                prevMonth = month
        
            datestring = tokens[1]
            monthDayYear = datestring.split('/')
            month = int(monthDayYear[0])
            day = int(monthDayYear[1]) 
            monthyear = (month,year)
            prevmonthyear = (prevMonth,prevYear)

            DeliveryDate = date(year,month,day)

            self.purchase_Quantity.append(quantity)
            self.purchase_Cost.append(cost)            
            self.purchase_Date.append(DeliveryDate)

            self.numDeliveries += 1

        self.UpdateTemp = True
        self.UpdateResistance = True
    
        return self.numDeliveries
    def saveFuelDeliveries(self,purchasesFile):
        # open the purchases file
        if self.numDeliveries<=0:
            print("No delivery data to save")
            return
    
        try:
            output = open(purchasesFile,'w', encoding='latin-1')

        except:
            print("Unable to open output file")
            return
        
        # write a couple line header
        now = datetime.date.today()
        now = now.isoformat()
        outputstring = "Fuel delivery data for: (enter name here)\nFile date: "+now+"\nYear	Date	$$	"+BaseEnergyUnits+"s\n"

        oldYear = 0
        for i in range(self.numDeliveries) :
            year = self.purchase_Date[i].year
            if oldYear!= year :
                oldYear = year
                outputstring += "%d\t" % year
            else :
                outputstring += "\t"
        
            day = self.purchase_Date[i].day
            month = self.purchase_Date[i].month
            year = self.purchase_Date[i].year % 100
            outputstring += "%d/%d/%02d\t" % (month, day, year)
        
            outputstring += "$%.2f\t" % self.purchase_Cost[i]
            outputstring += "%.1f\n" % self.purchase_Quantity[i]
        
        output.write(outputstring)
        output.close()
    
        return self.numDeliveries
    
    def ClearDeliveryData(self):
    
        # clear the data
        self.numDeliveries = 0
        self.purchase_Date.clear()
        self.purchase_Cost.clear()
        self.purchase_Quantity.clear()

    def DeleteDelivery(self,id):
        self.numDeliveries -= 1
        del self.purchase_Date[id]
        del self.purchase_Cost[id]
        del self.purchase_Quantity[id]
 
    def AddDelivery(self,id,date,cost,amount):
        self.numDeliveries += 1
        self.purchase_Date.insert(id,date)
        self.purchase_Cost.insert(id,cost)
        self.purchase_Quantity.insert(id,amount)

    def loadHeatPumps(self):

        # read the heat pump data file
        workingDirectory = './'
        filename = 'Cold Climate Air-Source Heat Pump Listing.txt'
        HeatPumpDataFile = workingDirectory + filename
        
        input = open(HeatPumpDataFile,'r', encoding='latin-1')
        test = input.read()
        lines = test.split('\n')

        LN = 0      # step through data starting at first line
        tokens = lines[0].split('\t')

        def tF(stringvar):
            return float((stringvar.replace(',','')).replace('"',''))
                 
        # ' Load Heat Pump Data
        first = True
        while True:
            
            if (LN==len(lines)):
                break
            LN += 1
            if LN<3:
                continue;
                
            tokens = lines[LN].split('\t') 
            if tokens[0]=='': break               
            if len(tokens)<50 : break
    
            heatPump = HeatPump(Manufacturer=tokens[0], Brand=tokens[1], AHRICertNumber=tokens[2], OutdoorUnit=tokens[3],                
                IndoorUnits=tokens[4],VariableSpeed=tokens[5],HSPFregIV=tokens[6],SEER=tokens[7],EER_95=tokens[8],EnergyStar=tokens[9],
                DuctedDuctless=tokens[10],Zones=tokens[11])
    
            try:
                # calculate linear parameters a and b from the NEEP data
                tData = [47,17,5]
                CAPMin = []
                CAPRated = []
                CAPMax = []
                COPMin = []
                COPRated = []
                COPMax = []
                CAPMin.append(tF(tokens[13]))
                CAPMin.append(tF(tokens[23]))
                CAPMin.append(tF(tokens[33]))
#               CAPRated.append(tF(tokens[14]))
#               CAPRated.append(tF(tokens[24]))
#               CAPRated.append(tF(tokens[34]))
                CAPMax.append(tF(tokens[15]))
                CAPMax.append(tF(tokens[25]))
                CAPMax.append(tF(tokens[35]))
            
                COPMin.append(tF(tokens[19]))
                COPMin.append(tF(tokens[29]))
                COPMin.append(tF(tokens[39]))
#               COPRated.append(tF(tokens[20]))
#               COPRated.append(tF(tokens[30]))
#               COPRated.append(tF(tokens[40]))
                COPMax.append(tF(tokens[21]))
                COPMax.append(tF(tokens[31]))
                COPMax.append(tF(tokens[41]))
                
                if tokens[47] != 'N/A':
                    tData.append(tF(tokens[47]))
                    CAPMin.append(tF(tokens[48]))
#                   CAPRated.append(tF(tokens[49]))
                    CAPMax.append(tF(tokens[50]))
                    COPMin.append(tF(tokens[54]))
#                   COPRated.append(tF(tokens[55]))
                    COPMax.append(tF(tokens[56]))
            
                heatPump.tData = tData
                heatPump.CAPMin = CAPMin
 #              heatPump.CAPRated = CAPRated 
                heatPump.CAPMax = CAPMax 
                heatPump.COPMin = COPMin
 #              heatPump.COPRated = COPRated
                heatPump.COPMax = COPMax
                   
#               heatPump.parametrize()

                self.HPList.append(heatPump)
            
            except Exception as e:
                print(e)
                
    def LoadTempDataRaw(self,status, year=0):
    
        self.T_Outdoor.clear()
        self.t_Data.clear()

        if year==0:
            yearStart = self.purchase_Date[0].year
            if yearStart<2002 :
                yearStart = 2002
            yearEnd = self.purchase_Date[-1].year
        else:
            yearStart = yearEnd = year
        
        prevTemp = -999
        oneHour = datetime.timedelta(0,0,0,0,0,1,0)
    
        # loop over files from these years
        ClimaticDataPath = './Climate Data/KBED'
        for year in range(yearStart,yearEnd+1):
            filename = "%s-%i.txt" % (ClimaticDataPath, year) 
            print("Reading "+filename)
        
            # can one get this information to the UI?  (updating a text widget)
            status.config(text="Loading temperature data from: "+filename)
            status.update()

            LN = -1
            nextHour = datetime.datetime(year,1,1,0,0)
            for line in open(filename,'r',encoding='latin-1'):
                LN+=1
                if LN==0: 
                    continue
                tokens = line.rstrip().split('\t')
                if len(tokens)<1:
                    print("len(tokens)<1") 
                    break
                try:
                    datestring = tokens[0]
                    if datestring.find('-') == 1 : 
                        datestring = "0"+datestring
                    if datestring.find('-',3,5) == 4 :
                        datestring = datestring[0:3]+"0"+datestring[3:]
                    if datestring.find(':') == 12 :
                        datestring = datestring[0:11]+"0"+datestring[11:]
                    dateTime = datetime.datetime.strptime(datestring[0:-4], "%m-%d-%Y %H:%M")
                except:     # hit the line past the date lines
                    break

                try:
                    temp = float(tokens[1])
                except:
                    pass
                
                # record hourly data when the next dateTime point is past the nextHour to be recorded     
                while nextHour<dateTime :
                    self.t_Data.append(nextHour)
                    self.T_Outdoor.append(temp)                
                    nextHour = nextHour+oneHour  
            
    def LoadTempData(self):     # OBSOLETE
        # Load climatic data
        # Find location of the start of the year of the heating period

        # Improvement would be to load from mesowest.utah.edu for the location specified

        # read the climatic data file
        ClimaticDataFile = './Superseded/Modified Temp data.txt'
        first = True
        LN = -1
        NextLN = 2
        for line in open(ClimaticDataFile):
            LN += 1
            if LN<NextLN :  continue
            if len(line)>1 :            
                tokens = line.split('\t')
                dateTime = datetime.datetime.strptime(tokens[3], "%m/%d/%y %H:%M")
            else:
                break
        
            if first:
                # Find location of the start of the year of the heating period
                FirstDateTime = dateTime
                year_Start = 24 * (datetime.datetime(purchase_Date[0].year, 1, 1,0,0) - FirstDateTime)
           
                # Quickly jump to January 1st of the purchase date (or year under scrutiny)
#               LN += year_Start.days - 1
                NextLN = LN+year_Start.days
                first = False;

            else :
                #Loop through the temperature data
                self.t_Data.append(dateTime)
                self.T_Outdoor.append(float(tokens[4]))

        print("Temperature data loaded")        
 
    def doHeatPumpAnalysis(self,status): 
        # certain years of note since 1993
        AverageHDDYear = 2008
        AverageCDDYear = 2003
        HighestHDDYear = 2003
        HighestCDDYear = 2010
    
        if len(self.HPChoice)==0 and self.HPWaterHeaterCOP==0 and self.SuppHeatType==self.BaseHeatType:
            msg = "No heat pump or H.P. water heater selected"
            return msg
        elif len(self.purchase_Date)<=0 :
            msg = "Enter purchase data which defines analysis time period"
            return msg
            
        if len(self.HPChoice)>0:
            hpNames = ""
            n = 0
            for hp in self.HPChoice :
                hpNames += hp.Manufacturer +'-' +hp.OutdoorUnit
                n += 1
                if n<len(self.HPChoice):
                    hpNames += "+"

        if self.updateTemp :
            # pass info back to UI status bar
            status.config(text="Loading temperature data for period")
            status.update()
            self.LoadTempDataRaw(status)
            self.updateTemp = False

        self.updateResistance = True
        if self.updateResistance :
            status.config(text="Calculating home thermal resistance")
            status.update()
            self.approxResistance()
            self.updateResistance = False

        if len(self.HPChoice)>0:
            status.config(text="Analyzing heat pump performance")
            status.update()
            p = self.heatPumpPerformance(0)
        elif self.SuppHeatType != self.BaseHeatType:
            status.config(text="Analyzing supplemental system performance")  
            status.update()
            p = self.heatPumpPerformance(0)
        
        totSavings = totBaseEmissions = totHPEmissions = totSuppEmissions = 0.
        totHPACEmissions = totBLACEmissions = 0.0
        totHPHWEmissions = totBLHWEmissions = 0.0
    
        BLAC = self.BaselineAC != 0 and self.SummerBLSetPoint> 0
        HPAC = self.SummerHPSetPoint>0

        # header line
        if len(self.HPChoice)>0:
            results = "\nAnalysis of heat pump performance for " + hpNames +"\n\n"
        elif self.HPWaterHeaterCOP>0:
            results = "\nAnalysis of heat pump water heater, COP = %.1f\n\n" % (self.HPWaterHeaterCOP)
        elif SuppHeatType != BaseHeatType:
            results = "\nAnalysis of supplemental heat system change to %s\n\n" % (self.SuppHeatType)
        
        # First line of table
        results += "\tBaseline ("+self.BaseHeatType+")\t\t"

        if (self.WaterHeatType == self.BaseHeatType and self.WaterHeatMonthlyUsage>0) or self.WaterHeatType == self.HEAT_NAME_ELEC:
            results += "Hot Water\t\t"
        
        if BLAC:
            results += "Air Conditioning\t\t"

        results += " |  "

        if len(self.HPChoice)>0:
            results += "Heat Pump\t\t\t"
        
        if self.HPWaterHeaterCOP>0:
            results += "Hot Water\t\t"
        if len(self.HPChoice)>0 or self.SuppHeatType != self.BaseHeatType:
            results += " |  "
            results += "Supplemental ("+self.SuppHeatType+")\t\t\t"

        if len(self.HPChoice)>0:
                results += "Air Conditioning"

        results +="\n"
    
        # second line of table
        results += "Year\t"+self.BaseEnergyUnits+"\tCost\t"

        if self.WaterHeatType == self.BaseHeatType and self.WaterHeatMonthlyUsage>0:
            results += self.BaseEnergyUnits+"\tCost\t"
        elif self.WaterHeatType==self.HEAT_NAME_ELEC:
            results += "KWh\tCost\t"
        

        if BLAC:
            results += "kWh\tCost\t"

        results += " |  "

        if len(self.HPChoice)>0:
            results += "KWh\tCost\tCOP\t"
        
        if self.HPWaterHeaterCOP>0:
            results += "KWh\tCost\t"
        
        if len(self.HPChoice)>0 or self.SuppHeatType!=self.BaseHeatType:
            results += " |  "

            results += "#days\t"+self.SuppEnergyUnits+"\tCost\t"
        if len(self.HPChoice)>0:
            results += "kWh\tCost\t"

        results += "\n"

        startYear = self.t_Data[self.t_Start].year
        endYear = self.t_Data[self.t_End].year
        for year in range(startYear+1,endYear):     # first and last years tend to be truncated, with potentially misleading results
            Y = year-startYear

            resultline = "%d\t%.0f\t$%.0f\t" % (year,self.BaseUnitsByYear[Y],self.BaseCostByYear[Y])
            waterUsage = 12.*self.WaterHeatMonthlyUsage
            if waterUsage>0:
                if self.WaterHeatType==self.BaseHeatType:
                    waterCost = waterUsage*(self.BaseCostByYear[Y]/self.BaseUnitsByYear[Y])
                elif self.WaterHeatType == self.HEAT_NAME_ELEC:
 #                  waterCost = waterUsage*WaterCostperUnit 
                    waterCost = waterUsage*self.STANDARD_PRICE_ELEC
                else:
                    waterCost = 0
                    print("WaterHeatType="+self.WaterHeatType)
                resultline += "%.0f\t$%.0f\t" % (waterUsage,waterCost )  
            if BLAC:
                resultline += "%.0f\t$%.0f\t" % (self.BLAC_KWhByYear[Y],self.BLAC_KWhByYear[Y]*self.STANDARD_PRICE_ELEC)
        
            resultline += " |  "

            if len(self.HPChoice)>0:
                COPAve = self.BaseUnitsByYear[Y]*self.BaseHvacEfficiency*(self.BaseEnergyContent/ENERGY_CONTENT_ELEC)/self.KWhByYear[Y]
                resultline += "%.0f\t$%.0f\t%.1f\t" % (self.KWhByYear[Y],self.KWhByYear[Y]*self.STANDARD_PRICE_ELEC,COPAve)

            HPWaterUnits = 0
            if self.HPWaterHeaterCOP>0:
                HPWaterUnits = 12.*self.WaterHeatMonthlyUsage*self.WaterEnergyContent/ENERGY_CONTENT_ELEC/self.HPWaterHeaterCOP
                if self.WaterHeatCombinedBill:
                    HPWaterUnits *= self.BaseHvacEfficiency
                resultline += "%.0f\t$%.0f\t" % (HPWaterUnits,HPWaterUnits*self.STANDARD_PRICE_ELEC)

            resultline += " |  "

            if len(self.HPChoice)>0 or self.SuppHeatType!=self.BaseHeatType:
                resultline += "%d\t%.0f\t$%.0f\t" % (self.SuppUsesByYear[Y],self.SuppUnitsByYear[Y],                
                                                    self.SuppUnitsByYear[Y]*self.SuppCostPerUnit)
        
                if len(self.HPChoice)>0:
                    if HPAC:
                        resultline += "%.0f\t$%.0f" % (self.HPAC_KWhByYear[Y],self.HPAC_KWhByYear[Y]*self.STANDARD_PRICE_ELEC)
            
            resultline += "\n"
            
            results += resultline

            if len(self.HPChoice)>0 or self.SuppHeatType!=self.BaseHeatType:
                totSavings += self.BaseCostByYear[Y] - (self.KWhByYear[Y]*self.STANDARD_PRICE_ELEC + self.SuppUnitsByYear[Y]*self.SuppCostPerUnit) 
            if BLAC or HPAC :
                totSavings += (self.BLAC_KWhByYear[Y]-self.HPAC_KWhByYear[Y]) * self.STANDARD_PRICE_ELEC
            if self.HPWaterHeaterCOP>0:
                totSavings += 12.*self.WaterHeatMonthlyUsage * self.WaterCostPerUnit - HPWaterUnits*self.STANDARD_PRICE_ELEC
            
            totBaseEmissions += self.BaseKgCO2PerUnit*self.BaseUnitsByYear[Y]
            totBLHWEmissions += self.WaterKgCO2PerUnit*waterUsage
            if len(self.HPChoice)>0 or self.SuppHeatType!=self.BaseHeatType:
                totHPEmissions   += self.ElecKgCO2PerUnit*self.KWhByYear[Y]
                totSuppEmissions += self.SuppKgCO2PerUnit*self.SuppUnitsByYear[Y]
            if BLAC or HPAC:
                totBLACEmissions += self.BLAC_KWhByYear[Y]*self.ElecKgCO2PerUnit
                totHPACEmissions += self.HPAC_KWhByYear[Y]*self.ElecKgCO2PerUnit
            totHPHWEmissions += HPWaterUnits*self.ElecKgCO2PerUnit
    
        if totSavings>0 :
            savingsImpact = "saved"
        else:
            savingsImpact = "cost an additional"
        
        CO2_percent_impact = 0
        if len(self.HPChoice)>0 or self.SuppHeatType!=self.BaseHeatType:
            CO2_percent_impact += (100.*(totBaseEmissions  - totHPEmissions - totSuppEmissions))
        if BLAC or HPAC:
            CO2_percent_impact += (100.*(totBLACEmissions- totHPACEmissions))
        if totHPHWEmissions > 0:
            CO2_percent_impact += 100.*(totBLHWEmissions - totHPHWEmissions)
        CO2_percent_impact /= (totBaseEmissions+totBLACEmissions+totBLHWEmissions)
        if CO2_percent_impact>0 : 
            CO2Impact = "less"
        else:
            CO2Impact = "more"

        if len(self.HPChoice)>0:
            change = "heat pump system"
        elif self.HPWaterHeaterCOP>0:
            change = "heat pump water heater"
        elif self.SuppHeatType!=self.BaseHeatType:
            change = "change to "+self.SuppHeatType
        results += "\nOver the years %d-%d, the %s would have %s $%.0f, emitting %.0f%% %s CO2eq than %s\n" % (startYear+1,endYear-1,change,savingsImpact, abs(totSavings), CO2_percent_impact, CO2Impact,self.BaseHeatType)

        analyzeExtremes = True
        if len(self.HPChoice)>0 and analyzeExtremes:
            for year in (AverageHDDYear, HighestHDDYear) :
            # average year first
                self.LoadTempDataRaw(status,year)
                self.heatPumpPerformance(year)

                totBaseEmissions = self.BaseKgCO2PerUnit*self.BaseUnitsByYear[0]
                totBLHWEmissions = self.WaterKgCO2PerUnit*waterUsage
                totBLACEmissions = self.BLAC_KWhByYear[0]*self.ElecKgCO2PerUnit
                totHPEmissions   = self.ElecKgCO2PerUnit*self.KWhByYear[0]
                totHPACEmissions = self.HPAC_KWhByYear[0]*self.ElecKgCO2PerUnit
                totHPHWEmissions = HPWaterUnits*self.ElecKgCO2PerUnit
                totSuppEmissions = self.SuppKgCO2PerUnit*self.SuppUnitsByYear[0]

                totSavings = self.BaseCostByYear[0] - (self.KWhByYear[0]*self.STANDARD_PRICE_ELEC + self.SuppUnitsByYear[0]*self.SuppCostPerUnit) 
                if BLAC or HPAC :
                    totSavings += (self.BLAC_KWhByYear[0]-self.HPAC_KWhByYear[0]) * self.STANDARD_PRICE_ELEC
                if totSavings>0 :
                    savingsImpact = "saved"
                else:
                    savingsImpact = "cost an additional"
    
                CO2_percent_impact = (100.*(totBaseEmissions + totBLACEmissions - totHPEmissions - totSuppEmissions- totHPACEmissions))
                if totHPHWEmissions > 0:
                    CO2_percent_impact += 100.*(totBLHWEmissions - totHPHWEmissions)
                CO2_percent_impact /= (totBaseEmissions+totBLACEmissions+totBLHWEmissions)
            
                if CO2_percent_impact>0 : 
                    CO2Impact = "less"
                else:
                    CO2Impact = "more"
    
                percentOfLoad = 100.* (self.totalRequiredHeating  - self.SuppUnitsByYear[0]*self.SuppEnergyContent)/self.totalRequiredHeating
            
                if year == AverageHDDYear:
                    self.HeatPumpAverageUnits = self.KWhByYear[0] + self.HPAC_KWhByYear[0]
                    self.BaseAverageUnits = self.BaseUnitsByYear[0]
                    if self.HPWaterHeaterCOP>0 :
                        self.HeatPumpAverageUnits += HPWaterUnits
                        self.BaseAverageUnits += waterUsage
                    if BLAC:
                        self.BLACAverageUnits = self.BLAC_KWhByYear[0]
                    else:
                        self.BLACAverageUnits = 0.
                    
                    self.SuppAverageUnits = self.SuppUnitsByYear[0]
                    adj = "Average"
                else:
                    adj = "Coldest"
                results += "%s heating year (%d), heat pump covers " % (adj,year)
                results += "%.1f%% of heating load, %s $%.0f, " % (percentOfLoad,savingsImpact,abs(totSavings))
                results += "emits %.0f%% %s CO2 than %s\n" % (CO2_percent_impact,CO2Impact,self.BaseHeatType)
            
            self.updateTemp = True

        status.config(text="Saving results")
        status.update()
        self.outputData(results)

        if len(self.HPChoice)>0:
            self.updateGraph = True

        return results
        
    def isHeating(self,t) :
# Author: Jonah Kadoko
# this function determines if the heat pump should heat the room at this particular time
# Reasons why your heat pump may not turn ON include, but not limited to the following,:
# 1, The outdoor temp is lower than the min operating temp of the heat pump
# 2, It is in the summer time before your specified turn_ON_Date and after the turn_OFF_Date
# 3, The heat pump overshoot for that particular hour and so is cycling (not much modelling has been done to simumlate cycling)

        if self.t_Data[t] <= datetime.datetime(self.t_Data[t].year, self.turn_OFF_Date.month, self.turn_OFF_Date.day) :
            self.current_Heating_Year = self.t_Data[t].year - 1    
        else:
            self.current_Heating_Year = self.t_Data[t].year
    
        self.yr_Turn_OFF = datetime.datetime(self.current_Heating_Year + 1, self.turn_OFF_Date.month, self.turn_OFF_Date.day)
        self.yr_Turn_ON = datetime.datetime(self.current_Heating_Year, self.turn_ON_Date.month, self.turn_ON_Date.day)

#    if (t_Data[t_Start] <= t_Data[t]) and (t_Data[t] <= yr_Turn_OFF) and \
#    (yr_Turn_ON <= t_Data[t]) and (t_Data[t] <= t_Data[t_End]) and (T_Outdoor[t] < WinterHPSetPoint) :
        if (self.t_Data[t] <= self.yr_Turn_OFF) and (self.yr_Turn_ON <= self.t_Data[t]) and (self.T_Outdoor[t] < self.WinterHPSetPoint) :
        # t is within range of the heating period and purchase period and the outdoor temperature is below the indoor temperature
            return True
        else:
            return False    
            
    def isCooling(self,t) :

# this function determines if the cooling should be applied at this time
# Reasons why your heat pump may not turn ON include, but not limited to the following,:
# 1, The outdoor temp is lower than the min operating temp of the heat pump
# 2, It is in the summer time before your specified turn_ON_Date and after the turn_OFF_Date
# 3, The heat pump overshoot for that particular hour and so is cycling (not much modelling has been done to simumlate cycling)

        if self.t_Data[t] <= datetime.datetime(self.t_Data[t].year, self.turn_OFF_Date.month, self.turn_OFF_Date.day) :
            self.current_Heating_Year = self.t_Data[t].year - 1    
        else:
            self.current_Heating_Year = self.t_Data[t].year
    
        self.yr_Turn_OFF = datetime.datetime(self.current_Heating_Year + 1, self.turn_OFF_Date.month, self.turn_OFF_Date.day)
        self.yr_Turn_ON = datetime.datetime(self.current_Heating_Year, self.turn_ON_Date.month, self.turn_ON_Date.day)

        if (self.T_Outdoor[t] > self.SummerHPSetPoint) :
        # t is within range of the heating period and purchase period and the outdoor temperature is below the indoor temperature
            return True
        else:
            return False        
    
    def approxResistance(self):
    # Adapted from VBA project, Author: Jonah Kadoko
    # Decide the hour to start and stop the calculations
    # 1, t_Start should be the index of time corresponding to the second purchase date (since the customer fills up their tank each time)
    # 2, t_End should be  the date corresponding the last purchase date
    
        p = 0
        self.approx_Resistance.clear()
        while True:
            self.approx_Resistance.append([0,0])
            p+=1
            if p==self.numDeliveries: break

        t = 0    
        self.t_Start = self.t_End = 0
 
        p = self.numDeliveries-1
        self.last_Purchase = p
        if self.purchase_Quantity[p] == 0 :
            self.last_Purchase = p - 1
    
        while t<len(self.t_Data):    # (t_Start == 0) or (t_End == 0):
            if (self.t_Start==0):
                if self.purchase_Date[0] == self.t_Data[t].date() :
                # All calculations should start a day after the customer fills up their tank around the start of the year
                # t_Start is the index of the time the customer fi
                    self.t_Start = t

            elif (self.t_End==0 and self.purchase_Date[self.last_Purchase] == self.t_Data[t].date()) :
            # calculations should stop at the last purchase date of the year
                self.t_End = t
                break

            t = t + 1

        if self.t_End==0 :
            self.t_End = len(self.t_Data)-1
        
        startYear = self.t_Data[self.t_Start].year
        endYear = self.t_Data[self.t_End].year
        self.BaseUnitsByYear.clear()
        self.BaseCostByYear.clear()
        for year in range(startYear,endYear+1):
            self.BaseUnitsByYear.append(0.0)
            self.BaseCostByYear.append(0.0)

        # Calculate total annual delta T
        delta_T = 0.0
        for t in range(self.t_Start,self.t_End) :
            if self.isHeating(t):
                delta_T = delta_T + (self.WinterHPSetPoint - self.T_Outdoor[t])

        # Calculate the total oil used
        total_Vol = 0.0
        prevDate = self.purchase_Date[0]
        for p in range(0, self.last_Purchase):
            if self.BaseHeatType == self.WaterHeatType and self.WaterHeatMonthlyUsage>0 :
                purchasePeriod = (self.purchase_Date[p] - prevDate)
                days = purchasePeriod.days
                months = days * (12./365)
                WaterFuelInPeriod = self.WaterHeatMonthlyUsage * months
            else:
                WaterFuelInPeriod = 0.
        
            prevDate = self.purchase_Date[p]
            year = self.purchase_Date[p].year
            Y = year - startYear
            if year <= endYear:
                Quantity_Used = (self.purchase_Quantity[p]-WaterFuelInPeriod)
                total_Vol += Quantity_Used
                self.BaseUnitsByYear[Y] += Quantity_Used
                self.BaseCostByYear[Y] += self.purchase_Cost[p]*(Quantity_Used/self.purchase_Quantity[p])

        # Calculate the average resistance per heating period
        p = 0
        self.approx_Resistance[0][0] = self.t_Start
        self.approx_Resistance[0][1] = 0.0
        for t in range(self.t_Start,self.t_End):
        
            if self.BaseHeatType == self.WaterHeatType and self.WaterHeatMonthlyUsage>0 and p<len(self.purchase_Date)-2 :
                purchasePeriod = (self.purchase_Date[p+1] - self.purchase_Date[p])
                days = purchasePeriod.days
                months = days * (12./365)
                WaterFuelInPeriod = self.WaterHeatMonthlyUsage * months
            else:
                WaterFuelInPeriod = 0.
            Quantity_Used = (self.purchase_Quantity[p]-WaterFuelInPeriod)

            ti = t-self.t_Start
            dateTime = self.t_Data[t]
            year = dateTime.year
            Y = year - startYear
        
            thisDate = self.t_Data[t].date()
            if self.isHeating(t) and (self.purchase_Date[p] <= thisDate) and (thisDate <= self.purchase_Date[p + 1]) and (p<self.last_Purchase):

                # Sum app eligible delta_T during each heating period
                self.approx_Resistance[p][1] += (self.WinterHPSetPoint - self.T_Outdoor[t]) / 
                                                (self.BaseHvacEfficiency * Quantity_Used * self.BaseEnergyContent)
            else:
                if self.isHeating(t) and (self.purchase_Date[p + 1] <= thisDate) and (thisDate <= self.purchase_Date[self.last_Purchase]) and (p < self.last_Purchase): 
                # this particular time sample belongs to the next purchase period
                    p = p + 1
                    self.approx_Resistance[p][0] = t
                    self.approx_Resistance[p][1] =  (self.WinterHPSetPoint - self.T_Outdoor[t]) / 
                                                    (self.BaseHvacEfficiency * Quantity_Used * self.BaseEnergyContent)
 
    # Average resistance during the heating period
        self.average_Resistance = delta_T / (self.BaseHvacEfficiency * self.BaseEnergyContent * total_Vol)

    def heatPumpPerformance(self,h):
    #Author: Jonah Kadoko
    #this function calculates the approximate min, and max heating capacity, COPave and average electrical consumption
    #One would expect that the required heat be in between the max and min heating capacities

# argument h: 0 - analyze data for the years provided
#             other - analyze performance for year h
        use_Average_R = True
    
        p = 0
    
        self.KWhByYear.clear()
        self.HPAC_KWhByYear.clear()
        self.BLAC_KWhByYear.clear()
        self.SuppUnitsByYear.clear()
        self.SuppUsesByYear.clear()

        if h==0:
            startYear = self.t_Data[self.t_Start].year
            endYear = self.t_Data[self.t_End].year
        
            self.timeArray = [self.t_Data[t] for t in range(self.t_Start,self.t_End)]
            self.Q_required = [0.0 for t in range(self.t_Start, self.t_End)]
            self.QC_required = [0.0 for t in range(self.t_Start, self.t_End)]
            self.capacity_Max = [-1.0 for t in range(self.t_Start,self.t_End)]
            self.capacity_Min = [0.0 for t in range(self.t_Start,self.t_End)]
            self.electric_Required = [0.0 for t in range(self.t_Start,self.t_End)]
            self.supplemental_Heat = [0.0 for t in range(self.t_Start,self.t_End)]
            self.COP_Ave = [0.0 for t in range(self.t_Start,self.t_End)]
        else:

            startYear = endYear = h
            self.t_Start = 0
            self.t_End = len(self.t_Data)

            self.timeArray1 = [self.t_Data[t] for t in range(self.t_Start,self.t_End)]
            self.Q_required1 = [0.0 for t in range(self.t_Start, self.t_End)]
            self.QC_required1 = [0.0 for t in range(self.t_Start, self.t_End)]
            self.capacity_Max1 = [-1.0 for t in range(self.t_Start,self.t_End)]
            self.capacity_Min1 = [0.0 for t in range(self.t_Start,self.t_End)]
            self.electric_Required1 = [0.0 for t in range(self.t_Start,self.t_End)]
            self.supplemental_Heat1 = [0.0 for t in range(self.t_Start,self.t_End)]
            self.COP_Ave1 = [0.0 for t in range(self.t_Start,self.t_End)]

            self.BaseUnitsByYear[0] = 0.
            self.BaseCostByYear[0] = 0.
 
        supplementalLastDate = self.t_Data[0]   # for determining how many supplemental days there are
        oldYear = 1900

        self.totalRequiredHeating = 0.
        self.totalRequiredCooling = 0.
    
        for t in range(self.t_Start,self.t_End):
            ti = t-self.t_Start
            if h==0:
                dateTime = self.timeArray[ti]
            else:
                dateTime = self.timeArray1[ti]
            
            year = dateTime.year
            Y = year - startYear
        
            if year > oldYear:
                oldYear = year
                self.KWhByYear.append(0.0)
                self.SuppUnitsByYear.append(0.0)
                self.SuppUsesByYear.append(0)
                self.BLAC_KWhByYear.append(0.0)
                self.HPAC_KWhByYear.append(0.0)
           
            # Calculate the perfomance
            if (use_Average_R) : 
                resistance = self.average_Resistance            
            else :
                resistance = self.approx_Resistance[p][1]

            temp = self.T_Outdoor[t]
            CAP_Max = 0
            CAP_Min = 0  
            COP_Min = []
            COP_Max = []
            np = len(self.HPChoice)

            for hp in self.HPChoice:
                CAP_Max += hp.MaxCapacity(temp)
                CAP_Min += hp.MinCapacity(temp)
            
                COP_Min.append(hp.COPatMinCapacity(temp))
                COP_Max.append(hp.COPatMaxCapacity(temp))

            if self.isHeating(t):
                heating_required = (self.WinterHPSetPoint - temp)/ resistance
                cooling_required = 0.            
            elif self.isCooling(t):
                heating_required = 0.
                cooling_required = (temp - self.SummerHPSetPoint)/ resistance

            if h==0:
                self.Q_required[ti] = heating_required
                self.QC_required[ti]= cooling_required
                self.capacity_Max[ti] = CAP_Max
                self.capacity_Min[ti] = CAP_Min
            
            self.totalRequiredHeating += heating_required
            self.totalRequiredCooling += cooling_required

            COPave = 0.0        
                        
        # calculate the average values of the above
        # Linear interpolation, doesn't work well
        # COP_Ave(t, h) = (Q_required(t) - capacity_Min(t, h)) * (COP_Max - COP_Min) / (capacity_Max(t, h) - capacity_Min(t, h)) + COP_Min          
        # Weighted average works better
#        c = (abs(Q_required[t] - capacity_Min[t]) * COP_Min + abs(Q_required[t] - capacity_Max[t]) * COP_Max)

        # for years with purchase data - use purchase data for baseline units and cost
        # for analysis of average and extreme, back-calculate what we would have used
            if h!= 0:
                self.BaseUnitsByYear[Y] += heating_required/self.BaseHvacEfficiency/self.BaseEnergyContent
                self.BaseCostByYear[Y] += self.BaseCostPerUnit*heating_required/self.BaseHvacEfficiency/self.BaseEnergyContent
        
            # Note times where the heat pump cannot meet demand
            if len(self.HPChoice)==0 or temp<self.SuppOutdoorTempNABL:

                supplemental_required = heating_required
            
                if h==0:
                    self.supplemental_Heat[ti] = supplemental_required

                self.SuppUnitsByYear[Y] += supplemental_required/self.SuppHvacEfficiency/self.SuppEnergyContent

                # is this a new supplemental usage (within 24 hours of the past one)
                deltaTime = dateTime - supplementalLastDate
                if deltaTime>datetime.timedelta(1,0)  : #timeDelta(0,0,1,0,0)
                    supplementalLastDate = dateTime
                    self.SuppUsesByYear[Y] += 1

            elif (heating_required > CAP_Max) :
                for i in range(np): 
                    COPave += COP_Max[i]/np
                
                supplemental_required = heating_required - CAP_Max
            
                if h==0:
                    self.supplemental_Heat[ti] = supplemental_required

                self.SuppUnitsByYear[Y] += supplemental_required/self.SuppHvacEfficiency/self.SuppEnergyContent
            
                
                # is this a new supplemental usage (within 24 hours of the past one)
                deltaTime = dateTime - supplementalLastDate
                if deltaTime>datetime.timedelta(1,0)  : #timeDelta(0,0,1,0,0)
                    supplementalLastDate = dateTime
                    self.SuppUsesByYear[Y] += 1
                
                # The amount of electricity required to heat the area with Q_required BTUs
                electric_required = CAP_Max / COPave/ENERGY_CONTENT_ELEC
            
                if h==0:
                    self.electric_Required[ti] = electric_required
                
                self.KWhByYear[Y] += electric_required
        
            else:
                if (heating_required < CAP_Min):
                    for i in range(np):                
                        COPave += COP_Min[i]/np
            
                else:
                    #Linear interpolation, doesn't work well
                    #COP_Ave[t] = ((abs(Q_required[t] - capacity_Min[t]) * COP_Min + \
                    #    abs(Q_required[t] - capacity_Max[t]) * COP_Max)) / abs(capacity_Max[t] - capacity_Min[t]) 
                    for i in range(np):                
                        COPave += COP_Min[i] + ((heating_required - CAP_Min) * (COP_Max[i] - COP_Min[i])) / (CAP_Max - CAP_Min) /np
                
                # The amount of electricity required to heat the area with Q_required BTUs
                electric_required = heating_required / COPave /ENERGY_CONTENT_ELEC     
                self.KWhByYear[Y] += electric_required
                if h==0:
                    self.electric_Required[ti] = electric_required
                
            if self.BaselineAC != 0 and self.BaselineSEER>0:
                self.BLAC_KWhByYear[Y] += cooling_required / self.BaselineSEER/1000.

            if len(self.HPChoice)>0 and cooling_required > 0 :
                # weighted average SEER based on fraction of total capacity at 47 degrees
                HPSEER = 0.
                CAPTOTAL = 0.
                for hp in self.HPChoice:
                    HPSEER += float(hp.SEER) * hp.MaxCapacity(47)
                    CAPTOTAL += hp.MaxCapacity(47)
                HPSEER = HPSEER/CAPTOTAL
                 
                if HPSEER>0.:
                    self.HPAC_KWhByYear[Y] += cooling_required / HPSEER/1000.
                                    
    def outputData(self,results):
        # This routine outputs all results to a text file
    
        hpNames = ""
        for hp in self.HPChoice :
            hpNames += hp.Manufacturer +'-' +hp.OutdoorUnit 
        
        outputFile = './Output Data/Heat Pump Analysis.txt'
        output = open(outputFile,'w')
           
        output.write('Analysis for: '+hpNames +'\r')    
 
        output.write(results)
        output.close()
    
