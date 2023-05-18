import typing
import os, io, shutil, gzip, platform, re
from enum import Enum

from pocketutils.core.exceptions import PathIsNotADirError, MissingResourceError

import json, sys
import unicodedata
from itertools import chain
import signal
import operator
from datetime import date, datetime
from typing import Callable, TypeVar, Iterator, Iterable, Optional, List, Any, Sequence, Mapping, Dict, ItemsView, KeysView, ValuesView, Tuple, Union
from hurry.filesize import size as hsize

from pocketutils.core.exceptions import LookupFailedError, MultipleMatchesError, ParsingError, ResourceError, MissingConfigKeyError, \
NaturalExpectedError, HashValidationError, FileDoesNotExistError

import logging
import subprocess
from subprocess import Popen, PIPE
from queue import Queue
from threading import Thread
from deprecated import deprecated

import datetime
#from datetime import datetime
from subprocess import Popen, PIPE
from infix import shift_infix, mod_infix, sub_infix

from colorama import Fore
import shutil
import argparse

import hashlib
import codecs
import gzip

import struct
from array import array
import numpy as np

def blob_to_byte_array(bytes_obj: bytes):
	return _blob_to_dt(bytes_obj, 'b', 1, np.ubyte) + 128
def blob_to_float_array(bytes_obj: bytes):
	return _blob_to_dt(bytes_obj, 'f', 4, np.float32)
def blob_to_double_array(bytes_obj: bytes):
	return _blob_to_dt(bytes_obj, 'd', 8, np.float64)
def blob_to_short_array(bytes_obj: bytes):
	return _blob_to_dt(bytes_obj, 'H', 2, np.int16)
def blob_to_int_array(bytes_obj: bytes):
	return _blob_to_dt(bytes_obj, 'I', 4, np.int32)
def blob_to_long_array(bytes_obj: bytes):
	return _blob_to_dt(bytes_obj, 'Q', 8, np.int64)
def _blob_to_dt(bytes_obj: bytes, data_type_str: str, data_type_len: int, dtype):
	return np.array(next(iter(struct.iter_unpack('>' + data_type_str * int(len(bytes_obj)/data_type_len), bytes_obj))), dtype=dtype)

class FileHasher:

	def __init__(self, algorithm: Callable[[], Any]=hashlib.sha1, extension: str='.sha1', buffer_size: int = 16*1024):
		self.algorithm = algorithm
		self.extension = extension
		self.buffer_size = buffer_size

	def hashsum(self, file_name: str) -> str:
		alg = self.algorithm()
		with open(file_name, 'rb') as f:
			for chunk in iter(lambda: f.read(self.buffer_size), b''):
				alg.update(chunk)
		return alg.hexdigest()

	def add_hash(self, file_name: str) -> None:
		with open(file_name + self.extension, 'w', encoding="utf8") as f:
			s = self.hashsum(file_name)
			f.write(s)

	def check_hash(self, file_name: str) -> bool:
		if not os.path.isfile(file_name + self.extension): return False 
		with open(file_name + self.extension, 'r', encoding="utf8") as f:
			hash_str = f.read().split()[0] # check only the first thing on the line before any spaces
			return hash_str == self.hashsum(file_name)

	def check_and_open(self, file_name: str, *args):
		return self._o(file_name, opener=lambda f: codecs.open(f, encoding='utf-8'), *args)

	def check_and_open_gzip(self, file_name: str, *args):
		return self._o(file_name, opener=gzip.open, *args)

	def _o(self, file_name: str, opener, *args):
		if not os.path.isfile(file_name + self.extension):
			raise FileDoesNotExistError("Hash for file {} does not exist".format(file_name))
		with open(file_name + self.extension, 'r', encoding="utf8") as f:
			if f.read() != self.hashsum(file_name):
				raise HashValidationError("Hash for file {} does not match".format(file_name))
		return opener(file_name, *args)

def mkdatetime(s: str) -> datetime:
	return datetime.strptime(s.replace(' ', 'T'), "%Y-%m-%dT%H:%M:%S")

def now() -> datetime:
	return datetime.datetime.now()

def today() -> datetime:
	return datetime.datetime.today()

def mkdate(s: str) -> datetime:
	return datetime.strptime(s, "%Y-%m-%d")

def this_year(s: str) -> datetime:
	return datetime.strptime(s, "%Y")

def year_range(year: int) -> Tuple[datetime.datetime, datetime.datetime]:
	return (
		datetime(year, 1, 1, 0, 0, 0, 0),
		datetime(year, 12, 31, 23, 59, 59, 999)
	)

@shift_infix
def approxeq(a, b):
	"""This takes 1e-09 * max(abs(a), abs(b)), which may not be appropriate."""
	"""Example: 5 <<approxeq>> 5.000000000000001"""
	return abs(a - b) < 1e-09 * max(abs(a), abs(b))

class TomlData:
	"""A better TOML data structure than a plain dict.
	Usage examples:
		data = TomlData({'x': {'y': {'z': 155}}})
		print(data['x.y.z'])   # prints 155
		data.sub('x.y')        # returns a new TomlData for {'z': 155}
		data.nested_keys()     # returns all keys and sub-keys
	"""
	def __init__(self, top_level_item: Dict[str, object]):
		assert top_level_item is not None
		self.top = top_level_item

	def __str__(self) -> str:
		return repr(self)
	def __repr__(self) -> str:
		return "TomlData({})".format(str(self.top))

	def __getitem__(self, key: str) -> Dict[str, object]:
		return self.sub(key).top

		def __contains__(self, key: str) -> bool:
			try:
					self.sub(key)
					return True
			except AttributeError: return False

	def get_str(self, key: str) -> str:
		return str(self.__as(key, str))

	def get_int(self, key: str) -> int:
		# noinspection PyTypeChecker
		return int(self.__as(key, int))

	def get_bool(self, key: str) -> int:
		# noinspection PyTypeChecker
		return bool(self.__as(key, bool))

	def get_str_list(self, key: str) -> List[str]:
		return self.__as_list(key, str)

	def get_int_list(self, key: str) -> List[int]:
		return self.__as_list(key, int)

	def get_float_list(self, key: str) -> List[int]:
		return self.__as_list(key, int)

	def get_bool_list(self, key: str) -> List[int]:
		return self.__as_list(key, bool)

	def get_float(self, key: str) -> int:
		# noinspection PyTypeChecker
		return int(self.__as(key, float))

	def __as_list(self, key: str, clazz):
		def to(v):
			if not isinstance(v, clazz):
				raise TypeError("{}={} is a {}, not {}".format(key, v, type(v), clazz))
			return [to(v) for v in self[key]]

	def __as(self, key: str, clazz):
		v = self[key]
		if isinstance(v, clazz):
			return v
		else:
			raise TypeError("{}={} is a {}, not {}".format(key, v, type(v), clazz))

	def sub(self, key: str):
		"""Returns a new TomlData with its top set to items[1][2]..."""
		items = key.split('.')
		item = self.top
		for i, s in enumerate(items):
			if s not in item: raise MissingConfigEntry(
				"{} is not in the TOML; failed at {}"
				.format(key, '.'.join(items[:i+1]))
			)
			item = item[s]
		return TomlData(item)

	def items(self) -> ItemsView[str, object]:
		return self.top.items()

	def keys(self) -> KeysView[str]:
		return self.top.keys()

	def values(self) -> ValuesView[object]:
		return self.top.values()

	def nested_keys(self, separator='.') -> Iterator[str]:
		for lst in self.nested_key_lists(self.top):
			yield separator.join(lst)

	def nested_key_lists(self, dictionary: Dict[str, object], prefix=None) -> Iterator[List[str]]:

		prefix = prefix[:] if prefix else []

		if isinstance(dictionary, dict):
			for key, value in dictionary.items():

				if isinstance(value, dict):
					for result in self.nested_key_lists(value, [key] + prefix): yield result
				else: yield prefix + [key]

		else: yield dictionary


def git_commit_hash(git_repo_dir: str='.') -> str:
	"""Gets the hex of the most recent Git commit hash in git_repo_dir."""
	p = Popen(['git', 'rev-parse', 'HEAD'], stdout=PIPE, cwd=git_repo_dir)
	(out, err) = p.communicate()
	exit_code = p.wait()
	if exit_code != 0: raise ValueError("Got nonzero exit code {} from git rev-parse".format(exit_code))
	return out.decode('utf-8').rstrip()

@deprecated(reason="Use klgists.common.flexible_logger instead.")
def init_logger(
	log_path: Optional[str]=None,
	format_str: str='%(asctime)s %(levelname)-8s: %(message)s',
	to_std: bool=True,
	child_logger_name: Optional[str]=None,
	std_level = logging.INFO,
	file_level = logging.DEBUG
):
	"""Initializes a logger that can write to a log file and/or stdout."""

	if log_path is not None and not os.path.exists(os.path.dirname(log_path)):
		os.mkdir(os.path.dirname(log_path))

	if child_logger_name is None:
		logger = logging.getLogger()
	else:
		logger = logging.getLogger(child_logger_name)
	logger.setLevel(logging.NOTSET)

	formatter = logging.Formatter(format_str)

	if log_path is not None:
		handler = logging.FileHandler(log_path, encoding='utf-8')
		handler.setLevel(file_level)
		handler.setFormatter(formatter)
		logger.addHandler(handler)

	if to_std:
		handler = logging.StreamHandler()
		handler.setLevel(std_level)
		handler.setFormatter(formatter)
		logger.addHandler(handler)

import datetime
def format_time(time: datetime) -> str:
	"""Standard timestamp format. Ex: 2016-05-02_22_35_56."""
	return time.strftime("%Y-%m-%d_%H-%M-%S")

def timestamp() -> str:
	"""Standard timestamp of time now. Ex: 2016-05-02_22_35_56."""
	return format_time(datetime.datetime.now())

def timestamp_path(path: str) -> str:
	"""Standard way to label a file path with a timestamp."""
	return "{}-{}".format(path, timestamp())


def nice_time(n_ms: int) -> str:
	length = datetime.datetime(1, 1, 1) + datetime.timedelta(milliseconds=n_ms)
	if n_ms < 1000 * 60 * 60 * 24:
		return "{}h, {}m, {}s".format(length.hour, length.minute, length.second)
	else:
		return "{}d, {}h, {}m, {}s".format(length.day, length.hour, length.minute, length.second)


def parse_local_iso_datetime(z: str) -> datetime:
	return datetime.datetime.strptime(z, '%Y-%m-%dT%H:%M:%S.%f')


logger = logging.getLogger(__name__)

class PipeType(Enum):
	STDOUT = 1
	STDERR = 2

def _disp(out, ell, name):
	out = out.strip()
	if '\n' in out:
		ell(name + ":\n<<=====\n" + out + '\n=====>>')
	elif len(out) > 0:
		ell(name + ": <<===== " + out + " =====>>")
	else:
		ell(name + ": <no output>")
	

def _log(out, err, ell):
	_disp(out, ell, "stdout")
	_disp(err, ell, "stderr")

	
def smart_log_callback(source, line, prefix: str = '') -> None:
	line = line.decode('utf-8')
	if line.startswith('FATAL:'):
		logger.fatal(prefix + line)
	elif line.startswith('ERROR:'):
		logger.error(prefix + line)
	elif line.startswith('WARNING:'):
		logger.warning(prefix + line)
	elif line.startswith('INFO:'):
		logger.info(prefix + line)
	elif line.startswith('DEBUG:'):
		logger.debug(prefix + line)
	else:
		logger.debug(prefix + line)


def _reader(pipe_type, pipe, queue):
	try:
		with pipe:
			for line in iter(pipe.readline, b''):
				queue.put((pipe_type, line))
	finally:
		queue.put(None)
	
def stream_cmd_call(cmd: List[str], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell_cmd: str=None, cwd: Optional[str] = None, timeout_secs: Optional[float] = None, log_callback: Callable[[PipeType, bytes], None] = None, bufsize: Optional[int] = None) -> None:
	"""Calls an external command, waits, and throws a ResourceError for nonzero exit codes.
	Returns (stdout, stderr).
	The user can optionally provide a shell to run the command with, e.g. "powershell.exe" 
	"""
	if log_callback is None:
		log_callback = smart_log_callback
	cmd = [str(p) for p in cmd]
	if shell_cmd:
		cmd = [shell_cmd] + cmd
	logger.debug("Streaming '{}'".format(' '.join(cmd)))
	
	p = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=cwd, bufsize=bufsize)
	try:
		q = Queue()
		Thread(target=_reader, args=[PipeType.STDOUT, p.stdout, q]).start()
		Thread(target=_reader, args=[PipeType.STDERR, p.stderr, q]).start()
		for _ in range(2):
			for source, line in iter(q.get, None):
				log_callback(source, line)
		exit_code = p.wait(timeout=timeout_secs)
	finally:
		p.kill()
	if exit_code != 0:
		raise ResourceError("Got nonzero exit code {} from '{}'".format(exit_code, ' '.join(cmd)), cmd, exit_code, '<<unknown>>', '<<unknown>>')
	

def wrap_cmd_call(cmd: List[str], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell_cmd: str=None, cwd: Optional[str] = None, timeout_secs: Optional[float] = None) -> (str, str):
	"""Calls an external command, waits, and throws a ResourceError for nonzero exit codes.
	Returns (stdout, stderr).
	The user can optionally provide a shell to run the command with, e.g. "powershell.exe" 
	"""
	cmd = [str(p) for p in cmd]
	if shell_cmd:
		cmd = [shell_cmd] + cmd
	logger.debug("Calling '{}'".format(' '.join(cmd)))
	p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, cwd=cwd)
	out, err, exit_code = None, None, None
	try:
		(out, err) = p.communicate(timeout=timeout_secs)
		out = out.decode('utf-8')
		err = err.decode('utf-8')
		exit_code = p.wait(timeout=timeout_secs)
	except Exception as e:
		_log(out, err, logger.warning)
		raise e
	finally:
		p.kill()
	if exit_code != 0:
		_log(out, err, logger.warning)
		raise ResourceError("Got nonzero exit code {} from '{}'".format(exit_code, ' '.join(cmd)), cmd, exit_code, out, err)
	_log(out, err, logger.debug)
	return out, err

def look(obj: object, attrs: str) -> any:
	if not isinstance(attrs, str) and isinstance(attrs, Iterable): attrs = '.'.join(attrs)
	try:
		return operator.attrgetter(attrs)(obj)
	except AttributeError: return None

def flatmap(func, *iterable):
	return chain.from_iterable(map(func, *iterable))

def flatten(*iterable):
	return list(chain.from_iterable(iterable))

class DevNull:
	def write(self, msg): pass

pjoin = os.path.join
pexists = os.path.exists
pdir = os.path.isdir
pfile = os.path.isfile
pis_dir = os.path.isdir
fsize = os.path.getsize
def pardir(path: str, depth: int=1):
	for _ in range(-1, depth):
		path = os.path.dirname(path)
	return path
def grandpardir(path: str):
	return pardir(path, 2)


T = TypeVar('T')
def try_index_of(element: List[T], list_element: T) -> Optional[T]:
	try:
		index_element = list_element.index(element)
		return index_element
	except ValueError:
		return None

def decorator(cls):
	return cls


def exists(keep_predicate: Callable[[T], bool], seq: Iterable[T]) -> bool:
	"""Efficient existential quantifier for a filter() predicate.
	Returns true iff keep_predicate is true for one or more elements."""
	for e in seq:
		if keep_predicate(e): return True  # short-circuit
	return False


def zip_strict(*args):
	"""Same as zip(), but raises an IndexError if the lengths don't match."""
	iters = [iter(axis) for axis in args]
	n_elements = 0
	failures = []
	while len(failures) == 0:
		n_elements += 1
		values = []
		failures = []
		for axis, iterator in enumerate(iters):
			try:
				values.append(next(iterator))
			except StopIteration:
				failures.append(axis)
		if len(failures) == 0:
			yield tuple(values)
	if len(failures) == 1:
		raise IndexError("Too few elements ({}) along axis {}".format(n_elements, failures[0]))
	elif len(failures) < len(iters):
		raise IndexError("Too few elements ({}) along axes {}".format(n_elements, failures))


def only(sequence: Iterable[Any]) -> Any:
	"""
	Returns either the SINGLE (ONLY) UNIQUE ITEM in the sequence or raises an exception.
	Each item must have __hash__ defined on it.
	:param sequence: A list of any items (untyped)
	:return: The first item the sequence.
	:raises: ValarLookupError If the sequence is empty
	:raises: MultipleMatchesError If there is more than one unique item.
	"""
	st = set(sequence)
	if len(st) > 1:
		raise MultipleMatchesError("More then 1 item in {}".format(sequence))
	if len(st) == 0:
		raise LookupFailedError("Empty sequence")
	return next(iter(st))


def read_lines_file(path: str, ignore_comments: bool = False) -> Sequence[str]:
	"""
	Returns a list of lines in a file, potentially ignoring comments.
	:param path: Read the file at this local path
	:param ignore_comments: Ignore lines beginning with #, excluding whitespace
	:return: The lines, with surrounding whitespace stripped
	"""
	lines = []
	with open(path) as f:
		line = f.readline().strip()
		if not ignore_comments or not line.startswith('#'):
			lines.append(line)
	return lines


def read_properties_file(path: str) -> Mapping[str, str]:
	"""
	Reads a .properties file, which is a list of lines with key=value pairs (with an equals sign).
	Lines beginning with # are ignored.
	Each line must contain exactly 1 equals sign.
	:param path: Read the file at this local path
	:return: A dict mapping keys to values, both with surrounding whitespace stripped
	"""
	lines = read_lines_file(path, ignore_comments=False)
	dct = {}
	for i, line in enumerate(lines):
		if line.startswith('#'): continue
		if line.count('=') != 1:
			raise ParsingError("Bad line {} in {}".format(i+1, path))
		parts = line.split('=')
		dct[parts[0].strip()] = parts[1].strip()
	return dct


class Comparable:
	"""A class that's comparable. Just implement __lt__. Credit ot Alex Martelli on https://stackoverflow.com/questions/1061283/lt-instead-of-cmp"""

	def __eq__(self, other):
		return not self < other and not other < self

	def __ne__(self, other):
		return self < other or other < self

	def __gt__(self, other):
		return other < self

	def __ge__(self, other):
		return not self < other

	def __le__(self, other):
		return not other < self


def json_serial(obj):
	"""JSON serializer for objects not serializable by default json code.
	From jgbarah at https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
	"""
	if isinstance(obj, (datetime, date)):
		return obj.isoformat()
	try:
		import peewee
		if isinstance(obj, peewee.Field):
			return type(obj).__name__
	except ImportError: pass
	raise TypeError("Type %s not serializable" % type(obj))

def pretty_dict(dct: dict) -> str:
	"""Returns a pretty-printed dict, complete with indentation. Will fail on non-JSON-serializable datatypes."""
	return json.dumps(dct, default=json_serial, sort_keys=True, indent=4)

def pp_dict(dct: dict) -> None:
	"""Pretty-prints a dict to stdout."""
	print(pretty_dict(dct))

def pp_size(obj: object) -> None:
	"""Prints to stdout a human-readable string of the memory usage of arbitrary Python objects. Ex: 8M for 8 megabytes."""
	print(hsize(sys.getsizeof(obj)))

def sanitize_str(value: str) -> str:
	"""Removes Unicode control (Cc) characters EXCEPT for tabs (\t), newlines (\n only), line separators (U+2028) and paragraph separators (U+2029)."""
	return "".join(ch for ch in value if unicodedata.category(ch) != 'Cc' and ch not in {'\t', '\n', '\u2028', '\u2029'})

def escape_for_properties(value: Any) -> str:
	return sanitize_str(str(value).replace('\n', '\u2028'))

def escape_for_tsv(value: Any) -> str:
	return sanitize_str(str(value).replace('\n', '\u2028').replace('\t', ' '))
	
class Timeout:
	def __init__(self, seconds: int = 10, error_message='Timeout'):
		self.seconds = seconds
		self.error_message = error_message
	def handle_timeout(self, signum, frame):
		raise TimeoutError(self.error_message)
	def __enter__(self):
		signal.signal(signal.SIGALRM, self.handle_timeout)
		signal.alarm(self.seconds)
	def __exit__(self, type, value, traceback):
		signal.alarm(0)


class OverwriteChoice(Enum):
	FAIL = 1
	WARN = 2
	IGNORE = 3
	OVERWRITE = 4

def fix_path(path: str) -> str:
	# ffmpeg won't recognize './' and will simply not write images!
	# and Python doesn't recognize ~
	if '%' in path: raise ValueError(
		'For technical limitations (regarding ffmpeg), local paths cannot contain a percent sign (%), but "{}" does'.format(path)
	)
	if path == '~': return os.environ['HOME']  # prevent out of bounds
	if path.startswith('~'):
		path = pjoin(os.environ['HOME'], path[2:])
	return path.replace('./', '')

def fix_path_platform_dependent(path: str) -> str:
	"""Modifies path strings to work with Python and external tools.
	Replaces a beginning '~' with the HOME environment variable.
	Also accepts either / or \ (but not both) as a path separator in windows. 
	"""
	path = fix_path(path)
	# if windows, allow either / or \, but not both
	if platform.system() == 'Windows':
		bits = re.split('[/\\\\]', path)
		return pjoin(*bits).replace(":", ":\\")
	else:
		return path


# NTFS doesn't allow these, so let's be safe
# Also exclude control characters
# 127 is the DEL char
_bad_chars = {'/', ':', '<', '>', '"', "'", '\\', '|', '?', '*', chr(127), *{chr(i) for i in range(0, 32)}}
assert ' ' not in _bad_chars
def _sanitize_bit(p: str) -> str:
	for b in _bad_chars: p = p.replace(b, '-')
	return p
def pjoin_sanitized_rel(*pieces: Iterable[any]) -> str:
	"""Builds a path from a hierarchy, sanitizing the path by replacing /, :, <, >, ", ', \, |, ?, *, <DEL>, and control characters 0–32 with a hyphen-minus (-).
	Each input to pjoin_sanitized must refer only to a single directory or file (cannot contain a path separator).
	This means that you cannot have an absolute path (it would begin with os.path (probably /); use pjoin_sanitized_abs for this.
	"""
	return pjoin(*[_sanitize_bit(str(bit)) for bit in pieces])
def pjoin_sanitized_abs(*pieces: Iterable[any]) -> str:
	"""Same as pjoin_sanitized_rel but starts with os.sep (the root directory)."""
	return pjoin(os.sep, pjoin_sanitized_rel(*pieces))


def make_dirs(output_dir: str):
	"""Makes a directory if it doesn't exist.
	May raise a PathIsNotADirError.
	"""
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	elif not os.path.isdir(output_dir):
		raise PathIsNotADirError("{} already exists and is not a directory".format(output_dir))


def remake_dirs(output_dir: str):
	"""Makes a directory, remaking it if it already exists.
	May raise a PathIsNotADirError.
	"""
	if os.path.exists(output_dir) and os.path.isdir(output_dir):
		shutil.rmtree(output_dir)
	elif os.path.exists(output_dir):
		raise PathIsNotADirError("{} already exists and is not a directory".format(output_dir))
	make_dirs(output_dir)



def lines(file_name: str, known_encoding='utf-8') -> Iterator[str]:
	"""Lazily read a text file or gzipped text file, decode, and strip any newline character (\n or \r).
	If the file name ends with '.gz' or '.gzip', assumes the file is Gzipped.
	Arguments:
		known_encoding: Applied only when decoding gzip
	"""
	if file_name.endswith('.gz') or file_name.endswith('.gzip'):
		with io.TextIOWrapper(gzip.open(file_name, 'r'), encoding=known_encoding) as f:
			for line in f: yield line.rstrip('\n\r')
	else:
		with open(file_name, 'r') as f:
			for line in f: yield line.rstrip('\n\r')

import dill

def pkl(data, path: str):
	with open(path, 'wb') as f:
		dill.dump(data, f)

def unpkl(path: str):
	with open(path, 'rb') as f:
		return dill.load(f)


def file_from_env_var(var: str) -> str:
	"""
	Just returns the path of a file specified in an environment variable, checking that it's a file.
	Will raise a MissingResourceError error if not set or not a file.
	:param var: The environment variable name, not including the $
	"""
	if var not in os.environ:
		raise MissingResourceError('Environment variable ${} is not set'.format(var))
	config_file_path = fix_path(os.environ[var])
	if not pexists(config_file_path):
		raise MissingResourceError("{} file {} does not exist".format(var, config_file_path))
	if not pfile(config_file_path):
		raise MissingResourceError("{} file {} is not a file".format(var, config_file_path))
	return config_file_path


def is_proper_file(path: str) -> bool:
	name = os.path.split(path)[1]
	return len(name) > 0 and name[0] not in {'.', '~', '_'}


def scantree(path: str, follow_symlinks: bool=False) -> Iterator[str]:
	"""List the full path of every file not beginning with '.', '~', or '_' in a directory, recursively.
	.. deprecated Use scan_for_proper_files, which has a better name
	"""
	for entry in os.scandir(path):
		if entry.is_dir(follow_symlinks=follow_symlinks):
			yield from scantree(entry.path)
		elif is_proper_file(entry.path):
			yield entry.path

scan_for_proper_files = scantree


def scan_for_files(path: str, follow_symlinks: bool=False) -> Iterator[str]:
	"""
	Using a generator, list all files in a directory or one of its subdirectories.
	Useful for iterating over files in a directory recursively if there are thousands of file.
	Warning: If there are looping symlinks, follow_symlinks will return an infinite generator.
	"""
	for d in os.scandir(path):
		if d.is_dir(follow_symlinks=follow_symlinks):
			yield from scan_for_files(d.path)
		else:
			yield d.path


def walk_until(some_dir, until: Callable[[str], bool]) -> Iterator[typing.Tuple[str, str, str]]:
	"""Walk but stop recursing after 'until' occurs.
	Returns files and directories in the same manner as os.walk
	"""
	some_dir = some_dir.rstrip(os.path.sep)
	assert os.path.isdir(some_dir)
	for root, dirs, files in os.walk(some_dir):
			yield root, dirs, files
			if until(root):
					del dirs[:]


def walk_until_level(some_dir, level: Optional[int]=None) -> Iterator[typing.Tuple[str, str, str]]:
	"""
	Walk up to a maximum recursion depth.
	Returns files and directories in the same manner as os.walk
	Taken partly from https://stackoverflow.com/questions/7159607/list-directories-with-a-specified-depth-in-python
	:param some_dir:
	:param level: Maximum recursion depth, starting at 0
	"""
	some_dir = some_dir.rstrip(os.path.sep)
	assert os.path.isdir(some_dir)
	num_sep = some_dir.count(os.path.sep)
	for root, dirs, files in os.walk(some_dir):
			yield root, dirs, files
			num_sep_this = root.count(os.path.sep)
			if level is None or num_sep + level <= num_sep_this:
					del dirs[:]


class SubcommandHandler:
	"""A convenient wrapper for a program that uses command-line subcommands.
	Calls any method that belongs to the target
	:param parser: Should contain a description and help text, but should NOT contain any arguments.
	:param target: An object (or type) that contains a method for each subcommand; a dash (-) in the argument is converted to an underscore.
	:param temp_dir: A temporary directory
	:param error_handler: Called logging any exception except for KeyboardInterrupt or SystemExit (exceptions in here are ignored)
	:param cancel_handler: Called after logging a KeyboardInterrupt or SystemExit (exceptions in here are ignored)
	"""
	def __init__(self,
			parser: argparse.ArgumentParser, target: Any,
			temp_dir: Optional[str] = None,
			error_handler: Callable[[BaseException], None] = lambda e: None,
			cancel_handler: Callable[[Union[KeyboardInterrupt, SystemExit]], None] = lambda e: None
	) -> None:
		parser.add_argument('subcommand', help='Subcommand to run')
		self.parser = parser
		self.target = target
		self.temp_dir = temp_dir
		self.error_handler = error_handler
		self.cancel_handler = cancel_handler


	def run(self, args: List[str]) -> None:

		full_args = self.parser.parse_args(args[1:2])
		subcommand = full_args.subcommand.replace('-', '_')

		if not hasattr(self.target, subcommand) and not subcommand.startswith('_'):
			print(Fore.RED + 'Unrecognized subcommand {}'.format(subcommand))
			self.parser.print_help()
			return

		# clever; from Chase Seibert: https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
		# use dispatch pattern to invoke method with same name
		try:
			if self.temp_dir is not None:
				if pexists(self.temp_dir) and pdir(self.temp_dir): shutil.rmtree(self.temp_dir)
				elif pexists(self.temp_dir): raise PathIsNotADirError(self.temp_dir)
				remake_dirs(self.temp_dir)
				logger.debug("Created temp dir at {}".format(self.temp_dir))
			getattr(self.target, subcommand)()
		except NaturalExpectedError as e:
			pass  # ignore totally
		except KeyboardInterrupt as e:
			try:
				logger.fatal("Received cancellation signal", exc_info=True)
				self.cancel_handler(e)
			except BaseException: pass
			raise e
		except SystemExit as e:
			try:
				logger.fatal("Received system exit signal", exc_info=True)
				self.cancel_handler(e)
			except BaseException: pass
			raise e
		except BaseException as e:
			try:
				logger.fatal("{} failed!".format(self.parser.prog), exc_info=True)
				self.error_handler(e)
			except BaseException: pass
			raise e
		finally:
			if self.temp_dir is not None:
				if pexists(self.temp_dir):
					logger.debug("Deleted temp dir at {}".format(self.temp_dir))
					shutil.rmtree(self.temp_dir)
					try:
						os.remove(self.temp_dir)
					except IOError: pass

#__all__ = ['scan_for_files', 'walk_until', 'walk_until_level']
