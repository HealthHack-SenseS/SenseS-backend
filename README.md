Products Used
-------------

InfluxDB - Time Series Database

* https://influxdb.com

Grafana - Data Visualisation Tool

* http://grafana.org

Docker - Container Hosting Tool

* http://www.docker.com

Local Development Setup
-----------------------

Using Docker.

Run InfluxDB:

```
docker run -d -p 8083:8083 -p 8086:8086 --expose 8090 --expose 8099 -e PRE_CREATE_DB=shimmer tutum/influxdb
```

This will create an initial database called ``shimmer``.

No storage is being mounted, so at this point data would be lost it container
restarted. This can be addressed by mounting external volume on ``/data``.

Run Grafana:

```
docker run -i -d  -p 3000:3000 grafana/grafana
```

Need to create a data source point Grafana at local InfluxDB. See:

![Data Source Configuration](GrafanaDataSourceSetup.jpg "Data Source Configuration")

Password for InfluxDB is default of ``root``.

Grafana dashboard configuration can be found in [shimmer-grafana-dashboard.json](shimmer-grafana-dashboard.json).

![Shimmer Dashboard](shimmer-grafana-dashboard.jpg "Shimmer Dashboard")

Loading of Data
---------------

Shimmer data from final CSV file can be replayed as live from current time
using script [upload-from-static-csv.py](upload-from-static-csv.py). Run as:

```
python upload-from-static-csv.py static-data.csv
```

To capture live data from Shimmer, use Windows Shimmer client to save to
CSV file. Then run script [upload-from-live-csv.py](upload-from-live-csv.py)
at same time as:

```
python upload-from-live-csv.py live-data.csv
```

This uses fact that Windows Shimmer client deals with bluetooth to talk 
to Shimmer, avoiding initial need to write dedicated bluetooth client from
scratch.

