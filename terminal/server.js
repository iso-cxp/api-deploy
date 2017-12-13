'use strict';

var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var file_tail = require('file-tail')
var read_last_lines = require('read-last-lines');

const n_lines = 300
const file_name = '/var/log/terminal/terminal.log'

// Read first n_lines lines
io.on('connection', function(socket){
  console.log(socket.id + ' connected');
    read_last_lines.read(file_name, n_lines)
    .then((lines) => socket.emit('init', lines))
    .catch(error => console.log(error));
});

// Tail f log file
var ft = file_tail.startTailing(file_name);
ft.on('line', function(line) {
    io.emit('terminal', line)
});

http.listen(3000, function() {
    console.log('listening on *:3000');
});
