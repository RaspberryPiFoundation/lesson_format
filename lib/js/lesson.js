/*
lesson.js

This file is used by phantomjs to do some bits of html injection
and reshuffling, to prepare lessons for pdf generation.
*/

/*
Add a span around the lesson number, so it can be made giant
in the header.

NB the alternative is to fix the manifest information and remove the
word "level" from all, then modify the template accordingly.
*/
var lvl = document.getElementsByClassName("level-indicator")[0];
if (lvl.innerHTML.toLowerCase().indexOf('level ') === 0) {
  lvl.innerHTML = 'Level <span class="level-number">' + lvl.innerHTML.substr(6) + '</span>';
}

/*
Add some colour to the "Step #:" bit of each activity heading
*/
var activities = document.getElementsByClassName("activity");
for (var x = 0; x < activities.length; x++) {
  var tag = activities[x].getElementsByTagName('h1')[0];
  var els = tag.innerHTML.split(':');
  if (els.length > 1) {
    tag.innerHTML = '<span class="step-num">' + els.shift() + ':</span>' + els.join(':');
  }
}
