#!/usr/bin/env python
# encoding:utf-8

"""
    :created: 2013-2014 by Jens Diemer - www.jensdiemer.de
    :copyleft: 2013-2014 by the DragonPy team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import logging
import sys
import unittest
import itertools

from cpu6809 import CPU
from Dragon32.config import Dragon32Cfg
from Dragon32.mem_info import DragonMemInfo
from tests.test_base import TextTestRunner2, BaseTestCase, UnittestCmdArgs


log = logging.getLogger("DragonPy")


class Test6809_ArithmeticShift(BaseTestCase):
    def test_ASRA_inherent(self):
        """
        Example assembler code to test ASRA

        CLRB        ; B is always 0
        TFR B,U     ; clear U
loop:
        TFR U,A     ; for next test
        TFR B,CC    ; clear CC
        LSRA
        NOP
        LEAU 1,U    ; inc U
        JMP loop
        """
        for i in xrange(0x100):
            self.cpu.accu_a.set(i)
            self.cpu.cc.set(0x00) # Clear all CC flags
            self.cpu_test_run(start=0x1000, end=None, mem=[
                0x44, # LSRA/ASRA Inherent
            ])
            r = self.cpu.accu_a.get()
#             print "%02x %s > ASRA > %02x %s -> %s" % (
#                 i, '{0:08b}'.format(i),
#                 r, '{0:08b}'.format(r),
#                 self.cpu.cc.get_info
#             )

            # test LSL result
            r2 = i >> 1 # shift right
            r2 = r2 & 0xff # wrap around
            self.assertEqualHex(r, r2)

            # test negative
            if 128 <= r <= 255:
                self.assertEqual(self.cpu.cc.N, 1)
            else:
                self.assertEqual(self.cpu.cc.N, 0)

            # test zero
            if r == 0:
                self.assertEqual(self.cpu.cc.Z, 1)
            else:
                self.assertEqual(self.cpu.cc.Z, 0)

            # test overflow
            self.assertEqual(self.cpu.cc.V, 0)

            # test carry
            source_bit0 = 0 if i & 2 ** 0 == 0 else 1
            self.assertEqual(self.cpu.cc.C, source_bit0)

    def test_ASLA_inherent(self):
        for i in xrange(260):
            self.cpu.accu_a.set(i)
            self.cpu.cc.set(0x00) # Clear all CC flags
            self.cpu_test_run(start=0x1000, end=None, mem=[
                0x48, # LSLA/ASLA Inherent
            ])
            r = self.cpu.accu_a.get()
#             print "%02x %s > LSLA > %02x %s -> %s" % (
#                 i, '{0:08b}'.format(i),
#                 r, '{0:08b}'.format(r),
#                 self.cpu.cc.get_info
#             )

            # test LSL result
            r2 = i << 1 # shift left
            r2 = r2 & 0xff # wrap around
            self.assertEqualHex(r, r2)

            # test negative
            if 128 <= r <= 255:
                self.assertEqual(self.cpu.cc.N, 1)
            else:
                self.assertEqual(self.cpu.cc.N, 0)

            # test zero
            if r == 0:
                self.assertEqual(self.cpu.cc.Z, 1)
            else:
                self.assertEqual(self.cpu.cc.Z, 0)

            # test overflow
            if 64 <= i <= 191:
                self.assertEqual(self.cpu.cc.V, 1)
            else:
                self.assertEqual(self.cpu.cc.V, 0)

            # test carry
            if 128 <= i <= 255:
                self.assertEqual(self.cpu.cc.C, 1)
            else:
                self.assertEqual(self.cpu.cc.C, 0)

    def assertROL(self, src, dst, source_carry):
            src_bit_str = '{0:08b}'.format(src)
            dst_bit_str = '{0:08b}'.format(dst)
#             print "%02x %s > ROLA > %02x %s -> %s" % (
#                 src, src_bit_str,
#                 dst, dst_bit_str,
#                 self.cpu.cc.get_info
#             )

            # Carry was cleared and moved into bit 0
            excpeted_bits = "%s%s" % (src_bit_str[1:], source_carry)
            self.assertEqual(dst_bit_str, excpeted_bits)

            # test negative
            if dst >= 0x80:
                self.assertEqual(self.cpu.cc.N, 1)
            else:
                self.assertEqual(self.cpu.cc.N, 0)

            # test zero
            if dst == 0:
                self.assertEqual(self.cpu.cc.Z, 1)
            else:
                self.assertEqual(self.cpu.cc.Z, 0)

            # test overflow
            source_bit6 = 0 if src & 2 ** 6 == 0 else 1
            source_bit7 = 0 if src & 2 ** 7 == 0 else 1
            if source_bit6 == source_bit7: # V = bit 6 XOR bit 7
                self.assertEqual(self.cpu.cc.V, 0)
            else:
                self.assertEqual(self.cpu.cc.V, 1)

            # test carry
            if 0x80 <= src <= 0xff: # if bit 7 was set
                self.assertEqual(self.cpu.cc.C, 1)
            else:
                self.assertEqual(self.cpu.cc.C, 0)

    def test_ROLA_with_clear_carry(self):
        for a in xrange(0x100):
            self.cpu.cc.set(0x00) # clear all CC flags
            a = self.cpu.accu_a.set(a)
            self.cpu_test_run(start=0x0000, end=None, mem=[
                0x49, # ROLA
            ])
            r = self.cpu.accu_a.get()
            self.assertROL(a, r, source_carry=0)

            # test half carry is uneffected!
            self.assertEqual(self.cpu.cc.H, 0)

    def test_ROLA_with_set_carry(self):
        for a in xrange(0x100):
            self.cpu.cc.set(0xff) # set all CC flags
            a = self.cpu.accu_a.set(a)
            self.cpu_test_run(start=0x0000, end=None, mem=[
                0x49, # ROLA
            ])
            r = self.cpu.accu_a.get()
            self.assertROL(a, r, source_carry=1)

            # test half carry is uneffected!
            self.assertEqual(self.cpu.cc.H, 1)

if __name__ == '__main__':
    log.setLevel(
#         1
#        10 # DEBUG
#         20 # INFO
#         30 # WARNING
#         40 # ERROR
        50 # CRITICAL/FATAL
    )
    log.addHandler(logging.StreamHandler())

    # XXX: Disable hacked XRoar trace
    import cpu6809; cpu6809.trace_file = None

    unittest.main(
        argv=(
            sys.argv[0],
#             "Test6809_ArithmeticShift.test_LSL",
        ),
        testRunner=TextTestRunner2,
#         verbosity=1,
        verbosity=2,
#         failfast=True,
    )
