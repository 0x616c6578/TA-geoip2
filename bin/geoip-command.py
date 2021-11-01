#!/usr/bin/env python

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from splunklib.searchcommands import \
    dispatch, StreamingCommand, Configuration, Option, validators 

import geoip2.database
from geoip2.errors import AddressNotFoundError


@Configuration(distributed=True)
class GeoIPCommand(StreamingCommand):
    prefix = Option(
        doc='''
            **Syntax:** **prefix=***<string>*
            **Description:** Specify a string to prefix the field names. With this argument you can add a prefix to the 
                added field names to avoid name collisions with existing fields. For example, if you specify prefix=ip. the field names that are added to the events become ip.isp, ip.network, etc.
            **Default:** NULL/empty string''',
        require=False,
        validate=validators.Fieldname())

    field = Option(
        doc='''
            **Syntax:** **field=***<ip-field>*
            **Description:** Specify the field containing IPv4 or IPv6 addresses to look up.
            **Default:** ip''',
        require=False,
        default="ip",
        validate=validators.Fieldname())


    def stream(self, events):
        ''' Generator function that processes and yields event records to the Splunk stream pipeline.
        '''
        self.logger.info('GeoIPCommand: %s', self)  # logs command line
        
        ip_field=self.field
        prefix = '' if not self.prefix else self.prefix
        input_databases = [database.lower() for database in self.fieldnames] if self.fieldnames else ["city"]

        # Store the database reader object for each MaxMind DB
        database_readers = {
            'Anonymous-IP': None,
            'City': None,
            'Connection-Type': None,
            'Domain': None,
            'ISP': None
        }

        # Validate the input database names; print a non-terminating warning if any are invalid.
        database_names = [database.lower().replace('-','_') for database in database_readers]
        for database in input_databases:
            if database not in database_names and database!="all":
                self.write_warning('\'{}\' is not a valid GeoIP2 database.'.format(database))

        # Load any requested databases (checks both the paid and free DBs). Warn if a DB can not be found.
        databases_path=os.path.join(os.path.dirname(__file__), "..", "data", "databases")
        for database in database_readers.keys():
            if database.lower().replace('-','_') in input_databases or "all" in input_databases:
                paid_db_path = os.path.join(databases_path, 'GeoIP2-' + database + '.mmdb')
                free_db_path = os.path.join(databases_path, 'GeoLite2-' + database + '.mmdb')

                if os.path.isfile(paid_db_path):
                    try:
                        database_readers[database] = geoip2.database.Reader(paid_db_path)
                    except:
                        self.error_exit(None, 
                            'Error in \'geoip\': There was an issue with the "{}" database.'.format(paid_db_path))
                elif os.path.isfile(free_db_path):
                    try:
                        database_readers[database] = geoip2.database.Reader(free_db_path)
                    except:
                        self.error_exit(None, 
                            'Error in \'geoip\': There was an issue with the "{}" database.'.format(free_db_path))
                else:
                    self.write_warning('Warning in \'geoip\': No \'{0}\' database could be found in \'{1}\'.'
                        .format(database, os.path.abspath(databases_path)))

        # Terminate if no databases were loaded (no readers were assigned).
        if not len(list((reader for reader in database_readers.values() if reader is not None))) :
            self.error_exit(None, 'Error in \'geoip\': No databases were loaded.')

        for event in events:
            # Terminate if the IP field does not exist
            try:
                ip = event[ip_field]
            except KeyError as error:
                self.error_exit(error, 
                    'Error in \'geoip\': Invalid option value. The \'{}\' field could not be found.'.format(self.field))

            # Look up the IP in each requested database. Adds additional fields to a dictionary to be added into the event all at once.
            new_fields = {}
            anonymous_ip_reader = database_readers.get('Anonymous-IP')
            if anonymous_ip_reader:
                try:
                    anonymous_ip_response = anonymous_ip_reader.anonymous_ip(ip)
                    new_fields.update({
                        prefix + 'is_anonymous': anonymous_ip_response.is_anonymous,
                        prefix + 'is_anonymous_vpn': anonymous_ip_response.is_anonymous_vpn,
                        prefix + 'is_hosting_provider': anonymous_ip_response.is_hosting_provider,
                        prefix + 'is_public_proxy': anonymous_ip_response.is_public_proxy,
                        prefix + 'is_residential_proxy': anonymous_ip_response.is_residential_proxy,
                        prefix + 'is_tor_exit_node': anonymous_ip_response.is_tor_exit_node,
                        prefix + 'network': anonymous_ip_response.network})
                except AddressNotFoundError:
                    pass    # Expected behaviour
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])
                    

            connection_type_reader = database_readers.get('Connection-Type')
            if connection_type_reader:
                try:
                    connection_type_response = connection_type_reader.connection_type(ip)
                    new_fields.update({
                        prefix + 'connection_type': connection_type_response.connection_type,
                        prefix + 'network': connection_type_response.network})
                except AddressNotFoundError:
                    pass    # Expected behaviour
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])

            domain_reader = database_readers.get('Domain')
            if domain_reader:
                try:
                    domain_response = domain_reader.domain(ip)
                    new_fields.update({
                        prefix + 'domain': domain_response.domain})
                except AddressNotFoundError:
                    pass    # Expected behaviour
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])

            isp_reader = database_readers.get('ISP')
            if isp_reader:
                try:
                    isp_response = isp_reader.isp(ip)
                    new_fields.update({
                        prefix + 'autonomous_system_number': isp_response.autonomous_system_number,
                        prefix + 'autonomous_system_organization': isp_response.autonomous_system_organization,
                        prefix + 'isp': isp_response.isp,
                        prefix + 'organization': isp_response.organization,
                        prefix + 'network': isp_response.network})
                except AddressNotFoundError:
                    pass    # Expected behaviour
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])

            city_reader = database_readers.get('City')
            if city_reader:
                try:
                    city_response = city_reader.city(ip)

                    # Show the registered country where the represented (user) country is not available.
                    #   This may not reflect the users' country.
                    country = city_response.country.name
                    country_code = city_response.country.iso_code
                    if country is None:
                        country = city_response.registered_country.name + ' (registered)'
                        country_code = city_response.registered_country.iso_code + ' (registered)'

                    new_fields.update({
                        prefix + 'Country': country,
                        prefix + 'Region': city_response.subdivisions.most_specific.name,
                        prefix + 'City': city_response.city.name,
                        prefix + 'lat': city_response.location.latitude,
                        prefix + 'lon': city_response.location.longitude,
                        prefix + 'Region.code': city_response.subdivisions.most_specific.iso_code,
                        prefix + 'Postal.code': city_response.postal.code,
                        prefix + 'Country.code': country_code,
                        prefix + 'network': city_response.traits.network})
                except AddressNotFoundError:
                    pass    # Expected behaviour
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])

            event.update(new_fields)
            yield event

dispatch(GeoIPCommand, sys.argv, sys.stdin, sys.stdout, __name__)