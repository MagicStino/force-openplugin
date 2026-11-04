#!/usr/bin/env python3
"""Execute exact original/patched ARM predicates. Requires unicorn and stock ELF inputs."""
import argparse,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openplugin.track_limits import CONFIG,patch_app,locate_sites
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_LR,UC_ARM_REG_PC
def setup(data, predicate):
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map((predicate & ~0xfff),0x1000);u.mem_write((predicate & ~0xfff),bytes(data[(predicate & ~0xfff):((predicate & ~0xfff)+0x1000)]));u.mem_map(0x10000000,0x1000);u.mem_map(0x20000000,0x1000);return u
def call(u,kind,count,add,total,predicate,max_total=128):
 obj=bytearray(0x200)
 for offset,value in [(0x44,max_total),(0xa0,0x30000000),(0xa4,0x30000000+4*total),(0xc0,0x31000000),(0xc4,0x31000000+4*count),(0x120,0x32000000),(0x124,0x32000000+4*count)]:struct.pack_into('<I',obj,offset,value)
 u.mem_write(0x10000000,bytes(obj))
 for reg,val in [(UC_ARM_REG_R0,0x10000000),(UC_ARM_REG_R1,kind),(UC_ARM_REG_R2,add),(UC_ARM_REG_LR,0x20000000)]:u.reg_write(reg,val)
 u.emu_start(predicate,0x20000000,count=100)
 assert u.reg_read(UC_ARM_REG_PC)==0x20000000
 return u.reg_read(UC_ARM_REG_R0)

p=argparse.ArgumentParser();p.add_argument('--device',choices=CONFIG,required=True);p.add_argument('--app',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
b=a.app.read_bytes();patched_bytes=patch_app(b,a.device);sites=locate_sites(b);pred=sites['predicate'];assert pred==sites['virtual_address'], 'Harness requires identity ELF mapping';orig=setup(b,pred);patched=setup(patched_bytes,pred);n=0
for kind in range(10):
 for count in [0,7,8,9,15,16,17]:
  for add in [0,1,2,8,16]:
   for total in [count,127,128]:
    before=call(orig,kind,count,add,total,pred);after=call(patched,kind,count,add,total,pred)
    expected=lambda cap:int(total+add<=128 and (kind not in [3,6] or count+add<=cap))
    if before!=expected(8) or after!=expected(16):raise RuntimeError((kind,count,add,total,before,after))
    n+=1
report={'device':a.device,'cases_passed':n,'audio_limit':16,'plugin_limit':16,'scope':'Actual ARM predicate with synthetic object state; not a host or hardware test','overall_limit_preserved':True}
a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
