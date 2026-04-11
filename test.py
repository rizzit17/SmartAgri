import os
import pickle
import sys

print("="*60)
print("SMART AGRICULTURE - MODEL DEBUG TOOL")
print("="*60)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "crop_model.pkl")

print(f"\n1. Python Version: {sys.version}")
print(f"2. Working Directory: {BASE_DIR}")
print(f"3. Model Path: {MODEL_FILE}")

# Check if file exists
print(f"\n4. Model File Exists: {os.path.exists(MODEL_FILE)}")

if os.path.exists(MODEL_FILE):
    print(f"   File Size: {os.path.getsize(MODEL_FILE)} bytes")
    
    # Try to load the model
    print("\n5. Attempting to load model...")
    try:
        with open(MODEL_FILE, "rb") as f:
            model = pickle.load(f)
        
        print("   ✓ Model loaded successfully!")
        print(f"   Model Type: {type(model)}")
        
        # Check model attributes
        if hasattr(model, 'n_features_in_'):
            print(f"   Expected Features: {model.n_features_in_}")
        
        if hasattr(model, 'classes_'):
            print(f"   Classes: {list(model.classes_)}")
        
        if hasattr(model, 'feature_names_in_'):
            print(f"   Feature Names: {list(model.feature_names_in_)}")
        
        # Try a test prediction
        print("\n6. Testing prediction with sample data...")
        try:
            test_input = [[24.0, 40.0, 91]]
            prediction = model.predict(test_input)[0]
            probs = model.predict_proba(test_input)[0]
            
            print(f"   ✓ Prediction works!")
            print(f"   Predicted: {prediction}")
            print(f"   Confidence: {max(probs)*100:.1f}%")
            
        except Exception as e:
            print(f"   ✗ Prediction failed: {e}")
            print(f"   Error Type: {type(e).__name__}")
            
            # Show what the model expects
            if hasattr(model, 'n_features_in_'):
                print(f"\n   Model expects {model.n_features_in_} features")
                print(f"   You provided: 3 features [24.0, 40.0, 91]")
        
    except Exception as e:
        print(f"   ✗ Failed to load model!")
        print(f"   Error: {e}")
        print(f"   Error Type: {type(e).__name__}")
        
        # Check pickle protocol
        try:
            with open(MODEL_FILE, "rb") as f:
                # Read first few bytes to check pickle protocol
                header = f.read(2)
                print(f"\n   Pickle header: {header.hex()}")
        except:
            pass
        
        print("\n   LIKELY CAUSE:")
        print("   → Model was created with different Python/sklearn version")
        print("   → Model was trained with different feature count")
        print("   → Model file is corrupted")

else:
    print("\n   ✗ Model file does not exist!")
    print("\n   SOLUTION: Run one of these training scripts:")
    print("   - train_model.py")
    print("   - train_model_v2.py")
    print("   - train_model_sensor_aligned.py")

# Check Python packages
print("\n" + "="*60)
print("7. Checking Required Packages:")
print("="*60)

packages = ['sklearn', 'pandas', 'numpy', 'pickle']
for pkg in packages:
    try:
        if pkg == 'pickle':
            import pickle as p
            print(f"   ✓ {pkg:12s} - built-in")
        elif pkg == 'sklearn':
            import sklearn
            print(f"   ✓ {pkg:12s} - version {sklearn.__version__}")
        else:
            mod = __import__(pkg)
            print(f"   ✓ {pkg:12s} - version {mod.__version__}")
    except ImportError:
        print(f"   ✗ {pkg:12s} - NOT INSTALLED")

print("\n" + "="*60)
print("8. RECOMMENDATION:")
print("="*60)

if not os.path.exists(MODEL_FILE):
    print("\n→ Model file missing. Run: python train_model_fixed.py")
else:
    print("\n→ Model exists but may be incompatible.")
    print("→ Delete crop_model.pkl and retrain:")
    print("  1. del crop_model.pkl")
    print("  2. python train_model_fixed.py")
    print("  3. streamlit run dashboard.py")

print("\n" + "="*60)