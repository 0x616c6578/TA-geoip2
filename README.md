# TA-geoip2

## Table of contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Upgrade instructions](#upgrade-instructions)
- [Reference material](#reference-material)


## Introduction

MaxMind GeoIP2 offerings provide IP geolocation and proxy detection for a wide range of applications including content customization, advertising, digital rights management, compliance, fraud detection, and security.

This Splunk technology add-on provides a custom search commmand (`geoip`) to query MaxMind GeoIP2 databases for IP address enrichment.

## Prerequisites

- Splunk Enterprise version 8.0 or later, with Python 3.7.  _Splunk Enterprise version 7.x is not supported_.
- Access to one or more of the MaxMind GeoIP2 databases:
    - **City**:  GeoIP2-City.mmdb / GeoLite2-City.mmdb
    - **Anonymous IP (Proxy Detection)**:  GeoIP2-Anonymous-IP.mmdb
    - **ISP**:  GeoIP2-ISP.mmdb
    - **Connection Type**:  GeoIP2-Connection-Type.mmdb
    - **Domain**:  GeoIP2-Domain.mmdb
    - **ASN**:  GeoLite2-ASN.mmdb
    - **Enterprise**:  GeoIP2-Enterprise.mmdb
    > MaxMind provides free versions of some of their databases (GeoLite2), found [here](https://www.maxmind.com/en/geolite2/signup).


## Architecture

The `geoip` command is a distributable streaming command (see [Command types](http://docs.splunk.com/Documentation/Splunk/8.2.2/SearchReference/Commandsbytype)).  The replication settings within [distsearch.conf](default/distsearch.conf) will allow the command to run on indexers.


## Installation

1. Install this TA under `$SPLUNK_HOME/etc/apps`.
2. Copy any available MaxMind GeoIP2 databases to `$SPLUNK_HOME/etc/apps/TA-geoip2/data/databases/`.


## Usage

See [usage](documentation/usage.md) for detailed usage instructions.

**Syntax**:  `geoip [prefix=<string>] [fillnull=<string>] [field=<ip-address-fieldname>] <geoip-databases>`

Where `<geoip-datebases>` is one or more of:  `anonymous_ip`, `asn`, `city`, `connection_type`, `domain`, `enterprise`, `isp`, or `all`.

This will include fields from the requested databases, as defined in the [databases documentation](documentation/databases.md).


## Upgrade instructions

None.

## Reference material

More details about the GeoIP2 Databases can be found on the [MaxMind website](https://www.maxmind.com/en/geoip2-databases).  
