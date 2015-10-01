from tkinter import *

def callback(sv):
    print(sv.get())

root = Tk()
sv = StringVar()
sv.set("testing")

# sv.trace("w", lambda name, index, mode, sv=sv: callback(sv))
e = Entry(root, textvariable=sv)
e.pack()
root.mainloop()  