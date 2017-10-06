

#***************************************************************************#
##  Based on supersid_plot.py from https://github.com/ericgibert/supersid  ##
##                                                                         ##
##                  Adaptation by Alberto García Merino                    ##
##    GitHub: AlbertoGM97 - EMAIL: alberto.garciamerino97@gmail.com        ##
#***************************************************************************#


## TODO: Add sunrise and sunset dimm


import argparse, csv, time
from datetime import datetime, timezone, timedelta

import numpy as np
import matplotlib as mpl
from matplotlib.mlab import movavg

from matplotlib import dates
from datetime import datetime
import urllib

import sys

parser = argparse.ArgumentParser(description = 'usage: python3 sid_plot.py file1.csv file2.csv [Options]')
parser.add_argument('-f', '--filter', dest = 'filter',  help='Filter with moving avg',action='store_true')
parser.add_argument('-o', '--out',  dest = 'out_file', 
          help='Out img to file (default svg). For auto date name type -o %%. NOTE:-o option implies -n')
parser.add_argument('-p', '--png', dest = 'format_png',  help='Use png image format',  action='store_true')
parser.add_argument('-n', '--nodisp', dest = 'no_disp',  help='Dont output to screen', action='store_true')
parser.add_argument('-w', '--web',  dest = 'do_xra',   help='Add NOAA XRA events(Not implemented)', action='store_true')
parser.add_argument('-t', '--time',   dest = 'add_time', help='Add timestamp on image',action='store_true')

# TODO: Files with 0's are a problem
#parser.add_argument("-l", "--log",  dest = "do_log",   help="Log scale",       action="store_true")
(args, unk) = parser.parse_known_args()

if args.no_disp:
  mpl.use('Agg')          # Needed when using in no x-server environment
  print('[+] Quiet mode selected')

import matplotlib.pyplot as plt

#----------------------------------------------------------------------
filenames = unk
#----------------------------------------------------------------------

class sid_plot:
  
  def __init__(self, file_obj):

    self.call_sign   = 'None'
    self.start_date = '0000-00-00'
    self.loginterval = 1
    self.stations  = []
    self.frequencies = []

    [self.lat, self.lon] = [0.00, 0.00]  

    self.file_obj = file_obj

    self.obtain_csv_properties()

  def obtain_csv_properties(self):

    file_obj.seek(0, 0)                       # Let's go back to the start
    reader = csv.reader(self.file_obj, delimiter=',')
    count = 0

    for line in reader:
      if line[0][0] == '#':                   # Header lines start with '#'
        if line[0].find('Site') > 0:
          self.call_sign = line[0][line[0].find('=')+1:].replace(' ', '')
          print('[+] Call signg extracted from file ' + self.call_sign)

        if line[0].find('UTC_StartTime') > 0:
          self.start_date = line[0][18:]
          print('[+] Date extracted from file ' + self.start_date)
        
        if line[0].find('Longitude') > 0:
          self.lon = float(line[0][line[0].find('=')+1:].replace(' ', ''))
          print('[+] Longitude extracted from file ' , self.lon)

        if line[0].find('Latitude') > 0:
          self.lat = float(line[0][line[0].find('=')+1:].replace(' ', ''))
          print('[+] Latitude extracted from file ' , self.lat)

        if line[0].find('Stations') > 0:
          self.stations = ','.join(line)[line[0].find('=')+1:].replace(' ','').split(',')
          print('[+] Stations extracted from file ', self.stations)

        if line[0].find('Frequencies') > 0:
          self.frequencies = ','.join(line)[line[0].find('=')+1:].replace(' ','').split(',')
          print('[+] Frequencies extracted from file', self.frequencies)

        if line[0].find('LogInterval') > 0:
          self.loginterval = int(line[0][line[0].find('=')+1:].replace(' ', ''))
          print('[+] Log Interval extracted from file' , self.loginterval)
      else:
        if count > 3:
          break

      count = count+1
    
    file_obj.seek(0, 0)          
    return self.call_sign, self.stations, self.frequencies, self.start_date, self.lat, self.lon

  def csv_reader(self, file_obj, st_num):
    col = np.zeros(shape=(24*3600//self.loginterval, 1))
    reader = csv.reader(file_obj, delimiter=',')
    count = 0

    file_obj.seek(0, 0)                                      # Let's go back to the start
    for line in reader:
      if line[0][0] != '#':
        col[count] = line[st_num]
        count = count+1
        
    col.astype(np.float)
    return col

  def make_plot(self):
    fig, ax = plt.subplots()                                 # Only one subplot

    #------------------------------------------
    ax.set_axisbelow(True)                                   # Grid below data
    ax.minorticks_on()                                       # To enable minor grid
    ax.grid(which = 'major', linestyle="-.")                 # Major grid
    ax.grid(which='minor', linestyle='-.', linewidth='0.5')  # Minor grid

    y_unit = '(Nat)'
    #if args.do_log: y_unit = '(dB)'                         # FIX: 0 val files

    plt.ylabel('Rx power (relative)' +  y_unit)              # Label on rx axis
    plt.xlabel('UTC time')                                   # Label on time axis
    plt.title('UAH SID - 12/08/2017', fontsize=10)           # Title = Date + Name
    
    #------------------------------------------
    
    hours = dates.HourLocator(interval=3)#days = dates.DayLocator()
    dfmt = dates.DateFormatter('%H:%M')

    datemin = datetime(2017, 1, 1, 0, 0)
    datemax = datetime(2017, 1, 2, 0, 0)
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(dfmt)
    ax.set_xlim(datemin, datemax)

    if args.add_time:
      ax.text(0.1, 0.9, datetime.now(timezone.utc).strftime("%H:%M")+ ' UTC',
          verticalalignment='top', horizontalalignment='center',
          transform=ax.transAxes, color='k', fontsize=15,
          bbox=dict(fill=True, alpha=0.9, facecolor='w'))


    plt.axvspan(datemin, datemin+timedelta(hours = 5.5),  facecolor='k', alpha=0.1)   # Dim on night 00-06
    plt.axvspan(datemin+timedelta(hours = 22), datemax,   facecolor='k', alpha=0.1)   # Dim on night 22-24
    #------------------------------------------
    # if args.do_log: rcv = 20*np.log10(rcv)                  # FIX: 0 val files
    x_data = self._generate_timestamp()
    
    plot_axis = []
    [k, offset] = [0, 0]

    while k < len(self.stations):
      try:
        y_data = self.csv_reader(self.file_obj, k+offset)
        if args.filter: y_data = self.mov_avg(y_data, 6*2+1)  # Filter with moving average

      except:
        offset = 1          # Will fail for buffers with timestamp
        k = 0               # Offset is to skip one column
        continue

      new_a, = ax.plot(x_data, y_data, alpha = 0.8)
      plot_axis.append(new_a)
      k = k+1
    
    leg_list = []
    for i in range(0,len(self.stations)):
      leg_list.append(self.stations[i] + ' ('+ '%.2f' % (float(self.frequencies[i])/1000)+'kHz)')


    plt.legend(plot_axis, leg_list, loc='upper right', bbox_to_anchor=(1,1), fontsize = 9)       # Add legend to plot

    
    #------------------------------------------

    if args.do_xra:
      events_list = self.get_XRA()
      
      for event in events_list:
        x_start = datetime(2017,1,1,int(event['Begin'][0:2]), int(event['Begin'][2:4]))
        x_max   = datetime(2017,1,1,int(event['Max'][0:2]),   int(event['Max'][2:4]))
        x_end   = datetime(2017,1,1,int(event['End'][0:2]),   int(event['End'][2:4]))
        plt.axvline(x = x_start, color = 'g', alpha = 0.9, linestyle = ':')
        plt.axvline(x = x_max,   color = 'r', alpha = 0.9, linestyle = ':')
        plt.axvline(x = x_end,   color = 'y', alpha = 0.9, linestyle = ':')

        ax.text(x_max, 0, event['Particulars'], bbox={'facecolor':'white', 'alpha':0.5})

    #------------------------------------------

    if args.out_file:                                       # If argument was provided
      fig.set_size_inches(12, 7.5) # (18.5, 10.5)           # Set image size
      if args.out_file == '%':                              # If '%' was provided as argument:
        name = self.call_sign +'_'+ self.start_date[0: 10]  # Then use automatic name
      else:                                                 # If not:
        name = args.out_file                                # Use provided name

      img_format = 'svg'
      if args.format_png: img_format = 'png'
      plt.savefig( name+'.'+img_format, format=img_format, bbox_inches='tight', pad_inches=0.1) # For now only svg

    elif args.no_disp == False:                            # If neither out_file nor no_disp was provided
      plt.show()                                           # Show plot

  def mov_avg(self, array, window = 10):
    temp = np.zeros(len(array))
    temp_avg = 0
    for j in range(0,len(array)-window):
      for i in range(0,window):
        temp_avg = temp_avg+array[j+i]
      temp_avg = temp_avg/window
      temp[j] = temp_avg
      temp_avg = 0

    return temp
  
  def _generate_timestamp(self): # Function extracted from supersid_plot.py
    timestamp = np.empty(24*3600 // self.loginterval, dtype=datetime)
    interval =  timedelta(seconds= self.loginterval)
    currentTimestamp = datetime(2017,1,1,0,0,0)
    for i in range(len(timestamp)):
      timestamp[i] =  currentTimestamp
      currentTimestamp += interval
    return timestamp


  def get_XRA(self):                         # TODO
 
    day = self.start_date[0: 10].replace('-','')
    NOAA_URL = 'ftp://ftp.swpc.noaa.gov/pub/indices/events/%sevents.txt' % (day)
    resulttext = b''
    try:
      request = urllib.request.Request(NOAA_URL)
      result = urllib.request.urlopen(request)
      resulttext = result.read()

    except:
      print ("[E] In NOAA XRA service")

    XRA_fields = []
    XRA_list   = []

    resulttext = resulttext.decode('UTF-8').split('\n')
    for each_line in resulttext:
      if each_line.find('#Event') > -1:
        XRA_fields = sid_plot._list_replace(each_line.replace('#','').split('  '), ' ', '')

      if each_line.find('XRA') > -1:
        each_line = sid_plot._list_replace(each_line.replace('+','').split('  '), ' ', '')       # Double space

        temp_dic = {}
        for k in range(0,len(XRA_fields)): temp_dic[XRA_fields[k]] = each_line[k]
        XRA_list.append(temp_dic)

    return XRA_list

  def _list_replace(list, del_char, new_char):
    k = 0
    l = len(list)
    while k < l:
      list[k] = list[k].replace(del_char, new_char)
      if list[k] == '':
        list.pop(k)
        l -= 1
      else:k += 1

    return list

  '''def get_day_night(self):                      # TODO
    pass
  '''

#----------------------------------------------------------------------
if __name__ == "__main__":
  
  for each_file in filenames:
    with open(each_file, 'r') as file_obj:
      ssp = sid_plot(file_obj)
      ssp.make_plot()
