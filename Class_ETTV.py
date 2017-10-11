import os
import numpy
import eppy
import sys
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.results import readhtml

class ETTV:
    def ETTVCalculator(self,eplusOutputTables):
        # Getting Tables That We Need From HTML or HTM
        for eplusOutputTable in eplusOutputTables:
            if 'Opaque Exterior' in str(eplusOutputTable[0]):
                opaqueExteriorTable=eplusOutputTable[1]
        for eplusOutputTable in eplusOutputTables:
            if 'Exterior Fenestration' in str(eplusOutputTable[0]):
                exteriorFenestrationTable=eplusOutputTable[1]

        # Get Walls Information
        self.wallsName=[]
        self.directions=[]
        self.degrees=[]
        for num in range(len(opaqueExteriorTable)):
            if 'WALL' in opaqueExteriorTable[num][1]:
                self.wallsName.append(str(opaqueExteriorTable[num][0]))
                self.directions.append(str(opaqueExteriorTable[num][-1]))
                self.degrees.append(str(opaqueExteriorTable[num][-2]))
        numberOfWalls=len(self.wallsName)

        #Compute ETTV of Each Wall
        self.ETTVs = [[]] * numberOfWalls
        self.AREAs = [[]] * numberOfWalls
        for num in range(numberOfWalls):
            CF=self.CFMap(self.directions[num],self.degrees[num])
            [self.AREAs[num],self.ETTVs[num]]=self.calETTV(opaqueExteriorTable,exteriorFenestrationTable,self.wallsName[num],CF)

        #Compute ETTV
        self.ETTV=0
        self.AREA=0
        for num in range(numberOfWalls):
            self.ETTV=self.ETTV+self.ETTVs[num]*self.AREAs[num]
            self.AREA=self.AREA+self.AREAs[num]
        self.ETTV=self.ETTV/self.AREA
        self.ans=self.ETTV

    def calETTV(self,opaqueExteriorTable,exteriorFenestrationTable,wallsName,CF): 
        #First Part 
        ETTV1=0  
        for num in range(len(opaqueExteriorTable)):
            if wallsName in opaqueExteriorTable[num][0]:
                ETTV1=opaqueExteriorTable[num][3]*opaqueExteriorTable[num][6]
                wallArea=opaqueExteriorTable[num][5]
        ETTV1=12*ETTV1/wallArea

        #Second Part
        ETTV2=0
        for num in range(len(exteriorFenestrationTable)):
            if wallsName in exteriorFenestrationTable[num][13]:
                ETTV2=ETTV2+exteriorFenestrationTable[num][5]*exteriorFenestrationTable[num][7]
        ETTV2=3.4*ETTV2/wallArea

        #Third Part
        ETTV3=0
        for num in range(len(exteriorFenestrationTable)):
            if wallsName in exteriorFenestrationTable[num][13]:
                ETTV3=ETTV3+(exteriorFenestrationTable[num][5]*exteriorFenestrationTable[num][8]/0.87*CF)
        ETTV3=211*ETTV3/wallArea

        ETTV=ETTV1+ETTV2+ETTV3
        return [wallArea,ETTV]

    def CFMap(self,direction,degree):
        CFTable=[['', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
        ['70.0', '1.17', '1.33', '1.47', '1.35', '1.21', '1.41', '1.56', '1.38'],
        ['75.0', '1.07', '1.23', '1.37', '1.25', '1.11', '1.32', '1.47', '1.28'],
        ['80.0', '0.98', '1.14', '1.30', '1.16', '1.01', '1.23', '1.39', '1.20'],
        ['85.0', '0.89', '1.05', '1.21', '1.07', '0.92', '1.14', '1.31', '1.11'],
        ['90.0', '0.80', '0.97', '1.13', '0.98', '0.83', '1.06', '1.23', '1.03'],
        ['95.0', '0.73', '0.90', '1.05', '0.91', '0.76', '0.99', '1.15', '0.96'],
        ['100.0', '0.67', '0.83', '0.97', '0.84', '0.70', '0.92', '1.08', '0.89'],
        ['105.0', '0.62', '0.77', '0.90', '0.78', '0.65', '0.86', '1.01', '0.83'],
        ['110.0', '0.59', '0.72', '0.83', '0.72', '0.61', '0.80', '0.94', '0.78'],
        ['115.0', '0.57', '0.67', '0.77', '0.67', '0.58', '0.75', '0.87', '0.73'],
        ['120.0', '0.55', '0.63', '0.72', '0.63', '0.56', '0.71', '0.81', '0.69']]

        [rowTable,colTable]=numpy.shape(CFTable)

        col=0
        row=0

        for num1 in range(colTable):
            if direction==CFTable[0][num1]:
                col=num1

        for num2 in range(1,rowTable):
            if float(degree)<float(CFTable[num2][0]):
                row=num2
                break

        #interpolation part
        flagDegree1=float(CFTable[row-1][0])
        flagDegree2=float(CFTable[row][0])
        ratio=(float(degree)-flagDegree1)/(flagDegree2-flagDegree1)
        CF1=float(CFTable[row-1][col])
        CF2=float(CFTable[row][col])
        CF=ratio*CF2+(1-ratio)*CF1

        return CF