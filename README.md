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

#### Creating the Workload.

![create_workload_start](/images/create_workload_start.png)

![vm_name_and_type](/images/vm_name_and_type.png)

![vm_workload_settings](/images/vm_workload_settings.png)

![vm_spec_storage_and_deployment](/images/vm_spec_storage_and_deployment.png)

![create_workload_finish](/images/create_workload_finish.png)

![vm_quick_overview_scheduling](/images/vm_quick_overview_scheduling.png)

![vm_quick_overview_running](/images/vm_quick_overview_running.png)

![vm_information](/images/vm_information.png)

### Part 2: Creating the Globally Deployed Scouter API Workload

### Part 3: Installing and Configuring InfluxDB on our VM

### Part 4: Installing and Configuring Telegraf on our VM

### Part 5: Installing and Configuring Grafana on our VM
