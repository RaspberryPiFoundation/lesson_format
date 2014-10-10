/*
pdf.js

This file is used by phantomjs to do some bits of html injection
and reshuffling, to prepare lessons for pdf generation.
*/

var makeUnbreakable = function(className) {
    var elements = document.getElementsByClassName(className);
    for (var i = 0; i < elements.length; i++) {
        elements[i].className += " unbreakable";
    }
};

window.onload = function () {
    /*
    Add a span around the lesson number, so it can be made giant
    in the header.

    NB the alternative is to fix the manifest information and remove the
    word "level" from all, then modify the template accordingly.
    */
    var lvl = document.getElementsByClassName("level-indicator");
    if (lvl.length > 0) {
        var lvlParts = lvl[0].innerHTML.match(/(.*?)(\d+)/);
        if (lvlParts !== null) {
            lvl[0].innerHTML = lvlParts[1] + '<span class="level-number">' + lvlParts[2] + '</span>';
        }
    }

    /*
    Add some colour to the "Step #:" bit of each activity heading
    */
    var activities = document.getElementsByClassName("activity");
    for (var x = 0; x < activities.length; x++) {
        var tag = activities[x].getElementsByTagName('h1');
        if (tag.length > 0) {
            var els = tag[0].innerHTML.split(':');
            if (els.length > 1) {
                tag[0].innerHTML = '<span class="step-num">' + els.shift() + ':</span>' + els.join(':');
            }
        }
    }

    var level1 = document.getElementsByClassName('level1');
    for (var i = 0; i < level1.length; i++) {
        var headers = level1[i].getElementsByTagName('h1');
        if (headers.length > 0) {
            headers[0].className += " unbreakable";
        }
    }

    makeUnbreakable('flag');
    makeUnbreakable('try');
    makeUnbreakable('challenge');

    /* Move the legend to the right place (the end of the first page) */
    var legend = document.getElementById("legend");
    var intro = document.getElementsByClassName("intro");
    if (intro.length > 0) {
        intro[0].appendChild(legend);
        legend.style.display = 'block';
    }
}
