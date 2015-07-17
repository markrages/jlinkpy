nrfjprog
--------

An implementation of the Nordic "nrfjprog.exe" program using python
and jlink.py.

nrfjprog.exe is used to program softdevices and application code in
the nRF51422 and nRF51822 system-on-chip radio microcontrollers.

It uses the Segger "J-Link" hardware, or the built-in Segger supplied
with many of the Nordic development kits and dongles.

Features
--------
I mostly intend to support the subset of features that are needed to
make the SDK Makefiles work on a Linux or OS X machine.

I ran the following on a selection of installed SDKs to see what
nrfjprog options are used by the Makefiles:

    grep nrfjprog -rI /opt/nrf51sdk-* | grep Makefile | sed s/.*nrfjprog/nrfjprog/ | sort | uniq
    
This gives the following set of uses:

    nrfjprog --erase
    nrfjprog --reset
    nrfjprog --reset --program softdevice.hex
    nrfjprog --reset --program $(OUTPUT_BINARY_DIRECTORY)/$(OUTPUT_FILENAME).hex

So nrfjprog implements the --erase, --reset, and --program commands.

Setting up
----------
There are two paths, `lib32/` and `lib64/`. You must download the
appropriate DLL from http://www.segger.com and add it to the
appropriate directory depending on your system.

The DLL ending is different among the three supported platforms:

| Platform | Extension |
| -------- | --------- |
| Windows  | .dll      |
| Linux    | .so       |
| OS X     | .dylib    |

The Windows dll is named `jlinkarm.dll`.

The Linux dll is named something like `libjlinkarm.so.4.62.1`.  After
putting it in the right directory, make a symlink to
`libjlinkarm.so.4` in the same directory:

     ln -s libjlinkarm.so.4.*.* libjlinkarm.so.4

Linux users should also install the Segger-provided udev rule to allow
the device to be used as a non-root user. See the Segger
documentation.

The OS X dll is named something like `libjlinkarm.4.62.1.dylib`.
After putting it in the right directory, make a symlink to
`libjlinkarm.4.dylib` in the same directory:

     ln -s libjlinkarm.4.*.*.dylib libjlinkarm.4.dylib

To test that the DLL is functioning properly, connect a Segger and run
`python jlink.py` by itself.  It will error out if the library doesn't
load or the Segger isn't connected.

Installation
------------
Install by running "setup.py install". This will install the library
and segger libs to a Python-findable location.

Usage
-----
Consult the nrfjprog.exe documentation. If this nrfjprog behavior
diverges from the official one, please file a bug.

Using Nordic SDK Makefiles
--------------------------

Here's a hint for using the Nordic Makefiles.  They have a weirdly
specific GCC installation path.  Furthermore, this path is hardcoded
in the SDK Makefile.common and cannot be overridden by application
Makefiles.

Rather than horsing around with compiling GCC from scratch, or using
~~lockin~~ toolchain vendors, it is easier and better to use a
distribution-supported GCC, or the ARM-unofficially-supported PPA (for
Ubuntu achievers):

    sudo add-apt-repository ppa:terry.guo/gcc-arm-embedded
    sudo apt-get update
    sudo apt-get install gcc-arm-none-eabi

A simple symlink will make things work fine with GCC in the normal
location:

     sudo ln -rs /usr /usr/local/gcc-arm-none-eabi-4_8-2014q1

Now the Makefiles in the SDK will work unchanged, including the "make
flash" target.
