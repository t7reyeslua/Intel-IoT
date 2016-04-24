angular.module('myApp').controller('AppCtrl', function($scope, $rootScope, $websocket) {
  $scope.status_gym = false;
  $scope.status_work = false;

  $scope.item1 = {gym: true, work: false};
  $scope.item2 = {gym: false, work: false};
  $scope.item3 = {gym: true, work: true};
  $scope.item4 = {gym: true, work: true};

  $scope.items = [
  $scope.item1,
  $scope.item2,
  $scope.item3,
  $scope.item4
  ]

  $scope.tag1 = {'id': 1, 'name': 'Tennis', 'mac': 'MAC:1:1:1'}
  $scope.tag2 = {'id': 2, 'name': 'Wallet', 'mac': 'MAC:1:1:2'}
  $scope.tag3 = {'id': 3, 'name': 'Keys', 'mac': 'MAC:1:1:3'}
  $scope.tag4 = {'id': 4, 'name': 'Towel', 'mac': 'MAC:1:1:4'}

  $scope.changeStatusGym = function(){
    $scope.status_gym = !$scope.status_gym;
    if ($scope.status_gym == true){
        $scope.status_work = !$scope.status_gym;
    }
  }
  $scope.changeStatusWork = function(){
    $scope.status_work = !$scope.status_work;
    if ($scope.status_work == true){
        $scope.status_gym = !$scope.status_work;
    }
  }

  $scope.sendToServer = function(){
    console.log($scope.status_gym);
    console.log($scope.status_work);
    console.log($scope.item1);
    console.log($scope.item2);
    console.log($scope.item3);
    console.log($scope.item4);

    data = {};
    tracked_tags = [];



    //$scope.send("send_notification", data, -1, null);

  }

  console.log($rootScope.clientIoT);
  var callbacks = {};
  var prev_id = 1000;
  function generateID() {
        prev_id = ((prev_id - 999) % 9000) + 1000;
        return prev_id;
  }

  var WS_URL = "ws://" + "localhost" + ":8878/API-ws/";
  $scope.ws = $websocket.$get(WS_URL, 'control');

  $scope.$on('$destroy', function detachMessageListener() {
        $scope.ws.$un('$message');
  });
  $scope.ws.$on('$message', function msgHandler(message) {

  });

  $scope.send = function (msgtype, msg, msgid, callback) {
        if (msgid == -1) {msgid = generateID();}
        if (callback != null) {callbacks[msgid] = callback;}
        var data = {'msgid':msgid,
            'handler':$scope.ws.$$config.channelType,
            'command':msgtype,
            'data': msg};
        $scope.ws.$$send(data);
  };

});