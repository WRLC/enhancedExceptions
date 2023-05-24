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
function mergeCells(status) {
    let db = document.getElementById(status);
    let dbRows = db.rows;
    let lastValue = "";
    let lastCounter = 1;
    let lastRow = 0;

    for (let i = 0; i < dbRows.length; i++) {
        let thisValue = dbRows[i].cells[1].innerHTML;
        if (thisValue === lastValue) {
            lastCounter++;
            dbRows[lastRow].cells[0].rowSpan = lastCounter;
            dbRows[lastRow].cells[1].rowSpan = lastCounter;
            dbRows[lastRow].cells[2].rowSpan = lastCounter;
            dbRows[lastRow].cells[3].rowSpan = lastCounter;
            dbRows[lastRow].cells[4].rowSpan = lastCounter;
            dbRows[lastRow].cells[5].rowSpan = lastCounter;
            dbRows[lastRow].cells[6].rowSpan = lastCounter;
            dbRows[lastRow].cells[12].rowSpan = lastCounter;
            dbRows[lastRow].cells[13].rowSpan = lastCounter;
            dbRows[i].cells[0].style.display = "none";
            dbRows[i].cells[1].style.display = "none";
            dbRows[i].cells[2].style.display = "none";
            dbRows[i].cells[3].style.display = "none";
            dbRows[i].cells[4].style.display = "none";
            dbRows[i].cells[5].style.display = "none";
            dbRows[i].cells[6].style.display = "none";
            dbRows[i].cells[12].style.display = "none";
            dbRows[i].cells[13].style.display = "none";
        } else {
            dbRows[i].cells[0].style.display = "table-cell";
            dbRows[i].cells[1].style.display = "table-cell";
            dbRows[i].cells[2].style.display = "table-cell";
            dbRows[i].cells[3].style.display = "table-cell";
            dbRows[i].cells[4].style.display = "table-cell";
            dbRows[i].cells[5].style.display = "table-cell";
            dbRows[i].cells[6].style.display = "table-cell";
            dbRows[i].cells[12].style.display = "table-cell";
            dbRows[i].cells[13].style.display = "table-cell";
            lastValue = thisValue;
            lastCounter = 1;
            lastRow = i;
        }
    }
}