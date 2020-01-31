# DeveloperWeek 2020 Workshop

This workshop will cover the steps required to deploy a lightweight global monitoring stack via
StackPath's Edge Compute platform and recently open-sourced API project, Scouter.

* [Getting Started](#getting_started)
  * [Prerequisities](#prerequisities)

<a name="getting_started"></a>
## Getting Started

These instructions will cover the deployment of a lightweight monitoring stack via StackPath's
Edge Compute platform.

<a name="getting_started"></a>
### Prerequisities

To follow this guide please register and create a StackPath 2.0 account.

* [StackPath](https://control.stackpath.com/register/)

### Core Components

The following section will be a breif overview of the core coponents of this workshop and how
they will be used to develop our monitoring stack.

#### StackPath Edge Compute

StackPath's Edge Compute platform will allow us to quickly and easily deploy all components of our
monitoring stack on a global scale.

In this workshope Edge Compute will be utilized in two ways:

1. A VM workload for the collection, recording and visualization of Performance metrics.
2. A globally deployed container workload using the Scouter API.

#### Scouter API

The Scouter API project will allow us to perform remote network diagnostics, in this case
an ICMP ping to record network latencies values over time.

#### Telegraf

Telegraf will be our collection agent. It will execute a custom script to perform ping tests
from all of our Scouter API instances deployed in our Edge Compute workload and write the resulting
data to InfluxDB.

#### InfluxDB

InfluxDB will be our time series datastore. Since InfluxDB work very well with Telegraf and Grafana,
the choice was very easy to make.

#### Grafana

Grafana will act as the visualization portion of our monitoring stack. With InfluxDB compatability
built-in we can easily jump in to visualizing our performance data.


## Workshop guide

Before proceeding please be sure to review the [Getting Started](#getting_started) section of this
README to ensure that all prerequisities are met and that you understand the components of this guide.
