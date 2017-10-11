import os
import sys
import numpy as np
import esoreader

class TDSE:
    def __init__(self):
        path=os.path.abspath('.')
        sys.path.append(path)
        PATH_TO_ESO="5ZoneAirCooled.eso"
        eso = esoreader.read_from_path(PATH_TO_ESO)

        CoolingTower=eso.dd.find_variable('Tower')

        if CoolingTower==[]:
            self.airCooledChilledWaterSystem(eso)
        else:
            self.waterCooledChilledWaterSystem(eso)

    def airCooledChilledWaterSystem(P,eso):
        #Daily Average Cooling Load(RT)
        #Cooling Coil Total Cooling Rate
        P.DACLs=P.findData('Cooling Coil',eso)
        P.DACL=0.000284345*sum(P.DACLs)

        #Chiller Power Input(PCH)
        #Chiller Electric Power
        P.PCHs=P.findData('Chiller',eso)
        P.PCH=0.001*sum(P.PCHs)

        #Chiller Water Pump Power(PCHWP)
        #Pump Electric Power
        P.PCHWPs=P.findData('Pump',eso)
        P.PCHWP=0.001*sum(P.PCHWPs)

        #Motor Input Power
        #Fan Electric Power
        P.TADPs=P.findData('Fan',eso)
        P.TADP=0.001*sum(P.TADPs)

        P.airCooledChillerPlantEfficiency=(P.PCH+P.PCHWP)/P.DACL
        P.airDistributionEfficiency=P.TADP/P.DACL

    def waterCooledChilledWaterSystem(P,eso):
        #Average Cooling Load(RT)
        P.DACLs=P.findData('Cooling Coil Total Cooling Rate',eso)
        P.DACL=0.000284345*sum(P.DACLs)

        #Chiller Power Input(PCH)
        P.PCHs=P.findData('Chiller',eso)
        P.PCH=0.001*sum(P.PCHs)

        #Chiller & Condenser Water Pump Power(PCHWP+PCWP)
        P.PCHWPAndPCWPs=P.findData('Pump',eso)
        P.PCHWPAndPCWP=0.001*sum(P.PCHWPAndPCWPs)

        #Cooling Tower Power(PCT)
        P.PCTs=P.findData('Tower',eso)
        P.PCT=0.001*sum(P.PCTs)

        #Air-Side
        P.TADPs=P.findData('Fan',eso)
        P.TADP=0.001*sum(P.TADPs)

        P.waterCooledChillerPlantEfficiency=(P.PCH+P.PCHWPAndPCWP+P.PCT)/P.DACL
        P.airDistributionEfficiency=P.TADP/P.DACL


    def findData(P,str,eso):
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