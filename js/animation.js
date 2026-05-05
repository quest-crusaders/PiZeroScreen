function set_src(id, src) {
    let elem = document.getElementById(id);
    elem.src = src;
}

function blink_src(id, src, time=1000){
    let elem = document.getElementById(id);
    let old_src = elem.src;
    elem.src = src;
    setTimeout(function () {elem.src = old_src;}, time);
}

function set_css_var(vname, value, id='body') {
    document.getElementById(id).style.setProperty(vname, value);
}

function blink_css_var(vname, value, id='body', time=1000) {
    let old_val = document.getElementById(id).style.getPropertyValue(vname);
    document.getElementById(id).style.setProperty(vname, value);
    setTimeout(function () {document.getElementById(id).style.setProperty(vname, old_val);}, time);
}


function play_audio(url, onend=null){
    var audio = new Audio(url);
    audio.play();
    if(onend !== null){
        audio.addEventListener('ended', onend);
    }
}

function loop(delta, func){
    func();
    setTimeout(function (){loop(delta, func);}, delta);
}

function delay(delta, func){
    setTimeout(func, delta);
}