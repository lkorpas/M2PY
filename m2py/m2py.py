# M2PY -- Python library used to control the Makergear M2 Pneumatic Control System [M2PCS]
# Developed in the Architected Materials Laboratory at the University of Pennsylvania
# Author: Matthew Sorna [sorna@seas.upenn.edu]

# Importing of necessary dependent modules
import os
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as mpatches

# Module Function Definitions

class Makergear:
    def __init__(self, com, baud, printout = 1):
        self.com = com
        self.baud = baud
        self.printout = printout
        self.fid = os.path.abspath('path_vis_temp.txt')
        self.channel_status = np.array([0,0,0])
        self.coords = np.array([0,0,0])
        self.current_tool = 1
        self.tool_coords = np.array([[0,0,0],[0,0,0],[0,0,0]])

        if self.printout == 1:
            self.handle = serial.Serial(com, baud, timeout = 1)
            time.sleep(2) # Make sure to give it enough time to initialize
            print('Serial port connected')
            for _ in range(21): # Reads in all 21 lines of initialization text for the M2
                self.handle.readline()
        elif self.printout == 0:
            self.coord_sys = 'abs'
            self.handle = open(self.fid, "w")

    def close(self):
        """
        Closes the specified handle. If self.printout = 1, this function will close the necessary serial object. If prinout = 0, this function will close the specified temporary file and plot a visualization of all relevant movement commands. Visualization function will use whatever coordinate system you explicity designate using coord. If coord isn't explicitly called, the coordinate system used by the visualization tool will be absolute.
        """
        if self.printout == 1:
            print("Serial port disconnected")
            self.handle.close()
        elif self.printout == 0:
            self.handle.close()
            self.path_vis()
            
    # GCode wrappers
    # G0/G1
    def move(self, x = 0, y = 0, z = 0, track = 1):
        """
        Moves to the specified point, keeping in mind the coordinate system (relative / absolute)
        """
        
        if self.coord_sys == 'abs':
            self.coords = np.array([x, y, z])
        elif self.coord_sys == 'rel':
            self.coords = self.coords + np.array([x, y, z])
        
        if self.printout == 1:
            self.handle.write(str.encode('G1 X{} Y{} Z{}\n'.format(x, y, z)))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            print('Move to ({}, {}, {})'.format(x, y, z))
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)

        elif self.printout == 0 and track == 1:
            self.handle.write('{} {} {} {} {} {}\n'.format(x, y, z, self.channel_status[0], self.channel_status[1], self.channel_status[2]))


    def speed(self, speed = 0):
        """
        Sets the movement speed of the printer to the specified speed in [mm/s] (default 0 mm/sec)
        """
        if self.printout == 1:
            self.handle.write(str.encode('G1 F{}\n'.format(speed*60)))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            print('Changing movement speed to {} mm/s'.format(speed))

    def rotate(self, speed = 0):
            """
            Sets the rotation speed of the motor to the specified speed [0-127] (default 0)
            """
            if self.printout == 1:
                self.handle.write(str.encode('M9 S{}\n'.format(int(speed))))
                read = self.handle.readline()
                while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                    read = self.handle.readline()
                    time.sleep(0.06)
                print('Changing rotation speed to {}'.format(int(speed)))

    def ramp(self, start = 0, stop = 0, seconds = 1):
            """
            Sets the rotation speed of the motor to the specified speed [0-127] (default 0 --> 0)
            """
            if self.printout == 1:
                diff = stop - start
                steps = abs(stop - start)
                if steps > 0:
                    for i in range(steps):
                        if diff > 0:
                            dt = seconds / steps
                            self.handle.write(str.encode('M9 S{}\n'.format(int(start + i))))
                            read = self.handle.readline()
                            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                                read = self.handle.readline()
                                time.sleep(0.06)
                        elif diff < 0:
                            dt = seconds / steps
                            self.handle.write(str.encode('M9 S{}\n'.format(int(start - i))))
                            read = self.handle.readline()
                            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                                read = self.handle.readline()
                                time.sleep(0.06)
                        
                        
                        self.handle.write(str.encode('G4 S{}\n'.format(dt)))
                        read = self.handle.readline()
                        while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                                read = self.handle.readline()
                                time.sleep(0.06)
                                
                print('Changing rotation from {} to {} in {} seconds'.format(int(start),int(stop), seconds))

    # G2/G3
    def arc(self, x = 0, y = 0, z = 0, i = 0, j = 0, direction = 'ccw'):
        """
        Moves to the specified x-y point, with the i-j point as the center of the arc, with direction specified as 'cw' or 'ccw' (default 'ccw')
        """
        if self.printout == 1:
            if direction == 'ccw':
                self.handle.write(str.encode('G3 X{} Y{} Z{} I{} J{}\n'.format(x, y, z, i, j)))
                read = self.handle.readline()
                while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                    read = self.handle.readline()
                    time.sleep(0.06)
                print('CCW arc to ({}, {}, {}), center at ({}, {})'.format(x, y, z, i, j))
            elif direction == 'cw':
                self.handle.write(str.encode('G2 X{} Y{} Z{} I{} J{}\n'.format(x, y, z, i, j)))
                read = self.handle.readline()
                while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                    read = self.handle.readline()
                    time.sleep(0.06)
                print('CW arc to ({}, {}, {}), center at ({}, {})'.format(x, y, z, i, j))

        elif self.printout == 0:
            self.handle.write('{} {} {}\n'.format(x, y, z))

    # G4
    def wait(self, seconds = 0):
        """
        Waits for the specified amount of time (default 0 seconds)
        """
        global pflag
        if pflag == 1:
            self.handle.write(str.encode('G4 S{}\n'.format(seconds)))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                    read = self.handle.readline()
                    time.sleep(0.06)
            print('Waiting for {} seconds'.format(seconds))

    # G28
    def home(self, axes = 'X Y Z'):
        """
        Homes the specified axes (default 'X Y Z')
        """
        split_axes = axes.split(' ')
        for i in range(len(split_axes)):
            if split_axes[i] == 'X':
                self.coords[0] = 0
            elif split_axes[i] == 'Y':
                self.coords[1] = 0
            elif split_axes[i] == 'Z':
                self.coords[2] = 0
        
        if self.printout == 1:
            self.handle.write(str.encode('G28 {}\n'.format(axes)))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                    read = self.handle.readline()
                    time.sleep(0.06)
            print('{} axes homed'.format(axes))

    # G90/G91
    def coord_sys(self, coord_sys = 'abs'):
        """
        Sets the coordinate system of the printer [relative or absolute] (default 'abs')
        """
        self.coord_sys = coord_sys

        if self.printout == 1:
            if self.coord_sys == 'abs':
                self.handle.write(str.encode('G90\n'))
                read = self.handle.readline()
                while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                    read = self.handle.readline()
                    time.sleep(0.06)
                print('Set to absolute coordinates')

            elif self.coord_sys == 'rel':
                self.handle.write(str.encode('G91\n'))
                read = self.handle.readline()
                while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                    read = self.handle.readline()
                    time.sleep(0.06)
                print('Set to relative coordinates')

    # G92
    def set_current_coords(self, x = 0, y = 0, z = 0):
        """
        Sets the current position to the specified (x, y, z) point (keeping in mind the current coordinate system)
        """
        
        self.coords = [x, y, z]
        
        if self.printout == 1:
            self.handle.write(str.encode('G92 X{} Y{} Z{}\n'.format(x, y, z)))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            print('Changed current position to ({}, {}, {})'.format(x, y, z))
    
    def return_current_coords(self):
        """
        Returns the current stored coordinates of the Makergear object
        """
        return self.coords

    # CORE SHELL SPECIFIC FUNCTIONS
    def allon(self):
        """
        Turns pneumatic CHANNEL 1, 2, 3 ON
        """
        if self.prinout == 1:
            self.handle.write(str.encode('M3\n'))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            self.handle.write(str.encode('M5\n'))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            self.handle.write(str.encode('M7\n'))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            print('All Channels ON')
        elif self.printout == 0:
            self.channel_status = np.array([1,1,1])

    def alloff(self):
        """
        Turns pneumatic CHANNEL 1, 2, 3 OFF
        """
        if self.printout == 1:
            self.handle.write(str.encode('M4\n'))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            self.handle.write(str.encode('M6\n'))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            self.handle.write(str.encode('M8\n'))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            print('All Channels OFF')
        elif self.printout == 0:
            self.channel_status = np.array([0,0,0])

    # M3/M5/M7
    def on(self, channel):
        """
        Turns pneumatic CHANNEL ON
        """
        if self.printout == 1:
            schannel = 'M{}\n'.format(channel*2 + 1)
            self.handle.write(str.encode(schannel))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            print('Channel {} ON'.format(channel))
        elif self.printout == 0:
            self.channel_status[channel - 1] = 1

    # M4/M6/M8
    def off(self, channel):
        """
        Turns pneumatic CHANNEL OFF
        """
        if self.printout == 1:
            schannel = 'M{}\n'.format(channel*2 + 2)
            self.handle.write(str.encode(schannel))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            print('Channel {} OFF'.format(channel))
        elif self.printout == 0:
            self.channel_status[channel - 1] = 0

    def set_channel_delay(self, delay = 50):
        """
        Sets the delay time (in ms) between a channel turning on and the execution of another command. Can be used to fine tune under extrusion effects, depending on ink viscosity.
        """
        if self.printout == 1:
            self.handle.write(str.encode('M50 S{}\n'.format(delay)))
            read = self.handle.readline()
            while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                read = self.handle.readline()
                time.sleep(0.06)
            print('Channel ON delay time changed to {} ms'.format(delay))
    
    def set_tool_coords(self, tool = 1, x = 0, y = 0, z = 0):
        """
        Sets internally stored coordinates of each tool, used in switching commands
        """
        self.tool_coords[tool - 1] = [x, y, z]
        

    def change_tool(self, change_to = 1):
        """
        This subroutine automatically swiches from the current to speicified tool
        """
        if self.printout == 1:
            self.alloff()
            old_coord_sys = self.coord_sys
            old_coords = self.coords
            self.coord_sys(coord_sys = 'rel')
            coord_change = self.tool_coords[change_to - 1] - self.tool_coords[self.current_tool - 1]
            self.move(x = coord_change[0], y = coord_change[1], z = coord_change[2])
            self.current_tool = change_to
            self.coord_sys(coord_sys = old_coord_sys)
            self.set_current_coords(x = old_coords[0], y = old_coords[1], z = old_coords[2])
            
            print('Changing to tool {}'.format(change_to))
            
    def path_vis(self):
        """
        Takes the (x, y, z) coordinates generated from mp.mopen(printout = 0), and plots them into a 3D line graph to check a print path before actually sending commands to the Makergear. Visualization function will use whatever coordinate system you explicity designate using coord. If coord isn't explicitly called, the coordinate system used by the visualization tool will be absolute. When using path_vis, the file directory of the path coordinates needs to be explicity set, unlike when it is implictly called inside mclose.
        """
        coord_array = np.zeros([1, 3])
        channel_array = np.zeros([1, 3])

        if self.coord_sys == 'abs':
            with open(self.fid, "r") as data:
                for line in data:
                    raw = line.split(' ')
                    coords = [float(raw[0]), float(raw[1]), float(raw[2])]
                    channels = [float(raw[3]), float(raw[4]), float(raw[5])]
                    coord_array = np.append(coord_array, [coords[0], coords[1], coords[2]])
                    channel_array = np.append(channel_array, [channels[0], channels[1], channels[2]])
            coord_array.shape = (int(len(coord_array)/3), 3)

        elif self.coord_sys == 'rel':
            old_coords = [0,0,0]
            with open(self.fid, "r") as data:
                for line in data:
                    raw = line.split(' ')
                    coords = [float(raw[0]), float(raw[1]), float(raw[2])]
                    channels = [float(raw[3]), float(raw[4]), float(raw[5])]
                    coord_array = np.append(coord_array, [coords[0] + old_coords[0], coords[1] + old_coords[1], coords[2] + old_coords[2]])
                    old_coords =  [coords[0] + old_coords[0], coords[1] + old_coords[1], coords[2] + old_coords[2]]
                    channel_array = np.append(channel_array, [channels[0], channels[1], channels[2]])
            coord_array.shape = (int(len(coord_array)/3), 3)
        
        channel_array.shape = (int(len(channel_array)/3), 3)
        num_moves = channel_array.shape[0]
        
        ch_split_index = np.array([])
        for i in range(num_moves-1):
            if np.array_equal(channel_array[i,:], channel_array[i+1,:]) == False:
                ch_split_index = np.append(ch_split_index, i+1)
                
        x_coord = coord_array[:,0]
        y_coord = coord_array[:,1]
        z_coord = coord_array[:,2]
        ch_split_index = ch_split_index.astype(int)
        
        x_split = np.split(x_coord, ch_split_index)
        y_split = np.split(y_coord, ch_split_index)
        z_split = np.split(z_coord, ch_split_index)
        ch_split = np.split(channel_array, ch_split_index)
        num_lines = len(x_split)
        
        for j in range(num_lines - 1):
            x_split[j+1] = np.insert(x_split[j+1], 0, x_split[j][-1])
            y_split[j+1] = np.insert(y_split[j+1], 0, y_split[j][-1])
            z_split[j+1] = np.insert(z_split[j+1], 0, z_split[j][-1])
            

        xmin = np.min(x_coord)
        xmax = np.max(x_coord)
        ymin = np.min(y_coord)
        ymax = np.max(y_coord)

        fig = plt.figure()
        ax = fig.gca(projection=Axes3D.name)
        ax.set_xlim3d(xmin, xmax)
        ax.set_ylim3d(ymin, ymax)
        ax.set_zlim3d(0, 203)
        ax.set_xlabel('X axis [mm]')
        ax.set_ylabel('Y axis [mm]')
        ax.set_zlabel('Z axis [mm]')
        
        for k in range(num_lines):
            
            if np.array_equal(ch_split[k][0], [0, 0, 0]):
                cstr = '#484848'
                linestyle = ':'
            elif np.array_equal(ch_split[k][0], [1, 0, 0]):
                cstr = '#0000ff'
                linestyle = '-'
            elif np.array_equal(ch_split[k][0], [0, 1, 0]):
                cstr = '#00ff00'
                linestyle = '-'
            elif np.array_equal(ch_split[k][0], [0, 0, 1]):
                cstr = '#ff0000'
                linestyle = '-'
                
            ax.plot(x_split[k], y_split[k], z_split[k], color = cstr, linewidth = 2, linestyle = linestyle)
        
        ch1_patch = mpatches.Patch(color='blue', label='Channel 1')
        ch2_patch = mpatches.Patch(color='green', label='Channel 2')
        ch3_patch = mpatches.Patch(color='red', label='Channel 3')
        plt.legend(handles=[ch1_patch, ch2_patch, ch3_patch], loc = 'best')
        plt.title('M2PCS Print Path Visualization')
        plt.show()

#Additional functions outside of the M2 CLASS
def prompt(com, baud):
    """
    Allows for quick, native GCode serial communication with the M2, provided that the proper com port and baud rate are selected, and match what is found in system settings. To exit the command prompt environment, just type exit in the IPython console.
    """
    escape = 0
    cmd = ''
    #Create and define serial port parameters
    handle = serial.Serial(com, baud, timeout = 0)
    time.sleep(2) # Make sure to give it enough time to initialize
    print("Enter a GCode command. To exit, type \'exit\'")
    handle.write(str.encode('M17\n'))
    x = y = z = 0
    xval = yval = zval = 0
    while escape == 0:
        cmd = input('>> ')
        if cmd == 'exit':
            handle.close()
            print("Serial port disconnected")
            escape = 1
        else:
            handle.write(str.encode('{}\n'.format(cmd)))
            if cmd =='G28':
                x = y = z = 0
                xval = yval = zval = 0
            cmd_split = cmd.split(' ')
            for a in cmd_split:
                xchar = a.split('X')
                ychar = a.split('Y')
                zchar = a.split('Z')
                if xchar[0] == '' and len(xchar) > 1 and xchar[1] != '':
                    xval = float(xchar[1])
                    x = x + xval
                if ychar[0] == '' and len(ychar) > 1 and ychar[1] != '':
                    yval = float(ychar[1])
                    y = y + yval
                if zchar[0] == '' and len(zchar) > 1 and zchar[1] != '':
                    zval = float(zchar[1])
                    z = z + zval
            print('Currently at ({}, {}, {})'.format(x, y, z))

def file_read(fid, com, baud):
    """
    Reads in a text file of GCode line by line, and waits for the M2 to acknowledge that it received the command before sending another, maintaining print accuracy.
    """
    #Create and define serial port parameters
    handle = serial.Serial(com, baud, timeout = 100)
    time.sleep(2) # Make sure to give it enough time to initialize

    print('Serial port initialized')
    for _ in range(21): # Reads in all 21 lines of initalization text for the M2
        handle.readline()
    print('Beginning print')
    with open(fid, "r") as gcode:
        for line in gcode:
            split_line = line.split(';') # chops off comments
            if split_line[0] != '':      # makes sure it's not a comment-only line of GCode
                handle.write(str.encode('{}\n'.format(split_line[0]))) #Reads in text file (GCode) line by line and sends commands to M2
                print(split_line[0])
                read = handle.readline()
                while read[0:2] != b'ok': #Waits for printer to send 'ok' command before sending the next command, ensuring print accuracy
                    read = handle.readline()

    print('Print complete!\nSerial port closed')
    handle.close() #Closes serial port