// Load the http module to create an http server.
var http = require('http');

// Configure our HTTP server to respond with Hello World to all requests.
var server = http.createServer(function (request, response) {
  response.writeHead(200, {"Content-Type": "text/plain"});
  text = "Running Node.js:" + process.versions.node
  text += "Mongo Servers: " + process.env.MONGODB

  response.end(text);

});

var port = process.env.PORT || 8080;
server.listen(port);

// Put a friendly message on the terminal
console.log("Server running at http://127.0.0.1:" + port + "/");