//console.log("Example to read line by line text");
//const f = require('fs');
//const readline = require('readline');
//var user_file = './log_python.txt';
//var r = readline.createInterface({
//    input : fs.createReadStream(user_file)
//});
//
//r.on('line', function (text) {
//    console.log(text);
//    $("<div />").text(text).appendTo("#tail")
//});


for(var i=0; i<100; i++) {
    $("<div />").text("log line " + i).appendTo("#tail")
}

// scroll to bottom on init
tailScroll();

// add button click
$("button").click(function(e) {
    e.preventDefault();
    $("<div />").text("new line").appendTo("#tail");
    tailScroll();
});

// tail effect
function tailScroll() {
    var height = $("#tail").get(0).scrollHeight;
    $("#tail").animate({
        scrollTop: height
    }, 500);
}