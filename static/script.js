const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const chatMessages = document.getElementById("chatMessages");
const sendButton = document.getElementById("sendButton");

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addMessage(text, type, id = null) {
    const message = document.createElement("div");
    message.className = `message ${type}-message`;
    if (id) message.id = id;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = type === "user" ? "👨‍🌾" : "🌱";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const paragraph = document.createElement("p");
    paragraph.textContent = text;

    bubble.appendChild(paragraph);
    message.appendChild(avatar);
    message.appendChild(bubble);
    chatMessages.appendChild(message);

    scrollToBottom();
    return message;
}

async function sendMessage(question) {
    addMessage(question, "user");

    const thinking = addMessage("Thinking...", "ai", "thinkingMessage");
    thinking.querySelector(".bubble").classList.add("thinking");

    messageInput.disabled = true;
    sendButton.disabled = true;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: question })
        });

        let data;
        try {
            data = await response.json();
        } catch {
            throw new Error("The server returned an invalid response.");
        }

        if (!response.ok) {
            throw new Error(data.response || "The server could not process the question.");
        }

        thinking.remove();
        addMessage(data.response, "ai");
    } catch (error) {
        thinking.remove();
        addMessage(
            "Sorry, I couldn't process that request right now. Please try again. " +
            "If the problem continues, check that the Flask server is running.",
            "ai"
        );
        console.error(error);
    } finally {
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const question = messageInput.value.trim();
    if (!question) return;

    messageInput.value = "";
    messageInput.style.height = "auto";
    sendMessage(question);
});

messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = `${Math.min(messageInput.scrollHeight, 140)}px`;
});

messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});

document.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", () => {
        messageInput.value = button.textContent.trim();
        messageInput.focus();
        messageInput.dispatchEvent(new Event("input"));
    });
});

scrollToBottom();
