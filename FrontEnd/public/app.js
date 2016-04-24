'use strict';

angular.module('myApp', [
  'ui.router','ngWebsocket'
]).config(function($stateProvider, $urlRouterProvider) {

    $urlRouterProvider.otherwise('/');

    $stateProvider.state('app', {
        url: '/',
        templateUrl: 'app/app.html',
        controller: 'AppCtrl'
    });

}).run(function () {

}).run(openWS);

openWS.$inject = ['$websocket', '$rootScope'];
function openWS($websocket, $rootScope) {
    console.log("opening websockets...");
    var rnd = Math.floor((Math.random() * 100) + 1);
    $rootScope.clientIoT = 'WebClient' + rnd.toString();

    var WS_URL = "ws://" + "10.10.40.4" + ":8878/API-ws/";
    var ws = $websocket.$new({
        url: WS_URL, channelType: 'control', clientName: $rootScope.clientIoT
    });

    var setChannelMode = function () {
        var data = {
            'msgid': 0,
            'handler': 'channel',
            'command': 'setchannelmode',
            'data': {
                'channelmode': this.$$config.channelType,
                'clientname': this.$$config.clientName
            }
        };
        this.$$send(data);
    };

    ws.$on('$open', setChannelMode);
}