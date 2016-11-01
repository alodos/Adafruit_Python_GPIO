# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import platform
import re

# Platform identification constants.
UNKNOWN          = 0
RASPBERRY_PI     = 1
BEAGLEBONE_BLACK = 2
MINNOWBOARD      = 3
SUNXI            = 4

def platform_detect():
    """Detect if running on the Raspberry Pi or Beaglebone Black and return the
    platform type.  Will return RASPBERRY_PI, BEAGLEBONE_BLACK, or UNKNOWN."""
    # Handle Raspberry Pi
    pi = pi_version()
    if pi is not None:
        return RASPBERRY_PI

    # Handle Beaglebone Black
    # TODO: Check the Beaglebone Black /proc/cpuinfo value instead of reading
    # the platform.
    plat = platform.platform()
    if plat.lower().find('armv7l-with-debian') > -1:
        return BEAGLEBONE_BLACK
    elif plat.lower().find('armv7l-with-ubuntu') > -1:
        return BEAGLEBONE_BLACK
    elif plat.lower().find('armv7l-with-glibc2.4') > -1:
        return BEAGLEBONE_BLACK
        
    # Handle Minnowboard
    # Assumption is that mraa is installed
    try: 
        import mraa 
        if mraa.getPlatformName()=='MinnowBoard MAX':
            return MINNOWBOARD
    except ImportError:
        pass

    # TODO: sunxi platforms
    # Handle Allwinner sunxi platforms
    #
    #  Cortex A5 - 0xc05
    #  Cortex A8 - 0xc08
    #  Cortex A9 - 0xc09
    #  Cortex A15 - 0xc0f
    #  Cortex R4 - 0xc14
    #  Cortex R5 - 0xc15
    #  ARM1136 - 0xb36
    #  ARM1156 - 0xb56
    #  ARM1176 - 0xb76
    #  ARM11 MPCore - 0xb02
    #
    #   Handle Cubieboard
    #       Cubieboard 1 sun4i (Allwinner A10 Cortex-A7)
    #       Cubieboard 2 sun7i (AllWinner A20 2xCortex-A7)
    #       Cubieboard 3 (cubietruck) sun7i (AllWinnerTech A20 2xCortex-A7)
    #       Cubieboard 4 (CC-A80) sun8i A83T/H8 (Allwinner H8 4xCortex-A15 + 4xCortex-A7)
    #
    #       Handle Cubieboard4
    #           cat /proc/cpuinfo
    #            Processor       : ARMv7 Processor rev 0 (v7l)
    #            Hardware        : sun9i
    #
    #           python>>> platform.uname()
    #            ('Linux', 'localhost', '3.4.39', '#1 SMP PREEMPT Thu Jul 28 04:18:26 MSK 2016', 'armv7l', 'armv7l')
    #            ('Linux', 'cubieboard4', '3.4.39', '#1 SMP PREEMPT Thu Jul 28 04:18:26 MSK 2016', 'armv7l', 'armv7l')
    #
    #           uname -a
    #            Linux cubieboard4 3.4.39 #1 SMP PREEMPT Thu Jul 28 04:18:26 MSK 2016 armv7l armv7l armv7l GNU/Linux
    #
    #           cat /etc/issue.net
    #            Linaro 14.04
    #
    #           cat /etc/os-release
    #            NAME="Linaro"
    #            VERSION="14.04"
    #            ID=linaro
    #            ID_LIKE=debian
    #   Handle Olimex
    #   ...
    #   return SUNXI

    # Couldn't figure out the platform, just return unknown.
    return UNKNOWN


def pi_revision():
    """Detect the revision number of a Raspberry Pi, useful for changing
    functionality like default I2C bus based on revision."""
    # Revision list available at: http://elinux.org/RPi_HardwareHistory#Board_Revision_History
    with open('/proc/cpuinfo', 'r') as infile:
        for line in infile:
            # Match a line of the form "Revision : 0002" while ignoring extra
            # info in front of the revsion (like 1000 when the Pi was over-volted).
            match = re.match('Revision\s+:\s+.*(\w{4})$', line, flags=re.IGNORECASE)
            if match and match.group(1) in ['0000', '0002', '0003']:
                # Return revision 1 if revision ends with 0000, 0002 or 0003.
                return 1
            elif match:
                # Assume revision 2 if revision ends with any other 4 chars.
                return 2
        # Couldn't find the revision, throw an exception.
        raise RuntimeError('Could not determine Raspberry Pi revision.')


def pi_version():
    """Detect the version of the Raspberry Pi.  Returns either 1, 2 or
    None depending on if it's a Raspberry Pi 1 (model A, B, A+, B+),
    Raspberry Pi 2 (model B+), or not a Raspberry Pi.
    """
    # Check /proc/cpuinfo for the Hardware field value.
    # 2708 is pi 1
    # 2709 is pi 2
    # Anything else is not a pi.
    with open('/proc/cpuinfo', 'r') as infile:
        cpuinfo = infile.read()
    # Match a line like 'Hardware   : BCM2709'
    match = re.search('^Hardware\s+:\s+(\w+)$', cpuinfo,
                      flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        # Couldn't find the hardware, assume it isn't a pi.
        return None
    if match.group(1) == 'BCM2708':
        # Pi 1
        return 1
    elif match.group(1) == 'BCM2709':
        # Pi 2
        return 2
    else:
        # Something else, not a pi.
        return None


def cubie_version():
    """Detect the version of the Cubieboard/CubieTruck.  Returns either 4, 5 or
    None depending on if it's a Cubieboard 4 (CC-A80), CubieTruck Plus/Cubieboard 5,
    or not a Cubieboard.
    """
    # Check /proc/cpuinfo for the Hardware field value.
    # sun9i is cb4
    # sun8i is cb5
    # Anything else is not a cubie.
    with open('/proc/cpuinfo', 'r') as infile:
        cpuinfo = infile.read()
    # Match a line like 'Hardware   : sun9i'
    match = re.search('^Hardware\s+:\s+(\w+)$', cpuinfo,
                      flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        # Couldn't find the hardware, assume it isn't a cubie.
        return None
    if match.group(1) == 'sun9i':
        # Cubieboard 4
        return 4
    elif match.group(1) == 'sun8i':
        # Cubieboard 5
        return 5
    else:
        # Something else, not a cubie.
        return None
