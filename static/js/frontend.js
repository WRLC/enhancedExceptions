// frontend js functions

// login form
function submitLogin() {
    const sp = "https://aladin-sp.wrlc.org/simplesaml/wrlcauth/issue.php?institution="
    let params = "&url=https://exceptions.wrlc.org/login/n"
    let select = document.getElementById('user-name');
    let institution = select.options[select.selectedIndex].value;
    window.location.replace(sp + institution + params);
    return false;
}
