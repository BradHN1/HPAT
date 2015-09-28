import tkinter as tk
from tkinter import *
from tkinter import ttk
import tkSimpleDialog

LARGE_FONT = ("Verdana",20)
NORM_FONT = ("Helvetica",16)
SMALL_FONT = ("Helvetica",13)


class GetString(tkSimpleDialog.Dialog):
    """Dialog box that accepts a string value"""
    def __init__(self, msg="Enter value", default=""):
        self.msg = msg
        self.default = default
        tkSimpleDialog.Dialog.__init__(self,parent=None,title="Enter string")
    
    def body(self, master):
        self.label = ttk.Label(master,text=self.msg,font=NORM_FONT)
        self.label.pack(side="top", fill="x",pady=10)
        self.entry = tk.Entry(master, width=12, justify=CENTER)
        self.entry.bind("<Return>", self.validate)
        self.entry.delete(0,END)
        self.entry.insert(0,self.default)
        self.entry.pack(side="top", fill="x",pady=10)

#    def validate(self):
#        self.result = self.entry.get() 

    def apply(self):
        self.result = self.entry.get()


class GetFloat(tkSimpleDialog.Dialog):
    """Dialog box that accepts a float value within limits"""
    def __init__(self, msg="Enter value", default="", min=None, max=None):
        self.msg = msg
        self.min = min
        self.max = max
        self.default = default
        tkSimpleDialog.Dialog.__init__(self,parent=None,title="Enter floating point value")
    
    def body(self, master):
        self.label = ttk.Label(master,text=self.msg,font=NORM_FONT)
        self.label.pack(side="top", fill="x",pady=10)
        self.entry = tk.Entry(master, width=12, justify=CENTER)
#        self.entry.bind("<Return>", self.validate)
        self.entry.delete(0,END)
        self.entry.insert(0,self.default)
        self.entry.pack(side="top", fill="x",pady=10)

    def validate(self):
        val = self.entry.get()
        try:
            val = float(val)
        except:
            print("Invalid float value")
            return 0
        if self.min!=None and val<self.min:
            print("Value is too low")
            return 0
        elif self.max!=None and val>self.max:
            print("Value is too high")
            return 0
        else:
            return 1
            

    def apply(self):
        self.result = float(self.entry.get())


class GetInt(tkSimpleDialog.Dialog):
    """Dialog box that accepts an integer value within limits"""
    def __init__(self, msg="Enter value", default="", min=None, max=None):
        self.msg = msg
        self.min = min
        self.max = max
        self.default = default
        tkSimpleDialog.Dialog.__init__(self,parent=None,title="Enter integer value")
    
    def body(self, master):
        self.label = ttk.Label(master,text=self.msg,font=NORM_FONT)
        self.label.pack(side="top", fill="x",pady=10)
        self.entry = tk.Entry(master, width=12, justify=CENTER)
        self.entry.bind("<Return>", self.validate)
        self.entry.delete(0,END)
        self.entry.insert(0,self.default)
        self.entry.pack(side="top", fill="x",pady=10)

    def validate(self):
        val = self.entry.get()
        try:
            val = int(val)
        except:
            print("Invalid integer value")
            return 0
        if self.min!=None and val<self.min:
            print("Value is too low")
            return 0
        elif self.max!=None and val>self.max:
            print("Value is too high")
            return 0
        else:
            return 1

    def apply(self):
        self.result = int(self.entry.get())
