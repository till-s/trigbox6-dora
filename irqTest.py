import pycpsw
import pathGrep
import IrqHandler
import ClockSwitcher
import os

r = pycpsw.Path.loadYamlFile("../yaml/000TopLevel.yaml")
pg=pathGrep.PathGrep(r, asPath=True)

irq = IrqHandler.IrqHandler(r, [ClockSwitcher.ClockSwitchAction(r,"../yaml/")])
#clk.start()

enb = pycpsw.ScalVal.create( pg("ClkSelIrqEnable$")[0] )
sta = pycpsw.ScalVal_RO.create( pg("ClkSelIrqPending$")[0] )
sel = pycpsw.ScalVal.create( pg("ClkSel$")[0] )

