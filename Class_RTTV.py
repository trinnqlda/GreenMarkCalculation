import os
import numpy
import eppy
import sys
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.results import readhtml

class RTTV:
    def RTTVCalculator(self,eplusOutputTables,idf1):
        # Getting Tables That We Need From HTML or HTM
        for eplusOutputTable in eplusOutputTables:
            if 'Opaque Exterior' in str(eplusOutputTable[0]):
                opaqueExteriorTable=eplusOutputTable[1]
        for eplusOutputTable in eplusOutputTables:
            if 'Exterior Fenestration' in str(eplusOutputTable[0]):
                exteriorFenestrationTable=eplusOutputTable[1]
        for eplusOutputTable in eplusOutputTables:
            if 'Skylight-Roof Ratio' in str(eplusOutputTable[0]):
                skylightRoofRatio=eplusOutputTable[1]
        for eplusOutputTable in eplusOutputTables:
            if 'Building Area' in str(eplusOutputTable[0]):
                buildingAreaTable=eplusOutputTable[1]

        #Judge if Have Skylight in Roof
        if str(skylightRoofRatio[3][1]) != '0.0':
            # Counting How Many Roof Do We Have
            self.roofsName=[]
            self.directions=[]
            self.degrees=[]
            for num in range(len(opaqueExteriorTable)):
                if 'ROOF' in opaqueExteriorTable[num][1]:
                    self.roofsName.append(str(opaqueExteriorTable[num][0]))
                    # self.directions.append(str(opaqueExteriorTable[num][-1]))
                    self.directions.append('N')
                    self.degrees.append(str(opaqueExteriorTable[num][-2]))
            numberOfRoofs=len(self.roofsName)

            #Compute RTTV in Each Direction
            self.RTTVs=[[]]*numberOfRoofs
            self.AREAs=[[]]*numberOfRoofs
            for num in range(numberOfRoofs):
                # CF=CFMap(self.directions[num],self.degrees[num])
                CF=self.CFMap(self.directions[num],self.degrees[num])
                [self.AREAs[num],self.RTTVs[num]]=self.calRTTV1(opaqueExteriorTable,exteriorFenestrationTable,self.roofsName[num],CF)

            #Compute RTTV
            self.RTTV=0
            self.AREA=0
            for num in range(numberOfRoofs):
                self.RTTV=self.RTTV+self.RTTVs[num]*self.AREAs[num]
                self.AREA=self.AREA+self.AREAs[num]
            self.RTTV=self.RTTV/self.AREA
            self.ans=self.RTTV
            
        else:
            self.constructions = idf1.idfobjects["CONSTRUCTION"]
            self.materials = idf1.idfobjects["MATERIAL"]
            self.roofLable=[]
            #Get All The Roof
            for i in range(len(opaqueExteriorTable)):
                if 'ROOF' in opaqueExteriorTable[i][1]:
                    self.roofLable.append(i)

            #Get All the Layer In Each Roof
            layer=[[]]*len(self.roofLable)
            for j in range(len(self.roofLable)):
                if len(self.constructions[self.roofLable[j]]) == 2:
                    layer[j].append(self.constructions[self.roofLable[j]].Outside_Layer)
                elif len(self.constructions[self.roofLable[j]]) == 3:
                    layer[j].append(self.constructions[self.roofLable[j]].Outside_Layer)
                    lyer[j].append(self.constructions[self.roofLable[j]].Layer_2)
                elif len(self.constructions[self.roofLable[j]]) == 4:
                    layer[j].append(self.constructions[self.roofLable[j]].Outside_Layer)
                    layer[j].append(self.constructions[self.roofLable[j]].Layer_2)
                    layer[j].append(self.constructions[self.roofLable[j]].Layer_3)
                elif len(self.constructions[self.roofLable[j]]) == 5:
                    layer[j].append(self.constructions[self.roofLable[j]].Outside_Layer)
                    layer[j].append(self.constructions[self.roofLable[j]].Layer_2)
                    layer[j].append(self.constructions[self.roofLable[j]].Layer_3)
                    layer[j].append(self.constructions[self.roofLable[j]].Layer_4)
            
            #Get Density and Thickness and Weight of Roof material
            density=[[]]*len(self.roofLable)
            thickness=[[]]*len(self.roofLable)
            self.weight=[[]]*len(self.roofLable)
            for j in range(len(self.roofLable)):
                self.weight[j]=0
                for k in range(len(layer[j])):
                    for material in self.materials:
                        if layer[j][k] == material.Name:
                            density[j].append(material.Density)
                            thickness[j].append(material.Thickness)
                            self.weight[j]=self.weight[j]+(material.Density*material.Thickness)

            #Get the U Factor of Each Roof
            self.roofU=[[]]*len(self.roofLable)
            length=len(opaqueExteriorTable)
            for i in range(len(self.roofLable)):
                self.roofU[i]=opaqueExteriorTable[self.roofLable[i]][3]

            #Get the Net Conditioned Building Area
            self.airConditionArea=buildingAreaTable[2][1]

            #Compute the result of RTTV
            self.RTTVs=[[]]*len(self.roofLable)
            for i in range(len(self.roofLable)):
                self.RTTVs[i]=self.judgeRTTV2(self.weight[i],self.airConditionArea,self.roofU[i])
                if self.RTTVs[i] == 'fail':
                    self.RTTV='fail'
                    self.ans=self.RTTV
                    return
            self.RTTV='pass'
            self.ans=self.RTTV

    def calRTTV1(self,opaqueExteriorTable,exteriorFenestrationTable,roofsName,CF): 
        #First Part
        RTTV1=0
        roofArea=0
        for num in range(len(opaqueExteriorTable)):
            if roofsName in opaqueExteriorTable[num][0]:
                RTTV1=opaqueExteriorTable[num][3]*opaqueExteriorTable[num][6]
                roofArea=opaqueExteriorTable[num][5]
        RTTV1=12.5*RTTV1/roofArea

        #Second Part
        RTTV2=0
        for num in range(len(exteriorFenestrationTable)):
            if roofsName in exteriorFenestrationTable[num][13]:
                RTTV2=RTTV2+exteriorFenestrationTable[num][5]*exteriorFenestrationTable[num][7]
        RTTV2=4.8*RTTV2/roofArea

        #Third Part
        RTTV3=0
        for num in range(len(exteriorFenestrationTable)):
            if roofsName in exteriorFenestrationTable[num][13]:
                RTTV3=RTTV3+(exteriorFenestrationTable[num][5]*exteriorFenestrationTable[num][8]/0.87*CF)
        RTTV3=485*RTTV3/roofArea

        RTTV=RTTV1+RTTV2+RTTV3
        return [roofArea,RTTV]

    def CFMap(self,direction,degree):
        CFTable=[['', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
        ['0.0', '1.00', '1.00', '1.00', '1.00', '1.00', '1.00', '1.00', '1.00'],
        ['5.0', '1.00', '1.00', '1.00', '1.00', '1.00', '1.00', '1.00', '1.00'],
        ['10.0', '0.99', '0.99', '1.00', '1.00', '1.00', '0.99', '0.99', '0.99'],
        ['15.0', '0.98', '0.98', '0.99', '0.99', '0.99', '0.98', '0.98', '0.98'],
        ['20.0', '0.96', '0.97', '0.98', '0.98', '0.97', '0.97', '0.97', '0.96'],
        ['25.0', '0.93', '0.95', '0.96', '0.96', '0.95', '0.95', '0.95', '0.94'],
        ['30.0', '0.91', '0.92', '0.94', '0.94', '0.93', '0.93', '0.93', '0.91'],
        ['35.0', '0.88', '0.90', '0.92', '0.91', '0.90', '0.90', '0.90', '0.89'],
        ['40.0', '0.84', '0.87', '0.89', '0.88', '0.87', '0.87', '0.87', '0.85'],
        ['45.0', '0.80', '0.83', '0.86', '0.85', '0.83', '0.84', '0.84', '0.82'],
        ['50.0', '0.76', '0.80', '0.83', '0.82', '0.79', '0.80', '0.81', '0.78'],
        ['55.0', '0.72', '0.76', '0.80', '0.78', '0.75', '0.76', '0.78', '0.75'],
        ['60.0', '0.67', '0.72', '0.76', '0.74', '0.70', '0.73', '0.74', '0.71'],
        ['65.0', '0.63', '0.68', '0.73', '0.70', '0.66', '0.69', '0.71', '0.67'],]

        [rowTable,colTable]=numpy.shape(CFTable)

        col=0
        row=0

        for num1 in range(0,colTable):
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

    def judgeRTTV2(self,weightRange,airConditionArea,averageUvalue):
        if weightRange < 50:
            if airConditionArea > 500:
                if averageUvalue <= 0.5:
                    return('pass')
                elif averageUvalue > 0.5:
                    return('fail')
            elif airConditionArea <= 500:
                if averageUvalue <= 0.8:
                    return('pass')
                elif averageUvalue > 0.8:
                    return('fail')
        elif 50 <= weightRange <= 230: 
            if airConditionArea > 500:
                if averageUvalue <= 0.8:
                    return('pass')
                elif averageUvalue > 0.8:
                    return('fail')
            elif airConditionArea <= 500:
                if averageUvalue <= 1.1:
                    return('pass')
                elif averageUvalue > 1.1:
                    return('fail')
        elif weightRange > 230: 
            if airConditionArea > 500:
                if averageUvalue <= 1.2:
                    return('pass')
                elif averageUvalue > 1.2:
                    return('fail')
            elif airConditionArea <= 500:
                if averageUvalue <= 1.5:
                    return('pass')
                elif averageUvalue > 1.5:
                    return('fail')