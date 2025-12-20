// Shift Calendar initialization
document.addEventListener("DOMContentLoaded", function () {
  var calendarEl = document.getElementById("calendar");
  var shiftDataElement = document.getElementById("shift-data");
  if (!calendarEl || !shiftDataElement) return;

  try {
    var shifts = JSON.parse(shiftDataElement.textContent);
    // Ensure FullCalendar is available
    if (typeof FullCalendar !== "undefined") {
      var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "dayGridMonth",
        headerToolbar: {
          left: "prev,next today",
          center: "title",
          right: "dayGridMonth,timeGridWeek,timeGridDay",
        },
        events: shifts,
        eventClick: function (info) {
          // Future: Show modal with shift details
          console.log("Event: " + info.event.title);
        },
      });
      calendar.render();
    } else {
      console.error("FullCalendar is not defined");
    }
  } catch (error) {
    console.error("Error initializing calendar:", error);
  }
});
