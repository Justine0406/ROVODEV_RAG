# Quick Start Guide - Thesis Panelist AI

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
Open a terminal in this directory and run:
```bash
pip install -r requirements.txt
```

**Note**: The installation may take 5-10 minutes as it downloads PyTorch and other large dependencies.

### Step 2: Get Your Free API Key
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up for a free account (no credit card required)
3. Go to API Keys section
4. Click "Create API Key"
5. Copy your API key (starts with `gsk_...`)

### Step 3: Run the Application

**Option A - Windows (Easy)**
- Double-click `run.bat`

**Option B - Command Line**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Step 4: Use the Application

1. **Enter API Key**
   - Paste your Groq API key in the sidebar
   - Click "Test API Key" to verify it works

2. **Upload PDF**
   - Click "Browse files" in sidebar
   - Select your thesis PDF (max 10MB, <50 pages recommended)
   - Click "Process PDF"
   - Wait for processing (30-60 seconds)

3. **Generate Review**
   - Choose a review mode:
     - **Full Panelist Review** - Complete analysis
     - **Methodology Check** - Research design focus
     - **Writing Quality** - Grammar and clarity
   - Or type a custom question
   - Click "Generate Review"
   - Watch as the critique streams in real-time

4. **Download Results**
   - Download the text review
   - Download the annotated PDF with highlights

## 💡 Tips for Best Results

### PDF Preparation
- ✅ Use text-based PDFs (not scanned images)
- ✅ Keep under 50 pages for faster processing
- ✅ Ensure file is under 10MB
- ✅ Use proper academic formatting

### Review Questions
- ✅ Be specific: "Is my sampling method appropriate for this study?"
- ✅ Focus on one area: "How can I improve the clarity of my methodology section?"
- ❌ Avoid vague: "Is this good?"

### Getting Better Critiques
1. **Full Review**: Best for first-time review of complete draft
2. **Methodology Check**: Use after revising research design
3. **Writing Quality**: Final polish before submission
4. **Custom Questions**: Target specific concerns from your advisor

## 🔧 Troubleshooting

### "ModuleNotFoundError"
**Problem**: Missing dependencies
**Solution**: 
```bash
pip install -r requirements.txt
```

### "Invalid API Key"
**Problem**: API key not working
**Solution**:
1. Check you copied the entire key (starts with `gsk_`)
2. Generate a new key at [console.groq.com](https://console.groq.com)
3. Make sure you're using the correct key format

### "File too large"
**Problem**: PDF exceeds 10MB
**Solution**:
1. Compress the PDF using online tools
2. Split into smaller sections
3. Remove unnecessary images

### "Processing takes too long"
**Problem**: First run is slow
**Solution**:
- First time: Downloads embedding model (~100MB), takes 1-2 minutes
- Subsequent runs: Much faster, model is cached
- Large PDFs (>30 pages): May take 2-3 minutes

### "Rate limit error"
**Problem**: Too many requests
**Solution**:
- Wait 5 seconds between requests
- Free tier: 14,400 requests/day (plenty for testing)
- Check your usage at [console.groq.com](https://console.groq.com)

### "Annotations not appearing"
**Problem**: PDF highlights missing
**Solution**:
- Check if PDF is text-based (not scanned image)
- Text must match exactly for highlighting
- Try "Full Panelist Review" mode for more comprehensive feedback

## 📊 What to Expect

### Processing Times
| Task | Expected Time |
|------|---------------|
| PDF Upload | < 1 second |
| Text Extraction | 1-3 seconds |
| First Model Load | 30-60 seconds |
| Embedding Generation | 5-15 seconds |
| Critique Generation | 10-30 seconds |
| PDF Annotation | 2-5 seconds |

### Review Quality
- **Comprehensive**: 300-800 words of feedback
- **Specific**: Direct quotes from your thesis
- **Actionable**: Clear suggestions for improvement
- **Academic**: Appropriate tone and terminology

## 🎯 Sample Workflow

### For a Complete Thesis Draft:

1. **Day 1: Full Review**
   - Upload complete thesis
   - Run "Full Panelist Review"
   - Note all major issues

2. **Day 2-3: Address Major Issues**
   - Revise based on feedback
   - Focus on methodology and logic issues

3. **Day 4: Methodology Check**
   - Upload revised draft
   - Run "Methodology Check"
   - Verify research design improvements

4. **Day 5: Writing Polish**
   - Upload latest draft
   - Run "Writing Quality"
   - Fix grammar and clarity issues

5. **Day 6: Final Questions**
   - Ask specific questions about remaining concerns
   - Get targeted feedback

6. **Day 7: Final Review**
   - One more "Full Panelist Review"
   - Verify all issues addressed

## 🔐 Privacy Notes

- ✅ Your PDF is processed in memory only
- ✅ Nothing is saved to disk or database
- ✅ Data is deleted when you close the browser
- ✅ You provide your own API key (not stored by us)
- ✅ No tracking or analytics

## 💰 Cost

**Everything is FREE!**
- Streamlit: Free hosting
- Groq: Free tier (14,400 requests/day)
- ChromaDB: Free (in-memory)
- sentence-transformers: Free (open-source)

## 📞 Need Help?

1. Check this guide first
2. Review README.md
3. Check DEPLOYMENT.md for setup issues
4. Review PROJECT_SUMMARY.md for technical details

## 🎉 You're Ready!

Now start the app and get your thesis reviewed by AI! 

```bash
streamlit run app.py
```

Good luck with your research! 🚀
