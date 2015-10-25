from __future__ import print_function

import sys
import time
import os

from influxdb import InfluxDBClient

data_set = sys.argv[1]

#database_host = 'docker.example.com'
database_host = '149.171.22.31'
database_port = 8086

batch = 1.0

threshold = 0.015

def follow(name):
    "Follow the live contents of a text file."
    pos = 0
    #for block in iter(lambda:stream.read(1024), None):
    residual = ''
    while True:
        stream = open(name, 'r')
        stream.seek(pos)
        block = stream.read(1024)
        if '\n' in block:
            # Only enter this block if we have at least one line to yield.
            # The +[''] part is to catch the corner case of when a block
            # ends in a newline, in which case it would repeat a line.
            #for line in (line+block).splitlines(True)+['']:
            for line in (residual+block).splitlines(True):
                if line.endswith('\n'):
                    yield line
                else:
                    residual = line
                    break
            # When exiting the for loop, 'line' has any remaninig text.
        elif not block:
            # Wait for data.
            print('SLEEP')
            time.sleep(1.0)
        else:
            residual = residual + block
        pos = stream.tell()
        stream.close()
    # The End.

def data_samples(name):
    #fp = follow(open(name, 'rt'))
    fp = follow(name)

    # CSV files have four header rows.
    #
    # Row 1: Always has 'SHIMMER' in each column.
    # Row 2: Name of data point.
    # Row 3: Indicator whether is raw or calculated value. (RAW/CAL)
    # Row 4: Units for value. For raw will always be 'no units'.

    # Ignore row 1.

    fp.next()

    # Create name of data point by normalising name from row 2 and then
    # suffixing it with data type indicator.

    names = [value.strip().replace(' ', '_')
            for value in fp.next().strip().split(',')]

    indicators = [value.strip()
            for value in fp.next().strip().split(',')]

    names = ['_'.join(x) for x in zip(names, indicators)]

    # Ignore units.

    fp.next()

    # Now process rows.

    line = fp.next().strip()

    while True:
        line = line.strip('\r\n')
        values = [x.strip() for x in line.split(',')]

        sample = {}

        for name, value in zip(names, values):
            if name != '_':
                sample[name] = value

        yield sample

        line = fp.next()

client = InfluxDBClient(database_host, database_port, 'root', 'root', 'shimmer')

start_time = time.time()
start_offset = 0.0

try:
    os.unlink('%s.offset' % data_set)

except OSError:
    pass

samples = []

count = 0

for sample in data_samples(data_set):
    now = time.time()

    sample.pop('Timestamp_RAW')

    if not sample:
        continue

    data = sample.pop('Timestamp_CAL')
    if data == '':
        continue

    offset = float(data) / 1000.0

    adjusted_time = start_time + (offset - start_offset)

    print("ADJ", adjusted_time, now)
    if adjusted_time > now + 3.0:
        print("SKIP")
        start_time = now
        start_offset = offset
        continue

    timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

    for name, value in sample.items():
        #if value == '':
        #    print(name, value)
        #    value = '-1'

        item = {}
        item['time'] = timestamp
        item['measurement'] = name
        fields = {}
        fields['value'] = float(value)
        item['fields'] = fields
        samples.append(item)

    #print(samples)

    count += 1

    if count % 10:
        continue

    if samples:
        print(len(samples))
        client.write_points(samples)
        samples = []
