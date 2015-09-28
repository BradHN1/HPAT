import ttkcalendar
import tkSimpleDialog

class CalendarDialog(tkSimpleDialog.Dialog):
    """Dialog box that displays a calendar and returns the selected date"""
    def __init__(self, msg="Enter date", default="", year=None, month=None):
        self.msg = msg
        self.year = year
        self.month = month
        self.default = default
        
        tkSimpleDialog.Dialog.__init__(self,parent=None,title=None)

    def body(self, master):
        kwargs = {}
        if self.month!=None:
            kwargs['month']=self.month
        if self.year!=None:
            kwargs['year']=self.year
            
        self.calendar = ttkcalendar.Calendar(master,**kwargs)
        self.calendar.pack()

    def apply(self):
        self.result = self.calendar.selection.date()
