"""

"""

__version__='90.12.4.0.dev1'

import warnings
warnings.filterwarnings("ignore")

import sys
import logging

import pandas as pd
import geopandas

import matplotlib.pyplot as plt
import matplotlib
from matplotlib import cm

import contextily as cx

logger = logging.getLogger('PT3S')  
if __name__ == "__main__":
    logger.debug("{0:s}{1:s}".format('in MODULEFILE: __main__ Context:','.')) 
else:
    logger.debug("{0:s}{1:s}{2:s}{3:s}".format('in MODULEFILE: Not __main__ Context: ','__name__: ',__name__," ."))

class NFDError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class NFD():

    """
    Raises:
        NFDError
    """

    def __init__(self):
        self.name = 'NFD'

    def plotNFD( gdf_FWVB
                ,gdf_ROHR

                # Layout FWVB

                ,colors_FWVB = ['green', 'red']
                ,color_FWVB_under = 'green'
                ,color_FWVB_over = 'red'

                ,cmap_color_FWVB = 'W0'
                ,norm_min_FWVB = None 
                ,norm_max_FWVB = None 

                ,FWVB_markerscaling_col = 'W0'
                ,FWVB_markerscaling_fac = 0.3

                ,FWVB_edgecolor = 'White'

                # Layout ROHR

                ,colors_ROHR = ['lightgray', 'dimgray']
                ,color_ROHR_under = 'magenta'
                ,color_ROHR_over = 'lime'

                ,cmap_color_ROHR = 'DI'
                ,norm_min_ROHR = None 
                ,norm_max_ROHR = None 

                ,ROHR_linewidth_col = 'DI'                
                ,ROHR_linewidth_fac =  0.005


                # Legend FWVB

                ,legend_FWVB_label = None 
                ,legend_FWVB_label_shrink = 1.

                ,yTicks = None
                ,yTickLabels = None

                # Karte
                ,LabelsOnTop = False                               
                ,Map_resolution = 15

                ):

        """
        Die Funktion plottet FWVB und ROHRe auf Hintergrundkarte.
        """

        logStr = "{0:s}.{1:s}: ".format(__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr,'Start.'))


        fig = plt.gcf()
        ax = plt.gca()

        #Erstellen der Colormap fuer die FWVB
        # ---
        if norm_min_FWVB == None:            
            norm_min_FWVB=gdf_FWVB[cmap_color_FWVB].min()
        if norm_max_FWVB == None:            
            norm_max_FWVB=gdf_FWVB[cmap_color_FWVB].max()
        norm_FWVB_color = plt.Normalize(vmin=norm_min_FWVB, vmax=norm_max_FWVB)
        cmap_FWVB = matplotlib.colors.LinearSegmentedColormap.from_list('FWVB', colors_FWVB, N = 256) 
        cmap_FWVB.set_under(color_FWVB_under)
        cmap_FWVB.set_over(color_FWVB_over)

        # fuer u.a. Linienstaerke des Markers
        norm_FWVB_size = plt.Normalize(vmin = gdf_FWVB[FWVB_markerscaling_col].min(), vmax = gdf_FWVB[FWVB_markerscaling_col].max()) #Festlegen wie diese Spalte normiert werden soll

        #Erstellen der Colormap fuer die Rohre
        # ---
        if norm_min_ROHR == None:            
            norm_min_ROHR=gdf_ROHR[cmap_color_ROHR].min()
        if norm_max_ROHR == None:            
            norm_max_ROHR=gdf_ROHR[cmap_color_ROHR].max()
        norm_ROHR_color = plt.Normalize(vmin=norm_min_ROHR, vmax=norm_max_ROHR)
        cmap_ROHR = matplotlib.colors.LinearSegmentedColormap.from_list('ROHR', colors_ROHR, N = 256) 
        cmap_ROHR.set_under(color_ROHR_under)
        cmap_ROHR.set_over(color_ROHR_over)

        

        try:
            gdf_FWVB.plot(ax = ax
                        ,marker = '.'
                        ,markersize = gdf_FWVB[FWVB_markerscaling_col] * FWVB_markerscaling_fac #Markersize ist abhaengig von der zum Markerscaling ausgewaehlten Spalte und einem Faktor
                        ,c = cmap_FWVB(norm_FWVB_color(gdf_FWVB[cmap_color_FWVB])) #Einfaerben der Marker entsprechend der definierten Colormap und ausgewaehlten Spalte
                        ,edgecolor = FWVB_edgecolor #FWVB Randfarbe des Markers
                        ,linewidth = norm_FWVB_size(gdf_FWVB[FWVB_markerscaling_col]) / 2 #FWVB Randdicke, abhaengig von der zum Markerscaling ausgewaehlten Spalte. Die Randdicke wird im Anschluss nochmal durch 2 geteilt.
                        ,alpha =  0.9 - (norm_FWVB_size(gdf_FWVB[FWVB_markerscaling_col]) / 2) #FWVB Durchsichtigkeit, abhaengig von der zum Markerscaling ausgewaehlten Spalte. Mit dem Teilen durch 2 ist die maximale Durchsichtigkeit bei 0.5 (0 bei Kleinen-0.5 bei Grossen). Um dies umzudrehen zieht man von 1 ab. Hier wird von 0.9 abgezogen. Damit sind kleinsten FWVB immer noch leicht durchsichtig und die Groessten trotzdem noch erkennbar (0.9 bei Kleinen - 0.4 bei Grossen) 
                        ,zorder = 2) #Reihenfolge zu den anderen geploteten Objekten (je hoeher die Zahl, desto hoeher die geplottete Ebene; Hoehe im Sinne von Vorder- und Hintergrund)

            #if Anzeigen_ROHR:

            #    if ROHR_Ampel:
            gdf_ROHR.plot(ax = ax
                                    ,zorder = 1
                                    ,linewidth = gdf_ROHR[ROHR_linewidth_col] * ROHR_linewidth_fac
                                    ,color = cmap_ROHR(norm_ROHR_color(gdf_ROHR[cmap_color_ROHR])))

            #    else:    
            #        gdf_ROHR.plot(ax = ax
            #                        ,zorder = 1
            #                        ,linewidth = gdf_ROHR[column_ROHR_Dicke] * ROHR_dicke
            #                        ,color = color_ROHR)

            if LabelsOnTop:
                cx.add_basemap(ax, crs=gdf_FWVB.crs.to_string(), source = cx.providers.CartoDB.PositronNoLabels, zoom = Map_resolution)
                cx.add_basemap(ax, crs=gdf_FWVB.crs.to_string(), source = cx.providers.CartoDB.PositronOnlyLabels, zoom = Map_resolution)
            else:
                cx.add_basemap(ax, crs=gdf_FWVB.crs.to_string(), source = cx.providers.CartoDB.Positron, zoom = Map_resolution)

            if legend_FWVB_label == None:
                legend_FWVB_label=cmap_color_FWVB

            cbar=fig.colorbar(cm.ScalarMappable(norm = norm_FWVB_color, cmap = cmap_FWVB)
                        ,ax = ax
                        ,label = legend_FWVB_label
                        ,shrink = legend_FWVB_label_shrink
                        ,ticks=yTicks
                        ,pad = 0.01)
            if yTickLabels != None:
                cbar.ax.set_yticklabels(yTickLabels)

            plt.axis('off')

        except NFDError:
            raise            
        except Exception as e:
            logStrFinal="{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(logStr,sys.exc_info()[-1].tb_lineno,type(e),str(e))
            logger.error(logStrFinal) 
            raise NFDError(logStrFinal)                       
        finally:       
            logger.debug("{0:s}{1:s}".format(logStr,'_Done.'))
            return