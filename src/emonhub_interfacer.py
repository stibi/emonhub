"""

  This code is released under the GNU Affero General Public License.
  
  OpenEnergyMonitor project:
  http://openenergymonitor.org

"""

import serial
import time
import datetime
import logging
import socket
import select

import emonhub_coder as ehc

"""class EmonHubInterfacer

Monitors a data source. 

This almost empty class is meant to be inherited by subclasses specific to
their data source.

"""


class EmonHubInterfacer(object):

    def __init__(self):
        
        # Initialize logger
        self._log = logging.getLogger("EmonHub")

        # Initialise settings
        self.name = ''
        self.init_settings = {}
        self._defaults = {'pause': 'off', 'interval': 0, 'datacode': 0}
        self._settings = {}
        self._packet_counter = 0

        # This line will stop the default values printing to logfile at start-up
        # unless they have been overwritten by emonhub.conf entries
        # comment out if diagnosing a startup value issue
        self._settings.update(self._defaults)

        # Initialize interval timer's "started at" timestamp
        self._interval_timestamp = 0
        
    def close(self):
        """Close socket."""
        pass

    def read(self):
        """Read data from socket and process if complete line received.

        Return data as a list: [NodeID, val1, val2]
        
        """
        pass

    def _process_frame(self, frame, timestamp=0.0):
        """Process a frame of data

        f (string): 'NodeID val1 val2 ...'

        This function splits the string into numbers and check its validity.

        'NodeID val1 val2 ...' is the generic data format. If the source uses 
        a different format, override this method.
        
        Return data as a list: [NodeID, val1, val2]

        """

        # Discard the frame if 'pause' set to 'all' or 'in'
        if 'pause' in self._settings and \
                        str.lower(self._settings['pause']) in ['all', 'in']:
            return

        # Add timestamp if not done already

        if not timestamp:
            timestamp = round(time.time(), 2)

        # Assign a "Packet" reference number
        self._packet_counter +=1
        ref = self._packet_counter

        # Log data
        self._log.debug(str(ref) + " NEW FRAME : " + str(timestamp) + " " + frame)
        
        # Get an array out of the space separated string
        frame = frame.strip().split(' ')

        # create a RSSI variable
        self.rssi = False

        # Validate frame
        validated = self._validate_frame(ref, frame)
        if not validated:
            #self._log.debug('Discard RX Frame "Failed validation"')
            return
        else:
            frame = self._decode_frame(ref, validated)

        if frame:
            self._log.debug(str(ref) + " Timestamp : " + str(timestamp))
            self._log.debug(str(ref) + "      Node : " + str(frame[0]))
            self._log.debug(str(ref) + "    Values : " + str(frame[1:]))
            frame = [timestamp] + frame
            # Append RSSI only if value is not 'False'
            if self.rssi:
                self._log.debug(str(ref) + "      RSSI : " + str(self.rssi))
                frame += [self.rssi]
            frame += [ref]
        else:
            return

        # pause output if 'pause' set to 'all' or 'out'
        if 'pause' in self._settings \
                and str(self._settings['pause']).lower() in ['all', 'out']:
            return
        
        return frame

    def _validate_frame(self, ref, received):
        """Validate a frame of data

        This function performs logical tests to filter unsuitable data.
        Each test discards frame with a log entry if False

        Returns True if data frame passes tests.

        """
        
        # Discard if frame not of the form [node, val1, ...]
        # with number of elements at least 2
        if len(received) < 2:
            self._log.warning(str(ref) + " Discarded RX frame 'string too short' : " + str(received))
            return False

        # Discard if anything non-numerical found
        try:
            [float(val) for val in received]
        except Exception:
            self._log.warning(str(ref) + " Discarded RX frame 'non-numerical content' : " + str(received))
            return False

        # If it passes all the checks return
        return received

    def _decode_frame(self, ref, data):
        """Decodes a frame of data

        Performs decoding of data types

        Returns decoded string of data.

        """

        node = data[0]
        data = data[1:]
        decoded = []

        # check if node is listed and has individual datacodes for each value
        if node in ehc.nodelist and 'datacodes' in ehc.nodelist[node]:
            # fetch the string of datacodes
            datacodes = ehc.nodelist[node]['datacodes']
            # fetch a string of data sizes based on the string of datacodes
            datasizes = []
            for code in datacodes:
                datasizes.append(ehc.check_datacode(code))
            # Discard the frame & return 'False' if it doesn't match the summed datasizes
            if len(data) != sum(datasizes):
                self._log.warning(str(ref) + " RX data length: " + str(len(data)) +
                                  " is not valid for datacodes " + str(datacodes))
                return False
            else:
                # Determine the expected number of values to be decoded
                count = len(datacodes)
                # Set decoder to "Per value" decoding using datacode 'False' as flag
                datacode = False
        else:
            # if node is listed, but has only a single default datacode for all values
            if node in ehc.nodelist and 'datacode' in ehc.nodelist[node]:
                datacode = ehc.nodelist[node]['datacode']
            else:
            # when node not listed or has no datacode(s) use the interfacers default if specified
                datacode = self._settings['datacode']
            # when no (default)datacode(s) specified, pass string values back as numerical values
            if not datacode:
                for val in data:
                    if float(val) % 1 != 0:
                        val = float(val)
                    else:
                        val = int(float(val))
                    decoded.append(val)
            # Discard frame if total size is not an exact multiple of the specified datacode size.
            elif len(data) % ehc.check_datacode(datacode) != 0:
                self._log.warning(str(ref) + " RX data length: " + str(len(data)) +
                                  " is not valid for datacode " + str(datacode))
                return False
            else:
            # Determine the number of values in the frame of the specified code & size
                count = len(data) / ehc.check_datacode(datacode)

        # Decode the string of data one value at a time into "decoded"
        if not decoded:
            bytepos = int(0)
            for i in range(0, count, 1):
                # Use single datacode unless datacode = False then use datacodes
                dc = datacode
                if not datacode:
                    dc = datacodes[i]
                # Determine the number of bytes to use for each value by it's datacode
                size = int(ehc.check_datacode(dc))
                try:
                    value = ehc.decode(dc, [int(v) for v in data[bytepos:bytepos+size]])
                except:
                    self._log.warning(str(ref) + " Unable to decode as values incorrect for datacode(s)")
                    return False
                bytepos += size
                decoded.append(value)

        # Insert node ID before data
        decoded.insert(0, int(node))
        return decoded
    
    def set(self, **kwargs):
        """Set configuration parameters.

        **kwargs (dict): settings to be sent. Example:
        {'setting_1': 'value_1', 'setting_2': 'value_2'}

        pause (string): pause status
            'pause' = all  pause Interfacer fully, nothing read, processed or posted.
            'pause' = in   pauses the input only, no input read performed
            'pause' = out  pauses output only, input is read, processed but not posted to buffer
            'pause' = off  pause is off and Interfacer is fully operational (default)
        
        """

        for key, setting in self._defaults.iteritems():
            if not key in kwargs.keys():
                setting = self._defaults[key]
            else:
                setting = kwargs[key]
            if key in self._settings and self._settings[key] == setting:
                pass
            elif key == 'pause' and not str(setting).lower() in ['all', 'in', 'out', 'off']:
                self._log.warning("'%s' is not a valid setting for %s: %s" % (setting, self.name, key))
                pass
            else:
                self._settings[key] = setting
                self._log.debug("Setting " + self.name + " " + key + ": " + str(setting))

    def run(self):
        """Placeholder for background tasks. 
        
        Allows subclasses to specify actions that need to be done on a 
        regular basis. This should be called in main loop by instantiater.
        
        """
        pass

    def _open_serial_port(self, com_port, com_baud):
        """Open serial port

        com_port (string): path to COM port

        """
        
        self._log.debug('Opening serial port: %s', com_port)
        
        if not int(com_baud) in [75, 110, 300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]:
            self._log.debug("Invalid 'com_baud': " + str(com_baud) + " | Default of 9600 used")
            com_baud = 9600

        try:
            s = serial.Serial(com_port, com_baud, timeout=0)
            self._log.info("Opened serial port: " + str(com_port) + " "+ str(com_baud) + " bits/s")
        except serial.SerialException as e:
            self._log.error(e)
            raise EmonHubInterfacerInitError('Could not open COM port %s' %
                                           com_port)
        else:
            return s
    
    def _open_socket(self, port_nb):
        """Open a socket

        port_nb (string): port number on which to open the socket

        """

        self._log.debug('Opening socket on port %s', port_nb)
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', int(port_nb)))
            s.listen(1)
        except socket.error as e:
            self._log.error(e)
            raise EmonHubInterfacerInitError('Could not open port %s' %
                                           port_nb)
        else:
            return s

"""class EmonhubSerialInterfacer

Monitors the serial port for data

"""


class EmonHubSerialInterfacer(EmonHubInterfacer):

    def __init__(self, com_port='', com_baud=9600):
        """Initialize interfacer

        com_port (string): path to COM port

        """
        
        # Initialization
        super(EmonHubSerialInterfacer, self).__init__()

        # Open serial port
        self._ser = self._open_serial_port(com_port, com_baud)
        
        # Initialize RX buffer
        self._rx_buf = ''

    def close(self):
        """Close serial port"""
        
        # Close serial port
        if self._ser is not None:
            self._log.debug("Closing serial port")
            self._ser.close()

    def read(self):
        """Read data from serial port and process if complete line received.

        Return data as a list: [NodeID, val1, val2]
        
        """

        # Read serial RX
        self._rx_buf = self._rx_buf + self._ser.readline()
        
        # If line incomplete, exit
        if '\r\n' not in self._rx_buf:
            return

        # Remove CR,LF
        f = self._rx_buf[:-2]

        # Reset buffer
        self._rx_buf = ''

        # unix timestamp
        t = round(time.time(), 2)

        # Process data frame
        return self._process_frame(f, t)

"""class EmonHubJeeInterfacer

Monitors the serial port for data from "Jee" type device

"""


class EmonHubJeeInterfacer(EmonHubSerialInterfacer):

    def __init__(self, com_port='/dev/ttyAMA0', com_baud=9600):
        """Initialize Interfacer

        com_port (string): path to COM port

        """
        
        # Initialization
        super(EmonHubJeeInterfacer, self).__init__(com_port, com_baud)

        # Initialize settings
        self._defaults.update({'pause': 'off', 'interval': 0, 'datacode': 'h', 'quiet': 'True'})
        self._settings.update({'baseid': '', 'frequency': '', 'group': ''})

        # This line will stop the default values printing to logfile at start-up
        # unless they have been overwritten by emonhub.conf entries
        # comment out if diagnosing a startup value issue
        self._settings.update(self._defaults)

    def _validate_frame(self, ref, received):
        """Validate a frame of data

        This function performs logical tests to filter unsuitable data.
        Each test discards frame with a log entry if False

        Returns True if data frame passes tests.

        """

        # Discard information messages
        if (received[0] == '>') or (received[0] == '->'):
            self._log.warning(str(ref) + " Discard RX frame 'information' : " + str(received))
            return False
            
        if received[0] == '\x01':
            self._log.info(str(ref) + " Ignoring frame consisting of SOH character")
            return False

        if received[0] == '?'and str(received[-1])[0]=='(' and str(received[-1])[-1]==')':
            self._log.info(str(ref) + " Discard RX frame 'unreliable content' : RSSI " + str(received[-1]))
            return False

        # Strip 'OK' and extract RSSI if packet is from RFM69 type Jee Device
        if received[0]=='OK' and str(received[-1])[0]=='(' and str(received[-1])[-1]==')':
            self.rssi = int(received[-1][1:-1])
            received = received[1:-1]
            return received
        else:
            # set RSSI false for standard frames so RSSI is not re-appended later
            self.rssi = False

        # include checks from parent
        if not super(EmonHubJeeInterfacer, self)._validate_frame(ref, received):
            return False

        return received

    def set(self, **kwargs):
        """Send configuration parameters to the "Jee" type device through COM port

        **kwargs (dict): settings to be modified. Available settings are
        'baseid', 'frequency', 'group'. Example:
        {'baseid': '15', 'frequency': '4', 'group': '210'}
        
        """

        for key, value in kwargs.iteritems():
            # If radio setting modified, transmit on serial link
            if key in ['baseid', 'frequency', 'group', 'quiet']:
                if value != self._settings[key]:
                    if key == 'baseid' and int(value) >=1 and int(value) <=26:
                        string = value + 'i'
                    elif key == 'frequency' and value in {'433','868','915'}:
                        string = value[:1] + 'b'
                    elif key == 'group'and int(value) >=0 and int(value) <=212:
                        string = value + 'g'
                    #elif key == 'quiet' and str.capitalize(value) in {'True', 'False'}:
                        #string = str(int(bool(str.capitalize(value)))) + 'q'
                    elif key == 'quiet' and str.lower(value) in {'true', 'false'}:
                        if str.lower(value) == 'true':
                            string = '1q'
                        else:
                            string = '0q'
                    else:
                        self._log.warning("'%s' is not a valid setting for %s: %s" % (value, self.name, key))
                        continue
                    self._settings[key] = value
                    self._log.debug("Setting " + self.name + " %s: %s" % (key, value) + " (" + string + ")")
                    self._ser.write(string)
                    # Wait a sec between two settings
                    time.sleep(1)

        # include kwargs from parent
        super(EmonHubJeeInterfacer, self).set(**kwargs)

    def run(self):
        """Actions that need to be done on a regular basis. 
        
        This should be called in main loop by instantiater.
        
        """

        now = time.time()

        # Broadcast time to synchronize emonGLCD
        interval = int(self._settings['interval'])
        if interval:  # A value of 0 means don't do anything
            if now - self._interval_timestamp > interval:
                self._send_time()
                self._interval_timestamp = now
    
    def _send_time(self):
        """Send time over radio link to synchronize emonGLCD

        The radio module can be used to broadcast time, which is useful
        to synchronize emonGLCD in particular.
        Beware, this is know to garble the serial link on RFM2Piv1
        sendtimeinterval defines the interval in seconds between two time
        broadcasts. 0 means never.

        """

        now = datetime.datetime.now()

        self._log.debug(self.name + " broadcasting time: %02d:%02d" % (now.hour, now.minute))

        self._ser.write("00,%02d,%02d,00,s" % (now.hour, now.minute))

"""class EmonHubSocketInterfacer

Monitors a socket for data, typically from ethernet link

"""


class EmonHubSocketInterfacer(EmonHubInterfacer):

    def __init__(self, port_nb=50011):
        """Initialize Interfacer

        port_nb (string): port number on which to open the socket

        """
 
        # Initialization
        super(EmonHubSocketInterfacer, self).__init__()

        # Open socket
        self._socket = self._open_socket(port_nb)

        # Initialize RX buffer for socket
        self._sock_rx_buf = ''

    def close(self):
        """Close socket."""
        
        # Close socket
        if self._socket is not None:
            self._log.debug('Closing socket')
            self._socket.close()

    def read(self):
        """Read data from socket and process if complete line received.

        Return data as a list: [NodeID, val1, val2]
        
        """
        
        # Check if data received
        ready_to_read, ready_to_write, in_error = \
            select.select([self._socket], [], [], 0)

        # If data received, add it to socket RX buffer
        if self._socket in ready_to_read:

            # Accept connection
            conn, addr = self._socket.accept()
            
            # Read data
            self._sock_rx_buf = self._sock_rx_buf + conn.recv(1024)
            
            # Close connection
            conn.close()

        # If there is at least one complete frame in the buffer
        if '\r\n' in self._sock_rx_buf:
            # Process and return first frame in buffer:
            f, self._sock_rx_buf = self._sock_rx_buf.split('\r\n', 1)
            return self._process_frame(f)

"""class EmonHubInterfacerInitError

Raise this when init fails.

"""


class EmonHubInterfacerInitError(Exception):
    pass
