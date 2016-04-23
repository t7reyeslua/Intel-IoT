#!/usr/bin/python
# Author: Brendan Le Foll <brendan.le.foll@intel.com>
# Copyright (c) 2014 Intel Corporation.
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

import pyupm_i2clcd as lcd
import time

bindings = [{'MAC': 123456, "ID": 1, "name": "shoe", "group": ["gym"]},
            {'MAC': 123456, "ID": 2, "name": "earplugs", "group": ["gym","work"]},
            {'MAC': 123456, "ID": 3, "name": "keys", "group": ["gym", "work"]},
            {'MAC': 123456, "ID": 4, "name": "laptop", "group": ["work"]}]

def clear_display(myLcd):
    myLcd.setColor(0, 0, 0)
    myLcd.setCursor(0,0)
    myLcd.write('                       ')
    myLcd.setCursor(1,0)
    myLcd.write('                       ')

def print_display(myLcd, line1, line2, is_error):
    print(myLcd)
    print(line1)
    print(line2)
    print(is_error)
    if is_error == True:
        myLcd.setColor(255, 0, 0)
    else:
        myLcd.setColor(0, 255, 0)

    clear_display(myLcd)
    myLcd.setCursor(0,0)
    myLcd.write(line1)
    myLcd.setCursor(1,0)
    myLcd.write(line2)

def update_display(scenario, ids_in_network):
    print "Scenario "+scenario
    print ids_in_network
    required_nodes = [x["ID"] for x in bindings if scenario in x["group"]]
    ids_not_in_network = [x for x in required_nodes if x not in ids_in_network]
    if(len(ids_not_in_network) == 0):
        print "All nodes in range"
        clear_display()
        myLcd.setColor(0, 255, 0)
        myLcd.setCursor(0,0)
        myLcd.write('All set!')
        myLcd.setCursor(1,0)
        myLcd.write('Lets get going.')
    else:
        print "Missing nodes in range"
        print ids_not_in_network
        clear_display()
        myLcd.setColor(255, 0, 0)
        missing_items = [x["name"] for x in bindings if x["ID"] in ids_not_in_network]
        myLcd.setCursor(0,0)
        myLcd.write('Did you forget ')
        myLcd.setCursor(1,0)
        myLcd.write(" ".join(missing_items))

# RGB Red

def config_lcd():
    tlcd = lcd.Jhd1313m1(0, 0x3E, 0x62)
    return tlcd

# if __name__ == "__main__":
#     myLcd = config_lcd()
#     # Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
#     print "LCD Display TEST"
#     update_display("work", [1,2,3,4])
#     time.sleep(2)
#     update_display("work", [1,2])
#     time.sleep(2)
#     update_display("gym", [1,2])
#     time.sleep(2)
#     update_display("gym", [1,2,3,4])
#     time.sleep(2)
#     clear_display()
#     time.sleep(2)
