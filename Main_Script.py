import os
import numpy
import eppy
import sys
import subprocess
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.results import readhtml

import Class_ETTV
import Class_RTTV
import Class_Trop
import Class_TDSE

class GreenMark():
    def __init__(self):
        #Change EplusPath Here
        eplusPath="D:/EnergyPlusV8-6-0/energyplus.exe"

        #Automate Setting
        self.path=os.path.abspath('.')
        sys.path.append(self.path)
        self.idfName = "test6.idf"
        self.eplusPath=eplusPath
        self.iddFile = "Energy+.idd"
        IDF.setiddname(self.iddFile)
        self.outputPath="."
        self.idf1 = IDF(self.idfName)
        self.epwFile = "SGP_Singapore.486980_IWEC.epw"
        esoPath="5ZoneAirCooled.eso"

        #Call Eplus Here
        # subprocess.call([self.eplusPath,'-i',self.iddFile,'-w',self.epwFile,'-d',self.outputPath,self.idfName])

        self.htmFile = "eplustbl.htm"
        fileHandle = open(self.htmFile, 'r').read() # get a file handle to the html file
        self.eplusOutputTables = readhtml.titletable(fileHandle) # reads the tables with their titles
        
        self.ETTV=Class_ETTV.ETTV()
        self.ETTV.ETTVCalculator(self.eplusOutputTables)
        self.RTTV=Class_RTTV.RTTV()
        self.RTTV.RTTVCalculator(self.eplusOutputTables,self.idf1)
        self.Trop=Class_Trop.Trop()
        self.Trop.TropCalculator(self.eplusOutputTables,self.RTTV.RTTV)
        self.TDSE=Class_TDSE.TDSE()
        self.TDSE.TDSECalculator(self.eplusOutputTables,esoPath)

        #Output
        self.get()

    def get(self):
        print("ETTV=",self.ETTV.ETTV)
        print("")
        
        print("RTTV=",self.RTTV.RTTV)
        print("")

        Tvalue=self.Trop.value2
        Tresult=self.Trop.Trops
        Tscore=self.Trop.scores
        print("Tropicality Performance: ")
        print("Envelope U-Value=",Tvalue[0],",State=",Tresult[0],",Green Mark Score=",Tscore[0])
        print("Window Wall Ratios=",Tvalue[1]/100,",State=",Tresult[1],",Green Mark Score=",Tscore[1])
        print("Shading Coefficient=",Tvalue[2],",State=",Tresult[2],",Green Mark Score=",Tscore[2])
        print("Effective Sun Shading=",Tvalue[3],",State=",Tresult[3],",Green Mark Score=",Tscore[3])
        print("Roof U-Value=",Tvalue[4],",State=",Tresult[4],",Green Mark Score=",Tscore[4])
        print("Sky Light U-Value=",Tvalue[5],",State=",Tresult[5],",Green Mark Score=",Tscore[5])
        print("")

        print("Building Energy Performance: ")
        print("Cooling System =",self.TDSE.System)
        print("Calculated Design Load=",self.TDSE.calculatedDesignLoad,"RT")
        if self.TDSE.System=='Air Cooled Chilled Water System':
            print("Chiller Efficiency=",self.TDSE.airCooledChillerPlantEfficiency)
            print("Air Distribution Efficiency=",self.TDSE.airDistributionEfficiency)
            print("Total Efficiency=",self.TDSE.airCooledChillerPlantEfficiency+self.TDSE.airDistributionEfficiency)
        if self.TDSE.System=='Water Cooled Chilled Water System':
            print("Chiller Efficiency=",self.TDSE.waterCooledChillerPlantEfficiency)
            print("Air Distribution Efficiency=",self.TDSE.airDistributionEfficiency)
            print("Total Efficiency=",self.TDSE.waterCooledChillerPlantEfficiency+self.TDSE.airDistributionEfficiency)
        print("Efficiency Rank=",self.TDSE.Rate)