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

// merge cells in report
function mergeCells() {
    let db = document.getElementById("reportbody");
    let dbRows = db.rows;
    let lastValue = "";
    let lastCounter = 1;
    let lastRow = 0;

    for (let i = 0; i < dbRows.length; i++) {
        let thisValue = dbRows[i].cells[1].innerHTML;
        for (let x = 0; x < 7; x++) {
            if (thisValue === lastValue) {
                lastCounter++;
                dbRows[lastRow].cells[x].rowSpan = lastCounter;
                dbRows[i].cells[x].style.display = "none";
            } else {
                dbRows[i].cells[x].style.display = "table-cell";
                lastValue = thisValue;
                lastCounter = 1;
                lastRow = i;
            }
        }
    }
}