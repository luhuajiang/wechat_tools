
var base_uri = location.origin;
var qcode_src = location.origin + '/getUUID?' + new Date().getTime();
var uuid;
var time_priod;
var base_request;
var flag = false;
var init;
var contact;
var app = angular.module("app", []);
app.controller('myCtrl', function($scope, $http, $location) {
    $scope.getConstact = function() {
        $.get('/getConstact', {pass_ticket:base_request.pass_ticket, skey:base_request.Skey}, function(data){
            console.log(data);
            contact = data;
            $scope.array = JSON.parse(contact); 
            $scope.$apply();
        });
    };
    $scope.sent = function(){
        var cks = $("input[type=checkbox]:checked");
		    var str = "";
		    $.each(cks,function(index,value){
            sendMessage($scope.msg, $(value).val());
		    });
    };

});

function sendMessage(message, toUserName){
    var user_name = JSON.parse(init).User.UserName;
    var target = "";
    console.log('toUserName' + toUserName);
    $.get('/send_msg',{message: message, user_name : user_name, to_user_name: toUserName, pass_ticket: base_request.pass_ticket,base_request: sessionStorage.getItem('base_request')}, function(data){
        console.log(data);
    });
}

function getTicket(redirect_uri) {
    $.post(base_uri + "/isLogin", {redirect_uri:redirect_uri}, function(data){
        console.log(data);
        base_request = JSON.parse(data);
        sessionStorage.setItem('base_request', data);
        webwxinit();
    });
}

function webwxinit() {
    $.get('/wxinit', {pass_ticket:base_request.pass_ticket, skey:base_request.Skey,base_request:sessionStorage.getItem('base_request')}, function(data){
        init = data;
        console.log(data);
        var appElement = document.querySelector('[ng-controller=myCtrl]');
        var $scope = angular.element(appElement).scope(); 
        $scope.getConstact();
    });
}

(function() {
    $.get(qcode_src,function(data, status){
        console.log(data);
        console.log(status);
        uuid = data;
        document.getElementById('qrcode').src = "https://login.weixin.qq.com/qrcode/" + data + "?t=webwx&_=" + new Date().getTime();
        time_priod= setInterval(confirmLogin, 1000);
    });

    function confirmLogin(){
        $.get("/isScan/" + uuid , function(data, status){
            if(data == "window.code=408;") {
                console.log("timeout");
            }
            if(data == "window.code=201;") {
                console.log("wait for confirm...");
            }
            if(data.indexOf("200") > -1) {
                console.log("login Success");
                clearInterval(time_priod);
                if (!flag) {
                    flag = true;
                    getTicket(data.substring(data.indexOf("https"),data.length -3));
                }
            }
        });
     }
})();


