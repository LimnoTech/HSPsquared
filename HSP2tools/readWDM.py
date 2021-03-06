''' Copyright (c) 2020 by RESPEC, INC.
Author: Robert Heaphy, Ph.D.

Based on MATLAB program by Seth Kenner, RESPEC
License: LGPL2
'''

import numpy as np
import pandas as pd
from numba import jit
import datetime

# look up attributes NAME, data type (Integer; Real; String) and data length by attribute number
attrinfo = {1:('TSTYPE','S',4),     2:('STAID','S',16),    11:('DAREA','R',1),
           17:('TCODE','I',1),     27:('TSBYR','I',1),     28:('TSBMO','I',1),
           29:('TSBDY','I',1),     30:('TSBHR','I',1),     32:('TFILL', 'R',1),
           33:('TSSTEP','I',1),    34:('TGROUP','I',1),    45:('STNAM','S',48),
           83:('COMPFG','I',1),    84:('TSFORM','I',1),    85:('VBTIME','I',1),
          444:('DATMOD','S',12),  443:('DATCRE','S',12),   22:('DCODE','I',1),
           10:('DESCRP','S', 80),   7:('ELEV','R',1),       8:('LATDEG','R',1),
            9:('LNGDEG','R',1),   288:('SCENARIO','S',8), 289:('CONSTITUENT','S',8),
          290:('LOCATION','S',8)}

freq = {7:'100YS', 6:'YS', 5:'MS', 4:'D', 3:'H', 2:'min', 1:'S'}   # pandas date_range() frequency by TCODE, TGROUP

def readWDM(wdmfile, hdffile, jupyterlab=True):
    iarray = np.fromfile(wdmfile, dtype=np.int32)
    farray = np.fromfile(wdmfile, dtype=np.float32)

    if iarray[0] != -998:
        print('Not a WDM file, magic number is not -990. Stopping!')
        return
    nrecords    = iarray[28]    # first record is File Definition Record
    ntimeseries = iarray[31]

    dsnlist = []
    for index in range(512, nrecords * 512, 512):
        if not (iarray[index]==0 and iarray[index+1]==0 and iarray[index+2]==0 and iarray[index+3]==0) and iarray[index+5]==1:
            dsnlist.append(index)
    if len(dsnlist) != ntimeseries:
        print('PROGRAM ERROR, wrong number of DSN records found')

    with pd.HDFStore(hdffile) as store:
        summary = []
        summaryindx = []

        # check to see which extra attributes are on each dsn
        columns_to_add = []
        search = ['STAID', 'STNAM', 'SCENARIO', 'CONSTITUENT', 'LOCATION']
        for att in search:
            found_in_all = True
            for index in dsnlist:
                dattr = {}
                psa = iarray[index + 9]
                if psa > 0:
                    sacnt = iarray[index + psa - 1]
                for i in range(psa + 1, psa + 1 + 2 * sacnt, 2):
                    id = iarray[index + i]
                    ptr = iarray[index + i + 1] - 1 + index
                    if id not in attrinfo:
                        continue
                    name, atype, length = attrinfo[id]
                    if atype == 'I':
                        dattr[name] = iarray[ptr]
                    elif atype == 'R':
                        dattr[name] = farray[ptr]
                    else:
                        dattr[name] = ''.join([itostr(iarray[k]) for k in range(ptr, ptr + length // 4)]).strip()
                if att not in dattr:
                    found_in_all = False
            if found_in_all:
                columns_to_add.append(att)

        for index in dsnlist:
            # get layout information for TimeSeries Dataset frame
            dsn   = iarray[index+4]
            psa   = iarray[index+9]
            if psa > 0:
                sacnt = iarray[index+psa-1]
            pdat  = iarray[index+10]
            pdatv = iarray[index+11]
            frepos = iarray[index+pdat]

            print(f'{dsn} reading from wdm')
            # get attributes
            dattr = {'TSBDY':1, 'TSBHR':1, 'TSBMO':1, 'TSBYR':1900, 'TFILL':-999.}   # preset defaults
            for i in range(psa+1, psa+1 + 2*sacnt, 2):
                id = iarray[index + i]
                ptr = iarray[index + i + 1] - 1 + index
                if id not in attrinfo:
                    # print('PROGRAM ERROR: ATTRIBUTE INDEX not found', id, 'Attribute pointer', iarray[index + i+1])
                    continue

                name, atype, length = attrinfo[id]
                if atype == 'I':
                    dattr[name] = iarray[ptr]
                elif atype == 'R':
                    dattr[name] = farray[ptr]
                else:
                    dattr[name] = ''.join([itostr(iarray[k]) for k in range(ptr, ptr + length//4)]).strip()

            # Get timeseries timebase data
            records = []
            for i in range(pdat+1, pdatv-1):
                a = iarray[index+i]
                if a != 0:
                    records.append(splitposition(a))
            if len(records) == 0:
                continue   # WDM preallocation, but nothing saved here yet

            srec, soffset = records[0]
            start = splitdate(iarray[srec*512 + soffset])

            sprec, spoffset = splitposition(frepos)
            finalindex = sprec * 512 + spoffset

            # calculate number of data points in each group, tindex is final index for storage
            tgroup = dattr['TGROUP']
            tstep  = dattr['TSSTEP']
            tcode  = dattr['TCODE']
            cindex = pd.date_range(start=start, periods=len(records)+1, freq=freq[tgroup])
            tindex = pd.date_range(start=start, end=cindex[-1], freq=str(tstep) + freq[tcode])
            counts = np.diff(np.searchsorted(tindex, cindex))

            ## Get timeseries data
            floats = np.zeros(sum(counts),  dtype=np.float32)
            findex = 0
            for (rec,offset),count in zip(records, counts):
                findex = getfloats(iarray, farray, floats, findex, rec, offset, count, finalindex, tcode, tstep)

            ## Write to HDF5 file
            series = pd.Series(floats[:findex], index=tindex[:findex])
            dsname = f'TIMESERIES/TS{dsn:03d}'
            # series.to_hdf(store, dsname, complib='blosc', complevel=9)
            if jupyterlab:
                series.to_hdf(store, dsname, complib='blosc', complevel=9)  # This is the official version
            else:
                series.to_hdf(store, dsname, format='t', data_columns=True)  # show the columns in HDFView

            data = [str(tindex[0]), str(tindex[-1]), str(tstep) + freq[tcode],
             len(series),  dattr['TSTYPE'], dattr['TFILL']]
            columns = ['Start', 'Stop', 'Freq','Length', 'TSTYPE', 'TFILL']
            # search = ['STAID', 'STNAM', 'SCENARIO', 'CONSTITUENT','LOCATION']
            for x in columns_to_add:
                if x in dattr:
                    data.append(dattr[x])
                    columns.append(x)

            summary.append(data)
            summaryindx.append(dsname[11:])


        dfsummary = pd.DataFrame(summary, index=summaryindx, columns=columns)
        store.put('TIMESERIES/SUMMARY',dfsummary, format='t', data_columns=True)
    return dfsummary


def todatetime(yr=1900, mo=1, dy=1, hr=0):
    '''takes yr,mo,dy,hr information then returns its datetime64'''
    if hr == 24:
        return datetime.datetime(yr, mo, dy, 23) + pd.Timedelta(1,'h')
    else:
        return datetime.datetime(yr, mo, dy, hr)

def splitdate(x):
    '''splits WDM int32 DATWRD into year, month, day, hour -> then returns its datetime64'''
    return todatetime(x >> 14, x >> 10 & 0xF, x >> 5 & 0x1F, x & 0x1F) # args: year, month, day, hour

def splitcontrol(x):
    ''' splits int32 into (qual, compcode, units, tstep, nvalues)'''
    return(x & 0x1F, x >> 5 & 0x3, x >> 7 & 0x7, x >> 10 & 0x3F, x >> 16)

def splitposition(x):
    ''' splits int32 into (record, offset), converting to Pyton zero based indexing'''
    return((x>>9) - 1, (x&0x1FF) - 1)

def itostr(i):
    return chr(i & 0xFF) + chr(i>>8 & 0xFF) + chr(i>>16 & 0xFF) + chr(i>>24 & 0xFF)

# @jit(nopython=True, cache=True)
def leap_year(y):
    if y % 400 == 0:
        return True
    if y % 100 == 0:
        return False
    if y % 4 == 0:
        return True
    else:
        return False

def getfloats(iarray, farray, floats, findex, rec, offset, count, finalindex, tcode, tstep):
    index = rec * 512 + offset + 1
    stop = (rec + 1) * 512
    cntr = 0
    while cntr < count and findex < len(floats):
        if index == stop -1 :
            print ('Problem?',str(rec)) #perhaps not, block cannot start at word 512 of a record because not spot for values
        if index >= stop-1:
            rec = iarray[rec * 512 + 3] - 1  # 3 is forward data pointer, -1 is python indexing
            print ('Process record ',str(rec))
            index = rec * 512 + 4  # 4 is index of start of new data
            stop = (rec + 1) * 512

        x = iarray[index]  # block control word or maybe date word at start of group
        nval = x >> 16
        ltstep = x >> 10 & 0x3f
        ltcode = x >> 7 & 0x7
        comp = x >> 5 & 0x3
        qual  = x & 0x1f
        ldate = todatetime() # dummy
        if ltstep != tstep or ltcode != tcode:
            nval = adjustNval(ldate, ltstep, tstep, ltcode, tcode, comp, nval)
            if nval == -1:  #unable to convert block
                try:
                    ldate = splitdate(x)
                    if isinstance(ldate,datetime.date):
                       print('Problem resolved - date found ',ldate)
                       nval = 1
                    else:
                        print('BlockConversionFailure at ', str(rec + 1), ' ', str(index % 512))
                except:
                  print ('BlockConversionFailure at ',str(rec+ 1),' ',str(index % 512))
                # try next word
                comp = -1
        index += 1
        if comp == 0:
            for k in range(nval):
                if findex >= len(floats):
                    return findex
                floats[findex] = farray[index + k]
                findex += 1
            index += nval
        elif comp > 0:
            for k in range(nval):
                if findex >= len(floats):
                    return findex
                floats[findex] = farray[index]
                findex += 1
            index += 1
        cntr += nval
    return findex

def adjustNval(ldate, ltstep, tstep, ltcode, tcode, comp, nval):
    lnval = nval
    if comp != 1:
        nval = -1  # only can adjust compressed data
    else:
        if tcode == 2:  # minutes
            if ltcode == 6:  # from years
                if leap_year(ldate.year):
                    ldays = 366
                else:
                    ldays = 365
                nval = ldays * lnval * 60 /ltstep
            elif ltcode == 5: # from months
                from calendar import monthrange
                ldateRange = monthrange(ldate.year, ldate.month)
                print ('month block ', ldateRange)
                nval = ldateRange[2] * lnval * 60/ ltstep
            elif ltcode == 4:  # from days
                nval = lnval * 60 / ltstep
            elif ltcode == 3:  # from hours
                nval = lnval * 1440 / ltstep
            else:  # dont know how to convert
                nval = -1
        elif tcode == 3:  # hours
            if ltcode == 6:  # from years
                nval = -1
            elif ltcode == 5: # from months
                nval = -1
            elif ltcode == 4:  # from days
                nval = lnval * 24 / ltstep
            else:  # dont know how to convert
                nval = -1
        else:
            nval = -1  # dont know how to convert

    nval = int(nval)
    if nval == -1:  # conversion problem
        print('Conversion problem (tcode ', str(tcode), ', ', str(ltcode), '), (tstep ', str(tstep), ',', str(ltstep), '), (comp ', str(comp), ')')
    else:
        print('Conversion complete (tcode ', str(tcode), ', ', str(ltcode), '), (tstep ', str(tstep), ',', str(ltstep), '), (nval ',
              str(nval) + ',', str(lnval), ')')

    return nval
