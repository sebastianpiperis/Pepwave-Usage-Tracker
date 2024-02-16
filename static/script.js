
var resetBtn = document.getElementById('resetBtn') // gets the reset button
var deviceList = document.getElementById('device-list-container'); // gets the device list
var startDateInput = document.getElementById('start_date'); // gets start date input
var endDateInput = document.getElementById('end_date'); // gets end date input
var searchForm = document.getElementById('search-form'); // gets search form
var today = new Date(); // create a new date object which represents the current date and time
var sixtyDaysAgo = new Date(); // create a new Date object representing the current date and time to then structure

sixtyDaysAgo.setDate(sixtyDaysAgo.getDate() - 60); // sets date to sixty days before the current date

var formattedToday = today.toISOString().split('T')[0]; // formats the current date as a string in YYYY-MM-DD format
var formattedSixtyDaysAgo = sixtyDaysAgo.toISOString().split('T')[0]; // format the date 60 days ago as a string in YYYY-MM-DD format

configureDateInput(startDateInput, formattedToday, formattedSixtyDaysAgo, formattedToday); // configure the start date input with max, min, and default values
configureDateInput(endDateInput, formattedToday, formattedSixtyDaysAgo, formattedToday); // configure the end date input with max, min, and default values

// configures date input
function configureDateInput(input, max, min, value) {
    if (input) {
        input.setAttribute('max', max); // sets max date
        input.setAttribute('min', min); // sets min date
        input.value = value; // sets default value of the input
    }
}

// resets list and dates to default
function resetList() {
    configureDateInput(startDateInput, formattedToday, formattedSixtyDaysAgo, formattedToday);
    configureDateInput(endDateInput, formattedToday, formattedSixtyDaysAgo, formattedToday);
    deviceList.style.visibility = 'hidden'; // Hide the device list
    resetBtn.style.visibility = 'hidden'; // hides the reset button after clicked 
}

// event listener to handle submit events
searchForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (formIsValid()) {
        deviceList.style.visibility = 'hidden'; // hides the device list
        resetBtn.style.visibility = 'hidden'; // hides the reset button
        searchForm.style.visibility = 'hidden' // hides the date picker
        searchForm.submit(); // submits the form
        showLoader(); // shows the hourglass spinner

    } else {
        alert("Start Date must come before End Date"); // shows an alert if they submit the dates wrong
    }

});

// function to show loading spinner
function showLoader() {
    document.getElementById('loading-spinner').style.display = ''; // makes the hourglass visible
}
function formIsValid() {
    // return true if valid, false otherwise
    return startDateInput.value <= endDateInput.value; // checks to see if start date is less than or = to end date. if start date is after the form is invalid
}
