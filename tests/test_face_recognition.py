"""
测试 face_recognition 库是否正常工作
"""

try:
    import face_recognition
    import numpy as np
    from PIL import Image
    print("✅ face_recognition 导入成功")
    print(f"   版本: {face_recognition.__version__ if hasattr(face_recognition, '__version__') else '未知'}")
    
    # 创建一个测试图片（纯色图片）
    print("\n测试人脸检测功能...")
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    face_locations = face_recognition.face_locations(test_image)
    print(f"✅ 人脸检测功能正常（检测到 {len(face_locations)} 张人脸）")
    
    print("\n✅ 所有测试通过！face_recognition 库工作正常")
    print("\n你现在可以:")
    print("  1. 运行 python init_db.py 初始化数据库")
    print("  2. 运行 python app.py 启动服务器")
    print("  3. 访问 http://127.0.0.1:5000 使用Face ID功能")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n请先安装依赖:")
    print("  方法1: 运行 install_face_recognition.bat")
    print("  方法2: 手动执行 pip install face_recognition")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")

