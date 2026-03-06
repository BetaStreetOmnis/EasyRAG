# 贡献指南

感谢您考虑为 EasyRAG 做贡献！

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/BetaStreetOmnis/EasyRAG.git
cd EasyRAG
```

### 2. 安装依赖

#### Python 依赖

```bash
# 生产依赖
pip install -r requirements_cpu.txt  # 或 requirements_gpu.txt

# 开发依赖（用于代码验证）
pip install -r requirements-dev.txt
```

#### 前端依赖

```bash
npm install
```

## ✅ 代码验证

在提交代码之前，请确保通过所有验证检查：

### 运行所有验证

```bash
./validate.sh
```

### 仅验证 Python 代码

```bash
./validate.sh python
```

### 仅验证前端代码

```bash
./validate.sh frontend
```

## 📝 代码规范

### Python

- 使用 **flake8** 进行代码检查
- 最大行长度：120 字符
- 遵循 PEP 8 规范

### JavaScript

- 使用 **ESLint** 进行代码检查
- 缩进：2 空格
- 引号：单引号（除非字符串中包含单引号）

## 🔧 开发工作流

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **进行更改**
   - 编写代码
   - 添加测试（如果适用）

3. **运行验证**
   ```bash
   ./validate.sh
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "描述你的更改"
   ```

5. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 等待代码审查

## 📋 Pull Request 检查清单

在提交 PR 之前，请确保：

- [ ] 代码通过所有验证检查（`./validate.sh`）
- [ ] 代码遵循项目的编码规范
- [ ] 更新了相关文档
- [ ] 添加了必要的注释
- [ ] PR 描述清晰说明了更改内容

## 🐛 报告问题

如果您发现 bug 或有功能建议，请：

1. 检查是否已有相关问题
2. 创建新 issue，包含：
   - 清晰的标题
   - 详细的描述
   - 复现步骤（如果是 bug）
   - 预期行为 vs 实际行为

## 📄 许可证

通过贡献代码，您同意您的代码将根据 [Apache 2.0 许可证](LICENSE) 授权。

---

再次感谢您的贡献！ 🎉
