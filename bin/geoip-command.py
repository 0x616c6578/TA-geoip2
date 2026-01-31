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
        default=None,
        validate=validators.Fieldname())

    field = Option(
        doc='''
            **Syntax:** **field=***<ip-field>*
            **Description:** Specify the field containing IPv4 or IPv6 addresses to look up.
            **Default:** ip''',
        require=False,
        default="ip",
        validate=validators.Fieldname())

    fillnull = Option(
        doc='''
            **Syntax:** **fillnull=***<string>*
            **Description:** Specify the value to fill null fields with.
            **Default:** NULL/empty string''',
        require=False,
        default=None)


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
            'ASN': None,
            'City': None,
            'Connection-Type': None,
            'Domain': None,
            'Enterprise': None,
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
                    response = anonymous_ip_reader.anonymous_ip(ip)
                except AddressNotFoundError:    # Expected behaviour; the entry was not in the database
                    response = None
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])
                finally:
                    anonymous_ip_fields = {
                        'is_anonymous': response.is_anonymous if response else self.fillnull,
                        'is_anonymous_vpn': response.is_anonymous_vpn if response else self.fillnull,
                        'is_hosting_provider': response.is_hosting_provider if response else self.fillnull,
                        'is_public_proxy': response.is_public_proxy if response else self.fillnull,
                        'is_residential_proxy': response.is_residential_proxy if response else self.fillnull,
                        'is_tor_exit_node': response.is_tor_exit_node if response else self.fillnull,
                        'network': response.network if response else self.fillnull}

                    if self.prefix:
                        anonymous_ip_fields = {prefix + field: value for field,value in anonymous_ip_fields.items()}
                    new_fields.update(anonymous_ip_fields)


            asn_reader = database_readers.get('ASN')
            if asn_reader:
                try:
                    response = asn_reader.asn(ip)
                except AddressNotFoundError:    # Expected behaviour; the entry was not in the database
                    response = None
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])
                finally:
                    asn_fields = {
                        'autonomous_system_number': response.autonomous_system_number if response else self.fillnull,
                        'autonomous_system_organization': response.autonomous_system_organization if response else self.fillnull,
                        'network': response.network if response else self.fillnull}

                    if self.prefix:
                        asn_fields = {prefix + field: value for field,value in asn_fields.items()}
                    new_fields.update(asn_fields)
                    

            connection_type_reader = database_readers.get('Connection-Type')
            if connection_type_reader:
                try:
                    response = connection_type_reader.connection_type(ip)
                except AddressNotFoundError:    # Expected behaviour; the entry was not in the database
                    response = None
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])
                finally:
                    connection_type_fields = {
                        'connection_type': response.connection_type if response else self.fillnull,
                        'network': response.network if response else self.fillnull}

                    if self.prefix:
                        connection_type_fields = {prefix + field: value 
                            for field,value in connection_type_fields.items()}
                    new_fields.update(connection_type_fields)


            domain_reader = database_readers.get('Domain')
            if domain_reader:
                try:
                    response = domain_reader.domain(ip)
                except AddressNotFoundError:    # Expected behaviour; the entry was not in the database
                    response = None
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])
                finally:
                    domain_fields = {
                        'domain': response.domain if response else self.fillnull}

                    if self.prefix:
                        domain_fields = {prefix + field: value for field,value in domain_fields.items()}
                    new_fields.update(domain_fields)


            isp_reader = database_readers.get('ISP')
            if isp_reader:
                try:
                    response = isp_reader.isp(ip)
                except AddressNotFoundError:    # Expected behaviour; the entry was not in the database
                    response = None
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])
                finally:
                    isp_fields = {
                        'autonomous_system_number': response.autonomous_system_number if response else self.fillnull,
                        'autonomous_system_organization': response.autonomous_system_organization if response else self.fillnull,
                        'isp': response.isp if response else self.fillnull,
                        'organization': response.organization if response else self.fillnull,
                        'network': response.network if response else self.fillnull}

                    if self.prefix:
                        isp_fields = {prefix + field: value for field,value in isp_fields.items()}
                    new_fields.update(isp_fields)


            city_reader = database_readers.get('City')
            if city_reader:
                

                try:
                    response = city_reader.city(ip)
                    # Show the registered country where the represented (user) country is not available.
                    #   This may not reflect the users' country.
                    country = response.country.name
                    country_code = response.country.iso_code
                    if country is None and response.registered_country.name is not None:
                        country = response.registered_country.name + ' (registered)'
                        country_code = response.registered_country.iso_code + ' (registered)'
                except AddressNotFoundError:    # Expected behaviour; the entry was not in the database
                    response = None
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])
                finally:
                    city_fields = {
                        'Country': country if response else self.fillnull,
                        'Region': response.subdivisions.most_specific.name if response else self.fillnull,
                        'City': response.city.name if response else self.fillnull,
                        'lat': response.location.latitude if response else self.fillnull,
                        'lon': response.location.longitude if response else self.fillnull,
                        'Region.code': response.subdivisions.most_specific.iso_code if response else self.fillnull,
                        'Postal.code': response.postal.code if response else self.fillnull,
                        'Country.code': country_code if response else self.fillnull,
                        'network': response.traits.network if response else self.fillnull}

                    if self.prefix:
                        city_fields = {prefix + field: value for field,value in city_fields.items()}
                    new_fields.update(city_fields)

            enterprise_reader = database_readers.get('Enterprise')
            if enterprise_reader:
                try:
                    response = enterprise_reader.enterprise(ip)
                except AddressNotFoundError:    # Expected behaviour; the entry was not in the database
                    response = None
                except ValueError:
                    self.logger.error('The IP address is invalid: %s', event[ip_field])
                finally:
                    enterprise_fields = {
                        'ip_address': response.traits.ip_address if response else self.fillnull,
                        'country': (f"{response.country.name} ({response.country.iso_code})") if response else self.fillnull,
                        'city': response.city.name if response else self.fillnull,
                        'postal_code': response.postal.code if response else self.fillnull,
                        'latitude': response.location.latitude if response else self.fillnull,
                        'longitude': response.location.longitude if response else self.fillnull,
                        'accuracy_radius': response.location.accuracy_radius if response else self.fillnull,
                        'autonomous_system_number': response.traits.autonomous_system_number if response else self.fillnull,
                        'autonomous_system_organization': response.traits.autonomous_system_organization if response else self.fillnull,
                        'isp': response.traits.isp if response else self.fillnull,
                        'organization': response.traits.organization if response else self.fillnull,
                        'domain': response.traits.domain if response else self.fillnull,
                        'user_type': response.traits.user_type if response else self.fillnull,
                        'connection_type': response.traits.connection_type if response else self.fillnull}

                    if self.prefix:
                        enterprise_fields = {prefix + field: value for field,value in enterprise_fields.items()}
                    new_fields.update(enterprise_fields)

            event.update(new_fields)
            yield event

dispatch(GeoIPCommand, sys.argv, sys.stdin, sys.stdout, __name__)
