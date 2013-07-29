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
VERSION = '0.2.0'
ERROR_DISK_FULL = 28
KILOBYTE = 1000
MEGABYTE = KILOBYTE * KILOBYTE
GIGABYTE = KILOBYTE * MEGABYTE

import argparse
import os
import os.path

class ScanOptions(object):
  def __init__(self):
    parser = argparse.ArgumentParser(add_help=True,
      usage='%(prog)s [options] PATH',
      description='Create an index file of files or directories')
    parser.add_argument('path', action='store', type=str,
      help='Directory where to save test files')
    parser.add_argument('-V', '--version'  , action='version',
      help='Display the program version number and exit',
      version='%s %s' % (APPNAME, VERSION))

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-w', '--writeonly' , action='store_true', 
      default=False,
      help='Writes only the data without testing them')
    group.add_argument('-c', '--checkonly' , action='store_true', 
      default=False,
      help='Checks only the data without testing them')

    group = parser.add_argument_group(title='Testing options')
    group.add_argument('-f', '--filename' , action='store', type=str,
      default='%s-' % APPNAME,
      help='Set the filename prefix for each file')
    group.add_argument('-l', '--length' , action='store', type=int,
      default=GIGABYTE,
      help='Set the maximum file size')
    group.add_argument('-b', '--block' , action='store', type=int, default=MEGABYTE,
      help='Set the block size to write')
    group.add_argument('-m', '--maxfiles' , action='store', type=int,
      default=0,
      help='Set the maximum number of files where 0 means until the disk is full')

    args = parser.parse_args()
    
    # Save the arguments
    self.path = args.path
    self.block_size = args.block
    self.filename = args.filename
    self.length = args.length
    self.max_files = args.maxfiles
    self.writeonly = args.writeonly
    self.checkonly = args.checkonly

class PatternGenerator(object):
  def __init__(self, block_size):
    self.block_size = block_size
  def create(self, index):
    return None

class PatternGeneratorIndexed(PatternGenerator):
  def __init__(self, block_size):
    PatternGenerator.__init__(self, block_size)
  def create(self, index):
    return (str(index) * (self.block_size / len(str(index)) + 1))[:self.block_size]

class Scanner(object):
  def __init__(self, options, generator):
    self.options = options
    self.generator = generator
    self.iTestFiles = 0
    self.lost_bytes = 0
    self.damaged_files = 0
    self.lost_files = 0

  def write(self):
    write_error = False
    while not write_error and \
      (self.iTestFiles < self.options.max_files or self.options.max_files <= 0):
      self.iTestFiles += 1
      real_filename = '%s%s' % (options.filename, str(self.iTestFiles))
      try:
        try:
          # Create the output file
          fOutput = open(os.path.join(options.path, real_filename), 'w')
          # Fill the file in multiple writes
          file_length = 0
          while file_length < options.length:
            # Write test data in output file
            write_pattern = self.generator.create(self.iTestFiles)
            fOutput.write(write_pattern)
            file_length += len(write_pattern)
        except IOError, error:
          # Handle disk full exception
          if error.errno != ERROR_DISK_FULL:
            # This is an unexpected exception, it should be handled in some way
            print 'There was an unexpected error during the write of a test'
          write_error = True
        finally:
          # Close output file
          fOutput.close()
      except IOError, error:
        # Unable to close the file, abort
        write_error = True

  def verify(self):
    for iVerification in xrange(1, self.iTestFiles + 1):
      real_filename = '%s%s' % (options.filename, str(iVerification))
      damaged_data = 0
      try:
        # Open the input file
        fInput = open(os.path.join(options.path, real_filename), 'rb')
        iBlockNr = 0
        while True:
          iBlockNr += 1
          # Read test data from the input file
          sInput = fInput.read(options.block_size)
          #print 'readed a block of %d bytes' % len(sInput)
          if len(sInput) == 0:
            break

          # Create another pattern for verification
          sVerification = self.generator.create(iVerification)

          # The two strings differ in length      
          if len(sInput) != len(sVerification):
            # Is it the last partial block?
            if iVerification == self.iTestFiles:
              # The last pattern needs to be cut to the exact size before to check
              sVerification = sVerification[:len(sInput)]
            else:
              print 'wrong length %d %d' % (len(sInput), len(sVerification))
              damaged_data += options.block_size
      
          # Are the two strings equal?
          if sInput != sVerification:
            print 'There was an error during the verification for the file # %d while checking the block %d at position %d' % \
              (iVerification, iBlockNr, iBlockNr * options.block_size)
            damaged_data += options.block_size
        # Close input file at the end
        fInput.close()
      except IOError, error:
        print 'The file # %d is missing, the whole test data are lost' % iVerification
        self.lost_files += 1
      if damaged_data > 0:
        self.damaged_files += 1
        self.lost_bytes += damaged_data

  def result(self):
    if self.damaged_files > 0:
      print '%d files were damaged' % self.damaged_files
    if self.lost_files > 0:
      print '%d files were lost for a total of %d bytes' % (self.lost_files, self.lost_files * self.options.length)
    if self.lost_bytes + self.lost_files > 0:
      print 'There was a data loss of %d bytes' % (self.lost_bytes + self.lost_files * self.options.length)

if __name__=='__main__':
  options = ScanOptions()
  generator = PatternGeneratorIndexed(options.block_size)
  scanner = Scanner(options, generator)
  if not options.checkonly:
    print 'write'
    # TODO: implement a pause/stop/continue feature
    scanner.write()
  else:
    # Detect which files are present before to check if not writing
    for sFileName in os.listdir(options.path):
      sSuffix = sFileName[len(options.filename):]
      if sFileName.startswith(options.filename) and sSuffix.isdigit():
        # The file names on the disk are not sorted, find the last number
        if scanner.iTestFiles < int(sSuffix):
          scanner.iTestFiles = int(sSuffix)

  if not options.writeonly:
    print 'verify'
    scanner.verify()
    scanner.result()
