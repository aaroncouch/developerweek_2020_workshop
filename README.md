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
  * [Part 1: Creating the Performance Metric Collection Workload](#workshop_guide_pt_1)
  * [Part 2: Creating the Globally Deployed Scouter API Workload](#workshop_guide_pt_2)
  * [Part 3: Installing and Configuring InfluxDB on our VM](#workshop_guide_pt_3)
  * [Part 4: Installing and Configuring Telegraf on our VM](#workshop_guide_pt_4)
  * [Part 5: Installing and Configuring Grafana on our VM](#workshop_guide_pt_5)
  * [Part 6: Exploring our Performance Data!](#workshop_guide_pt_6)

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

<a name="workshop_guide_pt_1"></a>
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

<a name="workshop_guide_pt_2"></a>
### Part 2: Creating the Globally Deployed Scouter API Workload

Let's continue by Deploying the Scouter API globally so we can collect performance metrics from
anywhere that Edge Compute is available.

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

<a name="workshop_guide_pt_3"></a>
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
echo "export INFLUX_USERNAME='admin'" >> ~/.bash_profile
echo "export INFLUX_PASSWORD='changeme'" >> ~/.bash_profile
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

<a name="workshop_guide_pt_4"></a>
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

#### Validate that the Performance Metrics are being Written to InfluxDB

Let's quickly validate that data is being inserted before we proceed to the next part of the
workshop.

Log back into InfluxDB:

```shell
influx
```

Query our `metricsdb` and `ping` measurement for metrics:

```shell
USE "metricsdb";
SHOW MEASUREMENTS;
SELECT * FROM "ping" LIMIT 2;
exit
```

The resulting query will look something like this:

```SQL
> SELECT * FROM "ping" LIMIT 2;
name: ping
time                avg_rtt dst           dst_pop failed loss public_ip      src_pop src_slug
----                ------- ---           ------- ------ ---- ---------      ------- --------
1580487181000000000 1.154   1.1.1.1       Unknown 0      0    151.139.188.43 ams     global-scouter-api-workload-global-ams-0
1580487181000000000 113.432 151.139.87.14 fra     0      0    151.139.188.43 yyz     global-scouter-api-workload-global-yyz-0
```

<a name="workshop_guide_pt_5"></a>
### Part 5: Installing and Configuring Grafana on our VM

At this point in the guide we should almost be ready to start visualizing some data.

#### Installation of Grafana v5.3.4

Let's get Grafana installed so we can start making some dashboards:

```shell
wget https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana-5.3.4-1.x86_64.rpm
sudo yum localinstall grafana-5.3.4-1.x86_64.rpm
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
systemctl status grafana-server
```

Let's also quickly install a plugin that adds a new panel type called `boomtable`:

```shell
sudo grafana-cli plugins install yesoreyeram-boomtable-panel
sudo systemctl restart grafana-server
```

#### Configuration of Grafana within the Web Interface

The `grafana-server` should now be up and running. From your local machine in your web browser
please navigate to:

**NOTE**: Please be sure to swap the following example IP address with yours.

http://151.139.188.43:3000/login

![grafana_login](/images/grafana_login.png)

The default login credentials for Grafana are admin/admin. Please change this in the next prompt.

Once you've completed the login process you'll be redirected to your `Home Dashboard`:

![grafana_home_dashboard](/images/grafana_home_dashboard.png)


#### Adding a new data source

Let's add our InfluxDB `metricsdb` as a new data source within Grafana.

From your `Home Dashboard` select `Add data source`. Here we can fill out the settings for
our local instance of InfluxDB and our `metricsdb` database:

![grafana_add_new_data_source](/images/grafana_add_new_data_source.png)

After completing this step; navigate back to your `Home Dashboard`.

#### Creating our First Dashboard

Let's add our very first dashboard so we can actually dive into our Performance metrics!

From your `Home Dashboard` select `New dashboard`. You will be redirected to the following page:

![grafana_new_dashboard](/images/grafana_new_dashboard.png)

Select the `Boom Table` panel type and then edit the panel:

![grafana_boom_table_edit](/images/grafana_boom_table_edit.png)

From the edit page for our panel change the `Data Souce` to `metricsdb`:

![grafana_boom_table_data_source](/images/grafana_boom_table_data_source.png)

Now let's `Toggle Edit Mode` so we can write raw InfluxQL:

![grafana_boom_table_toggle_edit_mode](/images/grafana_boom_table_toggle_edit_mode.png)

Time to query our database! Let's add the following simple query to get the average ICMP ping
latency between all of our `Global Scouter API Workload` instances:

```SQL
SELECT MEAN("avg_rtt") FROM "ping" WHERE $timeFilter AND "dst_pop" != 'Unknown' GROUP BY "dst_pop", "src_pop";
```

Let's also setup the `ALIAS BY` field to be used in table formatting next:

```shell
$tag_src_pop.$tag_dst_pop
```

Once added your query should look like this:

![grafana_boom_table_latency_metric_query](/images/grafana_boom_table_latency_metric_query.png)

Navigate to the `Patterns` tab and modify the following field values:

* *Pattern*
  * **Row Name**: `_0_`
  * **Col Name**: `_1_`
* *Stats*
  * **Stat**: `Current`
  * **Format**: `milliseconds (ms)`
  * **Decimals**: `0`
* *Thresholds*
  * **Thresholds**: `250,500,1000`
  * **Change BG Color based on thresholds?**: :white_check_mark:
  * **BG Colors for thresholds**: `green|yellow|orange|red`

Once modified our `Patterns` tab should look like this:

![grafana_boom_table_patterns](/images/grafana_boom_table_patterns.png)

Once completed navigate to the `General` tab take a look at that data!

![grafana_boom_table_finished](/images/grafana_boom_table_finished.png)

Awesome! We've essentially created a Ping Latency Mesh Table where we can view the average
latency between any given Edge Compute source PoP and Destination PoP.

We can now tell where we perform well and where we don't.

Let's proceed with adding some more visualizations and dashboards in the next section.

#### Importing Dashboard JSON Models

Included in this workshop guide are two completely built Grafana dashboard JSON models.

1. [edge-compute-performance-mesh.json](/resources/edge-compute-performance-mesh.json)
2. [mesh-detail.json](/resources/mesh-detail.json)

Let's go ahead and import both of these to our Grafana instance.

From your `Home Dashboard` select the `Create` option and `Import` in the left panel:

![grafana_create_import](/images/grafana_create_import.png)

You should be presented with the following page:

![grafana_dashboard_import](/images/grafana_dashboard_import.png)

Go ahead and paste the contents of [edge-compute-performance-mesh.json](/resources/edge-compute-performance-mesh.json) into the `Or paste JSON` text box and select `Load`.

You should now see the following:

![grafana_dashboard_import_load](/images/grafana_dashboard_import_load.png)

Go ahead and select `Import`.

You should now see the same exact panel we created in the previous section but also an additional
one, the `EdgeCompute Packet Loss Mesh`. This is very similar to our ping latency mesh but the
metric being visualized this time is packet loss.

![grafana_edge_compute_performance_mesh](/images/grafana_edge_compute_performance_mesh.png)

Please follow the same exact steps for the [mesh-detail.json](/resources/mesh-detail.json) JSON
model. Once completed you should have an additional dashboard called `Mesh Detail`:

![grafana_mesh_detail](/images/grafana_mesh_detail.png)

<a name="workshop_guide_pt_6"></a>
### Part 6: Exploring our Performance Data!

Our entire monitoring stack is now up and running and we're successfully visualizing our
performance data being pulled remotely from around the globe via Scouter, or at least I hope we are!

Let's do a quick deep dive into a small set of data. Let's say that I want to see how well the
interconnectivity between our HKG (Hong Kong) and our JFK (New York) instances look:

![grafana_explore_mesh_hkg_jfk](/images/grafana_explore_mesh_hkg_jfk.png)

Clicking on the cell will redirect us to our `Mesh Detail` page with both the correct `src_pop`
and `dst_pop` variables set to `hkg` and `jfk` respectively:

![grafana_export_mesh_detail_hkg_jfk](/images/grafana_export_mesh_detail_hkg_jfk.png)

On the `Mesh Detail` page we can explore our hisorical ping latency and packet loss data and
see how well we performed over time!
