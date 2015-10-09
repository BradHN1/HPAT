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

# to do:
# thermal resistance - improve calculation robustness
# generalize to natural gas for comparison
# HVAC efficiency a settable parameter for comparison
# programmable thermostats for baseline system for comparison
# dual fuel system
# heat pump cooling

# matplotlib figure plotting library
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2TkAgg
#from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from matplotlib import pyplot as plt

import matplotlib.dates as mdates
import matplotlib.ticker as mticker

import numpy as np

# tkinter user interface library
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from CalendarDialog import *
from getInput import *

from HeatPump import *          # new heat pump class

from datetime import datetime, date, time
from pylab import *

LARGE_FONT = ("Verdana",20)
NORM_FONT = ("Helvetica",16)
SMALL_FONT = ("Helvetica",13)
style.use("ggplot")

# globals

# Heat pump parameters

HPList = []         # list of all defined heat pumps
HPChoice = []       # new: list of chosen heat pumps (objects from HPList, can be repeated)

# Heating system types

HEAT_TYPE_OIL = 0
HEAT_NAME_OIL = "Fuel Oil"
STANDARD_PRICE_OIL = 3.20                               # Dec 2014 price - varied substantially in 2015
EFFICIENCY_HVAC_OIL = 0.75
UNITS_OIL = "Gallons"
ENERGY_CONTENT_OIL = 139000                             # from http://www.engineeringtoolbox.com/energy-content-d_868.html
KGCO2_PER_UNIT_OIL = 72.93*1e-6*ENERGY_CONTENT_OIL

HEAT_TYPE_GAS = 1
HEAT_NAME_GAS = "Natural Gas"
STANDARD_PRICE_GAS = 0.01447                            # average MA price 2015
EFFICIENCY_HVAC_GAS = 0.90
UNITS_GAS = "SCF"
ENERGY_CONTENT_GAS = 1050                               # listed as 950-1150 from http://www.engineeringtoolbox.com/energy-content-d_868.html
KGCO2_PER_UNIT_GAS = 53.06*1e-6*ENERGY_CONTENT_GAS      # http://www.epa.gov/climateleadership/documents/emission-factors.pdf

HEAT_TYPE_ELEC = 2
HEAT_NAME_ELEC = "Electric Resistance"
STANDARD_PRICE_ELEC = 0.15
EFFICIENCY_HVAC_ELEC = 0.75
UNITS_ELEC = "KWh"
ENERGY_CONTENT_ELEC = 3412                              # from http://www.engineeringtoolbox.com/energy-content-d_868.html
KGCO2_PER_UNIT_ELEC = (722/2.2)*1e-3

HEAT_TYPE_LPG = 3
HEAT_NAME_LPG = "Propane"
STANDARD_PRICE_LPG = 3.105                              # average Ma LPG price 2015
EFFICIENCY_HVAC_LPG = 0.75
UNITS_LPG = "Gallons"
ENERGY_CONTENT_LPG = 91330                              # from http://www.engineeringtoolbox.com/energy-content-d_868.html
KGCO2_PER_UNIT_LPG = 62.*1e-6*ENERGY_CONTENT_LPG

HEAT_TYPE_OTHER = 4
HEAT_NAME_OTHER = "????"
STANDARD_PRICE_OTHER = 999
EFFICIENCY_HVAC_OTHER = 1.0
UNITS_OTHER = "???"
ENERGY_CONTENT_OTHER = 1
KGCO2_PER_UNIT_OTHER = 0

# Baseline heating scenario - for which the usage data applies
BaseHeatType = HEAT_NAME_OIL
BaseHvacEfficiency = EFFICIENCY_HVAC_OIL
BaseEnergyContent = ENERGY_CONTENT_OIL     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
BaseEnergyUnits = UNITS_OIL
BaseKgCO2PerUnit = KGCO2_PER_UNIT_OIL
BaseCostPerUnit = STANDARD_PRICE_OIL

# supplemental system - augments the HeatPump system to meet necessary capacity
SuppHeatType = BaseHeatType
SuppHvacEfficiency = BaseHvacEfficiency
SuppEnergyContent = BaseEnergyContent     
SuppEnergyUnits = BaseEnergyUnits
SuppKgCO2PerUnit = BaseKgCO2PerUnit
SuppCostPerUnit = BaseCostPerUnit

# water heating system - augments the HeatPump system to meet necessary capacity
WaterHeatType = BaseHeatType
WaterHeatEfficiency = BaseHvacEfficiency
WaterEnergyContent = BaseEnergyContent
WaterEnergyUnits = BaseEnergyUnits
WaterKgCO2PerUnit = BaseKgCO2PerUnit
WaterCostPerUnit = BaseCostPerUnit
WaterHeatMonthlyUsage = 24              # in WaterEnergyUnits - which if same as BaseEnergyUnits are subtracted from heat load

#DehumidifierUsage
# ACUsage

ElecKgCO2PerUnit = KGCO2_PER_UNIT_ELEC

T_Outdoor = [] # (1 To SITE_DATA_MAX) As Single ' outdoor temperature
# T_Indoor = 65  #  As Single 'indoor temperaure as provided by the user
WinterHPSetPoint = 65
SummerHPSetPoint = 78
WinterBLSetPoint = WinterHPSetPoint
SummerBLSetPoint = SummerHPSetPoint
BaselineAC = 0      # none
BaselineSEER = 0

# times at which the temperature data was taken, this includes date and time
t_Data = []    # (1 To SITE_DATA_MAX) As Date 
t_Start = 0
t_End = 0

# Customer Specific parameters
fuelDeliveryHeader = ""
purchase_Date = []
purchase_Quantity = []
purchase_Cost = []
numDeliveries = 0
last_Purchase = -1
current_Heating_Year = 2003         # at the very least, current heating year

#turn_ON_Date  = datetime.date(2015,10,15)   # As Date # winter time on which the customer is likely to turn the HVAC
#turn_OFF_Date  = datetime.date(2015,5,15)  # As Date # turn off HVAC heating
turn_ON_Date  = datetime.date(2015,9,15)   # As Date # winter time on which the customer is likely to turn the HVAC
turn_OFF_Date  = datetime.date(2015,6,1)  # As Date # turn off HVAC heating

# average resistance is calculated per purchase period
approx_Resistance = [] # (1 To PURCHASES_MAX, 1 To 2) As Double 
average_Resistance = -1.0

# arrays indexed by time (calculated from temperature vs time data)
timeArray = []
Q_required = []         # Double # based on resistance and outdoor temperatures only
QC_required = []         # Double # based on resistance and outdoor temperatures only
electric_Required = []  # Min consumption, Approximate requirement, Max consumption (for each heat pump)

capacity_Max = []       # maximum capacity of each heat pump in the heating period
capacity_Min = []       # minimum capacity of each heat pump in the heating period
supplemental_Heat = []  # additional heat required to meet heating requirements per hour
COP_Ave = []            #  
baselineAC_pwr = []
heatpumpAC_pwr = []

KWhByYear = []
SuppUnitsByYear = []
SuppUsesByYear = []
BaseUnitsByYear = []
BaseCostByYear = []
BLAC_KWhByYear = []
HPAC_KWhByYear = []
  
updateGraph = False
updateTemp = True
updateResistance = True

#f = Figure(figsize=(10,6), dpi=100)
#a = f.add_subplot(111)
f = plt.figure()
a = plt.subplot2grid((3,3), (0,0), rowspan=3, colspan=3)

#f1 = Figure(figsize=(3,2), dpi=100)
#a1 = f1.add_subplot(111)
f1 = plt.figure()
a1 = plt.subplot2grid((9,3), (0,0), rowspan = 4, colspan = 3)
a1.set_ylabel('COP')
a1.set_ylim(0.,5.)
a1.set_autoscalex_on(False)
a1.set_autoscaley_on(False)
a1.set_xlim(-20.,60.)
firstPlot = True

a2 = plt.subplot2grid((9,3), (5,0), rowspan = 4, colspan = 3, sharex=a1)
a2.set_ylabel('Capacity')
a2.set_xlabel('Outdoor Temp (deg F)')
a2.set_ylim(0.,50000.)
a2.set_autoscalex_on(False)
a2.set_autoscaley_on(False)
plt.grid(True)

f3 = plt.figure()
a3 = plt.subplot2grid((3,3), (0,0), rowspan = 4, colspan = 3)
a3.set_ylabel('Quantity')
a3.set_xlabel('Date')
a3.set_ylim(0.,50000.)
a3.set_autoscalex_on(True)
a3.set_autoscaley_on(True)
plt.grid(True)

def popupmsg(title, msg):
    
    popup = tk.Tk()
    popup.wm_title(title)
    label = ttk.Label(popup,text=msg,font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1=ttk.Button(popup, text="OK",command=popup.destroy)
    B1.pack()
    popup.mainloop()    

def SetBLScenario(BLT) :
    global BaseHeatType,BaseHvacEfficiency,BaseEnergyContent,BaseEnergyUnits,BaseKgCO2PerUnit,BaseCostPerUnit
    global SuppHeatType,SuppHvacEfficiency,SuppEnergyContent,SuppEnergyUnits,SuppKgCO2PerUnit,SuppCostPerUnit
    global UpdateResistance
    
    if BLT == HEAT_TYPE_OIL :    # oil
        BaseHeatType = HEAT_NAME_OIL
        BaseHvacEfficiency = EFFICIENCY_HVAC_OIL
        BaseEnergyContent = ENERGY_CONTENT_OIL     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
        BaseEnergyUnits = UNITS_OIL
        BaseKgCO2PerUnit = KGCO2_PER_UNIT_OIL
        BaseCostPerUnit = STANDARD_PRICE_OIL
    elif BLT == HEAT_TYPE_GAS : # natural gas
        BaseHeatType = HEAT_NAME_GAS
        BaseHvacEfficiency = EFFICIENCY_HVAC_GAS
        BaseEnergyContent = ENERGY_CONTENT_GAS     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
        BaseEnergyUnits = UNITS_GAS
        BaseKgCO2PerUnit = KGCO2_PER_UNIT_GAS
        BaseCostPerUnit = STANDARD_PRICE_GAS
    elif BLT == HEAT_TYPE_ELEC : # electric
        BaseHeatType = HEAT_NAME_ELEC
        BaseHvacEfficiency = EFFICIENCY_HVAC_ELEC
        BaseEnergyContent = ENERGY_CONTENT_ELEC     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
        BaseEnergyUnits = UNITS_ELEC
        BaseKgCO2PerUnit = KGCO2_PER_UNIT_ELEC
        BaseCostPerUnit = STANDARD_PRICE_ELEC
    elif BLT == HEAT_TYPE_LPG : # propane
        BaseHeatType = HEAT_NAME_LPG
        BaseHvacEfficiency = EFFICIENCY_HVAC_LPG
        BaseEnergyContent = ENERGY_CONTENT_LPG     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
        BaseEnergyUnits = UNITS_LPG
        BaseKgCO2PerUnit = KGCO2_PER_UNIT_LPG
        BaseCostPerUnit = STANDARD_PRICE_LPG
    else:
        gs = GetString("Specify baseline energy source", default=HEAT_NAME_OIL)
        if gs.result:
            BaseHeatType = gs.result

            beu = BaseEnergyUnits = GetString("Specify units", default=UNITS_OIL)
            BaseEnergyUnits = beu.result
            
            buc = GetFloat("Standard unit price [2015] ($)", default=STANDARD_PRICE_OIL, min=0., max=1000.)
            BaseCostPerUnit = buc.result

            bhe = GetFloat("System efficiency (%)", default=100*EFFICIENCY_HVAC_OIL, min=1., max=100.)
            BaseHvacEfficiency = bhe.result * 0.01
            
            bhc = GetFloat("Energy content (BTU per unit)", default=ENERGY_CONTENT_OIL, min=1e-6, max=1e9)
            BaseEnergyContent = bhc.result

            bhk = GetFloat("CO2 emmissions (kg CO2 per unit)", default=KGCO2_PER_UNIT_OIL, min=1e-6, max=1e9)
            BaseKgCO2PerUnit = bhk.result
            
        else:
            BaseHeatType = HEAT_NAME_OIL
            BaseHvacEfficiency = EFFICIENCY_HVAC_OIL
            BaseEnergyContent = ENERGY_CONTENT_OIL     # from http://www.engineeringtoolbox.com/energy-content-d_868.html
            BaseEnergyUnits = UNITS_OIL
            BaseKgCO2PerUnit = KGCO2_PER_UNIT_OIL
            BaseCostPerUnit = STANDARD_PRICE_OIL
        print("Other baseline heating types not supported")
    print("Baseline scenario chosen: "+BaseHeatType)

    # for now, assume supplemental system is same as the baseline system
    SuppHeatType = BaseHeatType
    SuppHvacEfficiency = BaseHvacEfficiency
    SuppEnergyContent = BaseEnergyContent     
    SuppEnergyUnits = BaseEnergyUnits
    SuppKgCO2PerUnit = BaseKgCO2PerUnit
    SuppCostPerUnit = BaseCostPerUnit
    
    updateResistance = True

def SetBLWScenario(BLT) :
    global WaterHeatType
    global UpdateResistance
    
    if BLT == HEAT_TYPE_OIL :    # oil
        WaterHeatType = HEAT_NAME_OIL
    if BLT == HEAT_TYPE_ELEC :    # oil
        WaterHeatType = HEAT_NAME_ELEC
    if BLT == HEAT_TYPE_GAS :    # oil
        WaterHeatType = HEAT_NAME_GAS
    if BLT == HEAT_TYPE_LPG :    # oil
        WaterHeatType = HEAT_NAME_LPG
    elif BLT == HEAT_TYPE_OTHER : 
        gs = GetString("Specify water energy source", default=HEAT_NAME_OIL)
        if gs.result:
            WaterHeatType = gs.result
            
        else:
            waterHeatType = BaseHeatType
        print("Other baseline heating types not supported")
    print("Water scenario chosen: "+WaterHeatType)

    # for now, assume supplemental system is same as the baseline system
    SuppHeatType = BaseHeatType
    SuppHvacEfficiency = BaseHvacEfficiency
    SuppEnergyContent = BaseEnergyContent     
    SuppEnergyUnits = BaseEnergyUnits
    SuppKgCO2PerUnit = BaseKgCO2PerUnit
    SuppCostPerUnit = BaseCostPerUnit
    
    UpdateResistance = True

def SetBLAScenario(BLA) :
    global BaselineAC
    global UpdateResistance
    
    if BLA == 0 :    # none
        BaselineAC = 0
    if BLA == 1 :    # window units, how many
        BaselineAC = 1
    if BLA == 2 :    # central
        BaselineAC = 2

def loadFuelDeliveries(purchasesFile):

    # this was take from previous code tested using First Parish oil purchases
    # input = open('./Residential Profiles/FP Oil Deliveries.txt')
    global numDeliveries
    global fuelDeliveryHeader
    global UpdateTemp, UpdateResistance
        
    numDeliveries = 0
    fuelDeliveryHeader = ""
    purchase_Quantity.clear()
    purchase_Cost.clear()
    purchase_Date.clear()
    
    # read the purchases file
    
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
        fuelDeliveryHeader += lines[LN]
        LN += 1
        
        if lines[LN].find('Heat source: ')>=0 :
            HeatSource = lines[LN]
            if HeatSource.find(HEAT_NAME_OIL)>=0 :
                SetBLScenario(HEAT_TYPE_OIL)
            elif HeatSource.find(HEAT_NAME_GAS)>=0 :
                SetBLScenario(HEAT_TYPE_GAS)
            elif HeatSource.find(HEAT_NAME_ELEC)>=0 :
                SetBLScenario(HEAT_TYPE_ELEC)
            elif HeatSource.find(HEAT_NAME_LPG)>=0 :
                SetBLScenario(HEAT_TYPE_LPG)
            
        if lines[LN].find('$$')>=0 :
            LN += 1 
            break;    # locate where the data starts
    print('====================')

    if BaseHeatType == HEAT_NAME_OIL:
        lastPrice = STANDARD_PRICE_OIL
    elif BaseHeatType == HEAT_NAME_GAS:
        lastPrice = STANDARD_PRICE_GAS
    elif BaseHeatType == HEAT_NAME_ELEC:
        lastPrice = STANDARD_PRICE_ELEC
    elif BaseHeatType == HEAT_NAME_LPG:
        lastPrice = STANDARD_PRICE_LPG
    
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
            lastPrice = cost/quantity
        elif quantity>0:
            cost = lastPrice*quantity 
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

        purchase_Quantity.append(quantity)
        purchase_Cost.append(cost)            
        purchase_Date.append(DeliveryDate)

        numDeliveries += 1

    UpdateTemp = True
    UpdateResistance = True
    
    return numDeliveries
def saveFuelDeliveries(purchasesFile):

    global numDeliveries 
    global fuelDeliveryHeader   

    # open the purchases file
    if numDeliveries<=0:
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
    for i in range(numDeliveries) :
        year = purchase_Date[i].year
        if oldYear!= year :
            oldYear = year
            outputstring += "%d\t" % year
        else :
            outputstring += "\t"
        
        day = purchase_Date[i].day
        month = purchase_Date[i].month
        year = purchase_Date[i].year % 100
        outputstring += "%d/%d/%02d\t" % (month, day, year)
        
        outputstring += "$%.2f\t" % purchase_Cost[i]
        outputstring += "%.1f\n" % purchase_Quantity[i]
        
    output.write(outputstring)
    output.close()
    
    return numDeliveries

def initializeData():
    global UpdateTemp, UpdateResistance
    # adapted from VBA initialize, author Jonah Kadoko
    # Initialize important counters

    workingDirectory = './Residential Profiles/'
    # filename = 'FP Oil Deliveries.txt'
    filename = 'Default Oil Deliveries.txt'
    purchasesFile = workingDirectory + filename
    numDeliveries = loadFuelDeliveries(purchasesFile)
    
    UpdateTemp = True
    UpdateResistance = True
    
def loadHeatPumps():

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
        HPList.append(heatPump)
    
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
#            CAPRated.append(tF(tokens[14]))
#            CAPRated.append(tF(tokens[24]))
#            CAPRated.append(tF(tokens[34]))
            CAPMax.append(tF(tokens[15]))
            CAPMax.append(tF(tokens[25]))
            CAPMax.append(tF(tokens[35]))
            
            COPMin.append(tF(tokens[19]))
            COPMin.append(tF(tokens[29]))
            COPMin.append(tF(tokens[39]))
#            COPRated.append(tF(tokens[20]))
#            COPRated.append(tF(tokens[30]))
#            COPRated.append(tF(tokens[40]))
            COPMax.append(tF(tokens[21]))
            COPMax.append(tF(tokens[31]))
            COPMax.append(tF(tokens[41]))
                
            if tokens[47] != 'N/A':
                tData.append(tF(tokens[47]))
                CAPMin.append(tF(tokens[48]))
#                CAPRated.append(tF(tokens[49]))
                CAPMax.append(tF(tokens[50]))
                COPMin.append(tF(tokens[54]))
#                COPRated.append(tF(tokens[55]))
                COPMax.append(tF(tokens[56]))
            
            heatPump.tData = tData
            heatPump.CAPMin = CAPMin
 #           heatPump.CAPRated = CAPRated 
            heatPump.CAPMax = CAPMax 
            heatPump.COPMin = COPMin
 #           heatPump.COPRated = COPRated
            heatPump.COPMax = COPMax
                   
#            heatPump.parametrize()
            
        except Exception as e:
            print(e)
                
def LoadTempDataRaw(status, year=0):
    
    T_Outdoor.clear()
    t_Data.clear()

    if year==0:
        yearStart = purchase_Date[0].year
        yearEnd = purchase_Date[-1].year
    else:
        yearStart = yearEnd = year
        
    prevTemp = -999
    oneHour = datetime.timedelta(0,0,0,0,0,1,0)
    
    # loop over files from these years
    ClimaticDataPath = './Climate Data/KBED'
    for year in range(yearStart,yearEnd+1):
        filename = "%s-%i.txt" % (ClimaticDataPath, year) 
        print("Reading "+filename)
        
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
                print ("4 exception " + str(sys.exc_info()))
                break

            try:
                temp = float(tokens[1])
            except:
                pass
                
            # record hourly data when the next dateTime point is past the nextHour to be recorded     
            while nextHour<dateTime :
                t_Data.append(nextHour)
                T_Outdoor.append(temp)                
                nextHour = nextHour+oneHour  
            
def LoadTempData():     # OBSOLETE
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
#            LN += year_Start.days - 1
            NextLN = LN+year_Start.days
            first = False;

        else :
            #Loop through the temperature data
            t_Data.append(dateTime)
            T_Outdoor.append(float(tokens[4]))

    print("Temperature data loaded")


def animate(i):
#    dataLink = 'http://btc-e.com/api/3/trades/btc_usd?limit=2000'
#    data = urllib.request.urlopen(dataLink)
#    data = data.readall().decode("utf-8")
#    data = json.loads(data)
#    data = data["btc_usd"]
#    data = pd.DataFrame(data)
    
#    buys = data[(data['type'] == "bid")]
#    buys["datestamp"]=np.array(buys["timestamp"]).astype("datetime64[s]")
#    buyDates = (buys["datestamp"]).tolist()
#    buyPrices = (buys["price"]).tolist()
    
#    sells = data[(data['type'] == "ask")]
#    sells["datestamp"]=np.array(sells["timestamp"]).astype("datetime64[s]")
#    sellDates = (sells["datestamp"]).tolist()
#    sellPrices = (sells["price"]).tolist()
    global updateGraph

    if len(HPChoice)>0 :
        hp = HPChoice[0]
    else:
        return
            
    if updateGraph :
    
#        a = plt.subplot2grid((6,4), (0,0), rowspan = 5, colspan = 4)
#        a2 = plt.subplot2grid((6,4), (5,0), rowspan = 1, colspan = 4, sharex = a)

        a.clear()
        a.plot_date(timeArray,Q_required, "g", label = "Total required heat")
        a.plot_date(timeArray,supplemental_Heat, "r", label = "Supplemental needed")
        a.plot_date(timeArray,capacity_Max, "b", label = "Maximum Capacity")
        a.plot_date(timeArray,QC_required, "y", label = "Cooling required")
    
        a.legend(bbox_to_anchor=(0,0.92,1,.102),loc=3, ncol=3, borderaxespad=0)
        
        title = "Heat Pump Performance for "+hp.Manufacturer + " Model " + hp.OutdoorUnit
        a.set_title(title)
        f.canvas.draw()
        
        updateGraph = False
        
 
class HeatPumpPerformanceApp(tk.Tk):

    def __init__(self,*args, **kwargs):
        
        tk.Tk.__init__(self,*args,**kwargs)
        # tk.Tk.iconbitmap(self,default="preferences.ico")          # blows up
        tk.Tk.wm_title(self, string="Heat Pump Analysis Tool")

        def doNothing():
            print("do nothing")
            
        menu=Menu(self)
        self.config(menu=menu)
        fileMenu = Menu(menu)
        menu.add_cascade(label="File",menu=fileMenu)
        fileMenu.add_command(label="New",command=doNothing)
        fileMenu.add_separator()
        fileMenu.add_command(label="Print",command=quit)
        fileMenu.add_command(label="Quit",command=quit)
        
        container = tk.Frame(self)
        container.pack(side="top",fill="both",expand=True)
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)
        
        self.frames = {}

        for F in (StartPage,HomePage, FuelDeliveryPage, BaselineHeatingPage, SelectHeatPumpPage,GraphPage):
            
            frame = F(container,self)
            self.frames[F] = frame
            frame.grid(row=0,column=0,sticky="nsew")
            
        self.show_frame(StartPage)
        
    def show_frame(self,cont):
        frame = self.frames[cont]
        frame.tkraise()

def doHeatPumpAnalysis(status,text): 
    global updateGraph, updateTemp, updateResistance

    # certain years of note since 1993zzzzz
    AverageHDDYear = 2008
    AverageCDDYear = 2003
    HighestHDDYear = 2003
    HighestCDDYear = 2010
    
    hpNames = ""
    n = 0
    for hp in HPChoice :
        hpNames += hp.Manufacturer +'-' +hp.OutdoorUnit
        n += 1
        if n<len(HPChoice):
            hpNames += "+"

#    H = 13   #   the heat pump chosen
    if updateTemp :
        status.config(text="Loading temperature data for period")
        status.update()
        LoadTempDataRaw(status)
        updateTemp = False

    if updateResistance :
        status.config(text="Calculating home thermal resistance")
        status.update()
        approxResistance()
        updateResistance = False

    status.config(text="Analyzing heat pump performance")
    status.update()
    p = heatPumpPerformance(0)
    
    status.config(text="Saving results")
    status.update()
    outputData(0)
    
    totSavings = totBaseEmissions = totHPEmissions = totSuppEmissions = 0.
    totHPACEmissions = totBLACEmissions = 0.0

    BLAC = BaselineAC != 0 and SummerBLSetPoint> 0
    HPAC = SummerHPSetPoint>0

    results = "\nAnalysis of heat pump performance for " + hpNames +"\n\n"
    results += "\tBaseline ("+BaseHeatType+")\t\t"
    if BLAC:
        results += "A/C\t\t\t"
    results += "\tHeat Pump\t\t\t\tSupplemental ("+SuppHeatType+")"
    if HPAC:
        results += "\t\t\tA/C"
    results +="\n"
    
    results += "Year\t"+BaseEnergyUnits+"\tCost\t"
    if BLAC:
        results += "kWh\tCost\t"
    results += "\tKWh\tCost\tCOP\t\t#days\t"+SuppEnergyUnits+"\tCost\t"
    if HPAC:
        results += "kWh\tCost\t"
    results += "\n"

    startYear = t_Data[t_Start].year
    endYear = t_Data[t_End].year
    for year in range(startYear+1,endYear):     # first and last years tend to be truncated, with potentially misleading results
        Y = year-startYear

        COPAve = BaseUnitsByYear[Y]*BaseHvacEfficiency*(BaseEnergyContent/ENERGY_CONTENT_ELEC)/KWhByYear[Y]
        resultline = "%d\t%.1f\t$%.0f" % (year,BaseUnitsByYear[Y],BaseCostByYear[Y])

        if BLAC:
            resultline += "\t%.1f\t$%.0f" % (BLAC_KWhByYear[Y],BLAC_KWhByYear[Y]*STANDARD_PRICE_ELEC)
        
        resultline += "\t\t%.1f\t$%.0f\t%.1f\t\t%d\t%.1f\t$%.0f" % (KWhByYear[Y],KWhByYear[Y]*STANDARD_PRICE_ELEC,COPAve,SuppUsesByYear[Y],SuppUnitsByYear[Y],SuppUnitsByYear[Y]*SuppCostPerUnit)
        
        if HPAC:
            resultline += "\t%.1f\t$%.0f" % (HPAC_KWhByYear[Y],HPAC_KWhByYear[Y]*STANDARD_PRICE_ELEC)
            
        resultline += "\n"
            
        results += resultline
        totSavings += BaseCostByYear[Y] - (KWhByYear[Y]*STANDARD_PRICE_ELEC + SuppUnitsByYear[Y]*SuppCostPerUnit) 
        if BLAC or HPAC :
            totSavings += (BLAC_KWhByYear[Y]-HPAC_KWhByYear[Y]) * STANDARD_PRICE_ELEC
            
        totBaseEmissions += BaseKgCO2PerUnit*BaseUnitsByYear[Y]
        totHPEmissions += ElecKgCO2PerUnit*KWhByYear[Y]
        totSuppEmissions += SuppKgCO2PerUnit*SuppUnitsByYear[Y]
        totBLACEmissions += BLAC_KWhByYear[Y]*ElecKgCO2PerUnit
        totHPACEmissions += HPAC_KWhByYear[Y]*ElecKgCO2PerUnit
    
    if totSavings>0 :
        savingsImpact = "saved"
    else:
        savingsImpact = "cost an additional"
        
    CO2_percent_impact = (100.*(totBaseEmissions + totBLACEmissions - totHPEmissions - totSuppEmissions- totHPACEmissions))
    CO2_percent_impact /= (totBaseEmissions+totBLACEmissions)
    if CO2_percent_impact>0 : 
        CO2Impact = "less"
    else:
        CO2Impact = "more"
        
    results += "\nOver the years %d-%d, the heat pump would have %s $%.0f, emitting %.0f%% %s CO2eq than %s\n" % (startYear+1,endYear-1,savingsImpact, abs(totSavings), CO2_percent_impact, CO2Impact,BaseHeatType)

    analyzeExtremes = True
    if analyzeExtremes:
        # average year first
        LoadTempDataRaw(status,AverageHDDYear)
        heatPumpPerformance(AverageHDDYear)

        totBaseEmissions += BaseKgCO2PerUnit*BaseUnitsByYear[0]
        totHPEmissions   += ElecKgCO2PerUnit*KWhByYear[0]
        totSuppEmissions += SuppKgCO2PerUnit*SuppUnitsByYear[0]
        totBLACEmissions += BLAC_KWhByYear[0]*ElecKgCO2PerUnit
        totHPACEmissions += HPAC_KWhByYear[0]*ElecKgCO2PerUnit
        totSavings = BaseCostByYear[0] - (KWhByYear[0]*STANDARD_PRICE_ELEC + SuppUnitsByYear[0]*SuppCostPerUnit) 
        if BLAC or HPAC :
            totSavings += (BLAC_KWhByYear[0]-HPAC_KWhByYear[0]) * STANDARD_PRICE_ELEC
        if totSavings>0 :
            savingsImpact = "saved"
        else:
            savingsImpact = "cost an additional"

        CO2_percent_impact = (100.*(totBaseEmissions + totBLACEmissions - totHPEmissions - totSuppEmissions- totHPACEmissions))
        CO2_percent_impact /= (totBaseEmissions+totBLACEmissions)
        if CO2_percent_impact>0 : 
            CO2Impact = "less"
        else:
            CO2Impact = "more"

        percentOfLoad = 100.* (totalRequiredHeating  - SuppUnitsByYear[0]*SuppEnergyContent)/totalRequiredHeating
            
        results += "Average heating year (%d), heat pump covers " % (AverageHDDYear)
        results += "%.1f%% of heating load, %s $%.0f, " % (percentOfLoad,savingsImpact,abs(totSavings))
        results += "emits %.0f%% %s CO2 than %s\n" % (CO2_percent_impact,CO2Impact,BaseHeatType)
        
        LoadTempDataRaw(status,HighestHDDYear)
        heatPumpPerformance(HighestHDDYear)

        totBaseEmissions += BaseKgCO2PerUnit*BaseUnitsByYear[0]
        totHPEmissions += ElecKgCO2PerUnit*KWhByYear[0]
        totSuppEmissions += SuppKgCO2PerUnit*SuppUnitsByYear[0]
        totBLACEmissions += BLAC_KWhByYear[0]*ElecKgCO2PerUnit
        totHPACEmissions += HPAC_KWhByYear[0]*ElecKgCO2PerUnit
        totSavings = BaseCostByYear[0] - (KWhByYear[0]*STANDARD_PRICE_ELEC + SuppUnitsByYear[0]*SuppCostPerUnit) 
        if BLAC or HPAC :
            totSavings += (BLAC_KWhByYear[0]-HPAC_KWhByYear[0]) * STANDARD_PRICE_ELEC
        if totSavings>0 :
            savingsImpact = "saved"
        else:
            savingsImpact = "cost an additional"

        CO2_percent_impact = (100.*(totBaseEmissions + totBLACEmissions - totHPEmissions - totSuppEmissions- totHPACEmissions))
        CO2_percent_impact /= (totBaseEmissions+totBLACEmissions)
        if CO2_percent_impact>0 : 
            CO2Impact = "less"
        else:
            CO2Impact = "more"

        percentOfLoad = 100.* (totalRequiredHeating  - SuppUnitsByYear[0]*SuppEnergyContent)/totalRequiredHeating
            
        results += "Coldest heating year (%d), heat pump covers " % (HighestHDDYear) 
        results += "%.1f%% of heating load, %s $%.0f, " % (percentOfLoad,savingsImpact,abs(totSavings))
        results += "emits %.0f%% %s CO2 than %s\n" % (CO2_percent_impact,CO2Impact,BaseHeatType)
       
        updateTemp = True

    text.insert(END,results)
    
    updateGraph = True

def LoadDeliveriesDlg(parent,listbox,lbHdr) :
    
    fname = filedialog.askopenfilename(filetypes=( ("text files","*.txt"),("All files","*.*") ), 
    title="Select file containing oil deliveries data" )
    if fname is None:
        print("no file selected")
    else:
        loadFuelDeliveries(fname)
        UpdateDeliveryHdrView(lbHdr)    
        UpdateDeliveryDataView(listbox)
        UpdateDeliveryGraph(parent)
    
def SaveDeliveriesDlg() :
    
    fname = filedialog.asksaveasfilename(filetypes=( ("text files","*.txt"),("All files","*.*") ), 
    title="Select file to save fuel deliveries data" )
    if len(fname)>0:
        print("Saving delivery data to %s" % fname)
        saveOilDeliveries(fname)

def UpdateDeliveryDataView(listbox):
    listbox.delete(0,END)
    for h in range(numDeliveries) :
        datastring = "\t\t%s\t\t$%.2f\t\t%.1f" % (purchase_Date[h],purchase_Cost[h],purchase_Quantity[h])
        listbox.insert(h,datastring)

def UpdateDeliveryHdrView(lb):
    lb.delete(0,END)
    
    if len(fuelDeliveryHeader)>0 :
        hl = fuelDeliveryHeader.split('\n')
        for h in range(len(hl)):
            hdrString = "\t\t"+hl[h]
            lb.insert(h,hl[h])
    else:
        lb.insert(0,"\t\tNo delivery data entered")
    
        
def ClearDeliveryData(self,listbox):
    # are you sure
    global numDeliveries
    
    # clear the data
    numDeliveries = 0
    purchase_Date.clear()
    purchase_Cost.clear()
    purchase_Quantity.clear()
    
    # Update the listbox
    
    UpdateDeliveryDataView(listbox)
    UpdateDeliveryGraph(self)
        
def UpdateDeliveryGraph(self):
    updateGraph=True
    ohehour = datetime.timedelta(hours=1)
    tArray = []
    fuel_required = []
    monthdays = 365/12.
    months1 = 12.
    
    if updateGraph :
        for i in range(len(purchase_Date)):
            
            if i<len(purchase_Date)-1:
                days = (purchase_Date[i+1]-purchase_Date[i]).days
            else:
                days = (purchase_Date[i]-purchase_Date[i-1]).days
            months0 = months1
            months1 = days/monthdays
            
            time = datetime.datetime(purchase_Date[i].year,purchase_Date[i].month,purchase_Date[i].day,0,0)
            tArray.append(time)
            time = datetime.datetime(purchase_Date[i].year,purchase_Date[i].month,purchase_Date[i].day,1,0)
            tArray.append(time)
            if i>0:
                fuel_required.append(purchase_Quantity[i-1]/months0)
            else:
                fuel_required.append(purchase_Quantity[i]/months1)
                
            fuel_required.append(purchase_Quantity[i]/months1)
            
        ta1 = []
        ta1.append(tArray[0])
        ta1.append(tArray[0])
        ta1.append(tArray[-1])
        ma1 = []
        ma1.append(0)
        ma1.append(WaterHeatMonthlyUsage)    
        ma1.append(WaterHeatMonthlyUsage)
    
        a3.clear()
        a3.plot_date(tArray,fuel_required, "g", label = "Total monthly fuel consumption")   
        a3.plot_date(ta1, ma1, "r", label = "Fuel for water and cooking")    

        a3.legend(bbox_to_anchor=(0,0.92,1,.102),loc=3, ncol=3, borderaxespad=0)
        
        title = "Fuel consumption over time"
        a3.set_title(title)
        f3.canvas.draw()

    updateGraph=False

class StartPage(tk.Frame) :
        
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        
        label=ttk.Label(self,text="PRELIMINARY: This heat pump analysis tool is a prototype which has been adaptated\n"+
        "from the Tufts ME145 Spring 2015 project by J.Kadako et al.\n"+
        "It has limited applicability and needs to be extended to be useful\n"+
        "Use at your own risk",font=NORM_FONT)        
        label.pack(pady=10,padx=10)

        label2=ttk.Label(self,text="Copyright 2015, Town of Concord Comprehensive Sustainable Energy Committee",font=SMALL_FONT)        
        label2.pack(pady=10,padx=10)

        label3=ttk.Label(self,text="This software tool can be freely distributed, and is covered by the GNU Public License",font=SMALL_FONT)        
        label3.pack(pady=10,padx=10)
 
        ys = 5
        button1 = ttk.Button(self,text="Continue",width=26,
                    command = lambda: controller.show_frame(HomePage))
        button1.pack(pady=ys)

        def showLicense():
            input = open("LICENSE")
            text = input.read()            
            popupmsg("License Information",text)

        button0 = ttk.Button(self,text="License Information",width=26,
                    command = lambda: showLicense())
        button0.pack(pady=ys)

        button2 = ttk.Button(self,text="Quit",width=26,
                    command = quit)
        button2.pack(pady=ys)
       
        
class HomePage(tk.Frame) :
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        
        label=ttk.Label(self,text="Home Page",font=LARGE_FONT)        
        label.pack(pady=10,padx=10)
        
        statusBar = tk.Label(self,text="Status: idle",font=SMALL_FONT,bd=1,relief=SUNKEN,anchor=W)        
        statusBar.pack(side=BOTTOM, fill=X)

        ys = 5
        text1=tk.Text(self,font=NORM_FONT, height=30, width=120)
        text1.insert(END,"\nResults:\n")
        button1 = ttk.Button(self,width=26,text="Baseline Heating Scenario",
                    command = lambda: controller.show_frame(BaselineHeatingPage))
        button1.pack(pady=ys)

        button2 = ttk.Button(self,width=26,text="Fuel Purchase History",
                    command = lambda: controller.show_frame(FuelDeliveryPage))
        button2.pack(pady=ys)

        button3 = ttk.Button(self,width=26,text="Select Heat Pump Options",
                    command = lambda: controller.show_frame(SelectHeatPumpPage))
        button3.pack(pady=ys)

        button4 = ttk.Button(self,width=26,text="Do Analysis",
                    command = lambda: doHeatPumpAnalysis(statusBar, text1))
        button4.pack(pady=ys)

        button5 = ttk.Button(self,width=26,text="Show Graph",
                    command = lambda: controller.show_frame(GraphPage))
        button5.pack(pady=ys)
        
        buttonQ = ttk.Button(self,width=26,text = "Quit", command = quit)
        buttonQ.pack(pady=ys)

        text1.pack()

        
class FuelDeliveryPage(tk.Frame):
    global fuelDeliveryHeader

    def tkraise(self):
        UpdateDeliveryGraph(self)
        tk.Frame.tkraise(self)
        
    def AddDelivery(self,listbox):
        global numDeliveries
        # dialog to inquire date cost and volume
        cd = CalendarDialog(self,month=self.lastmonth,year=self.lastyear)
        dDate=cd.result
        self.lastmonth=dDate.month
        self.lastyear=dDate.year
        
        dc=GetFloat("Enter $ cost (w/o $ sign)",default=self.lastcost)
        dCost=dc.result
        self.lastcost=dCost
        
        da=GetFloat("Enter amount",default=self.lastamount)
        dAmount=da.result
        self.lastamount=dAmount
        
        # find location in list
        id = 0
        for date in purchase_Date:
            if date < dDate:
                id = purchase_Date.index(date)+1
            
        # insert into lists
        numDeliveries += 1
        purchase_Date.insert(id,dDate)
        purchase_Cost.insert(id,dCost)
        purchase_Quantity.insert(id,dAmount)
                
        UpdateDeliveryDataView(listbox)
        UpdateDeliveryGraph(self)

    def EditDelivery(self,listbox):
        global numDeliveries

        # get index to delivery
        sel = listbox.curselection()
        if len(sel)>0:
            id = sel[0]
        
            date = purchase_Date[id]
            cost = purchase_Cost[id]
            amount = purchase_Quantity[id]
            
            
        # if date changed, get new index
            # delete from existing loc, insert into new loc
        
        # update entry in lists
        
        UpdateDeliveryDataView(listbox)
        UpdateDeliveryGraph(self)

    def DeleteDelivery(self,listbox):
        global numDeliveries
        # inquire "Are you sure" (proceed, cancel options, with don't ask again option)
        
        # get index to delivery
        sel = listbox.curselection()
        if len(sel)>0:
            id = sel[0]
        
            # delete entry from lists
            numDeliveries -= 1
            del purchase_Date[id]
            del purchase_Cost[id]
            del purchase_Quantity[id]
            
            UpdateDeliveryDataView(listbox)
            UpdateDeliveryGraph(self)

    def __init__(self,parent,controller):
        global current_Heating_Year
        
        tk.Frame.__init__(self,parent)
        label=ttk.Label(self,text="Fuel Deliveries Page",font=LARGE_FONT)        
        label.grid(row=0,column=0,columnspan=2,sticky=(E,W), pady=10,padx=10)
        
        lblHdr=ttk.Label(self,text="Delivery header information (select to edit)",font=SMALL_FONT)        
        lblHdr.grid(row=1,column=0, pady=10)

        lblData=ttk.Label(self,text="Delivery data (select to edit)",font=SMALL_FONT)        
        lblData.grid(row=3,column=0, pady=10)

        button1 = ttk.Button(self,text="Load Delivery Data",
                    command = lambda: LoadDeliveriesDlg(self, lbData,lbHdr))
        button1.grid(row=8,column=0)

        button2 = ttk.Button(self,text="Enter/Edit Deliveries",
                    command = lambda: EditDeliveriesDlg(self))
        button2.grid(row=8,column=1)

        button3 = ttk.Button(self,text="Save Delivery data",
                    command = lambda: SaveDeliveriesDlg(self))
        button3.grid(row=8,column=2)

        lbHdr = tk.Listbox(self,selectmode=tk.SINGLE,height=2,width=40)
        lbHdr.grid(row=2,column=0,columnspan=2)

        lbData = tk.Listbox(self,selectmode=tk.SINGLE,height=20,width=40)
        lbData.grid(row=4,column=0,columnspan=2, rowspan=4)

        button4 = ttk.Button(self,text="Done",
                    command = lambda: controller.show_frame(HomePage))
        button4.grid(row=9,column=1)

        button5 = ttk.Button(self,text="Add Delivery",
                    command = lambda: self.AddDelivery(lbData))
        button5.grid(row=4,column=2)

        button6 = ttk.Button(self,text="Edit Delivery",
                    command = lambda: self.EditDelivery(lbData))
        button6.grid(row=5,column=2)

        button7 = ttk.Button(self,text="Delete Delivery",
                    command = lambda: self.DeleteDelivery(lbData))
        button7.grid(row=6,column=2)

        button7 = ttk.Button(self,text="Delete All",
                    command = lambda: ClearDeliveryData(self,lbData))
        button7.grid(row=7,column=2)

        button8 = ttk.Button(self,text="Edit",command = lambda: EditHeaderInfo())
        button8.grid(row=2,column=2)
 
        canvas = FigureCanvasTkAgg(f3,self)
        canvas.show()
        canvas.get_tk_widget().grid(column=3, columnspan=3, row=4, rowspan=4)  #fill=tk.BOTH,,pady=10
       
        UpdateDeliveryHdrView(lbHdr)    
        UpdateDeliveryDataView(lbData)
        UpdateDeliveryGraph(self)
        
        self.lastmonth=1
        self.lastyear=current_Heating_Year
        self.lastcost=0.0
        self.lastamount=0.0
            

class BaselineHeatingPage(tk.Frame):
    global EfficiencyHVAC, WaterHeatMonthlyUsage
    global WinterBLSetPoint, SummerBLSetPoint
    
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        label=ttk.Label(self,text="Baseline Heating Scenario: the exisiting system with it's fuel consumption specified",font=LARGE_FONT)
        label.grid(row=0,column=2,columnspan=3,pady=10,padx=10)
  
        label1=ttk.Label(self,text="Baseline heating system type, efficiency, and operating parameters",font=NORM_FONT)
        label1.grid(row=1,column=2,columnspan=3,pady=30,padx=10)
        
        BLType = IntVar()
        BLType.set(0)
        
        rb1 = tk.Radiobutton(self, width=16, text=HEAT_NAME_OIL, variable=BLType, value=0, command=lambda: SetBLScenario(HEAT_TYPE_OIL))
        rb2 = tk.Radiobutton(self, width=16, text=HEAT_NAME_GAS, variable=BLType, value=1, command=lambda: SetBLScenario(HEAT_TYPE_GAS))
        rb3 = tk.Radiobutton(self, width=16, text=HEAT_NAME_ELEC,variable=BLType, value=2, command=lambda: SetBLScenario(HEAT_TYPE_ELEC))
        rb4 = tk.Radiobutton(self, width=16, text=HEAT_NAME_LPG, variable=BLType, value=3, command=lambda: SetBLScenario(HEAT_TYPE_LPG))
        rb5 = tk.Radiobutton(self, width=16, text="Other",       variable=BLType, value=4, command=lambda: SetBLScenario(HEAT_TYPE_OTHER))

        ys = 5
        rb1.grid(row=2,column=0,padx=20, pady = ys)
        rb2.grid(row=3,column=0,padx=20, pady = ys)
        rb3.grid(row=4,column=0,padx=20, pady = ys)
        rb4.grid(row=5,column=0,padx=20, pady = ys)
        rb5.grid(row=6,column=0,padx=20, pady = ys)
        rb1.invoke()
        
        def getEfficiency(self):
            s = GetInt("Enter system efficiency in %", default=100*BaseHvacEfficiency, min=10, max=100)
            eff = s.result
            try:
                BaseHvacEfficiency = float(eff/100.)
            except:
                print("bad value")

            e.config(text=eff)
            e.update()

        eff = '{0:2.1f}'.format(100.*BaseHvacEfficiency)
        e = ttk.Label(self, width=5, text=eff)
        e.grid(row=2, column=3, pady = ys)

        btn1 =ttk.Button(self,text="System Efficiency",width=20,  command=lambda: getEfficiency(e))
        btn1.grid(row=2,column=2,padx=10, pady = ys)

        def setStartDate() :
            cd = CalendarDialog(self,year=2012,month=7)
            turn_ON_Date = datetime.date(cd.result.year, cd.result.month, cd.result.day)         
            print (turn_ON_Date)
        def setEndDate() :
            cd = CalendarDialog(self)
            turn_OFF_Date = datetime.date(cd.result.year, cd.result.month, cd.result.day)           
            print (turn_OFF_Date)
        def setTempSetPoint(e): 
            global WinterBLSetPoint
            s = GetFloat("Temperature set point", default=WinterBLSetPoint, min=50., max=90.)
            weff = s.result
            try:
                WinterBLSetPoint = float(weff)
            except:
                print("bad value")

            e.config(text=weff)
            e.update()
        def setACSetPoint(e): 
            global SummerBLSetPoint
            s = GetFloat("Temperature set point", default=SummerBLSetPoint, min=50., max=90.)
            weff = s.result
            try:
                SummerBLSetPoint = float(weff)
            except:
                print("bad value")

            e.config(text=weff)
            e.update()
            

        label3=ttk.Label(self,text="Set Annual System Start/End Dates",font=SMALL_FONT)
        label3.grid(row=3,column=2,columnspan=2,padx=10, pady = ys)
            
        button2 = ttk.Button(self,text="Start Date",width=20, 
                    command = setStartDate)
        button2.grid(row=4,column=2, pady = ys)

        labelSD = ttk.Label(self,text=turn_ON_Date)
        labelSD.grid(row=4,column=3, pady = ys)
        
        button3 = ttk.Button(self,text="End Date",width=20, 
                    command = setEndDate)
        button3.grid(row=5,column=2, pady = ys)

        labelED = ttk.Label(self,text=turn_OFF_Date)
        labelED.grid(row=5,column=3, pady = ys)

        label3=ttk.Label(self,text="Thermostat set point",font=SMALL_FONT)
        label3.grid(row=3,column=4,columnspan=2,padx=10, pady = ys)
            
        labelT = ttk.Label(self,text=str(WinterBLSetPoint))
        button2a = ttk.Button(self,text="Temperature",width=20, 
                    command = lambda: setTempSetPoint(labelT))
        button2a.grid(row=4,column=4, pady = ys)
        labelT.grid(row=4,column=5, pady = ys)

        
        labelW=ttk.Label(self,text="Baseline hot water type parameters",font=NORM_FONT)
        labelW.grid(row=10,column=2,columnspan=3,pady=30,padx=10)

        BLWType = IntVar()
        BLWType.set(0)
        rbw1 = tk.Radiobutton(self, width=16, text=HEAT_NAME_OIL, variable=BLWType, value=0, command=lambda: SetBLWScenario(HEAT_TYPE_OIL))
        rbw2 = tk.Radiobutton(self, width=16, text=HEAT_NAME_GAS, variable=BLWType, value=1, command=lambda: SetBLWScenario(HEAT_TYPE_GAS))
        rbw3 = tk.Radiobutton(self, width=16, text=HEAT_NAME_ELEC,variable=BLWType, value=2, command=lambda: SetBLWScenario(HEAT_TYPE_ELEC))
        rbw4 = tk.Radiobutton(self, width=16, text=HEAT_NAME_LPG, variable=BLWType, value=3, command=lambda: SetBLWScenario(HEAT_TYPE_LPG))
        rbw5 = tk.Radiobutton(self, width=16, text="Other",       variable=BLWType, value=4, command=lambda: SetBLWScenario(HEAT_TYPE_OTHER))
        rbw1.grid(row=12,column=0,padx=20, pady = ys)
        rbw2.grid(row=13,column=0,padx=20, pady = ys)
        rbw3.grid(row=14,column=0,padx=20, pady = ys)
        rbw4.grid(row=15,column=0,padx=20, pady = ys)
        rbw5.grid(row=16,column=0,padx=20, pady = ys)
        rbw1.invoke()
         
        def getWaterUse(e):
            global WaterHeatMonthlyUsage
            s = GetFloat("Estimate monthly heat units for water", default=WaterHeatMonthlyUsage, min=0.)
            weff = s.result
            try:
                WaterHeatMonthlyUsage = float(weff)
            except:
                print("bad value")

            e.config(text=weff)
            e.update()

        btnTxt = "Estimated monthly "+BaseEnergyUnits

        weff = '{0:.0f}'.format(WaterHeatMonthlyUsage)
        ew = ttk.Label(self, width=5, text=weff)
        ew.grid(row=12, column=3)
        btn1 =ttk.Button(self,text=btnTxt, width=20, command=lambda: getWaterUse(ew))
        btn1.grid(row=12,column=2)

        labelAC=ttk.Label(self,text="Baseline air conditioning parameters",font=NORM_FONT)
        labelAC.grid(row=20,column=2,columnspan=3,pady=30,padx=10)

        BLAType = IntVar()
        BLAType.set(0)
        rba1 = tk.Radiobutton(self, width=16, text="None", variable=BLAType, value=0, command=lambda: SetBLAScenario(0))
        rba2 = tk.Radiobutton(self, width=16, text="Central", variable=BLAType, value=1, command=lambda: SetBLAScenario(1))
        rba3 = tk.Radiobutton(self, width=16, text="Windows",variable=BLAType, value=2, command=lambda: SetBLAScenario(2))
        rba1.grid(row=22,column=0,padx=20, pady = ys)
        rba2.grid(row=23,column=0,padx=20, pady = ys)
        rba3.grid(row=24,column=0,padx=20, pady = ys)
        rba1.invoke()

        def getACSEER(e):
            global BaselineSEER
            s = GetFloat("Central AC SEER Rating", default=BaselineSEER, min=0.)
            weff = s.result
            try:
                BaselineSEER = float(weff)
            except:
                print("bad value")

            e.config(text=weff)
            e.update()

        if BaselineAC == 1 :
            weff = '{0:.0f}'.format(BaselineSEER)
        else:
            weff = ""
        eA = ttk.Label(self, width=5, text=weff)
        eA.grid(row=23, column=3)
        
        btnA1 =ttk.Button(self,text="SEER", width=20, command=lambda: getACSEER(eA))
        btnA1.grid(row=23,column=2)

        label3A=ttk.Label(self,text="A/C set point",font=SMALL_FONT)
        label3A.grid(row=22,column=4,columnspan=2,padx=10, pady = ys)
            
        labelAT = ttk.Label(self,text=str(SummerBLSetPoint))
        buttonA2a = ttk.Button(self,text="Temperature",width=20, 
                    command = lambda: setACSetPoint(labelAT))
        buttonA2a.grid(row=23,column=4, pady = ys)
        labelAT.grid(row=23,column=5, pady = ys)

        button4 = ttk.Button(self,text="Done",width=20, 
                    command = lambda: controller.show_frame(HomePage))
        button4.grid(row=30, column=2,pady=30)

def selHeatPump(H,info):
    global firstPlot

    heatPump = HPList[H]
    if len(HPChoice)==0 :
        HPChoice.insert(0,heatPump)
    else:
        HPChoice[0] = heatPump
        
    a1.clear()
            
    if firstPlot:
        l1c, = a1.plot(heatPump.tData, heatPump.COPMax, linestyle='-', color="red", marker='*', markersize=10,label = "COP (max capacity)") 
        l1d, = a1.plot(heatPump.tData, heatPump.COPMin, linestyle='-', color="blue", marker=r'*', markersize=10, label = "COP (min capacity)") 
    else:
        l1c.set_xdata(heatPump.tData)
        l1c.set_ydata(heatPump.COPMax)
        l1d.set_xdata(heatPump.tData)
        l1d.set_ydata(heatPump.COPMin)

    tMin = heatPump.tData[-1]
    a1.set_xlim(tMin-5., 60)
    a1.set_ylim(ymin=0.,ymax=6.)
    a1.legend(bbox_to_anchor=(0,0.80,1,.1),loc=3, ncol=3, borderaxespad=0)
        
    title = "COP for " + heatPump.Manufacturer +" Model " + heatPump.OutdoorUnit
    a1.set_title(title)

    a2.clear()
    if firstPlot:
                
        l2c, = a2.plot(heatPump.tData, heatPump.CAPMax, linestyle='-', color="red", marker=r'*', markersize=10, label = "Max capacity") 
        l2d, = a2.plot(heatPump.tData, heatPump.CAPMin, linestyle='-', color="blue", marker=r'*', markersize=10, label = "Min capacity") 
        title = "Capacity vs temperature"
        a2.set_title(title)
        a2.legend(bbox_to_anchor=(0,0.80,1,.1),loc=3, ncol=3, borderaxespad=0)
    else:
        l2c.set_xdata(heatPump.tData)
        l2c.set_ydata(heatPump.CAPMax)
        l2d.set_xdata(heatPump.tData)
        l2d.set_ydata(heatPump.CAPMin)
    a2.set_ylim(ymin=0.,ymax=60000.)
                
    f1.canvas.draw()
    updateHeatPumpInfo(info)

def addHeatPump(H,info):
    HPChoice.insert(0,None)
    selHeatPump(H,info)
 
def clearHeatPump(info):
    HPChoice.clear()
    updateHeatPumpInfo(info)
 
def updateHeatPumpInfo(info):
    ### update text box with chosen heat pump information"""
    infoText = ""
    for hp in HPChoice:
        infoText+= hp.Manufacturer + "-" + hp.OutdoorUnit + "," + hp.DuctedDuctless + "\n"
        
    info.config(text=infoText)
    info.update()
        
class SelectHeatPumpPage(tk.Frame):
    def __init__(self,parent,controller):
        global WinterHPSetPoint, SummerHPSetPoint
        HPFilter = ['Ductless','Ducted','All']

        HPListIndex2ID = []
        
        tk.Frame.__init__(self,parent)
        label=ttk.Label(self,text="\tHeat Pump Selection Page: View parameters for NEEP recommended cold climate heat pumps\n",font=LARGE_FONT)
        label.grid(row=0,column=0,columnspan=5, sticky=(W,E))

        lb = tk.Listbox(self,selectmode=tk.SINGLE,height=15,width=50)

        HPType = IntVar()
        HPType.set(0)
                    
        def FillHPListBox(lb, filterVar):
            HPListIndex2ID.clear()
            lb.delete(0,lb.size())
            filter = filterVar    # the string variable
            filter = HPFilter[filter]
            h = 0
            for hp in HPList:
                ductless = (hp.DuctedDuctless == 'Ductless')
                if ( (ductless and (filter=='Ductless' or filter=='All')) or ((not ductless) and (filter != 'Ductless'))) :
                    insertText = hp.Manufacturer + " Model " + hp.OutdoorUnit + " " + hp.DuctedDuctless
                    if hp.DuctedDuctless == 'Ductless': insertText+='-' + hp.Zones
                        
                    lb.insert(h,insertText)
                    HPListIndex2ID.append(h)
                h += 1
            print("Heat pump list filled")

        rb1 = tk.Radiobutton(self, text="Ductless", variable=HPType, value=0, command=lambda: FillHPListBox(lb,0))
        rb2 = tk.Radiobutton(self, text="Ducted",   variable=HPType, value=1, command=lambda: FillHPListBox(lb,1))
        rb3 = tk.Radiobutton(self, text="Both",     variable=HPType, value=2, command=lambda: FillHPListBox(lb,2))

        rb1.grid(row=1,column=0)
        rb2.grid(row=1,column=1)
        rb3.grid(row=1,column=2)
        rb1.invoke()

        lb.grid(row=2,column=0, rowspan=1,columnspan=3,sticky=(N))
        lb.activate(0)
        
        canvas = FigureCanvasTkAgg(f1,self)
        canvas.show()
        canvas.get_tk_widget().grid(column=3, columnspan=3, row=1, rowspan=4)  #fill=tk.BOTH,,pady=10

        text1 = ttk.Label(self,text='Selected Heat Pump System',font=NORM_FONT)
        text1.grid(row=3,column=0,columnspan=3,sticky=(N,E,W))
        
        text2 = ttk.Label(self,text='',font=NORM_FONT)
        text2.grid(row=4,column=0,columnspan=3,sticky=(N,E,W))

        button1 = ttk.Button(self,text="Select Heat Pump",
                    command = lambda: selHeatPump(HPListIndex2ID[lb.curselection()[0]],text2))
        button1.grid(row=5, column=0)
  
        button2 = ttk.Button(self,text="Add Heat Pump",
                    command = lambda: addHeatPump(HPListIndex2ID[lb.curselection()[0]],text2))
        button2.grid(row=5, column=1)
       
        button3 = ttk.Button(self,text="Clear Heat Pump selection",
                    command = lambda: clearHeatPump(text2))
        button3.grid(row=5, column=2)

        def setHHTSetPoint(e): 
            global WinterHPSetPoint
            s = GetFloat("Temperature set point", default=WinterHPSetPoint, min=40., max=100.)
            weff = s.result
            try:
                WinterHPSetPoint = float(weff)
            except:
                print("bad value")
            e.config(text=weff)
            e.update()

        def setHATSetPoint(e): 
            global SummerHPSetPoint
            s = GetFloat("Temperature set point", default=SummerHPSetPoint, min=60., max=100.)
            weff = s.result
            try:
                SummerHPSetPoint = float(weff)
            except:
                print("bad value")
            e.config(text=weff)
            e.update()

        labelHHT = ttk.Label(self,text=str(WinterHPSetPoint))
        buttonA2a = ttk.Button(self,text="Winter Temp Set Point",width=20, 
                    command = lambda: setHHTSetPoint(labelHHT))
        buttonA2a.grid(row=5,column=3)
        labelHHT.grid(row=5,column=4)

        labelHAT = ttk.Label(self,text=str(SummerHPSetPoint))
        buttonA2b = ttk.Button(self,text="Summer Temp Set Point",width=20, 
                    command = lambda: setHATSetPoint(labelHAT))
        buttonA2b.grid(row=6,column=3)
        labelHAT.grid(row=6,column=4)

        text2b = ttk.Label(self,text='Heat Pump Hot Water',font=NORM_FONT)
        text2b.grid(row=6,column=0,columnspan=3,pady=30, sticky=(N,E,W))

        def addHeatPumpHW():
            pass
            
        def delHeatPumpHW():
            pass
            
        button5 = ttk.Button(self,text="Add Heat Pump Water Heater",
                    command = lambda: addHeatPumpHW)
        button5.grid(row=7, column=0)
        
        button6 = ttk.Button(self,text="Remove Heat Pump Water Heater",
                    command = lambda: delHeatPumpHW)
        button6.grid(row=7, column=1)

        text3 = ttk.Label(self,text='',font=NORM_FONT)
        text3.grid(row=7,column=2,columnspan=3,sticky=(N,E,W))
       
        button4 = ttk.Button(self,text="Done",
                    command = lambda: controller.show_frame(HomePage))
        button4.grid(row=10,column=1, pady=30)        

class GraphPage(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        
        label=ttk.Label(self,text="Heat Pump Graph",font=LARGE_FONT)        
        label.pack(pady=10,padx=10)
        
        button1 = ttk.Button(self,text="Done",
                    command = lambda: controller.show_frame(HomePage))
        button1.pack()
        
        canvas = FigureCanvasTkAgg(f,self)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        
        toolbar = NavigationToolbar2TkAgg(canvas,self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP,fill=tk.BOTH,expand=True)

def isHeating(t) :
# Author: Jonah Kadoko
# this function determines if the heat pump should heat the room at this particular time
# Reasons why your heat pump may not turn ON include, but not limited to the following,:
# 1, The outdoor temp is lower than the min operating temp of the heat pump
# 2, It is in the summer time before your specified turn_ON_Date and after the turn_OFF_Date
# 3, The heat pump overshoot for that particular hour and so is cycling (not much modelling has been done to simumlate cycling)

    if t_Data[t] <= datetime.datetime(t_Data[t].year, turn_OFF_Date.month, turn_OFF_Date.day) :
        current_Heating_Year = t_Data[t].year - 1    
    else:
        current_Heating_Year = t_Data[t].year
    
    yr_Turn_OFF = datetime.datetime(current_Heating_Year + 1, turn_OFF_Date.month, turn_OFF_Date.day)
    yr_Turn_ON = datetime.datetime(current_Heating_Year, turn_ON_Date.month, turn_ON_Date.day)

#    if (t_Data[t_Start] <= t_Data[t]) and (t_Data[t] <= yr_Turn_OFF) and \
#    (yr_Turn_ON <= t_Data[t]) and (t_Data[t] <= t_Data[t_End]) and (T_Outdoor[t] < WinterHPSetPoint) :
    if (t_Data[t] <= yr_Turn_OFF) and (yr_Turn_ON <= t_Data[t]) and (T_Outdoor[t] < WinterHPSetPoint) :
        # t is within range of the heating period and purchase period and the outdoor temperature is below the indoor temperature
        return True
    else:
        return False    
            
def isCooling(t) :

# this function determines if the cooling should be applied at this time
# Reasons why your heat pump may not turn ON include, but not limited to the following,:
# 1, The outdoor temp is lower than the min operating temp of the heat pump
# 2, It is in the summer time before your specified turn_ON_Date and after the turn_OFF_Date
# 3, The heat pump overshoot for that particular hour and so is cycling (not much modelling has been done to simumlate cycling)

    if t_Data[t] <= datetime.datetime(t_Data[t].year, turn_OFF_Date.month, turn_OFF_Date.day) :
        current_Heating_Year = t_Data[t].year - 1    
    else:
        current_Heating_Year = t_Data[t].year
    
    yr_Turn_OFF = datetime.datetime(current_Heating_Year + 1, turn_OFF_Date.month, turn_OFF_Date.day)
    yr_Turn_ON = datetime.datetime(current_Heating_Year, turn_ON_Date.month, turn_ON_Date.day)

    if (T_Outdoor[t] > SummerHPSetPoint) :
        # t is within range of the heating period and purchase period and the outdoor temperature is below the indoor temperature
        return True
    else:
        return False        
    
def approxResistance():
    # Adapted from VBA project, Author: Jonah Kadoko
    # Decide the hour to start and stop the calculations
    # 1, t_Start should be the index of time corresponding to the second purchase date (since the customer fills up their tank each time)
    # 2, t_End should be  the date corresponding the last purchase date
    global t_Start
    global t_End
    global last_Purchase
    global average_Resistance
    
    p = 0
    approx_Resistance.clear()
    while True:
        approx_Resistance.append([0,0])
        p+=1
        if p==numDeliveries: break

    t = 0    
 
    p = numDeliveries-1
    last_Purchase = p
    if purchase_Quantity[p] == 0 :
                last_Purchase = p - 1
    
    while t<len(t_Data):    # (t_Start == 0) or (t_End == 0):
        if (t_Start==0):
            if purchase_Date[0] == t_Data[t].date() :
                # All calculations should start a day after the customer fills up their tank around the start of the year
                # t_Start is the index of the time the customer fi
                t_Start = t

        elif (t_End==0 and purchase_Date[last_Purchase] == t_Data[t].date()) :
            # calculations should stop at the last purchase date of the year
            t_End = t
            break

        t = t + 1

    if t_End==0 :
        t_End = len(t_Data)-1
        
    startYear = t_Data[t_Start].year
    endYear = t_Data[t_End].year
    BaseUnitsByYear.clear()
    BaseCostByYear.clear()
    BLAC_KWhByYear.clear()
    HPAC_KWhByYear.clear()
    for year in range(startYear,endYear+1):
        BaseUnitsByYear.append(0.0)
        BaseCostByYear.append(0.0)
        BLAC_KWhByYear.append(0.0)
        HPAC_KWhByYear.append(0.0)

    # Calculate total annual delta T
    delta_T = 0.0
    for t in range(t_Start,t_End) :
        if isHeating(t):
            delta_T = delta_T + (WinterHPSetPoint - T_Outdoor[t])

    # Calculate the total oil used
    total_Vol = 0.0
    prevDate = purchase_Date[0]
    for p in range(0, last_Purchase):
        if BaseHeatType == WaterHeatType and WaterHeatMonthlyUsage>0 :
            purchasePeriod = (purchase_Date[p] - prevDate)
            days = purchasePeriod.days
            months = days * (12./365)
            WaterFuelInPeriod = WaterHeatMonthlyUsage * months
        else:
            WaterFuelInPeriod = 0.
        
        prevDate = purchase_Date[p]
        year = purchase_Date[p].year
        Y = year - startYear
        if year <= endYear:
            Quantity_Used = (purchase_Quantity[p]-WaterFuelInPeriod)
            total_Vol += Quantity_Used
            BaseUnitsByYear[Y] += Quantity_Used
            BaseCostByYear[Y] += purchase_Cost[p]*(Quantity_Used/purchase_Quantity[p])

    # Calculate the average resistance per heating period
    p = 0
    approx_Resistance[0][0] = t_Start
    approx_Resistance[0][1] = 0.0
    for t in range(t_Start,t_End):
        
        if BaseHeatType == WaterHeatType and WaterHeatMonthlyUsage>0 and p<len(purchase_Date)-2 :
            purchasePeriod = (purchase_Date[p+1] - purchase_Date[p])
            days = purchasePeriod.days
            months = days * (12./365)
            WaterFuelInPeriod = WaterHeatMonthlyUsage * months
        else:
            WaterFuelInPeriod = 0.
        Quantity_Used = (purchase_Quantity[p]-WaterFuelInPeriod)

        ti = t-t_Start
        dateTime = t_Data[t]
        year = dateTime.year
        Y = year - startYear
        
        thisDate = t_Data[t].date()
        if isHeating(t) and (purchase_Date[p] <= thisDate) and (thisDate <= purchase_Date[p + 1]) and (p < last_Purchase) :

            # Sum app eligible delta_T during each heating period
    
            approx_Resistance[p][1] += (WinterHPSetPoint - T_Outdoor[t]) / (BaseHvacEfficiency * Quantity_Used * BaseEnergyContent)
    
        else:
            if isHeating(t) and (purchase_Date[p + 1] <= thisDate) and (thisDate <= purchase_Date[last_Purchase]) and (p < last_Purchase): 
                # this particular time sample belongs to the next purchase period
                p = p + 1
                approx_Resistance[p][0] = t
                approx_Resistance[p][1] =  (WinterHPSetPoint - T_Outdoor[t]) / (BaseHvacEfficiency * Quantity_Used * BaseEnergyContent)
    
 
    # Average resistance during the heating period
    average_Resistance = delta_T / (BaseHvacEfficiency * BaseEnergyContent * total_Vol)

def heatPumpPerformance(h):
    #Author: Jonah Kadoko
    #this function calculates the approximate min, and max heating capacity, COPave and average electrical consumption
    #One would expect that the required heat be in between the max and min heating capacities

# argument h: 0 - analyze data for the years provided
#             other - analyze performance for year h
    global last_Purchase,t_Start,t_End
    global average_Resistance
    global Q_required, QC_required, timeArray, totalRequiredHeating, totalRequiredCooling
    global capacity_Max, capacity_Min, electric_Required, supplemental_Heat, COP_Ave

    use_Average_R = True
    
    p = 0
    
    KWhByYear.clear()
    SuppUnitsByYear.clear()
    SuppUsesByYear.clear()

    if h==0:
        startYear = t_Data[t_Start].year
        endYear = t_Data[t_End].year
        
        timeArray = [t_Data[t] for t in range(t_Start,t_End)]
        Q_required = [0.0 for t in range(t_Start, t_End)]
        QC_required = [0.0 for t in range(t_Start, t_End)]
        capacity_Max = [-1.0 for t in range(t_Start,t_End)]
        capacity_Min = [0.0 for t in range(t_Start,t_End)]
        electric_Required = [0.0 for t in range(t_Start,t_End)]
        supplemental_Heat = [0.0 for t in range(t_Start,t_End)]
        COP_Ave = [0.0 for t in range(t_Start,t_End)]
    else:
        startYear = endYear = h
        t_Start = 0
        t_End = len(t_Data)

        timeArray1 = [t_Data[t] for t in range(t_Start,t_End)]
        Q_required1 = [0.0 for t in range(t_Start, t_End)]
        QC_required1 = [0.0 for t in range(t_Start, t_End)]
        capacity_Max1 = [-1.0 for t in range(t_Start,t_End)]
        capacity_Min1 = [0.0 for t in range(t_Start,t_End)]
        electric_Required1 = [0.0 for t in range(t_Start,t_End)]
        supplemental_Heat1 = [0.0 for t in range(t_Start,t_End)]
        COP_Ave1 = [0.0 for t in range(t_Start,t_End)]

        BaseUnitsByYear[0] = 0.
        BaseCostByYear[0] = 0.
 
    supplementalLastDate = t_Data[0]   # for determining how many supplemental days there are
    oldYear = 1900

    totalRequiredHeating = 0.
    totalRequiredCooling = 0.
    
    for t in range(t_Start,t_End):
        ti = t-t_Start
        if h==0:
            dateTime = timeArray[ti]
        else:
            dateTime = timeArray1[ti]
            
        year = dateTime.year
        Y = year - startYear
        
        if year > oldYear:
            oldYear = year
            KWhByYear.append(0.0)
            SuppUnitsByYear.append(0.0)
            SuppUsesByYear.append(0)
            
        # Calculate the perfomance
        if (use_Average_R) : 
            resistance = average_Resistance            
        else :
            resistance = approx_Resistance[p][1]

        temp = T_Outdoor[t]
        CAP_Max = 0
        CAP_Min = 0  
        COP_Min = []
        COP_Max = []
        np = len(HPChoice)

        for hp in HPChoice:
            CAP_Max += hp.MaxCapacity(temp)
            CAP_Min += hp.MinCapacity(temp)
            
            COP_Min.append(hp.COPatMinCapacity(temp))
            COP_Max.append(hp.COPatMaxCapacity(temp))

        if isHeating(t):
    
#           if (purchase_Date[p] <= t_Data[t].date()) and (t_Data[t].date() <= purchase_Date[p + 1]) and (p < last_Purchase) :
#               # Sum app eligible delta_T during each heating period
#               Q_required[ti] = (WinterHPSetPoint - temp)/ resistance
#           else:
#               if (purchase_Date[p + 1] <= t_Data[t].date()) and (t_Data[t].date() <= purchase_Date[last_Purchase]) and (p < last_Purchase) :
#                   # this particular time sample belongs to the next purchase period
#                  p = p + 1
#                  Q_required[ti] = (WinterHPSetPoint - temp) / resistance

            heating_required = (WinterHPSetPoint - temp)/ resistance
            cooling_required = 0.            
        elif isCooling(t):
            heating_required = 0.
            cooling_required = (temp - SummerHPSetPoint)/ resistance

        if h==0:
            Q_required[ti] = heating_required
            QC_required[ti]= cooling_required
            capacity_Max[ti] = CAP_Max
            capacity_Min[ti] = CAP_Min
            
        totalRequiredHeating += heating_required
        totalRequiredCooling += cooling_required

        COPave = 0.0        
                        
        # calculate the average values of the above
        # Linear interpolation, doesn't work well
        # COP_Ave(t, h) = (Q_required(t) - capacity_Min(t, h)) * (COP_Max - COP_Min) / (capacity_Max(t, h) - capacity_Min(t, h)) + COP_Min          
        # Weighted average works better
#        c = (abs(Q_required[t] - capacity_Min[t]) * COP_Min + abs(Q_required[t] - capacity_Max[t]) * COP_Max)

        # for years with purchase data - use purchase data for baseline units and cost
        # for analysis of average and extreme, back-calculate what we would have used
        if h!= 0:
            BaseUnitsByYear[Y] += heating_required/BaseHvacEfficiency/BaseEnergyContent
            BaseCostByYear[Y] += BaseCostPerUnit*heating_required/BaseHvacEfficiency/BaseEnergyContent
        
        # Note times where the heat pump cannot meet demand
        if (heating_required > CAP_Max) :
            for i in range(np): 
                COPave += COP_Max[i]/np
                
            supplemental_required = heating_required - CAP_Max
            
            if h==0:
                supplemental_Heat[ti] = supplemental_required

            SuppUnitsByYear[Y] += supplemental_required/SuppHvacEfficiency/SuppEnergyContent
            
                
            # is this a new supplemental usage (within 24 hours of the past one)
            deltaTime = dateTime - supplementalLastDate
            if deltaTime>datetime.timedelta(1,0)  : #timeDelta(0,0,1,0,0)
                supplementalLastDate = dateTime
                SuppUsesByYear[Y] += 1
                
            # The amount of electricity required to heat the area with Q_required BTUs
            electric_required = CAP_Max / COPave/ENERGY_CONTENT_ELEC
            
            if h==0:
                electric_Required[ti] = electric_required
                
            KWhByYear[Y] += electric_required
        
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
            KWhByYear[Y] += electric_required
            if h==0:
                electric_Required[ti] = electric_required
                
        if (cooling_required > 0) :
            if BaselineAC != 0 and BaselineSEER>0:
                BLAC_KWhByYear[Y] += cooling_required / BaselineSEER/1000.

            # weighted average SEER based on fraction of total capacity at 47 degrees
            HPSEER = 0.
            CAPTOTAL = 0.
            for hp in HPChoice:
                HPSEER += float(hp.SEER) * hp.MaxCapacity(47)
                CAPTOTAL += hp.MaxCapacity(47)
            HPSEER = HPSEER/CAPTOTAL
                 
            if HPSEER>0.:
                HPAC_KWhByYear[Y] += cooling_required / HPSEER/1000.
                                    
def outputData(H):
    # This routine outputs all results to a text file
    global last_Purchase
    
    hpNames = ""
    for hp in HPChoice :
        hpNames += hp.Manufacturer +'-' +hp.OutdoorUnit 
        
    outputFile = './Output Data/Heat Pump Analysis.txt'
    output = open(outputFile,'w')
           
    output.write('Analysis for: '+hpNames +'\r')
    
    
    for tv in range(t_Start,t_End):
        t= tv-t_Start
    
        output.write(timeArray[t].ctime()+'\t{0:.2f}\t{1:f}\t{2:f}\t{3:f}\t{4:f}\n'.format(Q_required[t],electric_Required[t],supplemental_Heat[t], capacity_Max[t],COP_Ave[t]))
    
    output.close()
    
# initialization code
initializeData()
loadHeatPumps()

# main routine 

app = HeatPumpPerformanceApp()
ani = animation.FuncAnimation(f,animate, interval=1000)
app.mainloop()
app.destroy()



