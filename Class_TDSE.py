import os
import sys
import numpy as np
import esoreader

class TDSE:
    def TDSECalculator(self,eplusOutputTables,PATH_TO_ESO):
        # Getting Tables That We Need From HTML or HTM
        for eplusOutputTable in eplusOutputTables:
            if 'Zone Sensible Cooling' in str(eplusOutputTable[0]):
                zoneSensibleCoolingTable=eplusOutputTable[1]

        self.calculatedDesignLoad=0
        for num in range(1,len(zoneSensibleCoolingTable)):
            self.calculatedDesignLoad=self.calculatedDesignLoad+zoneSensibleCoolingTable[num][1]

        eso = esoreader.read_from_path(PATH_TO_ESO)

        CoolingTower=eso.dd.find_variable('Tower')

        if CoolingTower==[]:
            self.airCooledChilledWaterSystem(eso)
            self.System='Air Cooled Chilled Water System'
            self.judgeAirTDSE(self.calculatedDesignLoad,self.airCooledChillerPlantEfficiency,self.airDistributionEfficiency)
        else:
            self.waterCooledChilledWaterSystem(eso)
            self.System='Water Cooled Chilled Water System'
            self.judgeWaterTDSE(self.calculatedDesignLoad,self.waterCooledChillerPlantEfficiency,self.airDistributionEfficiency)

    def airCooledChilledWaterSystem(self,eso):
        #Daily Average Cooling Load(RT)
        #Cooling Coil Total Cooling Rate
        self.DACLs=self.findData('Cooling Coil',eso)
        self.DACL=0.000284345*sum(self.DACLs)

        #Chiller Power Input(PCH)
        #Chiller Electric Power
        self.PCHs=self.findData('Chiller',eso)
        self.PCH=0.001*sum(self.PCHs)

        #Chiller Water Pump Power(PCHWP)
        #Pump Electric Power
        self.PCHWPs=self.findData('Pump',eso)
        self.PCHWP=0.001*sum(self.PCHWPs)

        #Motor Input Power
        #Fan Electric Power
        self.TADPs=self.findData('Fan',eso)
        self.TADP=0.001*sum(self.TADPs)

        self.airCooledChillerPlantEfficiency=(self.PCH+self.PCHWP)/self.DACL
        self.airDistributionEfficiency=self.TADP/self.DACL

    def waterCooledChilledWaterSystem(self,eso):
        #Average Cooling Load(RT)
        self.DACLs=self.findData('Cooling Coil Total Cooling Rate',eso)
        self.DACL=0.000284345*sum(self.DACLs)

        #Chiller Power Input(PCH)
        self.PCHs=self.findData('Chiller',eso)
        self.PCH=0.001*sum(self.PCHs)

        #Chiller & Condenser Water Pump Power(PCHWP+PCWP)
        self.PCHWPAndPCWPs=self.findData('Pump',eso)
        self.PCHWPAndPCWP=0.001*sum(self.PCHWPAndPCWPs)

        #Cooling Tower Power(PCT)
        self.PCTs=self.findData('Tower',eso)
        self.PCT=0.001*sum(self.PCTs)

        #Air-Side
        self.TADPs=self.findData('Fan',eso)
        self.TADP=0.001*sum(self.TADPs)

        self.waterCooledChillerPlantEfficiency=(self.PCH+self.PCHWPAndPCWP+self.PCT)/self.DACL
        self.airDistributionEfficiency=self.TADP/self.DACL


    def findData(self,str,eso):
        variable=eso.dd.find_variable(str)
        index=[[]]*len(variable)
        for num in range(len(variable)):
            index[num]=eso.dd.index[variable[num]]

        dataLength=len(eso.data[index[0]])
        dayLength=dataLength/24
        
        data=[[]]*len(index)
        for num in range(len(index)):
            data[num]=np.reshape(eso.data[index[num]],(int(dayLength),24))

        Consumption6_9=[0]*len(index)
        for num in range(len(index)):
            for i in range(int(dayLength)):
                for j in range(9,19):
                    Consumption6_9[num]=Consumption6_9[num]+data[num][i][j]
            Consumption6_9[num]=Consumption6_9[num]/dayLength
        return Consumption6_9

    def judgeAirTDSE(self,calculatedDesignLoad,Efficience1,Efficience2):
        self.Rate='NONE'
        if calculatedDesignLoad<500:
            if Efficience1<=0.9:
                self.Rate='GOLD'
            if Efficience1<=0.85:
                if Efficience2<=0.25:
                    self.Rate='GOLD PLUS'
            if Efficience1<=0.78:
                if Efficience2<=0.25:
                    self.Rate='PLATINUM'
        else:
            self.Rate='Case By Case'

    def judgeWaterTDSE(self,calculatedDesignLoad,Efficience1,Efficience2):
        self.Rate='NONE'
        if calculatedDesignLoad<500:
            if Efficience1<=0.75:
                self.Rate='GOLD'
            if Efficience1<=0.7:
                if Efficience2<=0.25:
                    self.Rate='GOLD PLUS'
            if Efficience1<=0.68:
                if Efficience2<=0.25:
                    self.Rate='PLATINUM'
        else:
            if Efficience1<=0.68:
                self.Rate='GOLD'
            if Efficience1<=0.65:
                if Efficience2<=0.25:
                    self.Rate='GOLD PLUS & PLATINUM'