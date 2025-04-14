# 智能库存系统部署文档

## 系统概述

智能库存系统(WMS)是一个基于Web的多租户仓库管理系统，具有以下特点：

- 多租户架构，支持多个独立组织使用同一套系统
- 完整的用户认证和基于角色的权限控制
- 全面的库存管理功能，包括产品管理、库存跟踪、批次管理等
- 强大的报表和分析功能
- 支持PWA，可在移动设备上离线使用

## 技术栈

- 前端：Vue.js 3 + Quasar Framework (PWA)
- 后端：Django + Django REST Framework
- 数据库：PostgreSQL
- 缓存：Redis (可选)

## 系统要求

- Node.js 14.x 或更高版本
- Python 3.8 或更高版本
- PostgreSQL 12 或更高版本
- Redis 6.x (可选，用于缓存和任务队列)
- 现代浏览器，支持Service Worker

## 部署步骤

### 1. 准备环境

#### 安装依赖

```bash
# 安装 Node.js 依赖
apt-get update
apt-get install -y nodejs npm

# 安装 Python 依赖
apt-get install -y python3 python3-pip python3-dev libpq-dev

# 安装 PostgreSQL
apt-get install -y postgresql postgresql-contrib

# 安装 Redis (可选)
apt-get install -y redis-server
```

#### 配置数据库

```bash
# 创建数据库用户和数据库
sudo -u postgres psql -c "CREATE USER wms_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE wms_db OWNER wms_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE wms_db TO wms_user;"
```

### 2. 部署后端

#### 克隆代码并安装依赖

```bash
git clone https://your-repository-url/wms-backend.git
cd wms-backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 配置环境变量

创建 `.env` 文件并设置以下环境变量：

```
DEBUG=False
SECRET_KEY=your_secret_key
DATABASE_URL=postgres://wms_user:your_password@localhost:5432/wms_db
ALLOWED_HOSTS=your_domain.com,www.your_domain.com
```

#### 数据库迁移和静态文件收集

```bash
python manage.py migrate
python manage.py collectstatic --no-input
```

#### 配置 Gunicorn 和 Nginx

创建 Gunicorn 服务文件 `/etc/systemd/system/wms.service`：

```ini
[Unit]
Description=WMS Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/wms-backend
ExecStart=/path/to/wms-backend/venv/bin/gunicorn --workers 3 --bind unix:/path/to/wms-backend/wms.sock wms_backend.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

配置 Nginx：

```nginx
server {
    listen 80;
    server_name your_domain.com www.your_domain.com;

    location /static/ {
        alias /path/to/wms-backend/static/;
    }

    location /media/ {
        alias /path/to/wms-backend/media/;
    }

    location / {
        proxy_pass http://unix:/path/to/wms-backend/wms.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启动服务：

```bash
sudo systemctl start wms
sudo systemctl enable wms
sudo systemctl restart nginx
```

### 3. 部署前端

#### 克隆代码并安装依赖

```bash
git clone https://your-repository-url/wms-frontend.git
cd wms-frontend

# 安装依赖
npm install
```

#### 配置环境变量

创建 `.env` 文件：

```
API_URL=https://your_domain.com/api
```

#### 构建PWA

```bash
npm run build:pwa
```

#### 配置 Nginx 服务前端

```nginx
server {
    listen 80;
    server_name app.your_domain.com;
    root /path/to/wms-frontend/dist/pwa;
    index index.html;

    # 启用 gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 缓存静态资源
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # 处理 Service Worker
    location /service-worker.js {
        add_header Cache-Control "no-cache";
        expires off;
    }

    # 所有请求都返回 index.html，由前端路由处理
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 4. SSL 配置 (推荐)

使用 Let's Encrypt 配置 HTTPS：

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com -d www.your_domain.com -d app.your_domain.com
```

### 5. 系统初始化

访问 `https://your_domain.com/admin` 创建初始租户和管理员用户。

## 多租户配置

系统支持通过子域名或请求头识别租户：

1. 子域名模式：`tenant1.your_domain.com`，`tenant2.your_domain.com`
2. 请求头模式：使用 `X-Tenant-ID` 请求头

配置子域名模式需要在 Nginx 中添加通配符域名：

```nginx
server {
    listen 80;
    server_name *.your_domain.com;
    
    # 其他配置与主域名相同
}
```

## 离线功能配置

系统支持离线工作模式，主要通过以下机制实现：

1. Service Worker 缓存静态资源和API响应
2. IndexedDB 存储离线交易数据
3. 后台同步功能在网络恢复时自动同步数据

离线功能默认已启用，无需额外配置。

## 性能优化

1. 启用数据库连接池
2. 配置 Redis 缓存
3. 使用 CDN 分发静态资源
4. 启用 HTTP/2

## 备份策略

1. 数据库定期备份：

```bash
# 创建备份脚本
cat > /usr/local/bin/backup_wms.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/wms_db_$TIMESTAMP.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -U wms_user -d wms_db > $BACKUP_FILE

# 压缩备份
gzip $BACKUP_FILE

# 删除30天前的备份
find $BACKUP_DIR -name "wms_db_*.sql.gz" -mtime +30 -delete
EOF

# 设置执行权限
chmod +x /usr/local/bin/backup_wms.sh

# 添加到 crontab
echo "0 2 * * * /usr/local/bin/backup_wms.sh" | sudo tee -a /etc/crontab
```

2. 文件系统备份：定期备份 media 目录

## 监控

推荐使用 Prometheus + Grafana 监控系统性能。

## 故障排除

常见问题及解决方案：

1. 数据库连接问题：检查数据库凭据和网络连接
2. 静态文件404：确保 collectstatic 命令已执行
3. 离线功能不工作：检查浏览器是否支持 Service Worker
4. 多租户识别问题：检查域名配置和请求头

## 升级指南

1. 备份数据库和配置文件
2. 拉取最新代码
3. 安装新依赖
4. 执行数据库迁移
5. 重新构建前端
6. 重启服务

## 联系支持

如有问题，请联系：support@your_domain.com
