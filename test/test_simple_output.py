"""Test main-CLI progress with real forwarding and isolated data boundaries."""

import contextlib
import datetime
import importlib.util
import io
import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import fitfile
from idbutils import JsonFileProcessor
from garmindb import Analyze, Copy, Download, GarminConnectConfigManager, Statistics
from garmindb.fit_data import FitData
from garmindb.garmin_tcx_data import GarminTcxData


JSON_FILES = {
    'GarminUserSettings': 'user-settings.json',
    'GarminPersonalInformation': 'personal-information.json',
    'GarminSocialProfile': 'social-profile.json',
    'GarminWeightData': 'weight_2024-01-01.json',
    'GarminSummaryData': 'daily_summary_2024-01-01.json',
    'GarminHydrationData': 'hydration_2024-01-01.json',
    'GarminConnectSleepData': 'sleep_2024-01-01.json',
    'GarminRhrData': 'rhr_2024-01-01.json',
    'GarminConnectHrvData': 'hrv_2024-01-01.json',
    'GarminJsonSummaryData': 'activity_123.json',
    'GarminJsonDetailsData': 'activity_details_123.json',
}
FIT_CLASSES = {'GarminSettingsFitData', 'GarminMonitoringFitData', 'GarminSleepFitData', 'GarminHrvFitData', 'GarminActivitiesFitData'}


class TestSimpleOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'scripts' / 'garmindb_cli.py'
        spec = importlib.util.spec_from_file_location('garmindb_cli', path)
        cls.cli = importlib.util.module_from_spec(spec)
        # Import the CLI without creating its normal log file in the test directory.
        with patch('logging.basicConfig'):
            spec.loader.exec_module(cls.cli)

    def setUp(self):
        self.addCleanup(logging.getLogger().setLevel, logging.getLogger().level)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = Mock(spec=GarminConnectConfigManager)
        for name in ('get_fit_files_dir', 'get_weight_dir', 'get_monitoring_base_dir', 'get_sleep_dir',
                     'get_rhr_dir', 'get_activities_dir', 'get_plugins_dir'):
            getattr(self.config, name).return_value = self.directory.name
        self.config.get_db_params.return_value = {}
        self.config.enabled_stats.return_value = [Statistics.weight, Statistics.monitoring, Statistics.sleep,
                                                  Statistics.rhr, Statistics.hrv, Statistics.activities]

    def test_cli_forwards_modes_including_rebuild(self):
        for simple_output in (False, True):
            with self.subTest(simple_output=simple_output):
                argv = ['garmindb_cli.py', '--all', '--copy', '--download', '--import', '--analyze', '--rebuild_db']
                if simple_output:
                    argv.append('--simple-output')
                with patch('sys.argv', argv), patch.object(self.cli, 'log_version'), patch.object(self.cli, 'GarminDbMain') as main_class:
                    instance = main_class.return_value
                    instance.gc_config = self.config
                    self.cli.main([])
                for method, count in (('copy_data', 1), ('download_data', 1), ('import_data', 2), ('analyze_data', 2)):
                    calls = getattr(instance, method).call_args_list
                    self.assertEqual(len(calls), count)
                    self.assertTrue(all(call.kwargs['simple_output'] == simple_output for call in calls))

    def test_operation_methods_forward_default_and_simple_modes_to_constructors(self):
        for options in ({}, {'simple_output': True}):
            simple_output = options.get('simple_output', False)
            with self.subTest(simple_output=simple_output), \
                    patch.object(self.cli, 'GarminConnectConfigManager', return_value=self.config), \
                    patch.object(self.cli, 'PluginManager'), \
                    patch.object(self.cli, 'Copy') as copy_class, \
                    patch.object(self.cli, 'Download') as download_class, \
                    patch.object(self.cli, 'Analyze') as analyze_class:
                main = self.cli.GarminDbMain()
                main.copy_data(False, False, [], **options)
                main.download_data(False, False, [], **options)
                main.analyze_data(3, **options)
                copy_class.assert_called_once_with(self.config, simple_output=simple_output)
                download_class.assert_called_once_with(self.config, simple_output=simple_output)
                analyze_class.assert_called_once_with(self.config, 2, simple_output=simple_output)
                copy_class.return_value.copy_settings.assert_called_once_with(self.directory.name)
                download_class.return_value.login.assert_called_once_with()
                analyze_class.return_value.summary.assert_called_once_with()
                analyze_class.return_value.create_dynamic_views.assert_called_once_with()

    def test_cli_reaches_all_real_importer_constructors_and_loops(self):
        for filename in JSON_FILES.values():
            Path(self.directory.name, filename).write_text('{}', encoding='utf-8')
        Path(self.directory.name, 'sample.fit').write_bytes(b'fixture')
        Path(self.directory.name, 'sample.tcx').write_text('<fixture/>', encoding='utf-8')
        for simple_output in (False, True):
            with self.subTest(simple_output=simple_output), contextlib.ExitStack() as stack:
                argv = ['garmindb_cli.py', '--all', '--import', '--trace', '3']
                if simple_output:
                    argv.append('--simple-output')
                stack.enter_context(patch('sys.argv', argv))
                stack.enter_context(patch.object(self.cli, 'log_version'))
                stack.enter_context(patch.object(self.cli, 'GarminConnectConfigManager', return_value=self.config))
                stack.enter_context(patch.object(self.cli, 'PluginManager'))
                stack.enter_context(patch.object(self.cli, 'GarminDb'))
                stack.enter_context(patch.object(self.cli.Attributes, 'measurements_type', return_value=fitfile.MeasurementSystem.metric))
                for module, names in (('garmindb.import_monitoring', ('GarminDb', 'SleepDb', 'HrvDb')),
                                      ('garmindb.garmin_json_data', ('ActivitiesDb',)),
                                      ('garmindb.garmin_tcx_data', ('GarminDb', 'ActivitiesDb'))):
                    for name in names:
                        stack.enter_context(patch(f'{module}.{name}'))
                for name in ('FitFileProcessor', 'MonitoringFitFileProcessor', 'SleepFitFileProcessor', 'HrvFitFileProcessor', 'ActivityFitFileProcessor'):
                    stack.enter_context(patch.object(self.cli, name))
                for name in JSON_FILES:
                    stack.enter_context(patch.object(getattr(self.cli, name), '_process_json', return_value=1))
                stack.enter_context(patch('garmindb.fit_data.fitfile.file.File', return_value=Mock(type=fitfile.FileType.activity)))
                stack.enter_context(patch.object(GarminTcxData, '_GarminTcxData__process_file'))
                seen = []

                def record(original):
                    def run(processor, *args):
                        seen.append(processor)
                        return original(processor, *args)
                    return run

                for owner, name in ((JsonFileProcessor, 'process'), (FitData, 'process_files'), (GarminTcxData, 'process_files')):
                    stack.enter_context(patch.object(owner, name, autospec=True, side_effect=record(getattr(owner, name))))
                json_bar = stack.enter_context(patch('idbutils.json_file_processor.tqdm', side_effect=lambda items, **kwargs: items))
                owned_bar = stack.enter_context(patch('garmindb.progress.tqdm', side_effect=lambda items, **kwargs: items))
                output = io.StringIO()
                with contextlib.redirect_stderr(output):
                    self.cli.main([])
                self.assertEqual({type(processor).__name__ for processor in seen}, set(JSON_FILES) | FIT_CLASSES | {'GarminTcxData'})
                self.assertEqual(len(seen), 17)
                self.assertTrue(all(processor.simple_output == simple_output for processor in seen))
                for processor in seen:
                    if isinstance(processor, JsonFileProcessor):
                        self.assertEqual(processor.debug, 3)
                        self.assertEqual(processor.total_updates, 1)
                self.assertEqual(json_bar.call_count, 0 if simple_output else 11)
                self.assertEqual(owned_bar.call_count, 0 if simple_output else 6)
                for bar in (json_bar, owned_bar):
                    for call in bar.call_args_list:
                        self.assertEqual(len(call.args), 1)
                        self.assertEqual(call.kwargs, {'unit': 'files'})
                if simple_output:
                    self.assertNotIn('\r', output.getvalue())
                    self.assertNotIn('\x1b', output.getvalue())
                    labels = [
                        'Processing user settings JSON files', 'Processing personal information JSON files',
                        'Processing social profile JSON files', 'Processing settings FIT files', 'Processing weight JSON files',
                        'Processing daily summary JSON files', 'Processing hydration JSON files', 'Processing monitoring FIT files',
                        'Processing sleep FIT files', 'Processing sleep JSON files', 'Processing resting heart rate JSON files',
                        'Processing HRV FIT files', 'Processing HRV JSON files', 'Processing activity TCX files',
                        'Processing activity summary JSON files', 'Processing activity detail JSON files', 'Processing activity FIT files',
                    ]
                    self.assertEqual(output.getvalue().splitlines(), [line for label in labels for line in (label, f'{label}: 1 file visited')])
                else:
                    self.assertEqual(output.getvalue(), '')

    def test_fit_existing_positional_arguments_filtering_and_handled_errors(self):
        processor = FitData(self.directory.name, 3, False, True, [fitfile.FileType.activity], fitfile.MeasurementSystem.metric,
                            simple_output=True)
        processor.file_names = ['bad.fit', 'settings.fit', 'activity.fit']
        activity = Mock(type=fitfile.FileType.activity)
        writer = Mock()
        output = io.StringIO()
        with patch('garmindb.fit_data.fitfile.file.File', side_effect=[ValueError('bad FIT'), Mock(type=fitfile.FileType.settings), activity]), \
                self.assertLogs(level='ERROR'), contextlib.redirect_stderr(output):
            processor.process_files(writer)
        writer.write_file.assert_called_once_with(activity)
        self.assertEqual(processor.debug, 3)
        self.assertEqual(output.getvalue(), 'Processing FIT files\nProcessing FIT files: 3 files visited\n')

    def test_copy_uses_simple_progress_and_copies_files(self):
        source = Path(self.directory.name, 'source')
        destination = Path(self.directory.name, 'destination')
        source.mkdir()
        destination.mkdir()
        (source / 'settings.fit').write_bytes(b'FIT fixture')
        self.config.device_mount_dir.return_value = self.directory.name
        self.config.device_settings_dir.return_value = str(source)
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            Copy(self.config, simple_output=True).copy_settings(str(destination))
        self.assertEqual((destination / 'settings.fit').read_bytes(), b'FIT fixture')
        self.assertEqual(output.getvalue(), 'Copying FIT files\nCopying FIT files: 1 file visited\n')

    def test_download_loops_and_retry_behavior(self):
        output = io.StringIO()
        day = datetime.date(2024, 1, 1)
        with patch('garmindb.download.GarminConnectAuthAdapter'), patch('garmindb.download.time.sleep') as sleep:
            download = Download(self.config, simple_output=True)
            download.garmin.connectapi.side_effect = [RuntimeError('retry'), {}]
            with self.assertLogs(level='WARNING'), contextlib.redirect_stderr(output):
                download.get_weight(self.directory.name, day, 1, False)
            self.assertEqual(download.garmin.connectapi.call_count, 2)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [5, 1])
            with patch('garmindb.download.tempfile.mkdtemp', return_value=self.directory.name), \
                    patch.object(download, '_Download__get_monitoring_day'), patch.object(download, '_Download__unzip_files'), \
                    patch.object(download, '_Download__get_activity_summaries', return_value=[{'activityId': 123}]), \
                    patch.object(download, '_Download__save_activity_details'), patch.object(download, '_Download__save_activity_file'), \
                    contextlib.redirect_stderr(output):
                download.get_monitoring(lambda year: self.directory.name, day, 1)
                download.get_activities(self.directory.name, 1)
        self.assertEqual(output.getvalue(), 'Downloading weight data\nDownloading weight data: 1 day visited\n'
                         'Downloading monitoring data\nDownloading monitoring data: 1 day visited\n'
                         'Downloading activities\nDownloading activities: 1 activity visited\n')

    def test_analysis_loops_use_simple_progress(self):
        with contextlib.ExitStack() as stack:
            for name in ('GarminDb', 'MonitoringDb', 'SleepDb', 'HrvDb', 'GarminSummaryDb', 'summarydb.SummaryDb', 'ActivitiesDb'):
                stack.enter_context(patch(f'garmindb.analyze.{name}'))
            stack.enter_context(patch('garmindb.analyze.Attributes.measurements_type', return_value=fitfile.MeasurementSystem.metric))
            analyze = Analyze(self.config, 3, simple_output=True)
            for name in ('Monitoring.s_get_days', 'Sleep.s_get_days', 'Activities.s_get_days', 'Monitoring.s_get_months', 'Activities.s_get_months'):
                stack.enter_context(patch(f'garmindb.analyze.{name}', return_value=[1]))
            for name in ('Activities.get_daily_stats', 'Activities.get_monthly_stats'):
                stack.enter_context(patch(f'garmindb.analyze.{name}', return_value={}))
            for name in ('DaysSummary.s_insert_or_update', 'summarydb.DaysSummary.s_insert_or_update',
                         'MonthsSummary.s_insert_or_update', 'summarydb.MonthsSummary.s_insert_or_update'):
                stack.enter_context(patch(f'garmindb.analyze.{name}'))
            for name in ('__populate_hr_intensity', '__calculate_day_stats', '__calculate_week_stats', '__calculate_monitoring_month_stats'):
                stack.enter_context(patch.object(analyze, f'_Analyze{name}'))
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                analyze._Analyze__calculate_days(2000, *([None] * 7))
                analyze._Analyze__calculate_weeks(2000, *([None] * 7))
                analyze._Analyze__calculate_months(2000, *([None] * 7))
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 10)
        self.assertTrue(all(line.endswith('visited') for line in lines[1::2]))
        self.assertIn('Analyzing weeks for 2000: 52 weeks visited', lines)
        self.assertNotIn('\r', output.getvalue())
        self.assertNotIn('\x1b', output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
