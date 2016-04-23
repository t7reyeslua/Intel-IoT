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

bindings = [{'MAC': 123456, "ID": 1, "name": "shoe", "group": ["gym"]},{'MAC': 123456, "ID": 2, "name": "earplugs", "group": ["gym","work"]}, {'MAC': 123456, "ID": 3, "name": "keys", "group": ["gym", "work"]}, {'MAC': 123456, "ID": 4, "name": "laptop", "group": ["work"]}]

def update_display(scenario, ids_in_network):
	myLcd.setCursor(0,0)
	print "Scenario "+scenario
	print ids_in_network
	required_nodes = [x["ID"] for x in bindings if scenario in x["group"]]
	ids_not_in_network = [x for x in required_nodes if x not in ids_in_network]
	if(len(ids_not_in_network) == 0):
		print "All nodes in range"
		myLcd.setColor(0, 255, 0)
		myLcd.write('All set! Lets get going.')
	else:
		print "Missing nodes in range"
		print ids_not_in_network
		myLcd.setColor(255, 0, 0)
		missing_items = [x["name"] for x in bindings if x["ID"] in ids_not_in_network]
		myLcd.write('Missing '+" ".join(missing_items))

# RGB Red

if __name__ == "__main__":
	# Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS) 
	myLcd = lcd.Jhd1313m1(0, 0x3E, 0x62)
	print "LCD Display TEST"
	while(True):
		update_display("gym", [1,2])
		time.sleep(5)
		update_display("work", [4,2])
		time.sleep(5)
