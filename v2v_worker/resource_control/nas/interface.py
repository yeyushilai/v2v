# -*- coding: utf-8 -*-


class NFSInterface(object):

    def __init__(self, address):
        if not address.startswith('nfs://'):
            address = 'nfs://' + address
        import libnfs
        self.nfs = libnfs.NFS(address)

    def readfile(self, path, mode='r'):
        nfs_file = self.nfs.open(path, mode)
        data = nfs_file.read()
        nfs_file.close()
        return data

    def writefile(self, path, data, mode='w'):
        nfs_file = self.nfs.open(path, mode)
        data = nfs_file.write(data)
        return data

    def listdirs(self, path):
        dirs = self.nfs.listdir(path)
        tmp_dirs = list()
        for dir in dirs:
            if not (dir == '.' or dir == '..'):
                tmp_dirs.append(dir)
        return tmp_dirs
