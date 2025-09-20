# Contributing to Chicken House Management System

Thank you for your interest in contributing to the Chicken House Management System! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+
- Python 3.11+

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/chicken-house-management.git
   cd chicken-house-management
   ```

2. **Set up development environment**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Development Guidelines

### Code Style

#### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Use meaningful variable and function names

#### TypeScript/React (Frontend)
- Use TypeScript for all new code
- Follow ESLint configuration
- Use functional components with hooks
- Use Material-UI components consistently

### Git Workflow

1. **Create a feature branch** from `main`
2. **Make your changes** with clear, descriptive commits
3. **Write tests** for new functionality
4. **Update documentation** if needed
5. **Create a pull request** with a clear description

### Commit Messages

Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(farms): add farm creation form validation`
- `fix(tasks): resolve task completion bug`
- `docs(readme): update installation instructions`

## 🧪 Testing

### Backend Testing
```bash
cd backend
python manage.py test
```

### Frontend Testing
```bash
cd frontend
npm test
```

### Integration Testing
```bash
docker-compose up --build
# Run tests against running containers
```

## 📚 Documentation

### Code Documentation
- Write clear docstrings for functions and classes
- Add inline comments for complex logic
- Update README.md for new features

### API Documentation
- Document new API endpoints
- Include request/response examples
- Update API documentation in README.md

## 🐛 Bug Reports

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, browser, versions)
- Relevant logs or screenshots

## ✨ Feature Requests

When requesting features, please include:
- Clear description of the feature
- Use case and motivation
- Implementation ideas (if any)
- Priority level

## 🔍 Code Review Process

### For Contributors
1. Ensure all tests pass
2. Update documentation
3. Request review from maintainers
4. Address feedback promptly

### For Reviewers
1. Check code quality and style
2. Verify tests are adequate
3. Test functionality manually
4. Provide constructive feedback

## 🏗️ Project Structure

```
chicken_house_management/
├── backend/                 # Django backend
│   ├── chicken_management/  # Django project settings
│   ├── farms/              # Farm management app
│   ├── houses/             # House management app
│   ├── tasks/              # Task management app
│   └── authentication/     # Authentication app
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── contexts/       # React contexts
│   │   └── services/       # API services
├── nginx/                  # Nginx configuration
├── .github/                # GitHub workflows and templates
└── docs/                   # Documentation
```

## 🚀 Deployment

### Local Development
```bash
./setup.sh
```

### Production Deployment
```bash
./deploy_railway.sh    # Railway
./deploy_render.sh     # Render
```

## 📋 Checklist for Pull Requests

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No console errors or warnings
- [ ] Feature works as expected
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages follow conventional format

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Follow the code of conduct

## 📞 Getting Help

- Check existing issues and discussions
- Ask questions in GitHub discussions
- Contact maintainers directly for urgent issues

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Chicken House Management System! 🐔

