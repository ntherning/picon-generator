#!/usr/bin/env python3

import os
import re
import sys
import argparse


parser = argparse.ArgumentParser(description='Generates picon files from svg/png originals at https://gitlab.com/picons/picons')
parser.add_argument('-s','--size', help='Size of box to fit logos in, e.g. 100x50 for a 100 by 50 pixels box', required=True)
parser.add_argument('-l','--lamedb', help='Path to the Enigma2 lamedb file', required=True)
parser.add_argument('-i','--logos', help='Path to where the input logo files can be found. Typically the build-source/logs/ folder of a clone of https://gitlab.com/picons/picons.', required=True)
parser.add_argument('-d','--target', help='Path to where the finished logos will be stored', required=True)
parser.add_argument('-m','--custom-mappings', help='Path to a custom file mapping channel names to logo file name', required=False)
args = vars(parser.parse_args())

size = args['size']
lamedb_path = args['lamedb']
logos_path = args['logos']
target_path = args['target']
custom_mappings_file = args['custom_mappings']
if not re.match('[0-9]+x[0-9]+', size):
    sys.exit('Size "{}" does not match expected WxH'.format(size))
if not os.path.isfile(lamedb_path):
    sys.exit('lamedb file "{}" does not exist'.format(lamedb_path))
if not os.path.isdir(logos_path):
    sys.exit('Logos path "{}" does not exist'.format(logos_path))
if not os.path.isdir(target_path):
    sys.exit('Target path "{}" does not exist'.format(target_path))


# The code for parsing lamedb files (the Enigma2 class and Transponder
# classes) have been copied from
# https://github.com/spacedentist/enigma2-bouqueteditor/blob/master/enigma2.py
# and adapted.

class JsonSerialisableObject(object):
    def __init__(self, **kw):
        for key in self._json_fields:
            if not hasattr(self, key):
                setattr(self, key, kw.get(key))

    @property
    def data(self):
        fields = ((i, getattr(self, i, None)) for i in self._json_fields)
        return dict((k, _serialise(v)) for k, v in fields if v is not None)

    def __repr__(self):
        return '<{0} {1!r}>'.format(self.__class__.__name__, self.data)

class JsonSerialisableObjectWithId(JsonSerialisableObject):
    def __init__(self, id, **kw):
        self.id = id
        JsonSerialisableObject.__init__(self, **kw)

    def __repr__(self):
        return '<{0} {1!r} {2!r}>'.format(self.__class__.__name__, self.id, self.data)

class Transponder(JsonSerialisableObjectWithId):
    _json_fields = 'type medium namespace tsid nid freq symbrate pol fec pos inv flags medium modulation rolloff pilot'.split()
    type = 'transponder'

    @staticmethod
    def find(transponders, namespace, tsid, nid):
        for transponder in transponders.values():
            if (transponder.namespace == namespace and
                transponder.tsid == tsid and
                transponder.nid == nid):
                return transponder

class SatelliteTransponder(Transponder):
    def __init__(self, id, medium='s', **kw):
        Transponder.__init__(self, id, medium=medium, **kw)

class CableTransponder(Transponder):
    def __init__(self, id, medium='c', **kw):
        Transponder.__init__(self, id, medium=medium, **kw)

class Service(JsonSerialisableObjectWithId):
    _json_fields = 'type sid transponder servicetype number name extra'.split()
    type = 'service'

class Enigma2(object):

    def __init__(self):
        self.transponders = {}
        self.services = {}

    def load(self, location):
        ## read lamedb file

        services = self.services = {}
        transponders = self.transponders = {}

        f = open(location)
        assert(f.readline() == 'eDVB services /4/\n')
        assert(f.readline() == 'transponders\n')
        while True:
            line = f.readline()
            if not line or line == 'end\n':
                break
            line2, line3 = f.readline(), f.readline()
            assert line3 == '/\n'
            info = line.strip().split(':')
            medium, info2 = line2.strip().split()
            info2 = info2.split(':')
            if medium == 's':
                t = SatelliteTransponder(
                    id = 't{0}'.format(len(self.transponders)),
                    namespace = int(info[0], 16),
                    tsid = int(info[1], 16),
                    nid = int(info[2], 16),
                    freq = int(info2[0]),
                    symbrate = int(info2[1]),
                    pol = int(info2[2]),
                    fec = int(info2[3]),
                    pos = int(info2[4]),
                    inv = int(info2[5]),
                    flags = int(info2[6]),
                    system = int(info2[7]) if len(info2)>=11 else None,
                    modulation = int(info2[8]) if len(info2)>=11 else None,
                    rolloff = int(info2[9]) if len(info2)>=11 else None,
                    pilot = int(info2[10]) if len(info2)>=11 else None,
                )
            elif medium == 'c':
                t = CableTransponder(
                    id = 't{0}'.format(len(self.transponders)),
                    namespace = int(info[0], 16),
                    tsid = int(info[1], 16),
                    nid = int(info[2], 16),
                    freq = int(info2[0]),
                    symbrate = int(info2[1]),
                    inv = int(info2[2]),
                    modulation = int(info2[3]),
                    fec = int(info2[4]),
                    flags = int(info2[5]),
                )
            else:
                sys.stderr.write("Unsupported medium {0!r}\n".format(medium))
                continue
            self.transponders[t.id] = t

        assert(f.readline() == 'services\n')
        while True:
            line = f.readline()
            if not line or line == 'end\n':
                break
            line2, line3 = f.readline(), f.readline()
            info = line.strip().split(':')
            name = line2.strip() #.decode('utf8')
            t = Transponder.find(self.transponders,
                    namespace = int(info[1], 16),
                    tsid = int(info[2], 16),
                    nid = int(info[3], 16),
                    )
            if t is None:
                sys.stderr.write('Service {0!r} references undefined transponder\n'.format(name))
                continue
            s = Service(
                id = 's{0}'.format(len(self.services)),
                sid = int(info[0], 16),
                transponder = t,
                servicetype = int(info[4]),
                number = int(info[5]),
                name = name,
                extra = line3.strip() #.decode('utf8'),
            )
            self.services[s.id] = s

    def get_service_desc(self, s):
        if not isinstance(s, Service):
            s = self.service[s]
        t = s.transponder
        return '1:0:1:{0:X}:{1:X}:{2:X}:{3:X}:0:0:0:'.format(s.sid, t.tsid, t.nid, t.namespace)


e = Enigma2()
e.load(lamedb_path)

custom_mappings = {}
if custom_mappings_file:
    with open(custom_mappings_file) as f:
        custom_mappings = dict(map(lambda l: l.split('='), f.read().splitlines()))

for service in e.services.values():
    custom_mapping = custom_mappings[service.name] if service.name in custom_mappings else None
    if custom_mapping == 'ignored':
        continue

    if custom_mapping:
        candidates_no_ext = [custom_mapping]
    else:
        basename1 = re.sub('[^a-z0-9]', '', service.name.lower().replace('&', 'and').replace('+', 'plus').replace('*', 'star'))
        basename2 = re.sub('[^a-z0-9_]', '', service.name.lower().replace('&', 'and').replace('+', 'plus').replace('*', 'star').replace(' ', '_').replace('/', '_'))
        basename3 = re.sub('hd$', '', basename1)
        basename4 = re.sub('_hd$', '', basename2)
        basenames = [basename1, basename2, basename3, basename4]
        extensions = ['.light.svg', '.light.png', '.default.svg', '.default.png']
        candidates_no_ext = [a + b for a in basenames for b in extensions]
    candidates = list(map(lambda c: os.path.join(logos_path, c), candidates_no_ext))

    source = (list(filter(os.path.isfile, candidates)) + [None])[0]
    if source:
        target = os.path.join(target_path, e.get_service_desc(service)[0:-1].replace(':','_') + '.png')
        if not os.path.isfile(target):
            cmd = 'convert -background transparent -gravity center -thumbnail {} -extent {} "{}" "{}"'.format(size, size, source, target)
            print(cmd)
            os.system(cmd)
    else:
        sys.stderr.write('No logo for channel "{}" found\n'.format(service.name))
