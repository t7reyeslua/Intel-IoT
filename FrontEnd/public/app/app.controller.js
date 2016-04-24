angular.module('myApp').controller('AppCtrl', function($scope) {
  $scope.message = 'Hello!';

  $scope.status_gym = false;
  $scope.status_work = false;

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

});