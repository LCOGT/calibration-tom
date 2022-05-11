#from django.db.models import Count

import csv
from .models import Instrument
from io import StringIO


# NOTE: This saves locally. To avoid this, create file buffer.
# referenced https://www.codingforentrepreneurs.com/blog/django-queryset-to-csv-files-datasets/
def export_instruments(qs):
    """
    Exports all the specified instruments into a csv file in folder csvInstrumentFiles
    NOTE: This saves locally. To avoid this, create file buffer.

    :param qs: List of instruments to export
    :type qs: QuerySet

    :returns: String buffer of exported instruments
    :rtype: StringIO
    """
    qs_pk = [data['id'] for data in qs]
    data_list = list(qs)
    instrument_fields = [field.name for field in Instrument._meta.get_fields()]

    file_buffer = StringIO()
    writer = csv.DictWriter(file_buffer, fieldnames=all_fields)
    writer.writeheader()
    for instrument_data in data_list:
        names = list(InstrumentName.objects.filter(instrument_id=instrument_data['id']))
        name_index = 2
        for name in names:
            instrument_data[f'name{str(name_index)}'] = name.name
            name_index += 1
        del instrument_data['id']  # do not export 'id'
        writer.writerow(instrument_data)
    return file_buffer


def import_instruments(instruments):
    """
    Imports a set of instruments into the TOM and saves them to the database.

    :param instruments: String buffer of instruments
    :type instruments: StringIO

    :returns: dictionary of successfully imported instruments, as well errors
    :rtype: dict
    """
    # TODO: Replace this with an in memory iterator
    instrumentreader = csv.DictReader(instruments, dialect=csv.excel)
    instruments = []
    errors = []
    base_instrument_fields = [field.name for field in Instrument._meta.get_fields()]
    for index, row in enumerate(instrumentreader):
        # filter out empty values in base fields, otherwise converting empty string to float will throw error
        row = {k: v for (k, v) in row.items() if not (k in base_instrument_fields and not v)}
        instrument_names = []
        instrument_fields = {}
        for k in row:
            # All fields starting with 'name' (e.g. name2, name3) that aren't literally 'name' will be added as
            # InstrumentNames
            if k != 'name' and k.startswith('name'):
                instrument_names.append(row[k])
            else:
                instrument_fields[k] = row[k]
        try:
            instrument = Instrument.objects.create(**instrument_fields)
            for name in instrument_names:
                if name:
                    InstrumentName.objects.create(instrument=instrument, name=name)
            instruments.append(instrument)
        except Exception as e:
            error = 'Error on line {0}: {1}'.format(index + 2, str(e))
            errors.append(error)

    return {'instruments': instruments, 'errors': errors}
