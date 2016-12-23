#!/usr/bin/env python3
from celery import Celery, bootsteps
from celery.utils.log import get_task_logger
import os
import sys
import codecs
import bencoder
import hashlib
from datetime import datetime, timedelta
from glob import iglob


app = Celery('tasks')
app.config_from_object('celeryconfig')

logger = get_task_logger(__name__)
started = datetime.now()


class ArgumentsBootstep(bootsteps.Step):
    def __init__(self, worker, torrents_dir, **options):
        if torrents_dir:
            logger.info("Setting torrent file storage dir: %s", torrents_dir)
            if not os.path.isdir(torrents_dir):
                logger.warn("Torrent file storage is no directory (%s)", torrents_dir)
                exit(-1)
            app.conf['torrents_dir'] = torrents_dir


app.steps['worker'].add(ArgumentsBootstep)
app.user_options['worker'].add(lambda parser: parser.add_argument('--torrents-dir', action='store', help='Set a torrent file storage directory.'))


def _torrent_path(infohash):
    return os.path.join(app.conf['torrents_dir'], infohash.lower() + ".torrent")


def _infohash(metadata):
    sha1 = hashlib.sha1()
    info = bencoder.encode(metadata[b'info'])
    sha1.update(info)
    return sha1.hexdigest()


@app.task
def echo(value):
    return value


@app.task
def print_stats(delta = timedelta(minutes=10)):
    since = started
    if delta:
        since = max(started, datetime.now() - delta)
    infohashes = get_infohashes(since.timestamp())['infohashes']
    running = datetime.now() - since

    stats = {
        'start': started.timestamp(),
        'running': running.total_seconds(),
        'saved': len(infohashes),
        'size': 0,
        'save_rate': 0,
        'size_rate': 0,
    }

    for infohash in infohashes:
        path = _torrent_path(infohash)
        if os.path.isfile(path):
            stats['size'] = stats['size'] + os.path.getsize(path)

    if stats['running'] > 0:
        stats['save_rate'] = len(infohashes) / stats['running']
        stats['size_rate'] = stats['size'] / stats['running']

    logger.info("last %.1f mins: %d torrents / %.1f MB saved",
                running.total_seconds() / 60,
                stats['saved'],
                stats['size'] / (2 ** 20))

    logger.info("Rate: %.1f/m, %.1f/h, %.1fk/d",
                stats['save_rate'] * 60,
                stats['save_rate'] * 3600,
                stats['save_rate'] * 3.600 * 24)

    logger.info("Storage consumption rate: %.1f MB/m, %.1f GB/h, %.1f GB/d",
                stats['size_rate'] * 60 / (2 ** 20),
                stats['size_rate'] * 3600 / (2 ** 30),
                stats['size_rate'] * 3600 * 24 / (2 ** 30))

    return stats


@app.task
def has_infohash(infohash):
    path = _torrent_path(infohash)
    exists = os.path.isfile(path)

    logger.info("%s exists: %s", infohash, exists)
    return exists


@app.task
def get_infohashes(since = None):
    infohashes = []
    until = datetime.now()
    it = iglob(_torrent_path('*'))
    for file in it:
        modified = os.path.getmtime(file) if since else None
        infohash = os.path.basename(file).rstrip('.torrent')
        if not since or modified > since:
            infohashes.append(infohash)

    if since: since = datetime.fromtimestamp(since)
    logger.info("Returning %d infohashes [%s - %s]", len(infohashes), str(since) if since else "start", str(until))

    return {
        'until': until.timestamp(),
        'infohashes': infohashes
    }


@app.task
def save_torrent(hex):
    torrent = codecs.decode(hex, 'hex')
    metadata = bencoder.decode(torrent)

    infohash = calculated_infohash = _infohash(metadata)
    if b'infohash' in metadata:
        infohash = metadata[b'infohash'].decode(encoding='ascii', errors='ignore').lower()
    if infohash != calculated_infohash:
        logger.warn("Infohash mismatch (%s != %s)", infohash, calculated_infohash)
        return

    name = metadata[b'info'][b'name']
    try:
        name = name.decode(encoding='utf8', errors='ignore')
    except AttributeError:
        pass

    path = _torrent_path(infohash)
    if not os.path.isdir(os.path.dirname(path)):
        os.mkdir(os.path.dirname(path))
    if os.path.isfile(path):
        logger.warn("Have already: %s", infohash)
        return

    with open(path, 'wb') as file:
        file.write(torrent)

    logger.info('%s.torrent <= [%s]', infohash, name)


if __name__ == '__main__':
    argv = sys.argv
    if len(argv) == 1:
        argv = [
            'worker',
            '--beat',
            '--loglevel=INFO',
        ]
    app.worker_main(argv)
