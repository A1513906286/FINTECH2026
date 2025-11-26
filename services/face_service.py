import face_recognition
import numpy as np
import base64
import json
from PIL import Image
import io

class FaceRecognitionService:
    """开源人脸识别服务（基于face_recognition库）"""
    
    def __init__(self):
        # 相似度阈值（距离越小越相似，通常0.6以下认为是同一人）
        self.tolerance = 0.6
    
    def detect_face(self, image_data):
        """
        检测人脸
        
        Args:
            image_data: 图片数据（numpy array或PIL Image）
            
        Returns:
            dict: {
                'success': bool,
                'face_count': int,
                'face_locations': list,
                'message': str
            }
        """
        try:
            # 转换为numpy array
            if isinstance(image_data, Image.Image):
                image_array = np.array(image_data)
            else:
                image_array = image_data
            
            # 检测人脸位置
            face_locations = face_recognition.face_locations(image_array)
            
            if len(face_locations) == 0:
                return {
                    'success': False,
                    'face_count': 0,
                    'message': '未检测到人脸，请确保面部清晰可见'
                }
            
            if len(face_locations) > 1:
                return {
                    'success': False,
                    'face_count': len(face_locations),
                    'message': f'检测到{len(face_locations)}张人脸，请确保只有一人'
                }
            
            return {
                'success': True,
                'face_count': 1,
                'face_locations': face_locations,
                'message': '人脸检测成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'人脸检测失败: {str(e)}'
            }
    
    def extract_face_encoding(self, image_data):
        """
        提取人脸特征编码（128维向量）
        
        Args:
            image_data: 图片数据（numpy array或PIL Image）
            
        Returns:
            dict: {
                'success': bool,
                'encoding': list,  # 128维特征向量
                'message': str
            }
        """
        try:
            # 转换为numpy array
            if isinstance(image_data, Image.Image):
                image_array = np.array(image_data)
            else:
                image_array = image_data
            
            # 先检测人脸
            detect_result = self.detect_face(image_array)
            if not detect_result['success']:
                return detect_result
            
            # 提取人脸特征编码
            face_encodings = face_recognition.face_encodings(image_array)
            
            if len(face_encodings) == 0:
                return {
                    'success': False,
                    'message': '无法提取人脸特征，请重新拍摄'
                }
            
            # 转换为列表（方便JSON序列化）
            encoding_list = face_encodings[0].tolist()
            
            return {
                'success': True,
                'encoding': encoding_list,
                'message': '人脸特征提取成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'特征提取失败: {str(e)}'
            }
    
    def compare_faces(self, known_encoding, unknown_encoding):
        """
        比对两个人脸特征
        
        Args:
            known_encoding: 已知的人脸特征（list）
            unknown_encoding: 待比对的人脸特征（list）
            
        Returns:
            dict: {
                'success': bool,
                'is_match': bool,
                'distance': float,  # 欧氏距离，越小越相似
                'similarity': float,  # 相似度百分比
                'message': str
            }
        """
        try:
            # 转换为numpy array
            known_array = np.array(known_encoding)
            unknown_array = np.array(unknown_encoding)
            
            # 计算欧氏距离
            distance = face_recognition.face_distance([known_array], unknown_array)[0]
            
            # 判断是否匹配
            is_match = distance <= self.tolerance
            
            # 转换为相似度百分比（距离越小，相似度越高）
            similarity = max(0, (1 - distance) * 100)

            return {
                'success': True,
                'is_match': is_match,
                'distance': float(distance),
                'similarity': float(similarity),
                'message': f'匹配成功，相似度: {similarity:.1f}%' if is_match else f'不匹配，相似度: {similarity:.1f}%'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'人脸比对失败: {str(e)}'
            }

    def register_face(self, image_base64):
        """
        注册人脸（提取特征编码）

        Args:
            image_base64: Base64编码的图片

        Returns:
            dict: {
                'success': bool,
                'encoding': list,
                'message': str
            }
        """
        try:
            # 解码Base64图片
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))

            # 提取人脸特征
            result = self.extract_face_encoding(image)

            return result

        except Exception as e:
            return {
                'success': False,
                'message': f'注册失败: {str(e)}'
            }

    def search_face(self, image_base64, all_users_encodings):
        """
        搜索匹配的人脸（登录时使用）

        Args:
            image_base64: Base64编码的图片
            all_users_encodings: 所有用户的人脸特征
                格式: [
                    {'user_id': 1, 'encoding': [...]},
                    {'user_id': 2, 'encoding': [...]},
                ]

        Returns:
            dict: {
                'success': bool,
                'user_id': int,
                'similarity': float,
                'message': str
            }
        """
        try:
            # 解码Base64图片
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))

            # 提取当前人脸特征
            extract_result = self.extract_face_encoding(image)
            if not extract_result['success']:
                return extract_result

            current_encoding = extract_result['encoding']

            # 与所有已注册用户比对
            best_match = None
            best_similarity = 0

            for user_data in all_users_encodings:
                user_id = user_data['user_id']
                known_encoding = user_data['encoding']

                # 比对人脸
                compare_result = self.compare_faces(known_encoding, current_encoding)

                if compare_result['success'] and compare_result['is_match']:
                    if compare_result['similarity'] > best_similarity:
                        best_similarity = compare_result['similarity']
                        best_match = user_id

            if best_match:
                return {
                    'success': True,
                    'user_id': best_match,
                    'similarity': best_similarity,
                    'message': f'识别成功，相似度: {best_similarity:.1f}%'
                }
            else:
                return {
                    'success': False,
                    'message': '未找到匹配的用户'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'人脸搜索失败: {str(e)}'
            }

