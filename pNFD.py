import logging
import os
import sys

import pandas as pd
import geopandas
import numpy as np
import math

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import matplotlib

from matplotlib import cm
from matplotlib.colors import ListedColormap
import matplotlib.font_manager as font_manager
import matplotlib.patheffects as path_effects

import contextily as cx

import matplotlib.patches as mpatches

logger = logging.getLogger('PT3S')  

def cmpTIMEs( df=pd.DataFrame() # a V3sErg=dx.MxAdd(mx) df i.e. v3sKNOT=V3sErg['V3_KNOT']
             ,col='KNOT~*~*~*~PH'
             ,timeLstA=[]
             ,timeLstB=[]             
             ,newColNamesBase=[]):

    """
    compares the value of col between 2 TIMEs (B-A) and creates new cols    
    """

    pass
    logStr = "{0:s}.{1:s}: ".format(__name__, sys._getframe().f_code.co_name)
    logger.debug("{0:s}{1:s}".format(logStr,'Start.')) 

    try:
        for timeA,timeB,newColNameBase in zip(timeLstA,timeLstB,newColNamesBase):

             ergCol_timeA=('TIME'
            ,col
            ,pd.Timestamp(timeA.strftime('%Y-%m-%d %X.%f'))
            ,pd.Timestamp(timeA.strftime('%Y-%m-%d %X.%f'))
            )

             ergCol_timeB=('TIME'
            ,col
            ,pd.Timestamp(timeB.strftime('%Y-%m-%d %X.%f'))
            ,pd.Timestamp(timeB.strftime('%Y-%m-%d %X.%f'))
            )

             if ergCol_timeA not in df.columns:               
                logger.warning("{:s}col: {:s} nicht vorhanden.".format(logStr,col)) 
                continue
             if ergCol_timeB not in df.columns:
                logger.warning("{:s}col: {:s} nicht vorhanden.".format(logStr,col)) 
                continue
             
             df[newColNameBase+'_DIF']=df.apply(lambda row: row[ergCol_timeB]-row[ergCol_timeA] ,axis=1)    
             df[newColNameBase+'_DIFAbs']=df.apply(lambda row: math.fabs(row[newColNameBase+'_DIF']) ,axis=1)    
         
         
    except Exception as e:
            logStrFinal="{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(logStr,sys.exc_info()[-1].tb_lineno,type(e),str(e))
            logger.error(logStrFinal) 
            raise e         
    finally:
            logger.debug("{0:s}{1:s}".format(logStr,'_Done.'))     

def pNFD_FW(     
                 ax=None
                ,axTitle=None
                ,gdf_ROHR=pd.DataFrame()      
                ,gdf_FWVB=pd.DataFrame()         
                ,gdf_KNOT=pd.DataFrame()                                 
             
                # Layout ROHR
            
                # Sachdatum
                ,attr_colors_ROHR_Sach = 'DI' 
                ,attr_colors_ROHR_Sach_zOrder = 3
                ,colors_ROHR_Sach = ['lightgray', 'dimgray']                
                ,norm_min_ROHR_Sach = None 
                ,norm_max_ROHR_Sach = None

                ,attr_lws_ROHR_Sach='DI'                     
                ,attr_colors_ROHR_Sach_patches_fmt="DN (Innen) {:4.0f}"
                ,attr_colors_ROHR_Sach_patchValues=None
                
                # Breitenfaktor (fuer Sach- und Ergebnisdaten)
                ,fac_lws_ROHR=5. 

                # Ergebnis: Farbe
                ,attr_colors_ROHR_Erg=None 
                ,attr_colors_ROHR_Erg_zOrder = 4 
                ,colors_ROHR_Erg = ['darkgreen','magenta']
                ,norm_min_ROHR_Erg = None 
                ,norm_max_ROHR_Erg = None            
                ,attr_colors_ROHR_Erg_patches_fmt="Q (abs.) {:4.0f} t/h"
                ,attr_colors_ROHR_Erg_patchValues=None
                
                                
                ,query_ROHR_Erg=None #'{:s} > 1.'.format(attr_colors_ROHR_Erg)
                # wenn angegeben, werden nur Ergebnisse von Rohren geplottet die dem query entsprechen
                                
                # Ergebnis: Breite: Standard: so wie die Sachdaten (diese werden dann komplett ueberzeichnet) ...
                ,lws_ROHR_Erg_Sach=True
                # andernfalls richtet sich die Breite nach dem Ergebnisattribut; es ergeben sich _dann in absteigender Richtung duennere oder dickere Breiten als bei den Sachdaten 
                # _Bsp. Sach DI und Erg QAbs: der max. DN und der max. Fluss werden mitderselben Breite gezeichnet; darunter ergeben sich unterschiedliche Breiten; DN i.d.R. breiter als Fluss
                ,fac_lws_ROHR_Erg=None # nur wirksam bei lws_ROHR_Erg_Sach=False; dann Standard fac_lws_ROHR  
            

                # Layout FWVB
            
                # Sachdatum
                ,attr_colors_FWVB_Sach='W0'
                ,attr_colors_FWVB_Sach_zOrder = 1
                ,attr_colors_FWVB_Sach_patches_fmt="W {:4.0f} kW"        
                ,attr_colors_FWVB_Sach_patchValues=None
                ,colors_FWVB_Sach = ['oldlace', 'orange'] 
                ,norm_min_FWVB_Sach = None 
                ,norm_max_FWVB_Sach = None            
            
                ,attr_ms_FWVB_Sach='W0' 
                ,fac_ms_FWVB=None # fac_ms_KNOT oder 8000.  wenn beides undefiniert

                # Ergebnis: Farbe
                ,attr_colors_FWVB_Erg=None 
                ,attr_colors_FWVB_Erg_zOrder = 2
                ,attr_colors_FWVB_Erg_patches_fmt="dp {:4.1f} bar"     
                ,attr_colors_FWVB_Erg_patchValues = None
                ,attr_colors_FWVB_ErgNeg_patches_fmt="dp -{:4.1f} bar"                     
                ,colors_FWVB_Erg = ['aquamarine','teal'] 
                ,norm_min_FWVB_Erg = None 
                ,norm_max_FWVB_Erg = None         
                
                # Ergebnis: Groesse: Standard: -1
                ,ms_FWVB_Erg=-1
                # -2: konst. Groesse 
                # -1: Groesse so wie die Sachdaten (diese werden dann komplett ueberzeichnet) 
                #       sind die Sachdaten nicht angefordert dasselbe Ergebnis wie ms_FWVB_Erg=0
                #  0: Groesse nach Ergebnisdaten (bei dp als Erg und W0 als Sach fuehrt dies zu vielen Überzeichnungen)
                # >0: Prozent (1=100%): Groesse nach Ergebnisdaten, aber nur max. ms_FWVB_Erg-Prozent der Sachdatengroesse 
                #               dies führt bei ]0;1[ dazu, dass die Sachdatenannotation immer sichtbar bleibt

                ,colors_FWVB_ErgNeg = ['lightskyblue','royalblue'] # ['aquamarine','skyblue']
                # wenn nicht None, dann werden negative Werte mit dieser Farbe gezeichnet; beide Farbskalen (die dann pos. und diese neg.) werden voll ausgenutzt
                # die Groesse erstreckt sich ueber den gesamten Wertebereich d.h. z.B. -.25 ist so gross wie +.25                

            
                # Layout KNOTen
                ,attr_colors_KNOT_Erg=None 
                ,attr_colors_KNOT_Erg_patches_fmt="pDiff +{:4.2f} bar"        
                ,attr_colors_KNOT_ErgNeg_patches_fmt="pDiff -{:4.2f} bar"                           
                ,colors_KNOT_Erg = ['yellow','red']
                ,norm_min_KNOT_Erg = None 
                ,norm_max_KNOT_Erg = None  

                ,colors_KNOT_ErgNeg = ['yellowgreen','sienna']
                # wenn nicht None, dann werden negative Werte mit dieser Farbe gezeichnet
                # beide Farbskalen (die dann pos. und diese neg.) werden dann voll ausgenutzt, wenn norm_max_KNOT_Erg nicht vorgegeben wird          
                # die Groesse erstreckt sich ueber den Absolutwert d.h. z.B. -.25 ist so gross wie +.25 

                ,fac_ms_KNOT = None  # fac_ms_FWVB oder 8000.  wenn beides undefiniert

                # Layout Karte
                ,MapOn=False
                ,LabelsOnTop = False                               
                ,Map_resolution = 15

                ):
    
        """   
        zeichnet ROHRe; Sachdatum und ggf. Ergebnis auf Sachdatum
        zeichnet ggf. FWVB; Sachdatum und ggf. Ergebnis auf Sachdatum
        zeichnet ggf. KNOTen Ergebnis
        
        Returns:
                attr_colors_ROHR_Sach_patches: Legendeneinträge
                attr_colors_ROHR_Erg_patches: Legendeneinträge     
                attr_colors_FWVB_Sach_patches: Legendeneinträge
                attr_colors_FWVB_Erg_patches: Legendeneinträge                 
        """

        logStr = "{0:s}.{1:s}: ".format(__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr,'Start.')) 

        try:
            
            attr_colors_ROHR_Sach_patches=None
            attr_colors_ROHR_Erg_patches=None
            attr_colors_FWVB_Sach_patches=None
            attr_colors_FWVB_Erg_patches=None
            attr_colors_KNOT_Erg_patches=None
           
            if ax == None:
                ax = plt.gca()

            ### ROHRe ###
        
            attr_colors_ROHR_Sach_patches=[]
            attr_colors_ROHR_Erg_patches=[]       
            if not gdf_ROHR.empty:        
        
        
                # Erstellen der Colormap 
                cmap_ROHR = matplotlib.colors.LinearSegmentedColormap.from_list('cmap_ROHR', colors_ROHR_Sach, N = 256)        
            
                # Normierung fuer Colormap
                if norm_min_ROHR_Sach == None:            
                    norm_min_ROHR_Sach=gdf_ROHR[attr_colors_ROHR_Sach].min()
                if norm_max_ROHR_Sach == None:
                    norm_max_ROHR_Sach=gdf_ROHR[attr_colors_ROHR_Sach].max()
                    
                norm_diff_ROHR_Sach=norm_max_ROHR_Sach-norm_min_ROHR_Sach
                
                if norm_diff_ROHR_Sach < 0.01:
                    norm_min_ROHR_Sach=0.99*norm_max_ROHR_Sach
                    norm_diff_ROHR_Sach=norm_max_ROHR_Sach-norm_min_ROHR_Sach
                                
                logger.debug("{0:s}norm_min_ROHR_Sach: {1:10.2f} norm_max_ROHR_Sach: {2:10.2f}".format(logStr,norm_min_ROHR_Sach,norm_max_ROHR_Sach)) 
                                
                norm_ROHR_color = plt.Normalize(vmin=norm_min_ROHR_Sach, vmax=norm_max_ROHR_Sach) 
                                
                # Plotten ROHRe
                gdf_ROHR.plot(ax = ax
                             ,zorder = attr_colors_ROHR_Sach_zOrder
                             ,linewidth = norm_ROHR_color(gdf_ROHR[attr_lws_ROHR_Sach]) * fac_lws_ROHR
                             # wg. astype: ufunc 'isnan' not supported for the input types, and the inputs could not be safely coerced to any supported types according to the casting rule ''safe''
                             ,color = cmap_ROHR(norm_ROHR_color(gdf_ROHR[attr_colors_ROHR_Sach].astype(float)))
                             ,path_effects=[path_effects.Stroke(capstyle="round")]
                             )
            
                if attr_colors_ROHR_Sach_patchValues == None:
                     attr_colors_ROHR_Sach_patchValues=np.arange(norm_min_ROHR_Sach,norm_max_ROHR_Sach+1,norm_diff_ROHR_Sach/4)                 
                attr_colors_ROHR_Sach_patches = [ mpatches.Patch(color=cmap_ROHR(norm_ROHR_color(value)), label=attr_colors_ROHR_Sach_patches_fmt.format(value) ) 
                                                 for value in attr_colors_ROHR_Sach_patchValues]        
            
                    
                if attr_colors_ROHR_Erg != None:
                    
                    # Erstellen der Colormap 
                    cmap_ROHRErg = matplotlib.colors.LinearSegmentedColormap.from_list('cmap_ROHRErg', colors_ROHR_Erg, N = 256)     
                
                    # Normierung fuer Colormap
                    if norm_min_ROHR_Erg == None:            
                        norm_min_ROHR_Erg=gdf_ROHR[attr_colors_ROHR_Erg].min()    
                    if norm_max_ROHR_Erg == None:            
                        norm_max_ROHR_Erg=gdf_ROHR[attr_colors_ROHR_Erg].max()
                    norm_ROHRErg_color = plt.Normalize(vmin=norm_min_ROHR_Erg, vmax=norm_max_ROHR_Erg)       
                    norm_diff_ROHR_Erg=norm_max_ROHR_Erg-norm_min_ROHR_Erg
                
                    # Breite
                    if lws_ROHR_Erg_Sach:            
                        attr_lws_ROHR_Erg=attr_colors_ROHR_Sach
                        norm_ROHR_lws_Erg=norm_ROHR_color
                        fac_lws_ROHR_Erg=fac_lws_ROHR
                    else:
                        attr_lws_ROHR_Erg=attr_colors_ROHR_Erg
                        norm_ROHR_lws_Erg=norm_ROHRErg_color
                        
                        if fac_lws_ROHR_Erg == None:
                            fac_lws_ROHR_Erg=fac_lws_ROHR
                    
                    if query_ROHR_Erg != None:
                        df=gdf_ROHR.query(query_ROHR_Erg)
                    else:
                        df=gdf_ROHR
                    # große ueber kleine zeichnen
                    df=df.sort_values(by=[attr_colors_ROHR_Erg],ascending=True)
            
                    df.plot(ax = ax
                             ,zorder = attr_colors_ROHR_Erg_zOrder
                             ,linewidth = norm_ROHR_lws_Erg(df[attr_lws_ROHR_Erg]) * fac_lws_ROHR_Erg
                             ,color = cmap_ROHRErg(norm_ROHRErg_color(df[attr_colors_ROHR_Erg]))
                             ,path_effects=[path_effects.Stroke(capstyle="round")]
                             )       
                    
                    
                    # Legendeneinräge
                                 
                    if attr_colors_ROHR_Erg_patchValues == None:
                         attr_colors_ROHR_Erg_patchValues=np.arange(norm_min_ROHR_Erg,norm_max_ROHR_Erg+1,norm_diff_ROHR_Erg/4)                 
                    attr_colors_ROHR_Erg_patches = [ mpatches.Patch(color=cmap_ROHRErg(norm_ROHRErg_color(value)), label=attr_colors_ROHR_Erg_patches_fmt.format(value) ) 
                                                     for value in attr_colors_ROHR_Erg_patchValues]                                                                                                                                 
                                                                                                                              
            
            ### FWVBe ###
            attr_colors_FWVB_Sach_patches=[]
            attr_colors_FWVB_Erg_patches=[]       
            if not gdf_FWVB.empty:

                # Groessenfaktor
                if fac_ms_FWVB == None:
                    if fac_ms_KNOT != None:
                        fac_ms_FWVB=fac_ms_KNOT
                    else:
                        fac_ms_FWVB=8000.
                        
                        
                logger.debug("{0:s}fac_ms_FWVB: {1:10.2f}".format(logStr,fac_ms_FWVB)) 

                #attr_colors_FWVB_Sach_patches=[]
                if attr_colors_FWVB_Sach != None:

                    # Erstellen der Colormap
                    cmap_FWVB = matplotlib.colors.LinearSegmentedColormap.from_list('cmap_FWVB', colors_FWVB_Sach, N = 256)        

                    # Normierung fuer Colormap
                    if norm_min_FWVB_Sach == None:            
                        norm_min_FWVB_Sach=gdf_FWVB[attr_colors_FWVB_Sach].min()
                    if norm_max_FWVB_Sach == None:
                        norm_max_FWVB_Sach=gdf_FWVB[attr_colors_FWVB_Sach].max()
                        
                    #norm_FWVB_color = plt.Normalize(vmin=norm_min_FWVB_Sach, vmax=norm_max_FWVB_Sach)
                    # Werte außerhalb vmin, vmax erhalten ohne clip Werte < 0 > 1 und damit (bei Wert <= 0) keine Darstellung wenn die Normierung auch fuer die Groesse verwendet wird
                    norm_diff_FWVB_Sach=norm_max_FWVB_Sach-norm_min_FWVB_Sach
                    
                    if norm_diff_FWVB_Sach < 0.01:
                        norm_min_FWVB_Sach=0.99*norm_max_FWVB_Sach
                        norm_diff_FWVB_Sach=norm_max_FWVB_Sach-norm_min_FWVB_Sach      
                        
                        
                    logger.debug("{0:s}norm_min_FWVB_Sach: {1:10.2f} norm_max_FWVB_Sach: {2:10.2f}".format(logStr,norm_min_FWVB_Sach,norm_max_FWVB_Sach)) 
                    norm_FWVB_color = plt.Normalize(vmin=norm_min_FWVB_Sach, vmax=norm_max_FWVB_Sach)                    
                    
                    logger.debug("{0:s}ms_min_FWVB_Sach: {1:10.2f} ms_max_FWVB_Sach: {2:10.2f}".format(logStr
                                                                                                         ,norm_FWVB_color(gdf_FWVB[attr_ms_FWVB_Sach].min())
                                                                                                         ,norm_FWVB_color(gdf_FWVB[attr_ms_FWVB_Sach].max())
                                 )) 
                
                    # Plotten FWVB
                    gdf_FWVB.plot(ax = ax
                                ,zorder = attr_colors_FWVB_Sach_zOrder 
                                ,marker = '.'
                                ,markersize = norm_FWVB_color(gdf_FWVB[attr_ms_FWVB_Sach]) * fac_ms_FWVB                       
                                ,color = cmap_FWVB(norm_FWVB_color(gdf_FWVB[attr_colors_FWVB_Sach]))
                                )
                            
                    if attr_colors_FWVB_Sach_patchValues == None:
                         attr_colors_FWVB_Sach_patchValues=np.arange(norm_min_FWVB_Sach,norm_max_FWVB_Sach+1,norm_diff_FWVB_Sach/4)    
                         
                    attr_colors_FWVB_Sach_patches = [ mpatches.Patch(color=cmap_FWVB(norm_FWVB_color(value)), label=attr_colors_FWVB_Sach_patches_fmt.format(value) ) 
                                                     for value in attr_colors_FWVB_Sach_patchValues]                                                                                                                                 
                                                                                                                               
                #attr_colors_FWVB_Erg_patches=[]
                if attr_colors_FWVB_Erg != None:
                    
                    logger.debug("{0:s}attr_colors_FWVB_Erg: {1:s}".format(logStr,str(attr_colors_FWVB_Erg))) 

                    minValue=gdf_FWVB[attr_colors_FWVB_Erg].astype(float).min()
                
                    # Erstellen der Colormaps 
                    cmap_FWVBErg = matplotlib.colors.LinearSegmentedColormap.from_list('cmap_FWVBErg', colors_FWVB_Erg, N = 256)     

                    if colors_FWVB_ErgNeg != None and minValue <0:                    
                        cmap_FWVBErgNeg = matplotlib.colors.LinearSegmentedColormap.from_list('cmap_FWVBErgNeg', colors_FWVB_ErgNeg, N = 256)  
            
                    # Normierung fuer (1) Colormap und Groesse
                    if norm_min_FWVB_Erg == None:    
                         if colors_FWVB_ErgNeg != None and minValue <0:
                            norm_min_FWVB_Erg=0.
                         else:
                            norm_min_FWVB_Erg=gdf_FWVB[attr_colors_FWVB_Erg].astype(float).min()    
                    if norm_max_FWVB_Erg == None:            
                        if colors_FWVB_ErgNeg != None and minValue <0:
                            norm_max_FWVB_Erg=max(gdf_FWVB[attr_colors_FWVB_Erg].astype(float).max(),-gdf_FWVB[attr_colors_FWVB_Erg].astype(float).min())
                        else:
                            norm_max_FWVB_Erg=gdf_FWVB[attr_colors_FWVB_Erg].astype(float).max()
                    norm_FWVBErg_color = plt.Normalize(vmin=norm_min_FWVB_Erg, vmax=norm_max_FWVB_Erg)    
                    norm_diff_FWVB_Erg=norm_max_FWVB_Erg-norm_min_FWVB_Erg
                
                    # Groesse
                    if ms_FWVB_Erg == -2:                           
                        markersizes=1. * fac_ms_FWVB                       
                    elif ms_FWVB_Erg == -1:   
                        if attr_colors_FWVB_Sach != None:
                            markersizes=norm_FWVB_color(gdf_FWVB[attr_colors_FWVB_Sach]) * fac_ms_FWVB       
                        else:
                            # Sachdaten nicht definiert
                            try:
                                markersizes=norm_FWVBErg_color(gdf_FWVB[attr_colors_FWVB_Erg].astype(float)) * fac_ms_FWVB           
                            except ValueError:
                                logger.debug("{0:s}ms_FWVB_Erg: {1:d} und attr_colors_FWVB_Sach nicht definiert; Verhalten wie bei -2 ...".format(logStr,ms_FWVB_Erg)) 
                                markersizes=1. * fac_ms_FWVB   
                                pass
                                
                            
                    elif ms_FWVB_Erg == 0:                         
                        markersizes=norm_FWVBErg_color(gdf_FWVB[attr_colors_FWVB_Erg].astype(float)) * fac_ms_FWVB           

                    else:
                        if attr_colors_FWVB_Sach != None:
                            markersizesSach=norm_FWVB_color(gdf_FWVB[attr_colors_FWVB_Sach]) * fac_ms_FWVB                
                        else:
                            markersizesSach=norm_FWVBErg_color(gdf_FWVB[attr_colors_FWVB_Erg].astype(float)) * fac_ms_FWVB          
                        markersizesErg=norm_FWVBErg_color(gdf_FWVB[attr_colors_FWVB_Erg].astype(float)) * fac_ms_FWVB           
                        markersizes=[min(ms_FWVB_Erg*msSach,msErg) for (msSach,msErg) in zip(markersizesSach,markersizesErg)]
                      
                    #if isinstance(markersizes,list):    
                    #    logger.debug("{0:s}markersizes: min {1:10.2f} max {2:10.2f} ".format(logStr,min(markersizes),max(markersizes))) 
                    #else:
                    #    logger.debug("{0:s}markersizes: {1:10.2f}  ".format(logStr,markersizes)) 

                    # Plotten FWVB

                    if colors_FWVB_ErgNeg != None and minValue <0:
                        # Farbnormierungen
                        norm_FWVBErg_color=plt.Normalize(vmin=norm_min_FWVB_Erg, vmax=gdf_FWVB[attr_colors_FWVB_Erg].astype(float).max())  
                        norm_FWVBErgNeg_color=plt.Normalize(vmin=norm_min_FWVB_Erg, vmax=-gdf_FWVB[attr_colors_FWVB_Erg].astype(float).min())  

                        norm_FWVBErg_size=plt.Normalize(vmin=0., vmax=max(gdf_FWVB[attr_colors_FWVB_Erg].astype(float).max(),-gdf_FWVB[attr_colors_FWVB_Erg].astype(float).min()))  

                        gdf=gdf_FWVB[gdf_FWVB[attr_colors_FWVB_Erg].astype(float)>=0]
                        if not gdf.empty:
                            gdf.plot(ax = ax
                                        ,zorder = attr_colors_FWVB_Erg_zOrder  
                                        ,marker = '.'                           
                                        ,markersize = norm_FWVBErg_size(gdf[attr_colors_FWVB_Erg].astype(float)) * fac_ms_FWVB   
                                        ,color = cmap_FWVBErg(norm_FWVBErg_color(gdf[attr_colors_FWVB_Erg].astype(float))) 
                                        )  
                            
                        colors=cmap_FWVBErg(np.arange(cmap_FWVBErg.N))
                        attr_colors_FWVB_Erg_patches = [ mpatches.Patch(color=colors[i], label=attr_colors_FWVB_Erg_patches_fmt.format(value) ) for (i,value) in zip([0
                                                                                                                  ,cmap_FWVBErg.N-1],[gdf[attr_colors_FWVB_Erg].min(),                                                                                                                    
                                                                                                                                   gdf[attr_colors_FWVB_Erg].max()])
                                                                                                                                   ]        
                        attr_colors_FWVB_Erg_patches[0].set_label("{:s} ({:7.6f})".format(attr_colors_FWVB_Erg_patches[0].get_label(),gdf_FWVB[gdf_FWVB[attr_colors_FWVB_Erg].astype(float)>0][attr_colors_FWVB_Erg].min()))                            
                                                    
                    
                        gdf=gdf_FWVB[gdf_FWVB[attr_colors_FWVB_Erg].astype(float)<0]
                        if not gdf.empty:
                            gdf.plot(ax = ax
                                        ,zorder = 2 
                                        ,marker = '.'                           
                                        ,markersize = norm_FWVBErg_size(gdf[attr_colors_FWVB_Erg].astype(float).apply(lambda x: math.fabs(x))) * fac_ms_FWVB   
                                        ,color = cmap_FWVBErgNeg(norm_FWVBErgNeg_color(gdf[attr_colors_FWVB_Erg].astype(float).apply(lambda x: math.fabs(x)))) 
                                        )  
                            
                            
                            colors=cmap_FWVBErgNeg(np.arange(cmap_FWVBErgNeg.N))
                            attr_colors_FWVB_Erg_patches=attr_colors_FWVB_Erg_patches + [ mpatches.Patch(color=colors[i], label=attr_colors_FWVB_ErgNeg_patches_fmt.format(value) ) for (i,value) in zip([0
                                                                                                                      ,cmap_FWVBErgNeg.N-1],[-gdf[attr_colors_FWVB_Erg].max(),                                                                                                                    
                                                                                                                                       -gdf[attr_colors_FWVB_Erg].min()])
                                                                                                                                       ]        
                            attr_colors_FWVB_Erg_patches[2].set_label("{:s} ({:7.6f})".format(attr_colors_FWVB_Erg_patches[2].get_label(),gdf_FWVB[gdf_FWVB[attr_colors_FWVB_Erg].astype(float)<0][attr_colors_FWVB_Erg].max()))                            
                            
                            
                            
                            
                            
                    else:
                        
                        try:
                            colors=cmap_FWVBErg(norm_FWVBErg_color(gdf_FWVB[attr_colors_FWVB_Erg].astype(float)))
                            pass
                        except ValueError:
                            colors=cmap_FWVBErg(.666)

                        gdf_FWVB.plot(ax = ax
                                    ,zorder = 2 
                                    ,marker = '.'                           
                                    ,markersize = markersizes          
                                    ,color = colors#cmap_FWVBErg(norm_FWVBErg_color(gdf_FWVB[attr_colors_FWVB_Erg].astype(float))) 
                                    )    

                        if attr_colors_FWVB_Erg_patchValues == None:
                            attr_colors_FWVB_Erg_patchValues=np.arange(norm_min_FWVB_Erg,norm_max_FWVB_Erg+1,norm_diff_FWVB_Erg/4)                                                                                 
                        attr_colors_FWVB_Erg_patches = [ mpatches.Patch(color=cmap_FWVBErg(norm_FWVBErg_color(value)), label=attr_colors_FWVB_Erg_patches_fmt.format(value) ) for value in attr_colors_FWVB_Erg_patchValues]
                                                                                                                                                                                                                                                  

        
            ### KNOTen ###

            attr_colors_KNOT_Sach_patches=[]
            attr_colors_KNOT_Erg_patches=[]   
            attr_colors_KNOT_Erg_patchesNeg=[]                      
            if not gdf_KNOT.empty and attr_colors_KNOT_Erg != None:

                minValue=gdf_KNOT[attr_colors_KNOT_Erg].astype(float).min()
                
                # Erstellen der Colormaps 
                cmap_KNOTErg = matplotlib.colors.LinearSegmentedColormap.from_list('cmap_KNOTErg', colors_KNOT_Erg, N = 256)     
                if colors_KNOT_ErgNeg != None and minValue <0:                    
                    cmap_KNOTErgNeg = matplotlib.colors.LinearSegmentedColormap.from_list('cmap_KNOTErgNeg', colors_KNOT_ErgNeg, N = 256)  
                    
                # Funktionsweise Farbskalen: Werte ]0,1[ erhalten die Randfarben 0,1
            
                # Normierung fuer Groesse
                # auch Normierung fuer Farbe, wenn mit einer Farbe gezeichnet wird
                if norm_min_KNOT_Erg == None:       
                    if colors_KNOT_ErgNeg != None and minValue <0:
                        norm_min_KNOT_Erg=0.
                    else:
                        norm_min_KNOT_Erg=gdf_KNOT[attr_colors_KNOT_Erg].astype(float).min()    
                if norm_max_KNOT_Erg == None:
                    if colors_KNOT_ErgNeg != None and minValue <0:
                        norm_max_KNOT_Erg=max(gdf_KNOT[attr_colors_KNOT_Erg].astype(float).max(),-gdf_KNOT[attr_colors_KNOT_Erg].astype(float).min())

                        # Farbnormierungen
                        norm_KNOTErg_color=plt.Normalize(vmin=norm_min_KNOT_Erg, vmax=gdf_KNOT[attr_colors_KNOT_Erg].astype(float).max())  
                        norm_KNOTErgNeg_color=plt.Normalize(vmin=norm_min_KNOT_Erg, vmax=-gdf_KNOT[attr_colors_KNOT_Erg].astype(float).min())  
                    else:
                        norm_max_KNOT_Erg=gdf_KNOT[attr_colors_KNOT_Erg].astype(float).max()                    
                else:                    
                    # Farbnormierungen
                    norm_KNOTErg_color=plt.Normalize(vmin=norm_min_KNOT_Erg, vmax=norm_max_KNOT_Erg)  
                    norm_KNOTErgNeg_color=plt.Normalize(vmin=norm_min_KNOT_Erg, vmax=norm_max_KNOT_Erg)  
                    



                norm_KNOTErg_Size = plt.Normalize(vmin=norm_min_KNOT_Erg, vmax=norm_max_KNOT_Erg)  

                # Werte ]vmin,vmax[ erhalten Werte ]0,1[ entsprechend der Normierung [0,1] mit [vmin,vmax]

                logger.debug("{:s}norm_KNOTErg_Size: norm_min_KNOT_Erg={:15.6f} norm_max_KNOT_Erg={:15.6f} .".format(logStr,norm_min_KNOT_Erg,norm_max_KNOT_Erg)) 

                # Groesse
                if fac_ms_KNOT == None:
                    if fac_ms_FWVB != None:
                        fac_ms_KNOT=fac_ms_FWVB
                    else:
                        fac_ms_KNOT=8000.                

                if colors_KNOT_ErgNeg != None and minValue <0:
                    ## Farbnormierungen
                    #norm_KNOTErg_color=plt.Normalize(vmin=norm_min_KNOT_Erg, vmax=gdf_KNOT[attr_colors_KNOT_Erg].astype(float).max())  
                    #norm_KNOTErgNeg_color=plt.Normalize(vmin=norm_min_KNOT_Erg, vmax=-gdf_KNOT[attr_colors_KNOT_Erg].astype(float).min())  

                    gdf=gdf_KNOT[gdf_KNOT[attr_colors_KNOT_Erg].astype(float)>=0]
                    if not gdf.empty:
                        gdf.plot(ax = ax
                                    ,zorder = 2 
                                    ,marker = '.'                           
                                    ,markersize = norm_KNOTErg_Size(gdf[attr_colors_KNOT_Erg].astype(float)) * fac_ms_KNOT   
                                    ,color = cmap_KNOTErg(norm_KNOTErg_color(gdf[attr_colors_KNOT_Erg].astype(float))) 
                                    )  
                        
                        colors=cmap_KNOTErg(np.arange(cmap_KNOTErg.N))
                        attr_colors_KNOT_Erg_patches = [ mpatches.Patch(color=colors[i], label=attr_colors_KNOT_Erg_patches_fmt.format(value) ) for (i,value) in zip([0
                                                                                                                 ,cmap_KNOTErg.N-1],[gdf[attr_colors_KNOT_Erg].min(),                                                                                                                    
                                                                                                                                  gdf[attr_colors_KNOT_Erg].max()])
                                                                                                                                  ]        
                        attr_colors_KNOT_Erg_patches[0].set_label("{:s} ({:7.6f})".format(attr_colors_KNOT_Erg_patches[0].get_label(),gdf_KNOT[gdf_KNOT[attr_colors_KNOT_Erg].astype(float)>0][attr_colors_KNOT_Erg].min()))
                            
                    
                    gdf=gdf_KNOT[gdf_KNOT[attr_colors_KNOT_Erg].astype(float)<0]
                    if not gdf.empty:
                        gdf.plot(ax = ax
                                    ,zorder = 2 
                                    ,marker = '.'                           
                                    ,markersize = norm_KNOTErg_Size(gdf[attr_colors_KNOT_Erg].astype(float).apply(lambda x: math.fabs(x))) * fac_ms_KNOT   
                                    ,color = cmap_KNOTErgNeg(norm_KNOTErgNeg_color(gdf[attr_colors_KNOT_Erg].astype(float).apply(lambda x: math.fabs(x)))) 
                                    )  

                        colors=cmap_KNOTErgNeg(np.arange(cmap_KNOTErgNeg.N))
                        attr_colors_KNOT_Erg_patchesNeg = [ mpatches.Patch(color=colors[i], label=attr_colors_KNOT_ErgNeg_patches_fmt.format(value) ) for (i,value) in zip([0
                                                                                                                 ,cmap_KNOTErgNeg.N-1],[-gdf[attr_colors_KNOT_Erg].max(),                                                                                                                    
                                                                                                                                  -gdf[attr_colors_KNOT_Erg].min()])
                                                                                                                                  ]     
                                                                                                                                        
                        attr_colors_KNOT_Erg_patchesNeg[0].set_label("{:s} ({:7.6f})".format(attr_colors_KNOT_Erg_patchesNeg[0].get_label(),gdf_KNOT[gdf_KNOT[attr_colors_KNOT_Erg].astype(float)<0][attr_colors_KNOT_Erg].max()))                                                                                                                                    
                        
                    attr_colors_KNOT_Erg_patches=attr_colors_KNOT_Erg_patches+attr_colors_KNOT_Erg_patchesNeg
                        
                    
                        
                        
                else:
                    
                    gdf_KNOT.plot(ax = ax
                                ,zorder = 2 
                                ,marker = '.'                           
                                ,markersize = norm_KNOTErg_Size(gdf_KNOT[attr_colors_KNOT_Erg].astype(float).apply(lambda x: math.fabs(x))) * fac_ms_KNOT   
                                ,color = cmap_KNOTErg(norm_KNOTErg_Size(gdf_KNOT[attr_colors_KNOT_Erg].astype(float))) 
                                )    



        
        
            if MapOn:
                if LabelsOnTop:
                    cx.add_basemap(ax, crs=gdf_ROHR.crs.to_string(), source = cx.providers.CartoDB.PositronNoLabels, zoom = Map_resolution)
                    cx.add_basemap(ax, crs=gdf_ROHR.crs.to_string(), source = cx.providers.CartoDB.PositronOnlyLabels, zoom = Map_resolution)
                else:
                    cx.add_basemap(ax, crs=gdf_ROHR.crs.to_string(), source = cx.providers.CartoDB.Positron, zoom = Map_resolution)

            ax.axis('off')

            if axTitle != None:
                ax.set_title(axTitle)


            #ax.legend(handles=attr_colors_ROHR_Sach_patches
            #          ,loc='upper left'
            #          ,facecolor='white', framealpha=.01)


        except Exception as e:
            logStrFinal="{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(logStr,sys.exc_info()[-1].tb_lineno,type(e),str(e))
            logger.error(logStrFinal) 
            raise e        
        finally:
            logger.debug("{0:s}{1:s}".format(logStr,'_Done.'))     
            return attr_colors_ROHR_Sach_patches,attr_colors_ROHR_Erg_patches,attr_colors_FWVB_Sach_patches,attr_colors_FWVB_Erg_patches,attr_colors_KNOT_Erg_patches