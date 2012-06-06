# -*- coding: utf-8 -*-
import os.path
import datetime

from south.db import db
from south.v2 import DataMigration
from django.db import models

from ..settings import *
from ..management.commands.cities_light import Command as CitiesLightCommand

class Migration(DataMigration):
    def _get_country(self, code2):
        if not hasattr(self, '_country_codes'):
            self._country_codes = {}

        if code2 not in self._country_codes.keys():
            self._country_codes[code2] = self.orm['cities_light.Country'].objects.get(code2=code2)

        return self._country_codes[code2]

    def _get_region(self, country_code2, region_id):
        '''
        Simple lazy identity map for (country_code2, region_id)->region
        '''
        if not hasattr(self, '_region_codes'):
            self._region_codes = {}

        country = self._get_country(country_code2)
        if country.code2 not in self._region_codes:
            self._region_codes[country.code2] = {}

        if region_id not in self._region_codes[country.code2]:
            self._region_codes[country.code2][region_id] = self.orm['cities_light.Region'].objects.get(
                country=country, geoname_id=region_id)

        return self._region_codes[country.code2][region_id]




    def forwards(self, orm):
        self.orm = orm
        cmd = CitiesLightCommand()

        if db.dry_run:
            return

        self.regions = {}
        for country in orm['cities_light.Country'].objects.all():
            self.regions[country.code2] = {}

        for url in REGION_SOURCES + CITY_SOURCES:
            destination_file_name = url.split('/')[-1]
            destination_file_path = os.path.join(DATA_DIR,
                destination_file_name)

            cmd.download(url, destination_file_path)

            if destination_file_name.split('.')[-1] == 'zip':
                # extract the destination file, use the extracted file as new
                # destination
                destination_file_name = destination_file_name.replace(
                    'zip', 'txt')

                cmd.extract(destination_file_path, destination_file_name)

                destination_file_path = os.path.join(
                    DATA_DIR, destination_file_name)


            if url in REGION_SOURCES:
                for items in cmd.parse(destination_file_path):
                    code2, geoname_id = items[0].split('.')
                    if code2 in self.regions.keys():
                        self.regions[code2][geoname_id] = items

            elif url in CITY_SOURCES:
                for items in cmd.parse(destination_file_path):
                    try:
                        kwargs = dict(name=items[1], country=self._get_country(items[8]))
                    except orm['cities_light.Country'].DoesNotExist:
                        continue

                    try:
                        city = orm['cities_light.City'].objects.get(**kwargs)
                    except orm['cities_light.City'].DoesNotExist:
                        continue

                    try:
                        city.region = self._get_region(items[8], items[10])
                    except orm['cities_light.Region'].DoesNotExist:
                        orm['cities_light.Region'](
                            geoname_id=items[10],
                            country=self._get_country(items[8]),
                            name=self.regions[items[8]][items[10]][2],
                        ).save()
                        city.region = self._get_region(items[8], items[10])

                    city.save()



        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        'cities_light.city': {
            'Meta': {'unique_together': "(('region', 'name'),)", 'object_name': 'City'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cities_light.Country']"}),
            'geoname_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '5', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '5', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'name_ascii': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cities_light.Region']", 'null': 'True'}),
            'search_names': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '4000', 'db_index': 'True', 'blank': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique_with': '()', 'max_length': '50', 'populate_from': 'None'})
        },
        'cities_light.country': {
            'Meta': {'object_name': 'Country'},
            'code2': ('django.db.models.fields.CharField', [], {'max_length': '2', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'code3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'continent': ('django.db.models.fields.CharField', [], {'max_length': '2', 'db_index': 'True'}),
            'geoname_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'name_ascii': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique_with': '()', 'max_length': '50', 'populate_from': 'None'}),
            'tld': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '5', 'blank': 'True'})
        },
        'cities_light.region': {
            'Meta': {'unique_together': "(('country', 'name'),)", 'object_name': 'Region'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cities_light.Country']"}),
            'geoname_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'name_ascii': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique_with': '()', 'max_length': '50', 'populate_from': 'None'})
        }
    }

    complete_apps = ['cities_light']
    symmetrical = True
