#Copyright [2017] [Mauro Riva <lemariva@mail.com> <lemariva.com>]
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
#
#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.

import time
import math

try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

NTP_PACKET_FORMAT = "!12I"
NTP_DELTA = 3155673600  # 1970-01-01 00:00:00

DaysPer4Years = 365*4+1
EPOCH_DOW = 3
SECS_PER_DAY = 60*60*24

days = [[   0,  31,  60,  91, 121, 152, 182, 213, 244, 274, 305, 335],
        [ 366, 397, 425, 46, 486, 517, 547, 578, 609, 639, 670, 700],
        [ 731, 762, 790, 821, 851, 882, 912, 943, 974,1004,1035,1065],
        [1096,1127,1155,1186,1216,1247,1277,1308,1339,1369,1400,1430],
       ]

class RTC():
    def __init__(self):
        self.ntp_tmp = 0
        self.ntp_epoch = 0
        self.ntp_sync_clk = 0
        self.synced_ = False

    def synced(self):
        return self.synced_

    def epoch(self):
        return self.ntp_epoch

    def ntp_sync(self, ntp_server):
        try:
            NTP_QUERY = bytearray(48)
            NTP_QUERY[0] = 0x1b
            addr = socket.getaddrinfo(ntp_server, 123)[0][-1]
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
            del(s) #s.close()
            unpacked = struct.unpack(NTP_PACKET_FORMAT, msg[0:struct.calcsize(NTP_PACKET_FORMAT)])
            self.ntp_epoch = (unpacked[10] + float(unpacked[11]) / 2**32 - NTP_DELTA)
            self.ntp_sync_clk = time.time()
            self.synced_ = True
        except Exception as e:
            print("Something wrong with the ntp-server: " + str(e))
        return

    def now(self):
        tmp_epoch = self.ntp_epoch + (time.time() - self.ntp_sync_clk)
        tmp_gmtime = self.gmtime(tmp_epoch)
        return tmp_gmtime[:-1] + (0,) + ('None',)

    # year 2000-2099, no DST, no leap second, no timezone.
    # epoch = (((year/4*(365*4+1)+days[year%4][month]+day)*24+hour)*60+minute)*60+second;
    def gmtime(self, epoch = None):
        if not epoch:
            epoch = self.ntp_epoch
        epoch_tmp = epoch

        seconds = int(epoch%60)     # not working as espected... ;)
        epoch = epoch / 60
        minutes = int(epoch%60)
        epoch = epoch / 60
        hours = int(epoch%24)
        epoch = epoch / 24

        years = epoch/(DaysPer4Years)*4
        epoch = epoch%(DaysPer4Years)

        for year in range(2,-1,-1):
            if (epoch >= days[year][0]):
                break
        for month in range(11,-1,-1):
            if (epoch >= days[year][month]):
                break

        day = int(epoch - days[year][month]) + 1
        year = 2000 + int(years) + year - 1
        month = month + 1

        dow = math.ceil((epoch_tmp / (SECS_PER_DAY)) % 7 - EPOCH_DOW)
        #print("epoch:" + str(epoch_tmp) + "-> year: " + str(year) + " month: " + str(month) + " day: " + str(day) + " hour: " + str(hours) + " minutes: " + str(minutes) + " dow: " + str(dow))
        return (year, month, day, hours, minutes, seconds, dow)

    def formatdate(self, time_epoch = None):
        """Returns a date string as specified by RFC 2822, e.g.:
        Fri, 09 Nov 2001 01:08:47 GMT
        """
        # Note: we cannot use strftime() because that honors the locale and RFC
        # 2822 requires that day and month names be the English abbreviations.
        if(time_epoch == None):
            time_epoch = self.ntp_epoch + (time.time() - self.ntp_sync_clk)

        now = self.gmtime(time_epoch)
        zone = 'GMT'

        try:
            date_str = self._format_timetuple_and_zone(now, zone)
        except Exception as e:
            date_str = "none"
            print("Timeutils exception: " + str(e))
        return date_str

    def format_timetuple_and_zone(self, timetuple, zone):
        return '%s, %02d %s %04d %02d:%02d:%02d %s' % (
            ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][timetuple[6]],
            timetuple[2],
            ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][timetuple[1] - 1],
            timetuple[0], timetuple[3], timetuple[4], timetuple[5],
            zone)
