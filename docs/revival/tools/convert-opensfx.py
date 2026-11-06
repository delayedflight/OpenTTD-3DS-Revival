"""Convert official OpenSFX 1.0.3 CAT into OpenTTD 0.7's PCM8/11025 bank.
Requires macOS afconvert. CC BY-SA 3.0 applies to converted audio; keep upstream
credits/license. No individual effects or their CAT index order are replaced.
"""
from pathlib import Path
import struct,io,wave,subprocess,hashlib,json,sys
p=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else Path(__file__).resolve().parent; p.mkdir(parents=True,exist_ok=True);up=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else p.parent/'opensfx-1.0.3/upstream/opensfx.cat';b=up.read_bytes();count=(struct.unpack_from('<I',b)[0]&0x7fffffff)//8;assert count==73
entries=[];manifest=[];wavdir=p/'wav';wavdir.mkdir(exist_ok=True)
for i in range(count):
 off,n=struct.unpack_from('<II',b,i*8);off&=0x7fffffff;name=b[off+1:off+1+b[off]];assert name.endswith(b'\0');start=off+1+b[off];raw=b[start:start+n];assert raw[:4]==b'RIFF'
 src=wavdir/f'{i:02d}-source.wav';dst=wavdir/f'{i:02d}-pcm8.wav';src.write_bytes(raw)
 subprocess.run(['afconvert','-f','WAVE','-d','UI8@11025','-c','1','-q','127',str(src),str(dst)],check=True)
 with wave.open(str(dst),'rb') as w:assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,1,11025);pcm=w.readframes(w.getnframes())
 assert (pcm and any(v!=128 for v in pcm)) or i in (34,50);n=len(pcm);pad=b'\0' if n%2 else b''
 riff=b'RIFF'+struct.pack('<I',36+n+len(pad))+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,1,11025,11025,1,8)+b'data'+struct.pack('<I',n)+pcm+pad
 entries.append((name,riff));manifest.append(dict(index=i,credit=name[:-1].decode('utf-8',errors='replace'),pcm_bytes=n,seconds=n/11025,sha256=hashlib.sha256(pcm).hexdigest()))
off=count*8;table=bytearray();data=bytearray()
for name,riff in entries:table+=struct.pack('<II',off,len(riff));entry=bytes([len(name)])+name+riff;data+=entry;off+=len(entry)
bank=bytes(table+data);(p/'sample.cat').write_bytes(bank);(p/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('Converted',count,'effects; bank bytes',len(bank),'largest PCM',max(x['pcm_bytes'] for x in manifest),'SHA256',hashlib.sha256(bank).hexdigest())
