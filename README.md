# TA-geoip2

MaxMind GeoIP2 offerings provide IP geolocation and proxy detection for a wide range of applications including content customization, advertising, digital rights management, compliance, fraud detection, and security.

This Splunk technology add-on provides a custom search commmand (`geoip`) to query MaxMind GeoIP2 databases for IP address enrichment.

## Prerequisites 
- Splunk Enterprise version 8.0 or later, with Python 3.7.  _Splunk Enterprise version 7.x is not supported_.
- Access to one or more of the MaxMind GeoIP2 databases:
    - **City**:  GeoIP2-City.mmdb / GeoLite2-City.mmdb
    - **Anonymous IP (Proxy Detection)**:  GeoIP2-Anonymous-IP.mmdb
    - **ISP**:  GeoIP2-ISP.mmdb
    - **Domain**:  GeoIP2-Domain.mmdb
    - **Connection Type**:  GeoIP2-Connection-Type.mmdb


## Installation

1. Install this TA under `$SPLUNK_HOME/etc/apps`.
2. Copy any available MaxMind GeoIP2 databases to `$SPLUNK_HOME/etc/apps/TA-geoip2/data/databases/`.

<br>

## Usage

See [usage](documentation/usage.md) for detailed usage instructions.

**Syntax**:  `geoip [prefix=<string>] [field=<ip-address-fieldname>] <geoip-databases>`

Where `<geoip-datebases>` is one or more of:  `anonymous_ip`, `city`, `connection_type`, `domain`, `isp`, or `all`.

This will include fields from the requested databases, as defined in the [databases documentation](documentation/databases.md).
