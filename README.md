# Flask 文件上传服务

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个轻量级的Flask文件上传服务，专为替代复杂的MinIO等对象存储服务而设计，避免复杂的AWS签名认证问题。特别适合n8n工作流集成使用。

## 快速开始

### 方式一：Docker部署（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd flask-file-server

# 使用Docker Compose启动
docker-compose up -d

# 或者手动构建和运行
docker build -t flask-file-server .
docker run -d -p 5000:5000 -v $(pwd)/files:/app/files --name file-server flask-file-server
```

### 方式二：本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

服务将在 `http://localhost:5000` 启动

## API 文档

### 健康检查
```bash
GET /health
```

### 文件上传
```bash
POST /upload
Content-Type: multipart/form-data

参数：
- file: 文件数据（必需）
- path: 存储路径（可选，默认根目录）
- filename: 自定义文件名（可选）
```

**示例：**
```bash
# 基本上传
curl -X POST -F "file=@test.txt" http://localhost:5000/upload

# 指定路径和文件名
curl -X POST -F "file=@test.txt" -F "path=documents/2024" -F "filename=my-doc.txt" http://localhost:5000/upload
```

### 文件下载
```bash
GET /download/<path:filename>
```

**示例：**
```bash
curl http://localhost:5000/download/documents/2024/my-doc.txt
```

### 创建文件夹
```bash
POST /create-folder
Content-Type: application/json

{
  "path": "folder/subfolder"
}
```

### 列出文件
```bash
GET /list?path=<folder_path>
```

## n8n 集成

### HTTP Request 节点配置

**文件上传：**
- Method: `POST`
- URL: `http://your-server:5000/upload`
- Body Type: `Form-Data`
- Parameters:
  - `file`: 文件数据
  - `path`: `{{$json.folder_path}}`（可选）
  - `filename`: `{{$json.custom_name}}`（可选）

### Function 节点 JSON 处理

项目包含完整的n8n Function节点代码（`n8n_json_processor.js`），支持：
- 嵌套JSON数据关键词搜索
- 大小写不敏感匹配
- 多字段搜索
- 完整记录返回

**使用方法：**
1. 复制 `n8n_json_processor.js` 中的代码到n8n Function节点
2. 修改关键词和搜索字段：
```javascript
const keywords = ['你的关键词1', '你的关键词2'];
const searchField = 'name'; // 或其他字段名
```

## 项目结构

```
├── app.py                    # Flask主程序
├── requirements.txt          # Python依赖
├── Dockerfile               # Docker容器配置
├── docker-compose.yml       # Docker Compose配置
├── .gitignore              # Git忽略文件
├── .dockerignore           # Docker忽略文件
├── n8n_json_processor.js    # n8n JSON处理代码
├── 使用说明.md              # 详细使用说明
└── README.md               # 项目说明（本文件）
```

## 配置

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `UPLOAD_FOLDER` | `/app/files` | 文件存储路径 |
| `MAX_CONTENT_LENGTH` | `104857600` | 最大文件大小（100MB） |
| `ALLOWED_EXTENSIONS` | `txt,pdf,png,jpg,jpeg,gif,doc,docx,xls,xlsx` | 允许的文件扩展名 |
| `FLASK_HOST` | `0.0.0.0` | 服务监听地址 |
| `FLASK_PORT` | `5000` | 服务端口 |

### 自定义配置

创建 `.env` 文件：
```env
UPLOAD_FOLDER=/custom/path
MAX_CONTENT_LENGTH=52428800
ALLOWED_EXTENSIONS=txt,pdf,png,jpg
```

## 安全注意事项

1. **生产环境部署**：建议使用nginx反向代理
2. **文件大小限制**：根据需求调整最大文件大小
3. **文件类型白名单**：配置允许的文件扩展名
4. **访问控制**：在生产环境中添加认证机制
5. **定期清理**：设置文件清理策略

## 生产环境部署

### 使用 Gunicorn

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。