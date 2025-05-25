# LearnSphere – FullStack Networking Programming Project (with AI-powered Features)

Django mini social-learning platform with course hierarchy and AI-powered features.  
> Developed by **Taylan Özveren** 
---

## 🔍 Vision

LearnSphere is a collaborative platform for CS, SE, and IT students to:
- Share lecture notes, code snippets, and project artifacts
- Interact through comments and likes
- Discover content via AI recommendations & summarization

---

## ✨ Key Features

- 🔐 Auth system with extended profiles & avatars
- 📚 Discipline → Course hierarchy
- 📝 Post system: text + file upload (PDF, TXT, CSV, IMG, ZIP)
- 💬 Comment & ❤️ Like system (AJAX)
- 📊 User dashboard (Chart.js)
- 🤖 AI layer:
  - TF-IDF post recommendations
  - PDF summarization via Hugging Face API
- 🌗 Light/Dark theme toggle
- ☁️ Live deployment on Render.com

---

## 🛠️ Tech Stack

| Layer       | Tool                        |
|-------------|-----------------------------|
| Backend     | Django                      |
| Database    | SQLite → PostgreSQL         |
| Frontend    | Bootstrap 5, HTMX/JS        |
| Charts      | Chart.js                    |
| AI Services | Hugging Face API            |
| Realtime    | HTMX / (opt.) Django Channels |
| Hosting     | Render.com                  |

---

## 🚀 Installation & Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/learnsphere.git
   cd learnsphere
   ```

2. Create and activate virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables
   - Copy `.env.example` to `.env`
   - Get a [Hugging Face API token](https://huggingface.co/settings/tokens)
   - Add your token to the `.env` file:
   ```
   HF_API_TOKEN=your_token_here
   ```

5. Run migrations and create superuser
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. Start the development server
   ```bash
   python manage.py runserver
   ```

## 🔧 Troubleshooting AI Features

If the AI summarization or explanation features are not working:

1. Ensure your `.env` file contains the following variables:
   ```
   HF_API_TOKEN=your_huggingface_api_token
   HF_SUMMARY_API_URL=https://api-inference.huggingface.co/models/facebook/bart-large-cnn
   HF_EXPLAIN_API_URL=https://api-inference.huggingface.co/models/facebook/bart-large-cnn
   ```

2. Check the browser console and server logs for error messages
3. Try with shorter content as there are limitations to the API's input size
4. Verify your Hugging Face token permissions and rate limits

---

## 🌟 Coming Soon

- Dark/Light theme toggle
- Drag-and-drop file uploads
- PostgreSQL migration
- GitHub Actions CI/CD pipeline
- Comprehensive documentation

---
