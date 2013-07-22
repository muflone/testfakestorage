#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
#       Project : testfakestorage
#       Version : 0.1.0
#   Description : A tool to test for fake storage like many cheap USB drives.
#        Author : Muflone <muflone@vbsimple.net>
#     Copyright : 2012 Fabio Castelli
#       License : GPL-2+
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation; either version 2 of the License, or (at your option)
#  any later version.
# 
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
##

APPNAME = 'testfakestorage'
VERSION = '0.1.0'

import argparse
import os.path

class ScanOptions(object):
  def __init__(self):
    parser = argparse.ArgumentParser(add_help=True,
      usage='%(prog)s [options] PATH',
      description='Create an index file of files or directories')
    parser.add_argument('path'             , action='store', type=str,
      help='Directory where to save test files')
    parser.add_argument('-V', '--version'  , action='version',
      help='Display the program version number and exit',
      version='%s %s' % (APPNAME, VERSION))

    group = parser.add_argument_group(title='Testing options')
    group.add_argument('-f', '--filename' , action='store', type=str,
      default='%s-' % APPNAME,
      help='Set the filename prefix for each file')
    group.add_argument('-b', '--block' , action='store', type=int, default=1024*1024,
      help='Set the block size to write')

    args = parser.parse_args()
    
    # Save the arguments
    self.path = args.path
    self.block_size = args.block
    self.filename = args.filename

class TestingPattern(object):
  def __init__(self, block_size):
    self.block_size = block_size
  def create(self, index):
    result = (str(index) * (self.block_size / len(str(index)) + 1))
    return result[:self.block_size]

class Scanner(object):
  def __init__(self, options):
    self.options = options
    
    for i in range(1, 11):
      fOutput = open(os.path.join(options.path, '%s%s' % (options.filename, str(i))), 'w')
      pattern = TestingPattern(options.block_size)
      fOutput.write(pattern.create(i))
      fOutput.close()

if __name__=='__main__':
  options = ScanOptions()
  print options.path
  print options.block_size
  print options.filename

  scanner = Scanner(options)
  
