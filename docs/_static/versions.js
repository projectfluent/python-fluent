/*
 * Show/hide versions when clicking on the versions paragraph
 */

$(function() {
    let versions = document.getElementById('versions');
    if (versions) {
        versions.onclick = function(ev) {
            let popup = this.querySelector('span');
            popup.classList.toggle('opened')
        }
    }
})
