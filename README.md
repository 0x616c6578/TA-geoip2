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
    - **Connection** Type:  GeoIP2-Connection-Type.mmdb


## Installation

1. Install this TA under `$SPLUNK_HOME/etc/apps`.
2. Copy any available MaxMind GeoIP2 databases to `$SPLUNK_HOME/etc/apps/TA-geoip2/data/databases/`.

<br>

## Usage

See [usage](documentation/usage.md) for detailed usage instructions.

**Syntax**:  `geoip [prefix=<string>] [field=<ip-address-fieldname>] <geoip-databases>`

Where `<geoip-datebases>` is one or more of:  `anonymous_ip`, `city`, `connection_type`, `domain`, `isp`, or `all`.

This will include fields from the requested databases, as defined below.



## Databases
The following attributes (fields) may be extracted from the GeoIP2 databases:

### City
_Determine the country, subdivisions (regions), city, and postal code associated with IPv4 and IPv6 addresses worldwide._


| field | Description |
| :-  | :- |
| country |  The name of the country. |
| country.code | The two-character [ISO 3166-1](http://en.wikipedia.org/wiki/ISO_3166-1) alpha code for the country. |
| region | The name of the subdivision (region). |
| region.code | This is a string up to three characters long containing the subdivision portion of the [ISO 3166-2 code](http://en.wikipedia.org/wiki/ISO_3166-2). |
| city | The name of the city. |
| location.latitude | The approximate latitude of the location associated with the IP address. This value is not precise and should not be used to identify a particular address or household. |
| location.longitude |  The approximate longitude of the location associated with the IP address. This value is not precise and should not be used to identify a particular address or household. |
| postal.code | The postal code of the location. Postal codes are not available for all countries. In some countries, this will only contain part of the postal code. |
| network | The network associated with the record. In particular, this is the largest network where all of the fields besides ip_address have the same value. |


### Anonymous IP (Proxy Detection)

_VPN, hosting, and proxy detection for geoblocking, geofencing, geomarketing, and security and risk applications._

| field | Description |
| :-  | :- |
| is_anonymous | This is true if the IP address belongs to any sort of anonymous network. |
| is_anonymous_vpn | This is true if the IP address is registered to an anonymous VPN provider. |
| is_hosting_provider |  This is true if the IP address belongs to a hosting or VPN provider. |
| is_public_proxy | This is true if the IP address belongs to a public proxy. |
| is_residential_proxy | This is true if the IP address is on a suspected anonymizing network and belongs to a residential ISP. |
| is_tor_exit_node | This is true if the IP address is a Tor exit node. |
| network | The network associated with the record. In particular, this is the largest network where all of the fields besides ip_address have the same value. |

### ISP

_Determine the Internet Service Provider, Registering Organization, and AS Number associated with an IP address_

| field | Description |
| :-  | :- |
| autonomous_system_number | The [autonomous system number](http://en.wikipedia.org/wiki/Autonomous_system_(Internet)) associated with the IP address. |
| autonomous_system_organization | The organization associated with the registered [autonomous system number](http://en.wikipedia.org/wiki/Autonomous_system_(Internet)) for the IP address.
| isp | The name of the ISP associated with the IP address. |
| organization | The name of the organization associated with the IP address. |
| network | The network associated with the record. In particular, this is the largest network where all of the fields besides ip_address have the same value. |

### Domain

_Look up the second level domain names associated with IP addresses_

| field | Description |
| :-  | :- |
| domain | The second level domain associated with the IP address. This will be something like "example.com" or "example.co.uk", not "foo.example.com". |

### Connection Type

_Estimate the connection speed of your visitors based on their IP address_

| field | Description |
| :-  | :- |
| connection_type | The connection type may take the following values: Dialup, Cable/DSL, Corporate, Cellular. Additional values may be added in the future.|
| network | The network associated with the record. In particular, this is the largest network where all of the fields besides ip_address have the same value. |
