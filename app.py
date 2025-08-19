#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask文件上传服务
替代MinIO复杂认证的轻量级文件服务器
支持动态路径创建和简单HTTP上传
"""

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = '/app/files'  # Docker容器内的文件存储路径
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB最大文件大小
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """
    检查文件扩展名是否允许
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_directory(path):
    """
    创建目录结构
    """
    full_path = os.path.join(UPLOAD_FOLDER, path.strip('/'))
    os.makedirs(full_path, exist_ok=True)
    return full_path

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'file-upload-server'
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    文件上传接口
    支持multipart/form-data格式
    参数:
    - file: 上传的文件
    - path: 可选，指定保存路径（如: user/docs/2025）
    - filename: 可选，自定义文件名
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'error': '没有找到文件',
                'code': 'NO_FILE'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'error': '文件名不能为空',
                'code': 'EMPTY_FILENAME'
            }), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'不支持的文件类型，支持的类型: {", ".join(ALLOWED_EXTENSIONS)}',
                'code': 'INVALID_FILE_TYPE'
            }), 400
        
        # 获取路径参数
        upload_path = request.form.get('path', '').strip('/')
        custom_filename = request.form.get('filename', '').strip()
        
        # 处理文件名
        if custom_filename:
            # 使用自定义文件名，但保留原始扩展名
            original_ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{secure_filename(custom_filename)}.{original_ext}"
        else:
            # 使用原始文件名
            filename = secure_filename(file.filename)
        
        # 创建完整的保存路径
        if upload_path:
            save_directory = create_directory(upload_path)
        else:
            save_directory = UPLOAD_FOLDER
        
        # 检查文件是否已存在，如果存在则添加时间戳
        file_path = os.path.join(save_directory, filename)
        if os.path.exists(file_path):
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}{ext}"
            file_path = os.path.join(save_directory, filename)
        
        # 保存文件
        file.save(file_path)
        
        # 构建访问URL
        if upload_path:
            file_url = f"http://localhost:5000/files/{upload_path}/{filename}"
            relative_path = f"{upload_path}/{filename}"
        else:
            file_url = f"http://localhost:5000/files/{filename}"
            relative_path = filename
        
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'filename': filename,
                'path': relative_path,
                'url': file_url,
                'size': os.path.getsize(file_path),
                'upload_time': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'上传失败: {str(e)}',
            'code': 'UPLOAD_ERROR'
        }), 500

@app.route('/files/<path:filename>', methods=['GET'])
def download_file(filename):
    """
    文件下载/访问接口
    支持嵌套路径访问
    """
    try:
        # 安全检查，防止路径遍历攻击
        if '..' in filename or filename.startswith('/'):
            return jsonify({
                'error': '非法的文件路径',
                'code': 'INVALID_PATH'
            }), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'error': '文件不存在',
                'code': 'FILE_NOT_FOUND'
            }), 404
        
        # 获取文件所在目录和文件名
        directory = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        
        return send_from_directory(directory, basename)
        
    except Exception as e:
        return jsonify({
            'error': f'文件访问失败: {str(e)}',
            'code': 'ACCESS_ERROR'
        }), 500

@app.route('/create-folder', methods=['POST'])
def create_folder():
    """
    创建文件夹接口
    参数:
    - path: 要创建的文件夹路径（如: user/docs/2025）
    """
    try:
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({
                'error': '缺少path参数',
                'code': 'MISSING_PATH'
            }), 400
        
        folder_path = data['path'].strip('/')
        if not folder_path:
            return jsonify({
                'error': '路径不能为空',
                'code': 'EMPTY_PATH'
            }), 400
        
        # 创建文件夹
        full_path = create_directory(folder_path)
        
        return jsonify({
            'success': True,
            'message': '文件夹创建成功',
            'data': {
                'path': folder_path,
                'full_path': full_path,
                'created_time': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'文件夹创建失败: {str(e)}',
            'code': 'CREATE_FOLDER_ERROR'
        }), 500

@app.route('/list/<path:folder_path>', methods=['GET'])
@app.route('/list', methods=['GET'])
def list_files(folder_path=''):
    """
    列出文件和文件夹
    """
    try:
        target_path = os.path.join(UPLOAD_FOLDER, folder_path.strip('/'))
        
        if not os.path.exists(target_path):
            return jsonify({
                'error': '路径不存在',
                'code': 'PATH_NOT_FOUND'
            }), 404
        
        items = []
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            is_dir = os.path.isdir(item_path)
            
            items.append({
                'name': item,
                'type': 'directory' if is_dir else 'file',
                'size': 0 if is_dir else os.path.getsize(item_path),
                'modified_time': datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
            })
        
        return jsonify({
            'success': True,
            'data': {
                'path': folder_path,
                'items': items,
                'count': len(items)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'列表获取失败: {str(e)}',
            'code': 'LIST_ERROR'
        }), 500

if __name__ == '__main__':
    # 开发模式运行
    app.run(host='0.0.0.0', port=5000, debug=True)