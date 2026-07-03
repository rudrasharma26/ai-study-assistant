# AI Study Assistant

An AI-powered study companion built using **Streamlit** that helps students learn, revise, and assess their understanding of academic topics through intelligent explanations, summaries, quizzes, and note exports.

The project is designed to provide students with an interactive learning experience by combining modern user interfaces with the capabilities of large language models.

---

## Live Demo

The application is deployed and accessible at:

👉 **[Launch StudyVerse AI](https://studyverse-ai.streamlit.app)**

---

## Features

### Multi-Mode Learning

The application provides multiple study modes to suit different learning requirements:

- **Learn Mode** – Generates detailed explanations for comprehensive understanding.
- **Revision Mode** – Produces concise revision notes for quick review.
- **Exam Mode** – Focuses on important concepts and exam-oriented preparation.

### AI-Powered Study Assistance

For any topic, the assistant can generate:

- Detailed explanations
- Concise summaries
- Important points and takeaways
- Topic-specific quizzes
- Structured learning material

### Interactive Quiz System

Users can:

- Attempt AI-generated quizzes
- Receive instant feedback
- Evaluate their understanding
- Track quiz performance

### Persistent Storage

The application stores user activity locally, including:

- Search history
- Favourite topics
- Previous study sessions

### Export Functionality

Generated study material can be exported as:

- PDF documents
- Text files

### Modern User Interface

The application features:

- Dark-themed interface
- Glassmorphism-inspired design
- Responsive layout
- Clean and intuitive user experience

---

## Project Structure

```text
ai-study-assistant/
│
├── backend/
│   ├── ai_handler.py
│   ├── parser.py
│   └── prompts.py
│
├── frontend/
│   ├── components.py
│   └── styles.py
│
├── utils/
│   ├── export.py
│   └── storage.py
│
├── assets/
├── app.py
├── requirements.txt
└── README.md
```

---

## Technologies Used

- Python
- Streamlit
- Google Gemini API
- OpenRouter API
- JSON
- ReportLab

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/rudrasharma26/ai-study-assistant.git
cd ai-study-assistant
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root directory and add the required API keys.

Example:

```env
GEMINI_API_KEY=your_api_key
OPENROUTER_API_KEY=your_api_key
```

---

## Running the Application Locally

Start the Streamlit application using:

```bash
streamlit run app.py
```

The application will be available locally in your browser.

---

## Future Enhancements

Planned improvements include:

- User authentication
- Study streak tracking
- Achievement badges
- Flashcard generation
- Spaced repetition system
- Cloud synchronization
- Multi-device support

---

## Contributing

Contributions, suggestions, and feature requests are welcome.

If you would like to contribute:

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Open a Pull Request

---

## Author

**Rudra Sharma**

B.Tech Computer Science and Engineering (Data Science)  
Manipal University Jaipur

---

## License

This project is intended for educational and personal learning purposes.

---

⭐ If you find this project useful, consider giving the repository a star.
