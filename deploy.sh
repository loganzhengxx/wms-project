#!/bin/bash

# WMS 智能库存系统部署脚本
# 此脚本用于自动化部署WMS系统的后端和前端组件

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
  if ! command -v $1 &> /dev/null; then
    print_error "$1 命令未找到，请先安装。"
    exit 1
  fi
}

# 检查必要的命令
check_dependencies() {
  print_message "检查依赖..."
  check_command python3
  check_command pip3
  check_command node
  check_command npm
  check_command psql
}

# 配置变量
setup_variables() {
  print_message "设置部署变量..."
  
  # 项目路径
  WMS_ROOT=$(pwd)
  BACKEND_DIR="$WMS_ROOT/wms_backend"
  FRONTEND_DIR="$WMS_ROOT/wms_frontend"
  
  # 数据库配置
  DB_NAME=${DB_NAME:-"wms_db"}
  DB_USER=${DB_USER:-"wms_user"}
  DB_PASSWORD=${DB_PASSWORD:-"wms_password"}
  DB_HOST=${DB_HOST:-"localhost"}
  DB_PORT=${DB_PORT:-"5432"}
  
  # 服务器配置
  DOMAIN=${DOMAIN:-"localhost"}
  PORT=${PORT:-"8000"}
  
  print_message "部署根目录: $WMS_ROOT"
  print_message "后端目录: $BACKEND_DIR"
  print_message "前端目录: $FRONTEND_DIR"
}

# 创建虚拟环境
create_virtualenv() {
  print_message "创建Python虚拟环境..."
  
  if [ ! -d "$BACKEND_DIR/venv" ]; then
    python3 -m venv "$BACKEND_DIR/venv"
    print_message "虚拟环境创建成功: $BACKEND_DIR/venv"
  else
    print_warning "虚拟环境已存在，跳过创建"
  fi
  
  source "$BACKEND_DIR/venv/bin/activate"
}

# 安装后端依赖
install_backend_dependencies() {
  print_message "安装后端依赖..."
  
  pip3 install --upgrade pip
  pip3 install -r "$BACKEND_DIR/requirements.txt"
  
  print_message "后端依赖安装完成"
}

# 配置数据库
setup_database() {
  print_message "配置数据库..."
  
  # 检查PostgreSQL是否正在运行
  if ! pg_isready -h $DB_HOST -p $DB_PORT > /dev/null 2>&1; then
    print_error "PostgreSQL数据库未运行，请先启动数据库服务"
    exit 1
  fi
  
  # 检查数据库是否已存在
  if psql -h $DB_HOST -p $DB_PORT -U postgres -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    print_warning "数据库 $DB_NAME 已存在，跳过创建"
  else
    print_message "创建数据库 $DB_NAME..."
    psql -h $DB_HOST -p $DB_PORT -U postgres -c "CREATE DATABASE $DB_NAME;"
    psql -h $DB_HOST -p $DB_PORT -U postgres -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"
    psql -h $DB_HOST -p $DB_PORT -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
  fi
}

# 配置后端环境变量
configure_backend() {
  print_message "配置后端环境..."
  
  # 创建.env文件
  cat > "$BACKEND_DIR/.env" << EOF
DEBUG=False
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
DATABASE_URL=postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1
EOF

  print_message "后端环境配置完成"
}

# 执行数据库迁移
run_migrations() {
  print_message "执行数据库迁移..."
  
  cd "$BACKEND_DIR"
  python3 manage.py makemigrations
  python3 manage.py migrate
  
  print_message "数据库迁移完成"
}

# 收集静态文件
collect_static() {
  print_message "收集静态文件..."
  
  cd "$BACKEND_DIR"
  python3 manage.py collectstatic --noinput
  
  print_message "静态文件收集完成"
}

# 创建超级用户
create_superuser() {
  print_message "创建超级用户..."
  
  cd "$BACKEND_DIR"
  
  # 检查是否已有超级用户
  SUPERUSER_COUNT=$(python3 -c "import django; django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).count())")
  
  if [ "$SUPERUSER_COUNT" -gt 0 ]; then
    print_warning "超级用户已存在，跳过创建"
  else
    # 创建超级用户
    python3 manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
User.objects.create_superuser('admin', 'admin@example.com', 'admin');
print('超级用户创建成功: admin/admin');
"
  fi
}

# 安装前端依赖
install_frontend_dependencies() {
  print_message "安装前端依赖..."
  
  cd "$FRONTEND_DIR"
  npm install
  
  print_message "前端依赖安装完成"
}

# 构建前端
build_frontend() {
  print_message "构建前端PWA应用..."
  
  cd "$FRONTEND_DIR"
  npm run build:pwa
  
  print_message "前端构建完成"
}

# 配置前端环境变量
configure_frontend() {
  print_message "配置前端环境..."
  
  # 创建.env文件
  cat > "$FRONTEND_DIR/.env" << EOF
API_URL=http://$DOMAIN:$PORT/api
EOF

  print_message "前端环境配置完成"
}

# 启动后端服务
start_backend() {
  print_message "启动后端服务..."
  
  cd "$BACKEND_DIR"
  python3 manage.py runserver 0.0.0.0:$PORT &
  BACKEND_PID=$!
  
  print_message "后端服务已启动，PID: $BACKEND_PID"
  print_message "API地址: http://$DOMAIN:$PORT/api/"
}

# 启动前端服务
start_frontend() {
  print_message "启动前端服务..."
  
  cd "$FRONTEND_DIR"
  npx quasar serve dist/pwa -p 8080 &
  FRONTEND_PID=$!
  
  print_message "前端服务已启动，PID: $FRONTEND_PID"
  print_message "前端地址: http://$DOMAIN:8080/"
}

# 创建部署摘要
create_deployment_summary() {
  print_message "创建部署摘要..."
  
  cat > "$WMS_ROOT/deployment_summary.txt" << EOF
WMS 智能库存系统部署摘要
=======================

部署时间: $(date)

后端信息:
--------
API地址: http://$DOMAIN:$PORT/api/
管理员地址: http://$DOMAIN:$PORT/admin/
超级用户: admin/admin

前端信息:
--------
应用地址: http://$DOMAIN:8080/
PWA构建目录: $FRONTEND_DIR/dist/pwa/

数据库信息:
---------
数据库名称: $DB_NAME
数据库用户: $DB_USER
数据库密码: $DB_PASSWORD
数据库主机: $DB_HOST:$DB_PORT

部署说明:
--------
1. 后端服务PID: $BACKEND_PID
2. 前端服务PID: $FRONTEND_PID
3. 如需停止服务，请执行: kill $BACKEND_PID $FRONTEND_PID
4. 详细部署文档请参考: $WMS_ROOT/deployment_guide.md
5. 用户指南请参考: $WMS_ROOT/user_guide.md
EOF

  print_message "部署摘要已创建: $WMS_ROOT/deployment_summary.txt"
}

# 主函数
main() {
  print_message "开始部署 WMS 智能库存系统..."
  
  check_dependencies
  setup_variables
  
  # 后端部署
  create_virtualenv
  install_backend_dependencies
  setup_database
  configure_backend
  run_migrations
  collect_static
  create_superuser
  
  # 前端部署
  install_frontend_dependencies
  configure_frontend
  build_frontend
  
  # 启动服务
  start_backend
  start_frontend
  
  # 创建部署摘要
  create_deployment_summary
  
  print_message "WMS 智能库存系统部署完成!"
  print_message "请查看部署摘要: $WMS_ROOT/deployment_summary.txt"
}

# 执行主函数
main
