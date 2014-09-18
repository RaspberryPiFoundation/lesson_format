var ul = document.getElementsByTagName("ul")
for (var x = 0; x < ul.length; x++) {
  if (ul[x].className == 'breadcrumbs-list') continue;
  ul[x].addEventListener('click', function(e) {
    if(e.target && e.target.nodeName == "LI") {
      e.target.classList.toggle('activity-done');
    }
  }, false);
}
