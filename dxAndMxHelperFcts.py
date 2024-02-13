# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 10:36:59 2024

@author: wolters
"""

import os
import sys

import re

import logging

import pandas as pd

import numpy as np

import networkx as nx    

import importlib
import glob

# ---
# --- PT3S Imports
# ---
logger = logging.getLogger('PT3S')  
if __name__ == "__main__":
    logger.debug("{0:s}{1:s}".format('in MODULEFILE: __main__ Context:','.')) 
else:
    logger.debug("{0:s}{1:s}{2:s}{3:s}".format('in MODULEFILE: Not __main__ Context: ','__name__: ',__name__," .")) 

try:
    from PT3S import Dx
except ImportError:
    logger.debug("{0:s}{1:s}".format('ImportError: ','from PT3S import Dx - trying import Dx instead ... maybe pip install -e . is active ...')) 
    import Dx

try:
    from PT3S import Mx
except ImportError:
    logger.debug("{0:s}{1:s}".format('ImportError: ','from PT3S import Mx - trying import Mx instead ... maybe pip install -e . is active ...')) 
    import Mx

try:
    from PT3S import dxDecodeObjsData
except:
    import dxDecodeObjsData


class dxWithMxError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class dxWithMx():
    """Wrapper for dx with attached mx
    """
    def __init__(self,dx,mx):
        
        logStr = "{0:s}.{1:s}: ".format(self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr,'Start.')) 
        
        try: 
            self.dx = dx
            self.mx = mx
            
            self.dfLAYR=dxDecodeObjsData.Layr(self.dx)
            self.dfWBLZ=dxDecodeObjsData.Wblz(self.dx)
                        
            if self.mx != None:                
                V3sErg=self.dx.MxAdd(mx)
                self.V3_ROHR=V3sErg['V3_ROHR']
                self.V3_KNOT=V3sErg['V3_KNOT']
                self.V3_FWVB=V3sErg['V3_FWVB']
                
                V_WBLZ=self.dx.dataFrames['V_WBLZ']
                df=V_WBLZ[['pk','fkDE','rk','tk','BESCHREIBUNG','NAME','TYP','AKTIV','IDIM']]
                dfMx=mx.getVecAggsResultsForObjectType(Sir3sVecIDReExp='^WBLZ~\*~\*~\*~')
                dfMx.columns=dfMx.columns.to_flat_index()
                
                self.V3_WBLZ=pd.merge(df,dfMx,left_on='tk',right_index=True)
                
            self.G=nx.from_pandas_edgelist(df=self.dx.dataFrames['V3_VBEL'].reset_index(), source='NAME_i', target='NAME_k', edge_attr=True) 
            nodeDct=self.V3_KNOT.to_dict(orient='index')    
            nodeDctNx={value['NAME']:value|{'idx':key} for key,value in nodeDct.items()}
            nx.set_node_attributes(self.G,nodeDctNx)
      
        except dxWithMxError:
            raise            
        except Exception as e:
            logStrFinal="{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(logStr,sys.exc_info()[-1].tb_lineno,type(e),str(e))
            logger.error(logStrFinal) 
            raise dxWithMxError(logStrFinal)                       
        finally:
            logger.debug("{0:s}{1:s}".format(logStr,'_Done.'))            
        
class readDxAndMxError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def readDxAndMx(dbFile):
    """
    Returns:
        dxWithMx
    """
    
    import os
    import importlib
    import glob
    
    dx=None
    mx=None
    
    logStr = "{0:s}.{1:s}: ".format(__name__, sys._getframe().f_code.co_name)
    logger.debug("{0:s}{1:s}".format(logStr,'Start.'))     
    
    try:
        
        try:
            from PT3S import Dx
        except:
            import Dx    

        # von wo wurde geladen ...
        importlib.reload(Dx)        

        ### Modell lesen
        try:
            dx=Dx.Dx(dbFile)
        except Dx.DxError:
            logStrFinal="{logStr:s}dbFile: {dbFile:s}: DxError!".format(logStr=logStr,dbFile=dbFile)     
            raise readDxAndMxError(logStrFinal)  

        ### mx Datenquelle bestimmen
        logger.debug("{logStrPrefix:s}dbFile rel: {dbFile:s}".format(logStrPrefix=logStr,dbFile=dx.dbFile))
        dbFile=os.path.abspath(dx.dbFile)
        logger.debug("{logStrPrefix:s}dbFile abs: {dbFile:s}".format(logStrPrefix=logStr,dbFile=dbFile))

        # wDir der Db
        sk=dx.dataFrames['SYSTEMKONFIG']
        wDirDb=sk[sk['ID'].isin([1,1.])]['WERT'].iloc[0]
        logger.debug("{logStrPrefix:s} wDirAusDb: {wDirDb:s}".format(logStrPrefix=logStr,wDirDb=wDirDb))
        wDir=os.path.abspath(os.path.join(os.path.dirname(dbFile),wDirDb))
        logger.debug("{logStrPrefix:s}  wDir abs: {wDir:s}".format(logStrPrefix=logStr,wDir=wDir))

        # Modell-Pk des in QGIS anzuzeigenden Modells (wird von den QGIS-Views ausgewertet)
        # diese xk wird hier verwendet um das Modell in der DB zu identifizieren dessen Ergebnisse geliefert werden sollen
        modelXk=sk[sk['ID'].isin([3,3.])]['WERT'].iloc[0]

        # Ergebnisverz. von modelXk
        vm=dx.dataFrames['VIEW_MODELLE']
        vms=vm[vm['pk'].isin([modelXk])].iloc[0]   
        
        #wDirMxDb=os.path.join(
        #     os.path.join(
        #     os.path.join(wDirDb,vms.Basis),vms.Variante),vms.BZ)        
        
        wDirMx=os.path.join(
            os.path.join(
            os.path.join(wDir,vms.Basis),vms.Variante),vms.BZ)
        logger.debug("{logStrPrefix:s}wDirMx abs: {wDirMx:s}".format(logStrPrefix=logStr,wDirMx=wDirMx))
        
        #wDirMxRel=os.path.relpath(wDirMx,start=wDir)
        #logger.debug("{logStrPrefix:s}wDirMx rel: {wDirMx:s}".format(logStrPrefix=logStr,wDirMx=wDirMxRel))
        
        wDirMxMx1Content=glob.glob(os.path.join(wDirMx,'*.MX1'))
        wDirMxMx1Content=sorted(wDirMxMx1Content) 

        if len(wDirMxMx1Content)>1:
            logger.debug("{logStrPrefix:s}Mehr als 1 ({anz:d}) MX1 in wDirMx vorhanden.".format(
                logStrPrefix=logStr,anz=len(wDirMxMx1Content)))
        mx1File= wDirMxMx1Content[0]
        logger.debug("{logStrPrefix:s}mx1File: {mx1File:s}".format(logStrPrefix=logStr,mx1File=mx1File))
        
        ### Modellergebnisse lesen
        try:
            mx=Mx.Mx(mx1File)
        except Mx.MxError:
            logStrFinal="{logStr:s}mx1File: {mx1File:s}: MxError!".format(logStr=logStr,mx1File=mx1File)     
            raise readDxAndMxError(logStrFinal)       
            
        
        

    except Exception as e:
        logStrFinal="{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(logStr,sys.exc_info()[-1].tb_lineno,type(e),str(e))
        logger.error(logStrFinal)         
    finally:
        logger.debug("{0:s}{1:s}".format(logStr,'_Done.'))  
    
    
    return dxWithMx(dx,mx)
