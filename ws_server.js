var Server = require('ws').Server;
var port = process.env.PORT || 8080;
var ws = new Server({port: port});

var sockets = [];
var apps = [];
var isFirstSession = [];

ws.on('connection', function(w){

  var id = w.upgradeReq.headers['sec-websocket-key'];
  console.log('New Connection id :: ', id);
  w.send( JSON.stringify( { from : 'SERVER' , cmd : 'GET_ID' , data : id } ) );
  isFirstSession[id] = true;

  w.on('message', function(msg){
    var id = w.upgradeReq.headers['sec-websocket-key'];

    if (isFirstSession[id]){
        console.log('new Client, id = ', id);
        isFirstSession[id] = false;
    }

	ParseMsg(id, msg);

  });

  w.on('close', function() {
    var id = w.upgradeReq.headers['sec-websocket-key'];
    console.log('Closing :: ', id);
  });

  sockets[id] = w;
});

var ParseMsg = function(id, msg)
{
	console.info("---------- ParseMsg ----------");
	console.log("Received a message : " + msg);
	if(typeof msg === 'object')
	{
		console.log("Msg received as an object, cast into string.");
		msg = msg.toLocaleString();

	}
  
	var msgObj = JSON.parse(msg);
	if(msgObj.cmd === "HELLO")
	{
		apps[msgObj.from] = id;
		console.log("App["+msgObj.from+"] associated to id["+id+"]")
	}
	else
	{
		//Analyze which app to send to and resend
		if(sockets[apps[msgObj.to]] != undefined)
		{
			sockets[apps[msgObj.to]].send( msg );
			console.log("Msg transmitted to " + msgObj.to);
		}
	}

	console.log("Msg parsed.");

};
