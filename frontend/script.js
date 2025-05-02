// קבלת הפניות לאלמנטים ב-HTML (ללא שינוי)
const chatbox = document.getElementById('chatbox');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');

// כתובת ה-API שלנו ב-Render (החלף אם הכתובת שלך שונה)
const API_URL = 'https://bot-y8ug.onrender.com/api/chat';

// הוספת מאזינים לאירועים (ללא שינוי)
sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' || e.keyCode === 13) {
        sendMessage();
    }
});

// פונקציה לשליחת ההודעה (עדכון עיקרי כאן)
function sendMessage() {
    const userMessage = userInput.value.trim();
    if (userMessage === "") {
        return;
    }

    // 1. הצג את הודעת המשתמש
    displayMessage('user', userMessage);

    // 2. נקה את תיבת הקלט
    userInput.value = "";

    // **** 3. שלח את ההודעה לשרת וטפל בתשובה ****
    getBotResponse(userMessage);
}

// פונקציה *מעודכנת* שמבצעת קריאת API לשרת
async function getBotResponse(userMessage) {
    // (אופציונלי) הצג הודעת "הבוט מקליד..."
    const typingIndicator = displayMessage('bot', 'הבוט חושב...');

    try {
        // בצע קריאת POST ל-API עם fetch
        const response = await fetch(API_URL, {
            method: 'POST', // סוג הבקשה
            headers: {
                'Content-Type': 'application/json' // מציין שאנחנו שולחים JSON
            },
            body: JSON.stringify({ message: userMessage }) // הופך את האובייקט למחרוזת JSON
        });

        // הסר את הודעת "הבוט מקליד..."
        chatbox.removeChild(typingIndicator);

        // בדוק אם הבקשה הצליחה (סטטוס 2xx)
        if (!response.ok) {
            // אם השרת החזיר שגיאה (כמו 500 או 400)
            const errorData = await response.json().catch(() => ({ error: "תשובה לא תקינה מהשרת" })); // נסה לקרוא שגיאת JSON, או צור אחת
            console.error('Server Error:', response.status, errorData);
            displayMessage('bot', `אופס! קרתה שגיאה בשרת: ${errorData.error || response.statusText}`);
            return;
        }

        // קבל את התשובה כ-JSON
        const data = await response.json();

        // הצג את התשובה של הבוט
        if (data.reply) {
            displayMessage('bot', data.reply);
        } else {
            displayMessage('bot', 'קיבלתי תשובה לא צפויה מהשרת.');
        }

    } catch (error) {
        // הסר את הודעת "הבוט מקליד..." גם במקרה של שגיאה
        if (typingIndicator.parentNode === chatbox) { // בדוק אם האלמנט עדיין קיים
             chatbox.removeChild(typingIndicator);
        }
        // אם קרתה שגיאת רשת או שגיאה אחרת בתהליך
        console.error('Fetch Error:', error);
        displayMessage('bot', 'אופס! נראה שיש בעיית תקשורת עם השרת.');
    }
}

// פונקציה להצגת הודעה (ללא שינוי)
function displayMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    if (sender === 'user') {
        messageElement.classList.add('user-message');
    } else {
        messageElement.classList.add('bot-message');
    }
    messageElement.textContent = message;
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;
    return messageElement; // החזרת האלמנט שימושי למחוון ההקלדה
}

// הודעת פתיחה (ללא שינוי)
displayMessage('bot', 'שלום! אני הבוט העסקי שלך. איך אני יכול לעזור?');