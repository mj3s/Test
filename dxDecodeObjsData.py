# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 17:12:49 2024

@author: wolters
"""

import os
import sys

import re

import logging

import pandas as pd

import numpy as np

# ---
# --- PT3S Imports
# ---
logger = logging.getLogger('PT3S')  
if __name__ == "__main__":
    logger.debug("{0:s}{1:s}".format('in MODULEFILE: __main__ Context:','.')) 
else:
    logger.debug("{0:s}{1:s}{2:s}{3:s}".format('in MODULEFILE: Not __main__ Context: ','__name__: ',__name__," .")) 


#try:
#    from PT3S import Dx
#except ImportError:
#    logger.debug("{0:s}{1:s}".format('ImportError: ','from PT3S import Dx - trying import Dx instead ... maybe pip install -e . is active ...')) 
#    import Dx

def Layr(dx):
    """Returns a df with decoded V_LAYR-Content.

    Args:
        dx: Dx-Instance 
            used: dx.dataFrames['V_LAYR']
                
    Returns:
        df:
            one row per LAYR and OBJ
            
            LAYR:
            'pk'
           ,'tk'
           ,'LFDNR' (numeric)
           ,'NAME'
           
            LAYR-Info:
           ,'AnzDerObjekteInGruppe'
           ,'AnzDerObjekteDesTypsInGruppe'    
           
            OBJ:
           ,'TYPE'
           ,'ID'
           
            OBJ-Info:
           ,'NrDesObjektesDesTypsInGruppe'
           ,'NrDesObjektesInGruppe'
           ,'GruppenDesObjektsAnz'
           ,'GruppenDesObjektsNamen'       
    
    """
    
    logStr = "{0:s}.{1:s}: ".format(__name__, sys._getframe().f_code.co_name)
    logger.debug("{0:s}{1:s}".format(logStr,'Start.')) 
    
    try: 
        
        df=pd.DataFrame()
        
        V_LAYR=dx.dataFrames['V_LAYR']
        
        V_LAYR['OBJSd']=V_LAYR.apply(lambda row: row['OBJS'].decode('utf-8').split('\t') if row['OBJS'] != None else None ,axis=1)
                
        dfs=[]
        
        for index,row in V_LAYR[~pd.isnull(V_LAYR['OBJSd'])].sort_values(by=['LFDNR']).iterrows():
            
            logger.debug("{0:s}LAYR: {1:s}:".format(logStr,row['NAME'])) 
            
            try:
                for x in row['OBJSd']:
                    
                    if x in [None,'']:
                        continue
                    
                    #logger.debug("{0:s}LAYR OBJd {1:s}:".format(logStr,x)) 
                    
                    try:
                        m=re.search('([A-Z]{4})~(\d{19})',x)
                        TYPE=m.group(1)
                        ID=m.group(2)        
                        
                        #logger.debug("{0:s}LAYR OBJd parsed: TYPE: {1:s} ID: {2:s}".format(logStr,TYPE,ID)) 
                        
                        
                        df=pd.DataFrame(data=np.array([[row['pk'],row['tk'],row['NAME'],row['LFDNR'],TYPE,ID]]),columns=['pk','tk','NAME','LFDNR','TYPE','ID'])
                        
                        #logger.debug("{0:s}LAYR OBJd parsed df: {1:s}".format(logStr,df.to_string())) 

                        dfs.append(df)
                        
                    except:
                        
                        continue
                    
            except:
                continue        
        
        df=pd.concat(dfs)
        
        df=df.reset_index(drop=True)
        
        
        df[['LFDNR']] = df[['LFDNR']].apply(pd.to_numeric)
        df=df.sort_values(by=['LFDNR','pk','tk','NAME','TYPE','ID'])
        
        #GruppenDesObjekts
        
        #Anz
        
        #Namen
        dfg=df.groupby(by=['TYPE','ID'])['NAME'].agg(list)           
        df=pd.merge(df,dfg,left_on=['TYPE','ID'],right_index=True,suffixes=('','_X'))
        df.rename(columns={'NAME_X':'GruppenDesObjektsNamen'},inplace=True)
        df['GruppenDesObjektsNamen']=df.apply(lambda row: sorted(row['GruppenDesObjektsNamen']),axis=1)
        #Anz
        df['GruppenDesObjektsAnz']=df.apply(lambda row: len(row['GruppenDesObjektsNamen']),axis=1)
        
        df=df.sort_values(by=['LFDNR','pk','tk','NAME','TYPE','ID'])
            
        df['NrDesObjektesDesTypsInGruppe']=df.groupby(by=['pk','tk','NAME','TYPE']).cumcount()+1
        df['NrDesObjektesInGruppe']=df.groupby(by=['pk','tk','NAME']).cumcount()+1
        
        
        dfg=df.groupby(by=['pk','tk','NAME'])[['NrDesObjektesInGruppe']].max()
        df=pd.merge(df,dfg,left_on=['pk','tk','NAME'],right_index=True,suffixes=('','_X'))
        df.rename(columns={'NrDesObjektesInGruppe_X':'AnzDerObjekteInGruppe'},inplace=True)
        df=df.sort_values(by=['LFDNR','pk','tk','NAME','TYPE','ID'])


        dfg=df.groupby(by=['pk','tk','NAME','TYPE'])[['NrDesObjektesDesTypsInGruppe']].max()
        df=pd.merge(df,dfg,left_on=['pk','tk','NAME','TYPE'],right_index=True,suffixes=('','_X'))
        df.rename(columns={'NrDesObjektesDesTypsInGruppe_X':'AnzDerObjekteDesTypsInGruppe'},inplace=True)
        df=df.sort_values(by=['LFDNR','pk','tk','NAME','TYPE','ID'])
        
        
        #df['AnzDesObjektesDesTypsInGruppe']=df[].max()
        #df['AnzDerObjekteInGruppe']=df.groupby(by=['pk','tk','NAME']).count()
        
        
        df=df.reset_index(drop=True)
        
        df=df[[
            'pk'
           ,'tk'
           ,'LFDNR'
           ,'NAME'
           ,'AnzDerObjekteInGruppe'
           ,'AnzDerObjekteDesTypsInGruppe'    
           ,'TYPE'
           ,'ID'
           ,'NrDesObjektesDesTypsInGruppe'
           ,'NrDesObjektesInGruppe'
           ,'GruppenDesObjektsAnz'
           ,'GruppenDesObjektsNamen'          
            ]]
            
     
    except Exception as e:
        logStrFinal="{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(logStr,sys.exc_info()[-1].tb_lineno,type(e),str(e))          
        logger.debug(logStrFinal) 
        
                                                                          
    finally:
        logger.debug("{0:s}{1:s}".format(logStr,'_Done.'))    
        return df    
    
def Wblz(dx):
    """Returns a df with decoded V_WBLZ-Content.

    Args:
        dx: Dx-Instance 
            used: dx.dataFrames['V_WBLZ']
                
    Returns:
        df:
            one row per WBLZ and OBJ
            
            LAYR:
            'pk'
           ,'tk'
           
    
    """
    
    logStr = "{0:s}.{1:s}: ".format(__name__, sys._getframe().f_code.co_name)
    logger.debug("{0:s}{1:s}".format(logStr,'Start.')) 
    
    try: 
        
        df=pd.DataFrame()
        
        V_WBLZ=dx.dataFrames['V_WBLZ']
        
        V_WBLZ['OBJSd']=V_WBLZ.apply(lambda row: row['OBJS'].decode('utf-8').split('\t') if row['OBJS'] != None else None ,axis=1)
                
        dfs=[]
        
        for index,row in V_WBLZ[~pd.isnull(V_WBLZ['OBJSd'])].sort_values(by=['NAME']).iterrows():
            
            logger.debug("{0:s}WBLZ: {1:s}:".format(logStr,row['NAME'])) 
            
            try:
                for x in row['OBJSd']:
                    
                    if x in [None,'']:
                        continue
                    
                    #logger.debug("{0:s}LAYR OBJd {1:s}:".format(logStr,x)) 
                    
                    try:
                        m=re.search('([A-Z]{4})~(\d{19})',x)
                        TYPE=m.group(1)
                        ID=m.group(2)        
                        
                        #logger.debug("{0:s}LAYR OBJd parsed: TYPE: {1:s} ID: {2:s}".format(logStr,TYPE,ID)) 
                        
                        
                        df=pd.DataFrame(data=np.array([[row['pk'],row['tk'],row['NAME'],row['BESCHREIBUNG'],TYPE,ID]]),columns=['pk','tk','NAME','BESCHREIBUNG','TYPE','ID'])
                        
                        #logger.debug("{0:s}LAYR OBJd parsed df: {1:s}".format(logStr,df.to_string())) 

                        dfs.append(df)
                        
                    except:
                        
                        continue
                    
            except:
                continue        
        
        df=pd.concat(dfs)
        
        df=df.sort_values(by=['NAME','pk','tk'])
        
        df=df.reset_index(drop=True)
        
        #WblzDesKnotens
        
        #Anz
        
        #Namen
        dfg=df.groupby(by=['ID'])['NAME'].agg(list)           
        df=pd.merge(df,dfg,left_on=['ID'],right_index=True,suffixes=('','_X'))
        df.rename(columns={'NAME_X':'BilanzenDesKnotensNamen'},inplace=True)
        df['BilanzenDesKnotensNamen']=df.apply(lambda row: sorted(row['BilanzenDesKnotensNamen']),axis=1)
        #Anz
        df['BilanzenDesKnotensAnz']=df.apply(lambda row: len(row['BilanzenDesKnotensNamen']),axis=1)        
        

        df=df.reset_index(drop=True)
        
        df=pd.merge(df,dx.dataFrames['V_BVZ_KNOT'],left_on='ID',right_on='tk',suffixes=('','_X')).filter(items=df.columns.to_list()+['NAME_X']).rename(columns={'NAME_X':'KNAM'})
      
        df=df[[
          'pk'
         ,'tk'        
         ,'NAME'
         
         #,'AnzDerObjekteInGruppe'
         #,'AnzDerObjekteDesTypsInGruppe'    
         
         ,'TYPE'
         ,'ID'
         ,'KNAM'
         
         #,'NrDesObjektesDesTypsInGruppe'
         #,'NrDesObjektesInGruppe'
         ,'BilanzenDesKnotensNamen'
         ,'BilanzenDesKnotensAnz'          
          ]]        
       
            
     
    except Exception as e:
        logStrFinal="{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(logStr,sys.exc_info()[-1].tb_lineno,type(e),str(e))          
        logger.debug(logStrFinal) 
        
                                                                          
    finally:
        logger.debug("{0:s}{1:s}".format(logStr,'_Done.'))    
        return df    
    
    pass