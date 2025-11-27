"""
Simple test script to verify all dependencies are installed correctly.
"""

import sys

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...\n")
    
    required_packages = {
        'streamlit': 'Streamlit',
        'groq': 'Groq',
        'chromadb': 'ChromaDB',
        'sentence_transformers': 'Sentence Transformers',
        'fitz': 'PyMuPDF',
        'numpy': 'NumPy',
        'torch': 'PyTorch'
    }
    
    failed = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name} - OK")
        except ImportError as e:
            print(f"❌ {name} - FAILED: {e}")
            failed.append(name)
    
    print("\n" + "="*50)
    
    if not failed:
        print("🎉 All dependencies installed successfully!")
        print("\nYou can now run the app with:")
        print("  streamlit run app.py")
        return True
    else:
        print(f"⚠️  {len(failed)} package(s) failed to import:")
        for package in failed:
            print(f"  - {package}")
        print("\nPlease install missing packages:")
        print("  pip install -r requirements.txt")
        return False


def test_utils():
    """Test that utility modules can be imported."""
    print("\n" + "="*50)
    print("Testing utility modules...\n")
    
    utils = [
        'utils.pdf_processor',
        'utils.embeddings',
        'utils.groq_client',
        'utils.annotator',
        'utils.prompts'
    ]
    
    failed = []
    
    for util in utils:
        try:
            __import__(util)
            print(f"✅ {util} - OK")
        except ImportError as e:
            print(f"❌ {util} - FAILED: {e}")
            failed.append(util)
    
    print("\n" + "="*50)
    
    if not failed:
        print("🎉 All utility modules loaded successfully!")
        return True
    else:
        print(f"⚠️  {len(failed)} module(s) failed to import")
        return False


if __name__ == "__main__":
    print("="*50)
    print("Thesis Panelist AI - Setup Test")
    print("="*50 + "\n")
    
    imports_ok = test_imports()
    utils_ok = test_utils()
    
    print("\n" + "="*50)
    if imports_ok and utils_ok:
        print("✅ Setup complete! Ready to run the application.")
        sys.exit(0)
    else:
        print("❌ Setup incomplete. Please fix the errors above.")
        sys.exit(1)
