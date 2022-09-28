import unittest
from typing import cast

from six import StringIO

from mock import Mock
from datetime import datetime

from trashcli.put.trash_directories_finder import TrashDirectoriesFinder
from trashcli.put.file_trasher import FileTrasher
from trashcli.put.reporter import TrashPutReporter
from trashcli.put.trash_result import TrashResult
from trashcli.put.my_logger import MyLogger
import os


class TestFileTrasher(unittest.TestCase):
    def setUp(self):
        self.reporter = Mock()
        self.fs = Mock()
        self.volumes = Mock()

        trash_directories_finder = Mock(spec=['possible_trash_directories_for'])
        trash_directories_finder.possible_trash_directories_for.return_value = []

        self.environ = {'XDG_DATA_HOME': '/xdh'}
        trash_directories_finder = TrashDirectoriesFinder(self.volumes)
        self.file_trasher = FileTrasher(self.fs,
                                        self.volumes,
                                        lambda x: x,
                                        datetime.now,
                                        trash_directories_finder,
                                        os.path.dirname)
        self.logger = cast(MyLogger, Mock())
        self.possible_trash_directories = Mock()
        self.possible_trash_directories.trash_directories_for.return_value = \
            [('/.Trash/1001', '/', 'relative_paths', 'top_trash_dir_rules'),
             ('/.Trash-1001', '/', 'relative_paths', 'all_is_ok_rules')]

    def test_log_volume(self):
        self.volumes.volume_of.return_value = '/'
        result = TrashResult(False)
        self.file_trasher.trash_file('a-dir/with-a-file',
                                     False,
                                     None,
                                     result,
                                     self.logger,
                                     cast(TrashPutReporter, self.reporter),
                                     {},
                                     1001,
                                     self.possible_trash_directories,
                                     'trash-put',
                                     99)

        self.reporter.volume_of_file.assert_called_with('/', 'trash-put', 99)

    def test_should_report_when_trash_fail(self):
        self.volumes.volume_of.return_value = '/'
        self.fs.move.side_effect = IOError

        result = TrashResult(False)
        self.file_trasher.trash_file('non-existent',
                                     None,
                                     None,
                                     result,
                                     self.logger,
                                     cast(TrashPutReporter, self.reporter),
                                     {},
                                     1001,
                                     self.possible_trash_directories,
                                     'trash-put',
                                     99)

        self.reporter.unable_to_trash_file.assert_called_with('non-existent',
                                                              'trash-put')

    def test_when_path_does_not_exists(self):
        self.volumes.volume_of.return_value = '/disk'
        stderr = StringIO()
        logger = MyLogger(stderr)
        reporter = TrashPutReporter(logger, {})
        result = TrashResult(False)

        self.file_trasher.trash_file("non-existent", None, None, result, logger,
                                     reporter, self.environ, 1001,
                                     self.possible_trash_directories,
                                     'trash-put',
                                     99)

        assert stderr.getvalue().splitlines() == [
            'trash-put: Volume of file: /disk',
            'trash-put: found unsecure .Trash dir (should not be a symlink): /.Trash',
            'trash-put: trash directory /.Trash/1001 is not secure',
            'trash-put: Trash-dir: /.Trash-1001 from volume: /disk',
            'trash-put: .trashinfo created as /.Trash-1001/info/non-existent.trashinfo.',
            "trash-put: 'non-existent' trashed in /.Trash-1001"]
