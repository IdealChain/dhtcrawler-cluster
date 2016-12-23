'use strict';

var bencode = require('bencode'),
    celery = require('node-celery'),
    fs = require('fs'),
    bunyan = require('bunyan');

var log = bunyan.createLogger({name: 'worker.store', level: 'debug'});
var updateInfohashesInterval = 60 * 1000;

function Store(config) {
    var self = this;

    self.infohashes = new Set();
    self.infohashes_fetched = null;
    self.infohashes_timer = null;

    log.debug("Connecting to broker (%s)", JSON.stringify(config));

    self.client = celery.createClient(config);
    self.client.on('connect', function() {
        log.info("Broker connected (%s)", JSON.stringify(self.client.conf));

        self.client.call('tasks.echo', [Date.now()], function (res) {
            log.debug("Result backend working [echo: %s]", res.result)
        });

        self.infohashes_timer = setInterval(self.updateInfohashes.bind(self), updateInfohashesInterval);
        self.updateInfohashes();
    });
    self.client.on('error', function(err) {
        log.error(err);
    });
}

Store.prototype.hasInfohash = function(infohash, callback) {
    var self = this;

    process.nextTick(function() {
       callback(null, self.infohashes.has(infohash));
    });
};

Store.prototype.hasInfohashUnbuffered = function(infohash, callback) {
    this.client.call('tasks.has_infohash', [infohash], function(res) {
        callback(null, res.result);
    });
};

Store.prototype.saveTorrent = function(metadata, callback) {
    var self = this;
    if (!metadata.infohash || !metadata.info || !metadata.info.name) {
        if (callback) callback("Missing required infohash/info.name");
        return;
    }

    if (self.infohashes.has(metadata.infohash)) {
        return;
    }

    var name = ("" + metadata.info.name).toString('utf8');
    var torrent = bencode.encode(metadata);
    self.client.call('tasks.save_torrent', [torrent.toString('hex')], function(res) {
        self.infohashes.add(metadata.infohash);
        if (callback) callback(null, name);
    });
};

Store.prototype.updateInfohashes = function() {
    var self = this;
    self.client.call('tasks.get_infohashes', [self.infohashes_fetched], function(res) {

        if (!res.result.hasOwnProperty('until') || !res.result.hasOwnProperty('infohashes') || !Array.isArray(res.result.infohashes)) {
            log.error("Not matching expected get_infohashes result: " + res.result);
            return;
        }

        log.debug("DB has %d new infohashes since %s", res.result.infohashes.length, new Date(self.infohashes_fetched * 1000));
        for(var index in res.result.infohashes) {
            if (res.result.infohashes.hasOwnProperty(index)) {
                var infohash = res.result.infohashes[index];
                self.infohashes.add(infohash);
            }
        }

        self.infohashes_fetched = res.result.until;

        if (res.result.infohashes.length > 0)
            log.info("Now %d infohashes known and excluded", self.infohashes.size);
    });
};

Store.prototype.end = function() {
    clearInterval(this.infohashes_timer);
    if (this.client.ready)
        this.client.end();
    log.debug("Disconnected.");
};

module.exports.connect = function(config) {
    return new Store(config);
};
