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

/* Controllers */

function SettingsController($scope, $location) {

}

function NavController($scope, $location) {
    $scope.activeClass = function (path) {
        if (path.substring(0, path.length) === path)
            return "active";
        else
            return "";
    };

    $scope.$on('$afterRouteChange', function () {
        $scope.path = $location.path();
    });
}

function ShowChartController($scope, $location, Charts) {

    $scope.loadChart = function () {

        var chart_query = {};
        if ($location.search().q !== undefined)
            chart_query.query = $location.search().q.replace("|chart", "");
        else
            chart_query.query = "*:*";

        if ($location.search().interval !== undefined)
            chart_query.interval = $location.search().interval;
        if ($location.search().since !== undefined)
            chart_query.since = $location.search().since;
        if ($location.search().since_unit !== undefined)
            chart_query.since_unit = $location.search().since_unit;
        $scope.chart = Charts.get(chart_query);
    }


    $scope.loadChart();

}


function SearchController($scope, $routeParams, $location, Logs) {
    var getResultMode = function () {
        if ($scope.query.match("\\|chart$"))
            $scope.resultMode = "chart";
        else
            $scope.resultMode = "list";

    };

    $scope.loadMorePrev = function () {

        var lastLog = $scope.logs.length;
        var moreLogs = Logs.query({q:$scope.lastQuery, before:$scope.logs[0].time / 1000,from:$scope.logs.length}, function (newLogs) {
            for (var i in newLogs) {
                $scope.logs.push(newLogs[i]);
            }

        });

    };


    // Search submit
    $scope.submitSearch = function () {
        getResultMode();
        $scope.update();
    };

    // Update log results
    $scope.update = function () {

        //TODO: The replacement string must be a regexp like |.*

        switch ($scope.resultMode) {
            case "chart":
                $scope.resultTemplate = "partials/search_chart.html";
                break;
            default:
                $scope.resultTemplate = "partials/search_list.html";
                $scope.logs = Logs.query({q:$scope.query});
                $scope.lastQuery = $scope.query;
                break;
        }


        $location.search({"q":$scope.query});
        $("#search-input").focus();
    };


    //initialization
    if ($location.search().q !== undefined) {
        $scope.query = $location.search().q
    }
    else {
        $scope.query = "";
    }

    getResultMode();
    $scope.update();
}

