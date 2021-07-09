function openLink(url){
    window.open(url, "_blank");
}
function checkForm(){
    if(document.getElementById('live').checked === true){
        alert("Copy the following and paste to VLC");
        alert("tcp/h264://"+window.location.host+":3333");
        document.getElementById("mainForm").target = "_blank";
    }else{
        document.getElementById("mainForm").target = "";
    }
}


function toggleControls(value){
    document.getElementById("previewControls").style.display = value;
}


/* V.1 Release */ 
function power(resetOrOff){
    var confirmMessage = "";
    if(resetOrOff == "reset"){
        confirmMessage = "Reset LetsLapse? Restart will take a minute.";
    }else{
        confirmMessage = "Shutdown LetsLapse? Pysical power will need to be reconnected to turn on.";
    }

    var r = confirm(confirmMessage);
    if (r == true) {
        var apiCall = "/?action="+resetOrOff;
        streamManager("stop");
        $.getJSON( apiCall)
            .done(function( json ) {
               //this should be a response to indicate process is about to happen
               //alert("device about to " + resetOrOff);
               if(resetOrOff == "reset"){
                   displayStatus("isRestarting");
               }else{
                    displayStatus("isPowerOff");
               }
               $(".navbar-toggler").click();
            })
            .fail(function( jqxhr, textStatus, error ) {
                var err = textStatus + ", " + error;
                console.log( "Request Failed: " + err );
      });
    }
}

var presets = [];
presets["sunnyDay"] = {ss: 100, iso: 10, awbg: '1.76,2.1'};
presets["sunnyForrest"] = {ss: 5000, iso: 10, awbg: '3,2'};
presets["sunset"] = {ss: 20000, iso: 75, awbg: '3,2'};
presets["nightIndoor"] = {ss: 6 * 100000, iso: 800, awbg: '1.8,2.9'};
presets["nightUrban"] = {ss: 2 * 100000, iso: 800, awbg: '3,2'};
presets["nightNature"] = {ss: 6 * 100000, iso: 800, awbg: '3,2'};

function setPreset(){
    preset = $("#presets").val();
    document.getElementById('ss').value = presets[preset].ss;
    document.getElementById('iso').value = presets[preset].iso;
    document.getElementById('awbg').value = presets[preset].awbg;

    //clear the active filters
    var presetsList = document.getElementById("presets");
    var liTargets = presetsList.getElementsByTagName("li");
    for(var n=0; n<liTargets.length; n++ ){
        liTargets[n].className = "";
    }
}


function streamManager(startOrStop){
    if(startOrStop == "start"){
        displayStatus("isStreaming");
        stream = ""
        if(window.location.host == "127.0.0.1"){
            console.log("local testing, see if the device is on the network")
            stream += "http://10.3.141.212:8081"
        }else{
            stream += "http://"+window.location.host+":8081";
        }
        stream += "/stream.mjpg?cachebuster"+Math.random(100);
        document.getElementById("imageViewport").style.backgroundImage = "url('"+stream+"')";
    }else{
        window.stop();
        displayStatus("isReady");
        document.getElementById("imageViewport").style.backgroundImage = "none";
    }

}



window.addEventListener("load", function(){
    console.log("document loaded");
    pollUptime();
    //streamManager("start");
    setPreset();
});


function secondsToDhms(seconds) {
    var d = Math.floor(seconds / (3600*24));
    var h = Math.floor(seconds % (3600*24) / 3600);
    var m = Math.floor(seconds % 3600 / 60);
    var s = Math.floor(seconds % 60);
    
    var dDisplay = d > 0 ? d + (d == 1 ? " day, " : " days, ") : "";
    var hDisplay = h + ":";
    var mDisplay = m+":";
    if (m < 10){
        mDisplay = "0"+m+":"
    }
    var sDisplay = s;
    if (s < 10){
        sDisplay = "0"+s;
    }

    return dDisplay + hDisplay + mDisplay + sDisplay;
    }


var realUptimeIndex=0;
var realUptimeCheckEvery=9;
var realUptimeLatest=-1;
function pollUptime(){

    console.log("pollUptime: "+ realUptimeIndex);


    realUptimeIndex++;
    if (realUptimeIndex == 1){
        //console.log("pollUptime REAL");
        $.getJSON( "/?action=uptime")
            .done(function( json ) {
                //console.log( Number(json.seconds));
                realUptimeLatest = json.seconds;
                $("footer").html("Running "+ secondsToDhms(realUptimeLatest));

                if(currentStatus == "isRestarting"){ //we're basically checking to see if the divice has come back to life
                    displayStatus("isReady");
                }

                window.setTimeout(pollUptime, 1000);
            })
            .fail(function( jqxhr, textStatus, error ) {
                var err = textStatus + ", " + error;
                if(currentStatus == "isRestarting"){
                    console.log("Device in restart state, need to check again")
                    realUptimeIndex = -10; //this will force a poll in 10 seconds
                    $("footer").html("Device currently restarting, checking again in " + (0 - realUptimeIndex));
                    
                    window.setTimeout(pollUptime, 1000);
                }else{
                    alert("Issue with camera - is it working?");
                }
                console.log( "Request Failed: " + err );
      });
    
    }else{
        //console.log("pollUptime fake");
        realUptimeLatest++
        if(currentStatus == "isRestarting"){
            if(realUptimeIndex > 1){
                realUptimeIndex = -10;
            }
            $("footer").html("Device currently restarting, checking again in " + (0 - realUptimeIndex));            
        }else{
            $("footer").html("Running "+ secondsToDhms(realUptimeLatest));
        }
        if (realUptimeIndex > realUptimeCheckEvery){
            realUptimeIndex = 0;
        }
        window.setTimeout(pollUptime, 1000);
    }
}


function clickViewport(){
    if(currentStatus == "isShooting"){
        parseProgress(true);
    }else if(currentStatus == "isReady"){
        if(document.getElementById("imageViewport").style.backgroundImage == "none"){
            streamManager("start");
        }else{
            streamManager("stop");
        }   
    }
}

function takeStill(){
    var apiCall = "?action=preview";

    if($("#manualSwitch1").hasClass("collapsed")){
        //shotting in auto mode
        apiCall += "&mode=auto";
    }else{
        apiCall += "&mode=manual&ss="+$("#ss").val()+"&iso="+$("#iso").val()+"&awbg="+$("#awbg").val();
    }

    displayStatus("isShooting");

    streamManager("stop");
    $.getJSON( apiCall)
        .done(function( json ) {
            console.log( "JSON Data: " + json );
            displayStill("/previews/"+json.filename);
            displayStatus("isReady");
            //window.setTimeout('streamManager("start");console.log("1 second attempt");', 1000);
            //window.setTimeout('streamManager("start");console.log("3 second attempt");', 3000);
            //window.setTimeout('streamManager("start");console.log("6 second attempt");', 6000);
        })
        .fail(function( jqxhr, textStatus, error ) {
            var err = textStatus + ", " + error;
            console.log( "Request Failed: " + err );
  });
}

var progressTxt = null;
function parseProgress(displayLatest){
    jQuery.get('progress.txt', function(data) {
        progressTxt = (data).split("\n");
        if(progressTxt.length>0){
            var progressIndex = parseInt(progressTxt[0]);
            var progressName = progressTxt[1];
            var folderNum = Math.ceil((progressIndex+1)/1000)-1
            var latestImage = "/auto_"+progressName+"/group"+folderNum+"/image"+progressIndex+".jpg";
            
            if (displayLatest){
                console.log(latestImage);
                displayStill(latestImage);
            }
            $("#status .isShooting .extraInfo").html(" | Images: "+  progressTxt[0]);
        }else{
            window.setTimeout("parseProgress(true)", 2000);
        }
    });
}


function timelapseMode(startOrStop){
    if (startOrStop == "start"){
        displayStatus("isShooting");
        $("#photo-tab").addClass("disabled");
        $("#timelapse .custom-switch").addClass("d-none");
        
        $("#timelapse .startBtn").addClass("d-none");
        $("#timelapse .stopBtn").removeClass("d-none");

        parseProgress(true);
    }else{
        displayStatus("isReady");
        $("#photo-tab").removeClass("disabled");
        $("#timelapse .custom-switch").removeClass("d-none");
        
        $("#timelapse .startBtn").removeClass("d-none");
        $("#timelapse .stopBtn").addClass("d-none");
    }
    
}


function stopTimelapse(){
    var txt;
    var r = confirm("Stop timelapse shoot?");
    if (r == true) {
        console.log("You pressed OK!");
        var apiCall = "?action=killtimelapse";
        $.getJSON( apiCall)
            .done(function( json ) {
                console.log(json );
                //alert("Timelapse in action. This is time consuming and heavy on the system. Doing too much, the system will crash.");
                //displayStill("latest.jpg");
                timelapseMode("stop");
                //window.setTimeout('streamManager("start");console.log("1 second attempt");', 1000);
                //window.setTimeout('streamManager("start");console.log("3 second attempt");', 3000);
                //window.setTimeout('streamManager("start");console.log("6 second attempt");', 6000);
            })
            .fail(function( jqxhr, textStatus, error ) {
                var err = textStatus + ", " + error;
                console.log( "Request Failed: " + err );
            });
    } else {
        console.log("You pressed Cancel!");
    }
}

function startTimelapse(){
    streamManager("stop");
    window.setTimeout("startTimelapseDelay()", 1000);
}

function startTimelapseDelay(){
    var apiCall = "?action=timelapse";
    var shootName = "default";
    if($("#manualSwitch2").hasClass("collapsed")){
        //shotting in auto mode
        apiCall += "&mode=auto";
    }else{
        apiCall += "&mode=manual"; //&ss="+$("#ss").val()+"&iso="+$("#iso").val()+"&awbg="+$("#awbg").val();
        if ($("#shootName").val() !== ""){
            shootName = $("#shootName").val();
        }
    }
    apiCall += "&shootName="+shootName;
    $.getJSON( apiCall)
    .done(function( json ) {
        console.log( "JSON Data: " + json );
        //alert("Timelapse in action. This is time consuming and heavy on the system. Doing too much, the system will crash.");
        //displayStill("latest.jpg");
        timelapseMode("start");
        //window.setTimeout('streamManager("start");console.log("1 second attempt");', 1000);
        //window.setTimeout('streamManager("start");console.log("3 second attempt");', 3000);
        //window.setTimeout('streamManager("start");console.log("6 second attempt");', 6000);
    })
    .fail(function( jqxhr, textStatus, error ) {
        var err = textStatus + ", " + error;
        console.log( "Request Failed: " + err );
    });
}



function displayStill(filename){
    var capturedImage = filename;
    document.getElementById("imageViewport").style.backgroundImage = "url('"+capturedImage+"')";
}
var currentStatus = "isReady";
function displayStatus(which){
    currentStatus = which;
    $("#status .statusMessage").addClass("d-none");
    $("#status ."+which).removeClass("d-none");
}