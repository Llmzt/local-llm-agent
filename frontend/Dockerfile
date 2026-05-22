# 第一阶段：前端构建阶段

# 使用 Node.js 22 alpine 精简镜像
FROM node:22-alpine AS build

# 设置容器内工作目录
WORKDIR /app

# 先复制依赖文件
COPY package.json package-lock.json ./

# 安装前端依赖
RUN npm ci

# 复制前端源码
COPY index.html ./
COPY src ./src

# 构建 Vite 前端
RUN npm run build


# 第二阶段：Nginx 生产部署阶段

# 使用 nginx 精简镜像
FROM nginx:1.27-alpine

# 把构建产物复制到 nginx 静态目录,nginx 会自动托管这些 html/css/js 文件
COPY --from=build /app/dist /usr/share/nginx/html

# 覆盖 nginx 默认配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 容器对外暴露 80 端口
EXPOSE 80