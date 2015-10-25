from __future__ import print_function

import sys
import time

from influxdb import InfluxDBClient

data_set = sys.argv[1]

database_host = 'docker.example.com'
#database_host = '149.171.22.31'
database_port = 8086

delay = 0.01
batch = 1.0

def data_samples(name):
    with open(name) as fp:
        # CSV files have four header rows.
        #
        # Row 1: Always has 'SHIMMER' in each column.
        # Row 2: Name of data point.
        # Row 3: Indicator whether is raw or calculated value. (RAW/CAL)
        # Row 4: Units for value. For raw will always be 'no units'.

        # Ignore row 1.

        fp.readline()

        # Create name of data point by normalising name from row 2 and then
        # suffixing it with data type indicator.

        names = [value.strip().replace(' ', '_')
                for value in fp.readline().strip().split(',')]

        indicators = [value.strip()
                for value in fp.readline().strip().split(',')]

        names = ['_'.join(x) for x in zip(names, indicators)]

        # Ignore units.

        fp.readline()

        # No process rows.

        for line in fp.readlines():
            values = [x.strip() for x in line.split(',')]

            sample = {}

            for name, value in zip(names, values):
                if name != '_':
                    sample[name] = value

            yield sample

client = InfluxDBClient(database_host, database_port, 'root', 'root', 'shimmer')

last_offset = 0.0

last_time = time.time()

for sample in data_samples(data_set):
    sample.pop('Timestamp_RAW')

    current_time = time.time()
    now = time.gmtime(current_time)

    timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', now)

    offset = float(sample.pop('Timestamp_CAL')) / 1000.0

    #print(offset)

    next_time = last_time + (offset - last_offset)
    wait = max(0, next_time - current_time)

    print(wait)

    time.sleep(wait)

    last_time = current_time

    #time.sleep(offset - last_offset)

    last_offset = offset

    samples = []

    for name, value in sample.items():
        item = {}
        item['time'] = timestamp
        item['measurement'] = name
        fields = {}
        fields['value'] = float(value)
        item['fields'] = fields
        samples.append(item)

    #print(samples)

    client.write_points(samples)
