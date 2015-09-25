#!/usr/bin/python

"""

An implementation of the Nordic "nrfjprog.exe" program
using python and jlink.py.

See README.md for installation and more information.
"""

from jlink import jlink
import sys

if __name__=="__main__":
    _jl=None
    def jl():
        global _jl
        _jl = _jl or jlink.JLink()
        return _jl

    args = sys.argv[1:]
    
    while (args):
        arg = args.pop(0)

        if arg=="--erase":
            jl().halt()
            #jl().erase_partial(0xA000,256*1024)
            jl().erase_all()

        elif arg=="--reset":
            jl().halt()
            jl().reset()
        
        elif arg=="--program":
            filename = args.pop(0)
            jl().auto_program(filename)

        elif arg=="--dumpfile":
            startaddr = int(args.pop(),base=0)
            endaddr = int(args.pop(),base=0)
            filename = args.pop(0)
            jl().halt()
            print 'Dumping %x -> %x to file "%s"'%(startaddr,
                                                   endaddr,
                                                   filename)
            jl().make_dump(startaddr,endaddr,filename)

        else:
            print "unknown argument: ",arg
            sys.exit(-1)

