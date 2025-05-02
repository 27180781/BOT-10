// קבלת הפניות לאלמנטים ב-HTML
const chatbox = document.getElementById('chatbox');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');

// הוספת מאזין לאירוע לחיצה על הכפתור
sendButton.addEventListener('click', sendMessage);

// הוספת מאזין לאירוע לחיצה על Enter בתיבת הטקסט
userInput.addEventListener('keypress', function (e) {
    // קוד 13 זה Enter
    if (e.key === 'Enter' || e.keyCode === 13) {
        sendMessage();
    }
});

// פונקציה לשליחת ההודעה (כרגע רק מציגה מקומית)
function sendMessage() {
    const userMessage = userInput.value.trim(); // קבלת הטקסט והסרת רווחים מיותרים

    // בדוק שההודעה לא ריקה
    if (userMessage === "") {
        return; // אל תעשה כלום אם אין טקסט
    }

    // 1. הצג את הודעת המשתמש בתיבת הצ'אט
    displayMessage('user', userMessage);

    // 2. נקה את תיבת הקלט
    userInput.value = "";

    // 3. כאן בעתיד: שלח את ההודעה לשרת וקבל תשובה מהבוט
    // קריאה לפונקציה שתשלח את הבקשה ל-API
    getBotResponse(userMessage);
}

// פונקציה שתטפל בקבלת התשובה מהבוט (כרגע מדמה תשובה)
function getBotResponse(userMessage) {
    console.log("Sending to backend (not really yet):", userMessage); // הדפסה לקונסול בינתיים

    // **** כאן נכניס את הקוד ששולח בקשה ל-API ב-Render ****
    // **** ופונקציה שתטפל בתשובה שתתקבל ****

    // הדמיית תשובה מהבוט אחרי זמן קצר
    setTimeout(() => {
        const botMessage = "קיבלתי: '" + userMessage + "'. אני עדיין לא מחובר לשרת...";
        displayMessage('bot', botMessage);
    }, 500); // השהייה של חצי שניה
}

// פונקציה להצגת הודעה בתיבת הצ'אט
function displayMessage(sender, message) {
    const messageElement = document.createElement('div'); // יצירת אלמנט div חדש
    messageElement.classList.add('message'); // הוספת קלאס כללי

    // הוספת קלאס ספציפי לפי השולח (user או bot) לעיצוב שונה
    if (sender === 'user') {
        messageElement.classList.add('user-message');
    } else {
        messageElement.classList.add('bot-message');
    }

    messageElement.textContent = message; // הכנסת טקסט ההודעה לאלמנט
    chatbox.appendChild(messageElement); // הוספת האלמנט לתיבת הצ'אט

    // גלילה אוטומטית לתחתית תיבת הצ'אט כדי לראות את ההודעה החדשה
    chatbox.scrollTop = chatbox.scrollHeight;
}

// (אופציונלי) הודעת פתיחה
displayMessage('bot', 'שלום! אני הבוט העסקי שלך. איך אני יכול לעזור?');