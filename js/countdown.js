var end_elem = document.getElementById("event_end");
var start_elem = document.getElementById("event_next_start");
var display_end_elem = document.getElementById("timer_end");
var display_start_elem = document.getElementById("timer_start");
var display_clock_elem = document.getElementById("clock");

function clock_loop() {
    setTimeout(clock_loop, 5000);

    var now = new Date();
    let h = now.getHours();
    let m = now.getMinutes();


    let display = "";

    if (h < 10) {
        display = "0";
    }
    display += h;
    display += ":";
    if (m < 10) {
        display += "0";
    }
    display += m;

    display_clock_elem.innerText = display;
}

function countdown_end_loop() {
    setTimeout(countdown_end_loop, 1000);

    var now = new Date();
    let h = now.getHours();
    let m = now.getMinutes();
    let s = now.getSeconds();
    let end = end_elem.innerText.split(":");
    let eh = parseInt(end[0]);
    let em = parseInt(end[1]);

    let dh = 24-Math.abs((h-eh)%24);
    let dm = 60-Math.abs((m-em)%60);
    let ds = 60-s;

    let display = "";

    if (dh > 0) {
        display = ">1h";
    }else {
        if (dm < 10) {
            display += "0";
        }
        display += dm + ":"

        if (ds < 10) {
            display += "0";
        }
        display += ds + "";
    }

    display_end_elem.innerText = display;
}

function countdown_start_loop() {
    setTimeout(countdown_start_loop, 1000);

    var now = new Date();
    let h = now.getHours();
    let m = now.getMinutes();
    let s = now.getSeconds();
    let end = start_elem.innerText.split(":");
    let eh = parseInt(end[0]);
    let em = parseInt(end[1]);

    let dh = 24-Math.abs((h-eh)%24);
    let dm = 60-Math.abs((m-em)%60);
    let ds = 60-s;

    let display = "";

    if (dh > 0) {
        display = dh + ":";
    }
    if (dm < 10) {
        display += "0";
    }
    display += dm + ":"
    if (dh === 0) {
        if (ds < 10) {
            display += "0";
        }
        display += ds + "";
    }

    display_start_elem.innerText = display;
}

if (display_end_elem) {
    countdown_end_loop();
}
if (display_start_elem) {
    countdown_start_loop();
}
if (display_clock_elem) {
    clock_loop();
}