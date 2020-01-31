# DeveloperWeek 2020 Workshop

This workshop will cover the steps required to deploy a lightweight global monitoring stack via
StackPath's Edge Compute platform and recently open-sourced API project, Scouter.

* [Getting Started](#getting_started)
  * [Prerequisities](#prerequisities)
  * [Core Components](#core_components)
    * [StackPath Edge Compute](#edge_compute)
    * [Scouter API](#scouter_api)
    * [Telegraf](#telegraf)
    * [InfluxDB](#influxdb)
    * [Grafana](#grafana)
* [Workshop Guide](#workshop_guide)

<a name="getting_started"></a>
## Getting Started

These instructions will cover the deployment of a lightweight monitoring stack via StackPath's
Edge Compute platform.

<a name="getting_started"></a>
### Prerequisities

To follow this guide please register and create a StackPath 2.0 account.

* [StackPath](https://control.stackpath.com/register/)

<a name="core_components"></a>
### Core Components

The following section will be a breif overview of the core coponents of this workshop and how
they will be used to develop our monitoring stack.

* [StackPath Edge Compute](https://www.stackpath.com/products/edge-computing/)
* [Scouter API v1.0.0](https://hub.docker.com/r/aaroncouch/scouter_api)
* [InfluxDB v1.7.1](https://www.influxdata.com/products/influxdb-overview/)
* [Telegraf v1.8.3](https://www.influxdata.com/time-series-platform/telegraf/)
* [Grafana v5.3.4](https://grafana.com/grafana/)

<a name="edge_compute"></a>
#### StackPath Edge Compute

StackPath's Edge Compute platform will allow us to quickly and easily deploy all components of our
monitoring stack on a global scale.

In this workshope Edge Compute will be utilized in two ways:

1. A VM workload for the collection, recording and visualization of Performance metrics.
2. A globally deployed container workload using the Scouter API.

<a name="scouter_api"></a>
#### Scouter API

The Scouter API project will allow us to perform remote network diagnostics, in this case
an ICMP ping to record network latencies values over time.

<a name="telegraf"></a>
#### Telegraf

Telegraf will be our collection agent. It will execute a custom script to perform ping tests
from all of our Scouter API instances deployed in our Edge Compute workload and write the resulting
data to InfluxDB.

<a name="influxdb"></a>
#### InfluxDB

InfluxDB will be our time series datastore. Since InfluxDB work very well with Telegraf and Grafana,
the choice was very easy to make.

<a name="grafana"></a>
#### Grafana

Grafana will act as the visualization portion of our monitoring stack. With InfluxDB compatability
built-in we can easily jump in to visualizing our performance data.

<a name="workshop_guide"></a>
## Workshop guide

Before proceeding please be sure to review the [Getting Started](#getting_started) section of this
README to ensure that all [Prerequisities](#prerequisities) are met and that you understand the
[Core Components](#core_components) of this guide.

### Part 1: Creating the Performance Metric Collection Workload

Let's begin our journey by creating our first Edge Compute workload within the StackPath 2.0
portal.

#### Creating the Workload

![vm_name_and_type](/images/vm_name_and_type.png)

![vm_workload_settings](/images/vm_workload_settings.png)

![vm_spec_storage_and_deployment](/images/vm_spec_storage_and_deployment.png)

![vm_quick_overview_scheduling](/images/vm_quick_overview_scheduling.png)

![vm_quick_overview_running](/images/vm_quick_overview_running.png)

![vm_information](/images/vm_information.png)

#### Creating an Inbound Network Policy to Restrict Access to Grafana

![vm_default_network_policy](/images/vm_default_network_policy.png)

One easy way to get your public IP is by running the following:
```shell
curl -4 icanhazip.com
```

Take the resulting IP address and fill out the following:

![vm_grafana_network_policy](/images/vm_grafana_network_policy.png)

#### Logging into our Workload Instance

```shell
ssh centos@151.139.188.43
```

#### Cloning the Workshop Repository and Setting Up Additional Dependencies

```shell
sudo yum install git wget python3
git clone https://github.com/aaroncouch/developerweek_2020_workshop.git
sudo python3 -m pip install requests
```

### Part 2: Creating the Globally Deployed Scouter API Workload

#### Creating the Workload

![scouter_name_and_type](/images/scouter_name_and_type.png)

![scouter_workload_settings](/images/scouter_workload_settings.png)

![scouter_spec_storage_and_deployment](/images/scouter_spec_storage_and_deployment.png)

![scouter_quick_overview_status](/images/scouter_quick_overview_status.png)

### Modifying the Default Inbound Network Policy to Restrict Access to Grafana

Let's go ahead and quickly modify the default inbound network policy that allows port 8000/TCP
to restrict this access to our previously created VM.

![scouter_default_network_policy_edit](/images/scouter_default_network_policy_edit.png)

![scouter_telegraf_network_policy](/images/scouter_telegraf_network_policy.png)

### From our Metric Collection VM; Validate that Scouter is Accessible and Working

Proceed to your "Global Scouter API Workload" overview page and select a few of the
public IP address of the running Scouter API instances and run the following from your
"Metric Collection Workload" VM:

**NOTE**: Please be sure to swap the following example IP address and example secret with yours.

```shell
curl -sSXGET -H "Authorization: secret" "http://151.139.47.79:8000/api/v1.0/status"
```

### Part 3: Installing and Configuring InfluxDB on our VM

Back to our VM. Let's continue there by installing and configuring InfluxDB so Telegraf has
something to write to.

#### Installation of InfluxDB v1.7.1

```shell
wget https://dl.influxdata.com/influxdb/releases/influxdb-1.7.1.x86_64.rpm
sudo yum localinstall influxdb-1.7.1.x86_64.rpm
sudo systemctl start influxdb
systemctl status influxdb
```

#### Setup Database and Users/Permissions

Login to Influx so we can start interacting with it:

```shell
influx
```

Once logged in let's create our database for storing performance metrics and setup users
and permissions:

```shell
CREATE DATABASE "metricsdb";
CREATE USER "admin" WITH PASSWORD 'changeme' WITH ALL privileges;
CREATE USER "telegraf_wo" WITH PASSWORD 'changeme';
CREATE USER "grafana_ro" WITH PASSWORD 'changeme';
GRANT WRITE ON "metricsdb" TO "telegraf_wo";
GRANT READ ON "metricsdb" TO "grafana_ro";
exit
```

Once completed let's quickly add our admin credentials to our environment:

```shell
echo "export INFLUX_USERNAME=admin" >> ~/.bash_profile
echo "export INFLUX_PASSWORD=[REDACTED]" >> ~/.bash_profile
source ~/.bash_profile
```

#### Configuring HTTP Authentication

InfluxDB has HTTP auth disabled by default. Let's enable that:

```shell
sudo vi /etc/influxdb/influxdb.conf
```

Locate the following section and ensure that `# auth-enabled = false` is uncommented and set to `true`:

```YAML
[http]
  ...
  auth-enabled = true
```

Restart the service for good measure:

```shell
sudo systemctl restart influxdb
```

### Part 4: Installing and Configuring Telegraf on our VM

Let's get the Telegraf server agent installed so we can actually start pulling peformance metrics
from the Scouter API.

#### Installation of Telegraf v1.8.3

```shell
wget https://dl.influxdata.com/telegraf/releases/telegraf-1.8.3-1.x86_64.rpm
sudo yum localinstall telegraf-1.8.3-1.x86_64.rpm
```

#### Configuration of Performance Metric Collection

Before we start the agent, let's get quickly setup to run the custom Scouter data collection script.

First let's add a few environment variables to `/etc/default/telegraf` so we don't have to expose
those in our telegraf.conf:

```shell
sudo vi /etc/default/telegraf
```

**NOTE**: Please be sure to swap out the placeholder values seen below appropriately.

```shell
SP_STACK_ID='<YOUR_STACKPATH_STACK_ID>'
SP_API_CLIENT_ID='<YOUR_STACKPATH_API_CLIENT_ID>'
SP_API_CLIENT_SECRET='<YOUR_STACKPATH_CLIENT_SECRET>'
SCOUTER_WORKLOAD_ID='<YOUR_SCOUTER_WORKLOAD_ID>'
SCOUTER_SECRET='<YOUR_SCOUTER_SECRET>'
```

For this workshop I've written a simple Python3 script that interacts with the SP2.0 API to pull
actively running Scouter instances for the given workload and executes ICMP pings for you.

[If you have a moment please review the custom script.](/resources/scouter_ping.py)

Let's go ahead and copy this custom script over to `/usr/bin/` so Telegraf can access it:

```shell
sudo cp ~/developerweek_2020_workshop/resources/scouter_ping.py /usr/bin/
```

Now let's setup `/etc/telegraf/telegraf.conf` so we can actually start collecting some performance
metrics from our Scouter API workload!

Provided in this repository's resources is a preconfigured [telegraf.conf](/resources/telegraf.conf)
file. Please take a moment to review its contents and make any appropriate changes:

```shell
vi ~/developerweek_2020_workshop/resources/telegraf.conf
```

```YAML
[global_tags]
[agent]
  # Run inputs every 60 seconds.
  interval = "60s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "10s"
  flush_jitter = "0s"
  precision = ""
  debug = false
  quiet = false
  # Log output to a file.
  logfile = "/var/log/telegraf/telegraf.log"
  hostname = ""
  omit_hostname = true

# Configuration to output our metrics to InfluxDB.
[[outputs.influxdb]]
  database = "metricsdb"
  # We created the database manually.
  skip_database_creation = true
  # Please be sure to modify these values if changed.
  username = "telegraf_wo"
  password = "changeme"

# Configuration of our custom Scouter API data collection script.
[[inputs.exec]]
    commands = [
      'python3 /usr/bin/scouter_ping.py --stack-id="$SP_STACK_ID" --workload-id="$SCOUTER_WORKLOAD_ID" --client-id="$SP_API_CLIENT_ID" --client-secret="$SP_API_CLIENT_SECRET" --scouter-secret="$SCOUTER_SECRET"',
      'python3 /usr/bin/scouter_ping.py --stack-id="$SP_STACK_ID" --workload-id="$SCOUTER_WORKLOAD_ID" --client-id="$SP_API_CLIENT_ID" --client-secret="$SP_API_CLIENT_SECRET" --scouter-secret="$SCOUTER_SECRET" --dst="1.1.1.1"'
    ]
    timeout = "30s"
    data_format = "influx"

# Configuration of metric data type conversion.
[[processors.converter]]
    # A few fields returned by the custom script need to be floats.
    [processors.converter.fields]
      float = ["avg_rtt", "loss"]
```

Once you're done editing the configuration file; proceed with copying it to `/etc/telegraf/telegraf.conf` and finally start the server agent:

```shell
sudo cp ~/developerweek_2020_workshop/resources/telegraf.conf /etc/telegraf/telegraf.conf
sudo systemctl enable telegraf
sudo systemctl start telegraf
systemctl status telegraf
```

Monitor our on-disk logging to ensure that no errors are present:

```shell
tail -f /var/log/telegraf/telegraf.log
```

### Part 5: Installing and Configuring Grafana on our VM
