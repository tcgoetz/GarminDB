"""
Benchmark the import of a sample of downloaded Garmin data and check that two code versions build the same databases.

Build a sample from an existing HealthData directory (data files are symlinked, the source is not modified):
    bench_import.py sample --source ~/HealthData --dest /tmp/garmin_sample

Import the sample with a given interpreter and GarminDB checkout, keeping the resulting databases:
    bench_import.py run --sample /tmp/garmin_sample --name baseline --python <venv>/bin/python --cli <checkout>/scripts/garmindb_cli.py
    bench_import.py run --sample /tmp/garmin_sample --name parallel --python <venv>/bin/python --cli <checkout>/scripts/garmindb_cli.py -- --jobs 8

Import again on top of the databases of a previous run, as a daily update does:
    bench_import.py run --sample /tmp/garmin_sample --name again --start-from baseline --python <venv>/bin/python --cli <checkout>/scripts/garmindb_cli.py

Compare the databases of two runs table by table:
    bench_import.py compare --sample /tmp/garmin_sample baseline parallel
"""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time


def _link(source, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(source))
    if not os.path.lexists(dest):
        os.symlink(source, dest)


def _spread(names, count):
    """Return count names taken as a few contiguous runs spread over the sorted list, so that neighbouring files stay together."""
    names = sorted(names)
    if len(names) <= count:
        return names
    runs = 4
    run_length = count // runs
    picked = []
    for run in range(runs):
        start = (len(names) - run_length) * run // (runs - 1)
        picked += names[start:start + run_length]
    return picked


def build_sample(source, dest, monitoring_count, activity_count, day_count):
    """Symlink a sample of the files under source into dest and write a config that points GarminDB at it."""
    fit_dir = os.path.join(source, 'FitFiles')
    # The profile files are rewritten by every download, copy them so that the sample does not change under a benchmark.
    os.makedirs(os.path.join(dest, 'FitFiles'), exist_ok=True)
    for name in os.listdir(fit_dir):
        if os.path.isfile(os.path.join(fit_dir, name)) and not os.path.lexists(os.path.join(dest, 'FitFiles', name)):
            shutil.copy(os.path.join(fit_dir, name), os.path.join(dest, 'FitFiles', name))
    years = sorted(year for year in os.listdir(os.path.join(fit_dir, 'Monitoring')) if os.path.isdir(os.path.join(fit_dir, 'Monitoring', year)))
    for year in years[-2:]:
        year_dir = os.path.join(fit_dir, 'Monitoring', year)
        names = os.listdir(year_dir)
        picked = _spread([name for name in names if name.endswith('.fit')], monitoring_count // 2)
        picked += _spread([name for name in names if not name.endswith('.fit')], day_count)
        for name in picked:
            _link(os.path.join(year_dir, name), os.path.join(dest, 'FitFiles', 'Monitoring', year))
    activities_dir = os.path.join(fit_dir, 'Activities')
    activity_ids = sorted(re.match(r'(\d+)_ACTIVITY', name).group(1) for name in os.listdir(activities_dir) if name.endswith('_ACTIVITY.fit'))
    for activity_id in _spread(activity_ids, activity_count):
        for name in (f'{activity_id}_ACTIVITY.fit', f'activity_{activity_id}.json', f'activity_details_{activity_id}.json', f'{activity_id}.tcx'):
            if os.path.isfile(os.path.join(activities_dir, name)):
                _link(os.path.join(activities_dir, name), os.path.join(dest, 'FitFiles', 'Activities'))
    for directory in ('Sleep', 'RHR', 'Weight'):
        if os.path.isdir(os.path.join(source, directory)):
            for name in sorted(os.listdir(os.path.join(source, directory)))[-day_count:]:
                _link(os.path.join(source, directory, name), os.path.join(dest, directory))
    config = {
        'db': {'type': 'sqlite'},
        'garmin': {'domain': 'garmin.com'},
        'credentials': {'user': '', 'secure_password': False, 'password': '', 'password_file': None},
        'data': {name + '_start_date': '12/31/2019' for name in ('weight', 'sleep', 'rhr', 'hrv', 'monitoring')},
        'directories': {'relative_to_home': False, 'base_dir': dest, 'mount_dir': '/Volumes/GARMIN'},
        'enabled_stats': {name: True for name in ('monitoring', 'steps', 'itime', 'sleep', 'rhr', 'weight', 'activities')},
        'course_views': {'steps': []},
        'modes': {},
        'activities': {'display': []},
        'settings': {'metric': False, 'default_display_activities': ['walking', 'running', 'cycling']},
        'checkup': {'look_back_days': 90},
    }
    os.makedirs(os.path.join(dest, 'config'), exist_ok=True)
    with open(os.path.join(dest, 'config', 'GarminConnectConfig.json'), 'w') as config_file:
        json.dump(config, config_file, indent=4)
    counts = {os.path.relpath(root, dest): len(files) for root, _, files in os.walk(dest) if files and 'runs' not in root}
    print(json.dumps(counts, indent=2))


def run_import(sample, name, python, cli, cli_args, start_from=None):
    """Import the sample into empty databases, or into a copy of those of a previous run, and keep them under runs/<name>."""
    db_dir = os.path.join(sample, 'DBs')
    run_dir = os.path.join(sample, 'runs', name)
    shutil.rmtree(db_dir, ignore_errors=True)
    shutil.rmtree(run_dir, ignore_errors=True)
    os.makedirs(run_dir)
    if start_from:
        shutil.copytree(os.path.join(sample, 'runs', start_from, 'DBs'), db_dir)
    command = [python, cli, '--config', os.path.join(sample, 'config'), '--all', '--import'] + cli_args
    start = time.perf_counter()
    with open(os.path.join(run_dir, 'output.txt'), 'w') as output:
        result = subprocess.run(command, cwd=run_dir, stdout=output, stderr=subprocess.STDOUT)
    elapsed = time.perf_counter() - start
    shutil.move(db_dir, os.path.join(run_dir, 'DBs'))
    with open(os.path.join(run_dir, 'elapsed.txt'), 'w') as elapsed_file:
        elapsed_file.write(f'{elapsed:.2f}\n')
    print(f'{name}: exit {result.returncode}, {elapsed:.1f}s')
    return result.returncode


def _table_digests(db_file):
    """Return {table: (row count, digest of the sorted rows)} for a database, leaving out when-it-was-written bookkeeping."""
    connection = sqlite3.connect(db_file)
    try:
        digests = {}
        for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"):
            columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
            if table in ('attributes', '_attributes'):
                columns.remove('timestamp')
            names = ', '.join(f'"{column}"' for column in columns)
            digest = hashlib.sha256()
            count = 0
            for row in connection.execute(f'SELECT {names} FROM "{table}" ORDER BY {names}'):
                digest.update(repr(row).encode())
                count += 1
            digests[table] = (count, digest.hexdigest())
        return digests
    finally:
        connection.close()


def compare_runs(sample, reference, candidate):
    """Print the tables whose rows differ between two runs. Returns the number of differing tables."""
    different = 0
    rows = 0
    reference_dbs = sorted(glob.glob(os.path.join(sample, 'runs', reference, 'DBs', '*.db')))
    for reference_db in reference_dbs:
        db_name = os.path.basename(reference_db)
        candidate_db = os.path.join(sample, 'runs', candidate, 'DBs', db_name)
        reference_digests = _table_digests(reference_db)
        candidate_digests = _table_digests(candidate_db) if os.path.isfile(candidate_db) else {}
        for table in sorted(set(reference_digests) | set(candidate_digests)):
            expected, actual = reference_digests.get(table), candidate_digests.get(table)
            rows += expected[0] if expected else 0
            if expected != actual:
                different += 1
                print(f'DIFFERENT {db_name} {table}: {reference} {expected and expected[0]} rows, {candidate} {actual and actual[0]} rows')
    print(f'{reference} vs {candidate}: {len(reference_dbs)} databases, {rows} rows, {different} differing tables')
    return different


def main():
    """Run the command given on the command line."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    sample = commands.add_parser('sample')
    sample.add_argument('--source', default=os.path.expanduser('~/HealthData'))
    sample.add_argument('--dest', required=True)
    sample.add_argument('--monitoring', type=int, default=1200)
    sample.add_argument('--activities', type=int, default=160)
    sample.add_argument('--days', type=int, default=120)
    run = commands.add_parser('run')
    run.add_argument('--sample', required=True)
    run.add_argument('--name', required=True)
    run.add_argument('--python', default=sys.executable)
    run.add_argument('--cli', required=True)
    run.add_argument('--start-from', help='import on top of the databases of this run instead of empty ones')
    run.add_argument('cli_args', nargs='*')
    compare = commands.add_parser('compare')
    compare.add_argument('--sample', required=True)
    compare.add_argument('reference')
    compare.add_argument('candidate')
    args = parser.parse_args()
    if args.command == 'sample':
        build_sample(args.source, os.path.abspath(args.dest), args.monitoring, args.activities, args.days)
    elif args.command == 'run':
        sys.exit(run_import(os.path.abspath(args.sample), args.name, args.python, args.cli, args.cli_args, args.start_from))
    else:
        sys.exit(1 if compare_runs(os.path.abspath(args.sample), args.reference, args.candidate) else 0)


if __name__ == '__main__':
    main()
