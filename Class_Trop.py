import os
import numpy
import eppy
import sys
from eppy import modeleditor
from eppy.modeleditor import IDF
from eppy.results import readhtml

class Trop:
    def TropCalculator(self,eplusOutputTables,RTTV):
        # Getting Tables That We Need From HTML or HTM
        for eplusOutputTable in eplusOutputTables:
            if 'Opaque Exterior' in str(eplusOutputTable[0]):
                opaqueExteriorTable=eplusOutputTable[1]
        for eplusOutputTable in eplusOutputTables:
            if 'Exterior Fenestration' in str(eplusOutputTable[0]):
                exteriorFenestrationTable=eplusOutputTable[1]
        for eplusOutputTable in eplusOutputTables:
            if 'Conditioned Window-Wall Ratio' in str(eplusOutputTable[0]):
                windowWallRatioTable=eplusOutputTable[1]

        #Weighted Window U-Value
        windowUs=0
        windowArea=0
        for num in range(len(exteriorFenestrationTable)):
            if 'WINDOW' in exteriorFenestrationTable[num][1]:
                windowUs=windowUs+exteriorFenestrationTable[num][5]*exteriorFenestrationTable[num][7]
                windowArea=windowArea+exteriorFenestrationTable[num][5]
        self.windowU=windowUs/windowArea

        #Weighted Wall U-Value
        wallUs=0
        wallArea=0
        for num in range(len(opaqueExteriorTable)):
            if 'WALL' in opaqueExteriorTable[num][1]:
                wallUs=wallUs+opaqueExteriorTable[num][3]*opaqueExteriorTable[num][6]
                wallArea=wallArea+opaqueExteriorTable[num][6]
        self.wallU=wallUs/wallArea

        #Overall Envelope U-Value
        self.envelopeU=(wallUs+windowUs)/(wallArea+windowArea)

        #Window-to-Wall Ratio(Each Facade)
        self.WWRs=windowWallRatioTable[-1][2:6]
        areaofFacades=windowWallRatioTable[1][2:6]
        self.WWR=0
        areaofFacade=0
        for num in range(len(self.WWRs)):
            self.WWR=self.WWR+self.WWRs[num]*areaofFacades[num]
            areaofFacade=areaofFacade+areaofFacades[num]
        self.WWR=self.WWR/areaofFacade

        #Total Effective Glass Shading Coefficient
        SC=0
        SC1=0
        SC2=0
        SCArea=0
        for num in range(len(exteriorFenestrationTable)):
            if 'WINDOW' in exteriorFenestrationTable[num][1]:
                SC=SC+exteriorFenestrationTable[num][8]*1*exteriorFenestrationTable[num][5]/0.87
                SC1=SC1+exteriorFenestrationTable[num][8]*exteriorFenestrationTable[num][5]/0.87
                SC2=SC2+1*exteriorFenestrationTable[num][5]/0.87
                SCArea=SCArea+exteriorFenestrationTable[num][5]
        self.SC=SC/SCArea
        self.SC1=SC1/SCArea
        self.SC2=SC2/SCArea

        #Weighted Roof U-Value
        roofUs=0
        roofArea=0
        for num in range(len(opaqueExteriorTable)):
            if 'ROOF' in opaqueExteriorTable[num][1]:
                roofUs=roofUs+opaqueExteriorTable[num][3]*opaqueExteriorTable[num][6]
                roofArea=roofArea+opaqueExteriorTable[num][6]
        self.roofU=roofUs/roofArea

        #Weighted Skylight or Roof Window U-Value
        skylightUs=0
        skylightArea=0
        for num in range(len(exteriorFenestrationTable)):
            if 'SKYLIGHT' in exteriorFenestrationTable[num][1]:
                skylightUs=skylightUs+exteriorFenestrationTable[num][5]*exteriorFenestrationTable[num][7]
                skylightArea=skylightArea+exteriorFenestrationTable[num][5]
        if skylightArea == 0:
            self.skylightU=0
        else:
            self.skylightU=skylightUs/skylightArea

        #RTTV
        self.RTTV=RTTV

        self.value1=[self.windowU,self.wallU,self.envelopeU,self.WWR,self.SC,self.roofU,self.skylightU,self.RTTV]
        self.value2=[self.envelopeU,self.WWR,self.SC1,self.SC2,self.roofU,self.skylightU]

        #Judgment
        # self.judgeTrop1(self.windowU,self.wallU,self.envelopeU,self.WWR,self.SC,self.roofU,self.skylightU,self.RTTV)
        self.judgeTrop2(self.envelopeU,self.WWRs,self.WWR,self.SC1,self.SC2,self.roofU,self.skylightU)

    def judgeTrop1(self,windowU,wallU,envelopeU,windowWallRatio,SC,roofU,skyLightU,RTTV):
        self.Trops=[[]]*8
        if windowU<=2.8:
            self.Trops[0]='pass'
        else:
            self.Trops[0]='fail'
        if wallU<=0.7:
            self.Trops[1]='pass'
        else:
            self.Trops[1]='fail'
        if envelopeU<=1.6:
            self.Trops[2]='pass'
        else:
            self.Trops[2]='fail'
        for num in range(len(windowWallRatio)):
            if windowWallRatio[num]>40:
                self.Trops[3]='fail'
        if self.Trops[3]==[]:
            self.Trops[3]='pass'
        if SC<=0.4:
            self.Trops[4]='pass'
        else:
            self.Trops[4]='fail'
        if roofU<=0.8:
            self.Trops[5]='pass'
        else:
            self.Trops[5]='fail'
        if skyLightU<=2.2:
            self.Trops[6]='pass'
        else:
            self.Trops[6]='fail'
        if type(RTTV)==type('a'):
            self.Trops[7]=RTTV
        elif RTTV<=50:
            self.Trops[7]='pass'
        else:
            self.Trops[7]='fail'

        for num in range(8):
            if self.Trops[num]=='fail':
                self.Trop='fail'
                return 
        self.Trop='pass'

        if self.Trop=='pass':
            self.score=1
        else:
            self.score=0

    def judgeTrop2(self,envelopeU,windowWallRatios,WWR,SC1,SC2,roofU,skyLightU):
        #Init
        self.Trops=[[]]*6
        self.scores=[0]*6

        #envelopeU
        if envelopeU<=1.6:
            self.scores[0]=0.5+(1.6-envelopeU)*2.5
            if self.scores[0]>2:
                self.scores[0]=2
            self.Trops[0]='pass'
        else:
            self.Trops[0]='fail'

        #windowWallRatios
        if windowWallRatios[1]>30:
            self.Trops[1]='fail'
        if windowWallRatios[3]>30:
            self.Trops[1]='fail'
        if WWR>40:
            self.Trops[1]='fail'
        
        if self.Trops[1]==[]:
            self.scores[1]=1+(40-WWR)/10
            if self.scores[1]>2:
                self.scores[1]=2
            self.Trops[1]='pass'
                

        #SC1
        if SC1<=0.4:
            self.scores[2]=0.5+(0.4-SC1)*10
            if self.scores[2]>2:
                self.scores[2]=2
            self.Trops[2]='pass'
            
        else:
            self.Trops[2]='fail'
        
        #SC2
        if SC2<=0.9:
            self.scores[3]=1
            if SC2<=0.7:
                self.scores[3]=2
            self.Trops[3]='pass'
        else:
            self.Trops[3]='fail'

        #roofU
        if roofU<=0.8:
            self.scores[4]=1
            self.Trops[4]='pass'
        else:
            self.Trops[4]='fail'
        
        #skylightU
        if skyLightU<=2.2:
            self.scores[5]=0.5
            self.Trops[5]='pass'
        else:
            self.Trops[5]='fail'

        #Overall
        self.score=0
        for num in range(6):
            self.score=self.score+self.scores[num]
