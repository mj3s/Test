"""

"""

import shapely
import geopandas
import doctest
import unittest
import argparse
import sqlite3
import pyodbc
import math
import glob
import logging
import struct
import base64
import time
import h5py
import tables
import numpy as np
import pandas as pd
import re
import sys
import os
import warnings
__version__ = '90.14.3.0.dev1'

# warnings.filterwarnings("ignore")


# ---
# --- PT3S Imports
# ---
logger = logging.getLogger('PT3S')
if __name__ == "__main__":
    logger.debug("{0:s}{1:s}".format('in MODULEFILE: __main__ Context:', '.'))
else:
    logger.debug("{0:s}{1:s}{2:s}{3:s}".format(
        'in MODULEFILE: Not __main__ Context: ', '__name__: ', __name__, " ."))

try:
    from PT3S import Xm
except ImportError:
    logger.debug("{0:s}{1:s}".format(
        'ImportError: ', 'from PT3S import Xm - trying import Xm instead ... maybe pip install -e . is active ...'))
    import Xm


class DxError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Dx():
    """SIR 3S Access/SQLite to pandas DataFrames.

    Args:
        * dbFile (str): SIR 3S Access/SQLite File
            * wird wie angegeben gesucht
            * ohne Pfadangabe wird im aktuellen Verz. gesucht und (wenn das Fehl schlaegt) im uebergeordneten

    Attributes:
        * dbFile: verwendetes dbFile

        * dataFrames: enthaelt alle gelesenen Tabellen und konstruierten Views

        * viewSets: fasst View- bzw. Tabellennamen zu Kategorien zusammen; dient zur Uebersicht bei Bedarf
            * allTables
            * pairTables
            * pairViews_BZ
            * pairViews_ROWT  
            * pairViews_ROWD
            * notPairTables
            * notPairTablesProbablyNotSir3sTables
            * notPairViews
            * notPairViewsProbablyNotSir3sTables

        * zu den Spaltennamen der Views:
            * grundsaetzlich die Originalnamen - aber ...
                * bei den _BVZ_ Views:
                    * :_BZ, wenn Spalten Namensgleich
                * Datenebenen:
                    * _VMBZ,_VMVARIANTE,_VMBASIS, wenn Spalten Namensgleich
                * CONT:
                    * immer _CONT
                * VKNO:
                    * immer _VKNO
                * VBEL:
                    * immer _i und _k fuer die Knotendaten

        * V3-Views i.e. dataFrames['V3_KNOT']
            * V3_KNOT: Knoten: "alle" Knotendaten      
            * V3_ROHR: Knoten: "alle" Rohrdaten  
            * V3_FWVB: Knoten: "alle" FWVB-Daten

            * V3_SWVT
                * 1 Zeile pro ZEIT und W; cols sind NAMEn der SWVT 
            * V3_RSLW_SWVT
                * 1 Zeile pro RSLW der aktiv eine SWVT referenziert

            * V3_VBEL: Kanten: "alle" Verbindungselementdaten des hydr. Prozessmodells
                * Multiindex:
                    * OBJTYPE
                    * OBJID (pk)
                * Graph Example:
                    * vVbel=self.dataFrames['V3_VBEL'].reset_index()
                    * G=nx.from_pandas_edgelist(df=vVbel, source='NAME_i', target='NAME_k', edge_attr=True) 
                    * vKnot=self.dataFrames['V3_KNOT']
                    * nodeDct=vKnot.to_dict(orient='index')
                    * nodeDctNx={value['NAME']:value|{'idx':key} for key,value in nodeDct.items()}
                    * nx.set_node_attributes(G,nodeDctNx)
                    
            * V3_DPKT: ausgewaehlte Daten von Datenpunkten
            * V3_RKNOT: Knotendaten des Signalmodells
                * Kn: Knotenname
                * OBJTYPE: der Typname des Elementes des Signalmodells z.B. RADD
            * V3_RRUES: 
                * wie V_BVZ_RUES - mit folgenden zusaetzlichen Spalten:
                    * pk_DEF	
                    * IDUE_DEF	
                    * OBJTYPE_SRC      RXXX-Objekttyp der das Signal definiert welches die Ue repraesentiert	                    
                    * Kn_SR            Signal fuer das die Ue ein Alias ist (KA des RXXX)
                    * NAME_CONT_SRC    Block in dem das Signal definiert wird (das RXXX-Element liegt)

            * V3_RVBEL: Kantendaten des Signalmodells
                * Multiindex:
                    * OBJTYPE_i
                    * OBJTYPE_k                
                * RUES-RXXX sind in den Spalten 'OBJTYPE_i','OBJID_i','Kn_i','KnExt_i','NAME_CONT_i' durch die RUES-Quelle ersetzt
                * Graph Example:
                    * vRVbel=self.dataFrames['V3_RVBEL'].reset_index()
                    * GSig=nx.from_pandas_edgelist(df=vRVbel, source='Kn_i', target='Kn_k', edge_attr=True, create_using=nx.DiGraph())
                    * nodeDct=vRknot.to_dict(orient='index')
                    * nodeDctNx={value['Kn']:value|{'idx':key} for key,value in nodeDct.items()}
                    * nx.set_node_attributes(GSig,nodeDctNx)
                                    
        * viewSets['pairViews_BZ']:
            * ['V_BVZ_ALLG'
            ...
            *, 'V_BVZ_WIND']
        * viewSets['pairViews_ROWS']:
            * ['V_BVZ_ANTE'
            ...
            *, 'V_BVZ_ZEP1', 'V_BVZ_ZEP2']
        * viewSets['pairViews_ROWT']:
            * ['V_BVZ_LFKT'
            ...
            *, 'V_BVZ_RCPL' # da RCPL_ROWT existiert "landet" RCPL bei den ROWTs
            ...
            , 'V_BVZ_WTTR']
            * enthalten alle Zeiten
            * Spalte lfdNrZEIT beginnt mit 1 fuer die chronologisch 1. Zeit (na_position='first')
        * viewSets['pairViews_ROWD']:
            * ['V_BVZ_DTRO']
        * viewSets['notPairViews']:
            * ['V_AB_DEF', 'V_AGSN', 'V_ARRW', 'V_ATMO'
            *, 'V_BENUTZER', 'V_BREF'
            *, 'V_CIRC', 'V_CONT', 'V_CRGL'
            *, 'V_DATENEBENE', 'V_DPGR_DPKT', 'V_DPKT', 'V_DRNP'
            *, 'V_ELEMENTQUERY'
            *, 'V_FSTF', 'V_FWBZ'
            *, 'V_GKMP', 'V_GMIX', 'V_GRAV', 'V_GTXT'
            *, 'V_HAUS'
            *, 'V_LAYR', 'V_LTGR'
            *, 'V_MODELL', 'V_MWKA'
            *, 'V_NRCV'
            *, 'V_OVAL'
            *, 'V_PARV', 'V_PGPR', 'V_PLYG', 'V_POLY', 'V_PROZESSE', 'V_PZON'
            *, 'V_RCON', 'V_RECT', 'V_REGP', 'V_RMES_DPTS', 'V_ROHR_VRTX', 'V_RPFL', 'V_RRCT'
            *, 'V_SIRGRAF', 'V_SOKO', 'V_SPLZ', 'V_STRASSE', 'V_SYSTEMKONFIG'
            *, 'V_TIMD', 'V_TRVA'
            *, 'V_UTMP'
            *, 'V_VARA', 'V_VARA_CSIT', 'V_VARA_WSIT', 'V_VERB', 'V_VKNO', 'V_VRCT'
            *, 'V_WBLZ']
    Raises:
        DxError
    """

    def __init__(self, dbFile):

        logStr = "{0:s}.{1:s}: ".format(
            self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

        try:
            if os.path.exists(dbFile):
                if os.access(dbFile, os.W_OK):
                    pass
                else:
                    logger.debug(
                        "{:s}dbFile: {:s}: Not writable.".format(logStr, dbFile))
                    if os.access(dbFile, os.R_OK):
                        pass
                    else:
                        logStrFinal = "{:s}dbFile: {:s}: Not readable!".format(
                            logStr, dbFile)
                        raise DxError(logStrFinal)
            else:
                # pruefen, ob dbFile im uebergeordneten Verzeichnis existiert
                logger.debug("{:s}dbFile: {:s}: Not existing! Suche im uebergeordneten Verz. ...".format(
                    logStr, dbFile))

                dbFileAlt = dbFile
                dbFile = os.path.join('..', dbFileAlt)
                if os.path.exists(dbFile):
                    if os.access(dbFile, os.W_OK):
                        pass
                    else:
                        logger.debug(
                            "{:s}dbFile: {:s}: Not writable.".format(logStr, dbFile))
                        if os.access(dbFile, os.R_OK):
                            pass
                        else:
                            logStrFinal = "{:s}dbFile: {:s}: Not readable!".format(
                                logStr, dbFile)
                            raise DxError(logStrFinal)
                else:
                    logStrFinal = "{:s}dbFile: {:s}: Not existing!".format(
                        logStr, dbFile)
                    raise DxError(logStrFinal)

            # das dbFile existiert und ist lesbar
            logger.debug("{:s}dbFile (abspath): {:s} existiert und ist lesbar".format(
                logStr, os.path.abspath(dbFile)))

            self.dbFile = dbFile

            # Access oder SQLite
            dummy, ext = os.path.splitext(dbFile)

            if ext == '.mdb':
                Driver = [x for x in pyodbc.drivers() if x.startswith(
                    'Microsoft Access Driver')]
                if Driver == []:
                    logStrFinal = "{:s}{:s}: No Microsoft Access Driver!".format(
                        logStr, dbFile)
                    raise DxError(logStrFinal)

                # ein Treiber ist installiert
                conStr = (
                    r'DRIVER={'+Driver[0]+'};'
                    r'DBQ='+dbFile+';'
                )
                logger.debug("{0:s}conStr: {1:s}".format(logStr, conStr))

                # Verbindung ...
                if True:
                    from sqlalchemy.engine import URL
                    connection_url = URL.create(
                        "access+pyodbc", query={"odbc_connect": conStr})
                    logger.debug("{0:s}connection_url type: {1:s}".format(
                        logStr, str(type(connection_url))))
                    from sqlalchemy import create_engine
                    engine = create_engine(connection_url)
                    logger.debug("{0:s}engine type: {1:s}".format(
                        logStr, str(type(engine))))
                    con = engine.connect()
                    logger.debug("{0:s}con type: {1:s}".format(
                        logStr, str(type(con))))

                    if True:
                        from sqlalchemy import inspect
                        insp = inspect(engine)
                        tableNames = insp.get_table_names()  # insp.get_view_names()
                        cur = con
                    else:
                        cur = con
                        tableNames = engine.table_names()
                else:
                    con = pyodbc.connect(conStr)
                    cur = con.cursor()
                    # all Tables in DB
                    tableNames = [
                        table_info.table_name for table_info in cur.tables(tableType='TABLE')]
                    viewNames = [
                        table_info.table_name for table_info in cur.tables(tableType='VIEW')]

            elif ext == '.db3':
                con = sqlite3.connect(dbFile)
                cur = con.cursor()
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';")
                l = cur.fetchall()
                tableNames = [x for x, in l]

                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='view';")
                l = cur.fetchall()
                viewNames = [x for x, in l]

            else:
                logStrFinal = "{:s}dbFile: {:s} ext: {:s}: unbekannter DB-Typ (.mdb und .db3 sind zulaessig)".format(
                    logStr, dbFile, ext)
                raise DxError(logStrFinal)

            logger.debug("{0:s}tableNames: {1:s}".format(
                logStr, str(tableNames)))
            allTables = set(tableNames)

            logger.debug("{0:s}viewNames: {1:s}".format(
                logStr, str(viewNames)))
            allViews = set(viewNames)

            # pandas DataFrames
            self.dataFrames = {}

            # Mengen von Typen von Tabellen und Views
            pairTables = set()
            pairViews = set()
            pairViews_BZ = set()
            pairViews_ROWS = set()
            pairViews_ROWT = set()
            pairViews_ROWD = set()

            # SIR 3S Grundtabellen und -views lesen
            try:
                dfViewModelle = pd.read_sql(fHelperSqlText(
                    'select * from VIEW_MODELLE'), con)
                self.dataFrames['VIEW_MODELLE'] = dfViewModelle
            except pd.io.sql.DatabaseError as e:
                logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                    logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
                logger.error(logStrFinal)
                raise DxError(logStrFinal)

            try:
                dfCONT = pd.read_sql(fHelperSqlText('select * from CONT'), con)
            except pd.io.sql.DatabaseError as e:
                logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                    logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
                logger.error(logStrFinal)
                raise DxError(logStrFinal)

            try:
                dfKNOT = pd.read_sql(fHelperSqlText('select * from KNOT'), con)
            except pd.io.sql.DatabaseError as e:
                logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                    logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
                logger.error(logStrFinal)
                raise DxError(logStrFinal)

            # Paare
            for pairType in ['_BZ', '_ROWS', '_ROWT', '_ROWD']:
                logger.debug(
                    "{0:s}pairType: {1:s}: ####".format(logStr, pairType))
                #tablePairsBVBZ=[(re.search('(?P<BV>[A-Z,1,2]+)('+pairType+')$',table_info.table_name).group('BV'),table_info.table_name) for table_info in cur.tables(tableType='TABLE') if re.search('(?P<BV>[A-Z,1,2]+)('+pairType+')$',table_info.table_name) != None]
                tablePairsBVBZ = [(re.search('(?P<BV>[A-Z,1,2]+)('+pairType+')$', table_name).group('BV'), table_name)
                                  for table_name in tableNames if re.search('(?P<BV>[A-Z,1,2]+)('+pairType+')$', table_name) != None]
                for (BV, BZ) in tablePairsBVBZ:

                    if BV not in tableNames:
                        logger.debug(
                            "{0:s}BV: {1:s}: Tabelle gibt es nicht. Falsche Paar-Ermittlung? Weiter. ".format(logStr, BV))
                        continue
                    if BZ not in tableNames:
                        logger.debug(
                            "{0:s}BZ: {1:s}: Tabelle gibt es nicht. Falsche Paar-Ermittlung? Weiter. ".format(logStr, BZ))
                        continue

                    if BZ == 'PGRP_PUMP_BZ':  # BV: PUMP BVZ: PGRP_PUMP_BZ V: V_PUMP - Falsch!; wird unten ergaenzt
                        continue

                    # TabellenNamen in entspr. Mengen abspeichern
                    pairTables.add(BV)
                    pairTables.add(BZ)

                    # VName
                    VName = 'V_BVZ_'+BV

                    dfBV, dfBZ, dfBVZ = fHelper(
                        con, BV, BZ, dfViewModelle, dfCONT, pairType, ext)

                    rows, cols = dfBVZ.shape
                    logger.debug("{0:s}BV: {1:s} BVZ: {2:s} V: {3:s} fertig mit {4:d} Zeilen und {5:d} Spalten.".format(
                        logStr, BV, BZ, VName, rows, cols))

                    self.dataFrames[BV] = dfBV
                    self.dataFrames[BZ] = dfBZ
                    self.dataFrames[VName] = dfBVZ

                    # ViewName in entspr. Menge abspeichern
                    pairViews.add(VName)
                    if pairType == '_BZ':
                        pairViews_BZ.add(VName)
                    elif pairType == '_ROWS':
                        pairViews_ROWS.add(VName)
                    elif pairType == '_ROWT':
                        pairViews_ROWT.add(VName)
                    elif pairType == '_ROWD':
                        pairViews_ROWD.add(VName)

            # BVZ-Paare Nachzuegler
            for (BV, BZ) in [('PGRP_PUMP', 'PGRP_PUMP_BZ'), ('RMES_DPTS', 'RMES_DPTS_BZ')]:

                dfBV, dfBZ, dfBVZ = fHelper(
                    con, BV, BZ, dfViewModelle, dfCONT, '_BZ', ext)

                VName = 'V_BVZ_'+BV
                self.dataFrames[VName] = dfBVZ

                rows, cols = dfBVZ.shape
                logger.debug("{0:s}BV: {1:s} BVZ: {2:s} V: {3:s} fertig mit {4:d} Zeilen und {5:d} Spalten.".format(
                    logStr, BV, BZ, VName, rows, cols))

                pairTables.add(BV)
                pairTables.add(BZ)

                pairViews.add(VName)
                pairViews_BZ.add(VName)

            # Nicht-Paare
            notInPairTables = sorted(allTables-pairTables)
            notInPairTablesW = [  # W: "Sollwert"; erwartete SIR 3S Tabellen, die nicht Paare sind
                # ,'DPKT' # ab 90-12 ein Paar
                'AB_DEF', 'AGSN', 'ARRW', 'ATMO', 'BENUTZER', 'BREF', 'CIRC', 'CONT', 'CRGL', 'DATENEBENE', 'DPGR_DPKT', 'DRNP', 'ELEMENTQUERY', 'FSTF', 'FWBZ', 'GEOMETRY_COLUMNS'  # 90-12
                # ,'MWKA' # nicht 90-12
                # ,'RMES_DPTS'#, 'RMES_DPTS_BZ'
                # , 'VARA_CSIT', 'VARA_WSIT'
                , 'GKMP', 'GMIX', 'GRAV', 'GTXT', 'HAUS', 'LAYR', 'LTGR', 'MODELL', 'NRCV', 'OVAL', 'PARV', 'PGPR', 'PLYG', 'POLY', 'PROZESSE', 'PZON', 'RCON', 'RECT', 'REGP', 'ROHR_VRTX', 'RPFL', 'RRCT', 'SIRGRAF', 'SOKO', 'SPLZ', 'STRASSE', 'SYSTEMKONFIG', 'TIMD', 'TRVA', 'UTMP', 'VARA', 'VERB', 'VKNO', 'VRCT', 'WBLZ']

            # erwartete SIR 3S Tabellen, die nicht Paare sind
            notPairTables = set()
            notPairViews = set()
            for tableName in notInPairTablesW:

                if tableName not in tableNames:
                    logger.debug(
                        "{0:s}tableName: {1:s}: Tabelle gibt es nicht - falsche Annahme in diesem Modul bzgl. der existierenden SIR 3S Tabellen? Weiter. ".format(logStr, tableName))
                    continue

                sql = 'select * from '+tableName
                try:
                    df = pd.read_sql(fHelperSqlText(sql, ext), con)
                    self.dataFrames[tableName] = df
                    notPairTables.add(tableName)
                except:  # pd.io.sql.DatabaseError as e:
                    logger.info(
                        "{0:s}sql: {1:s}: Fehler?! Weiter. ".format(logStr, sql))
                    continue

                df = fHelperCONTetc(df, tableName, '', dfViewModelle, dfCONT,
                                    'erwartete SIR 3S Tabellen, die nicht Paare sind')

                VName = 'V_'+tableName
                logger.debug("{0:s}V: {1:s}".format(logStr, VName))
                self.dataFrames[VName] = df
                notPairViews.add(VName)

            # unerwartete Tabellen
            notPairViewsProbablyNotSir3sTables = set()
            notPairTablesProbablyNotSir3sTables = set()
            for tableName in set(notInPairTables)-set(notInPairTablesW):

                logger.debug("{0:s}tableName: {1:s}: Tabelle keine SIR 3S Tabelle aus Sicht dieses Moduls. Trotzdem lesen. ".format(
                    logStr, tableName))

                sql = 'select * from '+tableName
                try:
                    df = pd.read_sql(fHelperSqlText(sql, ext), con)
                    self.dataFrames[tableName] = df
                    notPairTablesProbablyNotSir3sTables.add(tableName)
                except pd.io.sql.DatabaseError as e:
                    logger.debug(
                        "{0:s}sql: {1:s}: Fehler?! Weiter. ".format(logStr, sql))
                    continue

                df = fHelperCONTetc(
                    df, tableName, '', dfViewModelle, dfCONT, 'unerwartete Tabellen')

                VName = 'V_'+tableName
                logger.debug("{0:s}V: {1:s}".format(logStr, VName))
                self.dataFrames[VName] = df
                notPairViewsProbablyNotSir3sTables.add(VName)

            self.viewSets = {}

            self.viewSets['allTables'] = sorted(allTables)
            self.viewSets['pairTables'] = sorted(pairTables)

            self.viewSets['pairViews'] = sorted(pairViews)
            self.viewSets['pairViews_BZ'] = sorted(pairViews_BZ)
            self.viewSets['pairViews_ROWS'] = sorted(pairViews_ROWS)
            self.viewSets['pairViews_ROWT'] = sorted(pairViews_ROWT)
            self.viewSets['pairViews_ROWD'] = sorted(pairViews_ROWD)

            self.viewSets['notPairTables'] = sorted(notPairTables)
            self.viewSets['notPairTablesProbablyNotSir3sTables'] = sorted(
                notPairTablesProbablyNotSir3sTables)
            self.viewSets['notPairViews'] = sorted(notPairViews)
            self.viewSets['notPairViewsProbablyNotSir3sTables'] = sorted(
                notPairViewsProbablyNotSir3sTables)

            con.close()

            # #############################################################
            # #############################################################

            # V_BVZ_ROHR um u.a. DN erweitern
            # #############################################################
            logger.debug("{0:s}{1:s} erweitern...".format(
                logStr, 'V_BVZ_ROHR'))

            if 'pk_BZ' in self.dataFrames['V_BVZ_DTRO'].keys():
                df = pd.merge(self.dataFrames['V_BVZ_ROHR'], self.dataFrames['V_BVZ_DTRO'],
                              left_on='fkDTRO_ROWD', right_on='pk_BZ', suffixes=('', '_DTRO'))
                if df.empty:
                    df = pd.merge(self.dataFrames['V_BVZ_ROHR'], self.dataFrames['V_BVZ_DTRO'],
                                  left_on='fkDTRO_ROWD', right_on='tk_BZ', suffixes=('', '_DTRO'))
            elif 'pk_BV' in self.dataFrames['V_BVZ_DTRO'].keys():
                df = pd.merge(self.dataFrames['V_BVZ_ROHR'], self.dataFrames['V_BVZ_DTRO'],
                              left_on='fkDTRO_ROWD', right_on='pk_BV', suffixes=('', '_DTRO'))
                if df.empty:
                    df = pd.merge(self.dataFrames['V_BVZ_ROHR'], self.dataFrames['V_BVZ_DTRO'],
                                  left_on='fkDTRO_ROWD', right_on='tk_BV', suffixes=('', '_DTRO'))
            df = df.filter(items=self.dataFrames['V_BVZ_ROHR'].columns.to_list(
            )+['NAME', 'DN', 'DI', 'DA', 'S', 'KT', 'PN'])
            df.rename(columns={'NAME': 'NAME_DTRO'}, inplace=True)
            
            df['V']=df.apply(lambda row: math.pow(row['DI']/1000,2)*math.pi/4,axis=1)
            
            self.dataFrames['V_BVZ_ROHR'] = df

            # weitere Erweiterungen zu V3_ROHR
            # #############################################################
            logger.debug(
                "{0:s}weitere Erweiterung zu {1:s} ...".format(logStr, 'V3_ROHR'))
            extV = df

            for dfRefStr, fkRefStr, refName in zip(['LTGR', 'STRASSE'], ['fkLTGR', 'fkSTRASSE'], ['LTGR', 'STRASSE']):
                dfRef = self.dataFrames[dfRefStr]

                extV = extV.merge(dfRef.add_suffix('_'+refName), left_on=fkRefStr, right_on='pk' +
                                  '_'+refName, how='left').filter(items=extV.columns.to_list()+['NAME'+'_'+refName])
            self.dataFrames['V3_ROHR'] = extV

            # V3_SWVT
            # #############################################################
            logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_SWVT'))

            # 1 Zeile pro RSLW der aktiv eine SWVT referenziert
            # NAME_SWVT_Nr gibt an, um die wie-vielte Referenz derselben SWVT es sich handelt
            # NAME_SWVT_NrMax gibt die max. Anzahl der Referenzierungen an; typischerwweise sollte NAME_SWVT_NrMax=1 sein für alle SWVT
            # (ZEIT, count)	... (W, max) sind Aggregate der referenzierten SWVT

            vRSLW = self.dataFrames['V_BVZ_RSLW']

            # .sort_values(by=['pk','NAME','ZEIT'])
            vSWVT = self.dataFrames['V_BVZ_SWVT']

            for i, r in vSWVT[
                pd.isnull(vSWVT['ZEIT'])
                |
                pd.isnull(vSWVT['W'])
            ].iterrows():

                logger.debug("{:s}{:s} {:s}: ZEIT und/oder W sind Null?!: ZEIT: {!s:s} W: {!s:s}: Null-Wert(e) wird (werden) auf 0. gesetzt.".format(
                    logStr, 'vSWVT', r['NAME'], r['ZEIT'], r['W']))

            # die erste Zeit wird oft mit NaN gelesen obwohl sie mit 0. eingegeben ist
            vSWVT['ZEIT'] = vSWVT['ZEIT'].fillna(0.)
            # Werte mit NaN kann es iegentlich nicht geben ?! ...
            vSWVT['W'] = vSWVT['W'].fillna(0.)

            vSWVT = vSWVT.sort_values(by=['pk', 'NAME', 'ZEIT'])

            V3_SWVT = vSWVT.pivot_table(
                index='ZEIT', columns='NAME', values='W', aggfunc='last')
            self.dataFrames['V3_SWVT'] = V3_SWVT

            # V3_ROWT
            # #############################################################
            logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_ROWT'))
            valColName = {'V_BVZ_LFKT': 'LF', 'V_BVZ_PHI1': 'PHI', 'V_BVZ_PUMD': 'N', 'V_BVZ_PVAR': 'PH', 'V_BVZ_QVAR': 'QM', 'V_BVZ_TEVT': 'T'
                          }
            dfs = []
            for view in self.viewSets['pairViews_ROWT']:

                df = self.dataFrames[view]

                if df.empty:
                    continue

                if 'ZEIT' in df.columns.to_list():
                    # print(view)

                    if view in valColName.keys():
                        vCN = valColName[view]
                    else:
                        vCN = 'W'

                    df = df.rename(columns={vCN: 'value'})

                    df = df[['NAME', 'ZEIT', 'value']]

                    # die erste Zeit wird oft mit NaN gelesen obwohl sie mit 0. eingegeben ist
                    df['ZEIT'] = df['ZEIT'].fillna(0.)

                    # print(df[['NAME','ZEIT','value']].head())

                    dfs.append(df)

            dfAll = pd.concat(dfs)
            self.dataFrames['V3_ROWT'] = dfAll.pivot_table(
                index='ZEIT', columns='NAME', values='value', aggfunc='last')

            # V3_TFKT
            # #############################################################
            logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_TFKT'))
            self.dataFrames['V3_TFKT'] = self.dataFrames['V_BVZ_TFKT'][[
                'NAME', 'X', 'Y']].pivot_table(index='X', columns='NAME', values='Y', aggfunc='last')

            # V3_RSLW_SWVT
            # #############################################################
            logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_RSLW_SWVT'))

            vRSLW_SWVTAll = pd.merge(vRSLW, vSWVT.add_suffix(
                '_SWVT'), left_on='fkSWVT', right_on='pk_SWVT')
            # die aktiv eine Sollwerttabelle referenzieren ...
            vRSLW_SWVTAll = vRSLW_SWVTAll[vRSLW_SWVTAll['INDSLW'].isin([1])]
            # .copy(deep=True) #  nur 1 Zeile pro Sollwerttabelle
            vRSLW_SWVT = vRSLW_SWVTAll[vRSLW_SWVTAll['lfdNrZEIT_SWVT'].isin([
                                                                            1])]

            vRSLW_SWVT = vRSLW_SWVT.copy(deep=True)

            vRSLW_SWVT['NAME_SWVT_Nr'] = vRSLW_SWVT.groupby(
                by=['NAME_SWVT'])['NAME_SWVT'].cumcount()+1
            vRSLW_SWVT['NAME_SWVT_NrMax'] = vRSLW_SWVT.groupby(
                by=['NAME_SWVT'])['NAME_SWVT_Nr'].transform(pd.Series.max)

            #  Aggregate einer SWVT
            df = vSWVT.groupby(by=['NAME']).agg(
                {'ZEIT': ['count', 'first', 'min', 'last', 'max'], 'W': ['count', 'first', 'min', 'last', 'max']
                 }
            )
            df.columns = df.columns.to_flat_index()

            # diese Aggregate verfuegbar machen
            self.dataFrames['V3_RSLW_SWVT'] = pd.merge(
                vRSLW_SWVT, df, left_on='NAME_SWVT', right_on='NAME')

            # V3_KNOT
            # #############################################################
            logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_KNOT'))

            vKNOT = pd.merge(self.dataFrames['V_BVZ_KNOT'], self.dataFrames['V_VKNO'].add_suffix(
                '_VKNO'), left_on='tk', right_on='fkKNOT_VKNO', how='left')

            extV = vKNOT
            for dfRefStr, fkRefStr, refName in zip(['LFKT', 'PVAR', 'PZON', 'QVAR', 'UTMP', 'FSTF', 'FQPS'], ['fkLFKT', 'fkPVAR', 'fkPZON', 'fkQVAR', 'fkUTMP', 'fkFSTF', 'fkFQPS'], ['LFKT', 'PVAR', 'PZON', 'QVAR', 'UTMP', 'FSTF', 'FQPS']):
                dfRef = self.dataFrames[dfRefStr]

                extV = extV.merge(dfRef.add_suffix('_'+refName), left_on=fkRefStr, right_on='pk' +
                                  '_'+refName, how='left').filter(items=extV.columns.to_list()+['NAME'+'_'+refName])
            self.dataFrames['V3_KNOT'] = extV

            # V3_FWVB
            # #############################################################
            logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_FWVB'))
            extV_BVZ_FWVB = self.dataFrames['V_BVZ_FWVB']
            for dfRefStr, fkRefStr, refName in zip(['LFKT', 'ZEP1', 'ZEP1', 'TEVT', 'TRFT'], ['fkLFKT', 'fkZEP1VL', 'fkZEP1RL', 'fkTEVT', 'fkTRFT'], ['LFKT', 'ZEP1VL', 'ZEP1RL', 'TEVT', 'TRFT']):
                dfRef = self.dataFrames[dfRefStr]
                extV_BVZ_FWVB = extV_BVZ_FWVB.merge(dfRef.add_suffix(
                    '_'+refName), left_on=fkRefStr, right_on='pk'+'_'+refName, how='left').filter(items=extV_BVZ_FWVB.columns.to_list()+['NAME'+'_'+refName])
            self.dataFrames['V3_FWVB'] = extV_BVZ_FWVB

            # V3_:ROHR,KNOT,FWVB: filterTemplateObjects
            # #############################################################
            logger.debug("{0:s}{1:s} filterTemplateObjects ...".format(logStr, 'V3_:ROHR,KNOT,FWVB:'))
            self._filterTemplateObjects()

            # #############################################################
            # VBEL (V3_VBEL) - "alle" Verbindungselementdaten des hydr. Prozessmodells; Knotendaten mit _i und _k
            logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_VBEL'))

            vVBEL_UnionList = []
            for vName in self.viewSets['pairViews_BZ']:

                m = re.search('^(V_BVZ_)(\w+)', vName)
                OBJTYPE = m.group(2)

                dfVBEL = self.dataFrames[vName]
                if 'fkKI' in dfVBEL.columns.to_list():
                    df = pd.merge(dfVBEL, vKNOT.add_suffix('_i'), left_on='fkKI', right_on='tk_i'
                                  )

                    logger.debug("{0:s}{1:s} in VBEL-View mit fkKI ({2:d},{3:d}) ...".format(
                        logStr, OBJTYPE, df.shape[0], df.shape[1]))

                    if df.empty:
                        df = pd.merge(dfVBEL, vKNOT.add_suffix('_i'), left_on='fkKI', right_on='pk_i'
                                      )
                        if not df.empty:
                            logger.debug("{0:s}{1:s} in VBEL-View mit fkKI per pk! ({2:d},{3:d}) ...".format(
                                logStr, OBJTYPE, df.shape[0], df.shape[1]))
                        else:
                            logger.debug("{0:s}{1:s} in VBEL-View mit fkKI LEER! ({2:d},{3:d}) ...".format(
                                logStr, OBJTYPE, df.shape[0], df.shape[1]))

                    if 'fkKK' in df.columns.to_list():
                        df = pd.merge(df, vKNOT.add_suffix('_k'), left_on='fkKK', right_on='tk_k'
                                      )

                        if df.empty:
                            df = pd.merge(dfVBEL, vKNOT.add_suffix('_k'), left_on='fkKK', right_on='pk_k'
                                          )
                            if not df.empty:
                                logger.debug("{0:s}{1:s} in VBEL-View mit fkKI und fkKK per pk! ({2:d},{3:d}) ...".format(
                                    logStr, OBJTYPE, df.shape[0], df.shape[1]))
                            else:
                                logger.debug("{0:s}{1:s} in VBEL-View mit fkKI und fkKK LEER! ({2:d},{3:d}) ...".format(
                                    logStr, OBJTYPE, df.shape[0], df.shape[1]))

                        # m=re.search('^(V_BVZ_)(\w+)',vName)
                        # OBJTYPE=m.group(2)
                        df = df.assign(OBJTYPE=lambda x: OBJTYPE)

                        logger.debug("{0:s}{1:s} final in VBEL-View mit fkKI und fkKK ({2:d},{3:d}) ...".format(
                            logStr, OBJTYPE, df.shape[0], df.shape[1]))
                        vVBEL_UnionList.append(df)
                    elif 'KNOTK' in df.columns.to_list():
                        # Nebenschlusselement
                        pass
                        df = pd.merge(df, vKNOT.add_suffix('_k'), left_on='fkKI', right_on='tk_k'
                                      )
                        # m=re.search('^(V_BVZ_)(\w+)',vName)
                        # OBJTYPE=m.group(2)
                        df = df.assign(OBJTYPE=lambda x: OBJTYPE)

                        logger.debug(
                            "{0:s}{1:s} (Nebenschluss) in VBEL-View ...".format(logStr, OBJTYPE))
                        vVBEL_UnionList.append(df)

            vVBEL = pd.concat(vVBEL_UnionList)
            vVBEL = Xm.Xm.constructNewMultiindexFromCols(
                df=vVBEL, mColNames=['OBJTYPE', 'tk'], mIdxNames=['OBJTYPE', 'OBJID'])
            vVBEL.sort_index(level=0, inplace=True)
            self.dataFrames['V3_VBEL'] = vVBEL

            # #############################################################
            # V3_DPKT
            logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_DPKT'))
            # DPKT (V3_DPKT) - relevante Datenpunktdaten
            if 'V_BVZ_DPKT' in self.dataFrames.keys():
                vDPKT = self.dataFrames['V_BVZ_DPKT']
            elif 'V_DPKT' in self.dataFrames.keys():
                vDPKT = self.dataFrames['V_DPKT']


            vDPKT_DPGR1 = pd.merge(
                vDPKT, self.dataFrames['V_DPGR_DPKT'], left_on='tk', right_on='fkDPKT', suffixes=('', '_DPGR1'))

            vDPKT_DPGR = pd.merge(
                vDPKT_DPGR1, self.dataFrames['V_BVZ_DPGR'], left_on='fkDPGR', right_on='tk', suffixes=('', '_DPGR'))

            try:
                self.dataFrames['V3_DPKT'] = vDPKT_DPGR[[
                    'pk', 'tk', 'OBJTYPE', 'fkOBJTYPE', 'ATTRTYPE', 'EPKZ', 'TITLE', 'UNIT', 'FLAGS', 'CLIENT_ID',
                    'CLIENT_FLAGS', 'OPCITEM_ID', 'DESCRIPTION',

                    'NAME1',
                    'NAME2',
                    'NAME3',

                    'FACTOR',
                    'ADDEND',
                    'DEVIATION',
                    'CHECK_ALL',
                    'CHECK_MSG',
                    'CHECK_ABS',
                    'LOWER_LIMIT',
                    'UPPER_LIMIT',
                    'LIMIT_TOLER'                 # ---
                    , 'tk_DPGR', 'NAME'
                ]].drop_duplicates().reset_index(drop=True)

                v3_dpkt = self.dataFrames['V3_DPKT']
                v3_dpkt = v3_dpkt.sort_values(
                    by=['tk', 'NAME']).groupby(by='tk').first()
                v3_dpkt = v3_dpkt[
                    ~v3_dpkt['fkOBJTYPE'].isin(['-1', -1])
                ]
                self.dataFrames['V3_DPKT'] = v3_dpkt.reset_index()

            except Exception as e:
                logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                    logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
                logger.debug(logStrFinal)

                self.dataFrames['V3_DPKT'] = vDPKT_DPGR[[
                    'pk', 'OBJTYPE'                    # ,'fkOBJTYPE'
                    , 'ATTRTYPE', 'EPKZ', 'TITLE', 'UNIT', 'FLAGS'                    # ,'CLIENT_ID'
                    # ,'OPCITEM_ID'
                    , 'DESCRIPTION'                 # ---
                    , 'pk_DPGR', 'NAME'
                ]].drop_duplicates().reset_index(drop=True)

            # #############################################################
            # RXXX (RKNOT,RRUES,RVBEL)
            try:

                logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_RKNOT'))

                # RXXX-Nodes but RUES-Nodes
                vRXXX_nodes = ['RSLW', 'RMES', 'RHYS', 'RLVG', 'RLSR', 'RMMA', 'RADD',
                               'RMUL', 'RDIV', 'RTOT', 'RPT1', 'RINT', 'RPID', 'RFKT', 'RSTN']
                vRXXX_UnionList = []
                for NODE in vRXXX_nodes:
                    vName = 'V_BVZ_'+NODE
                    if vName in self.dataFrames:
                        vRXXX = self.dataFrames[vName]
                        if vRXXX is None:
                            pass
                        else:
                            vRXXX['OBJTYPE'] = NODE
                            vRXXX_UnionList.append(vRXXX)
                vRXXX = pd.concat(vRXXX_UnionList)
                vRXXX = vRXXX.rename(columns={'KA': 'Kn'})

                # all RXXX-Nodes
                V3_RKNOT_UnionList = []
                # [['OBJTYPE','BESCHREIBUNG','Kn','NAME','pk']])
                V3_RKNOT_UnionList.append(vRXXX)
                V3_RKNOT = pd.concat(V3_RKNOT_UnionList).reset_index(drop=True)
                self.dataFrames['V3_RKNOT'] = V3_RKNOT

                # RUES
                logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_RRUES'))
                # wahre Quelle (wahre SRC) ermitteln
                #  Ues sind nur Aliase fuer Signale (fuer Knoten)
                #  fuer jede Alias-Definition den wahren Signalnamen (Knotennamen) ermitteln

                # alle Ues
                vRUES = self.dataFrames['V_BVZ_RUES']
                # alle Kanten (alle Signalverbindungen)
                vCRGL = self.dataFrames['V_CRGL']
                # Ue-Definitionen per Kante (per Signal):
                vRUESDefs = pd.merge(
                    vRUES, vCRGL, left_on='pk', right_on='fkKk', suffixes=('', '_Edge'))
                if vRUESDefs.empty:
                    logger.debug(
                        "{0:s}vRUES: Referenz zu pk leer?! ...".format(logStr))
                    vRUESDefs = pd.merge(
                        vRUES, vCRGL, left_on='tk', right_on='fkKk', suffixes=('', '_Edge'))
                else:
                    rows, dummy = vRUESDefs.shape
                    df2 = pd.merge(vRUES, vCRGL, left_on='tk',
                                   right_on='fkKk', suffixes=('', '_Edge'))
                    rows2, dummy = df2.shape
                    if rows2 >= rows:
                        #logger.debug(
                        #    "{0:s}vRUES:: Referenz zu pk nicht leer aber tk findet mindestens genausoviel Treffer ...".format(logStr))
                        vRUESDefs = df2

                def get_UE_SRC(UeName  # Name der Ue deren SRC gesucht wird
                               , dfUes  # alle Ues (Defs und Refs)
                               , dfUesDefs  # alle Signalverbindungen die Ues definieren
                               ):
                    """
                    gibt per df diejenige Zeile von dfUesDefs zurueck die schlussendlich UeName definiert
                    fkKi ist dann die wahre Quelle von UeName
                    fkKi verweist dabei _nicht auf eine andere Ue, d.h. verkettete Referenzen werden bis zur wahren Quelle aufgeloest
                    """

                    df = dfUesDefs[dfUesDefs['IDUE'] == UeName]

                    if df['fkKi'].iloc[0] in dfUes['tk'].to_list():
                        
                        # die SRC der Ue ist eine Ue
                        #logger.debug("Die SRC der Ue {:s} ist eine Ue - die Ue-Def:\n{:s}".format(
                        #    UeName, str(df[['IDUE', 'pk', 'rkRUES', 'fkKi', 'fkKk']].iloc[0])))

                        # die Referenz
                        df = dfUes[dfUes['pk'] == df['fkKi'].iloc[0]]
                        df = dfUes[dfUes['pk'] ==
                                   df['rkRUES'].iloc[0]]  # die SRC

                        # print("{:s}".format((str(df[['IDUE','pk'
                        #                                                                      ,'rkRUES'
                        #                            #                                          ,'fkKi','fkKk'
                        #                            ]].iloc[0]))))

                        # Rekursion bis zur wahren Quelle
                        df = get_UE_SRC(df['IDUE'].iloc[0], dfUes, dfUesDefs
                                        )
                    else:
                        pass
                        #logger.debug("Die SRC der Ue {:s} gefunden -die Ue-Def:\n{:s}".format(
                        #    UeName, str(df[['IDUE', 'pk', 'rkRUES', 'fkKi', 'fkKk']].iloc[0])))

                    return df

                # fuer jede Ue-Definition die SRC bestimmen

                dcts = []
                for index, row in vRUESDefs.iterrows():

                    dfX = get_UE_SRC(row['IDUE']  # Name der Ue deren SRC gesucht wird
                                     , vRUES  # Ues
                                     , vRUESDefs  # Ue-Definitionen per Kante
                                     )
                    # df['fkKi'] ist die SRC
                    df=pd.DataFrame()
                    
                    df = V3_RKNOT[V3_RKNOT['pk'] == dfX['fkKi'].iloc[0]]
                    if df.empty:
                        
                        #logger.debug(
                        #    "{0:s}V3_RKNOT: Referenz zu pk leer?! ...".format(logStr))

                        df = V3_RKNOT[V3_RKNOT['tk'] == dfX['fkKi'].iloc[0]]
                    else:
                        df2 = V3_RKNOT[V3_RKNOT['tk'] == dfX['fkKi'].iloc[0]]

                        rows, dummy = df.shape
                        rows2, dummy = df2.shape

                        if rows2 >= rows:
                            #logger.debug(
                            #    "{0:s}V3_RKNOT: Referenz zu pk nicht leer aber tk findet mindestens genausoviel Treffer ...".format(logStr))
                            df = df2
                    
                    if df.empty:                        
                         logger.debug("{:s}{:12s} {:s}: UE-Symbol ohne Referenz?!".format(logStr,row['IDUE'],row['NAME_CONT']))        

                         dct = {'pk_DEF': row['pk'], 'tk_DEF': row['tk'], 'IDUE_DEF': row['IDUE']                           #
                                , 'OBJTYPE_SRC': None, 'OBJID_SRC': None, 'Kn_SRC': None, 'NAME_CONT_SRC': None
                                }
                         dcts.append(dct) #?!
                                                     
                    else:

                         dct = {'pk_DEF': row['pk'], 'tk_DEF': row['tk'], 'IDUE_DEF': row['IDUE']                           #
                               , 'OBJTYPE_SRC': df['OBJTYPE'].iloc[0], 'OBJID_SRC': df['pk'].iloc[0], 'Kn_SRC': df['Kn'].iloc[0], 'NAME_CONT_SRC': df['NAME_CONT'].iloc[0]
                               }
                         dcts.append(dct)

                    # break
                vRUESDefsSRCs = pd.DataFrame.from_dict(dcts)
                
                # UE-Symbole ohne Referenzen sind hier nicht enthalten
                logger.debug("{logStr:s}vRUESDefsSRCs: {vRUESDefsSRCs:s}".format(logStr=logStr,vRUESDefsSRCs=vRUESDefsSRCs.sort_values(by=['IDUE_DEF']).to_string())) 
                
                # Ausgabe, wo das Ue nicht so heisst wie die Quelle ...
                for index, row in vRUESDefsSRCs.sort_values(by=['IDUE_DEF']).iterrows():
                    
                    if row['IDUE_DEF'] != row['Kn_SRC']:
                        logger.debug("{logStr:s}IDUE_DEF: {IDUE_DEF!s:s} != Kn_SRC: {Kn_SRC!s:s} - ggf. ungewollt? ...".format(logStr=logStr
                                ,IDUE_DEF=row['IDUE_DEF']
                                ,Kn_SRC=row['Kn_SRC']
                                    )) 
                    
                # fuer alle Defs die wahre Quelle angeben
                #vRUES: self.dataFrames['V_BVZ_RUES']
                V3_RUES = pd.merge(vRUES.copy(deep=True), vRUESDefsSRCs, left_on='IDUE', right_on='IDUE_DEF', how='left')
                
                logger.debug("{logStr:s}V3_RUES Schritt 1: {V3_RUES:s}".format(logStr=logStr,V3_RUES=V3_RUES[['NAME_CONT','IDUE','IDUE_DEF','Kn_SRC','rkRUES']].sort_values(by=['IDUE_DEF']).to_string())) 

                # fuer alle Refs ebenfalls die wahre Quelle angeben
                for index, row in V3_RUES.iterrows():
                    #logger.debug("{logStr:s}{IDUE_DEF!s:s}".format(logStr=logStr,IDUE_DEF=row['IDUE_DEF'])) 
                    
                    
                    #logger.debug("{logStr:s}IDUE_DEF: {IDUE_DEF!s:s}, Kn_SRC: {Kn_SRC!s:s}".format(logStr=logStr
                    #        ,IDUE_DEF=row['IDUE_DEF']
                    #        ,Kn_SRC=row['Kn_SRC']
                    #            ))                     
                                        
                    if pd.isnull(row['IDUE_DEF']):
                                                                                         
                        rkRUES = row['rkRUES']
                        
                        dfx=vRUESDefsSRCs[vRUESDefsSRCs['tk_DEF']== rkRUES]
                        
                        (Treffer,dummy)=dfx.shape

                        #logger.debug("{logStr:s}IDUE_DEF ist NULL, rkRUES: {rkRUES:s}, Treffer: {Treffer:d}".format(logStr=logStr                                
                        #        ,rkRUES=row['rkRUES']
                        #        ,Treffer=Treffer
                        #            ))  
                                                
                        if Treffer == 0:

                            logger.debug("{logStr:s}IDUE_DEF ist NULL, rkRUES: {rkRUES:s}, KEIN Treffer?!".format(logStr=logStr                                
                                    ,rkRUES=row['rkRUES']                                    
                                        ))   
                            continue
                                                                    
                        if Treffer > 1:
                            logger.debug("{logStr:s}IDUE_DEF ist NULL, rkRUES: {rkRUES:s}, MEHR als 1 Treffer: {Treffer:d}?!".format(logStr=logStr                                
                                    ,rkRUES=row['rkRUES']
                                    ,Treffer=Treffer
                                        ))                              
                                                
                        s = dfx.iloc[0]                            
    
                        V3_RUES.loc[index, 'pk_DEF'] = s['pk_DEF']
                        V3_RUES.loc[index, 'IDUE_DEF'] = s['IDUE_DEF']
                        V3_RUES.loc[index, 'OBJTYPE_SRC'] = s['OBJTYPE_SRC']
                        V3_RUES.loc[index, 'Kn_SRC'] = s['Kn_SRC']
                        V3_RUES.loc[index,'NAME_CONT_SRC'] = s['NAME_CONT_SRC']

                        
                self.dataFrames['V3_RRUES'] = V3_RUES
                logger.debug("{logStr:s}V3_RUES Final: {V3_RUES:s}".format(logStr=logStr,V3_RUES=V3_RUES[['NAME_CONT','NAME_CONT_SRC','OBJTYPE_SRC','IDUE','IDUE_DEF','Kn_SRC','rkRUES','pk_DEF']].sort_values(by=['IDUE_DEF']).to_string()))                 

                # RKNOT voruebergehend erweitern um RUES um nachfolgend alle Kanten ausreferenzieren zu koennen
                logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_KNOT erweitern um RRUES'))

                V3_RKNOT = self.dataFrames['V3_RKNOT']
                vRUES = self.dataFrames['V_BVZ_RUES']
                vRUES = pd.merge(vRUES, vRUES, how='left', left_on='rkRUES',
                                 right_on='tk', suffixes=('', '_rkRUES'))
                vRUES['Kn'] = vRUES.apply(
                    lambda row: row.IDUE if row.IOTYP == '1' else row.IDUE_rkRUES, axis=1)
                vRUES['OBJTYPE'] = 'RUES'
                vRUES['BESCHREIBUNG'] = None
                V3_RKNOT = pd.concat([V3_RKNOT, vRUES[[
                                     'OBJTYPE', 'Kn', 'BESCHREIBUNG', 'pk', 'tk', 'NAME_CONT', 'IDUE', 'IOTYP']]]).reset_index(drop=True)
                
                # alle RXXX-Kanten
                logger.debug("{0:s}{1:s} ...".format(logStr, 'V3_RVBEL'))
                
                howMode = 'left'
                V_CRGL = self.dataFrames['V_CRGL']
                
                V3_RVBEL = pd.merge(V_CRGL, V3_RKNOT.add_suffix(
                    '_i'), left_on='fkKi', right_on='tk_i', how=howMode).filter(items=V_CRGL.columns.to_list()+['OBJTYPE_i','pk_i','tk_i','Kn_i','NAME_CONT_i'])
                V3_RVBEL['KnExt_i'] = V3_RVBEL['Kn_i'] + \
                    '_'+V3_RVBEL['OBJTYPE_i']
                    
                V3_RVBEL = pd.merge(V3_RVBEL, V3_RKNOT.add_suffix(
                    '_k'), left_on='fkKk', right_on='tk_k', how=howMode).filter(items=V3_RVBEL.columns.to_list()+['OBJTYPE_k','pk_k','tk_k','Kn_k','NAME_CONT_k'])
                V3_RVBEL['KnExt_k'] = V3_RVBEL['Kn_k'] + \
                    '_'+V3_RVBEL['OBJTYPE_k']

                V3_RVBEL = Xm.Xm.constructNewMultiindexFromCols(df=V3_RVBEL, mColNames=[
                                                                'OBJTYPE_i', 'OBJTYPE_k', 'pk'], mIdxNames=['OBJTYPE_i', 'OBJTYPE_k', 'OBJID'])

                V3_RVBEL = V3_RVBEL[~V3_RVBEL.index.get_level_values(
                    'OBJTYPE_k').isin(['RUES'])]

                V3_RVBEL = V3_RVBEL[~
                                    (
                                        (V3_RVBEL.index.get_level_values(
                                            'OBJTYPE_i').isin(['RUES']))
                                        &
                                        (V3_RVBEL.index.get_level_values(
                                            'OBJTYPE_k').isin(['RUES']))
                                    )
                                    ]

                
                # RUES-Verbindungen zur Quelle hin aufloesen ...                
                logger.debug("{0:s}{1:s} RUES-Verbindungen zur Quelle hin aufloesen ...".format(logStr, 'V3_RVBEL'))

                V3_RVBEL = V3_RVBEL.reset_index()
                V3_RRUES = self.dataFrames['V3_RRUES']
                for index, row in V3_RVBEL[V3_RVBEL['OBJTYPE_i'].isin(['RUES'])].iterrows():
                    
                    dfx=V3_RRUES[V3_RRUES['tk'] == row['fkKi']]
                    (Treffer,dummy)=dfx.shape
                    
                    if Treffer == 0:                   
                        logger.debug("{logStr:s}OBJTYPE_i: {OBJTYPE_i:s} Kn_i: {Kn_i:s}  KEIN Treffer?!".format(logStr=logStr                                
                                ,OBJTYPE_i=row['OBJTYPE_i']      
                                ,Kn_i=row['Kn_i']      
                                    ))   
                        continue
                                                                
                    if Treffer > 1:
                        logger.debug("{logStr:s}OBJTYPE_i: {OBJTYPE_i:s} Kn_i: {Kn_i:s}  MEHR als 1 Treffer: {Treffer:d}?!".format(logStr=logStr                                
                                ,OBJTYPE_i=row['OBJTYPE_i']      
                                ,Kn_i=row['Kn_i']      
                                ,Treffer=Treffer
                                    ))                           
                                                                                      
                    s = dfx.iloc[0]
                    
                    #logger.debug("{logStr:s}OBJTYPE_i: {OBJTYPE_i:s} Kn_i: {Kn_i:s} Treffer: {Treffer!s:s}?!".format(logStr=logStr                                
                    #        ,OBJTYPE_i=row['OBJTYPE_i']      
                    #        ,Kn_i=row['Kn_i']      
                    #        ,Treffer=s
                    #            ))         

                    V3_RVBEL.loc[index, 'OBJTYPE_i'] = s['OBJTYPE_SRC']
                    # V3_RVBEL.loc[index,'OBJID_i']=s['OBJID_SRC']
                    V3_RVBEL.loc[index, 'Kn_i'] = s['Kn_SRC']
                    V3_RVBEL.loc[index, 'KnExt_i'] = s['Kn_SRC'] + \
                        '_'+s['OBJTYPE_SRC']
                    V3_RVBEL.loc[index, 'NAME_CONT_i'] = s['NAME_CONT_SRC']

                
                V3_RVBEL=V3_RVBEL[~pd.isnull(V3_RVBEL['tk'])]
                V3_RVBEL = Xm.Xm.constructNewMultiindexFromCols(df=V3_RVBEL, mColNames=[
                                                                'OBJTYPE_i', 'OBJTYPE_k', 'OBJID'], mIdxNames=['OBJTYPE_i', 'OBJTYPE_k', 'OBJID'])
                self.dataFrames['V3_RVBEL'] = V3_RVBEL

            except Exception as e:
                logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                    logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
                logger.debug(logStrFinal)

        except Exception as e:
            logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
            logger.error(logStrFinal)
            raise DxError(logStrFinal)
        finally:
            logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))

    def MxSync(self, mx):
        """
        adds mx2Idx to V3_KNOT, V3_ROHR, V3_FWVB, ggf. weitere
        adds mx2NofPts to V3_ROHR        
        """

        logStr = "{0:s}.{1:s}: ".format(
            self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

        try:

            for dfName, resType in zip(['V3_KNOT', 'V3_ROHR', 'V3_FWVB'], ['KNOT', 'ROHR', 'FWVB']):

                if mx.mx2Df[mx.mx2Df['ObjType'].str.match(resType)].empty:
                    logger.debug(
                        "{:s}resType: {:s} hat keine mx2-Eintraege.".format(logStr, resType))
                    continue
                else:
                    logger.debug(
                        "{:s}resType: {:s} ...".format(logStr, resType))

                # mx2Idx ergaenzen

                # Liste der IDs in Mx2
                xksMx = mx.mx2Df[
                    (mx.mx2Df['ObjType'].str.match(resType))
                    &  # nur wg. ROHRe erf.
                    ~(mx.mx2Df['AttrType'].str.contains('N_OF_POINTS'))
                ]['Data'].iloc[0]

                # xk: pk oder tk
                xkTypeMx = mx.mx2Df[
                    (mx.mx2Df['ObjType'].str.match(resType))
                    &  # nur wg. ROHRe erf.
                    ~(mx.mx2Df['AttrType'].str.contains('N_OF_POINTS'))
                ]['AttrType'].iloc[0].strip()

                # lesen
                df = self.dataFrames[dfName]

                # Liste der xks
                xksXm = df[xkTypeMx]

                # zugeh. Liste der mx2Idx in df
                mxXkIdx = [xksMx.index(xk) for xk in xksXm]

                if resType == 'ROHR':

                    # Liste der N_OF_POINTS in Mx2
                    nopMx = mx.mx2Df[
                        (mx.mx2Df['ObjType'].str.match(resType))
                        &
                        (mx.mx2Df['AttrType'].str.contains('N_OF_POINTS'))
                    ]['Data'].iloc[0]

                    # zugeh. Liste der NOfPts in df
                    nopXk = [nopMx[mx2Idx] for mx2Idx in mxXkIdx]

                    # Spalte mx2NofPts anlegen (vor Spalte mx2Idx)
                    df['mx2NofPts'] = pd.Series(nopXk)

                # Spalte mx2Idx anlegen
                df['mx2Idx'] = pd.Series(mxXkIdx)

        except Exception as e:
            logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
            logger.error(logStrFinal)
            raise DxError(logStrFinal)
        finally:
            logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))

    # ,readFromMxs=False):
    def MxAdd(self, mx, addNodeData=True, addNodeDataSir3sVecIDReExp='^KNOT~\*~\*~\*~PH$'):
        """
        adds Vec-Results using mx' getVecAggsResultsForObjectType to V3_KNOT, V3_ROHR, V3_FWVB, ggf. weitere

        returns dct V3s; keys: V3_KNOT, V3_ROHR, V3_FWVB, ggf. weitere
        source: V3_KNOT, V3_ROHR, V3_FWVB, ggf. weitere      

        columns: 
            * Bsp.: V3s['V3_FWVB'][('TMAX', 'FWVB~*~*~*~P1', pd.Timestamp('2022-01-21 09:00:00'), pd.Timestamp('2022-01-21 09:01:00'))]

        V3_ROHR and V3_FWVB:
            if addNodeData: V3_KNOT ResData matching addNodeDataSir3sVecIDReExp is added as columns named with postfix _i and _k:
            * Bsp.: V3s['V3_FWVB']["('TMAX', 'KNOT~*~*~*~PH', Timestamp('2022-01-21 09:00:00'), Timestamp('2022-01-21 09:01:00'))_k"]

        """

        logStr = "{0:s}.{1:s}: ".format(
            self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

        try:
            V3 = {}
            for dfName, resType in zip(['V3_KNOT', 'V3_ROHR', 'V3_FWVB'], ['^KNOT', '^ROHR~', '^FWVB']):
                # Ergebnisse lesen
                dfRes = mx.getVecAggsResultsForObjectType(resType)

                #logger.debug("{0:s}dfRes: {1:s}".format(logStr,dfRes.to_string()))

                if dfName == 'V3_KNOT' and addNodeData:

                    # df mit Knotenergebnissen merken
                    dfKnotRes = dfRes
                    # gewünschte Ergebnisspalten von Knoten
                    Sir3sIDs = dfKnotRes.columns.get_level_values(1)
                    Sir3sIDsMatching = [Sir3sID for Sir3sID in Sir3sIDs if re.search(
                        addNodeDataSir3sVecIDReExp, Sir3sID) != None]
                    # die zur Ergänzung gewünschten Ergebnisspalten von Knoten
                    dfKnotRes = dfKnotRes.loc[:, (slice(
                        None), Sir3sIDsMatching, slice(None), slice(None))]
                    dfKnotRes.columns = dfKnotRes.columns.to_flat_index()

                dfRes.columns = dfRes.columns.to_flat_index()

                # Sachspalten lesen
                df = self.dataFrames[dfName]

                # Ergebnisspalten ergänzen
                V3[dfName] = df.merge(
                    dfRes, left_on='tk', right_index=True, how='left')  # inner

            if addNodeData:

                for dfName in ['V3_ROHR', 'V3_FWVB']:
                    df = V3[dfName]
                    df = pd.merge(df, dfKnotRes.add_suffix(
                        '_i'), left_on='fkKI', right_index=True, how='left')   # inner
                    df = pd.merge(df, dfKnotRes.add_suffix(
                        '_k'), left_on='fkKK', right_index=True, how='left')   # inner
                    V3[dfName] = df

        except Exception as e:
            logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
            logger.error(logStrFinal)
            raise DxError(logStrFinal)
        finally:
            logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))
            return V3

    def ShpAdd(self, shapeFile, crs='EPSG:25832', onlyObjectsInContainerLst=['M-1-0-1'], addNodeData=False, NodeDataKey='pk'):
        """
        returns dct with (hopefully) plottable GeoDataFrames; keys: V3_KNOT, V3_ROHR, V3_FWVB, ggf. weitere
        source: V3_KNOT, V3_ROHR, V3_FWVB, ggf. weitere

        adds Geometry from shapeFile (3S Shapefile-Export) to V3_KNOT, V3_ROHR, V3_FWVB, ggf. weitere

        geometry is set to shapeFile's column geometry
        crs is set to crs

        auch wenn SIR 3S ab N zukuenftig nativ eine Geometriespalte haelt, kann es sinnvoll sein 
        fuer bestimmte Darstellungszwecke Geometrien (zu generieren) und hier zuzuordnen 

        V3_FWVB:
            Geometry: LineString is converted to Point 
        V3_ROHR and V3_FWVB:
            if addNodeData: all V3_KNOT Data is added as columns named with postfix _i and _k

        """

        logStr = "{0:s}.{1:s}: ".format(
            self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

        try:
            shpGdf = geopandas.read_file(shapeFile)
            shpGdf.set_crs(crs=crs, inplace=True, allow_override=True)

            shpGdf = shpGdf[['3SPK', 'TYPE', 'geometry']]
            shpGdf.rename(columns={'TYPE': 'TYPE_shp'}, inplace=True)

            V3 = {}
            try:
                for dfName, shapeType in zip(['V3_KNOT', 'V3_ROHR', 'V3_FWVB'], ['KNOT', 'ROHR', 'FWVB']):
                    df = self.dataFrames[dfName]
                    if 'geometry' in df.columns.to_list():
                        df = df.drop(columns='geometry')
                    df = df.merge(shpGdf[shpGdf.TYPE_shp == shapeType], left_on='pk', right_on='3SPK', how='left').filter(
                        items=df.columns.to_list()+['geometry'])
                    gdf = geopandas.GeoDataFrame(df, geometry='geometry')
                    gdf.set_crs(crs=crs, inplace=True, allow_override=True)
                    gdf = gdf[
                        # nur Objekte fuer die das shapeFile eine Geometrieinformation geliefert hat
                        ~(gdf['geometry'].isin([None, '', np.nan]))
                        &
                        # keine Objekte in z.B. Stationen
                        (gdf['NAME_CONT'].isin(onlyObjectsInContainerLst))
                    ]
                    V3[dfName] = gdf
            except Exception as e:
                logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                    logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
                logger.debug(logStrFinal)
                # empty DataFrame if problem occured
                V3[dfName] = pd.DataFrame()

            # Nacharbeiten FWVB
            if 'V3_FWVB' in V3.keys():
                gdf = V3['V3_FWVB']
                for index, row in gdf.iterrows():
                    if not pd.isnull(row['geometry']):
                        if isinstance(row['geometry'], shapely.geometry.linestring.LineString):
                            gdf.loc[index, 'geometry'] = row['geometry'].centroid
                V3['V3_FWVB'] = gdf

            # Nacharbeiten addNodeData
            if addNodeData:
                for dfName in ['V3_ROHR', 'V3_FWVB']:
                    df = V3[dfName]
                    df = pd.merge(df, self.dataFrames['V3_KNOT'].add_suffix(
                        '_i'), left_on='fkKI', right_on=NodeDataKey+'_i')
                    df = pd.merge(df, self.dataFrames['V3_KNOT'].add_suffix(
                        '_k'), left_on='fkKK', right_on=NodeDataKey+'_k')
                    V3[dfName] = df

        except Exception as e:
            logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
            logger.error(logStrFinal)
            raise DxError(logStrFinal)

        finally:
            logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))
            return V3

    def _filterTemplateObjects(self):
        """        
        filters TemplateObjects 
        in V3_KNOT, V3_ROHR, V3_FWVB
        """

        logStr = "{0:s}.{1:s}: ".format(
            self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

        try:
            for dfName in ['V3_KNOT', 'V3_ROHR', 'V3_FWVB']:
                df = self.dataFrames[dfName]
                if 'KENNUNG' in df.columns.to_list():
                    df = df[(df['KENNUNG'] >= 0)
                            |
                            (pd.isnull(df['KENNUNG']))
                            ]
                else:
                    df = df[~df['BESCHREIBUNG'].str.contains('^Templ',na=False)]
                self.dataFrames[dfName] = df

        except Exception as e:
            logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
            logger.error(logStrFinal)
            raise DxError(logStrFinal)
        finally:
            logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))

    def _vROHRVecs(self, vROHR, mx):
        """Adds MX-ROHR-VEC-Results in dfVecAggs as cols to df.

        Args:
            vROHR: df (i.a. dataFrames['V3_ROHR'])
            cols expected in vROHR (call MxSync to add this cols to dataFrames['V3_ROHR']):
                mx2Idx
                mx2NofPts

        Returns:
            df with 
                vROHR's cols 
                IptIdx (S(tart), 0,1,2,3,... ,E(nde))
                x: fortl. Rohrachskoordinate errechnet aus L und mx2NofPts
                cols with MX-ROHR-VEC-Results i.e. (STAT, ROHR~*~*~*~MVEC, 2022-09-28 13:24:00, 2022-09-28 13:24:00)                          
        """

        logStr = "{0:s}.{1:s}: ".format(
            self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

        try:

            df = pd.DataFrame()

            # alle MX-ROHR-VEC-Results in dfVecAggs
            dfT = mx.dfVecAggs.loc[(slice(None), mx.getRohrVektorkanaeleIpkt(), slice(
                None), slice(None)), :].transpose()
            dfT.columns = dfT.columns.to_flat_index()
            # cols= (STAT, ROHR~*~*~*~MVEC, 2022-09-28 13:24:00, 2022-09-28 13:24:00) ...
            # idx= 0,1,2,3,...

            # dfT mit mx2Idx annotieren, damit merge vROHR moeglich
            # dfT mit IptIdx annotieren, damit IPKT-Sequenz leichter lesbar
            rVecMx2Idx = []
            IptIdx = []

            # Mx2-Records sind in Mx2-Reihenfolge und muessen auch so annotiert werden ...
            for row in vROHR.sort_values(['mx2Idx']).itertuples():
                oneVecIdx = np.empty(row.mx2NofPts, dtype=int)
                oneVecIdx.fill(row.mx2Idx)
                rVecMx2Idx.extend(oneVecIdx)

                oneLfdNrIdx = ['S']
                if row.mx2NofPts > 2:
                    oneLfdNrIdx.extend(np.arange(row.mx2NofPts-2, dtype=int))
                oneLfdNrIdx.append('E')
                IptIdx.extend(oneLfdNrIdx)

            dfTCols = dfT.columns.to_list()
            dfT['mx2Idx'] = rVecMx2Idx
            dfT['IptIdx'] = IptIdx

            # merge
            df = pd.merge(vROHR, dfT, how='inner',
                          left_on='mx2Idx', right_on='mx2Idx')

            # x
            df['dx'] = df.apply(lambda row: row.L/(row.mx2NofPts-1), axis=1)
            df['x'] = df.groupby('mx2Idx')['dx'].cumsum()
            df['x'] = df.apply(lambda row: row.x-row.dx, axis=1)

            # Reorg der Spalten
            df = df.filter(items=vROHR.columns.to_list() +
                           ['IptIdx', 'x']+dfTCols)

        except Exception as e:
            logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
            logger.debug(logStrFinal)

        finally:
            logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))
            return df

    def _vROHRVrtx(self, vROHR, mx):
        """Adds MX-ROHR-VRTX-Results in dfVecAggs as cols to df.

        Args:
            vROHR: df (i.a. dataFrames['V3_ROHR'])


        Returns:
            df with 
                vROHR's cols 
                VRTX-Cols:
                    pk_Vrtx
                    fk_Vrtx
                    XKOR
                    YKOR
                    ZKOR
                    LFDNR
                    mx2IdxVrtx        
                        the df is sorted by mx2IdxVrtx (should be equal to sort by ROHR, VRTX-LFDNR)
                s: fortl. Rohrachskoordinate errechnet aus VRTX
                cols with MX-ROHR-VRTX-Results i.e. (STAT, ROHR_VRTX~*~*~*~M, 2022-09-28 13:24:00, 2022-09-28 13:24:00)                          
        """

        logStr = "{0:s}.{1:s}: ".format(
            self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

        try:

            df = pd.DataFrame()

            # alle MX-ROHR-VRTX-Results in dfVecAggs
            dfT = mx.dfVecAggs.loc[(slice(None), mx.getRohrVektorkanaeleVrtx(), slice(
                None), slice(None)), :].transpose()
            dfT.columns = dfT.columns.to_flat_index()
            # cols= (STAT, ROHR~*~*~*~MVEC, 2022-09-28 13:24:00, 2022-09-28 13:24:00) ...
            # idx= 0,1,2,3,...

            # Liste der VRTX-PKs in MX2
            xksMx = mx.mx2Df[
                (mx.mx2Df['ObjType'].str.match('ROHR_VRTX'))
            ]['Data'].iloc[0]

            vROHR_VRTX = self.dataFrames['V_ROHR_VRTX']
            # diese Liste sollte leer sein:
            l = [x for x in xksMx if x not in vROHR_VRTX['pk'].values]
            if len(l) != 0:
                logger.error(
                    "{:s}Es gibt Verweise in MX2 die auf keinen VRTX-Wegpunkt zeigen?!".format(logStr))

            # -1 aussortieren
            # keine Sachdaten VRTX-Wegpunkte ohne Nennung in MX-VRTX
            vROHR_VRTX_eff = vROHR_VRTX[vROHR_VRTX['pk'].isin(xksMx)]

            # nur die Sach-ROHRe die Sach-Wegpunkte haben
            vROHR_eff = vROHR[vROHR['pk'].isin(vROHR_VRTX_eff['fk'].values)]

            # Wegpunkte
            df = pd.merge(vROHR_eff, vROHR_VRTX_eff.filter(items=['pk',
                                                                  'fk',
                                                                  'XKOR',
                                                                  'YKOR',
                                                                  'ZKOR',
                                                                  'LFDNR',
                                                                  ]), left_on='pk', right_on='fk', suffixes=('', '_Vrtx'))

            # Vorbereitung fuer Merge mit MX
            df['mx2IdxVrtx'] = [xksMx.index(xk) for xk in df['pk_Vrtx'].values]

            # Merge mit MX
            # df=pd.merge(df,dfT,how='inner',left_on='mx2IdxVrtx',right_index=True)

            df.sort_values(by=['mx2IdxVrtx'], inplace=True)
            df.reset_index(drop=True, inplace=True)

            # s errechnen

            dfTmp = df[['pk', 'LFDNR', 'XKOR', 'YKOR', 'ZKOR']]

            dfTmp['XKOR'] = dfTmp.groupby(
                ['pk'])['XKOR'].shift(periods=1, fill_value=0)
            dfTmp['YKOR'] = dfTmp.groupby(
                ['pk'])['YKOR'].shift(periods=1, fill_value=0)
            dfTmp['ZKOR'] = dfTmp.groupby(
                ['pk'])['ZKOR'].shift(periods=1, fill_value=0)

            dfTmp.rename(
                columns={'XKOR': 'DXKOR', 'YKOR': 'DYKOR', 'ZKOR': 'DZKOR'}, inplace=True)

            dfTmp = pd.concat([df[['mx2IdxVrtx', 'pk', 'L', 'LFDNR', 'XKOR', 'YKOR', 'ZKOR']], dfTmp[[
                              'DXKOR', 'DYKOR', 'DZKOR']]], axis=1)

            dfTmp['DXKOR'] = dfTmp.apply(lambda row: math.fabs(
                row.XKOR-row.DXKOR) if row.DXKOR > 0 else 0, axis=1)
            dfTmp['DYKOR'] = dfTmp.apply(lambda row: math.fabs(
                row.YKOR-row.DYKOR) if row.DYKOR > 0 else 0, axis=1)
            dfTmp['DZKOR'] = dfTmp.apply(lambda row: math.fabs(
                row.ZKOR-row.DZKOR) if row.DZKOR > 0 else 0, axis=1)

            dfTmp['ds'] = dfTmp.apply(lambda row: math.sqrt(math.pow(
                row.DZKOR, 2)+math.pow(math.sqrt(math.pow(row.DXKOR, 2)+math.pow(row.DYKOR, 2)), 2)), axis=1)
            dfTmp['s'] = dfTmp.groupby('pk')['ds'].cumsum()

            df = pd.concat([df, dfTmp[['s']]], axis=1)

            # Merge mit MX
            df = pd.merge(df, dfT, how='inner',
                          left_on='mx2IdxVrtx', right_index=True)

        except Exception as e:
            logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
                logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
            logger.debug(logStrFinal)

        finally:
            logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))
            return df

    def update(self,dfUpd):               
        """
        Updates (nur für SQLite Datenbanken)
        
        Args:
        -----
            * dfUpd: df with update data
            * requested cols:
                * table i.e. 'FWVB'
                * attrib i.e. 'W0'   
                * attribValue i.e. 6.55
                * xk i.e. 'tk'
                * xkValue i.e. 5423055592859548388
        
        Raises
        ------
        DxError

        Returns
        -------
        None

        """

        logStr = "{0:s}.{1:s}: ".format(
            self.__class__.__name__, sys._getframe().f_code.co_name)
        logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

        try:
            if os.path.exists(self.dbFile):
                if os.access(self.dbFile, os.W_OK):
                    pass
                else:
                    logStrFinal="{:s}dbFile: {:s}: Not writable.".format(logStr,self.dbFile)   
                    raise DxError(logStrFinal)
           
            # das dbFile existiert und ist lesbar
            logger.debug("{:s}dbFile: {:s} existiert und ist beschreibbar".format(
                logStr, self.dbFile))
            
            dummy, ext = os.path.splitext(self.dbFile)

            if ext != '.db3':
                 logStrFinal = "{:s}Update-Funktion nur fuer .db3 implementiert!".format(logStr)
                 raise DxError(logStrFinal)                
                           
            con = sqlite3.connect(self.dbFile)
            
            def updateFct(con,sql,OBJID,VALUE):
                """
                """
                cur = con.cursor()
                cur.execute(sql,(VALUE,OBJID))
                con.commit()
                                    
            try:                
                for index, row in dfUpd.iterrows():
                    sqlCmd = '''UPDATE {table:s} SET {attrib:s} = ? WHERE {xk:s} = ?'''.format(table=row['table'],attrib=row['attrib'],xk=row['xk'])
                    logStrSql="sqlCmd: {sqlCmd:s}: {attribValue:s} {xkValue:s} ...".format(sqlCmd=sqlCmd,attribValue=str(row['attribValue']),xkValue=str(row['xkValue']))
                    logger.debug("{:s}{:s}".format(logStr,logStrSql))
                    updateFct(con,sqlCmd,row['xkValue'],row['attribValue'])
            except Exception as e:
                logStrTmp = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
                logger.error("{:s} Last sqlCmd: {:s}".format(logStrTmp,logStrSql))
            finally:
                con.close()

        except Exception as e:
           logStrFinal = "{:s}Exception: Line: {:d}: {!s:s}: {:s}".format(
               logStr, sys.exc_info()[-1].tb_lineno, type(e), str(e))
           logger.debug(logStrFinal)
    
        finally:
           logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))       


def fHelperSqlText(sql, ext='.db3'):
    if ext != '.db3':
        from sqlalchemy import text
        return text(sql)
    else:
        return sql


def fHelper(con, BV, BZ, dfViewModelle, dfCONT, pairType, ext):

    logStr = "{0:s}.{1:s}: ".format(__name__, sys._getframe().f_code.co_name)
    logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

    # BV, BZ, BVZ #################

    sql = 'select * from '+BV
    try:
        dfBV = pd.read_sql(fHelperSqlText(sql, ext), con)
    except pd.io.sql.DatabaseError as e:
        logStrFinal = "{0:s}sql: {1:s}: Fehler?!".format(logStr, sql)
        raise DxError(logStrFinal)

    sql = 'select * from '+BZ
    try:
        dfBZ = pd.read_sql(fHelperSqlText(sql, ext), con)
    except pd.io.sql.DatabaseError as e:
        logStrFinal = "{0:s}sql: {1:s}: Fehler?!".format(logStr, sql)
        raise DxError(logStrFinal)

    dfBVZ = pd.merge(dfBZ, dfBV, left_on=['fk'], right_on=[
                     'pk'], suffixes=('_BZ', ''))

    if 'tk' in dfBV.columns.to_list():
        dfBVZ_tk = pd.merge(dfBZ, dfBV, left_on=['fk'], right_on=[
                            'tk'], suffixes=('_BZ', ''))

        if dfBVZ_tk.shape[0] >= dfBVZ.shape[0]:
            dfBVZ = dfBVZ_tk

    if dfBVZ.empty:
        logger.debug("{0:s}{1:s} {2:s} BVZ LEER ?!".format(logStr, BV, BZ))

    newCols = dfBVZ.columns.to_list()
    dfBVZ = dfBVZ.filter(items=[col for col in dfBV.columns.to_list(
    )]+[col for col in newCols if col not in dfBV.columns.to_list()])

    # CONT etc. #############################
    dfBVZ = fHelperCONTetc(dfBVZ, BV, BZ, dfViewModelle, dfCONT, pairType)

    if dfBVZ.empty:
        logger.debug(
            "{0:s}{1:s} {2:s} BVZ LEER nach CONT?!".format(logStr, BV, BZ))

    logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))
    return dfBV, dfBZ, dfBVZ


def fHelperCONTetc(dfBVZ, BV, BZ, dfViewModelle, dfCONT, pairType):

    logStr = "{0:s}.{1:s}: ".format(__name__, sys._getframe().f_code.co_name)
    logger.debug("{0:s}{1:s}".format(logStr, 'Start.'))

    logger.debug(
        "{0:s}Quelle dfBVZ BV: {1:s} Quelle dfBVZ BZ: {2:s}".format(logStr, BV, BZ))

    # CONT etc. #############################

    cols = dfBVZ.columns.to_list()

    if 'fkDE_BZ' in cols:
        dfOrig = dfBVZ
        df = pd.merge(dfBVZ, dfViewModelle, left_on=['fkDE_BZ'], right_on=[
                      'fkBZ'], suffixes=('', '_VMBZ'))
        if df.empty:
            logger.debug("{0:s}{1:s}".format(
                logStr, 'fkDE_BZ ist vmtl. kein BZ-Schluessel, da es sich vmtl. um keine BZ-Eigenschaft handelt sondern um eine BV-Eigenschaft; Spalten werden umbenannt und es wird nach BV-DE gesucht ...'))
            renDct = {col: col.replace('_BZ', '_BV') for col in df.columns.to_list(
            ) if re.search('_BZ$', col) != None}
            dfOrig.rename(columns=renDct, inplace=True)

            if 'fkDE' in cols:
                logger.debug("{0:s}{1:s}".format(
                    logStr, 'fkDE ist auch in den Spalten ...'))

                df = pd.merge(dfOrig, dfViewModelle, left_on=['fkDE'], right_on=[
                              'fkBASIS'], suffixes=('', '_VMBASIS'), how='left')
                df = pd.merge(df, dfViewModelle, left_on=['fkDE'], right_on=[
                              'fkVARIANTE'], suffixes=('', '_VMVARIANTE'), how='left')

            else:
                logger.debug("{0:s}{1:s}".format(
                    logStr, 'fkDE ist nicht in den Spalten?!'))

    elif 'fkDE' in cols:  # (und 'fkDE_BZ' gibt es nicht)
        df = pd.merge(dfBVZ, dfViewModelle, left_on=['fkDE'], right_on=[
                      'fkBASIS'], suffixes=('', '_VMBASIS'), how='left')
        df = pd.merge(df, dfViewModelle, left_on=['fkDE'], right_on=[
                      'fkVARIANTE'], suffixes=('', '_VMVARIANTE'), how='left')
    else:
        df = dfBVZ

    if 'fkCONT' in cols:
        dfTmp = df
        df = pd.merge(df, dfCONT.add_suffix('_CONT'), left_on=['fkCONT'], right_on=['pk_CONT']
                      # ,suffixes=('','_CONT')
                      )
        if df.empty:
            df = pd.merge(dfTmp, dfCONT.add_suffix('_CONT'), left_on=['fkCONT'], right_on=['tk_CONT']  # !
                          # ,suffixes=('','_CONT')
                          )
        else:
            # pk-Menge ist nicht leer; aber ggf. werden ueber tk mehr/weitere gezogen
            dfTk = pd.merge(dfTmp, dfCONT.add_suffix('_CONT'), left_on=['fkCONT'], right_on=['tk_CONT']  # !
                            # ,suffixes=('','_CONT')
                            )
            rows, cols = df.shape
            rowsTk, colsTk = dfTk.shape
            dfXk = pd.concat([df, dfTk]).drop_duplicates()
            rowsXk, colsXk = dfXk.shape
            if rowsXk > rows:
                if rowsTk == rowsXk:
                    logger.debug(
                        "{:s}rowsXk: {:d} rowsTk: {:d} rowsPk: {:d} - pk-Menge ist nicht leer; aber tk zieht alle.".format(logStr, rowsXk, rowsTk, rows))
                else:
                    # tk zieht auch nicht die volle Menge
                    logger.debug(
                        "{:s}rowsXk: {:d} rowsTk: {:d} rowsPk: {:d} - pk-Menge ist nicht leer; aber ueber tk werden NICHT alle gezogen?!".format(logStr, rowsXk, rowsTk, rows))
                df = dfXk

    if pairType == '_ROWT':
        if 'ZEIT' in df.columns.to_list():
            df['lfdNrZEIT'] = df.sort_values(['pk', 'ZEIT'], ascending=True, na_position='first').groupby([
                'pk'])['ZEIT'].cumcount(ascending=True)+1
        else:
            logger.debug(
                "{0:s}pairType ROWT: df hat keine Spalte ZEIT?!".format(logStr))
            df = dfBVZ

    dfBVZ = df

    logger.debug("{0:s}{1:s}".format(logStr, '_Done.'))
    return dfBVZ
