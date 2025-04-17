document.addEventListener('DOMContentLoaded', function() {
    const socket = io(); // Assuming socket.io is loaded before this script
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    // Use the correct ID from your HTML for file input if different
    const fileInput = document.getElementById('file-input'); 
    const messagesContainer = document.getElementById('messages');
    const searchInput = document.getElementById('teacher-search-input');
    const chatListContainer = document.querySelector('.chat-list');
    let currentChatId = window.currentChatId;
    let currentUserId = window.currentUserId;
    // --- Get currentChatId and currentUserId from script tags ---
    // These variables should be defined globally or passed appropriately
    // let currentChatId = ('currentChatId' in window) ? window.currentChatId : null; 
    // let currentUserId = ('currentUserId' in window) ? window.currentUserId : null;
    // Or preferably access them directly if they are global const/let
    if (searchInput && chatListContainer) {
        searchInput.addEventListener('keyup', function() {
          const searchTerm = searchInput.value.toLowerCase().trim();
          const chatItems = chatListContainer.querySelectorAll('.chat-item');
          chatItems.forEach(item => {
            const studentNameElement = item.querySelector('.chat-item-name');
            if (studentNameElement) {
              const studentName = studentNameElement.textContent.toLowerCase();
              item.style.display = studentName.includes(searchTerm) ? 'flex' : 'none';
            }
          });
        });
      }
      
     if (typeof currentChatId !== 'undefined' && currentChatId !== null) {
         console.log(`Current chat ID: ${currentChatId}`);
         // Emit mark_read event when a chat is loaded
         socket.emit('mark_read', { chat_id: currentChatId });
     } else {
         console.log("No active chat selected.");
     }
    // --------------------------------------------------------

    // --- Handle message form submission ---
    if (messageForm) { // Check if form exists (it doesn't if no chat is active)
         messageForm.addEventListener('submit', async (e) => {
             e.preventDefault();
             // Use fileInput instead of fileUpload if that's the correct ID
             if (!currentChatId || (!messageInput.value.trim() && fileInput.files.length === 0)) return;

             const formData = new FormData();
             formData.append('message', messageInput.value);
             // Use fileInput here too
             if (fileInput.files.length > 0) { 
                 formData.append('attachment', fileInput.files[0]);
             }

             // First try-catch block removed to fix duplicate code issue
             try {
                console.log("Sending message via fetch..."); // Log before fetch
                const response = await fetch(`/chat/${currentChatId}/send`, {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                console.log("Fetch response received:", data); // Log fetch response
                if (data.status === 'success') {
                    console.log("Message sent successfully via fetch."); // Log success
                    messageInput.value = '';
                    fileInput.value = '';
                } else {
                    console.error('Error sending message (fetch response):', data.message);
                    alert(`Error: ${data.message}`);
                }
            } catch (error) {
                console.error('Error sending message (fetch exception):', error); // Log fetch errors
                alert('An network error occurred while sending the message.');
            }
         });
    }
    // -----------------------------------------

    // --- Handle incoming messages ---
    socket.on('new_message', (data) => {
        console.log('Socket event "new_message" received:', data);
        // Check if the message belongs to the currently active chat
        if (data.chat_id === currentChatId) {
            console.log("Message is for current chat, attempting to append..."); // Log before appending
            appendMessage(data);
            scrollToBottom();
            // Optionally re-emit mark_read if needed, although opening the chat should suffice
            // socket.emit('mark_read', { chat_id: currentChatId });
        } else {
            // Message is for a different chat, update the badge for that chat in the list
            const chatItem = document.querySelector(`.chat-item[data-chat-id="${data.chat_id}"]`);
            if (chatItem) {
                const badge = chatItem.querySelector('.unread-badge');
                if (badge) {
                    let count = parseInt(badge.textContent || '0');
                    badge.textContent = count + 1;
                    badge.style.display = 'inline-block'; // Make sure it's visible
                }
            }
            // Update the total unread count for the main sidebar icon
            console.log("Message is for a different chat."); // Log if not for current chat
            updateTotalUnreadCount();
        }
    });
    // ------------------------------

    // --- Function to append message ---
    function appendMessage(message) {
        console.log("Executing appendMessage with data:", message);
        if (!messagesContainer) {
            console.error("Cannot append message: messagesContainer is null."); // Error if container not found
            return;
        }
        if (typeof currentUserId === 'undefined') {
            console.error("Cannot append message: currentUserId is undefined."); // Error if user ID missing
            return;
        }
        try { // Add try-catch for safety
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${message.sender_id === currentUserId ? 'sent' : 'received'}`;

            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            // Use sender_username if available, otherwise use sender_id as fallback
            headerDiv.innerHTML = `<strong>${message.sender_username || `User ${message.sender_id}`}</strong>`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = message.content || ""; // Handle null/undefined content

            // Append attachment if it exists
            if (message.attachment_path && message.attachment_url) {
                const attachmentDiv = document.createElement('div');
                attachmentDiv.className = 'attachment';
                const link = document.createElement('a');
                link.href = message.attachment_url; // Use the generated URL
                link.target = '_blank';
                link.className = 'file-link';

                const icon = document.createElement('i');
                icon.className = 'material-icons';
                icon.textContent = 'attach_file';

                // Try to get a cleaner filename
                const filename = message.attachment_path.split('_').pop() || message.attachment_path.split('/').pop();

                link.appendChild(icon);
                link.appendChild(document.createTextNode(` ${filename}`)); // Add space

                attachmentDiv.appendChild(link);
                contentDiv.appendChild(attachmentDiv);
            }

            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            try {
                // Ensure created_at is a valid date string
                const dateObj = new Date(message.created_at);
                if (!isNaN(dateObj)) { // Check if date is valid
                    timeDiv.textContent = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                } else {
                    timeDiv.textContent = "Invalid date"; // Fallback for invalid date
                }
            } catch (e) {
                console.error("Error formatting date:", e, message.created_at); // Log date formatting errors
                timeDiv.textContent = "??:??"; // Fallback
            }

            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timeDiv);
            messagesContainer.appendChild(messageDiv);
            console.log("Message appended to DOM."); // Confirm append happened

        } catch (error) {
            console.error("Error occurred within appendMessage:", error); // Log any errors during DOM manipulation
        }
    }
     // --------------------------------

     // --- Function to scroll ---
     function scrollToBottom() {
         if (messagesContainer) {
             messagesContainer.scrollTop = messagesContainer.scrollHeight;
         }
     }
     // --------------------------

     // --- Update TOTAL unread count (for main sidebar) ---
     function updateTotalUnreadCount() {
         fetch('/chat/unread_count') // Fetch total unread count
             .then(response => response.json())
             .then(data => {
                 // Find the badge next to the main 'Chat' nav item
                 // Adjust selector based on your final HTML structure
                 const chatNavItem = document.querySelector('a.nav-item[href*="/chat"]'); 
                 if (chatNavItem) {
                     let badge = chatNavItem.querySelector('.nav-unread-badge'); // Use a specific class?
                     if (!badge) { 
                         // Create badge if it doesn't exist
                         badge = document.createElement('span');
                         badge.className = 'nav-unread-badge'; // Add a class for styling
                         chatNavItem.appendChild(badge); 
                         // Add CSS for .nav-unread-badge (similar to .unread-badge but maybe positioned differently)
                     }

                     if (data.unread_count > 0) {
                         badge.textContent = data.unread_count;
                         badge.style.display = 'inline-block'; // Or 'flex', etc.
                     } else {
                         badge.textContent = '';
                         badge.style.display = 'none';
                     }
                 }
             })
             .catch(error => console.error('Error fetching unread count:', error));
     }
     // ----------------------------------------------------

    // --- Initial setup ---
    if (messagesContainer) { // Only scroll if messages are displayed
         scrollToBottom();
    }
    updateTotalUnreadCount(); // Update total count on load
    // Optional: Periodically update total count as a fallback
    // setInterval(updateTotalUnreadCount, 30000); // e.g., every 30 seconds
    // ---------------------

    // Remove teacher-specific modal/chat start functions if this file is only for students
    // window.showStudentList = ...
    // window.startChat = ...
    // window.openNewChatModal = ...

}); // End DOMContentLoaded