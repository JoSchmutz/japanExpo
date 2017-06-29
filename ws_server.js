/*************************************
*		WEBSOCKET SERVER PART		 *
* Link between Unity app and OpenBCI *
**************************************/

var Server = require('ws').Server;
var port = process.env.PORT || 9030;
var ws = new Server({port: port});

var sockets = [];
var apps = [];
var isFirstSession = [];

var data_1 = {};
var data_2 = {};
var sendData = false;

ws.on('connection', function(w, req){
	if(w.upgradeReq === undefined)
		w.upgradeReq = req;
  	var id = w.upgradeReq.headers['sec-websocket-key'];
  	console.log('---------- NEW CONNECTION [' + id + "] ----------");
  	w.send( JSON.stringify( { FROM : 'SERVER' , TO : "UNITY" , CMD : 'YOUR_ID' , DATA : id } ) );
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
	console.info("---- ParseMsg ----");
	console.log("Received a message : " + msg);
	/*if(typeof msg === 'object')
	{
		console.log("Msg received as an object, cast into string.");
		msg = msg.toLocaleString("fr-FR");
		console.log("Msg after translation : " + msg);
	}*/
  
	var msgObj = JSON.parse(msg);

	if(msgObj.TO === 'SERVER')
	{
		if(msgObj.CMD === "HELLO")
		{
			apps[msgObj.FROM] = id;
			console.log("App["+msgObj.FROM+"] associated to id["+id+"]")
		}
		else if(msgObj.CMD === "RECORD")
		{
			sendData = (msgObj.DATA === "ON");
			console.log( (sendData? "Starting" : "Stopping" ) + " to send data" );
		}
	}
	else if(msgObj.CMD === "SAVE")
	{
		//Analyze which app to send to and resend
		console.log('Data saved from OpenBCI['+msgObj.DATA.ID+']');
		if(sockets[apps[msgObj.TO]] != undefined && sendData)
		{
			sockets[apps[msgObj.TO]].send( msg );
		}
	}

	console.log("---- Parsing DONE ----");

};
