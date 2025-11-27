# Deployment Guide - Thesis Panelist AI

## Local Deployment

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation Steps

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test setup**
   ```bash
   python test_setup.py
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```
   Or on Windows, simply double-click `run.bat`

4. **Access the app**
   - Open your browser to `http://localhost:8501`

## Streamlit Community Cloud Deployment

### Prerequisites
- GitHub account
- Groq API key (users will provide their own)

### Steps

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Thesis Panelist AI MVP"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Select the repository and branch (main)
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Configure settings (if needed)**
   - No secrets needed for MVP (users provide their own API keys)
   - Default settings should work fine

4. **Get your public URL**
   - Your app will be available at: `https://your-app-name.streamlit.app`

### Post-Deployment

1. **Test the live app**
   - Upload a sample PDF
   - Generate a review
   - Verify downloads work

2. **Update README with live URL**
   ```markdown
   ## Live Demo
   Visit [https://your-app-name.streamlit.app](https://your-app-name.streamlit.app)
   ```

## Troubleshooting

### Common Issues

**Issue**: "ModuleNotFoundError"
- **Solution**: Ensure all dependencies in `requirements.txt` are installed
- Run: `pip install -r requirements.txt`

**Issue**: "API key error"
- **Solution**: User needs to provide valid Groq API key
- Get free key at: [console.groq.com](https://console.groq.com)

**Issue**: "PDF upload fails"
- **Solution**: Check file size (must be < 10MB) and format (must be PDF)

**Issue**: "Out of memory"
- **Solution**: Streamlit Cloud has memory limits. Keep PDFs under 50 pages

**Issue**: "Slow performance"
- **Solution**: 
  - First run loads the embedding model (takes ~30 seconds)
  - Subsequent runs use cached model
  - Large PDFs (>30 pages) may take 1-2 minutes to process

## Performance Optimization Tips

1. **Model caching**: The embedding model is cached using `@st.cache_resource`
2. **Rate limiting**: Built-in 5-second cooldown between API requests
3. **Chunk size**: Optimized at 500 characters with 100 character overlap
4. **Vector store**: In-memory ChromaDB for fast retrieval

## Monitoring Usage

Since this is an MVP with no backend:
- Waitlist signups stored in session_state only (resets on refresh)
- No analytics or logging
- Track manually through user feedback

## Next Steps (Phase 2)

After validating the MVP:
- [ ] Add persistent storage (database)
- [ ] Implement user authentication
- [ ] Add payment integration
- [ ] Email notifications for waitlist
- [ ] Advanced annotation features
- [ ] Multi-PDF comparison
- [ ] Usage analytics dashboard

## Support

For issues or questions:
1. Check this deployment guide
2. Review the main README.md
3. Check Streamlit documentation: [docs.streamlit.io](https://docs.streamlit.io)
4. Check Groq documentation: [console.groq.com/docs](https://console.groq.com/docs)
