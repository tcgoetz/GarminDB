"""Test the console contract of the small progress iterator."""

import contextlib
import io
import unittest
from unittest.mock import Mock, patch

from garmindb.progress import progress


class TestProgress(unittest.TestCase):
    def test_default_preserves_tqdm_options_and_items(self):
        output = io.StringIO()
        items = ['one', 'two']
        with contextlib.redirect_stderr(output), patch('garmindb.progress.tqdm', return_value=items) as bar:
            self.assertEqual(list(progress(items, 'Processing files', 'files')), items)
        bar.assert_called_once_with(items, unit='files')
        self.assertEqual(output.getvalue(), '')

    def test_simple_lines_are_flushed_and_preserve_iteration(self):
        output = io.StringIO()
        stream = Mock(wraps=output)
        with contextlib.redirect_stderr(stream), patch('garmindb.progress.tqdm', side_effect=AssertionError('unexpected bar')):
            items = progress(iter(['one', 'two']), 'Processing files', 'files', simple_output=True)
            self.assertEqual(next(items), 'one')
            self.assertEqual(output.getvalue(), 'Processing files\n')
            self.assertEqual(list(items), ['two'])
        self.assertEqual(output.getvalue(), 'Processing files\nProcessing files: 2 files visited\n')
        self.assertEqual(stream.flush.call_count, 2)

    def test_empty_input(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(list(progress([], 'Processing files', 'files', simple_output=True)), [])
        self.assertEqual(output.getvalue(), 'Processing files\nProcessing files: 0 files visited\n')

    def test_one_visited_item_uses_singular_units(self):
        for unit, singular in (('files', 'file'), ('days', 'day'), ('activities', 'activity'), ('weeks', 'week'), ('months', 'month')):
            with self.subTest(unit=unit):
                output = io.StringIO()
                with contextlib.redirect_stderr(output):
                    self.assertEqual(list(progress([1], 'Processing items', unit, simple_output=True)), [1])
                self.assertEqual(output.getvalue(), f'Processing items\nProcessing items: 1 {singular} visited\n')

    def test_consumer_failure_or_interruption_does_not_print_completion(self):
        for exception in (RuntimeError, KeyboardInterrupt, SystemExit):
            with self.subTest(exception=exception):
                output = io.StringIO()
                items = progress([1, 2], 'Processing files', 'files', simple_output=True)
                with contextlib.redirect_stderr(output):
                    with self.assertRaises(exception):
                        for _ in items:
                            raise exception()
                    items.close()
                self.assertEqual(output.getvalue(), 'Processing files\n')

    def test_early_break_does_not_print_completion(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            items = progress([1, 2], 'Processing files', 'files', simple_output=True)
            for _ in items:
                break
            items.close()
        self.assertEqual(output.getvalue(), 'Processing files\n')

    def test_producer_failure_does_not_print_completion(self):
        def failing_items():
            yield 1
            raise ValueError('cannot read next item')

        output = io.StringIO()
        with contextlib.redirect_stderr(output), self.assertRaises(ValueError):
            list(progress(failing_items(), 'Processing files', 'files', simple_output=True))
        self.assertEqual(output.getvalue(), 'Processing files\n')

    def test_interleaved_modes_are_independent(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output), patch('garmindb.progress.tqdm', side_effect=lambda items, **kwargs: items) as bar:
            simple = progress([1, 2], 'Processing files', 'files', simple_output=True)
            self.assertEqual(next(simple), 1)
            self.assertEqual(list(progress([3], 'Processing files', 'files')), [3])
            self.assertEqual(list(simple), [2])
        bar.assert_called_once_with([3], unit='files')
        self.assertEqual(output.getvalue(), 'Processing files\nProcessing files: 2 files visited\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
