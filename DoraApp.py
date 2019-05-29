#!/usr/local/bin/python3
import pycpsw
import pathGrep
import time
import IrqHandler
import ClockSwitcher
import re
import os
import YamlFixup
import genSimple
from   flask import render_template, send_from_directory

deviceTopName = "Timing-Trigger Box 7"

def TboxSimplePage():
  return render_template(simpleTemplateName, deviceTopName = deviceTopName)

def TboxStatic(path):
  prefix = os.path.dirname(__file__) + '/static/'
  return send_from_directory(prefix, path)

class YamlFixup(YamlFixup.YamlFixup):
  def __init__(self, optDict, argList):
    super(YamlFixup, self).__init__(optDict, argList)

  def findNode(self, rn, path):
    n = pycpsw.YamlFixup.findByName(rn, path)
    if not n.IsDefined() or n.IsNull():
      raise RuntimeError("tbox.YamlFixup: YAML node '" + path + "' not found")
    return n
 

  def __call__(self, rootNode, topNode):
    super(YamlFixup, self).__call__(rootNode, topNode)
    p = "/mmio/AmcCarrierCore/AmcCarrierTiming/EvrV2CoreTriggers/"
    trgs  = self.findNode(rootNode, p.replace("/","/children/"))
    chreg = self.findNode(trgs,     "EvrV2ChannelReg/children")
    n     = self.findNode(chreg,   "BsaEnabled")
    n["instantiate"] = "False"
    n     = self.findNode(chreg,   "BsaWindowDelay")
    n["instantiate"] = "False"
    n     = self.findNode(chreg,   "BsaWindowWidth")
    n["instantiate"] = "False"
    n     = self.findNode(chreg,   "BsaWindowSetup")
    n["instantiate"] = "False"
    n     = self.findNode(chreg,   "DmaEnabled")
    n["instantiate"] = "False"
    chreg = self.findNode(trgs,     "EvrV2ChannelReg")
    n     = self.findNode(chreg,   "at")
    n["nelms"] = "7"
    chreg = self.findNode(trgs,     "EvrV2TriggerReg")
    n     = self.findNode(chreg,   "at")
    n["nelms"] = "7"

class DoraApp(object):
  def __init__(self):
    super(DoraApp, self).__init__()

  def getYamlFixup(self, optDict, mainArgs):
    self.optDict_ = optDict
    return YamlFixup( optDict, mainArgs )

  def getTopLevelName(self):
    return deviceTopName

  def initApp(self, cpswRoot, flaskApp):
    self.flaskApp_ = flaskApp
    self.flaskApp_.add_url_rule('/simple', 'simple', TboxSimplePage)
    self.flaskApp_.add_url_rule('/simple/static/<path:path>', 'simpleStatic', TboxStatic)
    print("URL RULE ADDED")
    if self.optDict_["UseNullDev"]:
      return
    self.confDir_  = "../yaml/"
    self.cpswRoot_ = cpswRoot
    r              = self.cpswRoot_
    pg             = pathGrep.PathGrep( r, asPath=True)
    sysincal       = pycpsw.ScalVal_RO.create(pg("/Si5344/SYSINCAL$")[0])
    if 0 != sysincal.getVal():
      r.loadConfigFromYamlFile( self.confDir_ + "defaults_si5344.yaml" )
    for i in range(10):
      if 0 == sysincal.getVal():
        break
      time.sleep(0.5)
    else:
      raise RuntimeError("SI5344 would not finish calibrating")
    r.loadConfigFromYamlFile( self.confDir_ + "defaults.yaml" )
    self.irqHdlr_  = IrqHandler.IrqHandler( r, [ClockSwitcher.ClockSwitchAction(r, self.confDir_ )])
    self.irqHdlr_.start()

  def getDebugProbesPath(self):
    if self.optDict_["UseNullDev"]:
      return None
    rp = os.path.realpath("/lib/firmware/zynq-firmware.bin")
    ltxp = re.sub("[.]bin([.]swab)?", ".ltx", rp)
    if os.path.isfile( ltxp ):
      return ltxp
    else:
      return None

  def genHtml(self, appDb, chksumAsString, yamlHasChanged):
    global simpleTemplateName
    simpleTemplateName = "guts-simple-"+chksumAsString+".html"
    tmplPath           = "templates/" + simpleTemplateName
    if yamlHasChanged or not os.path.isfile( tmplPath ):
      genSimple.GenSimple( appDb, tmplPath )

  def getAppLinks(self):
    return [ { "ref": "/simple", "txt": "Trigger Controls" } ]
