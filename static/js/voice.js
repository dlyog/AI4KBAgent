$(document).ready(function() {


    // Speech Recognition setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.onstart = function () {
        console.log('Voice is activated');
        // Change button color to red while recording
        $('#voice').css('background-color', 'red');
    };

    recognition.onend = function () {
        console.log('Voice is deactivated');
        // Change button color back to original (or any color you want) when done
        $('#voice').css('background-color', 'green');
    };

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        $('#topic').val(transcript);
    };

    // Voice button event listener
    $('#voice').on('click', function() {
        recognition.start();
    });

    
// Outside your Ajax call...
// Prepare the speech synthesis
// Initialize speechSynthesis API
var msg = new SpeechSynthesisUtterance();
window.speechSynthesis.cancel();
msg.rate = 0.85; // Slow down the speed
msg.pitch = 1; // Increase the pitch

// Define voice parameters
voiceName = 'Google UK English Male'

$('#play').on('click', function() {
    if (msg !== null) {
        window.speechSynthesis.speak(msg);
    }
});

$('#pause').on('click', function() {
    window.speechSynthesis.pause();
});

$('#resume').on('click', function() {
    window.speechSynthesis.resume();
});
  
    
});
