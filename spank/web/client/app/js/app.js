/*
 Copyright 2012 Matias Surdi
 
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

*/
'use strict';

angular.module('spank', ['spank.filters', 'spank.services', 'spank.directives', "spank.common",
    "angularBootstrap.modal"]).
    config(['$routeProvider', function ($routeProvider) {
    $routeProvider.when('/search/chart/', {
        templateUrl:'partials/search.html',
        controller:SearchController
    });
    $routeProvider.when('/search/', {
        templateUrl:'partials/search.html',
        controller:SearchController
    });

    $routeProvider.otherwise({
        redirectTo:'/search'
    });
}]);

angular.module('spank.common', []).config(function ($httpProvider) {
    $httpProvider.responseInterceptors.push('myHttpInterceptor');
    var spinnerFunction = function (data, headersGetter) {
        if (angular.loading_timer)
            clearTimeout(angular.loading_timer);
        angular.loading_timer = setTimeout(function () {
            $('#loading').show();
        }, 200);
        return data;

    };

    $httpProvider.defaults.transformRequest.push(spinnerFunction);
})
    .factory('myHttpInterceptor', function ($q) {
        return function (promise) {
            return promise.then(function (response) {
                    clearTimeout(angular.loading_timer);
                    $('#loading').hide();
                    return response;

                },
                function (response) {
                    clearTimeout(angular.loading_timer);
                    $('#loading').hide();
                    return $q.reject(response);
                });
        };
    })

;
