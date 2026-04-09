
var msg = document.getElementById("msg_of_the_day");
var side_panel = document.getElementById("side_panel");
var sp_width = 0;
if (side_panel != null) {
    sp_width = side_panel.offsetWidth;
}
var offset = 0;
var is_scrolling = false;

var text_loop_len = 100;

setTimeout(loop, 1000);

function loop(){
    setTimeout(loop, 20);
    msg.innerText = msg.innerText.replaceAll("\n", " ");
    let ref_width = msg.parentElement.parentElement.offsetWidth-(2*sp_width)-100;
    if (is_scrolling){
    if (msg.offsetWidth < ref_width){
        offset = 0;
        is_scrolling = false;
        msg.style = "";
    }else {
        offset++;
        if (offset > msg.offsetWidth + (window.innerWidth/2) - sp_width){
            offset = -(window.innerWidth/2) + sp_width;
        }
        msg.style = "transform: translate("+(-offset).toString()+"px, 0)";
    }
    }else {
        if (msg.offsetWidth >= ref_width) {
            is_scrolling = true;
        }
    }
}