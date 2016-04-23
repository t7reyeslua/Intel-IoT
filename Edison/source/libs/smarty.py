#!/usr/bin/python
# Author: Zion Orent <zorent@ics.com>
# Copyright (c) 2015 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# import all libraries
import time, sys, signal, atexit
import pyupm_mma7660 as upmMMA7660
import pyupm_buzzer as upmBuzzer

# global defines
chords = [upmBuzzer.DO, upmBuzzer.RE, upmBuzzer.MI, upmBuzzer.FA,
          upmBuzzer.SOL, upmBuzzer.LA, upmBuzzer.SI, upmBuzzer.DO,
          upmBuzzer.SI, upmBuzzer.LA,upmBuzzer.SOL,
          upmBuzzer.FA, upmBuzzer.MI,upmBuzzer.RE, upmBuzzer.DO]

x = upmMMA7660.new_intp()
y = upmMMA7660.new_intp()
z = upmMMA7660.new_intp()
xyz_thresh = 1
SHAKE_THRESHOLD = 30

def config_buzzer():
    # Create the buzzer object using GPIO pin 5
    buzzer = upmBuzzer.Buzzer(5)
    buzzer.stopSound()
    buzzer.setVolume(0)
    return buzzer

def config_accelerometer():
    # Instantiate an MMA7660 on I2C bus 0
    myDigitalAccelerometer = upmMMA7660.MMA7660(
        upmMMA7660.MMA7660_I2C_BUS,
        upmMMA7660.MMA7660_DEFAULT_I2C_ADDR);


    # Register exit handlers
    atexit.register(exitHandler)
    signal.signal(signal.SIGINT, SIGINTHandler)


    # place device in standby mode so we can write registers
    myDigitalAccelerometer.setModeStandby()

    # enable 64 samples per second
    myDigitalAccelerometer.setSampleRate(upmMMA7660.MMA7660.AUTOSLEEP_64)

    # place device into active mode
    myDigitalAccelerometer.setModeActive()

    return myDigitalAccelerometer

## Exit handlers ##
# This function stops python from printing a stacktrace when you hit control-C
def SIGINTHandler(signum, frame):
    raise SystemExit

# This function lets you run code on exit, including functions from myDigitalAccelerometer
def exitHandler():
    print "Exiting"
    sys.exit(0)

#function which runs the main control loop
def run_control_loop():
    chord_ind = 0
    xyz_count = 0
    # check shake for 5 sec
    for shake_slot in range (0, 15):
        myDigitalAccelerometer.getRawValues(x, y, z)
        outputStr = ("Raw values: x = {0}"
                     " y = {1}"
                     " z = {2}").format(upmMMA7660.intp_value(x),
                                        upmMMA7660.intp_value(y),
                                        upmMMA7660.intp_value(z))
        if (abs(upmMMA7660.intp_value(x)) > SHAKE_THRESHOLD) or \
                (abs(upmMMA7660.intp_value(y)) > SHAKE_THRESHOLD) or \
                (abs(upmMMA7660.intp_value(z)) > SHAKE_THRESHOLD):
            print "value exceeded"
            print xyz_count
            xyz_count = xyz_count + 1
            if (xyz_count >= xyz_thresh):
                print "increasing thresh"
                for chord_ind in range (0,15):
                    print myBuzzer.playSound(chords[chord_ind], 100000)
                    print "buzzing"
                    #time.sleep(0.1)
                    #chord_ind = (chord_ind + 1) % 2
                    chord_ind += 1
                myBuzzer.stopSound()
                xyz_count = 0
                print outputStr
        print outputStr
        time.sleep(0.05)
    print "loop over"
    xyz_count = 0

###########################################
#instantiate all sensors
##########################################
# print "initializing the sensors"
# myBuzzer = config_buzzer()
# myDigitalAccelerometer = config_accelerometer()
#
# print "entering control loop"
# while (1):
#     run_control_loop()
#
# # Delete the buzzer object
# del myBuzzer
