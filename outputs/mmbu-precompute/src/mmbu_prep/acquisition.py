"""Explicit bounded public archive acquisition, separate from offline prep CLI.

Range reads verify server boundaries and selected ZIP member CRCs. They do not
verify a whole archive checksum or authenticate an unstated source revision.
"""
from collections import OrderedDict
import hashlib
import io
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import urllib.parse
import unicodedata
import urllib.request
import zipfile


class HTTPRangeReader(io.RawIOBase):
    def __init__(self, url, size, *, block_size=1_048_576, max_transfer_bytes=67_108_864, cache_blocks=8, timeout=30):
        super().__init__()
        parsed=urllib.parse.urlparse(url)
        if parsed.username or parsed.password or parsed.scheme not in ('https','http') or not parsed.netloc:
            raise ValueError('Expected explicit HTTP(S) URL without embedded credentials')
        for name,value in [('size',size),('block_size',block_size),('max_transfer_bytes',max_transfer_bytes),('cache_blocks',cache_blocks)]:
            if type(value) is not int or value<1:raise ValueError(name+' must be a positive integer')
        if timeout<=0 or timeout>60:raise ValueError('timeout must be in (0,60] seconds')
        self.url=url;self.size=size;self.block_size=block_size;self.max_transfer_bytes=max_transfer_bytes
        self.cache_blocks=cache_blocks;self.timeout=timeout;self.position=0;self.transferred_bytes=0
        self.ranges=[];self._cache=OrderedDict();self._etag=None;self._last_modified=None

    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.position

    def seek(self, offset, whence=0):
        if self.closed:raise ValueError('Reader is closed')
        if type(offset) is not int or whence not in (0,1,2):raise ValueError('Invalid seek')
        target=offset+(0 if whence==0 else self.position if whence==1 else self.size)
        if target<0:raise ValueError('Negative seek')
        self.position=target;return target

    def _block(self, index):
        if index in self._cache:
            self._cache.move_to_end(index);return self._cache[index]
        start=index*self.block_size;end=min(self.size,start+self.block_size)-1;count=end-start+1
        if self.transferred_bytes+count>self.max_transfer_bytes:raise ValueError('HTTP transfer budget exceeded')
        request=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
        with urllib.request.urlopen(request,timeout=self.timeout) as response:
            if response.status!=206:raise ValueError('Server did not honor range; body not read')
            if response.headers.get('Content-Range')!=f'bytes {start}-{end}/{self.size}':raise ValueError('Server range/size differs from requested source')
            if response.headers.get('Content-Encoding','identity')!='identity':raise ValueError('Unexpected content encoding')
            if response.headers.get('Transfer-Encoding') is not None:raise ValueError('Chunked or ambiguous transfer framing is unsupported')
            length=response.headers.get('Content-Length')
            if length is None or int(length)!=count:raise ValueError('Exact bounded Content-Length is required')
            etag=response.headers.get('ETag');modified=response.headers.get('Last-Modified')
            if self.ranges and ((self._etag is not None and etag!=self._etag) or (self._last_modified is not None and modified!=self._last_modified)):
                raise ValueError('Remote archive validator changed during acquisition')
            self._etag=etag;self._last_modified=modified
            data=response.read(count)
            self.transferred_bytes+=len(data)
            if len(data)!=count:raise ValueError('Truncated or oversized range response')
        self.ranges.append({'start':start,'end':end,'bytes':count,'sha256':hashlib.sha256(data).hexdigest(),'etag':etag,'last_modified':modified})
        self._cache[index]=data
        if len(self._cache)>self.cache_blocks:self._cache.popitem(last=False)
        return data

    def read(self, size=-1):
        if self.closed:raise ValueError('Reader is closed')
        if type(size) is not int or size < -1:raise ValueError('Invalid read size')
        size=max(0,self.size-self.position) if size==-1 else min(size,max(0,self.size-self.position))
        if size>self.max_transfer_bytes:raise ValueError('Single read exceeds bounded buffer size')
        result=bytearray()
        while len(result)<size:
            index,offset=divmod(self.position,self.block_size)
            block=self._block(index);part=block[offset:offset+size-len(result)]
            result.extend(part);self.position+=len(part)
        return bytes(result)


def copy_zip_members(reader, members, output, *, max_member_bytes=8_388_608, max_total_bytes=67_108_864):
    """Copy only selected safe files to a new directory, checking ZIP CRCs.

    Caller must establish source access and selection permissions independently.
    Selection is never broadened; any failure leaves no published output.
    """
    if not isinstance(members,list) or not members or any(not isinstance(name,str) for name in members):raise ValueError('Nonempty string ZIP member names required')
    normalized=set()
    for name in members:
        if not isinstance(name,str):raise ValueError('ZIP member name must be a string')
        path=PurePosixPath(name)
        canonical=unicodedata.normalize('NFC',name).casefold()
        if canonical in normalized:raise ValueError('Selected ZIP paths collide on a case-insensitive normalized filesystem')
        normalized.add(canonical)
        if not name or path.as_posix()!=name or path.is_absolute() or '..' in path.parts or '\\' in name or '\0' in name or ':' in name:
            raise ValueError('Unsafe selected ZIP path')
    for value in (max_member_bytes,max_total_bytes):
        if type(value) is not int or value<1:raise ValueError('Positive integer extraction limits required')
    output=Path(output)
    if output.exists():raise FileExistsError(str(output))
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.range-intake-',dir=output.parent))
    try:
        records=[]
        with zipfile.ZipFile(reader) as archive:
            names=[x.filename for x in archive.infolist()]
            selected=[]
            for name in members:
                if names.count(name)!=1:raise ValueError('Selected ZIP member is absent or duplicated')
                info=archive.getinfo(name)
                if info.is_dir() or info.flag_bits&1 or stat.S_ISLNK(info.external_attr>>16):raise ValueError('Selected ZIP member is not an ordinary unencrypted file')
                if info.file_size>max_member_bytes:raise ValueError('ZIP member exceeds size ceiling')
                selected.append(info)
            if sum(x.file_size for x in selected)>max_total_bytes:raise ValueError('Selected ZIP expansion exceeds total ceiling')
            for info in selected:
                payload=archive.read(info)
                if len(payload)!=info.file_size:raise ValueError('ZIP member length mismatch')
                path=staging/info.filename;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
                records.append({'member':info.filename,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'zip_crc32':format(info.CRC,'08x')})
        if output.exists():raise FileExistsError(str(output))
        staging.rename(output)
        return {'members':records,'whole_archive_checksum_verified':False,'selected_member_crc_verified':True,
                'source_url':getattr(reader,'url',None),'expected_archive_bytes':getattr(reader,'size',None),
                'http_bytes_received':getattr(reader,'transferred_bytes',None),'ranges':getattr(reader,'ranges',[])}
    finally:
        if staging.exists():shutil.rmtree(staging)
