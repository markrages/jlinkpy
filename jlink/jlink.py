#!/usr/bin/python

import sys
import os
import ctypes
import memory

DEBUG=0

BASE=0x4001e000
READY=BASE+0x400
CONFIG=BASE+0x504
CONFIG_EEN=2
CONFIG_WEN=1
CONFIG_REN=0
ERASEPAGE=BASE+0x508
ERASEALL=BASE+0x50c

def print_range(start, end, text=''):
    print " | 0x%08x -> 0x%08x (%d bytes)"%(start, end, end-start),
    print text

def print_segment(segment):
    return print_range(segment.startaddress, segment.startaddress + len(segment.data))

def print_mem_map(progdata):
    for segment in progdata.segments:
        print_segment(segment)

def locate_library(libname, paths=sys.path, loader=None):
    if loader is None: loader=ctypes.cdll #windll
    for path in paths:
        if path.lower().endswith('.zip'):
            path = os.path.dirname(path)
        library = os.path.join(path, libname)
        if DEBUG > 4: sys.stderr.write('trying %r...\n' % library)
        if os.path.exists(library):
            if DEBUG > 4: sys.stderr.write('using %r\n' % library)
            return loader.LoadLibrary(library), library
    else:
        raise IOError('%s not found' % libname)

def get_jlink_dll():

    # what kind of system am I?
    import platform
    if platform.architecture()[0]=='32bit':
        libpath='lib32'
    elif platform.architecture()[0]=='64bit':
        libpath='lib64'
    else:
        libpath=''
        raise Exception(repr(platform.architecture()))
        
    # start with the script path
    search_path = [os.path.join(os.path.dirname(os.path.realpath(__file__)),libpath)]
    search_path += sys.path[:]   #copy sys.path list

    # if environment variable is set, insert this path first
    try:
        search_path.insert(0, os.environ['JLINK_PATH'])
    except KeyError:
        try:
            search_path.extend(os.environ['PATH'].split(os.pathsep))
        except KeyError:
            pass

    if sys.platform == 'win32':
        jlink, backend_info = locate_library('jlinkarm.dll', search_path)
    elif sys.platform == 'linux2':
        jlink, backend_info = locate_library('libjlinkarm.so.4', 
                                             search_path, ctypes.cdll)
    elif sys.platform == 'darwin':
        jlink, backend_info = locate_library('libjlinkarm.so.4.dylib', 
                                             search_path, ctypes.cdll)
    return jlink, backend_info

class JLinkException(Exception): pass

import time
class JLink(object):
    def __init__(self):
        timeout=10
        retried=False
        t0=time.time()
        elapsed=-1
        while time.time() < t0+timeout:
            self.jl,self.jlink_lib_name = get_jlink_dll()
            try:
                self._init()
                if retried: print "success"
                return
            except JLinkException,x:
                if x.args[0]==-258:
                    new_elapsed=int(time.time()-t0)
                    if new_elapsed != elapsed:
                        elapsed=new_elapsed                     
                        print timeout-elapsed,
                        sys.stdout.flush()

                    retried=True
                    continue
                else:
                    raise
        else:
            raise            

    def _init(self):
        self.tif_select(1)
        self.set_speed(1000)
        self.reset()
        pass

    def clear_error(self): self.jl.JLINK_ClrError()
    def has_error(self): return self.jl.JLINK_HasError();

    def check_err(fn):
        def checked_transaction(self,*args):
            self.clear_error()
            ret=fn(self, *args)
            errno=self.has_error()
            if errno:
                raise JLinkException(errno)
            return ret
        return checked_transaction

    @check_err
    def tif_select(self, tif): 
        return self.jl.JLINKARM_TIF_Select(tif)
    @check_err
    def set_speed(self, khz): return self.jl.JLINKARM_SetSpeed(khz)
    @check_err
    def reset(self): return self.jl.JLINKARM_Reset()
    @check_err
    def halt(self): return self.jl.JLINKARM_Halt()
    @check_err
    def clear_tck(self): return self.jl.JLINKARM_ClrTCK()
    @check_err
    def clear_tms(self): return self.jl.JLINKARM_ClrTMS()
    @check_err
    def set_tms(self): return self.jl.JLINKARM_SetTMS()
    @check_err
    def read_reg(self,r): return self.jl.JLINKARM_ReadReg(r)
    @check_err
    def write_reg(self,r,val): return self.jl.JLINKARM_WriteReg(r,val)
    @check_err
    def write_U32(self,r,val): return self.jl.JLINKARM_WriteU32(r,val)
    @check_err                       
    def open(self): return self.jl.JLINKARM_Open()
    @check_err                       
    def close(self): return self.jl.JLINKARM_Close()
    @check_err                       
    def go(self): return self.jl.JLINKARM_Go()
    @check_err
    def write_mem(self,startaddress, data):
        buf=ctypes.create_string_buffer(data)
        return self.jl.JLINKARM_WriteMem(startaddress,len(data),buf)
    @check_err
    def read_mem(self, startaddress, length):
        buf=ctypes.create_string_buffer(length)
        ret=self.jl.JLINKARM_ReadMem(startaddress,length, buf)
        return buf,ret
    @check_err
    def read_mem_U32(self, startaddress, count):
        buftype=ctypes.c_uint32 * int(count)
        buf=buftype()
        ret=self.jl.JLINKARM_ReadMemU32(startaddress, count, buf, 0)
        return buf,ret

    # end of DLL functions

    def pinreset(self): 
        """executes sequence from 
        https://devzone.nordicsemi.com/question/18449
        """
        self.write_U32(0x40000544, 1)
        self.tif_select(0)
        self.clear_tck()
        self.clear_tms()
        time.sleep(0.010)
        self.set_tms()
    
    def erase_minimal(self, memory):
        startaddress=min(s.startaddress for s in memory.segments)
        endaddress=max(s.startaddress+len(s.data) for s in memory.segments)
        binsize=endaddress-startaddress

        startaddr=startaddress&~511
        endaddr=startaddr+512*(1+((binsize-1)//512))
        self.erase_partial(startaddr,endaddr)

    def erase_partial(self, startaddr, endaddr):
        print "erasing from 0x%x->0x%x"%(startaddr,endaddr)

        self.write_U32(CONFIG,CONFIG_EEN)
        for i in range(startaddr, endaddr, 512):
            print("0x%x (%d%%)\r"%(i,100*(i-startaddr)/(endaddr-startaddr))),
            sys.stdout.flush()
            self.write_U32(ERASEPAGE,i)            
            self._wait_ready()

        self.write_U32(CONFIG,CONFIG_REN)
        self._wait_ready()

    def erase_all(self):
        self.write_U32(CONFIG, CONFIG_EEN)
        self.write_U32(ERASEALL,1)
        self._wait_ready()
        self.write_U32(CONFIG, CONFIG_REN)
        self._wait_ready()

    def _wait_ready(self):
        while 1:
            ready,_=self.read_mem_U32(READY,1)
            if ready[0]: break
        
    def make_dump(self,startaddress,endaddress,name):
        x,y=self.read_mem(startaddress, endaddress-startaddress)
        file('%s.bin'%name,'w').write(x[:])
        
    def burn(self, memory):
        self.halt()
        #self.make_dump(0xa000,0x27c00,"before")
        self.erase_minimal(memory)
        #self.make_dump(0xa000,0x27c00,"erased")
        return self._burn_internal(memory.segments)

    def _burn_internal(self, segments):

        self.write_U32(CONFIG, CONFIG_WEN)
        self._wait_ready()
        startaddress=min(s.startaddress for s in segments)
        endaddress=max(s.startaddress+len(s.data) for s in segments)

        #startaddress=0

        if 0:
            mem_map=['\xff']*(endaddress-startaddress)

            for s in segments:
                s0=s.startaddress-startaddress
                s1=s0+len(s.data)
                mem_map[s0:s1]=s.data[:]

            print "writing from 0x%x->0x%x"%(startaddress,
                                             startaddress+len(mem_map))
            self.write_mem(startaddress,''.join(mem_map))

        else:
            for s in segments:
                print "writing from 0x%x->0x%x"%(s.startaddress,
                                                 s.startaddress+len(s.data))
                self.write_mem(s.startaddress,s.data)

        #self.make_dump(0xa000,0x27c00,"written")

        self.reset()

        self.go()
        #time.sleep(5)

        self.pinreset()

        return

        
    def burnfile(self,filename):
        print
        print "map of %s:"%filename
        progdata=load_elf(filename)
        print_mem_map(progdata)
        print
        return self.burn(progdata)

    def burnsoftdevice(self,softdevice_filename):
        mem=load_elf(softdevice_filename)
        print_mem_map(mem)
        print

        self.halt()
        self.erase_all()
        self.reset()
        self.halt()
        self._burn_internal(mem.segments)

    def auto_program(self, filename):
        mem=load_elf(filename)
        print_mem_map(mem)
        self.halt()
        self._burn_internal(mem.segments)


def load_elf(filename):
    progdata=memory.Memory()
    progdata.loadFile(filename)
    return progdata
    
if __name__=="__main__":
    jl=JLink()
