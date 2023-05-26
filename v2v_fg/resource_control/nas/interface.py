# -*- coding: utf-8 -*-

from libnfs import (
    NFS,

    nfs_init_context,
    nfs_parse_url_dir,
    nfs_mount
)


class NFSClient(NFS):
    def __init__(self, url):
        if not url.startswith('nfs'):
            url = 'nfs://' + url
        self._nfs = nfs_init_context()
        self._url = nfs_parse_url_dir(self._nfs, url)

    def mount(self):
        res = nfs_mount(self._nfs, self._url.server, self._url.path)
        if res == 0:
            return True
        else:
            return False

    def read_file(self, path, mode='r'):
        nfs_fh = self.open(path, mode)
        data = nfs_fh.read()
        nfs_fh.close()
        return data

    def list_dirs(self, path):
        dirs = self.listdir(path)
        ret = []
        for dir in dirs:
            if dir not in ['.', '..', 'lost+found']:
                ret.append(dir)
        return ret

    def stat_file(self, path):
        stat_info = self.stat(path)
        return stat_info

    def write_file(self, path, data, mode='w'):
        nfs_sh = self.open(path, mode)
        data = nfs_sh.write(data)
        nfs_sh.close()
        return data
