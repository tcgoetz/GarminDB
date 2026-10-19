"""
Write an anonymized copy of a FIT file, to be added to test_files.

Serial numbers are replaced by a fixed one, ANT device numbers, product names, opaque byte fields, developer fields and body measurements are cleared,
profile, sensor and location messages are dropped, and every date, as well as any other 32 bit value close to the creation time of the file, is moved back 512 days.

    anonymize_fit.py <source.fit> <dest.fit>
"""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import argparse
import collections
import struct
import sys

import fitfile
from fitfile.definition_message_data import DefinitionMessageData
from fitfile.fields import BytesField, TimestampField
from fitfile.message_type import MessageType


# A multiple of 65536 s keeps timestamp_16 fields and compressed timestamp headers valid, and a multiple of a day keeps the time of day.
DATE_SHIFT = 2 ** 16 * 675
DATE_WINDOW = 60 * 86400
FAKE_SERIAL_NUMBER = 1234567890

CLEARED_FIELDS = {
    MessageType.file_id: {'serial_number', 'product_name'},
    MessageType.device_info: {'serial_number', 'ant_device_number', 'product_name', 'descriptor'},
    MessageType.monitoring_info: {'cycles_to_distance', 'cycles_to_calories', 'resting_metabolic_rate'},
    MessageType.file_creator: {'data'},
}
REPLACEMENT_VALUES = {
    (MessageType.file_id, 'serial_number'): FAKE_SERIAL_NUMBER,
    (MessageType.device_info, 'serial_number'): FAKE_SERIAL_NUMBER,
    (MessageType.monitoring_info, 'resting_metabolic_rate'): 1700,
}
DROPPED_MESSAGES = {
    MessageType.user_profile, MessageType.hrm_profile, MessageType.bike_profile, MessageType.location, MessageType.weight_scale, MessageType.user_metrics,
    MessageType.sensor, MessageType.field_description, MessageType.dev_data_id
}

ELEMENT_SIZES = {0x83: 2, 0x84: 2, 0x8B: 2, 0x85: 4, 0x86: 4, 0x8C: 4, 0x88: 4, 0x89: 8, 0x8E: 8, 0x8F: 8, 0x90: 8}
INVALID_VALUES = {0x00: 0xFF, 0x01: 0x7F, 0x02: 0xFF, 0x83: 0x7FFF, 0x84: 0xFFFF, 0x85: 0x7FFFFFFF, 0x86: 0xFFFFFFFF, 0x0A: 0, 0x8B: 0, 0x8C: 0,
                  0x8E: 0x7FFFFFFFFFFFFFFF, 0x8F: 0xFFFFFFFFFFFFFFFF, 0x90: 0}
FORMATS = {1: 'B', 2: 'H', 4: 'I', 8: 'Q'}
CRC_TABLE = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401, 0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]


def crc(data):
    """Return the FIT CRC of data."""
    value = 0
    for byte in data:
        for nibble in (byte & 0xF, byte >> 4):
            tmp = CRC_TABLE[value & 0xF]
            value = ((value >> 4) & 0x0FFF) ^ tmp ^ CRC_TABLE[nibble]
    return value


def _message_type(global_number):
    try:
        return MessageType(global_number)
    except ValueError:
        return None


def _known_field(message_type, number):
    return DefinitionMessageData.known_messages.get(message_type, {}).get(number)


def _field_name(message_type, number):
    field = _known_field(message_type, number)
    return field.name if field else f'unknown_{number}'


def _is_date(message_type, number):
    return number == 253 or isinstance(_known_field(message_type, number), TimestampField)


def _is_opaque(message_type, number, base_type):
    field = _known_field(message_type, number)
    return base_type == 0x0D and (field is None or isinstance(field, BytesField))


def _clear(record, offset, size, base_type, endian, replacement):
    element = ELEMENT_SIZES.get(base_type, 1)
    for start in range(offset, offset + size, element):
        if replacement is not None:
            struct.pack_into(endian + FORMATS[element], record, start, replacement)
        elif base_type in INVALID_VALUES:
            struct.pack_into(endian + FORMATS[element], record, start, INVALID_VALUES[base_type])
        else:
            record[start:start + element] = (b'\x00' if base_type == 0x07 else b'\xff') * element


def anonymize(data, changes):
    """Return an anonymized copy of the FIT file data, counting what was changed in changes."""
    header_size = data[0]
    end = header_size + struct.unpack_from('<I', data, 4)[0]
    out = bytearray(data[:header_size])
    position = header_size
    definitions = {}
    time_created = None
    while position < end:
        record_header = data[position]
        if not record_header & 0x80 and record_header & 0x40:
            big_endian = data[position + 2] == 1
            global_number = struct.unpack_from('>H' if big_endian else '<H', data, position + 3)[0]
            field_count = data[position + 5]
            fields = [tuple(data[position + 6 + 3 * index:position + 9 + 3 * index]) for index in range(field_count)]
            length = 6 + 3 * field_count
            developer_size = 0
            if record_header & 0x20:
                developer_count = data[position + length]
                developer_size = sum(data[position + length + 2 + 3 * index] for index in range(developer_count))
                length += 1 + 3 * developer_count
            definitions[record_header & 0x0F] = (_message_type(global_number), big_endian, fields, developer_size)
            out += data[position:position + length]
            position += length
            continue
        local = (record_header >> 5) & 0x3 if record_header & 0x80 else record_header & 0x0F
        message_type, big_endian, fields, developer_size = definitions[local]
        size = 1 + sum(field[1] for field in fields) + developer_size
        record = bytearray(data[position:position + size])
        position += size
        if message_type in DROPPED_MESSAGES:
            changes[f'dropped {message_type.name}'] += 1
            continue
        if developer_size:
            record[size - developer_size:] = b'\xff' * developer_size
            changes['cleared developer fields'] += 1
        endian = '>' if big_endian else '<'
        offset = 1
        for number, field_size, base_type in fields:
            name = _field_name(message_type, number)
            if message_type == MessageType.file_id and name == 'time_created' and time_created is None:
                time_created = struct.unpack_from(endian + 'I', record, offset)[0]
            if name in CLEARED_FIELDS.get(message_type, set()) or _is_opaque(message_type, number, base_type):
                _clear(record, offset, field_size, base_type, endian, REPLACEMENT_VALUES.get((message_type, name)))
                changes[f'cleared {getattr(message_type, "name", "unknown")}.{name}'] += 1
            elif base_type in (0x86, 0x8C) and field_size == 4:
                value = struct.unpack_from(endian + 'I', record, offset)[0]
                if _is_date(message_type, number):
                    moved = 0x10000000 <= value < 0xFFFFFFFF
                else:
                    moved = time_created is not None and abs(value - time_created) < DATE_WINDOW
                if moved:
                    struct.pack_into(endian + 'I', record, offset, value - DATE_SHIFT)
                    changes['moved back dates'] += 1
            offset += field_size
        out += record
    struct.pack_into('<I', out, 4, len(out) - header_size)
    if header_size == 14:
        struct.pack_into('<H', out, 12, crc(out[:12]))
    out += struct.pack('<H', crc(out))
    return bytes(out)


def main():
    """Anonymize the FIT file given on the command line."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source')
    parser.add_argument('dest')
    args = parser.parse_args()
    with open(args.source, 'rb') as source:
        data = source.read()
    if crc(data[:-2]) != struct.unpack_from('<H', data, len(data) - 2)[0]:
        sys.exit(f'{args.source}: bad CRC')
    changes = collections.Counter()
    anonymized = anonymize(data, changes)
    with open(args.dest, 'wb') as dest:
        dest.write(anonymized)
    fitfile.file.File(args.dest, fitfile.MeasurementSystem.metric)
    for change, count in sorted(changes.items()):
        print(f'{change}: {count}')


if __name__ == '__main__':
    main()
