from __future__ import division

import struct
import sys

with open(sys.argv[1], 'rb') as f:
    d = f.read()
    d = list(struct.unpack('>%iI' % (len(d)//4,), d))

sync = []
data = [[], [], [], []]

for i, x in enumerate(d):
    if i % 10000 == 0: print i/len(d)
    b = '{0:025b}'.format(x)
    sync.extend(b[::5][::-1])
    #for i in xrange(4):
    #    data[i].extend(b[1+i::5][::-1])

sync = [1-x for x in map(int, sync)]
for i in xrange(4):
    data[i] = map(int, data[i])

#for i in xrange(100):
#    a = sync[10*i:10*(i+1)]
#    print a#, hex(int(''.join(map(str, a)), 2))

train = map(int, '{0:010b}'.format(0x3a6))
black = map(int, '{0:010b}'.format(0x015))
valid = map(int, '{0:010b}'.format(0x035))
crc   = map(int, '{0:010b}'.format(0x059))

p = 0
while sync[p:p+10]:
    if sync[p:p+10] == train:
        print 'train good'
        p += 10
    elif sync[p:p+10][3:] == [0, 1, 0, 1, 0, 1, 0] and sync[p:p+10][:3] == [1, 0, 1]:
        print 'frame sync - frame start',
        p += 10
        print sync[p:p+10]
        p += 10
    elif sync[p:p+10][3:] == [0, 1, 0, 1, 0, 1, 0] and sync[p:p+10][:3] == [1, 1, 0]:
        print 'frame sync - frame end',
        p += 10
        print sync[p:p+10]
        p += 10
    elif sync[p:p+10][3:] == [0, 1, 0, 1, 0, 1, 0] and sync[p:p+10][:3] == [0, 0, 1]:
        print 'frame sync - line start',
        p += 10
        print sync[p:p+10]
        p += 10
    elif sync[p:p+10][3:] == [0, 1, 0, 1, 0, 1, 0] and sync[p:p+10][:3] == [0, 1, 0]:
        print 'frame sync - line end',
        p += 10
        print sync[p:p+10]
        p += 10
    elif sync[p:p+10] == black:
        print 'black'
        p += 10
    elif sync[p:p+10] == valid:
        print 'valid', p
        p += 10
    elif sync[p:p+10] == crc:
        print 'crc'
        p += 10
    else:
        print 'bad', sync[p:p+10]
        p += 1

#for i in xrange(0, len(d), 2):
#    print '{0:025b} {1:025b}'.format(d[i], d[i+1])
