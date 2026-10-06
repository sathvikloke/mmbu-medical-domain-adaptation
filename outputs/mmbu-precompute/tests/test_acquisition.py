import contextlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import io
from pathlib import Path
import tempfile
import threading
import unittest
import zipfile


def api():
    from mmbu_prep.acquisition import HTTPRangeReader, copy_zip_members
    return HTTPRangeReader,copy_zip_members


@contextlib.contextmanager
def server(payload, *, ignore_range=False, wrong_range=False, truncate=False, omit_length=False, chunked=False):
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def do_GET(self):
            a,b=map(int,self.headers['Range'][6:].split('-'));body=payload[a:b+1]
            self.send_response(200 if ignore_range else 206)
            self.send_header('Content-Range',f'bytes {a+int(wrong_range)}-{b}/{len(payload)}')
            if not omit_length:self.send_header('Content-Length',str(len(body)))
            if chunked:self.send_header('Transfer-Encoding','chunked')
            self.end_headers()
            if chunked:self.wfile.write(b'5\r\nabcde\r\n0\r\n\r\n')
            else:self.wfile.write(body[:-1] if truncate else body)
            self.close_connection=True
        def log_message(self,*args):pass
    http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{http.server_port}/fixture.zip'
    finally:http.shutdown();http.server_close();thread.join()


class RangeTests(unittest.TestCase):
    def test_seek_read_cache_budget_and_eof(self):
        Reader,_=api()
        with server(b'0123456789abcdef') as url,Reader(url,16,block_size=4,max_transfer_bytes=12) as reader:
            self.assertEqual(reader.read(3),b'012');self.assertEqual(reader.read(3),b'345')
            reader.seek(-2,2);self.assertEqual(reader.read(),b'ef')
            self.assertEqual(reader.transferred_bytes,12)
            reader.seek(0);self.assertEqual(reader.read(2),b'01')
            reader.seek(8)
            with self.assertRaises(ValueError):reader.read(1)

    def test_server_must_honor_exact_range_and_length(self):
        Reader,_=api()
        for opts in ({'ignore_range':True},{'wrong_range':True},{'truncate':True}):
            with self.subTest(opts=opts),server(b'abcdefgh',**opts) as url,Reader(url,8,block_size=4) as reader:
                with self.assertRaises((ValueError,OSError)):reader.read(2)

    def test_invalid_seek_size_or_budget_rejected(self):
        Reader,_=api()
        for size in (0,-1,True):
            with self.assertRaises(ValueError):Reader('https://example.invalid/x',size)
        with server(b'ab') as url,Reader(url,2) as reader:
            with self.assertRaises(ValueError):reader.seek(-1)
            with self.assertRaises(ValueError):reader.read(-2)


class ZipTests(unittest.TestCase):
    def archive(self,members):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for name,data in members:z.writestr(name,data)
        return out.getvalue()

    def test_only_explicit_safe_members_are_copied_with_crc_and_hashes(self):
        Reader,copy=api();payload=self.archive([('train/a.jpg',b'raw a'),('train/b.jpg',b'raw b')])
        with server(payload) as url,tempfile.TemporaryDirectory() as d,Reader(url,len(payload),block_size=64) as reader:
            out=Path(d)/'images';report=copy(reader,['train/a.jpg'],out)
            self.assertEqual((out/'train/a.jpg').read_bytes(),b'raw a')
            self.assertFalse((out/'train/b.jpg').exists())
            self.assertEqual(report['members'][0]['bytes'],5)
            self.assertFalse(report['whole_archive_checksum_verified'])
            with self.assertRaises(FileExistsError):copy(reader,['train/a.jpg'],out)

    def test_missing_unsafe_duplicate_or_oversized_selection_never_publishes(self):
        Reader,copy=api();payload=self.archive([('train/a.jpg',b'a'*100),('../escape',b'bad')])
        for selection,kwargs in [(['missing'],{}),(['../escape'],{}),(['train/a.jpg','train/a.jpg'],{}),(['train/a.jpg'],{'max_member_bytes':50})]:
            with self.subTest(selection=selection,kwargs=kwargs),server(payload) as url,tempfile.TemporaryDirectory() as d,Reader(url,len(payload),block_size=64) as reader:
                out=Path(d)/'result'
                with self.assertRaises((ValueError,KeyError)):copy(reader,selection,out,**kwargs)
                self.assertFalse(out.exists())

    def test_aliases_and_case_collisions_are_rejected_before_publication(self):
        Reader,copy=api()
        for names in [('a/b.txt','a//b.txt'),('a/b.txt','a/./b.txt'),('a/B.txt','A/b.TXT')]:
            payload=self.archive([(names[0],b'first'),(names[1],b'second')])
            with server(payload) as url,tempfile.TemporaryDirectory() as d,Reader(url,len(payload),block_size=64) as reader:
                out=Path(d)/'result'
                with self.assertRaises(ValueError):copy(reader,list(names),out)
                self.assertFalse(out.exists())

    def test_unbounded_response_is_rejected_without_consuming_budget(self):
        Reader,_=api()
        with server(b'abcd',omit_length=True) as url,Reader(url,4,block_size=4,max_transfer_bytes=4) as reader:
            with self.assertRaises(ValueError):reader.read(4)
            self.assertEqual(reader.transferred_bytes,0)

    def test_conflicting_chunked_framing_cannot_exceed_byte_cap(self):
        Reader,_=api()
        with server(b'abcd',chunked=True) as url,Reader(url,4,block_size=4,max_transfer_bytes=4) as reader:
            with self.assertRaises(ValueError):reader.read(4)
            self.assertLessEqual(reader.transferred_bytes,4)
