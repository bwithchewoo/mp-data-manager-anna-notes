from django.core.management.base import BaseCommand
import sys

import requests

class Command(BaseCommand):
    help = "Import TSV of ESPIS Links and apply to layers."

    def handle(self, *args, **options):
        if not len(args) == 1 or not args[0][-2:] == 'sv':
            print('Usage: manage.py import_espis /full/path/to/input/file.csv (Must be .csv or .tsv)')
            sys.exit()

        import csv
        # infile = '/home/vagrant/marco_portal2/apps/mp-data-manager/import_files/ESPIS_Links-Sheet1.tsv'
        infile = args[0]
        if infile[-3:].lower() == 'tsv':
            delimiter = '\t'
        elif infile[-3:].lower() == 'csv':
            delimiter = ','
        else:
            print('Input file must be .csv or .tsv')
            sys.exit()
        try:
            f = open(infile, 'rb')
            reader = csv.reader(f, delimiter=delimiter)
            headers = reader.next()
            if not 'Layer Name' in headers:
                '"Layer Name" must be a header - make sure to keep header row attached when importing file'
                sys.exit()
            else:
                layer_idx = headers.index("Layer Name")
            if not 'Subject Keyword' in headers:
                '"Subject Keyword" must be a header - make sure to keep header row attached when importing file'
                sys.exit()
            else:
                keyword_idx = headers.index("Subject Keyword")
            if not 'Location Key' in headers:
                '"Location Key" must be a header - make sure to keep header row attached when importing file'
                sys.exit()
            else:
                geo_idx = headers.index("Location Key")

            from data_manager.models import Layer
            for row in reader:
                try:
                    layer = Layer.objects.get(name=row[layer_idx].strip())
                    if row[keyword_idx] == 'No relevant links':
                        print("No relevant links")
                        layer.espis_enabled = False
                        layer.espis_search = None
                        layer.espis_region = None
                        layer.save()
                    elif row[layer_idx] == '':
                        print("")
                        layer.espis_enabled = False
                        layer.espis_search = None
                        layer.espis_region = None
                        layer.save()
                    else:
                        if len(row[keyword_idx]) > 0 or len(row[geo_idx]) > 0:
                            layer.espis_enabled = True
                        else:
                            layer.espis_enabled = False
                        layer.espis_search = row[keyword_idx]
                        layer.espis_region = row[geo_idx]
                        layer.save()
                        print("ESPIS LINK SAVED: layer - [%s], search - [%s], region = [%s]" % (row[layer_idx], row[keyword_idx], row[geo_idx]))

                except:
                    if row[keyword_idx] == 'No relevant links':
                        print("No relevant links")
                    elif row[layer_idx] == '':
                        print("")
                    else:
                        print('Match not found for layer "%s"' % (row[layer_idx]))
                    pass


            f.close()
        except IOError:
            print('No such file or directory: %s' % args[0])
            sys.exit()
