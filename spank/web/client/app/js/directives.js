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

/* Directives */


angular.module('spank.directives', []).
    directive('appVersion', ['version', function (version) {
    return function (scope, elm) {
        elm.text(version);
    };
}])
    .directive('whenScrolledUp', function ($window, $rootElement) {
        return function (scope, elm, attr) {
            var jqWindow = $($window);
            var isScrolling = false;

            jqWindow.bind('scroll', function () {
                if (!isScrolling) {
                    if (jqWindow.scrollTop() == -5) {
                        isScrolling = true;
                        scope.$apply(attr.whenScrolledUp);
                    }
                }
                if (jqWindow.scrollTop() == 0) {
                    isScrolling = false;
                }
            });
        };
    })

    .directive('whenScrolledDown', function ($window, $rootElement) {
        return function (scope, elm, attr) {
            var jqWindow = $($window);
            var jqRootElement = $($rootElement);
            var isScrolling = false;
            jqWindow.bind('scroll', function () {
                if (!isScrolling) {
                    if (jqWindow.scrollTop() > jqRootElement.height() - jqWindow.height() + 5) {
                        isScrolling = true;
                        scope.$apply(attr.whenScrolledDown);
                    }
                }
                if (jqWindow.scrollTop() == jqRootElement.height() - jqWindow.height()) {
                    isScrolling = false;
                }

            });
        };
    })
    .directive("testchart", function () {
        var linkFn = function (scope, element, attrs) {

            function buildChart(data) {

                if (data === undefined)
                    return;

                var series = [
                    data
                ];

                var overviewSeries = [
                    {
                        data:data,
                        color:"steelblue"
                    }
                ];

                var options = {
                    xaxis:{ mode:"time" },
                    selection:{ mode:"x", color:"gray" },
                    bars:{show:false, barWidth:60 * 1000, fill:true, align:"center"},
                    lines:{show:true, fill:true},

                    series:{ color:"steelblue"},
                    grid:{borderWidth:0}
                };

                var overviewOptions = {
                    series:{
                        lines:{ show:true, lineWidth:1 },
                        shadowSize:0
                    },
                    xaxis:{ ticks:[], mode:"time" },
                    yaxis:{ ticks:[], min:0, autoscaleMargin:0.1 },
                    selection:{ mode:"x", color:"gray" }

                };

                var target = $("#chart-main");
                var overviewTarget = $("#chart-overview");

                var mainChart = $.plot(target, series, options);


                var overviewChart = $.plot(overviewTarget, overviewSeries, overviewOptions);

                target.bind("plotselected", function (event, ranges) {
                    var filteredSeries = [_.filter(data, function (d) {
                        return (d[0] >= ranges.xaxis.from && d[0] <= ranges.xaxis.to)
                    })];
                    mainChart = $.plot(target, filteredSeries, $.extend(true, {}, options, {
                        xaxis:{ min:ranges.xaxis.from, max:ranges.xaxis.to }
                    }));
                    overviewChart.setSelection(ranges, true);

                });

                overviewTarget.bind("plotselected", function (event, ranges) {
                    mainChart.setSelection(ranges);
                });


            }


            scope.$watch(function () {
                return scope.data
            }, function (value) {

                buildChart(value);

            });
        };

        return {
            restrict:'E',
            link:linkFn,
            template:'<div title="" subtitle="" data=""><div id="chart-main" style="width:900px;height:400px;" ></div> ' +
                '<div style="width:900px;height:40px;" id="chart-overview"></div></div>',
            replace:true,
            scope:{
                title:'@',
                subtitle:'@',
                data:'='
            }};


    })

;

angular.module('angularBootstrap.modal', [])
    .directive('bootstrapModal', function ($rootScope) {

        var escapeEvent, openEvent, closeEvent, linkFn;

        //Default directiveOpts
        var defaults = {
            backdrop:true,
            escapeExit:true,
            effect:null,
            effectTime:'250'
        };

        linkFn = function (scope, element, attrs) {
            //So when a modal is opened with an effect, it knows what to close it with
            var currentEffect = {};

            var directiveOpts = angular.extend(defaults, attrs);
            directiveOpts.effectTime = parseInt(directiveOpts.effectTime);

            //Escape event has to be declared so that when modal closes,
            //we only unbind modal escape and not everything
            escapeEvent = function (e) {
                if (e.which == 27)
                    closeEvent();
            };

            //Opens the modal
            openEvent = function (event, options) {
                var modalTop; //for slide effect

                //.modal child of the bootstrap-modal element is the actual div we want to control
                var modalElm = jQuery('.modal', element);

                //Fall back on directive options for parameters not given
                options = angular.extend(directiveOpts, options || {});

                //Assign currentEffect object so closeModal knows the effect
                currentEffect = { effect:options.effect, time:options.effectTime };

                //If there's an on-open attribute, call the function
                if (scope.onOpen !== undefined && scope.onOpen !== null)
                    $rootScope.$apply(function () {
                        scope.onOpen(attrs.id);
                    });

                //Make click on backdrop close modal
                if (options.backdrop === true || options.backdrop === "true") {
                    //If no backdrop el, have to add it
                    if (!document.getElementById('modal-backdrop'))
                        jQuery('body').append('<div id="modal-backdrop" class="modal-backdrop"></div>')
                    jQuery('#modal-backdrop')
                        .css({ display:'block' })
                        .bind('click', closeEvent);
                }
                //Make escape close modal unless set otherwise
                if (options.escapeExit === true || options.escapeExit === "true")
                    jQuery('body').bind('keyup', escapeEvent);

                jQuery('body').addClass('modal-open');
                jQuery('.modal-close', modalElm).bind('click', closeEvent);

                if (currentEffect.effect === 'fade') {
                    modalElm.fadeIn(currentEffect.time);

                } else if (currentEffect.effect === 'slide') {
                    //Slide modal from top. have to hide it at top first
                    modalTop = modalElm.css('top')
                    modalElm.css({ top:'-30%', display:'block' })
                        .animate({ top:modalTop }, currentEffect.time)
                } else {
                    modalElm.css({ display:'block' });
                }
            };

            //Closes the modal
            closeEvent = function (event) {
                //.modal child of the bootstrap-modal element is the actual div we want to control
                var modalElm = jQuery('.modal', element);
                var modalTop; //for slide

                //Call onClose function if it was set
                if (scope.onClose !== undefined && scope.onClose !== null)
                    $rootScope.$apply(function () {
                        scope.onClose(attrs.id);
                    });

                if (currentEffect.effect === 'fade') {
                    modalElm.fadeOut(currentEffect.time, function () {
                        modalElm.css({ display:'none' });
                    });
                } else if (currentEffect.effect === 'slide') {
                    modalTop = modalElm.css('top');
                    modalElm.animate({ top:'-30%' }, currentEffect.time, function () {
                        modalElm.css({ display:'none', top:modalTop });
                    });
                } else {
                    modalElm.css({ display:'none' });
                }

                jQuery('#modal-backdrop').unbind('click', closeEvent).css({ display:'none' });
                jQuery('body').unbind('keyup', escapeEvent).removeClass('modal-open');
            };

            //Bind modalOpen and modalClose events, so outsiders can trigger the modal
            element.bind('modalOpen', openEvent).bind('modalClose', closeEvent);

        }

        return {
            link:linkFn,
            restrict:'E',
            scope:{
                id:'attribute',
                onOpen:'evaluate',
                onClose:'evaluate'
            },
            template:'<div class="modal hide"><div ng-transclude></div></div>',
            transclude:true
        };
    })
    .factory('bootstrapModal', function () {
        return {
            show:function (modalId, options) {
                jQuery('#' + modalId).trigger('modalOpen', [options]);
            },
            hide:function (modalId) {
                jQuery('#' + modalId).trigger('modalClose');
            }
        }
    });
