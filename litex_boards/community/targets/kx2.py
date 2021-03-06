#!/usr/bin/env python3

# This file is Copyright (c) 2014-2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# This file is Copyright (c) 2014-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2014-2015 Yann Sionneau <ys@m-labs.hk>
# License: BSD

import argparse

from migen import *

from litex.boards.platforms import kx2

from litex.soc.cores.clock import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import H5TC4G63CFR
from litedram.phy import s7ddrphy


# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()

        # # #

        self.submodules.pll = pll = S7MMCM(speedgrade=-2)
        self.comb += pll.reset.eq(~platform.request("cpu_reset_n"))
        pll.register_clkin(platform.request("clk200"), 200e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        pll.create_clkout(self.cd_sys4x, 4 * sys_clk_freq)
        pll.create_clkout(self.cd_clk200, 200e6)

        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_clk200)


# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCSDRAM):
    def __init__(self, sys_clk_freq=int(125e6), integrated_rom_size=0x8000, **kwargs):
        platform = kx2.Platform()

        # SoCSDRAM ---------------------------------------------------------------------------------
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq,
                          integrated_rom_size=integrated_rom_size,
                          integrated_sram_size=0x8000,
                          **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # DDR3 SDRAM -------------------------------------------------------------------------------
        if not self.integrated_main_ram_size:
            self.submodules.ddrphy = s7ddrphy.K7DDRPHY(platform.request("ddram"),
                                                       memtype="DDR3",
                                                       nphases=4,
                                                       sys_clk_freq=sys_clk_freq)
            self.add_csr("ddrphy")
            sdram_module = H5TC4G63CFR(sys_clk_freq, "1:4")
            self.register_sdram(self.ddrphy,
                                geom_settings=sdram_module.geom_settings,
                                timing_settings=sdram_module.timing_settings)


# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on KX2")
    builder_args(parser)
    soc_sdram_args(parser)
    # parser.add_argument(action="store_true")
    args = parser.parse_args()

    soc = BaseSoC(**soc_sdram_argdict(args))
    builder = Builder(soc, **builder_argdict(args))
    builder.build()


if __name__ == "__main__":
    main()
