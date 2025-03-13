# 使用预装了 uv 的 Python 镜像
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

# 将项目安装到 `/app` 目录
WORKDIR /app

# 启用字节码编译
ENV UV_COMPILE_BYTECODE=1

# 由于是挂载卷，使用复制而不是链接
ENV UV_LINK_MODE=copy

# 使用锁文件和设置安装项目的依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# 然后，添加剩余的项目源代码并安装
# 将依赖项与源代码分开安装可以实现最佳的层缓存
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-bookworm

WORKDIR /app
 
COPY --from=uv /root/.local /root/.local
COPY --from=uv --chown=app:app /app/.venv /app/.venv

# 将可执行文件放在环境变量 PATH 的最前面
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["mcp-server-weather"]
