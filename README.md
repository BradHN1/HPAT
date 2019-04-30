# HPAT
Heat Pump Analysis Tool
Created: Brad Hubbard-Nelson, 3-September-2015

Building the application:
    
MacOS:
    Using the py2app utility 
    Following procedure in http://pythonhosted.org/py2app/tutorial.html
    
    0) start a terminal window, change directory to the HPAT folder
        
    1) create a setup.py file:
        $ py2applet --make-setup HeatPumpAnalysisTool-tkUI.py
        Wrote setup.py      ... expected response
        
    2) clean build directories:
        $ rm -rf build dist
      
    Following two steps are for building the application with "alias mode"    
    3) python3 setup.py py2app -A

    4) Run application directly from the terminal:
        $ ./dist/HeatPumpAnalysisTool-tkUI.app/Contents/MacOS/HeatPumpAnalysisTool-tkUI

    3) python3 setup.py py2app