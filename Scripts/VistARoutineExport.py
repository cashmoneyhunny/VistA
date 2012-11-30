#!/usr/bin/env python
#---------------------------------------------------------------------------
# Copyright 2012 The Open Source Electronic Health Record Agent
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#---------------------------------------------------------------------------

from __future__ import with_statement
import sys
import os
import re
import argparse
from VistATestClient import VistATestClientFactory, createTestClientArgParser

class VistARoutineExport(object):
  """ regular expression constants """
  REGEX_ROUTINES = re.compile("Routine(\(s\))?: ")
  def __init__(self):
    pass
  def __setupOutputInfoCache__(self, connection, outputFileName):
    connection.expect("Description:", 360)
    connection.send("\r")
    connection.expect("Device: ")
    nativeName = os.path.normpath(outputFileName)
    connection.send("%s\r" % nativeName)
    """ this could be system dependent format """
    selectionList = ["Parameters\? \"WNS\" =>",
                     "exists, do you want to overwrite it\? [ \r\n]*Yes =>",
                     "Printer Format\? No =>"]
    while True:
      index = connection.expect(selectionList)
      connection.send("\r")
      if index == len(selectionList) - 1:
        break

  def __setupOutputInfoGTM__(self, connection, outputFileName):
    connection.expect("Output device: ", 360)
    nativeName = os.path.normpath(outputFileName)
    connection.send("%s\r" % nativeName)
    connection.expect("Header Label: ")
    connection.send("\r")
    connection.expect("Strip comments ")
    connection.send("No\r")

  def __exportRoutineImpl__(self, vistATestClient, outputFileName,
                            routineList, excludeList=None,
                            allRoutines=False):
    vistATestClient.waitForPrompt()
    connection = vistATestClient.getConnection()
    connection.send("D ^%RO\r")
    if allRoutines:
      connection.expect(self.REGEX_ROUTINES)
      connection.send("*\r")
    else:
      for routine in routineList:
        connection.expect(self.REGEX_ROUTINES)
        connection.send("%s\r" % routine)
    if excludeList:
      for routine in excludeList:
        connection.expect(self.REGEX_ROUTINES)
        connection.send("'%s\r" % routine)
    connection.expect(self.REGEX_ROUTINES, 360)
    connection.send("\r")
    if vistATestClient.isCache():
      self.__setupOutputInfoCache__(connection, outputFileName)
    else:
      self.__setupOutputInfoGTM__(connection, outputFileName)
    vistATestClient.waitForPrompt(1200)
    connection.send('\r')
  def exportRoutines(self, vistATestClient,
                     outputFileName, routineList, excludeList=None):
    if not routineList:
      return True
    return self.__exportRoutineImpl__(vistATestClient,
                                      outputFileName,
                                      routineList,
                                      excludeList)
  def exportAllRoutines(self, vistATestClient, outputFileName, excludeList=None):
    return self.__exportRoutineImpl__(vistATestClient,
                                      outputFileName,
                                      None,
                                      excludeList,
                                      True)

DEFAULT_OUTPUT_LOG_FILE_NAME = "RoutineExportTest.log"
import tempfile
def getTempLogFile():
    return os.path.join(tempfile.gettempdir(), DEFAULT_OUTPUT_LOG_FILE_NAME)
def main():
  testClientParser = createTestClientArgParser()
  parser = argparse.ArgumentParser(description='VistA Routine Export',
                                   parents=[testClientParser])
  parser.add_argument('-o', '--outputFile',
                    help='Output File Name to store routine export information')
  parser.add_argument('-a', '--allRoutines', action="store_true", default=False,
                      help='export all routines')
  parser.add_argument('-r', '--routines', nargs='*',
                      help='only specified routine names')
  parser.add_argument('-e', '--exclude', nargs='*', default=None,
                      help='exclude specified routine names')
  result = parser.parse_args();
  print (result)
  outputFilename = result.outputFile
  outputDir = os.path.dirname(outputFilename)
  assert os.path.exists(outputDir)
  """ create the VistATestClient"""
  testClient = VistATestClientFactory.createVistATestClientWithArgs(result)
  assert testClient
  with testClient as vistAClient:
    logFilename = getTempLogFile()
    print "Log File is %s" % logFilename
    vistAClient.setLogFile(logFilename)
    isAllRoutines = result.allRoutines
    vistARoutineExport = VistARoutineExport()
    if isAllRoutines:
      vistARoutineExport.exportAllRoutines(vistAClient, outputFilename,
                                           result.exclude)
    else:
      vistARoutineExport.exportRoutines(vistAClient, outputFilename,
                                        result.routines,
                                        result.exclude)
if __name__ == '__main__':
  main()
