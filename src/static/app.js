document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  window.fetchActivities = async function() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and existing content
      activitiesList.innerHTML = "";
      
      // Clear existing activity select options (keep the first default option)
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        
        // Create participants list HTML
        const participantsList = details.participants.length > 0 
          ? `<ul class="participants-list">
               ${details.participants.map(participant => 
                 `<li>
                    <span>${participant}</span>
                    <button class="delete-btn" onclick="unregisterParticipant('${name}', '${participant}')" title="Remove participant">
                      ✕
                    </button>
                  </li>`
               ).join('')}
             </ul>`
          : `<p class="no-participants">No participants yet</p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <h5>Current Participants:</h5>
            ${participantsList}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email: email }),
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        
        // Refresh the activities list to show updated participants
        await window.fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  window.fetchActivities();
});

// Function to unregister a participant from an activity
async function unregisterParticipant(activityName, email) {
  if (!confirm(`Are you sure you want to unregister ${email} from ${activityName}?`)) {
    return;
  }

  try {
    const response = await fetch(
      `/activities/${encodeURIComponent(activityName)}/unregister`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: email }),
      }
    );

    const result = await response.json();

    if (response.ok) {
      // Refresh the activities list to show updated participants
      await window.fetchActivities();
      
      // Show success message briefly
      showMessage(result.message, "success");
    } else {
      showMessage(result.detail || "Failed to unregister participant", "error");
    }
  } catch (error) {
    showMessage("Failed to unregister participant. Please try again.", "error");
    console.error("Error unregistering participant:", error);
  }
}

// Helper function to show messages
function showMessage(text, type) {
  const messageDiv = document.getElementById("message");
  messageDiv.textContent = text;
  messageDiv.className = type;
  messageDiv.classList.remove("hidden");
  
  // Hide message after 3 seconds
  setTimeout(() => {
    messageDiv.classList.add("hidden");
  }, 3000);
}
