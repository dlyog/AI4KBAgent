$(document).ready(function() {

 

    new Darkmode().showWidget();

    //$('#messageContainer').css('display', 'block');


    var lastSelectedText = ''; 
    
   // Function to hide message containers if clicking/tapping outside of them
   function hideMessageOnOutsideClick(event) {
    const $messageContainer = $('#messageContainer');
    if ($messageContainer.is(':visible') && !$messageContainer.is(event.target) && $messageContainer.has(event.target).length === 0) {
        $messageContainer.hide();
    }
}

// Listen for clicks and touches outside the message container to hide it
$(document).on('click touchend', hideMessageOnOutsideClick);

function handleTextSelection() {
    const selectedText = window.getSelection().toString().trim();
    if (selectedText.length > 0) {
        lastSelectedText = selectedText;
        const rect = window.getSelection().getRangeAt(0).getBoundingClientRect();
        
        // Adjust the top position to show the icon three lines above the selected text
        // Assuming a line height of about 18 pixels, adjust as needed
        const lineHeight = 18; // Adjust this based on your actual line height
        const linesAbove = 3; // Number of lines above the selection
        const adjustment = lineHeight * linesAbove; // Total adjustment in pixels
        
        const topPosition = rect.top + window.scrollY - $('#explainPopup').outerHeight() - adjustment; // Adjusted line
        const explainLeftPosition = rect.left + window.scrollX + (rect.width / 2) - ($('#explainPopup').outerWidth() / 2);
        const summaryLeftPosition = explainLeftPosition + $('#explainPopup').outerWidth() + 10; // Add space between popups

        $('#explainPopup').css({
            top: topPosition + 'px', // Use the adjusted top position
            left: explainLeftPosition + 'px'
        }).attr('title', 'Explain this').removeClass('hidden');

        $('#summaryPopup').css({
            top: topPosition + 'px', // Use the same adjusted top position for consistency
            left: summaryLeftPosition + 'px'
        }).attr('title', 'Summarize this').removeClass('hidden');
    } else {
        $('#explainPopup, #summaryPopup').addClass('hidden');
    }
}


// Listen for mouseup and touchend events to handle text selection
$(document).on('mouseup touchend', function(e) {

    handleTextSelection();
});

var maxCharacters = 2000 * 4; // Roughly aiming for 2000 tokens

// Function to handle clicking on explainPopup
$('#explainPopup').on('click', function(event) {
    event.preventDefault();
    event.stopPropagation();
    if (lastSelectedText) {
        if (lastSelectedText.length > maxCharacters) {
            lastSelectedText = lastSelectedText.substring(0, maxCharacters);
        }
        explainThis(lastSelectedText);
        lastSelectedText = '';
        $('#explainPopup, #summaryPopup').addClass('hidden');
    }
});

// Function to handle clicking on summaryPopup
$('#summaryPopup').on('click', function(event) {
    event.preventDefault();
    event.stopPropagation();
    if (lastSelectedText) {
        if (lastSelectedText.length > maxCharacters) {
            lastSelectedText = lastSelectedText.substring(0, maxCharacters);
        }
        summarizeThis(lastSelectedText);
        lastSelectedText = '';
        $('#explainPopup, #summaryPopup').addClass('hidden');
    }
});

    // Add the updated touch and click event handler for explainPopup and summaryPopup
    $('#explainPopup, #summaryPopup').on('touchend click', function(event) {
        event.stopPropagation(); // Stop the event from propagating to document
        
        if (lastSelectedText) {
            if (lastSelectedText.length > maxCharacters) {
                lastSelectedText = lastSelectedText.substring(0, maxCharacters);
            }
            // Determine which function to call based on the ID of the clicked/touched element
            if ($(this).is('#explainPopup')) {
                explainThis(lastSelectedText);
            } else if ($(this).is('#summaryPopup')) {
                summarizeThis(lastSelectedText);
            }
            lastSelectedText = ''; // Reset the lastSelectedText
            $('#explainPopup, #summaryPopup').addClass('hidden'); // Hide the popups
        }
    });




    function summarizeThis(selectedText) {
        const blogTitle = document.title;
        const apiUrl = '/summarize_text';
    
        console.log('Generating Summary...');
        $('#summaryBlogTitle').text(blogTitle);
        $('#summarySelectedText').text(selectedText);
        $('#summaryMessageText').text('Generating Summary...');
        showPopup('#summaryMessageContainer');

    
        $.ajax({
            url: apiUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                blogTitle: blogTitle,
                selectedText: selectedText
            }),
            success: function(data) {
                //console.log('Success:', data.summary);
                $('#summaryMessageText').text(data.summary);
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                let errorMessage = "Error: Something went wrong.";
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }
                $('#summaryMessageText').text(errorMessage);
            }
        });
    }
    


function explainThis(selectedText) {
const blogTitle = document.title;
const apiUrl = '/explain_text';

// Show the overlay and the initial message
console.log('Generating Explanation...');
//$('#messageText').text('Generating Explanation...');
// Update modal content with blog title and selected text
$('#blogTitle').text(blogTitle);
$('#selectedText').text(selectedText);
$('#messageText').text('Generating Explanation...');
//$('#messageContainer').css('display', 'block'); 
showPopup('#messageContainer');



$.ajax({
url: apiUrl,
type: 'POST',
contentType: 'application/json',
data: JSON.stringify({
    blogTitle: blogTitle,
    selectedText: selectedText
}),
success: function(data) {
    //console.log('Success:', data.explanation);
    $('#messageText').text(data.explanation); // Show the explanation in the message text
},
error: function(xhr, status, error) {
    console.error('Error:', error);
    let errorMessage = "Error: Something went wrong.";
    if (xhr.responseJSON && xhr.responseJSON.error) {
        errorMessage = xhr.responseJSON.error; // Use the server-provided error message if available
    }
    $('#messageText').text(errorMessage); // Show the error message
}
});
}

function showPopup(popupId) {
    $('body').css('overflow', 'hidden'); // Disable scrolling on the body
    $(popupId).attr('tabindex', '-1').focus().css('display', 'block');
    $(popupId).addClass('overflow-y-auto');
    $(popupId + ' > div').addClass('overflow-y-auto max-h-[80vh]');

}

// Function to hide a popup and re-enable scrolling
function hidePopup(popupId) {
    $(popupId).css('display', 'none'); // Hide the popup
    $('body').css('overflow', ''); // Re-enable scrolling
    // Remove the class that was making the popup scrollable
    $(popupId).removeClass('overflow-y-auto');
    
    // And if you added classes to a child container
    $(popupId + ' > div').removeClass('overflow-y-auto max-h-[80vh]');
}

// Bind hidePopup to your close buttons
$('#closeMessage, #closeSummaryMessage').on('click', function() {
    // Determine which popup to close based on the button clicked
    var popupId = $(this).closest('.popupContainerId').attr('id');
    hidePopup('#' + popupId);
});


// Close functionality remains the same
$('#closeMessage').on('click', function() {
//$('#messageContainer').hide();
hidePopup('#messageContainer');

});

$('#closeSummaryMessage').click(function() {
    //$('#summaryMessageContainer').hide();
    hidePopup('#summaryMessageContainer');

});

});