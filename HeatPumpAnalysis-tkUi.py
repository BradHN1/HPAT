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
from HeatPumpAnalysis import *

HUGE_FONT = ("Verdana",36)
LARGE_FONT = ("Verdana",20)
NORM_FONT = ("Helvetica",16)
SMALL_FONT = ("Helvetica",13)
style.use("ggplot")

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

f4 = plt.figure()
a4 = plt.subplot2grid((2,2), (0,0), rowspan = 3, colspan = 3)
a4.set_ylabel('Cost')
a4.set_xlabel('Years after investment')
a4.set_ylim(0.,50000.)
a4.set_autoscalex_on(True)
a4.set_autoscaley_on(True)
plt.grid(True)

hpa = HeatPumpAnalysis()

def quit():
    exit(0)
    
def popupmsg(title, msg):
    
    popup = tk.Tk()
    popup.wm_title(title)
    label = ttk.Label(popup,text=msg,font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1=ttk.Button(popup, text="OK",command=popup.destroy)
    B1.pack()
    popup.mainloop()    

def animate(i):

    if len(hpa.HPChoice)>0 :
        hp = hpa.HPChoice[0]
    else:
        return
            
    if hpa.updateGraph :
    
#        a = plt.subplot2grid((6,4), (0,0), rowspan = 5, colspan = 4)
#        a2 = plt.subplot2grid((6,4), (5,0), rowspan = 1, colspan = 4, sharex = a)

        a.clear()
        a.plot_date(hpa.timeArray,hpa.Q_required, "g", label = "Total required heat")
        a.plot_date(hpa.timeArray,hpa.supplemental_Heat, "r", label = "Supplemental needed")
        a.plot_date(hpa.timeArray,hpa.capacity_Max, "b", label = "Maximum Capacity")
        a.plot_date(hpa.timeArray,hpa.QC_required, "y", label = "Cooling required")
    
        a.legend(bbox_to_anchor=(0,0.92,1,.102),loc=3, ncol=4, borderaxespad=0)
        
#        title = "Heat Pump Performance for "+hp.Manufacturer + " Model " + hp.OutdoorUnit
        title = "Heat Pump Performance for "+hp.Brand + " Model " + hp.OutdoorUnit
        a.set_title(title)
        f.canvas.draw()
        
        hpa.updateGraph = False
        
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

        for F in (StartPage,HomePage, FuelDeliveryPage, BaselineHeatingPage,        
                SelectHeatPumpPage,SupplementalHeatPage,FuelOptionsPage,GraphPage,EconomicsPage):
            
            frame = F(container,self)
            self.frames[F] = frame
            frame.grid(row=0,column=0,sticky="nsew")
            
        self.show_frame(StartPage)
        self.lift()
        
    def show_frame(self,cont):
        frame = self.frames[cont]
        frame.tkraise()

def LoadDeliveriesDlg(parent,listbox,lbHdr) :
    
    fname = filedialog.askopenfilename(filetypes=( ("text files","*.txt"),("All files","*.*") ), 
    title="Select file containing oil deliveries data" )
    if fname is None:
        print("no file selected")
    else:
        hpa.loadFuelDeliveries(fname)
        UpdateDeliveryHdrView(lbHdr)    
        UpdateDeliveryDataView(listbox)
        UpdateDeliveryGraph(parent)
    
def SaveDeliveriesDlg() :
    
    fname = filedialog.asksaveasfilename(filetypes=( ("text files","*.txt"),("All files","*.*") ), 
    title="Select file to save fuel deliveries data" )
    if len(fname)>0:
        print("Saving delivery data to %s" % fname)
        hpa.saveFuelDeliveries(fname)

def UpdateDeliveryDataView(listbox):
    listbox.delete(0,END)
    for h in range(hpa.numDeliveries) :
        datastring = "\t\t%s\t\t$%.2f\t\t%.1f" % (hpa.purchase_Date[h],hpa.purchase_Cost[h],hpa.purchase_Quantity[h])
        listbox.insert(h,datastring)

def UpdateDeliveryHdrView(lb):
    lb.delete(0,END)
    
    if len(hpa.fuelDeliveryHeader)>0 :
        hl = hpa.fuelDeliveryHeader.split('\n')
        for h in range(len(hl)):
            hdrString = "\t\t"+hl[h]
            lb.insert(h,hl[h])
    else:
        lb.insert(0,"\t\tNo delivery data entered")    
        
def ClearDeliveryData(self,listbox):
    
    # clear the data
    hpa.ClearDeliveryData()
    
    # Update the listbox    
    UpdateDeliveryDataView(listbox)
    UpdateDeliveryGraph(self)
        
def UpdateDeliveryGraph(self):
    ohehour = datetime.timedelta(hours=1)
    tArray = []
    fuel_required = []
    monthdays = 365/12.
    months1 = 12.
    
    updateGraph=True
    if updateGraph :
        for i in range(len(hpa.purchase_Date)):
            
            if i<len(hpa.purchase_Date)-1:
                days = (hpa.purchase_Date[i+1]-hpa.purchase_Date[i]).days
            else:
                days = (hpa.purchase_Date[i]-hpa.purchase_Date[i-1]).days
            months0 = months1
            months1 = days/monthdays
            
            theDate = hpa.purchase_Date[i]
            time = datetime.datetime(theDate.year,theDate.month,theDate.day,0,0)
            tArray.append(time)
            time = datetime.datetime(theDate.year,theDate.month,theDate.day,1,0)
            tArray.append(time)
            if i>0:
                fuel_required.append(hpa.purchase_Quantity[i-1]/months0)
            else:
                fuel_required.append(hpa.purchase_Quantity[i]/months1)
                
            fuel_required.append(hpa.purchase_Quantity[i]/months1)
            
        ta1 = []
        ma1 = []
        if len(tArray)>0:
            ta1.append(tArray[0])
            ta1.append(tArray[0])
            ta1.append(tArray[-1])
            ma1.append(0)
            ma1.append(hpa.WaterHeatMonthlyUsage)    
            ma1.append(hpa.WaterHeatMonthlyUsage)
    
        a3.clear()
        a3.plot_date(tArray,fuel_required, "g", label = "Total monthly fuel consumption")   

        if hpa.WaterHeatType==hpa.BaseHeatType and hpa.WaterHeatCombinedBill:
            a3.plot_date(ta1, ma1, "r", label = "Fuel for water and cooking")    

        a3.legend(bbox_to_anchor=(0,0.92,1,.102),loc=3, ncol=3, borderaxespad=0)
        
        title = "Fuel consumption over time"
        a3.set_title(title)
        f3.canvas.draw()

    updateGraph=False

class StartPage(tk.Frame) :
        
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        
        label=ttk.Label(self,text="NOTICE: This heat pump analysis tool is for evaluating the utility and economics for Cold Climate Heat\n"+    
        "Pumps as an alternative for residential heating in place of fuel oil, electric resistance and natural gas, and also hot water.\n"+
        "The original version was adaptated from the Tufts ME145 Spring 2015 project by J.Kadako et al.\n"+
        "Results are not guaranteed, and only as good as the data and assumptions going into it.  Use at your own risk",font=NORM_FONT)        
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
            input = open(hpa.workingDirectory+"/LICENSE")
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

        self._First = True
        self.controller = controller
        
    def LayoutFrame(self):
        
        label=ttk.Label(self,text="Home Page",font=LARGE_FONT)        
        label.pack(pady=10,padx=10)
        
        statusBar = tk.Label(self,text="Status: idle",font=SMALL_FONT,bd=1,relief=SUNKEN,anchor=W)        
        statusBar.pack(side=BOTTOM, fill=X)

        ys = 5
        text1=tk.Text(self,font=SMALL_FONT, height=30, width=150)
        text1.insert(END,"\nResults:\n")
        button1 = ttk.Button(self,width=26,text="Baseline Heating Scenario",
                    command = lambda: self.controller.show_frame(BaselineHeatingPage))
        button1.pack(pady=ys)

        button2 = ttk.Button(self,width=26,text="Fuel Purchase History",
                    command = lambda: self.controller.show_frame(FuelDeliveryPage))
        button2.pack(pady=ys)

        button3 = ttk.Button(self,width=26,text="Heat Pump System Options",
                    command = lambda: self.controller.show_frame(SelectHeatPumpPage))
        button3.pack(pady=ys)

        button3s = ttk.Button(self,width=26,text="Supplemental Heat Options",
                    command = lambda: self.controller.show_frame(SupplementalHeatPage))
        button3s.pack(pady=ys)

        def doAnalysis():
            msg = hpa.doHeatPumpAnalysis(statusBar)
            if len(msg) <100:
                popupmsg("Heat Pump Analysis Tool", msg)
                
            text1.insert(END,msg)    
            if hpa.updateGraph:
                animate(0)
                
        button4 = ttk.Button(self,width=26,text="Fuel Options",command = lambda:self.controller.show_frame(FuelOptionsPage) )
        button4.pack(pady=ys)

        button4 = ttk.Button(self,width=26,text="Do Analysis",command = lambda: doAnalysis() )
        button4.pack(pady=ys)

        button5 = ttk.Button(self,width=26,text="Show Graph",
                    command = lambda: self.controller.show_frame(GraphPage))
        button5.pack(pady=ys)
        
        button6 = ttk.Button(self,width=26,text="Economics",
                    command = lambda: self.controller.show_frame(EconomicsPage))
        button6.pack(pady=ys)
        
        buttonQ = ttk.Button(self,width=26,text = "Quit", command = quit)
        buttonQ.pack(pady=ys)

        text1.pack()

    def tkraise(self):
        if self._First:
            self.LayoutFrame()
            self._First = False
        tk.Frame.tkraise(self)
        
class FuelDeliveryPage(tk.Frame):

    def tkraise(self):
        if self._First:
            self.LayoutFrame()
            self._First = False
            
        UpdateDeliveryGraph(self)
        tk.Frame.tkraise(self)
        
    def AddDelivery(self,listbox):
        # dialog to inquire date cost and volume
        
        sel = listbox.curselection()
        if len(sel)>0:
            id = sel[0]        
            date = hpa.purchase_Date[id]
            self.lastmonth = date.month
            self.lastyear = date.year
            
        cd = CalendarDialog(title="Select delivery date", month=self.lastmonth,year=self.lastyear)
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
        for date in hpa.purchase_Date:
            if date < dDate:
                id = hpa.purchase_Date.index(date)+1
            
        # insert into lists
        hpa.AddDelivery(id,dDate,dCost,dAmount)
                
        UpdateDeliveryDataView(listbox)
        UpdateDeliveryGraph(self)

    def EditDelivery(self,listbox):
        # get index to delivery
        sel = listbox.curselection()
        if len(sel)>0:
            id = sel[0]
        
            date = hpa.purchase_Date[id]
            cost = hpa.purchase_Cost[id]
            amount = hpa.purchase_Quantity[id]
        else:
            popupmsg("Edit Delivery Date","Select entry from list to edit")
            return
            
        self.lastmonth = date.month
        self.lastyear = date.year

        # todo : change calendar dialog to allow default date selection (not just month and year)
        cd = CalendarDialog(title="Select delivery date", month=self.lastmonth,year=self.lastyear) # ,day=date.day)
        dDate=cd.result
        # if date changed, get new index
        if (dDate.month!=date.month or dDate.year != date.year or dDate.day!=date.day):
            for newId in range(len(hpa.purchase_Date))-1:
                nextDate = hpa.purchase_Date[newId+1]
                pass
                
            # find new id
            # delete from existing loc, insert into new loc
            return
            
            self.lastmonth=dDate.month
            self.lastyear=dDate.year
        
        dc=GetFloat("Enter $ cost (w/o $ sign)",default=self.lastcost)
        dCost=dc.result
        self.lastcost=dCost
        
        da=GetFloat("Enter amount",default=self.lastamount)
        dAmount=da.result
        self.lastamount=dAmount
            
        # update entry in lists
        
        UpdateDeliveryDataView(listbox)
        UpdateDeliveryGraph(self)

    def DeleteDelivery(self,listbox):
        # inquire "Are you sure" (proceed, cancel options, with don't ask again option)
        
        # get index to delivery
        sel = listbox.curselection()
        if len(sel)>0:
            id = sel[0]
        
            # delete entry from lists
            hpa.DeleteDelivery(id)
           
            UpdateDeliveryDataView(listbox)
            UpdateDeliveryGraph(self)

    def __init__(self,parent,controller):
        
        tk.Frame.__init__(self,parent)
        self._First = True
        self.controller = controller
        
    def LayoutFrame(self):
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
                    command = lambda: self.controller.show_frame(HomePage))
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
        self.lastyear=hpa.current_Heating_Year
        self.lastcost=0.0
        self.lastamount=0.0

class FuelOptionsPage(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        self._First = True
        self.controller = controller

    def tkraise(self):
        if self._First:
            self.LayoutFrame()
            self._First = False
        tk.Frame.tkraise(self)
            
    def LayoutFrame(self):
        ys = 5
        labelW=ttk.Label(self,text="Standard unit prices",font=NORM_FONT)
        labelW.grid(row=1,column=4,columnspan=3,pady=20,padx=10)

        def setStandardPrice(fuel, e):
            if fuel==0:
                standardPrice = hpa.STANDARD_PRICE_OIL
            elif fuel==1:
                standardPrice = hpa.STANDARD_PRICE_GAS
            elif fuel==2:
                standardPrice = hpa.STANDARD_PRICE_ELEC
            elif fuel==3:
                standardPrice = hpa.STANDARD_PRICE_LPG
            s = GetFloat("Standard price per unit (w/o $ sign)", default=standardPrice)
            weff = s.result
            try:
                standardPrice = float(weff)
                if fuel==0:
                    hpa.STANDARD_PRICE_OIL = standardPrice
                elif fuel==1:
                    hpa.STANDARD_PRICE_GAS = standardPrice
                elif fuel==2:
                    hpa.STANDARD_PRICE_ELEC = standardPrice
                elif fuel==3:
                    hpa.STANDARD_PRICE_LPG = standardPrice
            except:
                print("bad value")

            e.config(text=weff)
            e.update()

        p0 = "$%.2f" % hpa.STANDARD_PRICE_OIL
        p1 = "$%.3f" % hpa.STANDARD_PRICE_GAS
        p2 = "$%.3f" % hpa.STANDARD_PRICE_ELEC
        p3 = "$%.2f" % hpa.STANDARD_PRICE_LPG
        en0 = ttk.Label(self,text=p0,width=6)
        en0.grid(row=2,column=5, pady = ys)
        en1 = ttk.Label(self,text=p1,width=6)
        en1.grid(row=3,column=5, pady = ys)
        en2 = ttk.Label(self,text=p2,width=6)
        en2.grid(row=4,column=5, pady = ys)
        en3 = ttk.Label(self,text=p3,width=6)
        en3.grid(row=5,column=5, pady = ys)

        bt0 = ttk.Button(self,text=hpa.HEAT_NAME_OIL, width=15, command = lambda: setStandardPrice(0,en0))
        bt0.grid(row=2,column=4, pady = ys)
        bt1 = ttk.Button(self,text=hpa.HEAT_NAME_GAS, width=15, command = lambda: setStandardPrice(1,en1))
        bt1.grid(row=3,column=4, pady = ys)
        bt2 = ttk.Button(self,text=hpa.HEAT_NAME_ELEC,width=15, command = lambda: setStandardPrice(2,en2))
        bt2.grid(row=4,column=4, pady = ys)
        bt3 = ttk.Button(self,text=hpa.HEAT_NAME_LPG, width=15, command = lambda: setStandardPrice(3,en3))
        bt3.grid(row=5,column=4, pady = ys)

        eu0 = ttk.Label(self,text="per "+hpa.UNITS_OIL,width=10)
        eu0.grid(row=2,column=6, pady = ys)
        eu1 = ttk.Label(self,text="per "+hpa.UNITS_GAS,width=10)
        eu1.grid(row=3,column=6, pady = ys)
        eu2 = ttk.Label(self,text="per "+hpa.UNITS_ELEC,width=10)
        eu2.grid(row=4,column=6, pady = ys)
        eu3 = ttk.Label(self,text="per "+hpa.UNITS_LPG,width=10)
        eu3.grid(row=5,column=6, pady = ys)

        button4 = ttk.Button(self,text="Done",
                    command = lambda: self.controller.show_frame(HomePage))
        button4.grid(row=9,column=6)

    
class BaselineHeatingPage(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        self._First = True
        self.controller = controller

    def tkraise(self):
        if self._First:
            self.LayoutFrame()
            self._First = False
        tk.Frame.tkraise(self)
            
    def LayoutFrame(self):
        label=ttk.Label(self,text="Baseline Heating Scenario: the exisiting system with the fuel consumption specified",font=LARGE_FONT)
        label.grid(row=0,column=2,columnspan=3,pady=10,padx=10)
  
        label1=ttk.Label(self,text="Baseline heating system type, efficiency, and operating parameters",font=NORM_FONT)
        label1.grid(row=1,column=2,columnspan=3,pady=20,padx=10)
        
        BLType = IntVar()
        BLType.set(0)
        
        rb1 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_OIL, variable=BLType, value=0, command=lambda: hpa.SetBLScenario(0))
        rb2 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_GAS, variable=BLType, value=1, command=lambda: hpa.SetBLScenario(1))
        rb3 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_ELEC,variable=BLType, value=2, command=lambda: hpa.SetBLScenario(2))
        rb4 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_LPG, variable=BLType, value=3, command=lambda: hpa.SetBLScenario(3))
        rb5 = tk.Radiobutton(self, width=16, text="Other",           variable=BLType, value=4, command=lambda: hpa.SetBLScenario(4))

        ys = 5
        rb1.grid(row=2,column=0,padx=20, pady = ys)
        rb2.grid(row=3,column=0,padx=20, pady = ys)
        rb3.grid(row=4,column=0,padx=20, pady = ys)
        rb4.grid(row=5,column=0,padx=20, pady = ys)
        rb5.grid(row=6,column=0,padx=20, pady = ys)
        rb1.invoke()
        
        def getEfficiency(self):
            s = GetFloat("Enter system efficiency in %", default=100*hpa.BaseHvacEfficiency, min=10., max=100.)
            eff = s.result
            try:
                hpa.BaseHvacEfficiency = float(eff/100.)
            except:
                print("bad value")

            e.config(text=eff)
            e.update()

        eff = '{0:2.1f}'.format(100.*hpa.BaseHvacEfficiency)
        e = ttk.Label(self, width=5, text=eff)
        e.grid(row=2, column=3, pady = ys)

        btn1 =ttk.Button(self,text="System Efficiency",width=20,  command=lambda: getEfficiency(e))
        btn1.grid(row=2,column=2,padx=10, pady = ys)

        def setStartDate(e) :
            cd = CalendarDialog(self,year=2012,month=7)
            hpa.turn_ON_Date = datetime.date(cd.result.year, cd.result.month, cd.result.day)         
            e.config(text=hpa.turn_ON_Date)
        def setEndDate(e) :
            cd = CalendarDialog(self)
            hpa.turn_OFF_Date = datetime.date(cd.result.year, cd.result.month, cd.result.day)           
            e.config(text=hpa.turn_OFF_Date)

        def setTempSetPoint(e): 
            s = GetFloat("Temperature set point", default=hpa.WinterBLSetPoint, min=50., max=90.)
            weff = s.result
            try:
                hpa.WinterBLSetPoint = float(weff)
            except:
                print("bad value")

            e.config(text=weff)
            e.update()
        def setACSetPoint(e): 
            s = GetFloat("Temperature set point", default=hpa.SummerBLSetPoint, min=50., max=90.)
            weff = s.result
            try:
                hpa.SummerBLSetPoint = float(weff)
            except:
                print("bad value")

            e.config(text=weff)
            e.update()
            

        label3=ttk.Label(self,text="Set Annual System Start/End Dates",font=SMALL_FONT)
        label3.grid(row=3,column=2,columnspan=2,padx=10, pady = ys)
            
        labelSD = ttk.Label(self,text=hpa.turn_ON_Date)
        labelSD.grid(row=4,column=3, pady = ys)
        
        button2 = ttk.Button(self,text="Start Date",width=20, command = lambda: setStartDate(labelSD))
        button2.grid(row=4,column=2, pady = ys)

        labelED = ttk.Label(self,text=hpa.turn_OFF_Date)
        labelED.grid(row=5,column=3, pady = ys)

        button3 = ttk.Button(self,text="End Date",width=20, command = lambda: setEndDate(labelED))
        button3.grid(row=5,column=2, pady = ys)

        label3=ttk.Label(self,text="Thermostat set point",font=SMALL_FONT)
        label3.grid(row=3,column=4,columnspan=2,padx=10, pady = ys)
            
        labelT = ttk.Label(self,text=str(hpa.WinterBLSetPoint))
        button2a = ttk.Button(self,text="Temperature",width=15, 
                    command = lambda: setTempSetPoint(labelT))
        button2a.grid(row=4,column=4, pady = ys)
        labelT.grid(row=4,column=5, pady = ys)
        labelTs = ttk.Label(self,text="deg F")
        labelTs.grid(row=4,column=6, pady = ys)

        
        labelW=ttk.Label(self,text="Baseline hot water type parameters",font=NORM_FONT)
        labelW.grid(row=10,column=2,columnspan=2,pady=20,padx=10)

        def getWaterUse(e):
            s = GetFloat("Estimate monthly heat units for water", default=hpa.WaterHeatMonthlyUsage, min=0.)
            weff = s.result
            try:
                hpa.WaterHeatMonthlyUsage = float(weff)
            except:
                print("bad value")

            e.config(text=weff)
            e.update()

        btnTxt = "Estimated monthly " + hpa.WaterEnergyUnits

#        weff = '{0:.0f}'.format(hpa.WaterHeatMonthlyUsage)
        weff = '%.1f' % hpa.WaterHeatMonthlyUsage
        ew = ttk.Label(self, width=5, text=weff)
        ew.grid(row=12, column=3)
        btn1 =ttk.Button(self,text=btnTxt, width=20, command=lambda: getWaterUse(ew))
        btn1.grid(row=12,column=2)

        def setBLW(type):
            hpa.SetBLWScenario(type)
            btt = "Estimated Monthly %s" % (hpa.WaterEnergyUnits)
            btn1.config(text=btt)
            btn1.update()
            ett = "%.1f" % (hpa.WaterHeatMonthlyUsage)
            ew.config(text=ett)
            ew.update()

        BLWType = IntVar()
        BLWType.set(0)
        rbw1 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_OIL, variable=BLWType, value=0, command=lambda: setBLW(0))
        rbw2 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_GAS, variable=BLWType, value=1, command=lambda: setBLW(1))
        rbw3 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_ELEC,variable=BLWType, value=2, command=lambda: setBLW(2))
        rbw4 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_LPG, variable=BLWType, value=3, command=lambda: setBLW(3))
        rbw1.grid(row=12,column=0,padx=20, pady = ys)
        rbw2.grid(row=13,column=0,padx=20, pady = ys)
        rbw3.grid(row=14,column=0,padx=20, pady = ys)
        rbw4.grid(row=15,column=0,padx=20, pady = ys)
        rbw1.invoke()


        labelAC=ttk.Label(self,text="Baseline air conditioning parameters",font=NORM_FONT)
        labelAC.grid(row=20,column=2,columnspan=3,pady=20,padx=10)

        BLAType = IntVar()
        BLAType.set(0)
        rba1 = tk.Radiobutton(self, width=16, text="None", variable=BLAType, value=0, command=lambda: hpa.SetBLAScenario(0))
        rba2 = tk.Radiobutton(self, width=16, text="Central", variable=BLAType, value=1, command=lambda: hpa.SetBLAScenario(1))
        rba3 = tk.Radiobutton(self, width=16, text="Windows",variable=BLAType, value=2, command=lambda: hpa.SetBLAScenario(2))
        rba1.grid(row=22,column=0,padx=20, pady = ys)
        rba2.grid(row=23,column=0,padx=20, pady = ys)
        rba3.grid(row=24,column=0,padx=20, pady = ys)
        rba1.invoke()

        def getACSEER(e):
            s = GetFloat("Central AC SEER Rating", default=hpa.BaselineSEER, min=0.)
            weff = s.result
            try:
                hpa.BaselineSEER = float(weff)
            except:
                print("bad value")

            e.config(text=weff)
            e.update()

        if hpa.BaselineAC == 1 :
            weff = '{0:.0f}'.format(hpa.BaselineSEER)
        else:
            weff = ""
        eA = ttk.Label(self, width=5, text=weff)
        eA.grid(row=23, column=3)
        
        btnA1 =ttk.Button(self,text="SEER", width=20, command=lambda: getACSEER(eA))
        btnA1.grid(row=23,column=2)

        label3A=ttk.Label(self,text="A/C set point",font=SMALL_FONT)
        label3A.grid(row=22,column=4,columnspan=2,padx=10, pady = ys)
            
        labelAT = ttk.Label(self,text=str(hpa.SummerBLSetPoint))
        buttonA2a = ttk.Button(self,text="Temperature",width=15, 
                    command = lambda: setACSetPoint(labelAT))
        buttonA2a.grid(row=23,column=4, pady = ys)
        labelAT.grid(row=23,column=5, pady = ys)
        labelTd = ttk.Label(self,text="deg F")
        labelTd.grid(row=23,column=6, pady = ys)

        button4 = ttk.Button(self,text="Done",width=20, 
                    command = lambda: self.controller.show_frame(HomePage))
        button4.grid(row=30, column=2,pady=30)

def selHeatPump(H,info):
    global firstPlot

    heatPump = hpa.HPList[H]
    if len(hpa.HPChoice)==0 :
        hpa.HPChoice.insert(0,heatPump)
    else:
        hpa.HPChoice[0] = heatPump
        
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
        
#    title = "COP for " + heatPump.Manufacturer +" Model " + heatPump.OutdoorUnit
    title = "COP for " + heatPump.Brand +" Model " + heatPump.OutdoorUnit
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
    hpa.HPChoice.insert(0,None)
    selHeatPump(H,info)
 
def clearHeatPump(info):
    hpa.HPChoice.clear()
    updateHeatPumpInfo(info)
 
def updateHeatPumpInfo(info):
    ### update text box with chosen heat pump information"""
    infoText = ""
    for hp in hpa.HPChoice:
        infoText+= hp.Brand + "-" + hp.OutdoorUnit + "," + hp.DuctedDuctless + "\n"
#        infoText+= hp.Manufacturer + "-" + hp.OutdoorUnit + "," + hp.DuctedDuctless + "\n"
        
    info.config(text=infoText)
    info.update()
        
class SelectHeatPumpPage(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        self._First = True
        self.controller = controller

    def tkraise(self):
        if self._First:
            self.LayoutFrame()
            self._First = False
        tk.Frame.tkraise(self)
            
    def LayoutFrame(self):
        HPFilter = ['Ductless','Ducted','All']

        HPListIndex2ID = []
        
        label=ttk.Label(self,text="\tHeat Pump Selection Page: View parameters for NEEP recommended cold climate heat pumps\n",font=LARGE_FONT)
        label.grid(row=0,column=0,columnspan=5, sticky=(W,E))

#        Would like to have a manufacturers list box, and filter the heatpump models offered by that manufacturer
#        lbM = tk.Listbox(self,selectmode=tk.SINGLE,height=15,width=15)        

        lb = tk.Listbox(self,selectmode=tk.SINGLE,height=15,width=50)

        HPType = IntVar()
        HPType.set(0)
                    
        def FillHPListBox(lb, filterVar):
            HPListIndex2ID.clear()
            lb.delete(0,lb.size())
            filter = filterVar    # the string variable
            filter = HPFilter[filter]
            h = 0
            for hp in hpa.HPList:
                ductless = (hp.DuctedDuctless == 'Ductless')
                if ( (ductless and (filter=='Ductless' or filter=='All')) or ((not ductless) and (filter != 'Ductless'))) :
                    insertText = hp.Brand + " Model " + hp.OutdoorUnit + " " + hp.DuctedDuctless
#                    insertText = hp.Manufacturer + " Model " + hp.OutdoorUnit + " " + hp.DuctedDuctless
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
            s = GetFloat("Temperature set point", default=hpa.WinterHPSetPoint, min=40., max=100.)
            weff = s.result
            try:
                hpa.WinterHPSetPoint = float(weff)
            except:
                print("bad value")
            e.config(text=weff)
            e.update()

        def setHATSetPoint(e): 
            s = GetFloat("Temperature set point", default=hpa.SummerHPSetPoint, min=60., max=100.)
            weff = s.result
            try:
                hpa.SummerHPSetPoint = float(weff)
            except:
                print("bad value")
            e.config(text=weff)
            e.update()

        labelHHT = ttk.Label(self,text=str(hpa.WinterHPSetPoint))
        buttonA2a = ttk.Button(self,text="Winter Temp Set Point",width=20, 
                    command = lambda: setHHTSetPoint(labelHHT))
        buttonA2a.grid(row=5,column=3)
        labelHHT.grid(row=5,column=4)

        labelHAT = ttk.Label(self,text=str(hpa.SummerHPSetPoint))
        buttonA2b = ttk.Button(self,text="Summer Temp Set Point",width=20, 
                    command = lambda: setHATSetPoint(labelHAT))
        buttonA2b.grid(row=6,column=3)
        labelHAT.grid(row=6,column=4)

        text2b = ttk.Label(self,text='Heat Pump Hot Water',font=NORM_FONT)
        text2b.grid(row=6,column=0,columnspan=3,pady=30, sticky=(N,E,W))

        def addHeatPumpHW(e):
            s = GetFloat("Average COP of H.P. Water Heater", default=hpa.HPWaterHeaterCOP,min=0.0, max=4.0)
            weff = s.result
            try:
                 hpa.HPWaterHeaterCOP = float(weff)
            except:
                print("bad value")
            weff = "Heat Pump Water Heater, COP=%.1f" % (hpa.HPWaterHeaterCOP)
            e.config(text=weff)
            e.update()
            
        def delHeatPumpHW(e):
            weff = "No H.P. Water Heater installed"
            hpa.HPWaterHeaterCOP = 0
            e.config(text=weff)
            e.update()
            
        text3 = ttk.Label(self,text='',font=NORM_FONT)
        button5 = ttk.Button(self,text="Add H.P. Water Heater",width = 20, command = lambda: addHeatPumpHW(text3))
        button5.grid(row=7, column=0)
        
        button6 = ttk.Button(self,text="No H.P. Water Heater",width=20, command = lambda: delHeatPumpHW(text3))
        button6.grid(row=7, column=1)

        text3.grid(row=7,column=2,columnspan=3,sticky=(N,E,W))
       
        button4 = ttk.Button(self,text="Done", width=20, command = lambda: self.controller.show_frame(HomePage))
        button4.grid(row=10,column=2, pady=30)        

class SupplementalHeatPage(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        self._First = True
        self.controller = controller

    def tkraise(self):
        if self._First:
            self.LayoutFrame()
            self._First = False
        tk.Frame.tkraise(self)
            
    def LayoutFrame(self):

        label=ttk.Label(self,text="Supplemental Heating System: back up heating system for coldest days",font=LARGE_FONT)
        label.grid(row=0,column=2,columnspan=3,pady=10,padx=10)
  
        label1=ttk.Label(self,text="Supplemental heating system type, efficiency, and operating parameters",font=NORM_FONT)
        label1.grid(row=1,column=2,columnspan=3,pady=30,padx=10)
        
        BLType = IntVar()
        BLType.set(0)
        
        rb1 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_OIL, variable=BLType, value=0, command=lambda: hpa.SetSuppHeat(0))
        rb2 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_GAS, variable=BLType, value=1, command=lambda: hpa.SetSuppHeat(1))
        rb3 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_ELEC,variable=BLType, value=2, command=lambda: hpa.SetSuppHeat(2))
        rb4 = tk.Radiobutton(self, width=16, text=hpa.HEAT_NAME_LPG, variable=BLType, value=3, command=lambda: hpa.SetSuppHeat(3))
        rb5 = tk.Radiobutton(self, width=16, text="None",       variable=BLType, value=4, command=lambda: SetSuppHeatio(4))

        ys = 5
        rb1.grid(row=2,column=0,padx=20, pady = ys)
        rb2.grid(row=3,column=0,padx=20, pady = ys)
        rb3.grid(row=4,column=0,padx=20, pady = ys)
        rb4.grid(row=5,column=0,padx=20, pady = ys)
        rb5.grid(row=6,column=0,padx=20, pady = ys)
        rb1.invoke()
        
        def getEfficiency(e):
            s = GetFloat("Enter system efficiency in %", default=100*hpa.SuppHvacEfficiency, min=10, max=100)
            eff = s.result
            try:
                hpa.SuppHvacEfficiency = float(eff/100.)
            except:
                print("bad value")

            e.config(text=eff)
            e.update()
        def getOTNABL(e):
            s = GetInt("Enter outdoor temp for supplemental heat to kick in %", default=hpa.SuppOutdoorTempNABL, min=-50, max=50)
            eff = s.result
            try:
                hpa.SuppOutdoorTempNABL = float(eff)
            except:
                print("bad value")

            e.config(text=eff)
            e.update()

        eff = '{0:2.1f}'.format(100.*hpa.SuppHvacEfficiency)
        e = ttk.Label(self, width=5, text=eff)
        e.grid(row=2, column=3, pady = ys)

        btn1 =ttk.Button(self,text="System Efficiency",width=20,  command=lambda: getEfficiency(e))
        btn1.grid(row=2,column=2,padx=10, pady = ys)

        tset = '{0:2.1f}'.format(hpa.SuppOutdoorTempNABL)
        e1 = ttk.Label(self, width=5, text=tset)
        e1.grid(row=4, column=3, pady = ys)

        btn1 =ttk.Button(self,text="Outdoor Temp Enable",width=20,  command=lambda: getOTNABL(e1))
        btn1.grid(row=4,column=2,padx=10, pady = ys)
       
        button4 = ttk.Button(self,text="Done", width=20, command = lambda: self.controller.show_frame(HomePage))
        button4.grid(row=10,column=2, pady=30)        

class GraphPage(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        
        self._First = True
        self.controller = controller

    def tkraise(self):
        if self._First:
            self.LayoutFrame()
            self._First = False
        tk.Frame.tkraise(self)
            
    def LayoutFrame(self):
        label=ttk.Label(self,text="Heat Pump Graph",font=LARGE_FONT)        
        label.pack(pady=10,padx=10)
        
        button1 = ttk.Button(self,text="Done",
                    command = lambda: self.controller.show_frame(HomePage))
        button1.pack()
        
        canvas = FigureCanvasTkAgg(f,self)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        
        toolbar = NavigationToolbar2TkAgg(canvas,self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP,fill=tk.BOTH,expand=True)

        
class EconomicsPage(tk.Frame):
    def UpdatePaybackData(self):        
        textPD = "  Year\tH.P.\tB.L.\tDelta\tH.P. CO2\tB.L. CO2\n"
        InitialCost = self.equipmentCost + self.installCost - self.rebate - self.financing
        HeatPumpCost = InitialCost
        AlternativeCost = 0
        
        ElectricRate = hpa.STANDARD_PRICE_ELEC
        BaseRate = hpa.BaseCostPerUnit
        WaterRate = hpa.WaterCostPerUnit
        SuppRate = hpa.SuppCostPerUnit
        HPEmissions = 0
        AlternativeEmissions = 0.

        BLAC = hpa.BaselineAC != 0 and hpa.SummerBLSetPoint> 0
        HPAC = hpa.SummerHPSetPoint>0

        Years = []
        HeatPumpCostByYear = []
        AlternativeCostByYear = []
        DeltaByYear = []    
        for i in range(20):

            if i==1:
                HeatPumpCost -= self.taxCredits
                
            if i==hpa.AlternativeReplacementYears:
                AlternativeCost += hpa.AlternativeReplacementCost

            Years.append(i)
            HeatPumpFinancingCost = 0.
            if i<self.financingYears:
                HeatPumpFinancingCost = 12.*self.financingPayment
                
#           HeatPumpAverageUnits = 0.
#           BaseAverageUnits=0.
            HeatPumpOperatingCost = 0.
            AlternativeOperatingCost = 0.
            SupplementalOperatingCost = 0.
            
            if len(hpa.HPChoice)>0:
                HeatPumpOperatingCost += hpa.HeatPumpAverageUnits*ElectricRate
                AlternativeOperatingCost = hpa.BaseAverageUnits*BaseRate
                if BLAC:
                    AlternativeOperatingCost += hpa.BLACAverageUnits*ElectricRate
                SupplementalOperatingCost = hpa.SuppAverageUnits*SuppRate

                HPEmissions += hpa.HeatPumpAverageUnits*hpa.ElecKgCO2PerUnit*.001
                AlternativeEmissions += hpa.BaseAverageUnits*hpa.BaseKgCO2PerUnit*.001

            if hpa.HPWaterHeaterCOP>0:
                # hot water only
                HeatPumpWaterUnits = 12*hpa.WaterHeatMonthlyUsage*(hpa.WaterHeatEfficiency*hpa.WaterEnergyContent/hpa.ElecEnergyContent)/hpa.HPWaterHeaterCOP
                WaterAverageUnits = 12*hpa.WaterHeatMonthlyUsage
                AlternativeOperatingCost += WaterAverageUnits*WaterRate
                HeatPumpOperatingCost += HeatPumpWaterUnits*ElectricRate
                
                HPEmissions += HeatPumpWaterUnits*hpa.ElecKgCO2PerUnit*.001
                AlternativeEmissions += WaterAverageUnits*hpa.WaterKgCO2PerUnit*.001
                
            if BLAC:
                AlternativeEmissions += hpa.BLACAverageUnits*hpa.ElecKgCO2PerUnit*.001
            
            HeatPumpCost += HeatPumpOperatingCost + SupplementalOperatingCost + HeatPumpFinancingCost
            AlternativeCost += AlternativeOperatingCost

            HeatPumpCostByYear.append(HeatPumpCost)
            AlternativeCostByYear.append(AlternativeCost)
            Delta = HeatPumpCost - AlternativeCost
            DeltaByYear.append(Delta)
            textline = "   %d\t$%.0f\t$%.0f\t$%.0f\t%.2f T\t%.2f T\n" % (i,HeatPumpCost,AlternativeCost,Delta,HPEmissions, AlternativeEmissions)
            textPD += textline
            
            ElectricRate *= (1.+hpa.ElectricInflationRate)
            BaseRate *= (1.+hpa.BaseInflationRate)
            SuppRate *= (1.+hpa.SuppInflationRate)
            
            if hpa.WaterHeatType == hpa.HEAT_NAME_ELEC:
                WaterRate = ElectricRate
            elif hpa.WaterHeatType==hpa.BaseHeatType:
                WaterRate = BaseRate
            
        self.textPaybackData.config(text=textPD)
        self.textPaybackData.update()
        
        a4.clear()
        a4.plot(Years,HeatPumpCostByYear, "g", label = "Heat Pump Cost")
        a4.plot(Years,AlternativeCostByYear, "r", label = "Alternative System Cost")
    
        a4.legend(bbox_to_anchor=(0,0.92,1,.102),loc=3, ncol=4, borderaxespad=0)
        
        title = "Economic Analysis"
        a4.set_title(title)
        f4.canvas.draw()
        
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        self._First = True
        self.controller = controller

    def tkraise(self):
        if self._First:
            self.LayoutFrame()
            self._First = False
 
        hpNames = ""
        for hp in hpa.HPChoice :
            hpNames += hp.Brand+'-'+hp.OutdoorUnit+"-"+hp.IndoorUnits+","
#            hpNames += hp.Manufacturer+'-'+hp.OutdoorUnit+"-"+hp.IndoorUnits+","
            self.elabel.config(text=hpNames)
            self.elabel.update()
        
        if hpa.HPWaterHeaterCOP>0:
            waterHeater = "Heat Pump Water Heater, COP=%.1f" % (hpa.HPWaterHeaterCOP)
            self.labelw.config(text=waterHeater)
            self.labelw.update()
            
        updateValues = True    
        if updateValues:
            ett = "$%.3f" % hpa.STANDARD_PRICE_ELEC
            self.efc.config(text = ett)
            self.efc.update()

        self.UpdatePaybackData()
        
        tk.Frame.tkraise(self)
                    
    def LayoutFrame(self):
        
        label=ttk.Label(self,text="Economic Payback Calculation",font=LARGE_FONT)        
        label.grid(row = 0, column = 2, columnspan=2, pady=10,padx=10)

        label1 = ttk.Label(self,text="Equipment:",font=NORM_FONT)        
        label1.grid(row = 1, column = 0, columnspan=2, pady=10,padx=10)
        
        product = "" #manufacturer+" "+outdoorUnit+"-"+indoorUnit
        self.elabel=ttk.Label(self,text=product,font=NORM_FONT,width=50)
        self.elabel.grid(row = 2, column = 0,columnspan=3)
            
        self.labelw = ttk.Label(self,text="",font=NORM_FONT, width=50)
        self.labelw.grid(row=3, column=0, columnspan=3)

        def setEquipmentCost(e):
            s = GetFloat("Equipment cost in $", default=self.equipmentCost)
            eff = s.result
            try:
                self.equipmentCost = float(eff)
                ect = "$%.0f" % self.equipmentCost
                e.config(text=ect)
                e.update()
                self.UpdatePaybackData()
            except:
                print("bad value")
        
        self.equipmentCost = 0.0
        tc = "$%.0f" % (self.equipmentCost)
        lbltc = ttk.Label(self,text=tc)
        lbltc.grid(row=6, column=1)
        button1 = ttk.Button(self,text="Equipment Total Cost",width=16,
                    command = lambda: setEquipmentCost(lbltc))
        button1.grid(row=6, column=0)
        
        def setInstallCost(e):
            s = GetFloat("Enter installation cost in $", default=self.installCost)
            eff = s.result
            try:
                self.installCost = float(eff)
                eit = "$%.0f" % self.installCost
                e.config(text=eit)
                e.update()
                self.UpdatePaybackData()
            except:
                print("bad value")

        self.installCost = 0.0
        ic = "$%.0f" % (self.installCost)
        lblic = ttk.Label(self,text=ic)
        lblic.grid(row=7, column=1)
        button2 = ttk.Button(self,text="Installation Cost",width=16,
                    command = lambda: setInstallCost(lblic))
        button2.grid(row=7, column=0)

        def setRebate(e):
            s = GetFloat("Enter rebate in $", default=self.rebate)
            eff = s.result
            try:
                self.rebate = float(eff)
                ert = "$%.0f" % self.rebate
                e.config(text=ert)
                e.update()
                self.UpdatePaybackData()
            except:
                print("bad value")
        
        self.rebate = 0.0
        rc = "($%.0f)" % (self.rebate)
        lblrc = ttk.Label(self,text=rc)
        lblrc.grid(row=8, column=1)
        button3 = ttk.Button(self,text="Rebate incentives",width=16,
                    command = lambda: setRebate(lblrc))
        button3.grid(row=8, column=0)

        def setTI(e):
            s = GetFloat("Enter tax credit in $", default=self.taxCredits)
            eff = s.result
            try:
                self.taxCredits = float(eff)
                ett = "$%.0f" % self.taxCredits
                e.config(text=ett)
                e.update()
                self.UpdatePaybackData()
            except:
                print("bad value")

        self.taxCredits = 0.0
        ti = "($%.0f)" % (self.taxCredits)
        lblti = ttk.Label(self,text=ti)
        lblti.grid(row=9, column=1)
        button4 = ttk.Button(self,text="Tax incentives",width=16,
                    command = lambda: setTI(lblti))
        button4.grid(row=9, column=0)

        def setFI(c,i,y,p):
            s = GetFloat("Enter anount to be financed in $", default=self.financing)
            self.financing = float(s.result)
            ct = "Amount: $%.0f" % (self.financing)
            c.config(text=ct)
            c.update()
            s = GetFloat("Enter interest rate in %", default=100.*self.financingInterest)
            self.financingInterest = 0.01*float(s.result)
            it = "Interest rate: %.0f%%" % (self.financingInterest*100.)
            i.config(text=it)
            i.update()
            s = GetFloat("Enter payment period in years", default=self.financingYears)
            self.financingYears = float(s.result)
            yt = "paid over %.0f years" % (self.financingYears)
            y.config(text=yt)
            y.update()
            if self.financingInterest==0.:
                self.financingPayment = self.financing/self.financingYears/12
            else:
                interest = self.financingInterest/12.
                self.financingPayment = self.financing*(interest/(1.-pow((1.+interest),-12*self.financingYears) ))
            pt = "Monthly payment: $%.2f" % (self.financingPayment)
            p.config(text=pt)
            p.update()
            self.UpdatePaybackData()
            
        self.financing = 0.0
        fat = "Amount: $%.0f" % (self.financing)
        lblfc = ttk.Label(self,text=fat)
        lblfc.grid(row=10, column=1)
        self.financingInterest = 0.05
        fit = "Interest rate: %.3f%%" % (100.*self.financingInterest)
        lblfi = ttk.Label(self,text=fit)
        lblfi.grid(row=10, column=2)
        self.financingYears = 10
        fyt = "paid over %d years" % (self.financingYears)
        lblfy = ttk.Label(self,text=fyt)
        lblfy.grid(row=10, column=3)
        self.financingPayment = 0.0
        mpt = "Monthly payment: $%.2f" % (self.financingPayment)
        lblfp = ttk.Label(self,text=mpt)
        lblfp.grid(row=10, column=4)
       
        button5 = ttk.Button(self,text="Financing",width=16,
                    command = lambda: setFI(lblfc,lblfi,lblfy,lblfp))
        button5.grid(row=10, column=0)




        textec = ttk.Label(self,text='Energy Costs:', font=NORM_FONT)
        textec.grid(row=1,column=3)

        def setEFC(c,y):
            try:
                s = GetFloat("Electricity Price in $", default=hpa.STANDARD_PRICE_ELEC)
                eff = s.result
                hpa.STANDARD_PRICE_ELEC = float(eff)
                ett = "$%.3f" % hpa.STANDARD_PRICE_ELEC
                c.config(text=ett)
                c.update()
                
                s = GetFloat("Inflation rate in %", default=100*hpa.ElectricInflationRate)
                eff = s.result
                hpa.ElectricInflationRate = 0.01*float(eff)
                ett = "Inflation: %.1f%%" % (100*hpa.ElectricInflationRate)
                y.config(text=ett)
                y.update()
                self.UpdatePaybackData()
            except Exception as e:
                print(e)

        efct = "$%.3f" % hpa.STANDARD_PRICE_ELEC
        self.efc = ttk.Label(self,text=efct,width=6)
        efit = "Inflation: %.1f%%" % (100.*hpa.ElectricInflationRate)
        efi = ttk.Label(self,text=efit,width=12)
        buttonE = ttk.Button(self,text="Electricity price",width=16,
                    command = lambda: setEFC(self.efc,efi))
        buttonE.grid(row=2, column=3)
        self.efc.grid(row=2, column=4)
        efi.grid(row=2, column=5)

        def setBFC(c,y):
            try:
                s = GetFloat("Unit price in $", default=hpa.BaseCostPerUnit)
                eff = s.result
                hpa.BaseCostPerUnit = float(eff)
                ett = "$%.3f" % (hpa.BaseCostPerUnit)
                c.config(text=ett)
                c.update()
                self.UpdatePaybackData()

                s = GetFloat("Inflation rate in %", default=100*hpa.BaseInflationRate)
                eff = s.result
                hpa.BaseInflationRate = float(eff)/100.
                ett = "Inflation: %.1f%%" % (100.*hpa.BaseInflationRate)
                y.config(text=ett)
                y.update()
                self.UpdatePaybackData()
            except:
                print("bad value")

        if hpa.BaseCostPerUnit<1.0 :
            bfct = "$%.3f" % hpa.BaseCostPerUnit
        else:
            bfct = "$%.2f" % hpa.BaseCostPerUnit
        self.bfc = ttk.Label(self,text=bfct,width=6)
        bfit = "Inflation: %.1f%%" % (100.*hpa.BaseInflationRate)
        bfi = ttk.Label(self,text=efit,width=12)
        baseFuel = hpa.BaseHeatType+" price"
        buttonB = ttk.Button(self,text=baseFuel,width=16,
                    command = lambda: setBFC(self.bfc,bfi))
        buttonB.grid(row=3, column=3)
        self.bfc.grid(row=3, column=4)
        bfi.grid(row=3, column=5)

        def setSFC(c,y):
            try:
                s = GetFloat("Supplemental unit cost in $", default=hpa.SuppCostPerUnit)
                eff = s.result
                hpa.SuppCostPerUnit = float(eff)
                ett = "$%.3f" % hpa.SuppCostPerUnit
                c.config(text=ett)
                c.update()
                self.UpdatePaybackData()

                s = GetFloat("Inflation Rate in %", default=100*hpa.SuppInflationRate)
                eff = s.result
                hpa.SuppInflationRate = float(eff)/100.
                ett = "Inflation: %.1f%%" % (100.*hpa.SuppInflationRate)
                y.config(text=ett)
                y.update()
                self.UpdatePaybackData()
            except:
                print("bad value")

        if hpa.SuppHeatType!=hpa.BaseHeatType and hpa.SuppHeatType!=hpa.HEAT_NAME_ELEC:
            if hpa.SuppCostPerUnit<1.0 :
                sfct = "$%.3f" % hpa.SuppCostPerUnit
            else:
                sfct = "$%.2f" % hpa.SuppCostPerUnit
            self.sfc = ttk.Label(self,text=sfct,width=6)
            sfit = "Inflation: %.1f%%" % (100.*hpa.SuppInflationRate)
            sfi = ttk.Label(self,text=efit,width=12)
            suppFuel = hpa.SuppHeatType+" price"
            buttonS = ttk.Button(self,text=suppFuel,width=16,
                    command = lambda: setSFC(self.sfc,sfi))
            buttonS.grid(row=4, column=3)
            self.sfc.grid(row=4, column=4)
            sfi.grid(row=4, column=5)

        textec = ttk.Label(self,text='Alternative System:', font=NORM_FONT)
        textec.grid(row=7,column=3)

        def setASC(c,y):
            try:
                s = GetFloat("Alternative system cost in $", default=hpa.AlternativeReplacementCost)
                eff = s.result
                hpa.AlternativeReplacementCost = float(eff)
                ett = "$%.0f" % (hpa.AlternativeReplacementCost)
                c.config(text=ett)
                c.update()

                s = GetFloat("Replacement time in years", default=hpa.AlternativeReplacementYears)
                eff = s.result
                hpa.AlternativeReplacementYears = float(eff)
                ett = "spent in %.0f years" % (hpa.AlternativeReplacementYears)
                y.config(text=ett)
                y.update()
                self.UpdatePaybackData()
            except:
                print("bad value")

        asct = "$%.0f" % (hpa.AlternativeReplacementCost)
        asc = ttk.Label(self,text=asct,width=6)
        asyt = "spent in %.0f years" % (hpa.AlternativeReplacementYears)
        asy = ttk.Label(self,text=asyt,width=12)
        buttonAS = ttk.Button(self,text="Alternative cost",width=16,
                    command = lambda: setASC(asc,asy))
        buttonAS.grid(row=8, column=3)
        asc.grid(row=8, column=4)
        asy.grid(row=8, column=5)


        self.textPaybackData = ttk.Label(self,text='',width=60, font=NORM_FONT)
        self.textPaybackData.grid(row=20,rowspan=2,column=0,columnspan=3, pady=10)

        self.UpdatePaybackData()
        
        canvas = FigureCanvasTkAgg(f4,self)
        canvas.show()
        canvas.get_tk_widget().grid(column=3, columnspan=3, row=20)  #fill=tk.BOTH,,pady=10
        
        button10 = ttk.Button(self,text="Done",
                    command = lambda: self.controller.show_frame(HomePage))
        button10.grid(row=0, column=4)
    
hpa.loadHeatPumps()

# main routine 

app = HeatPumpPerformanceApp()
#ani = animation.FuncAnimation(f,animate, interval=1000)
app.mainloop()
app.destroy()
