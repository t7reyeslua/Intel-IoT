angular.module('myApp').controller('AppCtrl', function($scope, $rootScope, $websocket) {
  $scope.status_gym = false;
  $scope.status_work = false;

  $scope.item1 = {'gym': true, 'work': false};
  $scope.item2 = {'gym': false, 'work': true};
  $scope.item3 = {'gym': true, 'work': true};
  $scope.item4 = {'gym': true, 'work': false};

  $scope.items = [
  $scope.item1,
  $scope.item2,
  $scope.item3,
  $scope.item4
  ]

  $scope.smartBagIP = '10.10.40.4'
  $scope.tag1 = {'id': 1, 'name': 'Tennis', 'mac': '4C:74:03:64:85:2E'}
  $scope.tag2 = {'id': 2, 'name': 'Wallet', 'mac': 'C0:EE:FB:32:E4:84'}
  $scope.tag3 = {'id': 3, 'name': 'Keys', 'mac': '5C:E8:EB:7B:87:45'}
  $scope.tag4 = {'id': 4, 'name': 'Towel', 'mac': '5C:E8:EB:7B:87:45'}

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

    if ($scope.status_gym == true){
        if ($scope.item1['gym'] == true) { tracked_tags.push($scope.tag1);}
        if ($scope.item2['gym'] == true) { tracked_tags.push($scope.tag2);}
        if ($scope.item3['gym'] == true) { tracked_tags.push($scope.tag3);}
        if ($scope.item4['gym'] == true) { tracked_tags.push($scope.tag4);}
    }
    if ($scope.status_work == true){
        if ($scope.item1['work'] == true) { tracked_tags.push($scope.tag1);}
        if ($scope.item2['work'] == true) { tracked_tags.push($scope.tag2);}
        if ($scope.item3['work'] == true) { tracked_tags.push($scope.tag3);}
        if ($scope.item4['work'] == true) { tracked_tags.push($scope.tag4);}

    }

    data['target'] = $scope.smartBagIP
    data['tags'] = tracked_tags
    console.log(data);
    $scope.send("set_tracking_place", data, -1, null);

  }

  console.log($rootScope.clientIoT);
  var callbacks = {};
  var prev_id = 1000;
  function generateID() {
        prev_id = ((prev_id - 999) % 9000) + 1000;
        return prev_id;
  }

  var WS_URL = "ws://" + "10.10.40.4" + ":8878/API-ws/";
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
