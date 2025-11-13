#!/usr/bin/env python3
"""
Test script for Online Exam Protector - Option A: Skip dlib
This script tests if the application can start without dlib dependency
"""

import sys
import os

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import tensorflow as tf
        print("✅ TensorFlow imported successfully")
    except ImportError as e:
        print(f"❌ TensorFlow import failed: {e}")
        return False
    
    try:
        from face_detector import get_face_detector, find_faces
        print("✅ Face detector imported successfully")
    except ImportError as e:
        print(f"❌ Face detector import failed: {e}")
        return False
    
    try:
        from face_landmarks import get_landmark_model, detect_marks
        print("✅ Face landmarks imported successfully")
    except ImportError as e:
        print(f"❌ Face landmarks import failed: {e}")
        return False
    
    return True

def test_models():
    """Test if required model files exist"""
    print("\n🔍 Testing model files...")
    
    required_files = [
        'models/classes.TXT',
        'models/deploy.prototxt', 
        'models/opencv_face_detector_uint8.pb',
        'models/opencv_face_detector.pbtxt',
        'models/pose_model/saved_model.pb',
        'models/yolov3.weights'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_face_detection():
    """Test face detection functionality"""
    print("\n🔍 Testing face detection...")
    
    try:
        from face_detector import get_face_detector
        face_model = get_face_detector()
        print("✅ Face detector model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Face detection test failed: {e}")
        return False

def test_landmark_detection():
    """Test landmark detection functionality"""
    print("\n🔍 Testing landmark detection...")
    
    try:
        from face_landmarks import get_landmark_model
        landmark_model = get_landmark_model()
        print("✅ Landmark model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Landmark detection test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Online Exam Protector Test (Option A: Skip dlib)")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Import Test", test_imports),
        ("Model Files Test", test_models), 
        ("Face Detection Test", test_face_detection),
        ("Landmark Detection Test", test_landmark_detection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The application should work without dlib.")
        print("\n📝 Next steps:")
        print("1. Set up MySQL database (see DB/quizappstructure.sql)")
        print("2. Update database credentials in app.py")
        print("3. Run: python app.py")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)