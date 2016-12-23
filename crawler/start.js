#!/usr/bin/env node
'use strict';

var P2PSpider = require('p2pspider/lib'),
    Store = require('./lib/store'),
    bunyan = require('bunyan'),
    fs = require('fs'),
    bencode = require('bencode');

var log = bunyan.createLogger({name: 'worker'});
var broker_url = 'redis://';
if (process.argv.length > 2) {

    if (process.argv[2] == '-h') {
        console.log("Usage: " + process.argv.slice(0,2).join(' ') + " [redis://localhost/0]");
        process.exit(-1);
    }

    broker_url = process.argv[2];
}

var client = Store.connect({
    BROKER_URL: broker_url
});

process.on('SIGTERM', function () {
    client.end();
    process.exit(0);
});

process.on('SIGINT', function() {
   process.emit('SIGTERM');
});

var p2p = P2PSpider({
    nodesMaxSize: 400,
    maxConnections: 600,
    timeout: 30000
});

p2p.ignore(function (infohash, rinfo, callback) {
    client.hasInfohash(infohash, function(err, exists) {
        if (err) log.error(err);
        else callback(exists);
    });
});

p2p.on('metadata', function (metadata) {
    client.saveTorrent(metadata, function(err, name) {
        if (err) log.error(err);
        else log.info("%s.torrent <= [%s]", metadata.infohash, name);
    });
});

p2p.listen(6881, '0.0.0.0');

// send a torrent directly for debugging
// client.client.once('connect', function() {
//     var torrent = fs.readFileSync('e1a1e35e65454a08cde363cb5ee42fa56841a0e7.torrent');
//     var metadata = bencode.decode(torrent);
//     metadata.infohash = 'e1a1e35e65454a08cde363cb5ee42fa56841a0e7';
//     p2p.emit('metadata', metadata);
// });
